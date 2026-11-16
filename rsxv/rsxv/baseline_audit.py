"""BASELINE_AUDIT: each passed RSX-V register row against its simplest baseline. Design and rule: spec/BASELINE_AUDIT.md,
registered before this code. Re-uses each test's own procedure and seeds; checks reproduction before comparing.

    python3 -m rsxv.baseline_audit            # writes results/results_baseline_audit.json and results/baseline_audit.md
    python3 -m rsxv.baseline_audit --quick    # smoke run, nothing written
"""
from __future__ import annotations

import json
import math
import pathlib
import sys

from . import world as W
from .world_experiments import mean, paired_ci

HERE = pathlib.Path(__file__).resolve().parents[1]
STAB = "STABILISE"


# ------------------------------------------------------------------------------------------------ pure rules (tested)
def outcome(lo, hi, identical=False):
    """§4: HOLDS if the lower bound is above 0, LOSES if the upper bound is below 0, otherwise TIES."""
    if identical:
        return "TIES"
    if lo > 0:
        return "HOLDS"
    if hi < 0:
        return "LOSES"
    return "TIES"


def stab_only_table(troles: dict) -> dict:
    """§2.3: the target's STABILISE archetype in every context; LION everywhere if none was read."""
    a = troles.get(STAB) or "LION"
    return {c: a for c in W.CONTEXTS}


def fixed_best(pilot_means: dict) -> str:
    """§2.1: the mode with the highest pilot mean (ties broken by W.MODES order)."""
    return max(W.MODES, key=lambda m: (pilot_means[m], -W.MODES.index(m)))


def mcnemar_one_sided(b: int, c: int) -> float:
    """Exact one-sided McNemar: b = pairs where only the method is right, c = only the baseline is right.
    p = P(X >= b) for X ~ Binomial(b + c, 1/2)."""
    n = b + c
    if n == 0:
        return 1.0
    return sum(math.comb(n, k) for k in range(b, n + 1)) / 2 ** n


# ------------------------------------------------------------------------------------------------ A3 / A4
def _session(seed, policy, score, ticks=120, fixed_mode="LION"):
    w = W.World(W.PersonEnv(seed), policy, seed=seed, score=score, fixed_mode=fixed_mode)
    w.run(ticks)
    return mean(w.rewards)


def fixed_best_audit(name, score, test_seeds, pilot_seeds, recorded):
    pilot = {m: mean([_session(s, "fixed", score, fixed_mode=m) for s in pilot_seeds]) for m in W.MODES}
    pick = fixed_best(pilot)
    wd = [_session(s, "watchdog", score) for s in test_seeds]
    fb = [_session(s, "fixed", score, fixed_mode=pick) for s in test_seeds]
    each = {m: mean([_session(s, "fixed", score, fixed_mode=m) for s in test_seeds]) for m in W.MODES}
    reproduced = recorded is None or round(mean(wd), 6) == round(recorded, 6)
    c = paired_ci(wd, fb)
    return {"id": name, "baseline": f"FIXED-BEST ({pick})", "pilot_means": pilot, "chosen": pick,
            "method_mean": mean(wd), "baseline_mean": mean(fb), "contrast": c, "fixed_on_test_info_only": each,
            "reproduced": reproduced, "outcome": outcome(c["lo"], c["hi"]) if reproduced else "NOT REPRODUCED"}


