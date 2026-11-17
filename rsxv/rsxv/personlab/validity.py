"""PERSONLAB step 5c (spec/PERSONLAB.md §7c): reader stress against the seekers' own intensity ratings."""
from __future__ import annotations

import numpy as np
from scipy.stats import spearmanr

LEVEL = 1 - 0.05 / 3


def rho(x, y) -> float:
    r = spearmanr(x, y).statistic
    return float(r) if r == r else 0.0


def boot(x, y, B=2000, seed=12345, level=LEVEL):
    x, y = np.asarray(x, float), np.asarray(y, float)
    rng = np.random.default_rng(seed)
    n = len(x)
    st = [rho(x[i], y[i]) for i in (rng.integers(0, n, n) for _ in range(B))]
    a = (1 - level) / 2
    return rho(x, y), float(np.quantile(st, a)), float(np.quantile(st, 1 - a))


def verdict(res: dict) -> str:
    ok = all(r[1] > 0 for r in res.values())
    if ok and all(r[0] >= 0.3 for r in res.values()):
        return "VALID"
    return "PARTIAL" if ok else "NOT VALID"
