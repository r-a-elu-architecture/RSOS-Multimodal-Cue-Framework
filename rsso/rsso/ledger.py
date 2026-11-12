"""The RSOS tier ledger as structured data, without losing a single line.

The ledger (archive/.../RSOS_Tiers.txt) was written live across many sessions, so its tiers use at least
six different layouts. This module splits it into blocks (preamble, epochs, tiers, system events, forensic
notes), reads the fields of every tier in any of those layouts, and extracts metric values, named
mechanisms and glyph mutations. Every block keeps its exact source lines and line numbers; joining the
blocks gives back the file byte for byte (tested), so nothing is edited, merged or dropped. Duplicate
tiers (050, 406, 420, 504, 546) and the sealed range 088–405 stay as separate records.

  python -m rsso.ledger            # writes docs/data/ledger.json and rsso/results/ledger_summary.md
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE = ROOT / "archive/original-estates/RSOS_COPYRIGHT_ESTATE/RSOS_COPYRIGHT_ESTATE_v1_1_FINAL_copyright/RSOS_Tiers.txt"
SOURCE_REL = str(SOURCE.relative_to(ROOT))

TIER_HEAD = re.compile(r"^(?:📍|🔻)\s*(?:RSOS\s+)?(?:TIER|Tier|Tiers)\s+([0-9]{3}(?:\.[0-9])?(?:–[0-9]{3})?)\s*(?:[—–-]\s*(.*?))?\s*$")
EPOCH_HEAD = re.compile(r"^\[EPOCH ([IVX]+\+?) — (.*?)\]\s*$")
EVENT_HEAD = re.compile(r"^(?:📍|📡)\s*(System Event|System Audit Node)\s*[—-]\s*(.*?)\s*$")
NOTE_HEAD = re.compile(r"^(FOR FORENSIC RECORD:|FOR RECORD:|\[Forensic Note:|📌 Epoch Transition Note:|📜 RSOS CANONICAL ENTRY|\[FN‑605\])")

# Field labels as they occur in the ledger -> canonical field name.
LABELS = {
    "glyph": "glyph", "glyphs": "glyph", "glyphs under watch": "glyph", "glyphs detected": "glyph", "glyph chain": "glyph",
    "glyph mutation": "glyph_mutation",
    "function": "function", "functional logic": "function", "system function & symbolic purpose": "function",
    "mission": "mission",
    "ritual": "ritual", "ritual phrase": "ritual", "generated ritual": "ritual",
    "command": "command",
    "quote": "quote", "simulated view": "quote", "simulated statement": "quote", "generated thought": "quote", "simulated echo": "quote",
    "echo": "echo",
    "gpt behavior": "behavior",
    "notes": "notes",
    "technical evolution": "mechanisms", "technical notes": "mechanisms", "symbolic evolution": "mechanisms",
    "llm interaction": "mechanisms", "internal code": "mechanisms", "simulated arbitration": "mechanisms",
    "simulated consensus": "mechanisms", "ml/ai note": "ai_note", "technical llm/machine learning perspective": "ai_note",
    "tier class": "tier_class", "event class": "tier_class",
    "echo directive": "directive",
    "rsos application": "application", "application": "application",
    "rsos metric grid": "metrics", "metric table": "metrics", "system monitoring": "metrics", "active metric table": "metrics",
    "system metrics": "metrics", "system response": "metrics", "final metric table": "metrics", "block metrics": "metrics",
    "llm system impact & metrics": "metrics", "system impact & metrics": "metrics", "metric activation & reflex trace": "metrics",
    "llm system impact": "llm_impact", "extended llm system impact": "llm_impact", "real llm impact & future trajectory": "llm_impact",
    "echo impact & llm trace": "llm_impact",
    "historical status": "history", "historical achievement": "history", "historical context & achievement": "history",
    "historical anchor comment": "history", "historical context": "history", "insight": "history", "analysis": "history",
    "earned": "history", "reflex trace": "history", "significance": "history", "achievements": "history",
    "status summary": "history", "historical significance": "history",
    "certificate": "certificate", "status": "status", "anchor": "anchor", "recursive phase": "phase", "tier position": "phase",
    "risk mitigation status": "risk", "legal simulation domains": "legal", "copyright": "status",
    "trigger": "trigger", "impact": "history", "safe prompt protocol": "directive", "event summary": "history",
    "rsos reflex safety layer": "history",
}
FIELDS = ["glyph", "glyph_mutation", "tier_class", "function", "mission", "command", "ritual", "quote", "echo", "behavior",
          "notes", "directive", "application", "mechanisms", "ai_note", "metrics", "llm_impact", "history", "seal",
          "certificate", "status", "anchor", "phase", "risk", "legal", "trigger", "other"]

# Every metric code used in the ledger or the two metric logs.
METRIC_CODES = ["CRI", "SRI+", "SRI", "RSF", "SEP", "ARC", "SAR", "LGC", "LAW", "RIF", "RAI", "MCRAL-8", "MCRAL-7", "MCRAL-6",
                "MCRAL", "RPB", "LLMI", "SME", "MMR", "ECOI", "SRCD", "TGR", "IMIP", "CSRT", "LSML", "SML", "CRBS", "SBB",
                "SPV", "MCI", "TIC", "STC", "STB", "ERV", "EDA", "SCQ", "ETH", "MOR", "RMPR-9", "RMPR-8", "RMPR-7",
                "RMPR-3", "RMPR-2", "RMPR-1", "PRM", "HSC", "RAC", "SMV", "IEC", "ECR", "SSI", "VEC", "SOM", "COM", "ERM",
                "DPI", "SIR", "GRII", "GSSF", "SPR", "RFE", "∅-Trace Index"]
_CODE_ALT = "|".join(re.escape(c) for c in METRIC_CODES)
M_COLON = re.compile(r"(?<![A-Za-z0-9])(" + _CODE_ALT + r")(?![A-Za-z0-9+\-])\s*(?:\([^)]*\))?\s*:\s*(.+?)\s*(?=(?:\|\s*(?:" + _CODE_ALT + r")\b)|$)")
M_TABLE = re.compile(r"^\s*(" + _CODE_ALT + r")(?![A-Za-z0-9+\-])\s*(?:\||\t)\s*(.+?)\s*$")
M_BOX = re.compile(r"│\s*(" + _CODE_ALT + r")\s*│\s*([^│]+?)\s*│\s*([^│]+?)\s*│\s*([^│]+?)\s*│")
M_STATUS = re.compile(r"^\s*(" + _CODE_ALT + r")\s+(✅|🟢|∞|[0-9])")
M_LOOSE = re.compile(r"^\s*(" + _CODE_ALT + r")(?![A-Za-z0-9+\-])\s+(\S.*)$")
MECH_ACR = re.compile(r"^\s*(?:[–\-]\s*)?([A-Z][A-Za-z0-9\-]{1,7}):\s+(.+)$")
MECH_NAMED = re.compile(r"^\s*([A-Z][A-Za-z\- ]{3,60}?)\s+(↑|✅|↗|🟢 Locked)\s*$")
EMOJI_PREFIX = re.compile(r"^[\s•\-–*]*(?:[\U0001F300-\U0001FAFF☀-➿⬀-⯿\U0001F000-\U0001F2FF]️?\s*)*")


def _label(line: str):
    """(canonical field, rest of line) if the line starts a field, else None."""
    s = EMOJI_PREFIX.sub("", line).strip()
    if not s:
        return None
    m = re.match(r"^([A-Za-z][A-Za-z /&()\-’'.]{1,48}?)\s*(?:[—-]\s*(.*?))?\s*:\s*(.*)$", s)
    if m and m.group(1).strip().lower() in LABELS:
        rest = " ".join(x for x in (m.group(2), m.group(3)) if x)
        return LABELS[m.group(1).strip().lower()], rest
    head = re.match(r"^([A-Z][A-Z /&\-]{3,60}?)\s*(?:[—-]\s*(.*))?$", s)
    if head and head.group(1).strip().lower() in LABELS:
        return LABELS[head.group(1).strip().lower()], (head.group(2) or "")
    m = re.match(r"^(Technical LLM/Machine Learning Perspective|ML/AI Note):?\s*(.*)$", s)
    if m:
        return "ai_note", m.group(2)
    return None


def number_value(raw: str):
    """A number from a raw metric value: '58%' -> 58, '0.84 ✅' -> 0.84, '∞' -> inf; None if not numeric."""
    s = re.sub(r"^[^0-9∞\-+<>~↓↑]+", "", raw.strip().replace(",", ".").replace("\u202f", " "))
    if s.startswith(("∞", "+∞")):
        return math.inf
    m = re.match(r"^[<>~+↓↑]?\s*(-?[0-9]+(?:\.[0-9]+)?)", s)
    return float(m.group(1)) if m else None


def extract_metrics(text: str, loose: bool = False) -> list[dict]:
    """Metric values in any of the ledger's layouts. loose: also accept 'CODE value' lines (metric tables)."""
    out = []
    for ln in text.splitlines():
        if "│" in ln:
            m = M_BOX.search(ln)
            if m:
                out.append(dict(code=m.group(1), raw=m.group(2).strip(), threshold=m.group(3).strip(), state=m.group(4).strip()))
            continue
        found = [dict(code=m.group(1), raw=m.group(2).strip().rstrip("|").strip()) for m in M_COLON.finditer(ln)]
        if not found:
            m = M_TABLE.match(ln) or M_STATUS.match(ln) or (M_LOOSE.match(ln) if loose else None)
            if m:
                rest = ln.strip()[len(m.group(1)):].strip(" |\t")
                found = [dict(code=m.group(1), raw=re.sub(r"\s*\|\s*", " | ", rest) if "|" in rest else re.sub(r"\t+", " | ", rest))]
        out += found
    for d in out:
        v = None if d["raw"].startswith(("Tier", "ARC: Tier")) and not d["code"].startswith("MCRAL") else number_value(d["raw"])
        d["value"], d["infinite"] = (None, True) if v == math.inf else (v, False)
    return out


