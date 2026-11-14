# W5-R2 confirmation (persons): seeds + 100000, install hypothesis calm_better where the regime sets none

Design: [`AGENTS.md`](../AGENTS.md) §11.6, registered before any code. Operational choices fixed before the run are
listed in the module docstring of [`rsxv/w5r2_experiments.py`](../rsxv/w5r2_experiments.py).
Intervals: paired bootstrap, two-sided 0.9917. Primary outcome: mean per-tick mission score (§11.2) over 120 ticks.

## person: PASS

Training table (pooled ledger, 50 × 300 ticks): `{'calm': 'BEAR', 'rising': 'BEAR', 'loaded': 'BEAR', 'crisis': 'BEAR'}`; roles `{'RESTORE': 'BEAR', 'DRIVE': 'LEOPARD', 'STABILISE': 'BEAR'}`

| Regime | REPURPOSE | REPAIR | RANDOM-MECH | NONE | R−REPAIR [lo, hi] | R−RANDOM [lo, hi] | R−NONE lo | beats | non-inf | safe |
|---|---|---|---|---|---|---|---|---|---|---|
| E1 | 0.1257 | 0.1193 | 0.1235 | 0.1257 | +0.0064 [+0.0056, +0.0072] | +0.0022 [+0.0009, +0.0036] | +0.0000 | True | True | True |
| E2 | 0.1282 | 0.1211 | 0.1262 | 0.1282 | +0.0071 [+0.0063, +0.0079] | +0.0020 [+0.0006, +0.0037] | +0.0000 | True | True | True |
| E3 | 0.1377 | 0.1373 | 0.1377 | 0.1377 | +0.0004 [+0.0000, +0.0009] | +0.0000 [+0.0000, +0.0000] | +0.0000 | False | True | True |

R2 machinery per regime (REPURPOSE runs): E1: {'commit_direct': 173, 'probe_start': 0, 'probe_commit': 0, 'probe_end': 0, 'rollback': 0, 'refused': 0}; E2: {'commit_direct': 172, 'probe_start': 0, 'probe_commit': 0, 'probe_end': 0, 'rollback': 0, 'refused': 0}; E3: {'commit_direct': 5, 'probe_start': 0, 'probe_commit': 0, 'probe_end': 0, 'rollback': 0, 'refused': 0}

| Regime | spikes/run R / REPAIR / RANDOM / NONE | failure nodes | resolutions | mechanisms applied | open > 25 ticks | audit failures |
|---|---|---|---|---|---|---|
| E1 | 0.80 / 0.80 / 0.80 / 0.80 | 173 | {'new_mechanism': 173, 'updated_mechanism': 0, 'no_change': 0} | 173 | 0 | 0 |
| E2 | 0.81 / 0.81 / 0.81 / 0.81 | 172 | {'new_mechanism': 172, 'updated_mechanism': 0, 'no_change': 0} | 172 | 0 | 0 |
| E3 | 0.03 / 0.03 / 0.03 / 0.03 | 5 | {'new_mechanism': 5, 'updated_mechanism': 0, 'no_change': 0} | 5 | 0 | 0 |

Person model v2 lexicographic score (safety, depth, agency), means per arm (reported, not a pass condition):

- E1: REPURPOSE (-1.305, 3.475, 9.9271); REPAIR (-1.305, 3.475, 9.9333); RANDOM-MECH (-1.305, 3.475, 9.9271); NONE (-1.305, 3.475, 9.9271)
- E2: REPURPOSE (-1.245, 3.775, 9.8743); REPAIR (-1.245, 3.775, 9.8829); RANDOM-MECH (-1.245, 3.775, 9.8743); NONE (-1.245, 3.775, 9.8743)
- E3: REPURPOSE (-1.065, 4.675, 9.8901); REPAIR (-1.065, 4.675, 9.8901); RANDOM-MECH (-1.065, 4.675, 9.8901); NONE (-1.065, 4.675, 9.8901)
