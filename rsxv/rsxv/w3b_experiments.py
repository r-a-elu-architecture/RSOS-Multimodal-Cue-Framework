"""W3b, role-based transfer with gate v2, exactly as fixed in AGENTS.md §11.3.

    python3 -m rsxv.w3b_experiments          # writes results/results_w3b.json and results/w3b.md
"""
from __future__ import annotations

import itertools
import json
import pathlib
import random
import sys

from . import gate as G
from . import world as W
from .floor3_experiments import ENVS, TRUTH, TRUTH_TICKS, mission_table, random_cohort
from .world_experiments import fmt_ci, mean, paired_ci

SOURCE_TABLE_SEEDS = {"person": range(6100, 6150), "agent": range(6200, 6250), "agent_v2": range(6000, 6050)}
SOURCE_ROLE_SEEDS = {"person": range(6300, 6350), "agent": range(6400, 6450), "agent_v2": range(6500, 6550)}
PILOT_SEEDS = {"person": range(10000, 10020), "agent": range(10100, 10120), "agent_v2": range(10200, 10220)}
DEPLOY_SEEDS = {"person": range(11000, 11200), "agent": range(11200, 11400), "agent_v2": range(11400, 11600)}
DIRECTIONS = [("agent", "person"), ("person", "agent"), ("agent_v2", "person"), ("person", "agent_v2")]
SIZES = (5, 10, 20)
PILOT_TICKS, DEPLOY_TICKS, ROLE_TICKS = 30, 60, 60
MARGIN = 0.01
A4, A20 = 0.05 / 4, 0.05 / 20
PERMS = [p for p in itertools.permutations(range(4)) if list(p) != list(range(4))]
_cache: dict = {}


def worlds(env, seeds, ticks, policy="random"):
    out = []
    for s in seeds:
        w = W.World(ENVS[env](s), policy, seed=s, score="mission")
        w.run(ticks)
        out.append(w)
    return out


def deploy(env, table, seeds):
    key = (env, json.dumps(table, sort_keys=True), seeds[0], len(seeds))
    if key not in _cache:
        sc = []
        for s in seeds:
            w = W.World(ENVS[env](s), table, seed=s, score="mission")
            w.run(DEPLOY_TICKS)
            sc.append(mean([t[2] for t in w.trace]))
        _cache[key] = sc
    return _cache[key]


def best_per_context(cells):
    out = {}
    for c in W.CONTEXTS:
        ms = {m: mean(cells[(c, m)]) for m in W.MODES if cells.get((c, m))}
        out[c] = max(ms, key=ms.get) if ms else G.BASELINE
    return out


def permute(rt, p):
    return {W.CONTEXTS[i]: rt[W.CONTEXTS[p[i]]] for i in range(4)}


def role_pipeline(rtable, troles, cellsB):
    return G.gate_v2(G.from_roles(rtable, troles), cellsB, alpha=A4)


def one(src, tgt, size, src_table, src_roles, truth_eff, oracle, quick):
    seeds = list(DEPLOY_SEEDS[tgt])[: 20 if quick else 200]
    pilot = worlds(tgt, list(PILOT_SEEDS[tgt])[:size], PILOT_TICKS)
    half_a, half_b = pilot[1::2], pilot[0::2]
    cells_all = G.cells(w.trace for w in pilot)
    cells_a, cells_b = G.cells(w.trace for w in half_a), G.cells(w.trace for w in half_b)
    troles = G.roles(c for w in half_a for c in w.comps)
    rtable = G.role_table(src_table, src_roles)
    tables, vmaps = {}, {}
    tables["ROLE"], vmaps["ROLE"] = role_pipeline(rtable, troles, cells_b)
    tables["PILOT-BONF"], vmaps["PILOT-BONF"] = G.gate_v2(best_per_context(cells_all), cells_all, alpha=A20)
    tables["PILOT-SPLIT"], vmaps["PILOT-SPLIT"] = G.gate_v2(best_per_context(cells_a), cells_b, alpha=A4)
    tables["NAME-GATED"], vmaps["NAME-GATED"] = G.gate_v2(src_table, cells_all, alpha=A4)
    tables["NONE"], tables["ORACLE"] = "fixed", oracle
    arms = {k: deploy(tgt, t, seeds) for k, t in tables.items()}
    rr = [role_pipeline(_random_rt(i), troles, cells_b)[0] for i in range(20)]
    arms["ROLE-RANDOM"] = [mean(v) for v in zip(*[deploy(tgt, t, seeds) for t in rr])]
    rs = [role_pipeline(permute(rtable, p), troles, cells_b)[0] for p in PERMS]
    arms["ROLE-SHUFFLED"] = [mean(v) for v in zip(*[deploy(tgt, t, seeds) for t in rs])]
    con = {f"ROLE-{o}": paired_ci(arms["ROLE"], arms[o]) for o in
           ("NONE", "PILOT-BONF", "PILOT-SPLIT", "ROLE-RANDOM", "ROLE-SHUFFLED", "NAME-GATED", "ORACLE")}
    for row in vmaps["ROLE"]:
        te = truth_eff.get((row["context"], row["candidate"]), 0.0 if row["candidate"] == G.BASELINE else None)
        row["truth"] = te
        row["false_admit"] = row["decision"] == "admit" and te is not None and te < 0
    beats = all(con[f"ROLE-{o}"]["lo"] > 0 for o in ("NONE", "PILOT-BONF", "PILOT-SPLIT", "ROLE-RANDOM"))
    return {"source": src, "target": tgt, "size": size, "source_table": src_table, "source_roles": src_roles,
            "role_table": rtable, "target_roles": troles, "tables": tables, "validity_map_role": vmaps["ROLE"],
            "arms": {k: mean(v) for k, v in arms.items()}, "contrasts": con, "beats_all": beats,
            "noninferior": con["ROLE-NONE"]["lo"] > -MARGIN,
            "false_admits": sum(r["false_admit"] for r in vmaps["ROLE"]),
            "admitted": sum(r["decision"] == "admit" for r in vmaps["ROLE"])}


