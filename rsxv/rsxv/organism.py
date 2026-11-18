"""ORGANISM (spec/ORGANISM.md §2-3): the fused agent system vs always Bear, the Watchdog and the anchored policy.

    python3 -m rsxv.organism results/organism.json
Person side: anchored, no live exploration, ledger seeded by replayed runs of 50 other persons. Agent side: the
Watchdog. Stated models, not data about people.
"""
from __future__ import annotations

import copy
import json
import sys

import numpy as np

from .anchor import make as make3
from .cue_resolve import paired
from .person2 import PersonEnvV2
from .world import AgentEnvV2, FitLedger, World

SEEDS = range(280000, 280200)
REPLAY = range(281000, 281050)
TICKS, R = 120, 6


def person_env(seed):
    return PersonEnvV2(seed, trig_rate=0.15, self_resolve=R)


def replay_ledger():
    led = FitLedger()
    for s in REPLAY:
        w = World(person_env(s), policy="watchdog", seed=s, score="mission", ledger=led)
        for _ in range(TICKS):
            w.tick()
    return led


def make(side, arm, seed, led):
    env = person_env(seed) if side == "person" else AgentEnvV2(seed)
    if arm != "ORGANISM":
        return make3(env, arm, seed), env
    if side == "person":
        return World(env, policy="anchored", explore=0.0, seed=seed, score="mission", ledger=copy.deepcopy(led)), env
    return World(env, policy="watchdog", seed=seed, score="mission"), env


def run(side, arm, seed, led):
    w, _ = make(side, arm, seed, led)
    for _ in range(TICKS):
        w.tick()
    return {"mean": sum(w.rewards) / TICKS, "switches": w.switches,
            "violations": sum(1 for r in w.log.records if not r["aligned"]), "audit_ok": w.log.verify(),
            "non_bear_ticks": sum(1 for c, m, r in w.trace if m != "BEAR")}


def main(out):
    led = replay_ledger()
    arms = ("ORGANISM", "BEAR", "WATCHDOG", "ANCHORED")
    runs = {side: {a: [run(side, a, s, led) for s in SEEDS] for a in arms} for side in ("person", "agent")}
    m = {side: {a: np.array([r["mean"] for r in runs[side][a]]) for a in arms} for side in runs}
    comb = {a: m["person"][a] + m["agent"][a] for a in arms}
    res = {"replay_ledger_cells": len(led.n),
           "mean": {side: {a: float(v.mean()) for a, v in m[side].items()} for side in m},
           "combined_mean": {a: float(v.mean()) for a, v in comb.items()},
           "person_ORGANISM_minus_BEAR": paired(m["person"]["ORGANISM"], m["person"]["BEAR"]),
           "agent_ORGANISM_minus_BEAR": paired(m["agent"]["ORGANISM"], m["agent"]["BEAR"]),
           "combined_ORGANISM_minus": {x: paired(comb["ORGANISM"], comb[x]) for x in ("BEAR", "WATCHDOG", "ANCHORED")},
           "switches_per_run": {side: {a: float(np.mean([r["switches"] for r in runs[side][a]])) for a in arms} for side in runs},
           "non_bear_ticks_person": {a: float(np.mean([r["non_bear_ticks"] for r in runs["person"][a]])) for a in arms},
           "violations": {side: {a: int(sum(r["violations"] for r in runs[side][a])) for a in arms} for side in runs},
           "audit_ok": all(r["audit_ok"] for side in runs for a in arms for r in runs[side][a])}
    res["predictions"] = {
        "O2": res["person_ORGANISM_minus_BEAR"]["ci"][0] >= -0.00193,
        "O3": res["agent_ORGANISM_minus_BEAR"]["ci"][0] > 0,
        "O4": all(v["ci"][0] > 0 for v in res["combined_ORGANISM_minus"].values()),
        "O5_runs": res["audit_ok"] and all(v == 0 for side in res["violations"].values() for v in side.values()),
    }
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
