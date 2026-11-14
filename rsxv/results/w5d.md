# W5d — negative certificates and a fail-safe tube (ninth transfer test): results

Design: [`AGENTS.md`](../AGENTS.md) §11.8, registered before any code; operational choices fixed before the run are in
the docstring of [`rsxv/w5d_experiments.py`](../rsxv/w5d_experiments.py). Level 0.05 / 9 (99.44% paired bootstrap intervals).
All environments are stated models; no number here comes from people or production agents.

## Certificates issued by each source

- **person** (roles `{'RESTORE': 'BEAR', 'DRIVE': 'LEOPARD', 'STABILISE': 'BEAR'}`): calm: STABILISE (BEAR, +0.904 [+0.605, +1.204], n=110); rising: STABILISE (BEAR, +0.750 [+0.340, +1.159], n=49); loaded: STABILISE (BEAR, +0.967 [+0.754, +1.180], n=180); crisis: STABILISE (BEAR, +0.762 [+0.563, +0.961], n=179)
- **agent** (roles `{'RESTORE': 'LEOPARD', 'DRIVE': 'TIGER', 'STABILISE': 'LEOPARD'}`): calm: STABILISE (LEOPARD, +0.684 [+0.513, +0.855], n=360); rising: STABILISE (LEOPARD, +1.924 [+1.371, +2.478], n=42); loaded: STABILISE (LEOPARD, +1.661 [+1.235, +2.086], n=76); crisis: STABILISE (LEOPARD, +1.592 [+0.994, +2.189], n=33)
- **agent_v2** (roles `{'RESTORE': 'LEOPARD', 'DRIVE': 'TIGER', 'STABILISE': 'BEAR'}`): calm: RESTORE (LEOPARD, +0.596 [+0.267, +0.925], n=102)

## agent → person, pilot of 4

W5d adopted a non-baseline table in 16/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5d | +0.0072 | 2.109 |
| PILOT-ONLY | -0.0256 | 2.166 |
| W3C | -0.0965 | 2.375 |
| RANDOM-FUNC | -0.0965 | 2.375 |
| W5d-NO-FAIL | -0.0117 | 2.178 |
| NONE | -0.0965 | 2.375 |
| ORACLE (upper bound) | +0.2368 | |

| Contrast (99%) | Estimate |
|---|---|
| W5d-PILOT-ONLY | +0.0328 [+0.0288, +0.0372] |
| W5d-NONE | +0.1037 [+0.0890, +0.1179] |
| W5d-RANDOM-FUNC | +0.1037 [+0.0890, +0.1179] |
| W5d-W3C | +0.1037 [+0.0890, +0.1179] |
| W5d − W5d-NO-FAIL (ablation) | +0.0188 [+0.0170, +0.0206] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **yes**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 19, false certificates 0.

## agent → person, pilot of 8

W5d adopted a non-baseline table in 20/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5d | +0.0948 | 1.385 |
| PILOT-ONLY | +0.0771 | 1.597 |
| W3C | -0.0965 | 2.375 |
| RANDOM-FUNC | -0.0965 | 2.375 |
| W5d-NO-FAIL | +0.1042 | 1.375 |
| NONE | -0.0965 | 2.375 |
| ORACLE (upper bound) | +0.2368 | |

| Contrast (99%) | Estimate |
|---|---|
| W5d-PILOT-ONLY | +0.0177 [+0.0117, +0.0230] |
| W5d-NONE | +0.1912 [+0.1714, +0.2109] |
| W5d-RANDOM-FUNC | +0.1912 [+0.1714, +0.2109] |
| W5d-W3C | +0.1912 [+0.1714, +0.2109] |
| W5d − W5d-NO-FAIL (ablation) | -0.0094 [-0.0117, -0.0072] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **yes**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 36, false certificates 0.

## agent → person, pilot of 16

W5d adopted a non-baseline table in 20/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5d | +0.1921 | 0.534 |
| PILOT-ONLY | +0.1607 | 0.888 |
| W3C | -0.0897 | 2.648 |
| RANDOM-FUNC | -0.0965 | 2.375 |
| W5d-NO-FAIL | +0.2052 | 0.349 |
| NONE | -0.0965 | 2.375 |
| ORACLE (upper bound) | +0.2368 | |

| Contrast (99%) | Estimate |
|---|---|
| W5d-PILOT-ONLY | +0.0314 [+0.0266, +0.0364] |
| W5d-NONE | +0.2886 [+0.2780, +0.2990] |
| W5d-RANDOM-FUNC | +0.2886 [+0.2780, +0.2990] |
| W5d-W3C | +0.2818 [+0.2708, +0.2925] |
| W5d − W5d-NO-FAIL (ablation) | -0.0131 [-0.0143, -0.0115] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **yes**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 56, false certificates 0.

## person → agent, pilot of 4