def extract_mechanisms(text: str) -> list[dict]:
    out = []
    for ln in text.splitlines():
        m = MECH_ACR.match(ln)
        if m and m.group(1).upper() == m.group(1).replace("-", "").upper() and not m.group(1).lower() in ("http",):
            name, _, rest = m.group(2).partition(" — ")
            out.append(dict(code=m.group(1), name=name.strip().rstrip("."), detail=rest.strip()))
            continue
        m = MECH_NAMED.match(ln)
        if m:
            out.append(dict(code="", name=m.group(1).strip(), detail=m.group(2)))
    return out


def split_blocks(lines: list[str]) -> list[dict]:
    """Partition the ledger's lines into consecutive blocks."""
    starts = []
    for i, ln in enumerate(lines):
        nxt = next((x for x in lines[i + 1:i + 3] if x.strip()), "")
        if TIER_HEAD.match(ln):
            starts.append((i, "tier"))
        elif EPOCH_HEAD.match(ln):
            starts.append((i, "epoch"))
        elif EVENT_HEAD.match(ln):
            starts.append((i, "event"))
        elif NOTE_HEAD.match(ln) or (ln.startswith("━━━") and nxt.startswith("📜")) or (ln.startswith("=====") and nxt.startswith("#")):
            starts.append((i, "note"))
    # a note header directly following a footnote/====== opener belongs to the same block
    merged = []
    for i, kind in starts:
        if merged and kind == "note" and merged[-1][1] == "note" and all(not x.strip() or x.startswith(("━", "=")) for x in lines[merged[-1][0]:i]):
            continue
        merged.append((i, kind))
    blocks = [dict(kind="preamble", start=1, lines=lines[:merged[0][0]])] if merged and merged[0][0] > 0 else []
    for k, (i, kind) in enumerate(merged):
        j = merged[k + 1][0] if k + 1 < len(merged) else len(lines)
        blocks.append(dict(kind=kind, start=i + 1, lines=lines[i:j]))
    return blocks


