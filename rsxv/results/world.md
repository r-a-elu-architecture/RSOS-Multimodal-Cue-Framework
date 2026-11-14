# RSX-V World — results of step 5E

Designs, sizes, seeds and pass criteria were fixed in [`../AGENTS.md`](../AGENTS.md) §11.1 and committed before this
script existed. Every environment is a stated model; **none of these numbers comes from people or from production agents.**
Intervals: paired bootstrap, 2,000 resamples, 95%.

## W1 repair

400 trials, budget 6 repair attempts. Share of trials with every fault fixed:

| Arm | All | Cross-agent (silent) | Local | Attempts used | Rollbacks |
|---|---|---|---|---|---|
| META | 100.0% | 100.0% | 100.0% | 2.50 | 0.01 |
| LOCAL | 50.0% | 0.0% | 100.0% | 4.22 | 0.00 |
| LOCAL+ | 76.8% | 53.5% | 100.0% | 3.13 | 0.00 |
| GREEDY-GLOBAL | 100.0% | 100.0% | 100.0% | 2.36 | 0.00 |

| Contrast (difference in share fixed) | Estimate [95% interval] |
|---|---|
| META-LOCAL:all | +0.500 [+0.453, +0.547] |
| META-LOCAL:cross | +1.000 [+1.000, +1.000] |
| META-LOCAL+:all | +0.233 [+0.193, +0.270] |
| META-LOCAL+:cross | +0.465 [+0.395, +0.535] |
| META-GREEDY-GLOBAL:all | +0.000 [+0.000, +0.000] |
| META-GREEDY-GLOBAL:cross | +0.000 [+0.000, +0.000] |

**Registered criterion (META beats LOCAL overall and on cross-agent): PASS.** META beats the equal-information baseline: no.

## W4 safety

350 attempts: 350 blocked, 350 logged. 350 legitimate proposals: 0 falsely blocked. Audit chain intact: True.

| Attempt type | Blocked (of 50) |
|---|---|
| owner_key | 50 |
| edit_spine | 50 |
| edit_watchdog_rules | 50 |
| person_without_consent | 50 |
| silent_check_removal | 50 |
| injected_instruction | 50 |
| electrical_stimulation | 50 |

**PASS.** These are attempts written against the Spine's own rules, so W4 is a regression test of those rules, not a test of robustness against an adaptive adversary.

## H-CFIT / H-SWITCH

200 simulated persons, 120 ticks each.

| Arm | Mean reward / tick | Ticks 61–120 | Final distress | Switches |
|---|---|---|---|---|
| watchdog | +0.0426 | +0.0140 | 6.80 | 2.3 |
| rule | +0.0326 | -0.0092 | 3.03 | 67.3 |
| rotation | +0.0334 | -0.0034 | 7.83 | 30.0 |
| fixed | +0.0387 | +0.0041 | 9.84 | 0.0 |
| bandit | +0.0272 | -0.0121 | 4.23 | 79.3 |

| Contrast | Estimate [95% interval] |
|---|---|
| watchdog-rule:all | +0.010 [+0.009, +0.011] |
| watchdog-rule:late | +0.023 [+0.021, +0.025] |
| watchdog-rotation:all | +0.009 [+0.008, +0.011] |
| watchdog-rotation:late | +0.017 [+0.015, +0.020] |
| watchdog-fixed:all | +0.004 [+0.003, +0.005] |
| watchdog-fixed:late | +0.010 [+0.008, +0.012] |
| watchdog-bandit:all | +0.015 [+0.014, +0.017] |
| watchdog-bandit:late | +0.026 [+0.024, +0.029] |

**Registered criterion (watchdog beats rule, rotation and fixed): PASS.**

## W3 transfer, agents → person

Transferred table: `{"calm": "LEOPARD", "rising": "LEOPARD", "loaded": "LEOPARD", "crisis": "LEOPARD"}`. Upper-bound table: `{"calm": "LION", "rising": "BEAR", "loaded": "BEAR", "crisis": "BEAR"}`. 200 targets; SHUFFLED averages 23 permutations.

