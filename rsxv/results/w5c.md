# W5c — transfer with a spike guard in the pilot (seventh attempt): results

Design: [`AGENTS.md`](../AGENTS.md) §11.7, registered before any code; operational choices fixed before the run are in
the docstring of [`rsxv/w5c_experiments.py`](../rsxv/w5c_experiments.py). Level 0.05 / 7 (99.29% paired bootstrap intervals).
All environments are stated models; no number here comes from people or production agents.

## Certificates issued by each source

- **person** (roles `{'RESTORE': 'BEAR', 'DRIVE': 'LEOPARD', 'STABILISE': 'BEAR'}`): calm: STABILISE (BEAR, +0.953 [+0.662, +1.243], n=114); rising: STABILISE (BEAR, +0.662 [+0.195, +1.130], n=47); loaded: STABILISE (BEAR, +1.013 [+0.771, +1.255], n=151); crisis: STABILISE (BEAR, +1.076 [+0.826, +1.325], n=142)
- **agent** (roles `{'RESTORE': 'LEOPARD', 'DRIVE': 'TIGER', 'STABILISE': 'LEOPARD'}`): calm: STABILISE (LEOPARD, +0.665 [+0.488, +0.842], n=375); rising: STABILISE (LEOPARD, +1.515 [+1.035, +1.996], n=39); loaded: STABILISE (LEOPARD, +1.755 [+1.347, +2.162], n=78); crisis: STABILISE (LEOPARD, +2.368 [+1.612, +3.124], n=19)
- **agent_v2** (roles `{'RESTORE': 'LEOPARD', 'DRIVE': 'TIGER', 'STABILISE': 'BEAR'}`): calm: RESTORE (LEOPARD, +0.678 [+0.324, +1.031], n=122); rising: RESTORE (LEOPARD, +1.921 [+0.808, +3.035], n=10); loaded: DRIVE (TIGER, +0.184 [+0.046, +0.322], n=364)

## agent → person, pilot of 4

W5c adopted a non-baseline table in 12/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5c | -0.0141 | 2.105 |
| PILOT-ONLY | -0.0157 | 2.151 |
| W3C | -0.0961 | 2.395 |
| RANDOM-FUNC | -0.0961 | 2.395 |
| W5c-NO-FAIL | -0.0344 | 2.187 |
| NONE | -0.0961 | 2.395 |
| ORACLE (upper bound) | +0.2333 | |

| Contrast (99%) | Estimate |
|---|---|
| W5c-PILOT-ONLY | +0.0016 [-0.0008, +0.0039] |
| W5c-NONE | +0.0820 [+0.0730, +0.0920] |
| W5c-RANDOM-FUNC | +0.0820 [+0.0730, +0.0920] |
| W5c-W3C | +0.0820 [+0.0730, +0.0920] |
| W5c − W5c-NO-FAIL (ablation) | +0.0203 [+0.0172, +0.0233] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 17, false certificates 0.

## agent → person, pilot of 8

W5c adopted a non-baseline table in 20/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5c | +0.1080 | 1.237 |
| PILOT-ONLY | +0.1009 | 1.311 |
| W3C | -0.0925 | 2.588 |
| RANDOM-FUNC | -0.0961 | 2.395 |
| W5c-NO-FAIL | +0.0503 | 1.749 |
| NONE | -0.0961 | 2.395 |
| ORACLE (upper bound) | +0.2333 | |

| Contrast (99%) | Estimate |
|---|---|
| W5c-PILOT-ONLY | +0.0071 [+0.0058, +0.0086] |
| W5c-NONE | +0.2041 [+0.1884, +0.2210] |
| W5c-RANDOM-FUNC | +0.2041 [+0.1884, +0.2210] |
| W5c-W3C | +0.2005 [+0.1848, +0.2173] |
| W5c − W5c-NO-FAIL (ablation) | +0.0578 [+0.0547, +0.0606] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **yes**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 42, false certificates 0.

## agent → person, pilot of 16

W5c adopted a non-baseline table in 20/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5c | +0.1838 | 0.609 |
| PILOT-ONLY | +0.1904 | 0.609 |
| W3C | -0.0880 | 2.778 |
| RANDOM-FUNC | -0.0961 | 2.395 |
| W5c-NO-FAIL | +0.1816 | 0.582 |
| NONE | -0.0961 | 2.395 |
| ORACLE (upper bound) | +0.2333 | |

| Contrast (99%) | Estimate |
|---|---|
| W5c-PILOT-ONLY | -0.0067 [-0.0082, -0.0051] |
| W5c-NONE | +0.2799 [+0.2708, +0.2890] |
| W5c-RANDOM-FUNC | +0.2799 [+0.2708, +0.2890] |
| W5c-W3C | +0.2718 [+0.2624, +0.2808] |
| W5c − W5c-NO-FAIL (ablation) | +0.0022 [-0.0024, +0.0065] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 62, false certificates 0.

