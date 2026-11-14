"""W3c, policy-level transfer tested as deployed, exactly as fixed in AGENTS.md §11.4.

    python3 -m rsxv.w3c_experiments          # writes results/results_w3c.json and results/w3c.md
"""
from __future__ import annotations

import json
import pathlib
import random
import sys

from . import gate as G
from . import sim
from . import world as W
from .world_experiments import mean

ALPHA = 0.05 / 4
LABELS = ["BASE", "R", "D", "S", "S>R", "S>D"]
NONBASE = LABELS[1:]
SIZES = (4, 8, 16)
REPS = 20
PILOT_A, PILOT_B, DEPLOY_TICKS, SRC_TICKS = 10, 20, 60, 60
MARGIN = 0.01
DIRECTIONS = [("agent", "person"), ("person", "agent"), ("agent_v2", "person"), ("person", "agent_v2")]

ENV = {"person": lambda s: W.PersonEnv(s), "agent": lambda s: W.AgentEnv(s), "agent_v2": lambda s: W.AgentEnvV2(s),
       "person_alt": lambda s: W.PersonEnv(s, model=dict(sim.FULL, dilution=False))}
BASE_OF = {"person": "person", "person_alt": "person", "agent": "agent", "agent_v2": "agent_v2"}
SRC_ROLE = {"person": 12300, "agent": 12400, "agent_v2": 12500}
SRC_POL = {"person": 12000, "agent": 12100, "agent_v2": 12200}
PILOT0 = {"person": 13000, "agent": 14000, "agent_v2": 15000}
DEPLOY0 = {"person": 16000, "agent": 16200, "agent_v2": 16400}
ORACLE0 = {"person": 17000, "agent": 17100, "agent_v2": 17200}
_cache: dict = {}


def policy(label, roles):
    r = lambda k: roles.get(k, "LION")
    return {"BASE": W.RolePolicy("hold", "LION"), "R": W.RolePolicy("hold", r("RESTORE")),
            "D": W.RolePolicy("hold", r("DRIVE")), "S": W.RolePolicy("hold", r("STABILISE")),
            "S>R": W.RolePolicy("split", r("STABILISE"), r("RESTORE")),
            "S>D": W.RolePolicy("split", r("STABILISE"), r("DRIVE"))}[label]


def read_roles(env, seeds, ticks):
    comps = []
    for s in seeds:
        w = W.World(ENV[env](s), "random", seed=s, score="mission")
        w.run(ticks)
        comps += w.comps3
    return G.roles3(comps)


def deploy_scores(env, pol, seeds):
    key = (env, pol.key, seeds[0], len(seeds))
    if key not in _cache:
        out = []
        for s in seeds:
            w = W.World(ENV[env](s), pol, seed=s, score="mission")
            w.run(DEPLOY_TICKS)
            out.append(mean([t[2] for t in w.trace]))
        _cache[key] = out
    return _cache[key]


def pilot_run(env, seeds, assign):
    """Stage A (random archetypes) for all targets, roles read from it, then stage B with assign(i) -> label."""
    ws = []
    for s in seeds:
        w = W.World(ENV[env](s), "random", seed=s, score="mission")
        w.run(PILOT_A)
        ws.append(w)
    roles = G.roles3(c for w in ws for c in w.comps3)
    groups: dict = {}
    for i, w in enumerate(ws):
        lab = assign(i)
        w.policy = policy(lab, roles)
        w.run(PILOT_B)
        groups.setdefault(lab, []).append(mean([t[2] for t in w.trace[PILOT_A:]]))
    return roles, groups


def decide_transfer(env, seeds, label):
    roles, g = pilot_run(env, seeds, lambda i: label if i % 2 == 0 else "BASE")
    _, lb = G.welch_lower(g.get(label, []), g.get("BASE", []), ALPHA)
    return policy(label if lb is not None and lb > 0 else "BASE", roles), {"roles": roles, "bound": lb}


