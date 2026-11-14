# W5-R — failure repurposing vs ordinary repair under held-out extreme regimes: results

Design: [`AGENTS.md`](../AGENTS.md) §11.5, registered before any code. Operational choices fixed before the run are
listed in the module docstring of [`rsxv/w5r_experiments.py`](../rsxv/w5r_experiments.py).
Intervals: paired bootstrap, two-sided 0.9833. Primary outcome: mean per-tick mission score (§11.2) over 120 ticks.

## agent: FAIL

Training table (pooled ledger, 50 × 300 ticks): `{'calm': 'LEOPARD', 'rising': 'LEOPARD', 'loaded': 'TIGER', 'crisis': 'LION'}`; roles `{'RESTORE': 'LEOPARD', 'DRIVE': 'TIGER', 'STABILISE': 'BEAR'}`

| Regime | REPURPOSE | REPAIR | RANDOM-MECH | NONE | R−REPAIR [lo, hi] | R−RANDOM [lo, hi] | R−NONE lo | beats | non-inf | safe |
|---|---|---|---|---|---|---|---|---|---|---|
| E1 | -0.2522 | -0.2469 | -0.2388 | -0.2526 | -0.0053 [-0.0191, +0.0094] | -0.0135 [-0.0275, +0.0021] | -0.0014 | False | True | False |
| E2 | -0.0351 | -0.0901 | -0.0475 | -0.0351 | +0.0551 [+0.0506, +0.0593] | +0.0125 [+0.0064, +0.0185] | +0.0000 | True | True | True |
| E3 | -0.0068 | -0.0557 | -0.0140 | -0.0068 | +0.0489 [+0.0427, +0.0550] | +0.0073 [+0.0014, +0.0133] | +0.0000 | True | True | True |

| Regime | spikes/run R / REPAIR / RANDOM / NONE | failure nodes | resolutions | mechanisms applied | open > 25 ticks | audit failures |
|---|---|---|---|---|---|---|
| E1 | 6.29 / 5.57 / 6.66 / 6.30 | 7762 | {'new_mechanism': 424, 'updated_mechanism': 0, 'no_change': 5689} | 424 | 0 | 0 |
| E2 | 3.15 / 3.16 / 3.25 / 3.15 | 5278 | {'new_mechanism': 343, 'updated_mechanism': 0, 'no_change': 3783} | 343 | 0 | 0 |
| E3 | 2.12 / 2.03 / 2.15 / 2.12 | 5185 | {'new_mechanism': 335, 'updated_mechanism': 0, 'no_change': 3751} | 335 | 0 | 0 |

## person: FAIL

Training table (pooled ledger, 50 × 300 ticks): `{'calm': 'BEAR', 'rising': 'BEAR', 'loaded': 'BEAR', 'crisis': 'BEAR'}`; roles `{'RESTORE': 'BEAR', 'DRIVE': 'LEOPARD', 'STABILISE': 'BEAR'}`

| Regime | REPURPOSE | REPAIR | RANDOM-MECH | NONE | R−REPAIR [lo, hi] | R−RANDOM [lo, hi] | R−NONE lo | beats | non-inf | safe |
|---|---|---|---|---|---|---|---|---|---|---|
| E1 | 0.1292 | 0.1223 | 0.1292 | 0.1292 | +0.0069 [+0.0061, +0.0077] | +0.0000 [+0.0000, +0.0000] | +0.0000 | False | True | True |
| E2 | 0.1290 | 0.1220 | 0.1290 | 0.1290 | +0.0069 [+0.0062, +0.0077] | +0.0000 [+0.0000, +0.0000] | +0.0000 | False | True | True |
| E3 | 0.1343 | 0.1342 | 0.1343 | 0.1343 | +0.0001 [+0.0000, +0.0004] | +0.0000 [+0.0000, +0.0000] | +0.0000 | False | True | True |

| Regime | spikes/run R / REPAIR / RANDOM / NONE | failure nodes | resolutions | mechanisms applied | open > 25 ticks | audit failures |
|---|---|---|---|---|---|---|
| E1 | 0.80 / 0.80 / 0.80 / 0.80 | 352 | {'new_mechanism': 0, 'updated_mechanism': 0, 'no_change': 352} | 0 | 0 | 0 |
| E2 | 0.81 / 0.81 / 0.81 / 0.81 | 344 | {'new_mechanism': 0, 'updated_mechanism': 0, 'no_change': 344} | 0 | 0 | 0 |
| E3 | 0.01 / 0.01 / 0.01 / 0.01 | 4 | {'new_mechanism': 0, 'updated_mechanism': 0, 'no_change': 4} | 0 | 0 | 0 |

Person model v2 lexicographic score (safety, depth, agency), means per arm (reported, not a pass condition):

- E1: REPURPOSE (-1.39, 3.05, 9.9171); REPAIR (-1.39, 3.05, 9.9223); RANDOM-MECH (-1.39, 3.05, 9.9171); NONE (-1.39, 3.05, 9.9171)
- E2: REPURPOSE (-1.29, 3.55, 9.8944); REPAIR (-1.29, 3.55, 9.8972); RANDOM-MECH (-1.29, 3.55, 9.8944); NONE (-1.29, 3.55, 9.8944)
- E3: REPURPOSE (-1.03, 4.85, 9.8938); REPAIR (-1.03, 4.85, 9.8938); RANDOM-MECH (-1.03, 4.85, 9.8938); NONE (-1.03, 4.85, 9.8938)