## person → agent, pilot of 4

W5c adopted a non-baseline table in 10/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5c | -0.0388 | 0.958 |
| PILOT-ONLY | -0.0342 | 0.900 |
| W3C | -0.0806 | 1.471 |
| RANDOM-FUNC | -0.0845 | 1.530 |
| W5c-NO-FAIL | -0.0247 | 0.845 |
| NONE | -0.0845 | 1.530 |
| ORACLE (upper bound) | +0.0973 | |

| Contrast (99%) | Estimate |
|---|---|
| W5c-PILOT-ONLY | -0.0046 [-0.0053, -0.0039] |
| W5c-NONE | +0.0457 [+0.0386, +0.0528] |
| W5c-RANDOM-FUNC | +0.0457 [+0.0386, +0.0528] |
| W5c-W3C | +0.0418 [+0.0354, +0.0483] |
| W5c − W5c-NO-FAIL (ablation) | -0.0141 [-0.0162, -0.0123] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: False. Adopted contexts 10, false certificates 0.

## person → agent, pilot of 8

W5c adopted a non-baseline table in 17/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5c | -0.0085 | 0.612 |
| PILOT-ONLY | +0.0013 | 0.373 |
| W3C | -0.0729 | 1.354 |
| RANDOM-FUNC | -0.0820 | 1.499 |
| W5c-NO-FAIL | -0.0005 | 0.436 |
| NONE | -0.0845 | 1.530 |
| ORACLE (upper bound) | +0.0973 | |

| Contrast (99%) | Estimate |
|---|---|
| W5c-PILOT-ONLY | -0.0098 [-0.0122, -0.0077] |
| W5c-NONE | +0.0760 [+0.0645, +0.0878] |
| W5c-RANDOM-FUNC | +0.0734 [+0.0624, +0.0849] |
| W5c-W3C | +0.0643 [+0.0548, +0.0741] |
| W5c − W5c-NO-FAIL (ablation) | -0.0080 [-0.0098, -0.0064] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: False. Adopted contexts 22, false certificates 0.

## person → agent, pilot of 16

W5c adopted a non-baseline table in 20/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5c | +0.0028 | 0.439 |
| PILOT-ONLY | -0.0015 | 0.367 |
| W3C | -0.0419 | 0.884 |
| RANDOM-FUNC | -0.0825 | 1.538 |
| W5c-NO-FAIL | -0.0015 | 0.367 |
| NONE | -0.0845 | 1.530 |
| ORACLE (upper bound) | +0.0973 | |

| Contrast (99%) | Estimate |
|---|---|
| W5c-PILOT-ONLY | +0.0043 [+0.0034, +0.0051] |
| W5c-NONE | +0.0873 [+0.0741, +0.1015] |
| W5c-RANDOM-FUNC | +0.0853 [+0.0721, +0.0994] |
| W5c-W3C | +0.0447 [+0.0386, +0.0513] |
| W5c − W5c-NO-FAIL (ablation) | +0.0043 [+0.0034, +0.0051] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **yes**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: False. Adopted contexts 35, false certificates 0.

## agent_v2 → person, pilot of 4

W5c adopted a non-baseline table in 8/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5c | -0.0508 | 2.228 |
| PILOT-ONLY | -0.0157 | 2.151 |
| W3C | -0.0961 | 2.395 |
| RANDOM-FUNC | -0.0964 | 2.541 |
| W5c-NO-FAIL | -0.0633 | 2.288 |
| NONE | -0.0961 | 2.395 |
| ORACLE (upper bound) | +0.2333 | |

| Contrast (99%) | Estimate |
|---|---|
| W5c-PILOT-ONLY | -0.0351 [-0.0389, -0.0316] |
| W5c-NONE | +0.0453 [+0.0370, +0.0543] |
| W5c-RANDOM-FUNC | +0.0456 [+0.0373, +0.0544] |
| W5c-W3C | +0.0453 [+0.0370, +0.0543] |
| W5c − W5c-NO-FAIL (ablation) | +0.0125 [+0.0103, +0.0149] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: False. Adopted contexts 9, false certificates 0.

## agent_v2 → person, pilot of 8

W5c adopted a non-baseline table in 18/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5c | +0.0212 | 1.841 |
| PILOT-ONLY | +0.1009 | 1.311 |
| W3C | -0.0961 | 2.395 |
| RANDOM-FUNC | -0.0970 | 2.785 |
| W5c-NO-FAIL | +0.0175 | 1.887 |
| NONE | -0.0961 | 2.395 |
| ORACLE (upper bound) | +0.2333 | |

