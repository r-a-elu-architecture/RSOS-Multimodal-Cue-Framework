# W5e — W5d with the calibrated jam predictor (twelfth transfer test): results

Design: [`AGENTS.md`](../AGENTS.md) §11.9, registered before any code; operational choices fixed before the run are in
the docstring of [`rsxv/w5e_experiments.py`](../rsxv/w5e_experiments.py). Level 0.05 / 12 (99.58% paired bootstrap intervals).
All environments are stated models; no number here comes from people or production agents.

## Certificates issued by each source

- **person** (roles `{'RESTORE': 'BEAR', 'DRIVE': 'LEOPARD', 'STABILISE': 'BEAR'}`): calm: STABILISE (BEAR, +0.695 [+0.451, +0.939], n=139); rising: STABILISE (BEAR, +0.808 [+0.440, +1.175], n=67); loaded: STABILISE (BEAR, +0.840 [+0.637, +1.043], n=153); crisis: STABILISE (BEAR, +0.925 [+0.672, +1.179], n=139)
- **agent** (roles `{'RESTORE': 'LEOPARD', 'DRIVE': 'TIGER', 'STABILISE': 'LEOPARD'}`): calm: STABILISE (LEOPARD, +0.892 [+0.694, +1.089], n=306); rising: STABILISE (LEOPARD, +1.384 [+0.895, +1.874], n=45); loaded: STABILISE (LEOPARD, +1.613 [+1.252, +1.974], n=102); crisis: STABILISE (LEOPARD, +1.422 [+0.911, +1.933], n=32)
- **agent_v2** (roles `{'RESTORE': 'LEOPARD', 'DRIVE': 'TIGER', 'STABILISE': 'BEAR'}`): calm: RESTORE (LEOPARD, +0.711 [+0.391, +1.032], n=112); loaded: DRIVE (TIGER, +0.229 [+0.073, +0.385], n=318)

## agent → person, pilot of 4

W5e adopted a non-baseline table in 12/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5e | -0.0123 | 2.167 |
| PILOT-ONLY | -0.0154 | 2.239 |
| W3C | -0.0920 | 2.340 |
| RANDOM-FUNC | -0.0920 | 2.340 |
| W5ec-NO-FAIL | -0.0114 | 2.182 |
| NONE | -0.0920 | 2.340 |
| ORACLE (upper bound) | +0.2401 | |

| Contrast (99%) | Estimate |
|---|---|
| W5e-PILOT-ONLY | +0.0032 [+0.0012, +0.0053] |
| W5e-NONE | +0.0798 [+0.0675, +0.0915] |
| W5e-RANDOM-FUNC | +0.0798 [+0.0675, +0.0915] |
| W5e-W3C | +0.0798 [+0.0675, +0.0915] |
| W5e − W5e-NO-FAIL (ablation) | -0.0009 [-0.0049, +0.0032] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **yes**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 15, false certificates 0.

## agent → person, pilot of 8

W5e adopted a non-baseline table in 20/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5e | +0.0858 | 1.676 |
| PILOT-ONLY | +0.0365 | 2.004 |
| W3C | -0.0920 | 2.340 |
| RANDOM-FUNC | -0.0920 | 2.340 |
| W5ec-NO-FAIL | +0.0661 | 1.603 |
| NONE | -0.0920 | 2.340 |
| ORACLE (upper bound) | +0.2401 | |

| Contrast (99%) | Estimate |
|---|---|
| W5e-PILOT-ONLY | +0.0492 [+0.0440, +0.0541] |
| W5e-NONE | +0.1778 [+0.1592, +0.1953] |
| W5e-RANDOM-FUNC | +0.1778 [+0.1592, +0.1953] |
| W5e-W3C | +0.1778 [+0.1592, +0.1953] |
| W5e − W5e-NO-FAIL (ablation) | +0.0197 [+0.0126, +0.0269] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **yes**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 34, false certificates 0.

## agent → person, pilot of 16

W5e adopted a non-baseline table in 20/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5e | +0.1958 | 0.544 |
| PILOT-ONLY | +0.1738 | 0.833 |
| W3C | -0.0907 | 2.444 |
| RANDOM-FUNC | -0.0920 | 2.340 |
| W5ec-NO-FAIL | +0.1636 | 0.820 |
| NONE | -0.0920 | 2.340 |
| ORACLE (upper bound) | +0.2401 | |

| Contrast (99%) | Estimate |
|---|---|
| W5e-PILOT-ONLY | +0.0220 [+0.0195, +0.0246] |
| W5e-NONE | +0.2879 [+0.2755, +0.2993] |
| W5e-RANDOM-FUNC | +0.2879 [+0.2755, +0.2993] |
| W5e-W3C | +0.2865 [+0.2741, +0.2974] |
| W5e − W5e-NO-FAIL (ablation) | +0.0322 [+0.0274, +0.0374] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **yes**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 58, false certificates 0.

## person → agent, pilot of 4

