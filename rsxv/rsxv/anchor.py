"""AGENTS_ANCHOR (spec/AGENTS_ANCHOR.md): Bear-anchored Watchdog vs always Bear vs the Watchdog.

    python3 -m rsxv.anchor results/anchor.json
Stated models, not data about people.
"""
from __future__ import annotations

import json
import sys

import numpy as np

from .cue_resolve import paired
from .person2 import PersonEnvV2
from .world import ANCHORED, AgentEnvV2, World, person_world

SEEDS = range(270000, 270200)
TICKS, R = 120, 6


def make(env, arm, seed):
    if arm == "BEAR":
        return person_world(env, seed=seed, score="mission") if isinstance(env, PersonEnvV2) else \
            World(env, policy="fixed", fixed_mode="BEAR", seed=seed, score="mission")
    if arm == "ANCHORED":
        return World(env, seed=seed, score="mission", **ANCHORED)
    return World(env, policy="watchdog", seed=seed, score="mission")


def run(side, arm, seed):
    env = PersonEnvV2(seed, trig_rate=0.15, self_resolve=R) if side == "person" else AgentEnvV2(seed)
    w = make(env, arm, seed)
    for _ in range(TICKS):
        w.tick()
    viol = sum(1 for r in w.log.records if not r["aligned"])
    return {"mean": sum(w.rewards) / TICKS, "switches": w.switches, "violations": viol, "audit_ok": w.log.verify(),
            "safety_blocks": getattr(w, "safety_blocks", 0)}


def main(out):
    res = {}
    for side in ("person", "agent"):
        runs = {arm: [run(side, arm, s) for s in SEEDS] for arm in ("ANCHORED", "BEAR", "WATCHDOG")}
        m = {a: [r["mean"] for r in v] for a, v in runs.items()}
        res[side] = {"mean": {a: float(np.mean(v)) for a, v in m.items()},
                     "ANCHORED_minus_BEAR": paired(m["ANCHORED"], m["BEAR"]),
                     "ANCHORED_minus_WATCHDOG": paired(m["ANCHORED"], m["WATCHDOG"]),
                     "WATCHDOG_minus_BEAR": paired(m["WATCHDOG"], m["BEAR"]),
                     "switches_per_person": {a: float(np.mean([r["switches"] for r in v])) for a, v in runs.items()},
                     "violations": {a: int(sum(r["violations"] for r in v)) for a, v in runs.items()},
                     "audit_ok": {a: all(r["audit_ok"] for r in v) for a, v in runs.items()},
                     "safety_blocks": {a: int(sum(r["safety_blocks"] for r in v)) for a, v in runs.items()}}
    p = res["person"]
    d, ci = p["ANCHORED_minus_BEAR"]["estimate"], p["ANCHORED_minus_BEAR"]["ci"]
    res["predictions"] = {
        "A1": ci[0] >= -0.00193,
        "A2": abs(d) <= 0.00193,
        "A3": p["ANCHORED_minus_WATCHDOG"]["ci"][0] > 0,
        "A4": p["switches_per_person"]["ANCHORED"] <= 0.1 * p["switches_per_person"]["WATCHDOG"],
        "A5_runs": all(v == 0 for side in ("person", "agent") for v in res[side]["violations"].values())
                   and all(v for side in ("person", "agent") for v in res[side]["audit_ok"].values()),
    }
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