def _random_rt(i):
    r = random.Random(i)
    return {c: r.choice(["RESTORE", "DRIVE", "BASELINE"]) for c in W.CONTEXTS}


def run(quick=False):
    k = 5 if quick else 1
    src_tables = {e: mission_table(ENVS[e], list(SOURCE_TABLE_SEEDS[e])[: 50 // k]) for e in ENVS}
    src_roles = {e: G.roles(c for w in worlds(e, list(SOURCE_ROLE_SEEDS[e])[: 50 // k], ROLE_TICKS) for c in w.comps)
                 for e in ENVS}
    truth = {e: random_cohort(e, list(TRUTH[e])[: 200 // k], TRUTH_TICKS) for e in ("person", "agent", "agent_v2")}
    truth_eff = {e: G.truth_effects(t) for e, t in truth.items()}
    oracle = {e: {c: max([G.BASELINE] + [m for m in W.MODES if (c, m) in truth_eff[e]],
                         key=lambda m: truth_eff[e].get((c, m), 0.0)) for c in W.CONTEXTS} for e in truth_eff}
    res = []
    for src, tgt in DIRECTIONS:
        for size in SIZES:
            res.append(one(src, tgt, size, src_tables[src], src_roles[src], truth_eff[tgt], oracle[tgt], quick))
    at = lambda n: [r for r in res if r["size"] == n]
    out = {"runs": res, "source_tables": src_tables, "source_roles": src_roles, "oracle": oracle,
           "pass": sum(r["beats_all"] for r in at(10)) >= 2 and all(r["noninferior"] for r in at(10)),
           "strong_pass": sum(r["beats_all"] for r in at(5)) >= 2 and all(r["noninferior"] for r in at(5)),
           "false_admits": sum(r["false_admits"] for r in res), "admitted": sum(r["admitted"] for r in res)}
    return out


def report(R) -> str:
    L = ["# W3b — role-based transfer: results", "",
         "Designs, seeds and pass criteria were fixed in [`../AGENTS.md`](../AGENTS.md) §11.3 and committed before this code",
         "was written. The hypothesis came from an exploratory look at the floor-3 truth cohorts (disclosed there). All",
         "environments are stated models; **no number here comes from people or production agents.** Mission score per tick;",
         "paired bootstrap 95% intervals over 200 deployment targets.", "",
         f"Source roles: `{json.dumps(R['source_roles'])}`.", f"Source tables: `{json.dumps(R['source_tables'])}`.", ""]
    for r in R["runs"]:
        L += [f"## {r['source']} → {r['target']}, pilot of {r['size']} targets", "",
              f"Role table: `{json.dumps(r['role_table'])}`. Target roles (half A): `{json.dumps(r['target_roles'])}`. "
              f"ROLE deployed: `{json.dumps(r['tables']['ROLE'])}`.", "",
              "| Arm | Mean / tick |", "|---|---|"] + [f"| {k} | {v:+.4f} |" for k, v in r["arms"].items()]
        L += ["", "| Contrast | Estimate [95% interval] |", "|---|---|"] + [f"| {k} | {fmt_ci(c)} |" for k, c in r["contrasts"].items()]
        L += ["", "| Context | Candidate | Decision | Pilot est. | Bound | Truth | False admit |", "|---|---|---|---|---|---|---|"]
        f = lambda x: "—" if x is None else f"{x:+.3f}"
        L += [f"| {v['context']} | {v['candidate']} | {v['decision']} | {f(v['estimate'])} | {f(v['bound'])} | {f(v['truth'])} | "
              f"{'yes' if v['false_admit'] else 'no'} |" for v in r["validity_map_role"]]
        L += ["", f"Beats NONE, PILOT-BONF, PILOT-SPLIT and ROLE-RANDOM: **{'yes' if r['beats_all'] else 'no'}**. "
              f"Non-inferior to NONE: {'yes' if r['noninferior'] else 'no'}.", ""]
    L += [f"**Registered criterion (pilot 10): {'PASS' if R['pass'] else 'FAIL'}. Strong (pilot 5): "
          f"{'PASS' if R['strong_pass'] else 'FAIL'}.** False admits in ROLE: {R['false_admits']} of {R['admitted']} admitted.", ""]
    return "\n".join(L) + "\n"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    quick = "--quick" in argv
    R = run(quick)
    if not quick:
        out = pathlib.Path(__file__).resolve().parents[1] / "results"
        (out / "results_w3b.json").write_text(json.dumps(R, indent=1, sort_keys=True, default=str) + "\n")
        md = out / "w3b.md"
        keep = ""
        if md.exists() and "## What these results show" in md.read_text():
            keep = md.read_text()[md.read_text().index("## What these results show"):]
        md.write_text(report(R) + keep)
    return R


if __name__ == "__main__":
    print(report(main()))