def decide_pilot_only(env, seeds):
    roles, g = pilot_run(env, seeds, lambda i: LABELS[i % 6])
    ok = {k: v for k, v in g.items() if len(v) >= 2 and k != "BASE"}
    if len(g.get("BASE", [])) < 2 or not ok:
        return policy("BASE", roles), {"roles": roles, "chosen": None, "bound": None}
    best = max(ok, key=lambda k: mean(ok[k]))
    _, lb = G.welch_lower(ok[best], g["BASE"], ALPHA / 5)
    return policy(best if lb is not None and lb > 0 else "BASE", roles), {"roles": roles, "chosen": best, "bound": lb}


def ci(xs, ys, level=1 - ALPHA, boot=2000, seed=12345):
    d = [x - y for x, y in zip(xs, ys)]
    n = len(d)
    rng = random.Random(seed)
    ms = sorted(sum(d[rng.randrange(n)] for _ in range(n)) / n for _ in range(boot))
    a = (1 - level) / 2
    return {"diff": sum(d) / n, "lo": ms[int(a * boot)], "hi": ms[min(boot - 1, int((1 - a) * boot))]}


def source_choice(src, shift):
    base = BASE_OF[src]
    roles = read_roles(src, range(SRC_ROLE[base] + shift, SRC_ROLE[base] + shift + 50), SRC_TICKS)
    seeds = list(range(SRC_POL[base] + shift, SRC_POL[base] + shift + 50))
    vals = {lab: mean(deploy_scores(src, policy(lab, roles), seeds)) for lab in LABELS}
    return max(vals, key=vals.get), roles, vals


def direction(src, tgt, size, label, shift=0, quick=False):
    base = BASE_OF[tgt]
    dseeds = list(range(DEPLOY0[base] + shift, DEPLOY0[base] + shift + (20 if quick else 200)))
    reps = 3 if quick else REPS
    arms = {"TRANSFER": [], "PILOT-ONLY": [], "RANDOM-POLICY": []}
    log = []
    for r in range(reps):
        seeds = list(range(PILOT0[base] + shift + 16 * r, PILOT0[base] + shift + 16 * r + size))
        pt, it = decide_transfer(tgt, seeds, label)
        pp, ip = decide_pilot_only(tgt, seeds)
        rand = [decide_transfer(tgt, seeds, lab)[0] for lab in NONBASE]
        arms["TRANSFER"].append(deploy_scores(tgt, pt, dseeds))
        arms["PILOT-ONLY"].append(deploy_scores(tgt, pp, dseeds))
        arms["RANDOM-POLICY"].append([mean(v) for v in zip(*[deploy_scores(tgt, p, dseeds) for p in rand])])
        log.append({"rep": r, "transfer": pt.key, "transfer_bound": it["bound"], "pilot_only": pp.key,
                    "pilot_only_choice": ip["chosen"], "roles": it["roles"]})
    per = {k: [mean(col) for col in zip(*v)] for k, v in arms.items()}
    per["NONE"] = deploy_scores(tgt, policy("BASE", {}), dseeds)
    oroles = read_roles(tgt, range(ORACLE0[base] + shift, ORACLE0[base] + shift + (10 if quick else 50)), SRC_TICKS)
    ovals = {lab: mean(deploy_scores(tgt, policy(lab, oroles), dseeds)) for lab in LABELS}
    con = {f"TRANSFER-{o}": ci(per["TRANSFER"], per[o]) for o in ("PILOT-ONLY", "NONE", "RANDOM-POLICY")}
    beats = all(c["lo"] > 0 for c in con.values())
    nonin = ci(per["TRANSFER"], per["NONE"], level=0.95)["lo"] > -MARGIN
    adopted = sum(1 for e in log if e["transfer"] != ("hold", "LION", None))
    return {"source": src, "target": tgt, "size": size, "label": label, "arms": {k: mean(v) for k, v in per.items()},
            "oracle_policies": ovals, "oracle": max(ovals.values()), "contrasts": con, "beats_all": beats,
            "noninferior": nonin, "transfer_adopted": f"{adopted}/{reps}",
            "pilot_only_adopted": f"{sum(1 for e in log if e['pilot_only'] != ('hold', 'LION', None))}/{reps}",
            "log": log}


