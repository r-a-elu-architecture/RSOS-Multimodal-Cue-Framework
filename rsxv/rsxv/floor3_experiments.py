"""Floor 3 experiments (G1, G2) and H-CFIT-M, exactly as fixed in AGENTS.md §11.2.

    python3 -m rsxv.floor3_experiments          # writes results/results_floor3.json and results/floor3.md
"""
from __future__ import annotations

import itertools
import json
import pathlib
import sys

from . import gate as G
from . import world as W
from .world_experiments import fmt_ci, hcfit as _hcfit, mean, paired_ci, pooled_table, permuted

ENVS = {"person": W.PersonEnv, "agent": W.AgentEnv, "agent_v2": W.AgentEnvV2}
PILOT = {"person": range(7000, 7020), "agent": range(7100, 7120), "agent_v2": range(7200, 7220)}
DEPLOY = {"person": range(8000, 8200), "agent": range(8200, 8400), "agent_v2": range(8400, 8600)}
TRUTH = {"person": range(9000, 9200), "agent": range(9200, 9400), "agent_v2": range(9400, 9600)}
PILOT_TICKS, DEPLOY_TICKS, TRUTH_TICKS = 30, 60, 60
MARGIN = 0.01
PERMS = [p for p in itertools.permutations(range(len(W.CONTEXTS))) if list(p) != list(range(len(W.CONTEXTS)))]


def random_cohort(env, seeds, ticks):
    traces = []
    for s in seeds:
        w = W.World(ENVS[env](s), "random", seed=s, score="mission")
        w.run(ticks)
        traces.append(w.trace)
    return G.cells(traces)


def deploy_scores(env, table, seeds=None):
    seeds = DEPLOY[env] if seeds is None else seeds
    out = []
    for s in seeds:
        w = W.World(ENVS[env](s), table, seed=s, score="mission")
        w.run(DEPLOY_TICKS)
        out.append(mean([t[2] for t in w.trace]))
    return out


def direction(name, table, target, pilot, truth, quick=False):
    seeds = list(DEPLOY[target])[:20] if quick else DEPLOY[target]
    gated, vmap = G.gate(table, pilot)
    eff = G.truth_effects(truth)
    for row in vmap:
        te = eff.get((row["context"], row["candidate"]), 0.0 if row["candidate"] == G.BASELINE else None)
        row["truth"] = te
        row["false_admit"] = row["decision"].startswith("admit") and row["candidate"] != G.BASELINE and te is not None and te < 0
    arms = {"GATED": deploy_scores(target, gated, seeds), "UNGATED": deploy_scores(target, table, seeds),
            "NONE": deploy_scores(target, "fixed", seeds)}
    shuffled_tables = [G.gate(permuted(table, p), pilot)[0] for p in PERMS]
    distinct = {json.dumps(t, sort_keys=True): t for t in shuffled_tables}
    per_table = {k: deploy_scores(target, t, seeds) for k, t in distinct.items()}
    arms["SHUFFLED-GATED"] = [mean([per_table[json.dumps(t, sort_keys=True)][i] for t in shuffled_tables])
                              for i in range(len(seeds))]
    c = {f"GATED-{o}": paired_ci(arms["GATED"], arms[o]) for o in ("UNGATED", "NONE", "SHUFFLED-GATED")}
    full = gated == {k: table.get(k, G.BASELINE) for k in W.CONTEXTS}
    res = {"name": name, "table": table, "gated": gated, "validity_map": vmap, "n": len(seeds),
           "arms": {k: mean(v) for k, v in arms.items()}, "contrasts": c, "full_table_admitted": full,
           "crit_vs_ungated": full or c["GATED-UNGATED"]["lo"] > 0,
           "crit_noninferior": c["GATED-NONE"]["lo"] > -MARGIN,
           "useful": c["GATED-NONE"]["lo"] > 0, "beats_shuffled": c["GATED-SHUFFLED-GATED"]["lo"] > 0}
    res["pass"] = res["crit_vs_ungated"] and res["crit_noninferior"]
    return res


