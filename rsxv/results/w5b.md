# W5b — transfer with a pilot that fills every gate cell (sixth attempt): results

Design: [`AGENTS.md`](../AGENTS.md) §11.6, registered before any code; operational choices fixed before the run are in
the docstring of [`rsxv/w5b_experiments.py`](../rsxv/w5b_experiments.py). Level 0.05 / 6 (99.17% paired bootstrap intervals).
All environments are stated models; no number here comes from people or production agents.

## Certificates issued by each source

- **person** (roles `{'RESTORE': 'BEAR', 'DRIVE': 'LEOPARD', 'STABILISE': 'BEAR'}`): calm: STABILISE (BEAR, +0.684 [+0.404, +0.963], n=127); rising: STABILISE (BEAR, +0.838 [+0.343, +1.333], n=40); loaded: STABILISE (BEAR, +0.921 [+0.730, +1.113], n=162); crisis: STABILISE (BEAR, +1.012 [+0.763, +1.260], n=168)
- **agent** (roles `{'RESTORE': 'LEOPARD', 'DRIVE': 'TIGER', 'STABILISE': 'LEOPARD'}`): calm: STABILISE (LEOPARD, +0.678 [+0.480, +0.875], n=331); rising: STABILISE (LEOPARD, +1.590 [+1.080, +2.099], n=48); loaded: STABILISE (LEOPARD, +1.434 [+1.083, +1.785], n=87); crisis: STABILISE (LEOPARD, +1.666 [+1.158, +2.174], n=32)
- **agent_v2** (roles `{'RESTORE': 'LEOPARD', 'DRIVE': 'TIGER', 'STABILISE': 'BEAR'}`): calm: RESTORE (LEOPARD, +0.601 [+0.309, +0.894], n=104); rising: RESTORE (LEOPARD, +1.370 [+0.497, +2.244], n=25)

## agent → person, pilot of 4

W5b adopted a non-baseline table in 15/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5b | +0.0024 | 2.146 |
| PILOT-ONLY | -0.0046 | 2.109 |
| W3C | -0.0946 | 2.480 |
| RANDOM-FUNC | -0.0946 | 2.480 |
| W5b-NO-FAIL | -0.0483 | 2.384 |
| NONE | -0.0946 | 2.480 |
| ORACLE (upper bound) | +0.2423 | |

| Contrast (99%) | Estimate |
|---|---|
| W5b-PILOT-ONLY | +0.0070 [+0.0059, +0.0082] |
| W5b-NONE | +0.0970 [+0.0843, +0.1104] |
| W5b-RANDOM-FUNC | +0.0970 [+0.0843, +0.1104] |
| W5b-W3C | +0.0970 [+0.0843, +0.1104] |
| W5b − W5b-NO-FAIL (ablation) | +0.0507 [+0.0460, +0.0551] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **yes**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: False. Adopted contexts 20, false certificates 0.

## agent → person, pilot of 8

W5b adopted a non-baseline table in 20/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5b | +0.1089 | 1.391 |
| PILOT-ONLY | +0.1067 | 1.333 |
| W3C | -0.0946 | 2.480 |
| RANDOM-FUNC | -0.0946 | 2.480 |
| W5b-NO-FAIL | +0.0805 | 1.607 |
| NONE | -0.0946 | 2.480 |
| ORACLE (upper bound) | +0.2423 | |

| Contrast (99%) | Estimate |
|---|---|
| W5b-PILOT-ONLY | +0.0023 [+0.0007, +0.0037] |
| W5b-NONE | +0.2035 [+0.1856, +0.2214] |
| W5b-RANDOM-FUNC | +0.2035 [+0.1856, +0.2214] |
| W5b-W3C | +0.2035 [+0.1856, +0.2214] |
| W5b − W5b-NO-FAIL (ablation) | +0.0284 [+0.0244, +0.0325] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **yes**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: False. Adopted contexts 41, false certificates 0.

## agent → person, pilot of 16

W5b adopted a non-baseline table in 20/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5b | +0.2051 | 0.458 |
| PILOT-ONLY | +0.1954 | 0.550 |
| W3C | -0.0897 | 2.772 |
| RANDOM-FUNC | -0.0946 | 2.480 |
| W5b-NO-FAIL | +0.1597 | 0.833 |
| NONE | -0.0946 | 2.480 |
| ORACLE (upper bound) | +0.2423 | |

| Contrast (99%) | Estimate |
|---|---|
| W5b-PILOT-ONLY | +0.0097 [+0.0084, +0.0109] |
| W5b-NONE | +0.2997 [+0.2897, +0.3093] |
| W5b-RANDOM-FUNC | +0.2997 [+0.2897, +0.3093] |
| W5b-W3C | +0.2947 [+0.2844, +0.3042] |
| W5b − W5b-NO-FAIL (ablation) | +0.0454 [+0.0365, +0.0536] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **yes**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 62, false certificates 0.

