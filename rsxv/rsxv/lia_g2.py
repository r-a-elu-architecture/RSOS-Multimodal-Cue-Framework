"""LIA-G2, genealogy recovery with the architecture's parent rule (second attempt), as fixed in AGENTS.md §11.6.

Input: results/w5r2_runs.json (REPURPOSE runs of W5-R2, held-out regimes); planted edges = committed changes only.
Failure re-detection, compatibility table, TEMPORAL and RANDOM are those of lia_g.py (§11.5). Changes from §11.5:
- LIA-DIRECT2 parent: the first detected failure of a compatible kind in context c since the previous policy-change time
  (exclusive) and before T; fallback the first failure in c in that interval; else none.
- Changed contexts: per context, mode counts before and after T (bounded by neighbouring change times) compared with a
  G-test (p < 0.05, df = number of modes seen − 1); or mode changes within the context fall by half or more. The signature
  used for compatibility is the mode whose share rose most (RAVEN, BEAR, other) or NONE when no mode share rose.
Level 0.05 / 2 attempts / 2 comparisons = 0.0125 (two-sided 98.75%).

    python3 -m rsxv.lia_g2         # writes results/results_lia_g2.json and results/lia_g2.md
"""
from __future__ import annotations

import json
import pathlib
import random

from scipy import stats

from .lia_g import COMPAT, CTXS, detect, f1, rand, temporal
from .w5r_experiments import ci

LEVEL = 1 - 0.05 / 4


def gtest(a: dict, b: dict) -> float:
    modes = sorted(set(a) | set(b))
    if len(modes) < 2:
        return 1.0
    na, nb = sum(a.values()), sum(b.values())
    if na == 0 or nb == 0:
        return 1.0
    g = 0.0
    for m in modes:
        tot = a.get(m, 0) + b.get(m, 0)
        for obs, n in ((a.get(m, 0), na), (b.get(m, 0), nb)):
            exp = tot * n / (na + nb)
            if obs > 0:
                g += 2 * obs * __import__("math").log(obs / exp)
    return float(stats.chi2.sf(g, len(modes) - 1))


def changed_slots2(rows, times):
    bounds = [0] + list(times) + [10 ** 9]
    slots = []
    for i, T in enumerate(times):
        lo, hi = bounds[i], bounds[i + 2]
        for c in CTXS:
            before = [m for t, ctx, m, *_ in rows if ctx == c and lo < t <= T]
            after = [m for t, ctx, m, *_ in rows if ctx == c and T < t <= hi]
            if not before or not after:
                continue
            cb = {m: before.count(m) for m in set(before)}
            ca = {m: after.count(m) for m in set(after)}
            p = gtest(cb, ca)
            sw_b = sum(x != y for x, y in zip(before, before[1:])) / len(before)
            sw_a = sum(x != y for x, y in zip(after, after[1:])) / len(after)
            if p < 0.05 or (sw_b > 0 and sw_a <= 0.5 * sw_b):
                rise = {m: ca.get(m, 0) / len(after) - cb.get(m, 0) / len(before) for m in set(ca) | set(cb)}
                top = max(rise, key=rise.get)
                sig = "NONE" if rise[top] <= 0 else ("RAVEN" if top == "RAVEN" else ("BEAR" if top == "BEAR" else "OTHER"))
                slots.append((T, c, sig))
    return slots


def lia_direct2(slots, fails, times):
    pred = set()
    for T, c, sig in slots:
        prev = max([t for t in times if t < T], default=0)
        win = sorted([f for f in fails if prev < f[0] < T and f[1] == c], key=lambda f: f[0])
        comp = [f for f in win if f[2] in COMPAT[sig]]
        pick = comp[0] if comp else (win[0] if win else None)
        if pick:
            pred.add((pick[0], T))
    return pred


