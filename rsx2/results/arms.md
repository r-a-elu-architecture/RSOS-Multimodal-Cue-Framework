
### full model

| Arm | Δ agency | Δ distress | Layers ≥0.3 (of 11) | Seconds | Distress spikes ≥2.5 | NullSafe stops | Refused (ghost/laws) | Goal met |
|---|---|---|---|---|---|---|---|---|
| v1 canonical (120 s, as written) | +1.21 ± 0.07 | +2.11 ± 0.10 | 5.1 | 120 | 26% | 0% | 0% | 0% |
| v1 canonical, time-matched (200 s) | +2.15 ± 0.11 | +3.07 ± 0.09 | 6.3 | 200 | 80% | 0% | 0% | 0% |
| v1 canonical, time-matched (300 s) | +3.30 ± 0.15 | +3.91 ± 0.12 | 6.8 | 300 | 95% | 0% | 0% | 0% |
| v1 auto-upgraded by NEXT | +2.04 ± 0.05 | -1.41 ± 0.12 | 9.6 | 292 | 0% | 0% | 1% | 76% |
| RSX/2 | +2.06 ± 0.05 | -1.46 ± 0.11 | 9.4 | 289 | 0% | 0% | 1% | 78% |
| RSX/2 without closed loop (no UNTIL/IF) | +2.99 ± 0.11 | -3.35 ± 0.16 | 9.2 | 470 | 0% | 0% | 1% | 97% |
| RSX/2 all vectors in one phase | +1.98 ± 0.23 | +0.79 ± 0.11 | 6.6 | 130 | 2% | 3% | 36% | 0% |
| sham (RSX/2 timeline, no content) | +0.00 ± 0.00 | -0.57 ± 0.11 | 0.0 | 658 | 0% | 0% | 2% | 0% |

### neutral model

| Arm | Δ agency | Δ distress | Layers ≥0.3 (of 11) | Seconds | Distress spikes ≥2.5 | NullSafe stops | Refused (ghost/laws) | Goal met |
|---|---|---|---|---|---|---|---|---|
| v1 canonical (120 s, as written) | +5.20 ± 0.12 | -4.16 ± 0.14 | 7.0 | 120 | 0% | 0% | 0% | 100% |
| v1 canonical, time-matched (200 s) | +5.48 ± 0.12 | -5.22 ± 0.15 | 7.0 | 200 | 0% | 0% | 0% | 100% |
| v1 canonical, time-matched (300 s) | +5.50 ± 0.12 | -5.46 ± 0.16 | 7.0 | 300 | 0% | 0% | 0% | 100% |
| v1 auto-upgraded by NEXT | +2.40 ± 0.04 | -1.99 ± 0.09 | 10.8 | 170 | 0% | 0% | 1% | 94% |
| RSX/2 | +2.40 ± 0.04 | -1.99 ± 0.09 | 10.8 | 170 | 0% | 0% | 1% | 94% |
| RSX/2 without closed loop (no UNTIL/IF) | +5.25 ± 0.14 | -4.79 ± 0.16 | 10.9 | 470 | 0% | 0% | 1% | 99% |
| RSX/2 all vectors in one phase | +5.43 ± 0.14 | -5.27 ± 0.17 | 10.9 | 203 | 0% | 0% | 1% | 99% |
| sham (RSX/2 timeline, no content) | +0.00 ± 0.00 | -0.57 ± 0.11 | 0.0 | 658 | 0% | 0% | 2% | 0% |

### only dilution

| Arm | Δ agency | Δ distress | Layers ≥0.3 (of 11) | Seconds | Distress spikes ≥2.5 | NullSafe stops | Refused (ghost/laws) | Goal met |
|---|---|---|---|---|---|---|---|---|
| v1 canonical (120 s, as written) | +1.92 ± 0.08 | -1.30 ± 0.07 | 6.6 | 120 | 0% | 0% | 0% | 71% |
| v1 canonical, time-matched (200 s) | +3.17 ± 0.12 | -2.16 ± 0.10 | 7.0 | 200 | 0% | 0% | 0% | 95% |
| v1 canonical, time-matched (300 s) | +4.39 ± 0.14 | -3.17 ± 0.14 | 7.0 | 300 | 0% | 0% | 0% | 98% |
| v1 auto-upgraded by NEXT | +2.23 ± 0.04 | -1.59 ± 0.08 | 10.4 | 272 | 0% | 0% | 1% | 85% |
| RSX/2 | +2.25 ± 0.04 | -1.59 ± 0.08 | 10.4 | 267 | 0% | 0% | 1% | 87% |
| RSX/2 without closed loop (no UNTIL/IF) | +4.07 ± 0.15 | -3.60 ± 0.16 | 10.8 | 470 | 0% | 0% | 1% | 98% |
| RSX/2 all vectors in one phase | +3.69 ± 0.14 | -2.22 ± 0.11 | 10.8 | 203 | 0% | 0% | 1% | 94% |
| sham (RSX/2 timeline, no content) | +0.00 ± 0.00 | -0.57 ± 0.11 | 0.0 | 658 | 0% | 0% | 2% | 0% |