## person → agent, pilot of 4

W5b adopted a non-baseline table in 16/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5b | -0.0098 | 0.689 |
| PILOT-ONLY | -0.0308 | 0.935 |
| W3C | -0.0862 | 1.620 |
| RANDOM-FUNC | -0.0903 | 1.685 |
| W5b-NO-FAIL | -0.0167 | 0.746 |
| NONE | -0.0903 | 1.685 |
| ORACLE (upper bound) | +0.0967 | |

| Contrast (99%) | Estimate |
|---|---|
| W5b-PILOT-ONLY | +0.0210 [+0.0179, +0.0242] |
| W5b-NONE | +0.0805 [+0.0684, +0.0925] |
| W5b-RANDOM-FUNC | +0.0805 [+0.0684, +0.0925] |
| W5b-W3C | +0.0764 [+0.0650, +0.0878] |
| W5b − W5b-NO-FAIL (ablation) | +0.0069 [+0.0059, +0.0079] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **yes**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 16, false certificates 0.

## person → agent, pilot of 8

W5b adopted a non-baseline table in 20/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5b | +0.0048 | 0.425 |
| PILOT-ONLY | +0.0039 | 0.423 |
| W3C | -0.0739 | 1.426 |
| RANDOM-FUNC | -0.0903 | 1.685 |
| W5b-NO-FAIL | +0.0039 | 0.422 |
| NONE | -0.0903 | 1.685 |
| ORACLE (upper bound) | +0.0967 | |

| Contrast (99%) | Estimate |
|---|---|
| W5b-PILOT-ONLY | +0.0009 [+0.0007, +0.0012] |
| W5b-NONE | +0.0951 [+0.0806, +0.1096] |
| W5b-RANDOM-FUNC | +0.0951 [+0.0806, +0.1096] |
| W5b-W3C | +0.0787 [+0.0668, +0.0907] |
| W5b − W5b-NO-FAIL (ablation) | +0.0010 [+0.0007, +0.0012] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **yes**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 28, false certificates 0.

## person → agent, pilot of 16

W5b adopted a non-baseline table in 20/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5b | -0.0044 | 0.400 |
| PILOT-ONLY | -0.0025 | 0.405 |
| W3C | -0.0369 | 0.843 |
| RANDOM-FUNC | -0.0903 | 1.685 |
| W5b-NO-FAIL | -0.0035 | 0.403 |
| NONE | -0.0903 | 1.685 |
| ORACLE (upper bound) | +0.0967 | |

| Contrast (99%) | Estimate |
|---|---|
| W5b-PILOT-ONLY | -0.0018 [-0.0024, -0.0013] |
| W5b-NONE | +0.0859 [+0.0718, +0.0998] |
| W5b-RANDOM-FUNC | +0.0859 [+0.0718, +0.0998] |
| W5b-W3C | +0.0325 [+0.0275, +0.0375] |
| W5b − W5b-NO-FAIL (ablation) | -0.0009 [-0.0012, -0.0006] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 41, false certificates 0.

## agent_v2 → person, pilot of 4

W5b adopted a non-baseline table in 8/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5b | -0.0337 | 2.188 |
| PILOT-ONLY | -0.0046 | 2.109 |
| W3C | -0.0946 | 2.480 |
| RANDOM-FUNC | -0.0932 | 2.474 |
| W5b-NO-FAIL | -0.0550 | 2.329 |
| NONE | -0.0946 | 2.480 |
| ORACLE (upper bound) | +0.2423 | |

| Contrast (99%) | Estimate |
|---|---|
| W5b-PILOT-ONLY | -0.0291 [-0.0323, -0.0259] |
| W5b-NONE | +0.0609 [+0.0506, +0.0715] |
| W5b-RANDOM-FUNC | +0.0594 [+0.0495, +0.0698] |
| W5b-W3C | +0.0609 [+0.0506, +0.0715] |
| W5b − W5b-NO-FAIL (ablation) | +0.0212 [+0.0178, +0.0245] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: False. Adopted contexts 11, false certificates 0.

## agent_v2 → person, pilot of 8

W5b adopted a non-baseline table in 18/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5b | +0.0451 | 1.780 |
| PILOT-ONLY | +0.1067 | 1.333 |
| W3C | -0.0946 | 2.480 |
| RANDOM-FUNC | -0.0946 | 2.480 |
| W5b-NO-FAIL | +0.0366 | 1.840 |
| NONE | -0.0946 | 2.480 |
| ORACLE (upper bound) | +0.2423 | |