# ------------------------------------------------------------------------------------------------ A6
def j1_audit(quick=False):
    from . import j1_calibration as J      # sets J1's own seed ranges on the W5d module
    M = J.M
    certs = {}
    for src in ("person", "agent", "agent_v2"):
        certs[src], _ = M.certificates(src, 0)
        M.WARNS[src] = M.LAST_WARN
    te = {t: M.truth(t) for t in ("person", "agent", "agent_v2")}
    rows = []
    for src, tgt in M.DIRECTIONS:
        M.CUR_WARN = M.WARNS.get(src, {})
        base = M.BASE_OF[tgt]
        sp_t = M.TRUTH_SPK[tgt]
        rate = lambda k: (sum(sp_t[k]) / len(sp_t[k])) if sp_t.get(k) else 0.0
        for r in range(2 if quick else 20):
            seeds = list(range(M.PILOT0[base] + 16 * r, M.PILOT0[base] + 16 * r + 8))
            troles = M.read_target_roles(tgt, seeds)
            wa = M.warned_arch(troles)
            cand = M.cand_from_certs(certs[src], troles)
            cand = {c: ("LION" if a in wa.get(c, ()) else a) for c, a in cand.items()}
            cells, _ = M.pilot(tgt, seeds, cand, True, warned=wa)
            spk = dict(M.SPK)
            for c, a in cand.items():
                if a == "LION":
                    continue
                xa, xb = cells.get((c, a), []), cells.get((c, "LION"), [])
                rows.append({"pred": J.j1(cells, spk, c, a),
                             "pred_mean_only": len(xa) < 5 or len(xb) < 5 or mean(xa) <= mean(xb),
                             "truth": te[tgt].get((c, a), 0.0) <= 0 or rate((c, a)) > rate((c, "LION"))})
    n = len(rows)
    acc = sum(x["pred"] == x["truth"] for x in rows) / n
    never = sum(not x["truth"] for x in rows) / n
    mean_only = sum(x["pred_mean_only"] == x["truth"] for x in rows) / n
    b = sum(x["pred"] == x["truth"] and x["truth"] for x in rows)        # J1 right, never-jam wrong
    c = sum(x["pred"] != x["truth"] and not x["truth"] for x in rows)    # never-jam right, J1 wrong
    p = mcnemar_one_sided(b, c)
    reproduced = quick or (n == 260 and round(acc, 3) == 0.754)
    out = "HOLDS" if p < 0.01 else ("LOSES" if mcnemar_one_sided(c, b) < 0.01 else "TIES")
    return {"id": "A6 J1", "baseline": "NEVER-JAM", "n": n, "accuracy": acc, "never_jam": never,
            "mean_only_info_only": mean_only, "discordant": {"j1_only": b, "never_jam_only": c}, "p_one_sided": p,
            "reproduced": reproduced, "outcome": out if reproduced else "NOT REPRODUCED"}


# ------------------------------------------------------------------------------------------------ A7
def tap_audit(quick=False):
    from . import tap_experiments as T      # sets T-AP's level and seed ranges on the W5c module
    M = T.M
    runs = {}
    for label, shift, tgt, recorded in (("primary", 0, "person", 0.1113), ("confirmation", 100000, "person_v2", 0.0872)):
        certs, _ = M.certificates("agent", shift)
        base = M.BASE_OF[tgt]
        dseeds = list(range(M.DEPLOY0[base] + shift, M.DEPLOY0[base] + shift + (20 if quick else 200)))
        tap, stab, tables = [], [], []
        for r in range(2 if quick else M.REPS):
            seeds = list(range(M.PILOT0[base] + shift + 16 * r, M.PILOT0[base] + shift + 16 * r + 8))
            g5, _ = M.decide_w5(tgt, seeds, certs)
            tab = stab_only_table(M.read_target_roles(tgt, seeds))
            tables.append(tab)
            tap.append(M.deploy(tgt, M.TablePolicy(g5), dseeds)[0])
            stab.append(M.deploy(tgt, M.TablePolicy(tab), dseeds)[0])
        a, s = M.avg(tap), M.avg(stab)
        c = M.ci(a, s)
        rep = quick or round(mean(a), 4) == recorded
        runs[label] = {"target": tgt, "tap_mean": mean(a), "stab_only_mean": mean(s), "contrast": c,
                       "stab_tables": sorted({json.dumps(t, sort_keys=True) for t in tables}), "reproduced": rep,
                       "outcome": outcome(c["lo"], c["hi"]) if rep else "NOT REPRODUCED"}
    outs = [r["outcome"] for r in runs.values()]
    final = ("NOT REPRODUCED" if "NOT REPRODUCED" in outs else
             "HOLDS" if all(o == "HOLDS" for o in outs) else "LOSES" if "LOSES" in outs else "TIES")
    return {"id": "A7 T-AP", "baseline": "STAB-ONLY", "level": M.LEVEL, "runs": runs, "outcome": final}


