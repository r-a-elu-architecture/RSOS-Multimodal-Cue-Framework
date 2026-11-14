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


def welch_lower(xs, ys, alpha, min_n=2, var_floor=0.0):
    """One-sided (1 - alpha) lower bound for mean(xs) - mean(ys), Welch t. None if a cell has fewer than min_n values."""
    n, m = len(xs), len(ys)
    if n < max(2, min_n) or m < max(2, min_n):
        return None, None
    mx, my = sum(xs) / n, sum(ys) / m
    vx = max(var_floor, sum((x - mx) ** 2 for x in xs) / (n - 1))
    vy = max(var_floor, sum((y - my) ** 2 for y in ys) / (m - 1))
    se2 = vx / n + vy / m
    d = mx - my
    if se2 == 0:
        return d, d
    df = se2 ** 2 / ((vx / n) ** 2 / (n - 1) + (vy / m) ** 2 / (m - 1)) if vx > 0 and vy > 0 else min(n, m) - 1
    return d, d - stats.t.ppf(1 - alpha, df) * math.sqrt(se2)


def gate(table: dict, pilot: dict, baseline: str = BASELINE, family_alpha: float = FAMILY_ALPHA, alpha: float | None = None,
         min_n: int = 2, var_floor: float = 0.0) -> tuple[dict, list]:
    """Returns (gated table, validity map). `alpha` is the per-test level (default family_alpha / 4)."""
    alpha = family_alpha / len(W.CONTEXTS) if alpha is None else alpha
    gated, vmap = {}, []
    for c in W.CONTEXTS:
        m = table.get(c, baseline)
        row = {"context": c, "candidate": m, "n_candidate": len(pilot.get((c, m), [])),
               "n_baseline": len(pilot.get((c, baseline), []))}
        if m == baseline:
            row.update(decision="admit (already baseline)", estimate=0.0, bound=None)
            gated[c] = baseline
        else:
            est, lb = welch_lower(pilot.get((c, m), []), pilot.get((c, baseline), []), alpha, min_n, var_floor)
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


def gate_v2(table, pilot, alpha=FAMILY_ALPHA / 4, baseline=BASELINE):
    """Gate v2 (AGENTS.md §11.3): at least 5 ticks per cell, variance floored at 0.01."""
    return gate(table, pilot, baseline, alpha=alpha, min_n=5, var_floor=0.01)


# ---------------------------------------------------------------------------------------------------------- roles
def roles(comps, baseline=BASELINE) -> dict:
    """comps: iterable of (context, mode, gain, harm rise). Signature vs baseline pooled over contexts.
    RESTORE = largest reduction in harm rise; DRIVE = largest gain increase among the rest."""
    g, h = {}, {}
    for _, m, gain, rise in comps:
        g.setdefault(m, []).append(gain)
        h.setdefault(m, []).append(rise)
    if baseline not in g:
        return {}
    mg = {m: sum(v) / len(v) - sum(g[baseline]) / len(g[baseline]) for m, v in g.items() if m != baseline}
    mh = {m: sum(v) / len(v) - sum(h[baseline]) / len(h[baseline]) for m, v in h.items() if m != baseline}
    if not mh:
        return {}
    restore = min(mh, key=mh.get)
    rest = {m: v for m, v in mg.items() if m != restore}
    out = {"RESTORE": restore}
    if rest:
        out["DRIVE"] = max(rest, key=rest.get)
    return out


def role_table(table: dict, source_roles: dict) -> dict:
    inv = {a: r for r, a in source_roles.items()}
    return {c: inv.get(table.get(c), "BASELINE") for c in W.CONTEXTS}


def from_roles(rtable: dict, target_roles: dict, baseline=BASELINE) -> dict:
    return {c: target_roles.get(r, baseline) if r != "BASELINE" else baseline for c, r in rtable.items()}
