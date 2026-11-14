# LIA-G — genealogy recovery from behaviour alone: results

Design: [`AGENTS.md`](../AGENTS.md) §11.5; operational choices fixed before the run are in the docstring of
[`rsxv/lia_g.py`](../rsxv/lia_g.py). Data: the REPURPOSE runs of W5-R (held-out regimes only).

Runs scored: 560; runs with no planted and no predicted edges (excluded): 640.
Intervals: paired bootstrap, two-sided 0.975.

| Scope | runs | F1 LIA-DIRECT | F1 TEMPORAL | F1 RANDOM | DIRECT−TEMPORAL [lo, hi] | DIRECT−RANDOM [lo, hi] |
|---|---|---|---|---|---|---|
| all | 560 | 0.122 | 0.058 | 0.132 | +0.064 [+0.038, +0.089] | -0.010 [-0.042, +0.020] |
| agent | 560 | 0.122 | 0.058 | 0.132 | +0.064 [+0.038, +0.089] | -0.010 [-0.042, +0.020] |
| person | 0 | — | — | — | — | — |

**LIA-G: FAIL** (registered: LIA-DIRECT beats TEMPORAL and RANDOM over all runs, mean F1 ≥ 0.70).