W5e adopted a non-baseline table in 13/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5e | -0.0247 | 0.875 |
| PILOT-ONLY | -0.0255 | 1.071 |
| W3C | -0.0935 | 1.580 |
| RANDOM-FUNC | -0.0908 | 1.604 |
| W5ec-NO-FAIL | -0.0247 | 0.875 |
| NONE | -0.0935 | 1.580 |
| ORACLE (upper bound) | +0.0946 | |

| Contrast (99%) | Estimate |
|---|---|
| W5e-PILOT-ONLY | +0.0008 [-0.0014, +0.0030] |
| W5e-NONE | +0.0688 [+0.0593, +0.0791] |
| W5e-RANDOM-FUNC | +0.0660 [+0.0564, +0.0765] |
| W5e-W3C | +0.0688 [+0.0593, +0.0791] |
| W5e − W5e-NO-FAIL (ablation) | +0.0000 [+0.0000, +0.0000] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 12, false certificates 0.

## person → agent, pilot of 8

W5e adopted a non-baseline table in 19/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5e | +0.0018 | 0.605 |
| PILOT-ONLY | -0.0005 | 0.546 |
| W3C | -0.0809 | 1.416 |
| RANDOM-FUNC | -0.0922 | 1.592 |
| W5ec-NO-FAIL | +0.0016 | 0.732 |
| NONE | -0.0935 | 1.580 |
| ORACLE (upper bound) | +0.0946 | |

| Contrast (99%) | Estimate |
|---|---|
| W5e-PILOT-ONLY | +0.0023 [+0.0018, +0.0029] |
| W5e-NONE | +0.0954 [+0.0821, +0.1100] |
| W5e-RANDOM-FUNC | +0.0940 [+0.0806, +0.1087] |
| W5e-W3C | +0.0827 [+0.0713, +0.0950] |
| W5e − W5e-NO-FAIL (ablation) | +0.0002 [-0.0018, +0.0021] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **yes**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: False. Adopted contexts 24, false certificates 0.

## person → agent, pilot of 16

W5e adopted a non-baseline table in 19/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5e | -0.0027 | 0.545 |
| PILOT-ONLY | +0.0015 | 0.490 |
| W3C | -0.0598 | 1.142 |
| RANDOM-FUNC | -0.0935 | 1.580 |
| W5ec-NO-FAIL | +0.0106 | 0.686 |
| NONE | -0.0935 | 1.580 |
| ORACLE (upper bound) | +0.0946 | |

| Contrast (99%) | Estimate |
|---|---|
| W5e-PILOT-ONLY | -0.0042 [-0.0050, -0.0035] |
| W5e-NONE | +0.0909 [+0.0777, +0.1056] |
| W5e-RANDOM-FUNC | +0.0909 [+0.0777, +0.1056] |
| W5e-W3C | +0.0571 [+0.0492, +0.0658] |
| W5e − W5e-NO-FAIL (ablation) | -0.0132 [-0.0152, -0.0114] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: False. Adopted contexts 35, false certificates 0.

## agent_v2 → person, pilot of 4

W5e adopted a non-baseline table in 9/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5e | -0.0386 | 2.269 |
| PILOT-ONLY | -0.0154 | 2.239 |
| W3C | -0.0920 | 2.340 |
| RANDOM-FUNC | -0.0921 | 2.429 |
| W5ec-NO-FAIL | -0.0386 | 2.269 |
| NONE | -0.0920 | 2.340 |
| ORACLE (upper bound) | +0.2401 | |

| Contrast (99%) | Estimate |
|---|---|
| W5e-PILOT-ONLY | -0.0232 [-0.0262, -0.0200] |
| W5e-NONE | +0.0534 [+0.0428, +0.0638] |
| W5e-RANDOM-FUNC | +0.0535 [+0.0430, +0.0635] |
| W5e-W3C | +0.0534 [+0.0428, +0.0638] |
| W5e − W5e-NO-FAIL (ablation) | +0.0000 [+0.0000, +0.0000] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 8, false certificates 0.

## agent_v2 → person, pilot of 8

W5e adopted a non-baseline table in 16/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5e | +0.0123 | 2.164 |
| PILOT-ONLY | +0.0365 | 2.004 |
| W3C | -0.0920 | 2.340 |
| RANDOM-FUNC | -0.0926 | 2.788 |
| W5ec-NO-FAIL | +0.0001 | 2.255 |
| NONE | -0.0920 | 2.340 |
| ORACLE (upper bound) | +0.2401 | |

| Contrast (99%) | Estimate |
|---|---|
| W5e-PILOT-ONLY | -0.0242 [-0.0287, -0.0197] |
| W5e-NONE | +0.1044 [+0.0877, +0.1207] |
| W5e-RANDOM-FUNC | +0.1049 [+0.0881, +0.1200] |
| W5e-W3C | +0.1044 [+0.0877, +0.1207] |
| W5e − W5e-NO-FAIL (ablation) | +0.0122 [+0.0112, +0.0130] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: False. Adopted contexts 13, false certificates 0.

