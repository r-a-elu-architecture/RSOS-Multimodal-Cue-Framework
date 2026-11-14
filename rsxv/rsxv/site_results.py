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
    if "pass" in x and ("fail" in x or "of 7" in x or "not testable" in x or "inconclusive" in x):
        return "mixed"
    if "pass" in x or "accepted" in x:
        return "pass"
    if "fail" in x:
        return "fail"
    return "other"


def main(src, out):
    lines = open(src).read().split("## 8.", 1)[1].split("## 9.", 1)[0].splitlines()
    rows = []
    for l in lines:
        if not l.startswith("| ") or l.startswith("| Test") or l.startswith("|---"):
            continue
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if len(c) < 3:
            continue
        rows.append({"test": md(c[0]), "result": md(c[1]), "meaning": md(c[2]), "status": status(c[1])})
    json.dump({"source": "rsxv/RESULTS.md §8", "rows": rows}, open(out, "w"), indent=1)
    print(len(rows), {s: sum(r["status"] == s for r in rows) for s in ("pass", "mixed", "fail", "other")})


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
