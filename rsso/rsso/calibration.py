"""Personal glyph calibration: Bradley-Terry ranking from pairwise choices, with adaptive pair selection.

The person sees two glyphs and picks the one that feels more like the tier (for example, more courage
and agency for the Lion tier). After about 2n comparisons for n candidates, the ranking is usually stable.
Each candidate gets a virtual half-win against a reference of strength 1, which keeps estimates finite
when a glyph has won or lost every comparison.

Mirrors btFit / nextPair in docs/js/ugcl.js (identical results, tested).
"""
from __future__ import annotations

import math


def bt_fit(n: int, comparisons: list[tuple[int, int]], iters: int = 200) -> list[float]:
    """comparisons: (winner, loser) pairs. Returns log-strengths (mean 0 on the log scale)."""
    w = [1.0] * n
    wins = [0.0] * n
    pairs: dict[str, int] = {}
    for a, b in comparisons:
        wins[a] += 1
        k = f"{a},{b}" if a < b else f"{b},{a}"
        pairs[k] = pairs.get(k, 0) + 1
    for _ in range(iters):
        for i in range(n):
            den = 0.0
            for k, c in pairs.items():
                a, b = map(int, k.split(","))
                if a == i or b == i:
                    j = b if a == i else a
                    den += c / (w[i] + w[j])
            w[i] = (wins[i] + 0.5) / (den + 0.5 / (w[i] + 1) * 2) if den > 0 else w[i]
        g = math.exp(sum(math.log(x) for x in w) / n)
        w = [x / g for x in w]
    return [math.log(x) for x in w]


def next_pair(n: int, comparisons: list[tuple[int, int]], scores: list[float]) -> tuple[int, int]:
    """The most informative next comparison: close in strength, rarely compared, not yet asked."""
    count = [0] * n
    seen = set()
    for a, b in comparisons:
        count[a] += 1; count[b] += 1
        seen.add(f"{a},{b}" if a < b else f"{b},{a}")
    best = None
    for i in range(n):
        for j in range(i + 1, n):
            cost = (10 if f"{i},{j}" in seen else 0) + abs(scores[i] - scores[j]) + 0.5 * (count[i] + count[j])
            if best is None or cost < best[0] - 1e-12:
                best = (cost, i, j)
    return best[1], best[2]


def simulate_session(true_strength: list[float], n_comparisons: int, noise: float = 1.0, seed: int = 0):
    """A simulated person choosing between glyphs by a noisy comparison of true strengths (for testing)."""
    import random
    rng = random.Random(seed)
    n = len(true_strength); comps = []; scores = [0.0] * n
    for _ in range(n_comparisons):
        i, j = next_pair(n, comps, scores)
        p_i = 1 / (1 + math.exp(-(true_strength[i] - true_strength[j]) / noise))
        comps.append((i, j) if rng.random() < p_i else (j, i))
        scores = bt_fit(n, comps, iters=60)
    return scores, comps
