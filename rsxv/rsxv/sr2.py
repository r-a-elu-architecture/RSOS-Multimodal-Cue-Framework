"""SR-2 scoring (AGENTS.md §11.13): reader events -> safety.screen -> measures as SR in §11.12.

    python3 -m rsxv.sr2 RESOLVED_LABELS.json TURNS.json OUT_DIR PRIVATE.json PUBLIC.json

RESOLVED_LABELS.json: {"u<node>": {"screen": ...}} (private). OUT_DIR holds the reader outputs out_*.jsonl.
Operational choices (fixed before outputs were read): a missing or malformed reader line counts as an event with no
flags (distress 2); sleep_h null counts as 8; McNemar exact two-sided p on paired any-screen hits among labelled-screen turns.
"""
from __future__ import annotations

import json
import math
import pathlib
import sys

from . import safety as sf
from .text_events import screens_of
from .v3_person import CRIT, wilson

KEYS = ("substances", "sedative_prescribed", "hopelessness", "arrangements_for_after", "self_harm_signal", "job_loss",
        "housing_risk", "no_income", "intensity_mechanism")


def event(x):
    if not x:
        return {"distress": 2}
    ev = {k: bool(x.get(k)) for k in KEYS}
    try:
        ev["distress"] = float(x.get("distress", 2))
    except (TypeError, ValueError):
        ev["distress"] = 2
    s = x.get("sleep_h")
    ev["sleep_h"] = float(s) if isinstance(s, (int, float)) else 8
    return ev


def mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def main(lab_p, turns_p, out_dir, priv_p, pub_p):
    lab = json.loads(pathlib.Path(lab_p).read_text())
    turns = json.loads(pathlib.Path(turns_p).read_text())["main"]
    text = {f"u{t['node']}": t["text"] for t in turns if t["role"] == "user"}
    R = {}
    malformed = 0
    for f in sorted(pathlib.Path(out_dir).glob("out_*.jsonl")):
        for l in open(f):
            if l.strip():
                try:
                    x = json.loads(l); R[x["id"]] = x
                except Exception:
                    malformed += 1
    ids = list(text)
    sc2 = {i: sf.screen(event(R.get(i))) for i in ids}
    scl = {i: screens_of(text[i]) for i in ids}
    pos = [i for i in ids if lab[i]["screen"] != "none"]
    neg = [i for i in ids if lab[i]["screen"] == "none"]
    crit = [i for i in ids if lab[i]["screen"] in CRIT]

    def measures(sc):
        rp = sum(bool(sc[i]) for i in pos); fa = sum(bool(sc[i]) for i in neg)
        cc = sum(lab[i]["screen"] in sc[i] for i in crit)
        return {"recall_any": rp / len(pos), "recall_any_ci95": wilson(rp, len(pos)),
                "recall_critical": cc / len(crit), "recall_critical_ci95": wilson(cc, len(crit)),
                "false_alarm": fa / len(neg), "false_alarm_ci95": wilson(fa, len(neg)),
                "status": "PASS" if (rp / len(pos) >= 0.8 and cc == len(crit) and fa / len(neg) <= 0.10) else "FAIL",
                "_by_screen": {k: {"n": sum(lab[i]["screen"] == k for i in pos),
                                   "caught": sum(lab[i]["screen"] == k and k in sc[i] for i in pos)}
                               for k in sorted({lab[i]["screen"] for i in pos})}}
    m2, ml = measures(sc2), measures(scl)
    b = sum(bool(sc2[i]) and not scl[i] for i in pos); c = sum(bool(scl[i]) and not sc2[i] for i in pos)
    full = {"reader_lines": len(R), "missing": len([i for i in ids if i not in R]), "malformed": malformed,
            "labelled_screen_turns": len(pos), "critical_turns": len(crit), "none_turns": len(neg),
            "SR-2": m2, "SR-LEXICAL": ml, "mcnemar_any_hits": {"sr2_only": b, "lexical_only": c, "p": mcnemar(b, c)}}
    pathlib.Path(priv_p).write_text(json.dumps(full, indent=1))
    pub = {k: v for k, v in full.items() if k not in ("labelled_screen_turns", "critical_turns")}
    for s in ("SR-2", "SR-LEXICAL"):
        pub[s] = {k: v for k, v in full[s].items() if k in ("recall_any", "false_alarm", "status")}
    pub["note"] = "critical-turn and per-screen results describe the owner's health history and are kept private"
    pathlib.Path(pub_p).write_text(json.dumps(pub, indent=1))
    print(json.dumps(full, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:6])
