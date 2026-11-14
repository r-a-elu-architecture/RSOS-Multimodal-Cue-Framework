# Floor 3 — certified cross-substrate transfer: results

Designs, seeds and pass criteria were fixed in [`../AGENTS.md`](../AGENTS.md) §11.2 and committed before this code
was written. All environments are stated models; **no number here comes from people or production agents.** Scores
are the mission score (gain − 2 × harm rise − spike). Intervals: paired bootstrap, 2,000 resamples, 95%. Within a gate
cell, ticks are treated as independent (disclosed simplification).

## G1 agents → person

Source table: `{"calm": "LEOPARD", "rising": "LEOPARD", "loaded": "LEOPARD", "crisis": "LEOPARD"}`. Gated table: `{"calm": "LION", "rising": "LION", "loaded": "LION", "crisis": "LION"}`.

| Context | Candidate | Decision | Pilot estimate | Lower bound | Truth estimate | False admit | n (cand / base) |
|---|---|---|---|---|---|---|---|
| calm | LEOPARD | reject | -1.002 | -2.136 | +0.049 | no | 13 / 17 |
| rising | LEOPARD | reject | +0.283 | -0.632 | -0.099 | no | 9 / 7 |
| loaded | LEOPARD | reject | -0.631 | -1.220 | -0.213 | no | 40 / 28 |
| crisis | LEOPARD | reject | -0.700 | -1.404 | -0.355 | no | 33 / 34 |

| Arm | Mean mission score / tick |
|---|---|
| GATED | -0.0996 |
| UNGATED | -0.1604 |
| NONE | -0.0996 |
| SHUFFLED-GATED | -0.0996 |

| Contrast | Estimate [95% interval] |
|---|---|
| GATED-UNGATED | +0.061 [+0.057, +0.065] |
| GATED-NONE | +0.000 [+0.000, +0.000] |
| GATED-SHUFFLED-GATED | -0.000 [-0.000, +0.000] |

Better than ungated: yes. Non-inferior to no transfer (margin 0.01): yes. Useful (beats no transfer): no. Beats shuffled: no. **PASS.**

## G1 person → agents

Source table: `{"calm": "LION", "rising": "BEAR", "loaded": "BEAR", "crisis": "BEAR"}`. Gated table: `{"calm": "LION", "rising": "LION", "loaded": "LION", "crisis": "LION"}`.

| Context | Candidate | Decision | Pilot estimate | Lower bound | Truth estimate | False admit | n (cand / base) |
|---|---|---|---|---|---|---|---|
| calm | LION | admit (already baseline) | +0.000 | — | +0.000 | no | 79 / 79 |
| rising | BEAR | reject | -0.060 | -0.060 | -0.042 | no | 10 / 4 |
| loaded | BEAR | reject | +0.273 | -0.511 | -0.047 | no | 11 / 6 |
| crisis | BEAR | reject: too few data | — | — | +0.025 | no | 2 / 0 |

| Arm | Mean mission score / tick |
|---|---|
| GATED | -0.0800 |
| UNGATED | -0.1025 |
| NONE | -0.0800 |
| SHUFFLED-GATED | -0.0800 |

| Contrast | Estimate [95% interval] |
|---|---|
| GATED-UNGATED | +0.023 [+0.020, +0.025] |
| GATED-NONE | +0.000 [+0.000, +0.000] |
| GATED-SHUFFLED-GATED | +0.000 [+0.000, +0.000] |

Better than ungated: yes. Non-inferior to no transfer (margin 0.01): yes. Useful (beats no transfer): no. Beats shuffled: yes. **PASS.**

## G2 agents(v2) → person

Source table: `{"calm": "LEOPARD", "rising": "LEOPARD", "loaded": "TIGER", "crisis": "LION"}`. Gated table: `{"calm": "LION", "rising": "LION", "loaded": "LION", "crisis": "LION"}`.

| Context | Candidate | Decision | Pilot estimate | Lower bound | Truth estimate | False admit | n (cand / base) |
|---|---|---|---|---|---|---|---|
| calm | LEOPARD | reject | -1.002 | -2.136 | +0.049 | no | 13 / 17 |
| rising | LEOPARD | reject | +0.283 | -0.632 | -0.099 | no | 9 / 7 |
| loaded | TIGER | reject | -0.124 | -0.553 | -0.144 | no | 46 / 28 |
| crisis | LION | admit (already baseline) | +0.000 | — | +0.000 | no | 34 / 34 |

| Arm | Mean mission score / tick |
|---|---|
| GATED | -0.0996 |
| UNGATED | -0.2463 |
| NONE | -0.0996 |
| SHUFFLED-GATED | -0.0996 |

| Contrast | Estimate [95% interval] |
|---|---|
| GATED-UNGATED | +0.147 [+0.136, +0.156] |
| GATED-NONE | +0.000 [+0.000, +0.000] |
| GATED-SHUFFLED-GATED | -0.000 [-0.000, +0.000] |

Better than ungated: yes. Non-inferior to no transfer (margin 0.01): yes. Useful (beats no transfer): no. Beats shuffled: no. **PASS.**

## G2 person → agents(v2)

