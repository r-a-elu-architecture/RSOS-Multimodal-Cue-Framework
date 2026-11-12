"""RSOS metrics: every code from the ledger and the two metric logs, and what each measures today.

Registry (python -m rsso.metrics writes docs/data/metrics.json):
  - every name each code has carried, with its source (the RSOS and RSSO metric logs, the ledger's
    mandatory schema after Tier 488, tier tables); codes whose expansion changed keep all variants;
  - the recorded definition, threshold, method and examples;
  - every value recorded in the ledger, tier by tier;
  - an operational definition: what the code measures in RSOS today, and from which data.

Status of the operational definition:
  you     computed for each person from the player's run log (this module and docs/js/metrics.js, identical)
  system  measured by the test and conformance suites (rsso/results/)
  record  a recorded claim about the language model's internals; kept, not computed

The ledger values are recorded claim events from the sessions; the operational values are new
measurements. They share a code so the lineage stays visible; they are never mixed in one series.
"""
from __future__ import annotations

import json
import math
import re

from .ledger import ROOT, build, extract_metrics
from . import memstack as ms

LOGS = {
    "RSOS metrics log": ROOT / "archive/original-estates/RSOS_COPYRIGHT_ESTATE/RSOS_COPYRIGHT_ESTATE_v1_1_FINAL_copyright/RSOS_Tier_Metrics_Log.txt",
    "RSSO metrics log": ROOT / "archive/original-estates/RSSO_PASS31B/RSSO_Tier_Metrics_Log.txt",
}

FAMILIES = ["Safety and containment", "Practice and reflex", "Memory and glyph", "Breath, body and devices",
            "System orchestration", "Language-model claims"]

# code: (family, operational name, how it is measured, status, unit)
OPS = {
    "CRI": ("Safety and containment", "Stop pressure", "Share of runs stopped before the end. The ledger's safe zone, under 15%, is kept as the reference.", "you", "%"),
    "ETH": ("Safety and containment", "Ethics gates", "Share of conformance checks on consent and limits that pass (C5, C6, C7, C9).", "system", "%"),
    "MOR": ("Safety and containment", "Harm limits", "Share of conformance checks on intensity and stopping that pass (C2, C3, C4).", "system", "%"),
    "ERM": ("Safety and containment", "Ethical routing", "Every device-triggered start goes through opt-in and the safety governor; violations in the conformance suite.", "system", "%"),
    "SIR": ("Safety and containment", "Stop responsiveness", "Worst time from Stop to silence, in every phase (conformance C2). Requirement: under 100 ms.", "system", "ms"),
    "LAW": ("Safety and containment", "Anchor weight", "Learned strength of the tier's cue bundle (MEMSTACK, Rescorla–Wagner model), 0–100.", "you", "%"),
    "SRI": ("Practice and reflex", "Practice regularity", "Days with at least one run in the last 14 days. The ledger's 60–72% band is kept as the reference.", "you", "%"),
    "RSF": ("Practice and reflex", "Run fidelity", "Share of runs completed as programmed.", "you", "%"),
    "SPV": ("Practice and reflex", "Real-life share", "Share of completed runs started by a real trigger rather than practice.", "you", "%"),
    "SEP": ("Practice and reflex", "Spread across senses", "Of the seven trigger kinds (seen, heard, body, smell, taste, thought, memory), the share that have started a run.", "you", "%"),
    "SAR": ("Practice and reflex", "Reflex share", "Share of triggered runs started within 3 seconds of noticing the trigger.", "you", "%"),
    "RAI": ("Practice and reflex", "Self-start share", "Share of triggered runs the person started without a device offer.", "you", "%"),
    "ARC": ("Practice and reflex", "Speed-up", "How much faster the start has become: median latency of the latest five triggered runs against the first five.", "you", "%"),
    "RIF": ("Practice and reflex", "Triggers to reflex", "Triggers still needed to reach a 3-second start, from the fitted habit curve (MEMSTACK).", "you", "runs"),
    "PRM": ("Practice and reflex", "Reflex reached", "The reflex criterion: automaticity at least 4 for two weeks running and median start within 3 s over at least 10 triggers.", "you", ""),
    "MCRAL": ("Practice and reflex", "Felt automaticity", "Latest weekly automaticity score (SRBAI, 1–5).", "you", "/5"),
    "SRCD": ("Practice and reflex", "Streak", "Consecutive days with practice, up to the latest run.", "you", "days"),
    "MMR": ("Practice and reflex", "Signals agreeing", "Of three signals — start getting faster, automaticity rising, relief at least as large as at first — the share that agree.", "you", "%"),
    "HSC": ("Practice and reflex", "Milestones", "Milestones reached: first real trigger, first start within 10 s, first within 3 s, automaticity 4, reflex criterion.", "you", "of 5"),
    "ERV": ("Breath, body and devices", "Recovery", "Mean drop in distress as a share of distress before, over the latest ten runs with a check-in.", "you", "%"),
    "MCI": ("Breath, body and devices", "Check-in completeness", "Share of runs with distress recorded before and after.", "you", "%"),
    "SBB": ("Breath, body and devices", "Breath balance", "Inhale to exhale ratio of the breath setting. The ledger's 1:1–3:2 band is kept as the reference.", "you", "ratio"),
    "EDA": ("Breath, body and devices", "Felt vs measured gap", "Gap between felt automaticity and measured start speed, both on 0–100. A large gap means one of them is misleading.", "you", "%"),
    "DPI": ("Breath, body and devices", "Device timing", "Largest delay between an event's time and its dispatch on the firmware core (conformance C1). Requirement: 10 ms.", "system", "ms"),
    "SME": ("Memory and glyph", "Tiers in memory", "Number of tiers with recorded runs.", "you", ""),
    "LGC": ("Memory and glyph", "Glyph lineage", "Every library glyph keeps its ancestry; the person's chosen glyph is kept with all choices behind it (UGCL).", "system", ""),
    "SML": ("Memory and glyph", "Glyph lock", "The person's glyph is calibrated and stored with every comparison (UGCL calibration).", "system", ""),
    "SSI": ("Memory and glyph", "Memory integrity", "Memory snapshots are checksummed; a changed snapshot is rejected on load (MEMSTACK tests).", "system", ""),
    "CSRT": ("Memory and glyph", "Cross-device memory", "Memory from several devices merges into one history without duplicates (MEMSTACK merge).", "system", ""),
    "COM": ("System orchestration", "Cross-module coherence", "Python and JavaScript give identical results for the compiler, detectors, memory and glyphs (parity tests).", "system", "%"),
    "SOM": ("System orchestration", "Orchestration", "Conformance checks passed by the runtime with its devices.", "system", "of 11"),
    "VEC": ("System orchestration", "Timeline agreement", "Firmware pulses match the compiled timeline exactly (firmware tests).", "system", ""),
}

