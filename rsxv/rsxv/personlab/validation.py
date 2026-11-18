"""PERSONLAB step 5 (spec/PERSONLAB.md §7): fit the intensity dynamics on development conversations, validate final
intensity on the held-out 100 against three baselines and a no-profile ablation."""
from __future__ import annotations

import random

import numpy as np

from .person import STRATEGY_TO_ACTION

ACTS = ("STABILISE", "EXPLORE", "SUGGEST", "SHARE", "NONE")


def actions(conv) -> list:
    """One action per supporter turn, from its strategy label (unlabelled or unknown -> NONE)."""
    return [STRATEGY_TO_ACTION.get((t.get("annotation") or {}).get("strategy"), "NONE")
            for t in conv["dialog"] if t["speaker"] == "supporter"]


def predict_final(theta, I0: float, acts: list, signals: int = 0) -> float:
    """§7: expected intensity path. theta = [r_STABILISE, r_EXPLORE, r_SUGGEST, r_SHARE, r_NONE, drift, lam]."""
    r = dict(zip(ACTS, theta[:5]))
    drift, lam = theta[5], theta[6]
    up = drift * (1 + 0.25 * min(4, signals))
    I = I0
    for a in acts:
        I = min(5.0, max(1.0, I + up))
        I = min(5.0, max(1.0, I - r[a]))
        I = min(5.0, max(1.0, I - lam * (I - 1)))
    return I


def _bounds(theta):
    t = list(theta)
    t[:5] = [min(1.0, max(-1.0, x)) for x in t[:5]]
    t[5] = min(1.0, max(0.0, t[5]))
    t[6] = min(1.0, max(0.0, t[6]))
    return t


def fit(dev, starts=5, seed=2028):
    """dev: list of (I0, acts, final). Nelder-Mead on MAE, from the defaults and `starts` random starts."""
    from scipy.optimize import minimize

    def loss(th):
        th = _bounds(th)
        return float(np.mean([abs(predict_final(th, i0, a) - f) for i0, a, f in dev]))
    rng = random.Random(seed)
    inits = [[0.2, 0.2, 0.2, 0.2, 0.0, 0.05, 0.02]]
    inits += [[rng.uniform(-0.2, 0.4) for _ in range(5)] + [rng.uniform(0, 0.2), rng.uniform(0, 0.1)] for _ in range(starts)]
    best = None
    for x0 in inits:
        r = minimize(loss, x0, method="Nelder-Mead", options={"maxiter": 4000, "xatol": 1e-4, "fatol": 1e-5})
        th = _bounds(r.x)
        L = loss(th)
        if best is None or L < best[1]:
            best = (th, L)
    return best


def linear_fit(rows):
    """B3: least squares of final on [1, initial, count per action]. rows: (I0, acts, final)."""
    X = np.array([[1.0, i0] + [a.count(x) for x in ACTS] for i0, a, _ in rows])
    y = np.array([f for _, _, f in rows])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return coef


def linear_predict(coef, I0, acts):
    return float(np.dot(coef, [1.0, I0] + [acts.count(x) for x in ACTS]))


def paired_interval(e_model, e_base, level, B=2000, seed=12345):
    """Interval of mean(|e_model| - |e_base|) by paired bootstrap over conversations."""
    d = np.abs(np.array(e_model)) - np.abs(np.array(e_base))
    rng = np.random.default_rng(seed)
    n = len(d)
    stats = np.array([d[rng.integers(0, n, n)].mean() for _ in range(B)])
    a = (1 - level) / 2
    return float(d.mean()), float(np.quantile(stats, a)), float(np.quantile(stats, 1 - a))