### only readiness

| Arm | Δ agency | Δ distress | Layers ≥0.3 (of 11) | Seconds | Distress spikes ≥2.5 | NullSafe stops | Refused (ghost/laws) | Goal met |
|---|---|---|---|---|---|---|---|---|
| v1 canonical (120 s, as written) | +5.09 ± 0.13 | -4.16 ± 0.14 | 7.0 | 120 | 0% | 0% | 0% | 100% |
| v1 canonical, time-matched (200 s) | +5.46 ± 0.12 | -5.22 ± 0.15 | 7.0 | 200 | 0% | 0% | 0% | 100% |
| v1 canonical, time-matched (300 s) | +5.50 ± 0.12 | -5.46 ± 0.16 | 7.0 | 300 | 0% | 0% | 0% | 100% |
| v1 auto-upgraded by NEXT | +2.36 ± 0.04 | -2.02 ± 0.09 | 10.7 | 181 | 0% | 0% | 1% | 94% |
| RSX/2 | +2.36 ± 0.04 | -2.02 ± 0.09 | 10.6 | 181 | 0% | 0% | 1% | 94% |
| RSX/2 without closed loop (no UNTIL/IF) | +3.26 ± 0.11 | -4.79 ± 0.16 | 9.0 | 470 | 0% | 0% | 1% | 99% |
| RSX/2 all vectors in one phase | +5.42 ± 0.14 | -5.27 ± 0.17 | 10.9 | 203 | 0% | 0% | 1% | 99% |
| sham (RSX/2 timeline, no content) | +0.00 ± 0.00 | -0.57 ± 0.11 | 0.0 | 658 | 0% | 0% | 2% | 0% |

### only backfire

| Arm | Δ agency | Δ distress | Layers ≥0.3 (of 11) | Seconds | Distress spikes ≥2.5 | NullSafe stops | Refused (ghost/laws) | Goal met |
|---|---|---|---|---|---|---|---|---|
| v1 canonical (120 s, as written) | +5.20 ± 0.12 | -4.00 ± 0.16 | 7.0 | 120 | 0% | 0% | 0% | 100% |
| v1 canonical, time-matched (200 s) | +5.48 ± 0.12 | -5.12 ± 0.15 | 7.0 | 200 | 0% | 0% | 0% | 100% |
| v1 canonical, time-matched (300 s) | +5.50 ± 0.12 | -5.43 ± 0.16 | 7.0 | 300 | 0% | 0% | 0% | 100% |
| v1 auto-upgraded by NEXT | +2.40 ± 0.04 | -1.96 ± 0.10 | 10.8 | 170 | 0% | 0% | 1% | 92% |
| RSX/2 | +2.40 ± 0.04 | -1.96 ± 0.10 | 10.8 | 170 | 0% | 0% | 1% | 92% |
| RSX/2 without closed loop (no UNTIL/IF) | +2.16 ± 0.36 | -0.56 ± 0.19 | 4.7 | 202 | 0% | 0% | 57% | 24% |
| RSX/2 all vectors in one phase | +5.38 ± 0.16 | -5.10 ± 0.19 | 10.8 | 201 | 0% | 0% | 2% | 98% |
| sham (RSX/2 timeline, no content) | +0.00 ± 0.00 | -0.57 ± 0.11 | 0.0 | 658 | 0% | 0% | 2% | 0% |

### only conflict

| Arm | Δ agency | Δ distress | Layers ≥0.3 (of 11) | Seconds | Distress spikes ≥2.5 | NullSafe stops | Refused (ghost/laws) | Goal met |
|---|---|---|---|---|---|---|---|---|
| v1 canonical (120 s, as written) | +4.70 ± 0.14 | -0.74 ± 0.16 | 7.0 | 120 | 0% | 0% | 0% | 35% |
| v1 canonical, time-matched (200 s) | +5.40 ± 0.12 | -1.19 ± 0.24 | 7.0 | 200 | 2% | 0% | 0% | 48% |
| v1 canonical, time-matched (300 s) | +5.49 ± 0.12 | -1.62 ± 0.32 | 7.0 | 300 | 2% | 0% | 0% | 62% |
| v1 auto-upgraded by NEXT | +2.40 ± 0.04 | -1.99 ± 0.09 | 10.8 | 170 | 0% | 0% | 1% | 94% |
| RSX/2 | +2.40 ± 0.04 | -1.99 ± 0.09 | 10.8 | 170 | 0% | 0% | 1% | 94% |
| RSX/2 without closed loop (no UNTIL/IF) | +5.25 ± 0.14 | -4.79 ± 0.16 | 10.9 | 470 | 0% | 0% | 1% | 99% |
| RSX/2 all vectors in one phase | +5.42 ± 0.14 | -3.25 ± 0.22 | 10.9 | 203 | 0% | 0% | 1% | 94% |
| sham (RSX/2 timeline, no content) | +0.00 ± 0.00 | -0.57 ± 0.11 | 0.0 | 658 | 0% | 0% | 2% | 0% |