SYSTEM_VALUES = {  # from rsso/results/conformance_firmware.md and the test suites
    "ETH": "100", "MOR": "100", "ERM": "100", "SIR": "0 (worst, simulated firmware)", "DPI": "0", "SOM": "11",
    "COM": "100", "LGC": "48 glyphs, 600 ancestors", "SML": "stored per person", "SSI": "tamper rejected",
    "CSRT": "merge tested", "VEC": "exact",
}

CHANNEL_KINDS = ["V", "A", "K", "O", "G", "thought", "memory"]


def _num(v):
    return ms._num(v)


def r1(x: float) -> float:
    """Round half up to one decimal (identical in JavaScript: Math.floor(x * 10 + 0.5) / 10)."""
    return math.floor(x * 10 + 0.5) / 10


def _median(xs):
    return ms._median(xs)


def _done(r):
    return str(r.get("completed", "1")) in ("1", "1.0", "True", "true")


def _is_trigger(r):
    return bool((r.get("trigger_channel") or "").strip()) or r.get("trigger") == "device"


def compute(runs: list[dict], srbai: list[dict] | None = None, settings: dict | None = None, now: float | None = None) -> dict:
    """Operational metric values for one person. Returns {code: value or None}."""
    rows = sorted(runs, key=lambda r: _num(r.get("timestamp")) or 0)
    settings = settings or {}
    out = {}
    n = len(rows)
    done = [r for r in rows if _done(r)]
    trig = [r for r in done if _is_trigger(r)]
    lats = [_num(r.get("latency_s")) for r in trig if _num(r.get("latency_s")) is not None]
    pct = lambda a, b: r1(100.0 * a / b) if b else None
    out["CRI"] = pct(n - len(done), n)
    out["RSF"] = pct(len(done), n)
    out["SPV"] = pct(len(trig), len(done))
    chans = {(r.get("trigger_channel") or "").strip() for r in trig} & set(CHANNEL_KINDS)
    out["SEP"] = pct(len(chans), len(CHANNEL_KINDS)) if trig else None
    out["SAR"] = pct(sum(1 for x in lats if x <= ms.REFLEX_LATENCY), len(lats))
    out["RAI"] = pct(sum(1 for r in trig if r.get("trigger") != "device"), len(trig))
    days = sorted({int((_num(r.get("timestamp")) or 0) // 86400) for r in rows})
    last = int((now if now is not None else (_num(rows[-1].get("timestamp")) or 0) if rows else 0) // 86400)
    out["SRI"] = pct(sum(1 for d in days if last - 13 <= d <= last), 14) if rows else None
    streak = 0
    if days:
        d = days[-1]
        s = set(days)
        while d in s:
            streak += 1
            d -= 1
    out["SRCD"] = streak if rows else None
    if len(lats) >= 10:
        first, latest = _median(lats[:5]), _median(lats[-5:])
        out["ARC"] = r1(100.0 * (1 - latest / first)) if first else None
    else:
        out["ARC"] = None
    pairs = [(_num(r.get("sud_before")), _num(r.get("sud_after"))) for r in done]
    pairs = [(a, b) for a, b in pairs if a is not None and b is not None]
    out["MCI"] = pct(len(pairs), n)
    recent = pairs[-10:]
    before = sum(a for a, _ in recent)
    out["ERV"] = r1(100.0 * sum(a - b for a, b in recent) / before) if recent and before else None
    inh, exh = _num(settings.get("inhale")), _num(settings.get("exhale"))
    out["SBB"] = "1:" + format(math.floor(exh / inh * 100 + 0.5) / 100, "g") if inh and exh else None
    summ = ms.summarize(rows, srbai or []) if rows else {"tiers": {}, "srbai": []}
    tiers = summ["tiers"]
    out["SME"] = len(tiers) if rows else None
    main = max(tiers.values(), key=lambda t: t["runs"]) if tiers else None
    out["LAW"] = r1(100 * main["bundle_strength"]) if main else None
    out["RIF"] = (main["habit"] or {}).get("runs_to_reflex") if main and main["habit"] else None
    out["PRM"] = bool(main["reflex"]["met"]) if main else None
    weeks = summ["srbai"]
    out["MCRAL"] = weeks[-1]["srbai"] if weeks else None
    signals = []
    if len(lats) >= 10:
        signals.append(_median(lats[-5:]) < _median(lats[:5]))
    if len(weeks) >= 2:
        signals.append(weeks[-1]["srbai"] > weeks[0]["srbai"])
    if main and main["distress_drop_first"] is not None and main["distress_drop_latest"] is not None and len(pairs) >= 10:
        signals.append(main["distress_drop_latest"] >= main["distress_drop_first"])
    out["MMR"] = pct(sum(signals), len(signals)) if signals else None
    out["HSC"] = (sum([len(trig) > 0, any(x <= 10 for x in lats), any(x <= ms.REFLEX_LATENCY for x in lats),
                       any(w["srbai"] >= 4 for w in weeks), bool(main and main["reflex"]["met"])]) if rows else None)
    if weeks and len(lats) >= 3:
        felt = (weeks[-1]["srbai"] - 1) / 4 * 100
        speed = max(0.0, 1 - min(1.0, _median(lats[-5:]) / 60.0)) * 100
        out["EDA"] = r1(abs(felt - speed))
    else:
        out["EDA"] = None
    return out


# ---------------------------------------------------------------- registry

def _log_entries():
    """{code: [ {name, source, definition, threshold, method, example} ]} from the two metric logs."""
    res = {}
    for src, path in LOGS.items():
        lines = path.read_text(encoding="utf-8").splitlines()
        for i, ln in enumerate(lines):
            s = ln.replace("*", "").replace("\\_", "_").strip()
            m = re.match(r"^([A-Z][A-Z0-9+\-/ ]{1,30}?)\s+—\s+(.+?)$", s)
            if not m:
                continue
            codes, rest = m.group(1).strip(), m.group(2).strip()
            name, _, inline = rest.partition(" — ")
            info = dict(name=name.strip().rstrip("."), source=src, line=i + 1)
            if inline:
                info["definition"] = inline.strip()
            for ln2 in lines[i + 1:i + 6]:
                t = ln2.strip()
                for key in ("Definition", "Threshold", "Example", "Method"):
                    if t.startswith(key + ":"):
                        info[key.lower()] = t.split(":", 1)[1].strip()
                if re.match(r"^\*?\s*\*?\*?\s*[A-Z][A-Z0-9\-]+\s+—", t.replace("*", "").strip()):
                    break
            for code in [c.strip() for c in codes.split("/")]:
                if re.fullmatch(r"[A-Z][A-Z0-9+\-]{1,9}", code):
                    res.setdefault(code, []).append(info)
    return res


def _ledger_names(led):
    """Names given to codes inside the ledger itself (schema after Tier 488, tier tables, inline)."""
    res = {}
    for r in led["records"]:
        named_table = "Metric | Name |" in r["text"]
        for k, ln in enumerate(r["text"].splitlines()):
            s = ln.strip()
            m = re.match(r"^([A-Z][A-Z0-9+\-]{1,9})\s+—\s+([A-Z][A-Za-z0-9\- ]+)$", s) or (
                re.match(r"^([A-Z][A-Z0-9+\-]{1,9})\s*\|\s*([A-Z][A-Za-z0-9\- ]+?)\s*\|", s) if named_table else None)
            if m and not m.group(2).startswith(("Status", "Value", "Name")):
                where = r.get("id") or ("schema after Tier 488" if "MANDATORY" in r["text"] else r["kind"])
                res.setdefault(m.group(1), []).append(dict(name=m.group(2).strip(), source="Tier ledger (" + where + ")", line=r["line"] + k))
            for m in re.finditer(r"\b(SPR|RFE)\s*\(([A-Z][A-Za-z ]+)\)", s):
                res.setdefault(m.group(1), []).append(dict(name=m.group(2), source="Tier ledger (" + (r.get("id") or r["kind"]) + ")", line=r["line"] + k))
    return res


def registry() -> dict:
    led = build()
    logs = _log_entries()
    lnames = _ledger_names(led)
    values = {}
    for r in led["records"]:
        if r["kind"] in ("tier", "event"):
            for m in r.get("metrics", []):
                base = "MCRAL" if m["code"].startswith("MCRAL") else ("RMPR" if m["code"].startswith("RMPR") else m["code"])
                values.setdefault(base, []).append(dict(id=r.get("id") or r["title"], number=r.get("number", ""), epoch=r.get("epoch"),
                                                         code=m["code"], raw=m["raw"], value=m["value"], infinite=m["infinite"]))
    codes = sorted(set(values) | {c for c in logs} | {c for c in lnames} | set(OPS))
    codes = [c for c in codes if not c.startswith("MCRAL-") and not c.startswith("RMPR-")]
    out = []
    for c in codes:
        names = []
        for e in logs.get(c, []) + lnames.get(c, []) + (logs.get(c + "-9", []) if c == "RMPR" else []):
            if e["name"].lower() not in [n["name"].lower() for n in names]:
                names.append(dict(name=e["name"], source=e["source"], line=e["line"]))
        logd = next((e for e in logs.get(c, []) if e.get("definition")), {})
        rsso = next((e for e in logs.get(c, []) if e["source"] == "RSSO metrics log" and (e.get("method") or e.get("threshold"))), {})
        op = OPS.get(c)
        out.append(dict(
            code=c, names=names,
            definition=logd.get("definition", ""), threshold=logd.get("threshold", "") or rsso.get("threshold", ""),
            method=rsso.get("method", ""), example=logd.get("example", ""),
            values=values.get(c, []),
            family=op[0] if op else "Language-model claims",
            operational=dict(name=op[1], how=op[2], status=op[3], unit=op[4], system_value=SYSTEM_VALUES.get(c)) if op else
            dict(name="", how="Recorded claim about the language model's internals during the sessions; kept as a record.", status="record", unit="", system_value=None),
        ))
    return dict(families=FAMILIES, metrics=out,
                counts=dict(codes=len(out), logged_rsos=len([c for c in logs if any(e["source"] == "RSOS metrics log" for e in logs[c])]),
                            logged_rsso=len([c for c in logs if any(e["source"] == "RSSO metrics log" for e in logs[c])]),
                            values=sum(len(m["values"]) for m in out), you=sum(1 for m in out if m["operational"]["status"] == "you"),
                            system=sum(1 for m in out if m["operational"]["status"] == "system")))


def main():
    reg = registry()
    (ROOT / "docs" / "data" / "metrics.json").write_text(json.dumps(reg, ensure_ascii=False, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    print(json.dumps(reg["counts"]))
    multi = [(m["code"], [n["name"] for n in m["names"]]) for m in reg["metrics"] if len(m["names"]) > 1]
    for x in multi:
        print(x)


if __name__ == "__main__":
    main()