Source table: `{"calm": "BEAR", "rising": "BEAR", "loaded": "BEAR", "crisis": "BEAR"}`. Gated table: `{"calm": "LION", "rising": "LION", "loaded": "LION", "crisis": "LION"}`.

| Context | Candidate | Decision | Pilot estimate | Lower bound | Truth estimate | False admit | n (cand / base) |
|---|---|---|---|---|---|---|---|
| calm | BEAR | reject | -0.317 | -0.802 | -0.007 | no | 22 / 38 |
| rising | BEAR | reject | -0.060 | -0.060 | +0.030 | no | 2 / 3 |
| loaded | BEAR | reject | +0.025 | -0.166 | -0.105 | no | 56 / 72 |
| crisis | BEAR | reject | +0.298 | -0.452 | -0.082 | no | 8 / 13 |

| Arm | Mean mission score / tick |
|---|---|
| GATED | -0.0808 |
| UNGATED | -0.1307 |
| NONE | -0.0808 |
| SHUFFLED-GATED | -0.0808 |

| Contrast | Estimate [95% interval] |
|---|---|
| GATED-UNGATED | +0.050 [+0.048, +0.052] |
| GATED-NONE | +0.000 [+0.000, +0.000] |
| GATED-SHUFFLED-GATED | +0.000 [-0.000, +0.000] |

Better than ungated: yes. Non-inferior to no transfer (margin 0.01): yes. Useful (beats no transfer): no. Beats shuffled: no. **PASS.**

**G1: PASS. G2: FAIL.** False admits: 0 of 0 admitted changes.

## H-CFIT under the mission score (H-CFIT-M)

200 simulated persons, 120 ticks.

| Arm | Mean mission score / tick | Ticks 61–120 | Final distress | Switches |
|---|---|---|---|---|
| watchdog | +0.0447 | +0.0861 | 3.58 | 2.0 |
| rule | -0.0994 | -0.1595 | 2.47 | 67.0 |
| rotation | -0.1101 | -0.1536 | 7.69 | 30.0 |
| fixed | -0.0497 | -0.0027 | 9.77 | 0.0 |
| bandit | -0.0498 | -0.0769 | 1.17 | 69.5 |

| Contrast | Estimate [95% interval] |
|---|---|
| watchdog-rule:all | +0.144 [+0.131, +0.158] |
| watchdog-rule:late | +0.246 [+0.226, +0.266] |
| watchdog-rotation:all | +0.155 [+0.142, +0.168] |
| watchdog-rotation:late | +0.240 [+0.217, +0.264] |
| watchdog-fixed:all | +0.094 [+0.083, +0.105] |
| watchdog-fixed:late | +0.089 [+0.072, +0.106] |
| watchdog-bandit:all | +0.095 [+0.083, +0.106] |
| watchdog-bandit:late | +0.163 [+0.143, +0.183] |

**PASS.**

## What these results show

**The gate works as a safety gate.** In all four directions the source table, used as is, would have lowered the target's
mission score (by 0.023 to 0.147 per tick). The gate rejected every non-baseline entry, so the gated policy equals no
transfer: never worse, and better than ungated transfer in every direction. No harmful change was admitted (0 false admits;
0 admitted changes in total). G1 passes as registered.

**It did not yet deliver useful transfer.** G2 fails: nothing was admitted, so nothing was gained. Two reasons, both visible in
the validity maps:

1. *The sources proposed the wrong archetypes.* An exploratory look at the truth cohorts
   ([`floor3_truth_exploratory.json`](floor3_truth_exploratory.json), computed after the registered results were seen) shows one
   archetype dominating on each substrate: **Bear** for the person (+0.81 to +0.95 over Lion in every context) and **Leopard**
   for the agents (+0.87 to +1.79; in AgentEnvV2 large when calm or rising, near zero when loaded). Each substrate's source
   table proposed its own winner by name, which is the wrong archetype on the other substrate. The gate correctly refused it.
2. *The pilot is small.* 20 targets × 30 ticks gives cells of 2 to 79 ticks; some pilot estimates have the wrong sign.

**The finding behind it.** What the two substrates share is a role, not a name: the *restoring* archetype (Bear for a person,
Leopard for agents) dominates on both, and in AgentEnvV2 its value depends on load. A transfer that carries roles ("restore,
and when to restore") and lets a small pilot identify which archetype plays each role on the target is the next hypothesis
(W3b). It must be compared with a pilot-only baseline that picks the target's best archetype from the same pilot through the
same gate: if transfer adds nothing beyond the pilot, there is no transfer value. Where transfer should help is statistical
power: one hypothesis per context instead of five, which matters most when the pilot is small.

**A weakness found in the gate.** A cell whose scores have zero variance (agents often score exactly the same each tick) gives
a bound equal to the estimate, so a tiny zero-variance cell could be admitted on one or two ticks. It did not happen here.
The fix (a minimum cell size and a variance floor) is a change to the gate and will be registered before it is used.

**H-CFIT under the mission score passes, and the distress problem is mostly fixed.** Ledger-estimated switching beats rule,
rotation, fixed and the bandit by +0.09 to +0.16 per tick. Final distress falls from 6.80 (old score) to 3.58; it is still
higher than the rule (2.47) and the bandit (1.17), which switch about 70 times per session against the Watchdog's 2.
