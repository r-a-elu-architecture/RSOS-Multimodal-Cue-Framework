#!/usr/bin/env python3
"""EVIDENCE_LABELS (spec/EVIDENCE_LABELS.md): one evidence scale, a label on every live page, README section.

Reads architecture/evidence_map.json and docs/data/results_register.json; writes docs/data/evidence.json, the label
block in each live page and the "Evidence levels" section of README.md. Run from anywhere; `--check` writes nothing
and exits 1 if any output would change.
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
START, END = "<!-- evidence:start -->", "<!-- evidence:end -->"
ORDER = ["E0", "E1", "E2", "E3", "E4", "E5"]
STATUSES = ["pass", "mixed", "fail", "analysis", "other"]
TAIL = "Not yet tested with people using RSOS."
OVERCLAIM = ["proven", "validated", "evidence-based", "clinically", "scientifically", "shown to work", "guaranteed",
             "effective", "efficacy", "cures", "heals", "rewires", "reprograms"]
EXEMPT = ["validated instrument"]


def path(*p):
    return os.path.join(ROOT, *p)


def load(rel):
    with open(path(rel), encoding="utf-8") as f:
        return json.load(f)


def strip_tags(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def row_source(test: str, sources: dict) -> str:
    """The source of the longest key that starts the row's test name (L3: exactly one at that length, or an error).
    Longest key wins so that "Round 8f" (simulation) is not caught by "Round 8" (public data) (FIXES_NIGHT E-1)."""
    name = strip_tags(test)
    hits = [(len(k), src) for src, keys in sources.items() for k in keys if name.startswith(k)]
    if not hits:
        raise ValueError(f"results-register row needs exactly one source, has []: {name[:80]}")
    top = max(n for n, _ in hits)
    best = sorted({src for n, src in hits if n == top})
    if len(best) != 1:
        raise ValueError(f"results-register row needs exactly one source, has {best}: {name[:80]}")
    return best[0]


def check_stated(row: dict, src: str) -> None:
    """L4 (FIXES_NIGHT E-1): a row that says it ran on stated models is never counted as recorded or public data."""
    text = strip_tags(row.get("result", "") + " " + row.get("meaning", "")).lower()
    if "stated model" in text and src in ("public", "record"):
        raise ValueError(f"row says 'stated model' but is filed under '{src}': {strip_tags(row['test'])[:80]}")


def counts(rows) -> dict:
    c = Counter(r["status"] for r in rows)
    return {s: c.get(s, 0) for s in STATUSES if c.get(s, 0) or s in ("pass", "mixed", "fail")}


def fmt_counts(c: dict) -> str:
    n = sum(c.values())
    return f"{n} registered test{'s' if n != 1 else ''}: " + ", ".join(f"{v} {k}" for k, v in c.items())


def build():
    m, reg = load("architecture/evidence_map.json"), load("docs/data/results_register.json")
    rows = reg["rows"]
    for r in rows:
        r["source"] = row_source(r["test"], m["row_sources"])
        check_stated(r, r["source"])
    if not any(r["source"] == "people" for r in rows):
        for p, v in m["pages"].items():
            if v.get("level") == "E5":
                raise ValueError(f"L4: {p} is labelled E5 but no register row has source 'people'")
    L = {k: dict(v) for k, v in m["levels"].items()}
    # spec/PUBLIC_EDITION_2.md L: E4 says so while no registered test on recorded or public data has passed
    if not any(r["source"] in ("public", "record") and r["status"] == "pass" for r in rows):
        L["E4"]["name"] += ": no positive result yet"
    pages = {}
    for p, v in m["pages"].items():
        kind = v["kind"]
        if kind == "part":
            lvl = v["level"]
            for b in v.get("basis", []):
                if not os.path.exists(path(b)):
                    raise ValueError(f"L2: {p} cites a missing file {b}")
            text = f"Evidence: {lvl} {L[lvl]['name']}. "
            detail = {}
            if lvl in ("E1", "E2"):
                text += L[lvl]["means"][0].upper() + L[lvl]["means"][1:]
                text += f" ({', '.join(v['basis'])})." if lvl == "E2" else "."
                if v.get("note"):
                    text += f" {v['note'][0].upper() + v['note'][1:]}."
            else:
                fam = set(v["families"])
                mine = [r for r in rows if r["family"] in fam]
                need = {"E3": {"sim"}, "E4": {"public", "record"}, "E5": {"people"}}[lvl]
                if not any(r["source"] in need for r in mine):
                    raise ValueError(f"L2: {p} at {lvl} cites no register row of source {sorted(need)}")
                sim = [r for r in mine if r["source"] == "sim"]
                rec = [r for r in mine if r["source"] in ("public", "record")]
                parts = []
                if sim:
                    detail["simulation"] = counts(sim)
                    parts.append("in simulation, " + fmt_counts(detail["simulation"]))
                if rec:
                    detail["recorded"] = counts(rec)
                    parts.append("on recorded data, " + fmt_counts(detail["recorded"]))
                text += parts[0][0].upper() + parts[0][1:] + ("; " + "; ".join(parts[1:]) if parts[1:] else "") + "."
            text += " " + TAIL
            pages[p] = {"kind": kind, "level": lvl, "part": v["part"], "text": text, "basis": v.get("basis", []),
                        "families": v.get("families", []), "counts": detail}
        elif kind == "record":
            pages[p] = {"kind": kind, "level": None, "text": "Evidence: this page shows records as written and makes no "
                        "claim of effect. " + TAIL}
    by_level = Counter(v["level"] for v in pages.values() if v["kind"] == "part")
    reg_c = counts(rows)
    lv = ", ".join(f"{by_level[k]} at {k} {L[k]['name']}" for k in ORDER if by_level.get(k))
    summary = f"Evidence across RSOS: of {sum(by_level.values())} parts, {lv}. Results register: {fmt_counts(reg_c)}. {TAIL}"
    for p, v in m["pages"].items():
        if v["kind"] == "summary":
            pages[p] = {"kind": "summary", "level": None, "text": summary}
    src_c = {s: counts([r for r in rows if r["source"] == s]) for s in m["row_sources"]}
    data = {"spec": m["spec"], "levels": L, "pages": pages, "register": reg_c, "register_by_source": src_c,
            "parts_by_level": {k: by_level.get(k, 0) for k in ORDER}}
    return data


def label_html(pg: dict) -> str:
    lvl = pg["level"] or pg["kind"]
    return (f'{START}<p class="evidence" data-level="{lvl}" style="font-size:.88em;color:var(--muted);'
            f'border-left:3px solid var(--muted);padding-left:10px;margin:0 0 22px">{html.escape(pg["text"], quote=False)}'
            f'</p>{END}')


def place(s: str, block: str) -> str:
    """Replace the existing block, or insert it after the first paragraph that follows the page's <h1>."""
    if START in s:
        return re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, s, count=1, flags=re.S)
    h = s.index("<h1")
    p = s.index("<p", h)
    e = s.index("</p>", p) + len("</p>")
    return s[:e] + "\n  " + block + s[e:]


