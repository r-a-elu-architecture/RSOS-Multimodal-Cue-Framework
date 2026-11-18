"""CUE_RESOLVE (spec/CUE_RESOLVE.md): person model v3, a cue resolves on its own after R ticks.

    python3 -m rsxv.cue_resolve results/cue_resolve.json [--quick]

Part A: the 15 recorded configurations of rsxv.site_traces, person side, always Bear and Watchdog, v2 and v3.
Part B: Watchdog vs always Bear vs Lion on 200 fresh persons, v3 (R = 6) and v2 for reference.
Stated models, not data about people.
"""
from __future__ import annotations

import json
import sys

import numpy as np

from .person2 import PersonEnvV2
from .site_traces import EVENTS, SEEDS, TIMES, TICKS
from .world import World, person_world

R_MAIN, R_SENS = 6, (3, 12)
STUCK = 20
B_SEEDS = range(260000, 260200)
B_TICKS = 120
BOOT, BOOT_SEED, LEVEL = 2000, 12345, 0.99


def _world(env, arm, seed):
    if arm == "BEAR":
        return person_world(env, seed=seed, score="mission")
    if arm == "LION":
        return World(env, policy="fixed", fixed_mode="LION", seed=seed, score="mission")
    return World(env, policy="watchdog", seed=seed, score="mission")


def run_recorded(seed, event, t0, arm, R):
    """The person side of site_traces.run, for one arm; counts blocked ticks and stuck cues."""
    pe = PersonEnvV2(seed + 500, med_on=(event == "shift"), trig_rate=0.15, self_resolve=R)
    w = _world(pe, arm, seed + 500)
    blocked = 0
    for t in range(1, TICKS + 1):
        if event == "storm":
            on = t0 <= t < t0 + 20
            pe.trig_rate = 0.40 if on else 0.15
            if t == t0 and pe.open is None:
                pe._trigger()
        elif event == "shift" and t == t0:
            pe.med_on = False
        blocked += pe.open is not None
        w.tick()
    stuck = pe.open is not None and pe.ticks - pe.open["t"] >= STUCK
    return {"cues": len(pe.events), "open_at_end": pe.open is not None, "stuck_at_end": stuck, "blocked_ticks": blocked,
            "mean": sum(w.rewards) / TICKS, "self_resolved": pe.outcomes()["self_resolved"]}


def part_a():
    configs = [(s, ev, t0) for s in SEEDS for ev in EVENTS for t0 in (TIMES if ev else (0,))]
    out = {}
    for version, R in (("v2", None), ("v3", R_MAIN)):
        for arm in ("BEAR", "WATCHDOG"):
            rows = [run_recorded(s, ev, t0, arm, R) for s, ev, t0 in configs]
            out[f"{version}_{arm}"] = {
                "runs": len(rows), "stuck_at_end": sum(r["stuck_at_end"] for r in rows),
                "open_at_end": sum(r["open_at_end"] for r in rows), "blocked_ticks": sum(r["blocked_ticks"] for r in rows),
                "cues_total": sum(r["cues"] for r in rows), "cues_min": min(r["cues"] for r in rows),
                "cues_max": max(r["cues"] for r in rows), "mean_per_tick": float(np.mean([r["mean"] for r in rows])),
                "self_resolved": sum(r["self_resolved"] for r in rows)}
    b2, b3 = out["v2_BEAR"], out["v3_BEAR"]
    passes = b3["stuck_at_end"] <= 1 and b3["blocked_ticks"] * 10 <= b2["blocked_ticks"]
    return {"by_version_arm": out, "passes": passes, "blocked_ratio_v2_over_v3_bear": b2["blocked_ticks"] / max(1, b3["blocked_ticks"])}


def person_run(seed, arm, R, ticks=B_TICKS):
    pe = PersonEnvV2(seed, trig_rate=0.15, self_resolve=R)
    w = _world(pe, arm, seed)
    for _ in range(ticks):
        w.tick()
    o = pe.outcomes()
    return {"mean": sum(w.rewards) / ticks, "cues": o["triggers"], "distress": o["distress"]}


def paired(a, b, seed=BOOT_SEED, B=BOOT, level=LEVEL):
    d = np.array(a) - np.array(b)
    rng = np.random.default_rng(seed)
    bs = [float(d[rng.integers(0, len(d), len(d))].mean()) for _ in range(B)]
    return {"estimate": float(d.mean()), "ci": [float(np.quantile(bs, (1 - level) / 2)), float(np.quantile(bs, 1 - (1 - level) / 2))]}


def verdict(ci):
    if ci[1] < 0:
        return "BEAR STILL WINS"
    if ci[0] > 0:
        return "WATCHDOG WINS"
    return "TIE"


def part_b(seeds=B_SEEDS):
    res = {}
    runs = {}
    for version, R in (("v2", None), ("v3", R_MAIN)) + tuple((f"v3_R{r}", r) for r in R_SENS):
        arms = ("WATCHDOG", "BEAR", "LION") if version in ("v2", "v3") else ("WATCHDOG", "BEAR")
        runs[version] = {arm: [person_run(s, arm, R) for s in seeds] for arm in arms}
    for version, arms in runs.items():
        m = {arm: [r["mean"] for r in rows] for arm, rows in arms.items()}
        c = paired(m["WATCHDOG"], m["BEAR"])
        entry = {"WATCHDOG_minus_BEAR": c, "verdict": verdict(c["ci"]),
                 "mean": {arm: float(np.mean(v)) for arm, v in m.items()},
                 "cues_per_person": {arm: float(np.mean([r["cues"] for r in rows])) for arm, rows in arms.items()},
                 "final_distress": {arm: float(np.mean([r["distress"] for r in rows])) for arm, rows in arms.items()}}
        if "LION" in m:
            entry["WATCHDOG_minus_LION"] = paired(m["WATCHDOG"], m["LION"])
            entry["BEAR_minus_LION"] = paired(m["BEAR"], m["LION"])
        res[version] = entry
    gap2 = -res["v2"]["WATCHDOG_minus_BEAR"]["estimate"]
    gap3 = -res["v3"]["WATCHDOG_minus_BEAR"]["estimate"]
    res["loophole_share"] = {"bear_minus_watchdog_v2": gap2, "bear_minus_watchdog_v3": gap3, "difference": gap2 - gap3}
    return res


