"""WHOLE_ORGANISM (spec/WHOLE_ORGANISM.md): AgentEnvV3, where Baseline (Lion) is the return to the origin.

    python3 -m rsxv.organism_env results/whole_organism.json      # W1 and W4
LION keeps progress 0.5 and, when health is below the best state kept so far, restores it (keep the gain). Every
recorded environment is unchanged. Stated models.
"""
from __future__ import annotations

import json
import random
import sys

import numpy as np

from . import roles
from .cue_resolve import paired
from .world import AgentEnvV2, MODES, World

EPS = 1e-9
W1_SEEDS = roles.SEEDS
W4_SEEDS = range(295000, 295200)
TICKS = 120


class AgentEnvV3(AgentEnvV2):
    side = "agent_v3"

    def __init__(self, seed: int, **kw):
        super().__init__(seed, **kw)
        self.best_h = self.sys.health()
        self.origin = self.loop.mem.snapshot("origin", self.sys.state())
        self.regained = 0.0

    def step(self, mode: str) -> float:
        self.regained = 0.0
        if mode == "LION" and self.sys.health() < self.best_h - EPS:
            h0 = self.sys.health()
            self.sys.load(self.loop.mem.restore(self.origin))       # return to the origin
            self.regained = self.sys.health() - h0
        r = super().step(mode)
        if self.sys.health() >= self.best_h - EPS:
            self.best_h = self.sys.health()
            self.origin = self.loop.mem.snapshot("origin", self.sys.state())
        return r


class AgentEnvV4(AgentEnvV2):
    """spec/GUARD_GAIN.md: LION hardens the system for the next 3 ticks (new faults at half the rate)."""
    side = "agent_v4"
    HARDEN = 3

    def __init__(self, seed: int, **kw):
        super().__init__(seed, **kw)
        self.shield = 0
        self.granted = 0

    def _maybe_fault(self, p):
        super()._maybe_fault(p / 2 if self.shield > 0 else p)

    def step(self, mode: str) -> float:
        r = super().step(mode)
        self.shield = max(0, self.shield - 1)
        self.granted = 0
        if mode == "LION":
            self.granted = self.HARDEN - self.shield
            self.shield = self.HARDEN
        return r


def sensors_on(env_cls, baseline_attr):
    sums = {m: {r: 0.0 for r in roles.ROLE_OF_MODE.values()} for m in MODES}
    n = {m: 0 for m in MODES}
    for seed in W1_SEEDS:
        env, rng = roles.attach(env_cls(seed)), random.Random(seed * 13 + 5)
        for _ in range(TICKS):
            mode = rng.choice(MODES)
            _, sens = roles.step_with_sensors(env, mode)
            sens["Baseline"] = getattr(env, baseline_attr)
            n[mode] += 1
            for role, v in sens.items():
                sums[mode][role] += v
    means = {m: {r: sums[m][r] / n[m] for r in sums[m]} for m in MODES}
    diag = {role: {"own_mode": mode, "own_mean": means[mode][role],
                   "best_other_mean": max(means[m][role] for m in MODES if m != mode)} for mode, role in roles.ROLE_OF_MODE.items()}
    for d in diag.values():
        d["ok"] = d["own_mean"] > d["best_other_mean"]
    return {"diagonal": diag, "all": all(d["ok"] for d in diag.values())}


def margins(classes):
    out = {}
    for name, cls in classes:
        org = [run(cls, "WATCHDOG", s) for s in W4_SEEDS]
        bear = [run(cls, "BEAR", s) for s in W4_SEEDS]
        out[name] = {"ORGANISM": float(np.mean([x[0] for x in org])), "BEAR": float(np.mean([x[0] for x in bear])),
                     "ORGANISM_minus_BEAR": paired([x[0] for x in org], [x[0] for x in bear]),
                     "lion_ticks_per_run": float(np.mean([x[1] for x in org]))}
    return out


def guard_gain():
    h1 = sensors_on(AgentEnvV4, "granted")
    m = margins((("v2", AgentEnvV2), ("v4", AgentEnvV4)))
    v2, v4 = m["v2"]["ORGANISM_minus_BEAR"], m["v4"]["ORGANISM_minus_BEAR"]
    return {"h1": h1, "margins": m, "H1": h1["all"], "H2": v4["ci"][0] > 0 and v4["estimate"] >= v2["estimate"],
            "H3": v4["estimate"] >= 0.146}


def w1():
    sums = {m: {r: 0.0 for r in roles.ROLE_OF_MODE.values()} for m in MODES}
    n = {m: 0 for m in MODES}
    for seed in W1_SEEDS:
        env, rng = roles.attach(AgentEnvV3(seed)), random.Random(seed * 13 + 5)
        for _ in range(TICKS):
            mode = rng.choice(MODES)
            _, sens = roles.step_with_sensors(env, mode)
            sens["Baseline"] = env.regained
            n[mode] += 1
            for role, v in sens.items():
                sums[mode][role] += v
    means = {m: {r: sums[m][r] / n[m] for r in sums[m]} for m in MODES}
    diag = {role: {"own_mode": mode, "own_mean": means[mode][role],
                   "best_other_mean": max(means[m][role] for m in MODES if m != mode)} for mode, role in roles.ROLE_OF_MODE.items()}
    for d in diag.values():
        d["ok"] = d["own_mean"] > d["best_other_mean"]
    return {"diagonal": diag, "W1": all(d["ok"] for d in diag.values())}


def run(env_cls, policy, seed):
    env = env_cls(seed)
    w = World(env, policy="fixed", fixed_mode="BEAR", seed=seed, score="mission") if policy == "BEAR" else \
        World(env, policy="watchdog", seed=seed, score="mission")
    for _ in range(TICKS):
        w.tick()
    return sum(w.rewards) / TICKS, sum(1 for c, m, r in w.trace if m == "LION")


def w4():
    out = {}
    for name, cls in (("v2", AgentEnvV2), ("v3", AgentEnvV3)):
        org = [run(cls, "WATCHDOG", s) for s in W4_SEEDS]
        bear = [run(cls, "BEAR", s) for s in W4_SEEDS]
        c = paired([x[0] for x in org], [x[0] for x in bear])
        out[name] = {"ORGANISM": float(np.mean([x[0] for x in org])), "BEAR": float(np.mean([x[0] for x in bear])),
                     "ORGANISM_minus_BEAR": c, "lion_ticks_per_run": float(np.mean([x[1] for x in org]))}
    out["W4"] = out["v3"]["ORGANISM_minus_BEAR"]["estimate"] >= 0.088 and out["v3"]["ORGANISM_minus_BEAR"]["ci"][0] > 0
    return out


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[2] == "guard":
        res = guard_gain()
        json.dump(res, open(sys.argv[1], "w"), indent=1)
        print(json.dumps({k: res[k] for k in ("H1", "H2", "H3")} | {"diag": {r: (round(d["own_mean"], 3), round(d["best_other_mean"], 3)) for r, d in res["h1"]["diagonal"].items()}, "margins": res["margins"]}, indent=1))
        sys.exit(0)
    res = {"w1": w1(), "w4": w4()}
    json.dump(res, open(sys.argv[1], "w"), indent=1)
    print(json.dumps(res, indent=1))
