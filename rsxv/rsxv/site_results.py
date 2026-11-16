"""Results register for the website (docs/results.html), generated from RESULTS.md §8 so the site always matches the
record. Links are made absolute to the repository.

    python3 -m rsxv.site_results RESULTS.md ../docs/data/results_register.json
"""
from __future__ import annotations

import json
import re
import sys

BASE = "https://github.com/r-a-elu-architecture/RSOS-Multimodal-Cue-Framework/blob/main/rsxv/"


def md(s):
    s = re.sub(r"\[`?([^\]`]+)`?\]\(([^)]+)\)", lambda m: f'<a href="{BASE + m.group(2)}">{m.group(1)}</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", s)


def status(r):
    x = re.sub(r"<[^>]+>", "", r).lower()
    if x.lstrip(" *_").startswith("analysis"):   # spec/FIXES_P2.md C3: an analysis, not evidence for or against
        return "analysis"
    if "pass" in x and ("fail" in x or "of 7" in x or "not testable" in x or "inconclusive" in x):
        return "mixed"
    if "pass" in x or "accepted" in x:
        return "pass"
    if "fail" in x:
        return "fail"
    return "other"


# spec/SITE_CATCHUP.md S8.1, S8.2, S8.5: fixed rules on the test ID, applied in register order.
FAMILIES = ["transfer", "repurposing", "lineage", "person model", "agents", "other"]
WORDING = [("past-crisis", "past high-distress")]


def plain(s):
    return re.sub(r"<[^>]+>", "", s).strip()


def family(test):
    t = plain(test)
    if t.startswith("W5-R"):
        return "repurposing"
    if t.startswith(("W3", "W5", "G1", "G2", "T-AP")):
        return "transfer"
    if t.startswith(("LIA-", "C1", "Corpus")):
        return "lineage"
    if t.startswith(("SR-", "Round", "Phase 9")):
        return "person model"
    if t.startswith(("W1", "W4", "H-", "J1")):
        return "agents"
    return "other"


def series(test):
    t = plain(test)
    for prefix, name in (("W5-R", "W5-R"), ("W5", "W5"), ("W3", "W3"), ("LIA-", "LIA"), ("T-AP", "T-AP")):
        if t.startswith(prefix):
            return name
    return None


def word(s):
    for a, b in WORDING:
        s = s.replace(a, b)
    return s


def main(src, out):
    lines = open(src).read().split("## 8.", 1)[1].split("## 9.", 1)[0].splitlines()
    rows = []
    for l in lines:
        if not l.startswith("| ") or l.startswith("| Test") or l.startswith("|---"):
            continue
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if len(c) < 3:
            continue
        rows.append({"test": word(md(c[0])), "result": word(md(c[1])), "meaning": word(md(c[2])), "status": status(c[1]),
                     "family": family(md(c[0])), "series": series(md(c[0]))})
    last = {}
    for i, r in enumerate(rows):   # parent: the previous row of the same series, by register order (S8.2)
        r["parent"] = last.get(r["series"]) if r["series"] else None
        if r["series"]:
            last[r["series"]] = i
    for r in rows:
        r["parent"] = None if r["parent"] is None else plain(rows[r["parent"]]["test"])
    fam = {f: {s: sum(r["status"] == s for r in rows if r["family"] == f) for s in ("pass", "mixed", "fail", "analysis", "other")} for f in FAMILIES}
    json.dump({"source": "rsxv/RESULTS.md §8", "families": FAMILIES, "family_counts": fam, "rows": rows}, open(out, "w"), indent=1)
    print(len(rows), {s: sum(r["status"] == s for r in rows) for s in ("pass", "mixed", "fail", "other")})


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
