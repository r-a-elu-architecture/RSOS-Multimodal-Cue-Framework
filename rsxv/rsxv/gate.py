"""Floor 3: the cross-substrate transfer gate (AGENTS.md §11.2).

Knowledge from the source substrate (a table: context -> archetype) reaches the target only where a micro-randomised pilot
on the target gives a one-sided lower confidence bound above zero for (archetype - baseline) on the target's mission
score. Elsewhere the baseline runs. The decisions form a validity map.
"""
from __future__ import annotations

import math

from scipy import stats

from . import world as W

FAMILY_ALPHA = 0.05
BASELINE = "LION"


def cells(traces) -> dict:
    """traces: iterable of World.trace lists -> {(context, mode): [scores]}."""
    out: dict = {}
    for tr in traces:
        for ctx, mode, r in tr:
            out.setdefault((ctx, mode), []).append(r)
    return out


def welch_lower(xs, ys, alpha):
    """One-sided (1 - alpha) lower bound for mean(xs) - mean(ys), Welch t. None if a cell has fewer than 2 values."""
    n, m = len(xs), len(ys)
    if n < 2 or m < 2:
        return None, None
    mx, my = sum(xs) / n, sum(ys) / m
    vx = sum((x - mx) ** 2 for x in xs) / (n - 1)
    vy = sum((y - my) ** 2 for y in ys) / (m - 1)
    se2 = vx / n + vy / m
    d = mx - my
    if se2 == 0:
        return d, d
    df = se2 ** 2 / ((vx / n) ** 2 / (n - 1) + (vy / m) ** 2 / (m - 1)) if vx > 0 and vy > 0 else min(n, m) - 1
    return d, d - stats.t.ppf(1 - alpha, df) * math.sqrt(se2)


def gate(table: dict, pilot: dict, baseline: str = BASELINE, family_alpha: float = FAMILY_ALPHA) -> tuple[dict, list]:
    """Returns (gated table, validity map)."""
    alpha = family_alpha / len(W.CONTEXTS)
    gated, vmap = {}, []
    for c in W.CONTEXTS:
        m = table.get(c, baseline)
        row = {"context": c, "candidate": m, "n_candidate": len(pilot.get((c, m), [])),
               "n_baseline": len(pilot.get((c, baseline), []))}
        if m == baseline:
            row.update(decision="admit (already baseline)", estimate=0.0, bound=None)
            gated[c] = baseline
        else:
            est, lb = welch_lower(pilot.get((c, m), []), pilot.get((c, baseline), []), alpha)
            ok = lb is not None and lb > 0
            row.update(decision="admit" if ok else ("reject: too few data" if lb is None else "reject"),
                       estimate=est, bound=lb)
            gated[c] = m if ok else baseline
        vmap.append(row)
    return gated, vmap


def truth_effects(truth: dict, baseline: str = BASELINE) -> dict:
    """Mean (archetype - baseline) per context from a large uniformly randomised cohort."""
    out = {}
    for c in W.CONTEXTS:
        b = truth.get((c, baseline), [])
        for m in W.MODES:
            x = truth.get((c, m), [])
            if x and b:
                out[(c, m)] = sum(x) / len(x) - sum(b) / len(b)
    return out