## agent_v2 → person, pilot of 16

W5e adopted a non-baseline table in 19/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5e | +0.0839 | 1.786 |
| PILOT-ONLY | +0.1738 | 0.833 |
| W3C | -0.0920 | 2.340 |
| RANDOM-FUNC | -0.0930 | 3.146 |
| W5ec-NO-FAIL | +0.0839 | 1.786 |
| NONE | -0.0920 | 2.340 |
| ORACLE (upper bound) | +0.2401 | |

| Contrast (99%) | Estimate |
|---|---|
| W5e-PILOT-ONLY | -0.0900 [-0.0985, -0.0818] |
| W5e-NONE | +0.1759 [+0.1594, +0.1918] |
| W5e-RANDOM-FUNC | +0.1769 [+0.1574, +0.1946] |
| W5e-W3C | +0.1759 [+0.1594, +0.1918] |
| W5e − W5e-NO-FAIL (ablation) | +0.0000 [+0.0000, +0.0000] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: False. Adopted contexts 19, false certificates 0.

## person → agent_v2, pilot of 4

W5e adopted a non-baseline table in 0/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5e | -0.0729 | 1.340 |
| PILOT-ONLY | -0.0729 | 1.340 |
| W3C | -0.0729 | 1.340 |
| RANDOM-FUNC | -0.0719 | 1.340 |
| W5ec-NO-FAIL | -0.0724 | 1.339 |
| NONE | -0.0729 | 1.340 |
| ORACLE (upper bound) | +0.0181 | |

| Contrast (99%) | Estimate |
|---|---|
| W5e-PILOT-ONLY | +0.0000 [+0.0000, +0.0000] |
| W5e-NONE | -0.0000 [-0.0000, +0.0000] |
| W5e-RANDOM-FUNC | -0.0010 [-0.0011, -0.0009] |
| W5e-W3C | +0.0000 [+0.0000, +0.0000] |
| W5e − W5e-NO-FAIL (ablation) | -0.0005 [-0.0006, -0.0003] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 0, false certificates 0.

## person → agent_v2, pilot of 8

W5e adopted a non-baseline table in 4/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5e | -0.0711 | 1.335 |
| PILOT-ONLY | -0.0496 | 1.333 |
| W3C | -0.0729 | 1.340 |
| RANDOM-FUNC | -0.0707 | 1.339 |
| W5ec-NO-FAIL | -0.0711 | 1.335 |
| NONE | -0.0729 | 1.340 |
| ORACLE (upper bound) | +0.0181 | |

| Contrast (99%) | Estimate |
|---|---|
| W5e-PILOT-ONLY | -0.0214 [-0.0230, -0.0196] |
| W5e-NONE | +0.0018 [+0.0014, +0.0026] |
| W5e-RANDOM-FUNC | -0.0003 [-0.0008, +0.0005] |
| W5e-W3C | +0.0018 [+0.0014, +0.0026] |
| W5e − W5e-NO-FAIL (ablation) | +0.0000 [+0.0000, +0.0000] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: True. Adopted contexts 0, false certificates 0.

## person → agent_v2, pilot of 16

W5e adopted a non-baseline table in 5/20 repetitions.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| W5e | -0.0751 | 1.358 |
| PILOT-ONLY | -0.0589 | 1.336 |
| W3C | -0.0729 | 1.340 |
| RANDOM-FUNC | -0.0706 | 1.339 |
| W5ec-NO-FAIL | -0.0722 | 1.337 |
| NONE | -0.0729 | 1.340 |
| ORACLE (upper bound) | +0.0181 | |

| Contrast (99%) | Estimate |
|---|---|
| W5e-PILOT-ONLY | -0.0162 [-0.0170, -0.0153] |
| W5e-NONE | -0.0022 [-0.0027, -0.0016] |
| W5e-RANDOM-FUNC | -0.0045 [-0.0050, -0.0040] |
| W5e-W3C | -0.0022 [-0.0027, -0.0016] |
| W5e − W5e-NO-FAIL (ablation) | -0.0029 [-0.0032, -0.0025] |

Beats PILOT-ONLY, NONE and RANDOM-FUNC: **no**. Non-inferior: {'NONE': True, 'W3C': True}. Safety gate holds: False. Adopted contexts 0, false certificates 0.

**Certificate audit (pilot 8, pooled):** 0 false of 71 adopted — holds.

**Primary criterion (pilot 8): FAIL.** Directions meeting all three comparisons: ['agent->person', 'person->agent'].

**Strong pass (three of four directions): NO.** Jam prediction: 151 of 280 correct at pilot 8. Warnings issued by each source: {'person': {'loaded': ['DRIVE']}, 'agent': {'calm': ['unassigned'], 'rising': ['unassigned']}, 'agent_v2': {'rising': ['unassigned'], 'loaded': ['unassigned'], 'crisis': ['unassigned']}}.

**W5e overall: FAIL.**

Ablation W5e-NO-FAIL: the same pilot without the failure rule (reported, not a pass condition).