def run(quick=False):
    k = 5 if quick else 1
    pilot = {e: random_cohort(e, list(PILOT[e])[: 20 // k], PILOT_TICKS) for e in ENVS}
    truth = {e: random_cohort(e, list(TRUTH[e])[: 200 // k], TRUTH_TICKS) for e in ENVS}
    # G1: the W3 tables, with W3's seeds and reward (legacy)
    t_a2p = pooled_table(lambda s: W.AgentEnv(s), range(0, 50 // k), 300)
    t_p2a = pooled_table(lambda s: W.PersonEnv(s), range(3000, 3000 + 50 // k), 300)
    # G2: v2 tables learned under the mission score
    t_a2p_v2 = mission_table(W.AgentEnvV2, range(6000, 6000 + 50 // k))
    t_p2a_v2 = mission_table(W.PersonEnv, range(6100, 6100 + 50 // k))
    R = {"G1": {"agents_to_person": direction("G1 agents → person", t_a2p, "person", pilot["person"], truth["person"], quick),
                "person_to_agents": direction("G1 person → agents", t_p2a, "agent", pilot["agent"], truth["agent"], quick)},
         "G2": {"agents_to_person": direction("G2 agents(v2) → person", t_a2p_v2, "person", pilot["person"], truth["person"], quick),
                "person_to_agents": direction("G2 person → agents(v2)", t_p2a_v2, "agent_v2", pilot["agent_v2"], truth["agent_v2"], quick)}}
    g2 = R["G2"]
    R["G2_pass"] = all(d["pass"] for d in g2.values()) and any(d["useful"] and d["beats_shuffled"] for d in g2.values())
    R["G1_pass"] = all(d["pass"] for d in R["G1"].values())
    R["false_admits"] = sum(r["false_admit"] for g in ("G1", "G2") for d in R[g].values() for r in d["validity_map"])
    R["admitted_changes"] = sum(1 for g in ("G1", "G2") for d in R[g].values() for r in d["validity_map"]
                                if r["decision"] == "admit")
    return R


def mission_table(env_cls, seeds):
    pool = W.FitLedger()
    for s in seeds:
        w = W.World(env_cls(s), "watchdog", seed=s, score="mission")
        w.run(300)
        for key, n in w.ledger.n.items():
            pool.n[key] = pool.n.get(key, 0) + n
            pool.s[key] = pool.s.get(key, 0.0) + w.ledger.s[key]
            pool.ss[key] = pool.ss.get(key, 0.0) + w.ledger.ss[key]
    return pool.table()


def hcfit_m(quick=False):
    import rsxv.world as Wm
    orig = Wm.World.__init__

    def init(self, *a, **kw):
        kw.setdefault("score", "mission")
        orig(self, *a, **kw)
    Wm.World.__init__ = init
    try:
        return _hcfit(range(5000, 5020 if quick else 5200))
    finally:
        Wm.World.__init__ = orig


def report(R, H) -> str:
    L = ["# Floor 3 — certified cross-substrate transfer: results", "",
         "Designs, seeds and pass criteria were fixed in [`../AGENTS.md`](../AGENTS.md) §11.2 and committed before this code",
         "was written. All environments are stated models; **no number here comes from people or production agents.** Scores",
         "are the mission score (gain − 2 × harm rise − spike). Intervals: paired bootstrap, 2,000 resamples, 95%. Within a gate",
         "cell, ticks are treated as independent (disclosed simplification).", ""]
    for g in ("G1", "G2"):
        for d in R[g].values():
            L += [f"## {d['name']}", "", f"Source table: `{json.dumps(d['table'])}`. Gated table: `{json.dumps(d['gated'])}`.", "",
                  "| Context | Candidate | Decision | Pilot estimate | Lower bound | Truth estimate | False admit | n (cand / base) |",
                  "|---|---|---|---|---|---|---|---|"]
            for r in d["validity_map"]:
                f = lambda x: "—" if x is None else f"{x:+.3f}"
                L.append(f"| {r['context']} | {r['candidate']} | {r['decision']} | {f(r['estimate'])} | {f(r['bound'])} | "
                         f"{f(r['truth'])} | {'yes' if r['false_admit'] else 'no'} | {r['n_candidate']} / {r['n_baseline']} |")
            L += ["", "| Arm | Mean mission score / tick |", "|---|---|"] + [f"| {k} | {v:+.4f} |" for k, v in d["arms"].items()]
            L += ["", "| Contrast | Estimate [95% interval] |", "|---|---|"] + [f"| {k} | {fmt_ci(c)} |" for k, c in d["contrasts"].items()]
            vac = " (full table admitted: criterion vacuous)" if d["full_table_admitted"] else ""
            L += ["", f"Better than ungated{vac}: {'yes' if d['crit_vs_ungated'] else 'no'}. Non-inferior to no transfer "
                  f"(margin {MARGIN}): {'yes' if d['crit_noninferior'] else 'no'}. Useful (beats no transfer): "
                  f"{'yes' if d['useful'] else 'no'}. Beats shuffled: {'yes' if d['beats_shuffled'] else 'no'}. "
                  f"**{'PASS' if d['pass'] else 'FAIL'}.**", ""]
    L += [f"**G1: {'PASS' if R['G1_pass'] else 'FAIL'}. G2: {'PASS' if R['G2_pass'] else 'FAIL'}.** "
          f"False admits: {R['false_admits']} of {R['admitted_changes']} admitted changes.", ""]
    L += ["## H-CFIT under the mission score (H-CFIT-M)", "", f"{H['n']} simulated persons, {H['ticks']} ticks.", "",
          "| Arm | Mean mission score / tick | Ticks 61–120 | Final distress | Switches |", "|---|---|---|---|---|"]
    L += [f"| {k} | {a['all']:+.4f} | {a['late']:+.4f} | {a['distress']:.2f} | {a['switches']:.1f} |" for k, a in H["arms"].items()]
    L += ["", "| Contrast | Estimate [95% interval] |", "|---|---|"] + [f"| {k} | {fmt_ci(c)} |" for k, c in H["contrasts"].items()]
    L += ["", f"**{'PASS' if H['pass'] else 'FAIL'}.**", ""]
    return "\n".join(L) + "\n"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    quick = "--quick" in argv
    R, H = run(quick), hcfit_m(quick)
    if not quick:
        out = pathlib.Path(__file__).resolve().parents[1] / "results"
        (out / "results_floor3.json").write_text(json.dumps({"floor3": R, "hcfit_m": H}, indent=1, sort_keys=True,
                                                            default=str) + "\n")
        md = out / "floor3.md"
        keep = ""
        if md.exists() and "## What these results show" in md.read_text():
            keep = md.read_text()[md.read_text().index("## What these results show"):]
        md.write_text(report(R, H) + keep)
    return R, H


if __name__ == "__main__":
    R, H = main()
    print(report(R, H))
