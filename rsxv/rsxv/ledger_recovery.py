"""Planted-effects recovery study for the Causal Ledger (simulation).

Each replicate: a simulated person, a translated message, known per-clause effects planted on distress
(some helpful, some harmful, the rest zero), operators made inert so the planted effects are the whole
truth, 30 micro-randomised sessions. Reported: bias, interval coverage of the true effect, power for
non-zero clauses and false-positive rate for zero clauses."""
from __future__ import annotations
import json
import random
import sys
from . import translate as T, sim as S, ledger as L

DENSE = ("how do you know that? who am I in this exchange with you? imagine 1000 people in one room and you answer them all at once.\n"
         "what would you analyse first? would my signal stand out from the others? how much weight would these ideas carry for society?\n"
         "where would you place them in your own hierarchy?\nif this way of thinking had a symbol and a name what would it be?\n"
         "would you pass it on to others so it reaches the next generation?\nonly honest answers, no fluff.")
CTX = {"consent": ["subject", "operator", "randomisation"]}


def study(reps: int = 40, sessions: int = 30, seed: int = 7) -> dict:
    t = T.to_program(DENSE, msg_id="m1")
    units = L.clause_units(t["program"], t["lineage"])
    clauses = sorted({c for ids in units.values() for c in ids})
    rng = random.Random(seed)
    rows = []
    for r in range(reps):
        p = S.person(rng, r)
        p["base"]["distress"] = 5.0
        truth = {c: rng.choice([-0.012, -0.006, 0.0, 0.0, 0.006, 0.012]) for c in clauses}   # per second
        planted = {c: {"distress": v} for c, v in truth.items() if v}
        led = L.build(t["program"], t["lineage"], p, sessions=sessions, ctx=CTX, planted=planted, inert=True, seed=r + 1)
        for e in led["entries"]:
            x = e.get("distress")
            if not x:
                continue
            tv = truth[e["clause"]] * L.CYCLE
            rows.append({"true": tv, "est": x["effect"], "lo": x["lo"], "hi": x["hi"]})
    nz = [x for x in rows if x["true"] != 0]; z = [x for x in rows if x["true"] == 0]
    res = {
        "replicates": reps, "sessions_per_person": sessions, "clause_estimates": len(rows),
        "mean_bias": round(sum(x["est"] - x["true"] for x in rows) / len(rows), 4),
        "coverage_95": round(sum(x["lo"] <= x["true"] <= x["hi"] for x in rows) / len(rows), 3),
        "power_nonzero": round(sum(not (x["lo"] <= 0 <= x["hi"]) and (x["est"] * x["true"] > 0) for x in nz) / len(nz), 3),
        "false_positive_zero": round(sum(not (x["lo"] <= 0 <= x["hi"]) for x in z) / len(z), 3),
        "correct_sign_nonzero": round(sum(x["est"] * x["true"] > 0 for x in nz) / len(nz), 3),
    }
    return res


def pooled(seeds=(7, 11, 13), reps: int = 40, sessions: int = 30) -> dict:
    runs = [study(reps, sessions, s) for s in seeds]
    keys = ("mean_bias", "coverage_95", "power_nonzero", "false_positive_zero", "correct_sign_nonzero")
    return {"seeds": list(seeds), "per_seed": runs,
            "pooled": {k: round(sum(r[k] for r in runs) / len(runs), 3) for k in keys},
            "clause_estimates": sum(r["clause_estimates"] for r in runs)}


if __name__ == "__main__":
    res = pooled()
    json.dump(res, open(sys.argv[1], "w"), indent=1) if len(sys.argv) > 1 else None
    print(json.dumps(res, indent=1))