W5d adopted a non-baseline table in 10/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5d | -0.0460 | 1.127 |
| PILOT-ONLY | -0.0531 | 1.150 |
| W3C | -0.0815 | 1.445 |
| RANDOM-FUNC | -0.0790 | 1.417 |
| W5d-NO-FAIL | -0.0441 | 1.047 |
| NONE | -0.0815 | 1.445 |
| ORACLE (upper bound) | +0.0935 | |

| Contrast (99%) | Estimate |
|---|---|
| W5d-PILOT-ONLY | +0.0071 [+0.0060, +0.0082] |
| W5d-NONE | +0.0355 [+0.0302, +0.0402] |
| W5d-RANDOM-FUNC | +0.0330 [+0.0282, +0.0373] |
| W5d-W3C | +0.0355 [+0.0302, +0.0402] |
| W5d − W5d-NO-FAIL (ablation) | -0.0019 [-0.0032, -0.0004] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **yes**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 7, false certificates 0.

## person → agent, pilot of 8

W5d adopted a non-baseline table in 20/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5d | +0.0048 | 0.475 |
| PILOT-ONLY | +0.0028 | 0.455 |
| W3C | -0.0739 | 1.331 |
| RANDOM-FUNC | -0.0779 | 1.418 |
| W5d-NO-FAIL | +0.0041 | 0.469 |
| NONE | -0.0815 | 1.445 |
| ORACLE (upper bound) | +0.0935 | |

| Contrast (99%) | Estimate |
|---|---|
| W5d-PILOT-ONLY | +0.0020 [+0.0014, +0.0026] |
| W5d-NONE | +0.0863 [+0.0724, +0.0999] |
| W5d-RANDOM-FUNC | +0.0828 [+0.0694, +0.0958] |
| W5d-W3C | +0.0788 [+0.0662, +0.0910] |
| W5d − W5d-NO-FAIL (ablation) | +0.0007 [+0.0005, +0.0010] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **yes**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: False. Adopted contexts 18, false certificates 0.

## person → agent, pilot of 16

W5d adopted a non-baseline table in 20/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5d | -0.0002 | 0.346 |
| PILOT-ONLY | -0.0017 | 0.335 |
| W3C | -0.0325 | 0.701 |
| RANDOM-FUNC | -0.0815 | 1.445 |
| W5d-NO-FAIL | -0.0009 | 0.340 |
| NONE | -0.0815 | 1.445 |
| ORACLE (upper bound) | +0.0935 | |

| Contrast (99%) | Estimate |
|---|---|
| W5d-PILOT-ONLY | +0.0015 [+0.0009, +0.0020] |
| W5d-NONE | +0.0813 [+0.0672, +0.0939] |
| W5d-RANDOM-FUNC | +0.0813 [+0.0672, +0.0939] |
| W5d-W3C | +0.0324 [+0.0271, +0.0375] |
| W5d − W5d-NO-FAIL (ablation) | +0.0007 [+0.0005, +0.0010] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **yes**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 36, false certificates 0.

## agent_v2 → person, pilot of 4

W5d adopted a non-baseline table in 6/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5d | -0.0507 | 2.208 |
| PILOT-ONLY | -0.0256 | 2.166 |
| W3C | -0.0965 | 2.375 |
| RANDOM-FUNC | -0.0965 | 2.375 |
| W5d-NO-FAIL | -0.0278 | 2.125 |
| NONE | -0.0965 | 2.375 |
| ORACLE (upper bound) | +0.2368 | |

| Contrast (99%) | Estimate |
|---|---|
| W5d-PILOT-ONLY | -0.0251 [-0.0291, -0.0212] |
| W5d-NONE | +0.0458 [+0.0377, +0.0542] |
| W5d-RANDOM-FUNC | +0.0458 [+0.0377, +0.0542] |
| W5d-W3C | +0.0458 [+0.0377, +0.0542] |
| W5d − W5d-NO-FAIL (ablation) | -0.0229 [-0.0271, -0.0188] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 6, false certificates 0.

## agent_v2 → person, pilot of 8

W5d adopted a non-baseline table in 15/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5d | +0.0180 | 1.959 |
| PILOT-ONLY | +0.0771 | 1.597 |
| W3C | -0.0965 | 2.375 |
| RANDOM-FUNC | -0.0965 | 2.375 |
| W5d-NO-FAIL | +0.0104 | 1.987 |
| NONE | -0.0965 | 2.375 |
| ORACLE (upper bound) | +0.2368 | |

| Contrast (99%) | Estimate |
|---|---|
| W5d-PILOT-ONLY | -0.0591 [-0.0678, -0.0505] |
| W5d-NONE | +0.1145 [+0.0941, +0.1354] |
| W5d-RANDOM-FUNC | +0.1145 [+0.0941, +0.1354] |
| W5d-W3C | +0.1145 [+0.0941, +0.1354] |
| W5d − W5d-NO-FAIL (ablation) | +0.0076 [+0.0063, +0.0090] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: False. Adopted contexts 15, false certificates 0.

