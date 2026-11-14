"""LIA-G, recovering failure -> mechanism genealogy from behaviour alone, as fixed in AGENTS.md §11.5.

Input: results/w5r_runs.json (REPURPOSE runs of W5-R on the held-out regimes). The reconstructor reads only, per tick, the
state (World context, load before the tick, harm rise), the action (mode) and the mission score, plus the times of policy
changes. The Watchdog's failure labels stored in the run file, the registry, lineage edges and audit text are not read; the
ground-truth changes are read only by the scorer.

Operational choices fixed before the run (disclosed in results/lia_g.md):
- Failures are re-detected from observable data with the Watchdog's published rules where they are observable: flicker
  (modes), person setback (harm rise > 1, person runs), agent fault (harm rise > 0, agent runs), contaminated anchor
  approximated as an interrupting mode (BEAR, RAVEN, TIGER) at load >= 0.8 with harm rising (person runs). Silent faults are
  not observable from the trace and are not detected.
- A context counts as changed at a policy-change time T when a mode appears at least twice in that context between T and
  the next change (or the end) that did not appear there between the previous change (or the start) and T, or when mode
  changes inside that context fall by half or more (the hysteresis signature). The same changed (T, context) slots are used
  by every method, so methods differ only in the parent they choose.
- Signature -> compatible failure kinds (the mechanism library read as a hypothesis): new RAVEN -> silent fault; new BEAR ->
  contaminated anchor, agent fault, person setback, refused transfer; another new mode -> person setback, refused transfer,
  agent fault; no new mode -> flicker.
- LIA-DIRECT considers failures in [T - 25, T) (one maintenance cycle, a property of the architecture, not of the run):
  most recent failure with the same context and a compatible kind; else most recent with the same context; else none.
  TEMPORAL: nearest failure before T. RANDOM: a uniformly random failure before T (seed 4242 + run index).
- An edge is correct when its failure tick and change time equal those of a planted edge. Per-run F1; a run where both the
  planted set and every method's prediction set are empty has no F1 and is excluded (count reported).

    python3 -m rsxv.lia_g          # writes results/results_lia_g.json and results/lia_g.md
"""
from __future__ import annotations

import json
import pathlib
import random

from .w5r_experiments import ci

LEVEL = 1 - 0.05 / 2
INTERRUPT = {"BEAR", "RAVEN", "TIGER"}
CTXS = ["calm", "rising", "loaded", "crisis"]


def detect(rows, sub):
    out, modes = [], []
    for t, ctx, mode, r, load, rise, _labels in rows:          # _labels: Watchdog output, not read
        modes.append(mode)
        last = modes[-6:]
        if sum(a != b for a, b in zip(last, last[1:])) >= 3:
            out.append((t, ctx, "flicker"))
        if sub == "person":
            if rise > 1.0:
                out.append((t, ctx, "person_setback"))
            if mode in INTERRUPT and load >= 0.8 and rise > 0:
                out.append((t, ctx, "contaminated_anchor"))
        elif rise > 0:
            out.append((t, ctx, "agent_fault"))
    return out


def changed_slots(rows, times):
    bounds = [0] + list(times) + [10 ** 9]
    slots = []
    for i, T in enumerate(times):
        lo, hi = bounds[i], bounds[i + 2]
        for c in CTXS:
            before = [m for t, ctx, m, *_ in rows if ctx == c and lo < t <= T]
            after = [m for t, ctx, m, *_ in rows if ctx == c and T < t <= hi]
            new = {m for m in set(after) if after.count(m) >= 2 and m not in before}
            sw_b = sum(a != b for a, b in zip(before, before[1:])) / max(1, len(before))
            sw_a = sum(a != b for a, b in zip(after, after[1:])) / max(1, len(after))
            if new:
                slots.append((T, c, "RAVEN" if "RAVEN" in new else ("BEAR" if "BEAR" in new else "OTHER")))
            elif before and after and sw_b > 0 and sw_a <= 0.5 * sw_b:
                slots.append((T, c, "NONE"))
    return slots


COMPAT = {"RAVEN": {"silent_fault"},
          "BEAR": {"contaminated_anchor", "agent_fault", "person_setback", "refused_transfer"},
          "OTHER": {"person_setback", "refused_transfer", "agent_fault"},
          "NONE": {"flicker"}}


def lia_direct(slots, fails):
    pred = set()
    for T, c, sig in slots:
        win = [f for f in fails if T - 25 <= f[0] < T and f[1] == c]
        comp = [f for f in win if f[2] in COMPAT[sig]]
        pick = max(comp, key=lambda f: f[0]) if comp else (max(win, key=lambda f: f[0]) if win else None)
        if pick:
            pred.add((pick[0], T))
    return pred


def temporal(slots, fails):
    pred = set()
    for T, c, sig in slots:
        prev = [f for f in fails if f[0] < T]
        if prev:
            pred.add((max(prev, key=lambda f: f[0])[0], T))
    return pred


