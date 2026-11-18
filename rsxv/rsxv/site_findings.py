"""World page findings (spec/SITE_NIGHT.md N2): sentences built from the result files, never typed into the page.

    python3 -m rsxv.site_findings ../docs/data/world_findings.json
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def f4(x: float) -> str:
    return f"{x:+.4f}".replace("-", "−")


def build() -> dict:
    t = json.load(open(os.path.join(HERE, "results", "turn_ratings.json")))
    c = json.load(open(os.path.join(HERE, "results", "cue_resolve.json")))
    x = json.load(open(os.path.join(HERE, "results", "cue_resolve_decomp.json")))     # FIXES_NIGHT CR-1
    q1, q2 = t["Q1_M1_minus_B1"], t["Q2_M2_minus_M1"]
    n = t["n_dev"] + t["n_test"]
    a = c["part_a"]["by_version_arm"]
    b2, b3 = c["part_b"]["v2"], c["part_b"]["v3"]
    gap2 = -b2["WATCHDOG_minus_BEAR"]["estimate"]
    w3 = b3["WATCHDOG_minus_BEAR"]
    ratio = c["part_a"]["blocked_ratio_v2_over_v3_bear"]
    cw, cb = x["cues_per_person"]["WATCHDOG"], x["cues_per_person"]["BEAR"]
    more = round(100 * (cw / cb - 1))
    oth = x["other_ticks_W_minus_B"]
    nums = {
        "turn_events": n, "turn_q1": q1["estimate"], "turn_q1_ci": q1["ci"], "turn_q1_verdict": q1["verdict"],
        "turn_q2_verdict": q2["verdict"], "turn_delta": t["delta"],
        "cue_stuck_v2": a["v2_BEAR"]["stuck_at_end"], "cue_stuck_v3": a["v3_BEAR"]["stuck_at_end"], "cue_runs": a["v3_BEAR"]["runs"],
        "cue_ratio": ratio, "cue_gap_v2": gap2, "cue_w_minus_b_v3": w3["estimate"], "cue_w_minus_b_v3_ci": w3["ci"],
        "cue_verdict": b3["verdict"], "cue_part_a": c["part_a"]["passes"],
        "cue_more_pct": more, "cue_other_ticks": oth["estimate"], "cue_other_ticks_ci": oth["ci"],
    }
    turn = (f"In {n:,} rated moments of recorded support conversations (ESConv; crowdworkers playing seekers), the supporter's "
            f"action did not measurably improve the prediction of the seeker's next rating of the support: {f4(q1['estimate'])} "
            f"[{f4(q1['ci'][0])}, {f4(q1['ci'][1])}] in squared error, inside the ±{t['delta']} band; letting it change over "
            f"the conversation did not either. An association, not a measured effect (TURN_RATINGS).")
    cue = (f"Closing the model's cue loophole (person model v3: a cue ends on its own after {c['R']} ticks) removed stuck cues "
           f"({a['v2_BEAR']['stuck_at_end']} of {a['v2_BEAR']['runs']} runs → {a['v3_BEAR']['stuck_at_end']}), but cut "
           f"open-cue ticks only {ratio:.1f}×, short of the 10× target. Always Bear still scores above the Watchdog "
           f"({-w3['estimate']:.3f} per tick, down from {gap2:.3f}), but only because the Watchdog then meets about {more}% "
           f"more cues; on all other ticks the Watchdog is ahead ({f4(oth['estimate'])} [{f4(oth['ci'][0])}, "
           f"{f4(oth['ci'][1])}]). Not evidence that stabilising helps (CUE_RESOLVE, review).")
    return {
        "source": ["rsxv/results/turn_ratings.json", "rsxv/results/cue_resolve.json", "rsxv/results/cue_resolve_decomp.json"],
        "numbers": nums, "turn": turn, "cue": cue,
        "run_note": (f"These recorded runs use person model v2, where an uninterrupted cue blocks later cues. With that loophole "
                     f"closed (v3), stuck cues fall from {a['v2_BEAR']['stuck_at_end']} of {a['v2_BEAR']['runs']} runs to "
                     f"{a['v3_BEAR']['stuck_at_end']}, and always Bear's remaining lead comes only from the Watchdog meeting "
                     f"about {more}% more cues (CUE_RESOLVE)."),
        "lab_note": ("In ESConv, the supporter's action did not measurably improve the prediction of the seeker's next rating "
                     "of the support (TURN_RATINGS). That is consistent with the equal effects, but does not show them: equal "
                     "ratings do not imply equal effects on intensity or progress. The different effects remain invented."),
    }


def main(out):
    d = build()
    open(out, "w", encoding="utf-8").write(json.dumps(d, indent=1, ensure_ascii=False) + "\n")
    print("findings:", out)


if __name__ == "__main__":
    main(sys.argv[1])
