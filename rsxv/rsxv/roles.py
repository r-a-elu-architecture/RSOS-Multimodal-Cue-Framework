"""Role sensors (spec/ROLE_ORGANISM.md §2.1): one signature measure per World role, read around each tick.

    python3 -m rsxv.roles results/role_sensors.json      # R1
Monitor = silent faults made visible; Stabilise = pressure removed beyond its drift; Plan = next repair armed with
noise-free readings; Repair = faulty modules fixed; Drive = progress; Baseline = progress net of added load.
"""
from __future__ import annotations

import json
import random
import sys

from .world import AgentEnvV2, MODES

ROLE_OF_MODE = {"RAVEN": "Monitor", "BEAR": "Stabilise", "EAGLE": "Plan", "LEOPARD": "Repair", "TIGER": "Drive",
                "LION": "Baseline"}
SEEDS, TICKS = range(290000, 290200), 120


class _Silent(set):
    """The silent-fault set, counting how many become visible when it is cleared."""
    cleared = 0

    def clear(self):
        self.cleared += len(self)
        super().clear()


def _faulty(sys_):
    return sum(1 for a in sys_.q for v in sys_.q[a].values() if v < 0.999)


def attach(env):
    if not isinstance(env.sys.silent, _Silent):
        env.sys.silent = _Silent(env.sys.silent)
    return env


def step_with_sensors(env, mode):
    """Run one tick on an attached AgentEnvV2 and return (reward, sensors)."""
    s = env.sys.silent
    c0, p0, f0, n0 = s.cleared, env.P, _faulty(env.sys), len(env.sys.faults)
    r = env.step(mode)
    drift = min(1.0, p0 + env.p_rise)
    new = len(env.sys.faults) - n0
    progress = env.comp[0] / 0.2
    added = max(0.0, env.P - drift)
    sensors = {"Monitor": env.sys.silent.cleared - c0, "Stabilise": max(0.0, drift - env.P),
               "Plan": 1.0 if env.precise else 0.0, "Repair": max(0, f0 + new - _faulty(env.sys)),
               "Drive": progress, "Baseline": progress - 3 * added}
    return r, sensors


def experiment():
    sums = {m: {r: 0.0 for r in ROLE_OF_MODE.values()} for m in MODES}
    n = {m: 0 for m in MODES}
    for seed in SEEDS:
        env, rng = attach(AgentEnvV2(seed)), random.Random(seed * 13 + 5)
        for _ in range(TICKS):
            mode = rng.choice(MODES)
            _, sens = step_with_sensors(env, mode)
            n[mode] += 1
            for role, v in sens.items():
                sums[mode][role] += v
    means = {m: {r: sums[m][r] / n[m] for r in sums[m]} for m in MODES}
    diag = {}
    for mode, role in ROLE_OF_MODE.items():
        own = means[mode][role]
        best_other = max(means[m][role] for m in MODES if m != mode)
        diag[role] = {"own_mode": mode, "own_mean": own, "best_other_mean": best_other, "ok": own > best_other}
    return {"ticks_per_mode": n, "means": means, "diagonal": diag, "R1": all(d["ok"] for d in diag.values())}


if __name__ == "__main__":
    out = experiment()
    json.dump(out, open(sys.argv[1], "w"), indent=1)
    print(json.dumps({"diagonal": out["diagonal"], "R1": out["R1"]}, indent=1))