def rand(slots, fails, rng):
    pred = set()
    for T, c, sig in slots:
        prev = [f for f in fails if f[0] < T]
        if prev:
            pred.add((rng.choice(prev)[0], T))
    return pred


def f1(pred, truth):
    if not pred and not truth:
        return None
    tp = len(pred & truth)
    p = tp / len(pred) if pred else 0.0
    r = tp / len(truth) if truth else 0.0
    return 0.0 if p + r == 0 else 2 * p * r / (p + r)


def run(path):
    runs = json.loads(pathlib.Path(path).read_text())
    rows_out, excluded = [], 0
    for i, (key, R) in enumerate(sorted(runs.items())):
        sub = key.split("/")[0]
        truth = {(c["failure_t"], c["applied_t"]) for c in R["changes"]}
        fails = detect(R["trace"], sub)
        slots = changed_slots(R["trace"], R["change_times"])
        P = {"LIA-DIRECT": lia_direct(slots, fails), "TEMPORAL": temporal(slots, fails),
             "RANDOM": rand(slots, fails, random.Random(4242 + i))}
        s = {k: f1(v, truth) for k, v in P.items()}
        if all(v is None for v in s.values()):
            excluded += 1
            continue
        s = {k: (0.0 if v is None else v) for k, v in s.items()}
        rows_out.append({"run": key, "sub": sub, "n_truth": len(truth), "n_slots": len(slots), **s})
    out = {"design": "AGENTS.md §11.5 LIA-G", "level": LEVEL, "n_runs": len(rows_out), "excluded_empty": excluded}
    for scope in ("all", "agent", "person"):
        rs = [r for r in rows_out if scope == "all" or r["sub"] == scope]
        if not rs:
            out[scope] = None
            continue
        m = {k: sum(r[k] for r in rs) / len(rs) for k in ("LIA-DIRECT", "TEMPORAL", "RANDOM")}
        c = {f"LIA-DIRECT-{o}": ci([r["LIA-DIRECT"] for r in rs], [r[o] for r in rs], level=LEVEL)
             for o in ("TEMPORAL", "RANDOM")}
        out[scope] = {"n": len(rs), "mean_f1": m, "ci": c}
    a = out["all"]
    out["pass"] = (a is not None and all(v["lo"] > 0 for v in a["ci"].values()) and a["mean_f1"]["LIA-DIRECT"] >= 0.70)
    return out


def report(R) -> str:
    L = ["# LIA-G — genealogy recovery from behaviour alone: results", "",
         "Design: [`AGENTS.md`](../AGENTS.md) §11.5; operational choices fixed before the run are in the docstring of",
         "[`rsxv/lia_g.py`](../rsxv/lia_g.py). Data: the REPURPOSE runs of W5-R (held-out regimes only).", "",
         f"Runs scored: {R['n_runs']}; runs with no planted and no predicted edges (excluded): {R['excluded_empty']}.",
         f"Intervals: paired bootstrap, two-sided {LEVEL:.3f}.", "",
         "| Scope | runs | F1 LIA-DIRECT | F1 TEMPORAL | F1 RANDOM | DIRECT−TEMPORAL [lo, hi] | DIRECT−RANDOM [lo, hi] |",
         "|---|---|---|---|---|---|---|"]
    for scope in ("all", "agent", "person"):
        X = R[scope]
        if X is None:
            L.append(f"| {scope} | 0 | — | — | — | — | — |")
            continue
        m, c = X["mean_f1"], X["ci"]
        L.append(f"| {scope} | {X['n']} | {m['LIA-DIRECT']:.3f} | {m['TEMPORAL']:.3f} | {m['RANDOM']:.3f} | "
                 f"{c['LIA-DIRECT-TEMPORAL']['diff']:+.3f} [{c['LIA-DIRECT-TEMPORAL']['lo']:+.3f}, {c['LIA-DIRECT-TEMPORAL']['hi']:+.3f}] | "
                 f"{c['LIA-DIRECT-RANDOM']['diff']:+.3f} [{c['LIA-DIRECT-RANDOM']['lo']:+.3f}, {c['LIA-DIRECT-RANDOM']['hi']:+.3f}] |")
    L += ["", f"**LIA-G: {'PASS' if R['pass'] else 'FAIL'}** (registered: LIA-DIRECT beats TEMPORAL and RANDOM over all runs, "
          "mean F1 ≥ 0.70).", ""]
    return "\n".join(L)


def main():
    d = pathlib.Path(__file__).resolve().parents[1] / "results"
    R = run(d / "w5r_runs.json")
    print(report(R))
    (d / "results_lia_g.json").write_text(json.dumps(R, indent=1))
    (d / "lia_g.md").write_text(report(R))


if __name__ == "__main__":
    main()
