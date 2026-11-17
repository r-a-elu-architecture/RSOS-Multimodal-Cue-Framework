"""W5-CEILING: is perfect source knowledge worth anything to the target? Design and decision rule: spec/CEILING.md,
registered before any code or run. Uses W5's environments, score, smoothed context, seeds and deployment unchanged.

    python3 -m rsxv.ceiling_experiments            # writes results/results_ceiling.json and results/ceiling.md
    python3 -m rsxv.ceiling_experiments --quick    # small smoke run, nothing written
"""
from __future__ import annotations

import json
import pathlib
import sys

from . import w3c_experiments as C
from . import w5_experiments as X
from . import world as W
from .world_experiments import mean

HERE = pathlib.Path(__file__).resolve().parents[1]
FUNCS = ("STABILISE", "RESTORE", "DRIVE")          # §1: the first matching function wins
PILOT_SIZE, REPS = 8, 20


def best_table(effects: dict) -> dict:
    """Per context, the archetype with the largest positive effect over LION; LION if none is positive."""
    out = {}
    for c in W.CONTEXTS:
        opts = {m: e for (cc, m), e in effects.items() if cc == c and m != "LION" and e > 0}
        out[c] = max(opts, key=opts.get) if opts else "LION"
    return out


def map_table(src_table: dict, src_roles: dict, tgt_roles: dict) -> dict:
    """Source archetype -> function (first of STABILISE, RESTORE, DRIVE whose role it is) -> target archetype."""
    out = {}
    for c, a in src_table.items():
        f = next((f for f in FUNCS if src_roles.get(f) == a), None) if a != "LION" else None
        out[c] = tgt_roles.get(f, "LION") if f else "LION"
    return out


def verdict(con_none: dict, con_pilot: dict) -> dict:
    return {"value": con_none["lo"] > 0, "room": con_pilot["lo"] > 0}


def line_verdict(per_dir: list) -> dict:
    room = [d["source"] + " → " + d["target"] for d in per_dir if d["verdict"]["room"]]
    return {"pass": bool(room), "room_in": room,
            "decision": ("Pass for " + ", ".join(room) + " by the registered rule. The room cannot be credited to the source: a source-free rule "
                         "(the target's stabilising archetype everywhere, read from the pilot's own role-reading ticks) reaches the same value "
                         "(review P2-1; spec/FIXES_P2.md C1). The W5 transfer line stops in all four directions (C2).")
            if room else "Fail: even perfect source knowledge is no better than an 8-target pilot in any direction. The W5 transfer line stops (no W5f); T-AP stays as recorded."}


def direction(src, tgt, quick=False):
    bt = X.BASE_OF[tgt]
    n_or = 10 if quick else 50
    dseeds = list(range(X.DEPLOY0[bt], X.DEPLOY0[bt] + (20 if quick else 200)))
    s_roles = C.read_roles(src, range(X.ORACLE0[X.BASE_OF[src]], X.ORACLE0[X.BASE_OF[src]] + n_or), 60)
    t_roles = C.read_roles(tgt, range(X.ORACLE0[bt], X.ORACLE0[bt] + n_or), 60)
    s_true, t_true = best_table(TRUTH[src]), best_table(TRUTH[tgt])
    src_mapped = map_table(s_true, s_roles, t_roles)
    per = {"SRC-TRUE": X.deploy(tgt, X.TablePolicy(src_mapped), dseeds)[0],
           "TGT-TRUE": X.deploy(tgt, X.TablePolicy(t_true), dseeds)[0],
           "NONE": X.deploy(tgt, X.TablePolicy({}), dseeds)[0]}
    reps, tables = [], []
    for r in range(2 if quick else REPS):
        seeds = list(range(X.PILOT0[bt] + 16 * r, X.PILOT0[bt] + 16 * r + PILOT_SIZE))
        g, _ = X.decide_pilot_only(tgt, seeds)
        tables.append(g)
        reps.append(X.deploy(tgt, X.TablePolicy(g), dseeds)[0])
    per["PILOT-8"] = X.avg(reps)
    m = {k: mean(v) for k, v in per.items()}
    con = {"SRC-TRUE − NONE": X.ci(per["SRC-TRUE"], per["NONE"]), "SRC-TRUE − PILOT-8": X.ci(per["SRC-TRUE"], per["PILOT-8"]),
           "TGT-TRUE − NONE": X.ci(per["TGT-TRUE"], per["NONE"]), "PILOT-8 − NONE": X.ci(per["PILOT-8"], per["NONE"])}
    gap = m["TGT-TRUE"] - m["NONE"]
    return {"source": src, "target": tgt, "source_roles": s_roles, "target_roles": t_roles, "source_true_table": s_true,
            "src_true_mapped": src_mapped, "target_true_table": t_true, "pilot_tables": tables, "arms": m, "contrasts": con,
            "share": (m["SRC-TRUE"] - m["NONE"]) / gap if abs(gap) > 1e-9 else None,
            "verdict": verdict(con["SRC-TRUE − NONE"], con["SRC-TRUE − PILOT-8"])}


