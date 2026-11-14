# T-AP — directional transfer agents v1 → person: results

Design: [`AGENTS.md`](../AGENTS.md) §11.8 (W5c design, one direction, pilot 8, level 0.05 / 8, two-sided 99.375%).
Origin disclosed: the direction was chosen after it met every comparison in W5b and every condition in W5c.

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| T-AP | +0.1113 | 1.442 |
| PILOT-ONLY | +0.0872 | 1.544 |
| W3C | -0.0904 | 2.350 |
| RANDOM-FUNC | -0.0919 | 2.370 |
| T-AP-NO-FAIL | +0.0855 | 1.478 |
| NONE | -0.0904 | 2.350 |
| ORACLE (upper bound) | +0.2439 | |

| Contrast | Estimate [interval] |
|---|---|
| T-AP − PILOT-ONLY | +0.0242 [+0.0210, +0.0275] |
| T-AP − NONE | +0.2017 [+0.1873, +0.2146] |
| T-AP − RANDOM-FUNC | +0.2033 [+0.1886, +0.2166] |
| T-AP − W3C | +0.2017 [+0.1873, +0.2146] |

| Spike contrast | Estimate [interval] |
|---|---|
| T-AP − PILOT-ONLY | -0.102 [-0.139, -0.068] |
| T-AP − NONE | -0.908 [-1.111, -0.676] |
| T-AP − RANDOM-FUNC | -0.928 [-1.135, -0.700] |
| T-AP − W3C | -0.908 [-1.111, -0.676] |

Adopted a non-baseline table in 20/20 repetitions; adopted contexts 41, false certificates 0.

**Primary: PASS.**

## Confirmation (seeds + 100000; target person model v2, arousal_deeper)

| Arm | Mean / tick | Spikes / target |
|---|---|---|
| T-AP | +0.0872 | 0.952 |
| PILOT-ONLY | +0.0529 | 0.956 |
| RANDOM-FUNC | +0.0692 | 0.960 |
| T-AP-NO-FAIL | +0.0739 | 0.952 |
| NONE | +0.0692 | 0.960 |

| Contrast | Estimate [interval] |
|---|---|
| W5-PILOT-ONLY-ADAPTIVE | +0.0343 [+0.0297, +0.0386] |
| W5-NONE | +0.0180 [+0.0109, +0.0240] |
| W5-RANDOM-CERT | +0.0180 [+0.0109, +0.0240] |

Beats all: True; non-inferior: {'NONE': True}; safety gate: True.

**T-AP overall (primary and confirmation): PASS.**
