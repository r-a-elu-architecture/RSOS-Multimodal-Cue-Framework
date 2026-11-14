"""LIA-G3, genealogy recovery from probe fingerprints (third attempt), as fixed in AGENTS.md §11.7.

Input: results/w5r3_runs.json (REPURPOSE runs of W5-R3, held-out regimes); planted edges = committed changes.
Operational choices fixed before the run:
- Visits to a context are the ticks whose World context is c. A fingerprint ending at change time T in context c is the
  longest run of visits ending at the last visit at or before T in which successive visits differ in mode in at least 60%
  of pairs, with at least 6 visits; its start is the time of its first visit, its signature the less frequent of the two
  most common modes in it (RAVEN, BEAR or OTHER).
- LIA-DIRECT3: for every (T, c) with a fingerprint, parent = first detected failure in c of a compatible kind in
  (previous change time, start]; fallback first failure in c in that interval. Slots without a fingerprint come from the
  §11.6 G-test detector with the §11.6 parent rule.
- TEMPORAL and RANDOM as before, on the same slots. Level 0.05 / 3 attempts / 2 comparisons (two-sided 99.17%).

    python3 -m rsxv.lia_g3         # writes results/results_lia_g3.json and results/lia_g3.md
"""
from __future__ import annotations

import json
import pathlib
import random

from .lia_g import COMPAT, CTXS, detect, f1, rand, temporal
from .lia_g2 import changed_slots2, lia_direct2
from .w5r_experiments import ci

LEVEL = 1 - 0.05 / 6


def fingerprint(rows, c, T):
    vis = [(t, m) for t, ctx, m, *_ in rows if ctx == c and t <= T]
    best = None
    for k in range(len(vis) - 6, -1, -1):
        seg = vis[k:]
        alt = sum(a[1] != b[1] for a, b in zip(seg, seg[1:])) / (len(seg) - 1)
        if alt >= 0.6:
            best = seg
        elif best is not None and len(seg) > len(best) + 6:
            break
    if best is None:
        return None
    modes = [m for _, m in best]
    top = sorted(set(modes), key=modes.count, reverse=True)[:2]
    x = top[1] if len(top) > 1 else top[0]
    return {"start": best[0][0], "sig": "RAVEN" if x == "RAVEN" else ("BEAR" if x == "BEAR" else "OTHER")}