| Contrast (99%) | Estimate |
|---|---|
| W5b-PILOT-ONLY | -0.0616 [-0.0681, -0.0548] |
| W5b-NONE | +0.1397 [+0.1167, +0.1636] |
| W5b-RANDOM-FUNC | +0.1397 [+0.1167, +0.1636] |
| W5b-W3C | +0.1397 [+0.1167, +0.1636] |
| W5b − W5b-NO-FAIL (ablation) | +0.0085 [+0.0069, +0.0101] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: False. Adopted contexts 27, false certificates 0.

## agent_v2 → person, pilot of 16

W5b adopted a non-baseline table in 20/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5b | +0.0835 | 1.449 |
| PILOT-ONLY | +0.1954 | 0.550 |
| W3C | -0.0946 | 2.480 |
| RANDOM-FUNC | -0.0946 | 2.480 |
| W5b-NO-FAIL | +0.0878 | 1.427 |
| NONE | -0.0946 | 2.480 |
| ORACLE (upper bound) | +0.2423 | |

| Contrast (99%) | Estimate |
|---|---|
| W5b-PILOT-ONLY | -0.1119 [-0.1318, -0.0900] |
| W5b-NONE | +0.1781 [+0.1499, +0.2061] |
| W5b-RANDOM-FUNC | +0.1781 [+0.1499, +0.2061] |
| W5b-W3C | +0.1781 [+0.1499, +0.2061] |
| W5b − W5b-NO-FAIL (ablation) | -0.0043 [-0.0060, -0.0027] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: False. Adopted contexts 38, false certificates 0.

## person → agent_v2, pilot of 4

W5b adopted a non-baseline table in 0/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5b | -0.0768 | 1.475 |
| PILOT-ONLY | -0.0768 | 1.475 |
| W3C | -0.0768 | 1.475 |
| RANDOM-FUNC | -0.0729 | 1.475 |
| W5b-NO-FAIL | -0.0768 | 1.475 |
| NONE | -0.0768 | 1.475 |
| ORACLE (upper bound) | +0.0138 | |

| Contrast (99%) | Estimate |
|---|---|
| W5b-PILOT-ONLY | +0.0000 [+0.0000, +0.0000] |
| W5b-NONE | -0.0000 [-0.0000, +0.0000] |
| W5b-RANDOM-FUNC | -0.0039 [-0.0041, -0.0037] |
| W5b-W3C | +0.0000 [+0.0000, +0.0000] |
| W5b − W5b-NO-FAIL (ablation) | +0.0000 [+0.0000, +0.0000] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 0, false certificates 0.

## person → agent_v2, pilot of 8

W5b adopted a non-baseline table in 0/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5b | -0.0768 | 1.475 |
| PILOT-ONLY | -0.0628 | 1.474 |
| W3C | -0.0768 | 1.475 |
| RANDOM-FUNC | -0.0749 | 1.475 |
| W5b-NO-FAIL | -0.0768 | 1.475 |
| NONE | -0.0768 | 1.475 |
| ORACLE (upper bound) | +0.0138 | |

| Contrast (99%) | Estimate |
|---|---|
| W5b-PILOT-ONLY | -0.0140 [-0.0145, -0.0133] |
| W5b-NONE | -0.0000 [-0.0000, +0.0000] |
| W5b-RANDOM-FUNC | -0.0019 [-0.0020, -0.0018] |
| W5b-W3C | +0.0000 [+0.0000, +0.0000] |
| W5b − W5b-NO-FAIL (ablation) | +0.0000 [+0.0000, +0.0000] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 0, false certificates 0.

## person → agent_v2, pilot of 16

W5b adopted a non-baseline table in 0/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5b | -0.0768 | 1.475 |
| PILOT-ONLY | -0.0701 | 1.462 |
| W3C | -0.0768 | 1.475 |
| RANDOM-FUNC | -0.0728 | 1.472 |
| W5b-NO-FAIL | -0.0768 | 1.475 |
| NONE | -0.0768 | 1.475 |
| ORACLE (upper bound) | +0.0138 | |

| Contrast (99%) | Estimate |
|---|---|
| W5b-PILOT-ONLY | -0.0066 [-0.0082, -0.0051] |
| W5b-NONE | -0.0000 [-0.0000, +0.0000] |
| W5b-RANDOM-FUNC | -0.0040 [-0.0043, -0.0037] |
| W5b-W3C | +0.0000 [+0.0000, +0.0000] |
| W5b − W5b-NO-FAIL (ablation) | +0.0000 [+0.0000, +0.0000] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 0, false certificates 0.

**Certificate audit (pilot 8, pooled):** 0 false of 96 adopted — holds.

**Primary criterion (pilot 8): FAIL.** Directions meeting all three comparisons: ['agent->person', 'person->agent'].

**W5b overall: FAIL.**

Ablation W5b-NO-FAIL: the same pilot without the failure rule (reported, not a pass condition).
