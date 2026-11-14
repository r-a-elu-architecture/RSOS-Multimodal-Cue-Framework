# LIA-G3 — genealogy recovery from probe fingerprints: results

Design: [`AGENTS.md`](../AGENTS.md) §11.7; choices in the docstring of [`rsxv/lia_g3.py`](../rsxv/lia_g3.py).
Data: committed changes in the REPURPOSE runs of W5-R3 (held-out regimes).

Runs scored: 8; excluded (no planted and no predicted edges): 1192. Planted edges: 8. Fingerprint recall: 0.125. Parent accuracy given a fingerprint: 0.000. Intervals: two-sided 0.9917.

| Scope | runs | F1 LIA-DIRECT3 | F1 TEMPORAL | F1 RANDOM | DIRECT3−TEMPORAL [lo, hi] | DIRECT3−RANDOM [lo, hi] |
|---|---|---|---|---|---|---|
| all | 8 | 0.000 | 0.000 | 0.000 | +0.000 [+0.000, +0.000] | +0.000 [+0.000, +0.000] |
| agent | 5 | 0.000 | 0.000 | 0.000 | +0.000 [+0.000, +0.000] | +0.000 [+0.000, +0.000] |
| person | 3 | 0.000 | 0.000 | 0.000 | +0.000 [+0.000, +0.000] | +0.000 [+0.000, +0.000] |

**LIA-G3: FAIL** (registered: beats TEMPORAL and RANDOM, mean F1 ≥ 0.70).