def main(argv):
    quick = "--quick" in argv
    a = None if quick else part_a()             # the smoke run never touches the registered configurations
    b = part_b(range(990000, 990010) if quick else B_SEEDS)
    res = {"spec": "spec/CUE_RESOLVE.md", "quick": quick, "R": R_MAIN, "part_a": a, "part_b": b}
    txt = json.dumps(res, indent=1, sort_keys=True)
    if argv and not argv[0].startswith("--"):
        open(argv[0], "w").write(txt + "\n")
    print(txt)




# ---------------------------------------------------------------- follow-up B (spec/CUE_RESOLVE.md §8): is v3 adopted?
ADOPT_SEEDS = range(270000, 270200)


def ratio_ci(a, b, seed=BOOT_SEED, B=BOOT, level=LEVEL):
    """Ratio of mean cues per person (a / b), paired bootstrap over persons."""
    a, b = np.array(a, float), np.array(b, float)
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(B):
        i = rng.integers(0, len(a), len(a))
        bs.append(float(a[i].mean() / b[i].mean()))
    return {"ratio": float(a.mean() / b.mean()),
            "ci": [float(np.quantile(bs, (1 - level) / 2)), float(np.quantile(bs, 1 - (1 - level) / 2))]}


def adopt_pass(r):
    return 0.85 <= r["ratio"] <= 1.15 and r["ci"][0] >= 0.80 and r["ci"][1] <= 1.25


def adoption(seeds=ADOPT_SEEDS):
    out = {}
    for version, R in (("v2", None), ("v3", R_MAIN)):
        cues = {arm: [person_run(s, arm, R)["cues"] for s in seeds] for arm in ("BEAR", "WATCHDOG", "LION")}
        bw, bl = ratio_ci(cues["BEAR"], cues["WATCHDOG"]), ratio_ci(cues["BEAR"], cues["LION"])
        out[version] = {"cues_per_person": {k: float(np.mean(v)) for k, v in cues.items()},
                        "bear_over_watchdog": bw, "bear_over_lion": bl}
    out["passes"] = adopt_pass(out["v3"]["bear_over_watchdog"]) and adopt_pass(out["v3"]["bear_over_lion"])
    return out


def main_adopt(argv):
    res = {"spec": "spec/CUE_RESOLVE.md §8", "R": R_MAIN, "seeds": [ADOPT_SEEDS.start, ADOPT_SEEDS.stop - 1], **adoption()}
    txt = json.dumps(res, indent=1, sort_keys=True)
    if argv:
        open(argv[0], "w").write(txt + "\n")
    print(txt)


# ---------------------------------------------------------------- FIXES_NIGHT CR-1: where Bear's lead on v3 comes from
def decomposition(seeds=B_SEEDS, R=R_MAIN, ticks=B_TICKS):
    """Information, not a test: each person's mean per tick split into ticks where a cue was triggered and all others."""
    parts = {}
    for arm in ("WATCHDOG", "BEAR"):
        cue_part, other_part, cost, n_cues = [], [], [], []
        for s in seeds:
            pe = PersonEnvV2(s, trig_rate=0.15, self_resolve=R)
            w = _world(pe, arm, s)
            trig = []
            for _ in range(ticks):
                n0 = len(pe.events)
                w.tick()
                trig.append(len(pe.events) > n0)
            r = np.array(w.rewards)
            t = np.array(trig)
            cue_part.append(r[t].sum() / ticks)
            other_part.append(r[~t].sum() / ticks)
            n_cues.append(int(t.sum()))
            if t.any():
                cost.extend(r[t].tolist())
        parts[arm] = {"cue": cue_part, "other": other_part, "cues": n_cues, "cost_per_trigger_tick": float(np.mean(cost))}
    W, Bp = parts["WATCHDOG"], parts["BEAR"]
    return {"seeds": [seeds.start, seeds.stop - 1], "R": R,
            "total_W_minus_B": paired(np.add(W["cue"], W["other"]), np.add(Bp["cue"], Bp["other"])),
            "cue_ticks_W_minus_B": paired(W["cue"], Bp["cue"]),
            "other_ticks_W_minus_B": paired(W["other"], Bp["other"]),
            "cues_per_person": {"WATCHDOG": float(np.mean(W["cues"])), "BEAR": float(np.mean(Bp["cues"]))},
            "score_per_trigger_tick": {"WATCHDOG": W["cost_per_trigger_tick"], "BEAR": Bp["cost_per_trigger_tick"]}}


if __name__ == "__main__":
    if sys.argv[1:2] == ["decompose"]:
        res = {"spec": "spec/FIXES_NIGHT.md CR-1 (information)", **decomposition()}
        txt = json.dumps(res, indent=1, sort_keys=True)
        if sys.argv[2:]:
            open(sys.argv[2], "w").write(txt + "\n")
        print(txt)
    else:
        (main_adopt(sys.argv[2:]) if sys.argv[1:2] == ["adopt"] else main(sys.argv[1:]))

