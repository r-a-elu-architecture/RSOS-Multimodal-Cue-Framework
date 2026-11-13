"""Arm comparison on a simulated population: canonical v1, RSX-V, sham, and
controls that isolate each RSX-V feature. Run under the full model and the
neutral model, so every difference can be traced to an assumption."""
from __future__ import annotations
import copy
import json
import math
import random
from . import lang as Lg, sim as S
from .run import run

CTX = {"now_min": 600, "consent": ["subject", "operator", "auditor"], "ghost_runs": 12}


def _strip_loop(p):
    q = copy.deepcopy(p)
    for b in q["blocks"]:
        b["until"] = None; b["if"] = None
    return q


def _one_phase(p):
    q = copy.deepcopy(p)
    gate = [b for b in q["blocks"] if b["kind"] == "GATE"]
    rest = [v for b in q["blocks"] if b["kind"] != "GATE" for v in b["vectors"]][:17]
    q["blocks"] = gate + [{"kind": "PHASE", "name": "all", "if": None, "until": None, "max_s": 200, "vectors": rest}]
    q["laws"] = [l for l in q["laws"] if l != "InteractionMatrix"]
    return q


def _long_v1(p, s=200):
    q = copy.deepcopy(p); q["blocks"][0]["max_s"] = s; return q


def _auto(v1):
    from .run import next_program
    r = run(v1, S.person(random.Random(0), 0), {"seed": 1})
    return next_program(v1, r)["program"]


def arms(v1, v2):
    return {
        "v1 canonical (120 s, as written)": (v1, {}),
        "v1 canonical, time-matched (200 s)": (_long_v1(v1), {}),
        "v1 canonical, time-matched (300 s)": (_long_v1(v1, 300), {}),
        "v1 auto-upgraded by NEXT": (_auto(v1), {}),
        "RSX-V": (v2, {}),
        "RSX-V without closed loop (no UNTIL/IF)": (_strip_loop(v2), {}),
        "RSX-V all vectors in one phase": (_one_phase(v2), {}),
        "sham (RSX-V timeline, no content)": (v2, {"sham": True}),
    }


def _ci(xs):
    n = len(xs); m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1)) if n > 1 else 0
    return round(m, 3), round(1.96 * sd / math.sqrt(n), 3)


def compare(v1, v2, n=200, seed=42, model=None, goal=None):
    rng = random.Random(seed)
    people = [S.person(rng, i) for i in range(n)]
    goal = goal or v2["goal"]
    out = {}
    for name, (prog, extra) in arms(v1, v2).items():
        rows = []
        for p in people:
            r = run(prog, p, {**CTX, **extra, "seed": seed * 1000 + p["id"], "model": model or S.FULL})
            o = r["outcome"]
            met = r["status"] == "done" and o["agency"] >= 1 and o["distress"] <= -1 and o["drift"] <= 0
            rows.append({"agency": o["agency"], "distress": o["distress"], "coverage": o["coverage"], "seconds": o["seconds"],
                         "spike": o["peak_rise"] >= 2.5, "stopped": r["status"] == "stopped", "refused": r["status"] == "refused", "goal": met})
        out[name] = {"agency": _ci([x["agency"] for x in rows]), "distress": _ci([x["distress"] for x in rows]),
                     "coverage": _ci([x["coverage"] for x in rows]), "seconds": _ci([x["seconds"] for x in rows]),
                     "spike_rate": round(sum(x["spike"] for x in rows) / n, 3), "stop_rate": round(sum(x["stopped"] for x in rows) / n, 3),
                     "refused_rate": round(sum(x["refused"] for x in rows) / n, 3), "goal_rate": round(sum(x["goal"] for x in rows) / n, 3)}
    return out


def table(res):
    L = ["| Arm | Δ agency | Δ distress | Layers ≥0.3 (of 11) | Seconds | Distress spikes ≥2.5 | NullSafe stops | Refused (ghost/laws) | Goal met |", "|---|---|---|---|---|---|---|---|---|"]
    for k, v in res.items():
        f = lambda t: f"{t[0]:+.2f} ± {t[1]:.2f}"
        L.append(f"| {k} | {f(v['agency'])} | {f(v['distress'])} | {v['coverage'][0]:.1f} | {v['seconds'][0]:.0f} | {v['spike_rate']:.0%} | {v['stop_rate']:.0%} | {v['refused_rate']:.0%} | {v['goal_rate']:.0%} |")
    return "\n".join(L)


if __name__ == "__main__":
    import sys
    v1 = Lg.parse(open(sys.argv[1]).read()); v2 = Lg.parse(open(sys.argv[2]).read())
    from concurrent.futures import ProcessPoolExecutor
    models = {"full model": S.FULL, "neutral model": S.NEUTRAL}
    for m in ("dilution", "readiness", "backfire", "conflict"):
        models[f"only {m}"] = {**S.NEUTRAL, m: True}
    with ProcessPoolExecutor(len(models)) as ex:
        futs = {k: ex.submit(compare, v1, v2, 200, 42, m) for k, m in models.items()}
        res = {k: f.result() for k, f in futs.items()}
    json.dump(res, open(sys.argv[3], "w"), indent=1)
    for k, v in res.items():
        print(f"\n### {k}\n"); print(table(v))
