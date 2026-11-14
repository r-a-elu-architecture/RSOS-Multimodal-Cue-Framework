# T-AP-R — how far the confirmed transfer reaches: results

Design: [`AGENTS.md`](../AGENTS.md) §11.9 (T-AP design; level 0.05 / 11, two-sided 99.55%).

## T-AP-4: FAIL

### Primary (pilot 4, source agent)

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| T-AP-4 | -0.0284 | 2.161 |
| PILOT-ONLY | -0.0331 | 2.214 |
| W3C | -0.0967 | 2.420 |
| RANDOM-FUNC | -0.0967 | 2.420 |
| T-AP-4-NO-FAIL | -0.0282 | 2.212 |
| NONE | -0.0967 | 2.420 |

| Contrast | Score | Spikes |
|---|---|---|
| T-AP-4 − PILOT-ONLY | +0.0047 [+0.0034, +0.0062] | -0.0540 [-0.0755, -0.0325] |
| T-AP-4 − NONE | +0.0683 [+0.0551, +0.0817] | -0.2595 [-0.4017, -0.1457] |
| T-AP-4 − RANDOM-FUNC | +0.0683 [+0.0551, +0.0817] | -0.2595 [-0.4017, -0.1457] |
| T-AP-4 − W3C | +0.0683 [+0.0551, +0.0817] | -0.2595 [-0.4017, -0.1457] |

Beats PILOT-ONLY, NONE, RANDOM-FUNC: True; non-inferior: {'NONE': True, 'W3C': True}; safety gate: True; adopted in 11/20 repetitions.

False certificates: 0 of 15 adopted contexts. Primary: PASS.

### Confirmation (seeds + 100000; person model v2 arousal_deeper; W3C included)

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| T-AP-4 | +0.0503 | 0.924 |
| PILOT-ONLY | +0.0490 | 0.925 |
| W3C | +0.0646 | 0.945 |
| RANDOM-FUNC | +0.0646 | 0.945 |
| T-AP-4-NO-FAIL | +0.0502 | 0.933 |
| NONE | +0.0646 | 0.945 |

| Contrast | Score | Spikes |
|---|---|---|
| T-AP-4 − PILOT-ONLY | +0.0013 [+0.0005, +0.0021] | -0.0010 [-0.0035, +0.0017] |
| T-AP-4 − NONE | -0.0142 [-0.0218, -0.0072] | -0.0205 [-0.0440, -0.0040] |
| T-AP-4 − RANDOM-FUNC | -0.0142 [-0.0218, -0.0072] | -0.0205 [-0.0440, -0.0040] |
| T-AP-4 − W3C | -0.0142 [-0.0218, -0.0072] | -0.0205 [-0.0440, -0.0040] |

Beats PILOT-ONLY, NONE, RANDOM-FUNC: False; non-inferior: {'NONE': False, 'W3C': False}; safety gate: True; adopted in 15/20 repetitions.

## T-AP-V2: FAIL

### Primary (pilot 8, source agent_v2)

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| T-AP-V2 | +0.0052 | 1.954 |
| PILOT-ONLY | +0.0360 | 1.932 |
| W3C | -0.0938 | 2.390 |
| RANDOM-FUNC | -0.0938 | 2.390 |
| T-AP-V2-NO-FAIL | +0.0039 | 1.919 |
| NONE | -0.0938 | 2.390 |

| Contrast | Score | Spikes |
|---|---|---|
| T-AP-V2 − PILOT-ONLY | -0.0307 [-0.0364, -0.0256] | +0.0223 [-0.0535, +0.1013] |
| T-AP-V2 − NONE | +0.0991 [+0.0815, +0.1173] | -0.4358 [-0.6270, -0.2423] |
| T-AP-V2 − RANDOM-FUNC | +0.0991 [+0.0815, +0.1173] | -0.4358 [-0.6270, -0.2423] |
| T-AP-V2 − W3C | +0.0991 [+0.0815, +0.1173] | -0.4358 [-0.6270, -0.2423] |

Beats PILOT-ONLY, NONE, RANDOM-FUNC: False; non-inferior: {'NONE': True, 'W3C': True}; safety gate: True; adopted in 15/20 repetitions.

False certificates: 0 of 18 adopted contexts. Primary: FAIL.