## agent_v2 → person, pilot of 16

W5d adopted a non-baseline table in 19/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5d | +0.0485 | 1.848 |
| PILOT-ONLY | +0.1607 | 0.888 |
| W3C | -0.0965 | 2.375 |
| RANDOM-FUNC | -0.0965 | 2.375 |
| W5d-NO-FAIL | +0.0485 | 1.848 |
| NONE | -0.0965 | 2.375 |
| ORACLE (upper bound) | +0.2368 | |

| Contrast (99%) | Estimate |
|---|---|
| W5d-PILOT-ONLY | -0.1122 [-0.1280, -0.0974] |
| W5d-NONE | +0.1450 [+0.1192, +0.1715] |
| W5d-RANDOM-FUNC | +0.1450 [+0.1192, +0.1715] |
| W5d-W3C | +0.1450 [+0.1192, +0.1715] |
| W5d − W5d-NO-FAIL (ablation) | +0.0000 [+0.0000, +0.0000] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: False. Adopted contexts 19, false certificates 0.

## person → agent_v2, pilot of 4

W5d adopted a non-baseline table in 1/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5d | -0.0692 | 1.380 |
| PILOT-ONLY | -0.0662 | 1.380 |
| W3C | -0.0696 | 1.380 |
| RANDOM-FUNC | -0.0696 | 1.380 |
| W5d-NO-FAIL | -0.0696 | 1.380 |
| NONE | -0.0696 | 1.380 |
| ORACLE (upper bound) | +0.0216 | |

| Contrast (99%) | Estimate |
|---|---|
| W5d-PILOT-ONLY | -0.0031 [-0.0033, -0.0029] |
| W5d-NONE | +0.0004 [+0.0003, +0.0005] |
| W5d-RANDOM-FUNC | +0.0004 [+0.0003, +0.0005] |
| W5d-W3C | +0.0004 [+0.0003, +0.0005] |
| W5d − W5d-NO-FAIL (ablation) | +0.0004 [+0.0003, +0.0005] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 0, false certificates 0.

## person → agent_v2, pilot of 8

W5d adopted a non-baseline table in 9/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5d | -0.0662 | 1.382 |
| PILOT-ONLY | -0.0651 | 1.378 |
| W3C | -0.0696 | 1.380 |
| RANDOM-FUNC | -0.0693 | 1.378 |
| W5d-NO-FAIL | -0.0662 | 1.382 |
| NONE | -0.0696 | 1.380 |
| ORACLE (upper bound) | +0.0216 | |

| Contrast (99%) | Estimate |
|---|---|
| W5d-PILOT-ONLY | -0.0010 [-0.0018, -0.0002] |
| W5d-NONE | +0.0035 [+0.0026, +0.0045] |
| W5d-RANDOM-FUNC | +0.0031 [+0.0023, +0.0040] |
| W5d-W3C | +0.0035 [+0.0026, +0.0045] |
| W5d − W5d-NO-FAIL (ablation) | +0.0000 [+0.0000, +0.0000] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 0, false certificates 0.

## person → agent_v2, pilot of 16

W5d adopted a non-baseline table in 5/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5d | -0.0616 | 1.381 |
| PILOT-ONLY | -0.0636 | 1.369 |
| W3C | -0.0696 | 1.380 |
| RANDOM-FUNC | -0.0684 | 1.375 |
| W5d-NO-FAIL | -0.0688 | 1.381 |
| NONE | -0.0696 | 1.380 |
| ORACLE (upper bound) | +0.0216 | |

| Contrast (99%) | Estimate |
|---|---|
| W5d-PILOT-ONLY | +0.0020 [+0.0003, +0.0037] |
| W5d-NONE | +0.0081 [+0.0076, +0.0085] |
| W5d-RANDOM-FUNC | +0.0069 [+0.0059, +0.0077] |
| W5d-W3C | +0.0081 [+0.0076, +0.0085] |
| W5d − W5d-NO-FAIL (ablation) | +0.0072 [+0.0068, +0.0076] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **yes**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 0, false certificates 0.

**Certificate audit (pilot 8, pooled):** 0 false of 69 adopted — holds.

**Primary criterion (pilot 8): FAIL.** Directions meeting all three comparisons: ['agent->person', 'person->agent'].

**Strong pass (three of four directions): NO.** Jam prediction: 132 of 260 correct at pilot 8. Warnings issued by each source: {'person': {'crisis': ['DRIVE', 'unassigned']}, 'agent': {'calm': ['unassigned'], 'loaded': ['unassigned']}, 'agent_v2': {'loaded': ['unassigned'], 'crisis': ['unassigned']}}.

**W5d overall: FAIL.**

Ablation W5d-NO-FAIL: the same pilot without the failure rule (reported, not a pass condition).
