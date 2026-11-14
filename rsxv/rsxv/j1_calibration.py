"""J1, jam-predictor calibration (AGENTS.md §11.9), scored on fresh seeds before W5e may use it.

Rule: a certified context jams when, in the pooled pilot, the candidate's spike rate per tick exceeds BASE's, or the
candidate's mean mission score is not above BASE's, or either cell holds fewer than 5 ticks. Truth: jam is correct when the
candidate's truth effect against BASE is <= 0 or its truth spike rate exceeds BASE's. Procedure: W5d (warnings on), pilot 8,
20 repetitions, four directions. Accepted when pooled accuracy >= 0.70 and above always-jam and never-jam.

    python3 -m rsxv.j1_calibration      # writes results/results_j1.json and results/j1.md
"""
from __future__ import annotations

import json
import pathlib

from . import w5d_experiments as M
from .world_experiments import mean

M.SRC0 = {"person": 221000, "agent": 221100, "agent_v2": 221200}
M.PILOT0 = {"person": 222000, "agent": 223000, "agent_v2": 224000}
M.TRUTH0 = {"person": 225000, "agent": 225200, "agent_v2": 225400}


def j1(cells, spk, c, a):
    xa, xb = cells.get((c, a), []), cells.get((c, "LION"), [])
    sa, sb = spk.get((c, a), []), spk.get((c, "LION"), [])
    if len(xa) < 5 or len(xb) < 5:
        return True
    return (sum(sa) / len(sa) > sum(sb) / len(sb)) or (mean(xa) <= mean(xb))


def main():
    certs, roles = {}, {}
    for src in ("person", "agent", "agent_v2"):
        certs[src], roles[src] = M.certificates(src, 0)
        M.WARNS[src] = M.LAST_WARN
    te = {t: M.truth(t) for t in ("person", "agent", "agent_v2")}
    rows = []
    for src, tgt in M.DIRECTIONS:
        M.CUR_WARN = M.WARNS.get(src, {})
        base = M.BASE_OF[tgt]
        sp_t = M.TRUTH_SPK[tgt]
        rate = lambda k: (sum(sp_t[k]) / len(sp_t[k])) if sp_t.get(k) else 0.0
        for r in range(20):
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
                pred = j1(cells, spk, c, a)
                truth = te[tgt].get((c, a), 0.0) <= 0 or rate((c, a)) > rate((c, "LION"))
                rows.append({"dir": f"{src}->{tgt}", "rep": r, "ctx": c, "arch": a, "pred": pred, "truth": truth})
    n = len(rows)
    acc = sum(x["pred"] == x["truth"] for x in rows) / n if n else 0.0
    base_jam = sum(x["truth"] for x in rows) / n if n else 0.0
    by = {}
    for x in rows:
        d = by.setdefault(x["dir"], [0, 0])
        d[0] += x["pred"] == x["truth"]
        d[1] += 1
    accepted = n > 0 and acc >= 0.70 and acc > base_jam and acc > 1 - base_jam
    R = {"n": n, "accuracy": acc, "always_jam": base_jam, "never_jam": 1 - base_jam, "accepted": accepted,
         "by_direction": {k: v[0] / v[1] for k, v in by.items()},
         "confusion": {"tp": sum(x["pred"] and x["truth"] for x in rows), "fp": sum(x["pred"] and not x["truth"] for x in rows),
                       "fn": sum((not x["pred"]) and x["truth"] for x in rows),
                       "tn": sum((not x["pred"]) and not x["truth"] for x in rows)}}
    L = ["# J1 — jam-predictor calibration: results", "",
         "Design: [`AGENTS.md`](../AGENTS.md) §11.9; code [`rsxv/j1_calibration.py`](../rsxv/j1_calibration.py).", "",
         f"Predictions scored: {n}. Accuracy {acc:.3f}; always-jam {base_jam:.3f}; never-jam {1 - base_jam:.3f}.",
         f"Confusion: {R['confusion']}. By direction: " + "; ".join(f"{k} {v:.3f}" for k, v in R["by_direction"].items()),
         "", f"**J1: {'ACCEPTED' if accepted else 'NOT ACCEPTED'}** (needs ≥ 0.70 and above both trivial predictors).", ""]
    d = pathlib.Path(__file__).resolve().parents[1] / "results"
    (d / "results_j1.json").write_text(json.dumps(R, indent=1))
    (d / "j1.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
