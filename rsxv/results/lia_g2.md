# LIA-G2 — genealogy recovery with the architecture's parent rule: results

Design: [`AGENTS.md`](../AGENTS.md) §11.6; choices in the docstring of [`rsxv/lia_g2.py`](../rsxv/lia_g2.py).
Data: committed changes in the REPURPOSE runs of W5-R2 (held-out regimes).

Runs scored: 941; excluded (no planted and no predicted edges): 259. Planted edges: 3391. Slot recall: 0.398. Parent accuracy given a found slot: 0.384. Intervals: two-sided 0.9875.

| Scope | runs | F1 LIA-DIRECT2 | F1 TEMPORAL | F1 RANDOM | DIRECT2−TEMPORAL [lo, hi] | DIRECT2−RANDOM [lo, hi] |
|---|---|---|---|---|---|---|
| all | 941 | 0.123 | 0.012 | 0.037 | +0.111 [+0.097, +0.126] | +0.086 [+0.071, +0.101] |
| agent | 600 | 0.194 | 0.019 | 0.059 | +0.175 [+0.154, +0.195] | +0.135 [+0.114, +0.156] |
| person | 341 | 0.000 | 0.000 | 0.000 | +0.000 [+0.000, +0.000] | +0.000 [+0.000, +0.000] |

**LIA-G2: FAIL** (registered: beats TEMPORAL and RANDOM, mean F1 ≥ 0.70).