# ------------------------------------------------------------------------------------------------ recorded rows
def recorded_rows():
    world = json.loads((HERE / "results" / "results_world.json").read_text())
    floor3 = (HERE / "results" / "floor3.md").read_text()
    lion = '{"calm": "LION", "rising": "LION", "loaded": "LION", "crisis": "LION"}'
    gated_all_lion = floor3.count(f"Gated table: `{lion}`")
    return [
        {"id": "A1 W1", "baseline": "GREEDY (equal information)", "recorded": {"beats_equal_information": world["W1"]["beats_equal_information"]},
         "outcome": "HOLDS" if world["W1"]["beats_equal_information"] else "TIES"},
        {"id": "A2 W4", "baseline": "none applies (§3)", "outcome": "NOT APPLICABLE"},
        {"id": "A5 G1", "baseline": "NONE (transfer nothing)", "recorded": {"g1_gated_tables_all_lion": gated_all_lion >= 2},
         "outcome": "TIES" if floor3.split("## G2")[0].count(f"Gated table: `{lion}`") == 2 else "SEE RECORD"},
    ]


def run(quick=False):
    rows = recorded_rows()
    rows.append(fixed_best_audit("A3 H-SWITCH", "legacy", range(1000, 1020 if quick else 1200), range(1200, 1205 if quick else 1220),
                                 None if quick else 0.042649191321466134))
    rows.append(fixed_best_audit("A4 H-CFIT-M", "mission", range(5000, 5020 if quick else 5200), range(5200, 5205 if quick else 5220),
                                 None if quick else 0.04473175661630185))
    rows.append(j1_audit(quick))
    rows.append(tap_audit(quick))
    rows.sort(key=lambda r: r["id"])
    return {"test": "BASELINE_AUDIT", "spec": "spec/BASELINE_AUDIT.md", "quick": quick, "rows": rows}


def _ci(c, d=4):
    return f"{c['diff']:+.{d}f} [{c['lo']:+.{d}f}, {c['hi']:+.{d}f}]"


def report(R) -> str:
    L = ["# BASELINE_AUDIT — the passed RSX-V rows against their simplest baselines (results)", "",
         "Design and rule: [`spec/BASELINE_AUDIT.md`](../../spec/BASELINE_AUDIT.md), registered before this code. Stated models;",
         "no number here comes from people or production agents.", "",
         "| Row | Baseline | Outcome |", "|---|---|---|"]
    L += [f"| {r['id']} | {r['baseline']} | **{r['outcome']}** |" for r in R["rows"]]
    for r in R["rows"]:
        L += ["", f"## {r['id']}", ""]
        if "contrast" in r:
            L += [f"- Pilot means (20 pilot persons): " + ", ".join(f"{m} {v:+.4f}" for m, v in r["pilot_means"].items()),
                  f"- Chosen: {r['chosen']}. Watchdog {r['method_mean']:+.4f}; FIXED-BEST {r['baseline_mean']:+.4f}.",
                  f"- Watchdog − FIXED-BEST (95%): {_ci(r['contrast'])}. Reproduced: {r['reproduced']}.",
                  "- Information only, each fixed mode on the test persons: "
                  + ", ".join(f"{m} {v:+.4f}" for m, v in r["fixed_on_test_info_only"].items())]
        elif "runs" in r:
            for k, x in r["runs"].items():
                L += [f"- {k} ({x['target']}): T-AP {x['tap_mean']:+.4f}; STAB-ONLY {x['stab_only_mean']:+.4f}; "
                      f"T-AP − STAB-ONLY {_ci(x['contrast'])}; reproduced {x['reproduced']}; **{x['outcome']}**.",
                      f"  STAB-ONLY tables used: {', '.join(x['stab_tables'])}."]
        elif "p_one_sided" in r:
            L += [f"- n {r['n']}; J1 accuracy {r['accuracy']:.3f}; never-jam {r['never_jam']:.3f}; mean-only rule "
                  f"{r['mean_only_info_only']:.3f} (information only).",
                  f"- Discordant pairs: J1 only right {r['discordant']['j1_only']}, never-jam only right "
                  f"{r['discordant']['never_jam_only']}; exact one-sided McNemar p = {r['p_one_sided']:.2e}. "
                  f"Reproduced: {r['reproduced']}."]
        else:
            L += [f"- Recorded: {json.dumps(r.get('recorded', {}))}."]
    return "\n".join(L) + "\n"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    quick = "--quick" in argv
    R = run(quick)
    if quick:
        print(json.dumps([{k: r[k] for k in ("id", "outcome")} for r in R["rows"]]))
        return R
    (HERE / "results" / "results_baseline_audit.json").write_text(json.dumps(R, indent=1, default=str) + "\n")
    (HERE / "results" / "baseline_audit.md").write_text(report(R))
    print(report(R))
    return R


if __name__ == "__main__":
    main()