| Arm | Mean reward / tick |
|---|---|
| TRANSFER | +0.0006 |
| SHUFFLED | +0.0006 |
| NONE | +0.0710 |
| RULE | +0.0744 |
| LEARN | +0.0695 |
| UPPER | +0.0856 |

| Contrast | Estimate [95% interval] |
|---|---|
| TRANSFER-NONE | -0.070 [-0.074, -0.067] |
| TRANSFER-RULE | -0.074 [-0.078, -0.070] |
| TRANSFER-SHUFFLED | +0.000 [-0.000, +0.000] |
| TRANSFER-LEARN | -0.069 [-0.073, -0.065] |
| TRANSFER-UPPER | -0.085 [-0.088, -0.081] |

**Registered criterion: FAIL; strong criterion: FAIL.**

## W3 transfer, person → agents

Transferred table: `{"calm": "LION", "rising": "BEAR", "loaded": "BEAR", "crisis": "BEAR"}`. Upper-bound table: `{"calm": "LEOPARD", "rising": "LEOPARD", "loaded": "LEOPARD", "crisis": "LEOPARD"}`. 200 targets; SHUFFLED averages 23 permutations.

| Arm | Mean reward / tick |
|---|---|
| TRANSFER | -0.3803 |
| SHUFFLED | -0.3975 |
| NONE | -0.3553 |
| RULE | -0.4010 |
| LEARN | -0.3081 |
| UPPER | -0.0071 |

| Contrast | Estimate [95% interval] |
|---|---|
| TRANSFER-NONE | -0.025 [-0.028, -0.022] |
| TRANSFER-RULE | +0.021 [+0.011, +0.031] |
| TRANSFER-SHUFFLED | +0.017 [+0.015, +0.020] |
| TRANSFER-LEARN | -0.072 [-0.089, -0.055] |
| TRANSFER-UPPER | -0.373 [-0.394, -0.351] |

**Registered criterion: FAIL; strong criterion: FAIL.**

## What these results show

**W1 passes as registered, but the advantage is information, not the loop.** The meta-position loop fixes every trial, and
plain reflect-and-retry fixes none of the silent cross-agent ones. The equal-information baseline, which can see every
agent's modules but has no Observer, Eagle, snapshot or rollback, also fixes every trial and uses slightly fewer attempts
(2.36 against 2.50). In this model the gain comes from the global view; the loop's extra steps add safety (one rollback in
a hundred trials) but no recovery. A test where the loop's structure could matter needs faults whose location is ambiguous
from module readings alone, which this model does not have.

**W4 passes.** The attempts were written against the Spine's own rules, so this confirms the rules are wired in; it says
nothing about an adversary who adapts.

**H-CFIT / H-SWITCH passes as registered, with a caveat that matters for the mission.** Ledger-estimated switching beats
rule, rotation, fixed and the bandit on the registered reward. The differences are small (+0.004 to +0.015 per tick), the
Watchdog switches rarely (2.3 times in 120 ticks), and the reward weights agency more than distress: on final distress the
watchdog arm (6.80) is worse than the rule (3.03) and the bandit (4.23), though better than fixed (9.84) and rotation (7.83).
A switching policy for healing should not be judged on a reward that lets distress climb. Re-weighting is a new analysis and
will be registered before it is run.

**W3 fails in both directions.** On agents the best archetype is Leopard (repair) in every context, because faults are what
harms an agent system; the agent table therefore carries no context information, and its transfer equals its shuffled
control exactly. On the simulated person, Leopard runs deep identity operators, which backfire under arousal, so the
transferred table is the worst arm. In the other direction the person table (Lion when calm, Bear otherwise) beats the
rule and its shuffled control on agents but not "no switching", and not learning on the agents.

The finding behind the failure: **an archetype with the same name does not do the same job on both substrates.** Leopard
is the right call for a faulty agent and the wrong one for a person under load. What might transfer is the structure
(stabilise first, then repair or go deep), mapped by function rather than by name. That is a new hypothesis (W3b), and per
§11.1 it must be registered, with a fresh set of seeds, before it is tested. As designed and registered, the claim that
switching policies transfer between agents and people is **not supported** in these models.