def run(path):
    runs = json.loads(pathlib.Path(path).read_text())
    rows_out, excluded, slot_hit, n_planted, parent_ok, parent_n = [], 0, 0, 0, 0, 0
    for i, (key, R) in enumerate(sorted(runs.items())):
        sub = key.split("/")[0]
        truth = {(c["failure_t"], c["applied_t"]) for c in R["changes"]}
        times = sorted({c["applied_t"] for c in R["changes"]})
        fails = detect(R["trace"], sub)
        slots = changed_slots2(R["trace"], times)
        P = {"LIA-DIRECT2": lia_direct2(slots, fails, times), "TEMPORAL": temporal(slots, fails),
             "RANDOM": rand(slots, fails, random.Random(4242 + i))}
        sl = {(T, c) for T, c, _ in slots}
        for ch in R["changes"]:
            n_planted += 1
            if (ch["applied_t"], ch["ctx"]) in sl:
                slot_hit += 1
                parent_n += 1
                parent_ok += (ch["failure_t"], ch["applied_t"]) in P["LIA-DIRECT2"]
        s = {k: f1(v, truth) for k, v in P.items()}
        if all(v is None for v in s.values()):
            excluded += 1
            continue
        s = {k: (0.0 if v is None else v) for k, v in s.items()}
        rows_out.append({"run": key, "sub": sub, **s})
    out = {"design": "AGENTS.md §11.6 LIA-G2", "level": LEVEL, "n_runs": len(rows_out), "excluded_empty": excluded,
           "planted": n_planted, "slot_recall": slot_hit / n_planted if n_planted else None,
           "parent_accuracy_given_slot": parent_ok / parent_n if parent_n else None}
    for scope in ("all", "agent", "person"):
        rs = [r for r in rows_out if scope == "all" or r["sub"] == scope]
        if not rs:
            out[scope] = None
            continue
        m = {k: sum(r[k] for r in rs) / len(rs) for k in ("LIA-DIRECT2", "TEMPORAL", "RANDOM")}
        c = {f"LIA-DIRECT2-{o}": ci([r["LIA-DIRECT2"] for r in rs], [r[o] for r in rs], level=LEVEL)
             for o in ("TEMPORAL", "RANDOM")}
        out[scope] = {"n": len(rs), "mean_f1": m, "ci": c}
    a = out["all"]
    out["pass"] = bool(a is not None and all(v["lo"] > 0 for v in a["ci"].values())
                       and a["mean_f1"]["LIA-DIRECT2"] >= 0.70)
    return out


def report(R) -> str:
    L = ["# LIA-G2 — genealogy recovery with the architecture's parent rule: results", "",
         "Design: [`AGENTS.md`](../AGENTS.md) §11.6; choices in the docstring of [`rsxv/lia_g2.py`](../rsxv/lia_g2.py).",
         "Data: committed changes in the REPURPOSE runs of W5-R2 (held-out regimes).", "",
         f"Runs scored: {R['n_runs']}; excluded (no planted and no predicted edges): {R['excluded_empty']}. Planted edges: "
         f"{R['planted']}. Slot recall: {R['slot_recall']:.3f}. Parent accuracy given a found slot: "
         f"{R['parent_accuracy_given_slot']:.3f}. Intervals: two-sided {LEVEL:.4f}.", "",
         "| Scope | runs | F1 LIA-DIRECT2 | F1 TEMPORAL | F1 RANDOM | DIRECT2−TEMPORAL [lo, hi] | DIRECT2−RANDOM [lo, hi] |",
         "|---|---|---|---|---|---|---|"]
    for scope in ("all", "agent", "person"):
        X = R[scope]
        if X is None:
            L.append(f"| {scope} | 0 | — | — | — | — | — |")
            continue
        m, c = X["mean_f1"], X["ci"]
        L.append(f"| {scope} | {X['n']} | {m['LIA-DIRECT2']:.3f} | {m['TEMPORAL']:.3f} | {m['RANDOM']:.3f} | "
                 + " | ".join(f"{c[k]['diff']:+.3f} [{c[k]['lo']:+.3f}, {c[k]['hi']:+.3f}]" for k in c) + " |")
    L += ["", f"**LIA-G2: {'PASS' if R['pass'] else 'FAIL'}** (registered: beats TEMPORAL and RANDOM, mean F1 ≥ 0.70).", ""]
    return "\n".join(L)


def main():
    d = pathlib.Path(__file__).resolve().parents[1] / "results"
    R = run(d / "w5r2_runs.json")
    print(report(R))
    (d / "results_lia_g2.json").write_text(json.dumps(R, indent=1))
    (d / "lia_g2.md").write_text(report(R))


if __name__ == "__main__":
    main()
