# MSE — multi-scale echo on the private record (origin, not a test)

Definitions: [`AGENTS.md`](../AGENTS.md) §11.8; code [`rsxv/mse.py`](../rsxv/mse.py). Held-out half of the record (nodes > 290);
the record was read during design, so these are origin numbers. The registered test runs on public data in Phase 9.

| Scale | Measure | n | Observed | Baseline / interval | Clears 0.01/3 |
|---|---|---|---|---|---|
| notes | reentry | 145 | 0.3136 | 0.1350 (p = 0.001) | True |
| notes | carry_forward | 115 | +0.506 (re-entered − own) | [+0.403, +0.589] | True |
| phrases | reentry | 145 | 0.0818 | 0.0005 (p = 0.001) | True |
| phrases | carry_forward | 46 | +0.237 (re-entered − own) | [+0.101, +0.407] | True |
| melody | reentry | 145 | 0.0382 | 0.0292 (p = 0.094) | False |
| melody | carry_forward | 24 | -0.006 (re-entered − own) | [-0.013, -0.001] | False |
| melody | inheritance | 143 | 0.5526 | 0.4927 (p = 0.001) | True |