def run(quick=False):
    labels, src_info = {}, {}
    for src in ("person", "agent", "agent_v2"):
        lab, roles, vals = source_choice(src, 0)
        labels[src], src_info[src] = lab, {"label": lab, "roles": roles, "values": vals}
    runs = [direction(s, t, n, labels[s], 0, quick) for s, t in DIRECTIONS for n in SIZES]
    at8 = [r for r in runs if r["size"] == 8]
    primary = sum(r["beats_all"] for r in at8) >= 2 and all(r["noninferior"] for r in at8)
    conf = []
    if primary:
        shift = 100000
        for r in at8:
            if not r["beats_all"]:
                continue
            s = "person_alt" if r["source"] == "person" else r["source"]
            t = "person_alt" if r["target"] == "person" else r["target"]
            lab, roles, vals = source_choice(s, shift)
            c = direction(s, t, 8, lab, shift, quick)
            c["source_values"] = vals
            conf.append(c)
    confirmed = primary and conf and all(c["beats_all"] and c["noninferior"] for c in conf)
    return {"source": src_info, "runs": runs, "primary_pass": primary, "confirmation": conf,
            "pass": bool(confirmed)}


def fmt(c):
    return f"{c['diff']:+.4f} [{c['lo']:+.4f}, {c['hi']:+.4f}]"


def report(R) -> str:
    L = ["# W3c — policy-level transfer tested as deployed: results", "",
         "Designs, seeds and criteria were fixed in [`../AGENTS.md`](../AGENTS.md) §11.4 and committed before this code was",
         "written. Fourth attempt at positive transfer: confirmatory intervals are at 98.75% (level 0.05 / 4). All",
         "environments are stated models; **no number here comes from people or production agents.** Mission score per tick;",
         "each arm's value is averaged over 20 pilot repetitions, then compared paired over 200 deployment targets.", "",
         "| Source | Transferred policy | Roles on the source | Policy values on the source |", "|---|---|---|---|"]
    for k, v in R["source"].items():
        L.append(f"| {k} | {v['label']} | `{json.dumps(v['roles'])}` | "
                 + ", ".join(f"{a} {b:+.3f}" for a, b in v["values"].items()) + " |")
    L.append("")

    def block(r, title):
        out = [f"## {title}", "",
               f"Transferred: `{r['label']}`. Adopted by the TRANSFER pilot in {r['transfer_adopted']} repetitions; "
               f"PILOT-ONLY adopted a policy in {r['pilot_only_adopted']}.", "",
               "| Arm | Mean / tick |", "|---|---|"] + [f"| {k} | {v:+.4f} |" for k, v in r["arms"].items()]
        out += [f"| ORACLE (upper bound) | {r['oracle']:+.4f} |", "", "| Contrast (98.75% interval) | Estimate |", "|---|---|"]
        out += [f"| {k} | {fmt(c)} |" for k, c in r["contrasts"].items()]
        out += ["", f"Beats PILOT-ONLY, NONE and RANDOM-POLICY: **{'yes' if r['beats_all'] else 'no'}**. Non-inferior to "
                f"NONE: {'yes' if r['noninferior'] else 'no'}.", ""]
        return out
    for r in R["runs"]:
        L += block(r, f"{r['source']} → {r['target']}, pilot of {r['size']}")
    L += [f"**Primary criterion (pilot 8): {'PASS' if R['primary_pass'] else 'FAIL'}.**", ""]
    if R["confirmation"]:
        L += ["# Confirmation run (seeds +100000; person model with attention dilution off)", ""]
        for r in R["confirmation"]:
            L += block(r, f"Confirmation: {r['source']} → {r['target']}, pilot of 8")
    L += [f"**W3c overall (primary and confirmation): {'PASS' if R['pass'] else 'FAIL'}.**", ""]
    return "\n".join(L) + "\n"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    quick = "--quick" in argv
    R = run(quick)
    if not quick:
        out = pathlib.Path(__file__).resolve().parents[1] / "results"
        (out / "results_w3c.json").write_text(json.dumps(R, indent=1, sort_keys=True, default=str) + "\n")
        md = out / "w3c.md"
        keep = ""
        if md.exists() and "## What these results show" in md.read_text():
            keep = md.read_text()[md.read_text().index("## What these results show"):]
        md.write_text(report(R) + keep)
    return R


if __name__ == "__main__":
    print(report(main()))