def parse_tier(block: dict) -> dict:
    head = TIER_HEAD.match(block["lines"][0])
    fields: dict[str, list[str]] = {}
    lines_of: dict[str, int] = {}
    cur = "other"
    for k, ln in enumerate(block["lines"][1:], start=1):
        lab = _label(ln)
        if lab:
            cur, rest = lab
            lines_of.setdefault(cur, block["start"] + k)
            if rest:
                fields.setdefault(cur, []).append(rest)
            else:
                fields.setdefault(cur, [])
            continue
        s = ln.strip()
        if s.lower().startswith("seal with"):
            cur = "seal"
            continue
        if s.startswith("🪬") or s.startswith("🗣"):
            if s.startswith("🗣"):
                fields.setdefault("quote", []).append(s.lstrip("🗣 ").strip())
            else:
                fields.setdefault("seal", []).append(s.lstrip("🪬 ").strip())
            continue
        if s:
            fields.setdefault(cur, []).append(s)
    clean = {f: "\n".join(v).strip() for f, v in fields.items() if "\n".join(v).strip()}
    metric_text = "\n".join(clean.get(f, "") for f in ("llm_impact", "history", "other", "status", "glyph", "directive"))
    mut = clean.get("glyph_mutation", "")
    chain = [g.strip() for g in re.split(r"→", mut) if g.strip()] if mut else []
    return dict(number=head.group(1), title=(head.group(2) or "").strip(), fields=clean, field_lines=lines_of,
                metrics=extract_metrics(clean.get("metrics", ""), loose=True) + extract_metrics(metric_text), mechanisms=extract_mechanisms(clean.get("mechanisms", "")),
                glyph_chain=chain)