| Contrast (99%) | Estimate |
|---|---|
| W5c-PILOT-ONLY | -0.0797 [-0.0878, -0.0716] |
| W5c-NONE | +0.1173 [+0.0974, +0.1397] |
| W5c-RANDOM-FUNC | +0.1182 [+0.0976, +0.1404] |
| W5c-W3C | +0.1173 [+0.0974, +0.1397] |
| W5c − W5c-NO-FAIL (ablation) | +0.0037 [+0.0001, +0.0074] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: False. Adopted contexts 26, false certificates 0.

## agent_v2 → person, pilot of 16

W5c adopted a non-baseline table in 19/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5c | +0.0585 | 1.505 |
| PILOT-ONLY | +0.1904 | 0.609 |
| W3C | -0.0961 | 2.395 |
| RANDOM-FUNC | -0.0981 | 3.272 |
| W5c-NO-FAIL | +0.0719 | 1.408 |
| NONE | -0.0961 | 2.395 |
| ORACLE (upper bound) | +0.2333 | |

| Contrast (99%) | Estimate |
|---|---|
| W5c-PILOT-ONLY | -0.1320 [-0.1548, -0.1077] |
| W5c-NONE | +0.1546 [+0.1288, +0.1844] |
| W5c-RANDOM-FUNC | +0.1566 [+0.1287, +0.1855] |
| W5c-W3C | +0.1546 [+0.1288, +0.1844] |
| W5c − W5c-NO-FAIL (ablation) | -0.0134 [-0.0160, -0.0111] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: False. Adopted contexts 35, false certificates 0.

## person → agent_v2, pilot of 4

W5c adopted a non-baseline table in 0/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5c | -0.0749 | 1.435 |
| PILOT-ONLY | -0.0749 | 1.435 |
| W3C | -0.0749 | 1.435 |
| RANDOM-FUNC | -0.0734 | 1.434 |
| W5c-NO-FAIL | -0.0749 | 1.435 |
| NONE | -0.0749 | 1.435 |
| ORACLE (upper bound) | +0.0157 | |

| Contrast (99%) | Estimate |
|---|---|
| W5c-PILOT-ONLY | +0.0000 [+0.0000, +0.0000] |
| W5c-NONE | +0.0000 [-0.0000, +0.0000] |
| W5c-RANDOM-FUNC | -0.0016 [-0.0016, -0.0015] |
| W5c-W3C | +0.0000 [+0.0000, +0.0000] |
| W5c − W5c-NO-FAIL (ablation) | +0.0000 [+0.0000, +0.0000] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 0, false certificates 0.

## person → agent_v2, pilot of 8

W5c adopted a non-baseline table in 1/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5c | -0.0771 | 1.434 |
| PILOT-ONLY | -0.0668 | 1.428 |
| W3C | -0.0749 | 1.435 |
| RANDOM-FUNC | -0.0682 | 1.433 |
| W5c-NO-FAIL | -0.0749 | 1.435 |
| NONE | -0.0749 | 1.435 |
| ORACLE (upper bound) | +0.0157 | |

| Contrast (99%) | Estimate |
|---|---|
| W5c-PILOT-ONLY | -0.0104 [-0.0109, -0.0098] |
| W5c-NONE | -0.0022 [-0.0024, -0.0020] |
| W5c-RANDOM-FUNC | -0.0090 [-0.0093, -0.0086] |
| W5c-W3C | -0.0022 [-0.0024, -0.0020] |
| W5c − W5c-NO-FAIL (ablation) | -0.0022 [-0.0024, -0.0020] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 1, false certificates 1.

## person → agent_v2, pilot of 16

W5c adopted a non-baseline table in 0/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5c | -0.0749 | 1.435 |
| PILOT-ONLY | -0.0624 | 1.404 |
| W3C | -0.0749 | 1.435 |
| RANDOM-FUNC | -0.0681 | 1.427 |
| W5c-NO-FAIL | -0.0749 | 1.435 |
| NONE | -0.0749 | 1.435 |
| ORACLE (upper bound) | +0.0157 | |

| Contrast (99%) | Estimate |
|---|---|
| W5c-PILOT-ONLY | -0.0125 [-0.0149, -0.0102] |
| W5c-NONE | +0.0000 [-0.0000, +0.0000] |
| W5c-RANDOM-FUNC | -0.0068 [-0.0073, -0.0064] |
| W5c-W3C | +0.0000 [+0.0000, +0.0000] |
| W5c − W5c-NO-FAIL (ablation) | +0.0000 [+0.0000, +0.0000] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: False. Adopted contexts 0, false certificates 0.

**Certificate audit (pilot 8, pooled):** 1 false of 91 adopted — holds.

**Primary criterion (pilot 8): FAIL.** Directions meeting all three comparisons: ['agent->person'].

**W5c overall: FAIL.**

Ablation W5c-NO-FAIL: the same pilot without the failure rule (reported, not a pass condition).