TRUTH: dict = {}


def run(quick=False):
    for env in ("person", "agent", "agent_v2"):
        TRUTH[env] = X.truth(env) if not quick else _quick_truth(env)
    dirs = [direction(s, t, quick) for s, t in X.DIRECTIONS]
    return {"test": "W5-CEILING", "spec": "spec/CEILING.md", "quick": quick, "directions": dirs, "line": line_verdict(dirs)}


def _quick_truth(env):
    base, cells = X.BASE_OF[env], {}
    for s in range(X.TRUTH0[base], X.TRUTH0[base] + 20):
        w = W.World(X.ENV[env](s), "random", seed=s, score="mission")
        sm = X.Smooth()
        for _ in range(60):
            c = sm.ctx(w.env.sense()); out = w.tick()
            cells.setdefault((c, out["mode"]), []).append(out["reward"])
    from . import gate as G
    return G.truth_effects(cells)


def fmt(c):
    return f"{c['diff']:+.4f} [{c['lo']:+.4f}, {c['hi']:+.4f}]"


def report(R) -> str:
    L = ["# W5-CEILING — is perfect source knowledge worth anything to the target? (results)", "",
         "Design and decision rule: [`spec/CEILING.md`](../../spec/CEILING.md), registered before any code or run. W5's environments,",
         "mission score, smoothed context, seeds and deployment, unchanged. 99% paired bootstrap intervals over 200 deployment",
         "seeds. All environments are stated models; no number here comes from people or production agents.", ""]
    for d in R["directions"]:
        L += [f"## {d['source']} → {d['target']}", "",
              f"- Source true table {d['source_true_table']}; source roles {d['source_roles']}; target roles {d['target_roles']}.",
              f"- SRC-TRUE (mapped) {d['src_true_mapped']}; TGT-TRUE {d['target_true_table']}.", "",
              "| Arm | Mean / tick |", "|---|---|"] + [f"| {k} | {v:+.4f} |" for k, v in d["arms"].items()] + ["",
              "| Contrast (99%) | Estimate |", "|---|---|"] + [f"| {k} | {fmt(v)} |" for k, v in d["contrasts"].items()] + ["",
              f"Share of the reachable gain: {d['share']:+.2f}." if d["share"] is not None else "Share: not defined (no reachable gain).",
              f"VALUE: **{'yes' if d['verdict']['value'] else 'no'}**. ROOM: **{'yes' if d['verdict']['room'] else 'no'}**.", ""]
    L += ["## Verdict", "", R["line"]["decision"], ""]
    return "\n".join(L)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    quick = "--quick" in argv
    R = run(quick)
    if quick:
        print(json.dumps(R["line"], ensure_ascii=False)); return R
    (HERE / "results" / "results_ceiling.json").write_text(json.dumps(R, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (HERE / "results" / "ceiling.md").write_text(report(R), encoding="utf-8")
    print(R["line"]["decision"])
    return R


if __name__ == "__main__":
    main()