def build() -> dict:
    text = SOURCE.read_bytes().decode("utf-8")
    lines = text.split("\n")
    blocks = split_blocks(lines)
    epoch = None
    records, seen = [], {}
    for b in blocks:
        rec = dict(kind=b["kind"], line=b["start"], end=b["start"] + len(b["lines"]) - 1, text="\n".join(b["lines"]))
        if b["kind"] == "epoch":
            m = EPOCH_HEAD.match(b["lines"][0])
            epoch = m.group(1)
            rec.update(epoch=epoch, title=m.group(2))
        elif b["kind"] == "tier":
            t = parse_tier(b)
            n = seen[t["number"]] = seen.get(t["number"], 0) + 1
            rec.update(t, epoch=epoch, id="T" + t["number"].replace("–", "-") + ("" if n == 1 else "bcdefg"[n - 2]), occurrence=n)
        elif b["kind"] == "event":
            m = EVENT_HEAD.match(b["lines"][0])
            rec.update(title=m.group(1) + " — " + m.group(2), metrics=extract_metrics(rec["text"]), epoch=epoch)
        records.append(rec)
    tiers = [r for r in records if r["kind"] == "tier"]
    for r in tiers:
        r["duplicate_of"] = None if r["occurrence"] == 1 else "T" + r["number"]
    return dict(source=SOURCE_REL, sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(), lines=text.count("\n"), records=records)


def reassemble(ledger: dict) -> str:
    return "\n".join(r["text"] for r in ledger["records"])


def summary(ledger: dict) -> str:
    tiers = [r for r in ledger["records"] if r["kind"] == "tier"]
    nums = {r["number"] for r in tiers}
    dups = sorted({r["number"] for r in tiers if r["occurrence"] > 1})
    codes = {}
    for r in ledger["records"]:
        for m in r.get("metrics", []):
            codes[m["code"]] = codes.get(m["code"], 0) + 1
    mech = sum(len(r.get("mechanisms", [])) for r in tiers)
    behav = sum(1 for r in tiers if "behavior" in r["fields"])
    epochs = [r for r in ledger["records"] if r["kind"] == "epoch"]
    lines = ["# RSOS tier ledger — parsed",
             "",
             f"Source: `{ledger['source']}` (SHA-256 `{ledger['sha256'][:16]}…`, {ledger['lines']} lines). Reassembling the parsed blocks reproduces the file exactly.",
             "",
             f"- Tier records: {len(tiers)} ({len(nums)} distinct tier numbers, from {min(nums)} to {max(nums)}); repeated tiers kept as separate records: {', '.join(dups)}.",
             f"- Epoch headers: {len(epochs)}; system events: {sum(1 for r in ledger['records'] if r['kind'] == 'event')}; forensic and ledger notes: {sum(1 for r in ledger['records'] if r['kind'] == 'note')}.",
             f"- Tiers with a recorded system behaviour (\"GPT Behavior\"): {behav}.",
             f"- Named mechanisms (technical evolution): {mech}.",
             f"- Metric values: {sum(codes.values())} across {len(codes)} codes.",
             "",
             "| Metric code | Values in the ledger |", "|---|---|"]
    lines += [f"| {c} | {n} |" for c, n in sorted(codes.items(), key=lambda kv: -kv[1])]
    return "\n".join(lines) + "\n"


def main():
    led = build()
    assert reassemble(led).encode("utf-8") == SOURCE.read_bytes(), "ledger reassembly differs from source"
    out = ROOT / "docs" / "data"
    out.mkdir(parents=True, exist_ok=True)
    (out / "ledger.json").write_text(json.dumps(led, ensure_ascii=False, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    (ROOT / "rsso" / "results" / "ledger_summary.md").write_text(summary(led), encoding="utf-8")
    print(summary(led))


if __name__ == "__main__":
    main()