def run(path):
    runs = json.loads(pathlib.Path(path).read_text())
    rows_out, excluded, planted, fp_found, fp_right = [], 0, 0, 0, 0
    for i, (key, R) in enumerate(sorted(runs.items())):
        sub = key.split("/")[0]
        truth = {(c["failure_t"], c["applied_t"]) for c in R["changes"]}
        times = sorted({c["applied_t"] for c in R["changes"]})
        fails = detect(R["trace"], sub)
        gslots = changed_slots2(R["trace"], times)
        pred, slots = set(), []
        fp_slots = set()
        for T in times:
            prev = max([t for t in times if t < T], default=0)
            for c in CTXS:
                fp = fingerprint(R["trace"], c, T)
                if fp is None or fp["start"] <= prev:
                    continue
                fp_slots.add((T, c))
                slots.append((T, c, fp["sig"]))
                win = sorted([f for f in fails if prev < f[0] <= fp["start"] and f[1] == c], key=lambda f: f[0])
                comp = [f for f in win if f[2] in COMPAT[fp["sig"]]]
                pick = comp[0] if comp else (win[0] if win else None)
                if pick:
                    pred.add((pick[0], T))
        rest = [s for s in gslots if (s[0], s[1]) not in fp_slots]
        pred |= lia_direct2(rest, fails, times)
        slots += rest
        for ch in R["changes"]:
            planted += 1
            if (ch["applied_t"], ch["ctx"]) in fp_slots:
                fp_found += 1
                fp_right += (ch["failure_t"], ch["applied_t"]) in pred
        P = {"LIA-DIRECT3": pred, "TEMPORAL": temporal(slots, fails), "RANDOM": rand(slots, fails, random.Random(4242 + i))}
        s = {k: f1(v, truth) for k, v in P.items()}
        if all(v is None for v in s.values()):
            excluded += 1
            continue
        rows_out.append({"run": key, "sub": sub, **{k: (0.0 if v is None else v) for k, v in s.items()}})
    out = {"design": "AGENTS.md §11.7 LIA-G3", "level": LEVEL, "n_runs": len(rows_out), "excluded_empty": excluded,
           "planted": planted, "fingerprint_recall": fp_found / planted if planted else None,
           "parent_accuracy_given_fingerprint": fp_right / fp_found if fp_found else None}
    for scope in ("all", "agent", "person"):
        rs = [r for r in rows_out if scope == "all" or r["sub"] == scope]
        if not rs:
            out[scope] = None
            continue
        m = {k: sum(r[k] for r in rs) / len(rs) for k in ("LIA-DIRECT3", "TEMPORAL", "RANDOM")}
        c = {f"LIA-DIRECT3-{o}": ci([r["LIA-DIRECT3"] for r in rs], [r[o] for r in rs], level=LEVEL)
             for o in ("TEMPORAL", "RANDOM")}
        out[scope] = {"n": len(rs), "mean_f1": m, "ci": c}
    a = out["all"]
    out["pass"] = bool(a is not None and all(v["lo"] > 0 for v in a["ci"].values())
                       and a["mean_f1"]["LIA-DIRECT3"] >= 0.70)
    return out


def report(R) -> str:
    fmt = lambda x: "—" if x is None else f"{x:.3f}"
    L = ["# LIA-G3 — genealogy recovery from probe fingerprints: results", "",
         "Design: [`AGENTS.md`](../AGENTS.md) §11.7; choices in the docstring of [`rsxv/lia_g3.py`](../rsxv/lia_g3.py).",
         "Data: committed changes in the REPURPOSE runs of W5-R3 (held-out regimes).", "",
         f"Runs scored: {R['n_runs']}; excluded (no planted and no predicted edges): {R['excluded_empty']}. Planted edges: "
         f"{R['planted']}. Fingerprint recall: {fmt(R['fingerprint_recall'])}. Parent accuracy given a fingerprint: "
         f"{fmt(R['parent_accuracy_given_fingerprint'])}. Intervals: two-sided {LEVEL:.4f}.", "",
         "| Scope | runs | F1 LIA-DIRECT3 | F1 TEMPORAL | F1 RANDOM | DIRECT3−TEMPORAL [lo, hi] | DIRECT3−RANDOM [lo, hi] |",
         "|---|---|---|---|---|---|---|"]
    for scope in ("all", "agent", "person"):
        X = R[scope]
        if X is None:
            L.append(f"| {scope} | 0 | — | — | — | — | — |")
            continue
        m, c = X["mean_f1"], X["ci"]
        L.append(f"| {scope} | {X['n']} | {m['LIA-DIRECT3']:.3f} | {m['TEMPORAL']:.3f} | {m['RANDOM']:.3f} | "
                 + " | ".join(f"{c[k]['diff']:+.3f} [{c[k]['lo']:+.3f}, {c[k]['hi']:+.3f}]" for k in c) + " |")
    L += ["", f"**LIA-G3: {'PASS' if R['pass'] else 'FAIL'}** (registered: beats TEMPORAL and RANDOM, mean F1 ≥ 0.70).", ""]
    return "\n".join(L)


def main():
    d = pathlib.Path(__file__).resolve().parents[1] / "results"
    R = run(d / "w5r3_runs.json")
    print(report(R))
    (d / "results_lia_g3.json").write_text(json.dumps(R, indent=1))
    (d / "lia_g3.md").write_text(report(R))


if __name__ == "__main__":
    main()