def readme_section(data) -> str:
    L = data["levels"]
    out = [START, "", "Every page on the site carries one of these labels (scale and rules: "
           "[`spec/EVIDENCE_LABELS.md`](spec/EVIDENCE_LABELS.md)). " + TAIL, "",
           "| Part | Level | What that means |", "|---|---|---|"]
    for p, v in sorted(data["pages"].items(), key=lambda kv: (kv[1]["level"] or "", kv[0])):
        if v["kind"] != "part":
            continue
        means = L[v["level"]]["means"]
        if v["counts"]:
            names = {"simulation": "in simulation", "recorded": "on recorded data"}
            means += ": " + "; ".join(f"{names[k]}, {fmt_counts(c)}" for k, c in v["counts"].items())
        out.append(f"| {v['part']} | {v['level']} {L[v['level']]['name']} | {means} |")
    rc = data["register"]
    out += ["", f"Results register: {fmt_counts(rc)} ([`rsxv/RESULTS.md`](rsxv/RESULTS.md)).", "", END]
    return "\n".join(out)


def outputs(data) -> dict:
    out = {"docs/data/evidence.json": json.dumps(data, indent=1, ensure_ascii=False) + "\n"}
    for p, pg in data["pages"].items():
        rel = f"docs/{p}.html"
        with open(path(rel), encoding="utf-8") as f:
            out[rel] = place(f.read(), label_html(pg))
    with open(path("README.md"), encoding="utf-8") as f:
        s = f.read()
    sec = readme_section(data)
    if START in s:
        s = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: sec, s, count=1, flags=re.S)
    else:
        i = s.index("\n## The four systems")
        s = s[:i] + "\n## Evidence levels\n\n" + sec + "\n" + s[i:]
    out["README.md"] = s
    return out


def visible_text(s: str) -> str:
    s = re.sub(r"<script.*?</script>|<style.*?</style>|<!--(?!\s*evidence).*?-->", " ", s, flags=re.S)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())


def overclaims(text: str) -> list:
    t = text.lower()
    for e in EXEMPT:
        t = t.replace(e, " ")
    return [w for w in OVERCLAIM if re.search(r"(?<![\w-])" + re.escape(w) + r"(?![\w-])", t)]


def main(argv):
    data = build()
    changed = []
    for rel, content in outputs(data).items():
        old = open(path(rel), encoding="utf-8").read() if os.path.exists(path(rel)) else None
        if old != content:
            changed.append(rel)
            if "--check" not in argv:
                with open(path(rel), "w", encoding="utf-8") as f:
                    f.write(content)
    if "--check" in argv:
        print("evidence: up to date" if not changed else "evidence: out of date: " + ", ".join(changed))
        return 1 if changed else 0
    print(f"evidence: {len(data['pages'])} pages labelled; wrote {len(changed)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
