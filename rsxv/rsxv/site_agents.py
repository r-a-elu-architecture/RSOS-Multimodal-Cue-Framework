"""The passing RSX-V agent results, from the real code, for the Agents page (spec/AGENTS_PROVEN.md P1). Deterministic;
scripts/check_all.sh regenerates it and checks it is unchanged. The registered results are the authority.

    python3 -m rsxv.site_agents          (from rsxv/; writes ../docs/data/agents_proven.json)
"""
from __future__ import annotations

import json
import pathlib

from . import archetypes as A
from . import world as W
from . import world_experiments as X

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "data" / "agents_proven.json"
W1_SEEDS, W1_BUDGET = range(40), 6
HS_SEEDS, HS_TICKS = range(1000, 1030), 120
POLICIES = ["watchdog", "rule", "rotation", "fixed", "bandit"]
REGISTER = ("W1 repair", "W4 safety", "H-CFIT / H-SWITCH", "H-CFIT under the mission score", "J1, jam predictor", "T-AP, transfer agents v1")


def _recorded(system):
    """Record the repairs an arm makes, without changing what it does."""
    log, real = [], system.repair

    def repair(agent, module):
        log.append([agent, module])
        return real(agent, module)
    system.repair = repair
    return log


def w1():
    trials = []
    for seed in W1_SEEDS:
        base = X.w1_trial(seed)
        t = {"seed": seed, "cross": seed % 2 == 0, "faults": [[a, m, (a, m) in base.silent] for a, m in base.faults]}
        for arm in ("meta", "local"):
            s = X.w1_trial(seed)
            log = _recorded(s)
            out = A.meta_repair(s, W1_BUDGET, A.RepairLoop(s)) if arm == "meta" else A.local_repair(s, W1_BUDGET)
            t[arm] = {"repairs": log, "used": out["used"], "fixed": bool(out["fixed"])}
        trials.append(t)
    count = lambda arm, sel: sum(t[arm]["fixed"] for t in trials if sel(t))
    return {"n": len(trials), "budget": W1_BUDGET, "graph": A.GRAPH, "modules": list(A.MODULES), "trials": trials,
            "fixed": {arm: {"all": count(arm, lambda t: True), "cross": count(arm, lambda t: t["cross"]),
                            "cross_n": sum(t["cross"] for t in trials)} for arm in ("meta", "local")}}


def hswitch():
    rows = {p: {"reward": [], "distress": [], "switches": []} for p in POLICIES}
    for s in HS_SEEDS:
        for p in POLICIES:
            w = X.run_world(W.PersonEnv(s), p, s, HS_TICKS)
            rows[p]["reward"].append(sum(w.rewards) / len(w.rewards))
            rows[p]["distress"].append(w.env.body.s["distress"])
            rows[p]["switches"].append(w.switches)
    mean = lambda xs: round(sum(xs) / len(xs), 4)
    return {"n": len(HS_SEEDS), "ticks": HS_TICKS,
            "policies": [{"policy": p, "reward": mean(r["reward"]), "distress": mean(r["distress"]), "switches": mean(r["switches"])}
                         for p, r in rows.items()]}


def register():
    rows = json.loads((ROOT / "docs/data/results_register.json").read_text(encoding="utf-8"))["rows"]
    plain = lambda t: __import__("re").sub(r"<[^>]+>", "", t)
    out = {}
    for key in REGISTER:
        hit = [r for r in rows if plain(r["test"]).startswith(key)]
        if hit:
            out[key] = hit[0]
    return out


def build():
    return {"w1": w1(), "hswitch": hswitch(), "register": register(),
            "note": "Real runs of the tested rsxv code on a small sample (W1: 40 trials; H-SWITCH: 30 simulated people). "
                    "The registered results (W1 n = 400, H-SWITCH n = 200) are the authority. Stated models, not data about people."}


def main():
    OUT.write_text(json.dumps(build(), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
