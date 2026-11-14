# W3c — policy-level transfer tested as deployed: results

Designs, seeds and criteria were fixed in [`../AGENTS.md`](../AGENTS.md) §11.4 and committed before this code was
written. Fourth attempt at positive transfer: confirmatory intervals are at 98.75% (level 0.05 / 4). All
environments are stated models; **no number here comes from people or production agents.** Mission score per tick;
each arm's value is averaged over 20 pilot repetitions, then compared paired over 200 deployment targets.

| Source | Transferred policy | Roles on the source | Policy values on the source |
|---|---|---|---|
| person | R | `{"RESTORE": "BEAR", "DRIVE": "LEOPARD", "STABILISE": "BEAR"}` | BASE -0.088, R +0.239, D -0.150, S +0.239, S>R +0.239, S>D -0.047 |
| agent | S>D | `{"RESTORE": "LEOPARD", "DRIVE": "TIGER", "STABILISE": "LEOPARD"}` | BASE -0.081, R -0.006, D -0.056, S -0.006, S>R -0.006, S>D +0.098 |
| agent_v2 | D | `{"RESTORE": "LEOPARD", "DRIVE": "TIGER", "STABILISE": "BEAR"}` | BASE -0.089, R -0.135, D +0.002, S -0.137, S>R -0.003, S>D -0.062 |

## agent → person, pilot of 4

Transferred: `S>D`. Adopted by the TRANSFER pilot in 0/20 repetitions; PILOT-ONLY adopted a policy in 0/20.

| Arm | Mean / tick |
|---|---|
| TRANSFER | -0.0966 |
| PILOT-ONLY | -0.0966 |
| RANDOM-POLICY | -0.0768 |
| NONE | -0.0966 |
| ORACLE (upper bound) | +0.2340 |

| Contrast (98.75% interval) | Estimate |
|---|---|
| TRANSFER-PILOT-ONLY | +0.0000 [+0.0000, +0.0000] |
| TRANSFER-NONE | -0.0000 [-0.0000, +0.0000] |
| TRANSFER-RANDOM-POLICY | -0.0198 [-0.0203, -0.0193] |

Beats PILOT-ONLY, NONE and RANDOM-POLICY: **no**. Non-inferior to NONE: yes.

## agent → person, pilot of 8

Transferred: `S>D`. Adopted by the TRANSFER pilot in 1/20 repetitions; PILOT-ONLY adopted a policy in 0/20.

| Arm | Mean / tick |
|---|---|
| TRANSFER | -0.0944 |
| PILOT-ONLY | -0.0966 |
| RANDOM-POLICY | +0.1022 |
| NONE | -0.0966 |
| ORACLE (upper bound) | +0.2340 |

| Contrast (98.75% interval) | Estimate |
|---|---|
| TRANSFER-PILOT-ONLY | +0.0022 [+0.0014, +0.0031] |
| TRANSFER-NONE | +0.0022 [+0.0014, +0.0031] |
| TRANSFER-RANDOM-POLICY | -0.1966 [-0.2010, -0.1915] |

Beats PILOT-ONLY, NONE and RANDOM-POLICY: **no**. Non-inferior to NONE: yes.

## agent → person, pilot of 16

Transferred: `S>D`. Adopted by the TRANSFER pilot in 3/20 repetitions; PILOT-ONLY adopted a policy in 3/20.

| Arm | Mean / tick |
|---|---|
| TRANSFER | -0.0916 |
| PILOT-ONLY | -0.0470 |
| RANDOM-POLICY | +0.1027 |
| NONE | -0.0966 |
| ORACLE (upper bound) | +0.2340 |

| Contrast (98.75% interval) | Estimate |
|---|---|
| TRANSFER-PILOT-ONLY | -0.0446 [-0.0471, -0.0420] |
| TRANSFER-NONE | +0.0050 [+0.0025, +0.0078] |
| TRANSFER-RANDOM-POLICY | -0.1943 [-0.1987, -0.1894] |

Beats PILOT-ONLY, NONE and RANDOM-POLICY: **no**. Non-inferior to NONE: yes.

## person → agent, pilot of 4

Transferred: `R`. Adopted by the TRANSFER pilot in 0/20 repetitions; PILOT-ONLY adopted a policy in 0/20.

| Arm | Mean / tick |
|---|---|
| TRANSFER | -0.0778 |
| PILOT-ONLY | -0.0778 |
| RANDOM-POLICY | -0.0778 |
| NONE | -0.0778 |
| ORACLE (upper bound) | +0.0949 |

| Contrast (98.75% interval) | Estimate |
|---|---|
| TRANSFER-PILOT-ONLY | +0.0000 [+0.0000, +0.0000] |
| TRANSFER-NONE | -0.0000 [-0.0000, +0.0000] |
| TRANSFER-RANDOM-POLICY | +0.0000 [+0.0000, +0.0000] |

Beats PILOT-ONLY, NONE and RANDOM-POLICY: **no**. Non-inferior to NONE: yes.

## person → agent, pilot of 8

Transferred: `R`. Adopted by the TRANSFER pilot in 2/20 repetitions; PILOT-ONLY adopted a policy in 0/20.

| Arm | Mean / tick |
|---|---|
| TRANSFER | -0.0706 |
| PILOT-ONLY | -0.0778 |
| RANDOM-POLICY | -0.0700 |
| NONE | -0.0778 |
| ORACLE (upper bound) | +0.0949 |

| Contrast (98.75% interval) | Estimate |
|---|---|
| TRANSFER-PILOT-ONLY | +0.0072 [+0.0059, +0.0085] |
| TRANSFER-NONE | +0.0072 [+0.0059, +0.0085] |
| TRANSFER-RANDOM-POLICY | -0.0006 [-0.0009, -0.0002] |

Beats PILOT-ONLY, NONE and RANDOM-POLICY: **no**. Non-inferior to NONE: yes.

## person → agent, pilot of 16

Transferred: `R`. Adopted by the TRANSFER pilot in 13/20 repetitions; PILOT-ONLY adopted a policy in 1/20.

| Arm | Mean / tick |
|---|---|
| TRANSFER | -0.0309 |
| PILOT-ONLY | -0.0742 |
| RANDOM-POLICY | -0.0337 |
| NONE | -0.0778 |
| ORACLE (upper bound) | +0.0949 |

| Contrast (98.75% interval) | Estimate |
|---|---|
| TRANSFER-PILOT-ONLY | +0.0433 [+0.0357, +0.0507] |
| TRANSFER-NONE | +0.0470 [+0.0386, +0.0549] |
| TRANSFER-RANDOM-POLICY | +0.0028 [+0.0005, +0.0052] |

Beats PILOT-ONLY, NONE and RANDOM-POLICY: **yes**. Non-inferior to NONE: yes.

## agent_v2 → person, pilot of 4

Transferred: `D`. Adopted by the TRANSFER pilot in 0/20 repetitions; PILOT-ONLY adopted a policy in 0/20.

| Arm | Mean / tick |
|---|---|
| TRANSFER | -0.0966 |
| PILOT-ONLY | -0.0966 |
| RANDOM-POLICY | -0.0768 |
| NONE | -0.0966 |
| ORACLE (upper bound) | +0.2340 |

| Contrast (98.75% interval) | Estimate |
|---|---|
| TRANSFER-PILOT-ONLY | +0.0000 [+0.0000, +0.0000] |
| TRANSFER-NONE | -0.0000 [-0.0000, +0.0000] |
| TRANSFER-RANDOM-POLICY | -0.0198 [-0.0203, -0.0193] |

Beats PILOT-ONLY, NONE and RANDOM-POLICY: **no**. Non-inferior to NONE: yes.

## agent_v2 → person, pilot of 8

Transferred: `D`. Adopted by the TRANSFER pilot in 0/20 repetitions; PILOT-ONLY adopted a policy in 0/20.

| Arm | Mean / tick |
|---|---|
| TRANSFER | -0.0966 |
| PILOT-ONLY | -0.0966 |
| RANDOM-POLICY | +0.1022 |
| NONE | -0.0966 |
| ORACLE (upper bound) | +0.2340 |

| Contrast (98.75% interval) | Estimate |
|---|---|
| TRANSFER-PILOT-ONLY | +0.0000 [+0.0000, +0.0000] |
| TRANSFER-NONE | -0.0000 [-0.0000, +0.0000] |
| TRANSFER-RANDOM-POLICY | -0.1988 [-0.2034, -0.1936] |

Beats PILOT-ONLY, NONE and RANDOM-POLICY: **no**. Non-inferior to NONE: yes.

## agent_v2 → person, pilot of 16

Transferred: `D`. Adopted by the TRANSFER pilot in 0/20 repetitions; PILOT-ONLY adopted a policy in 3/20.

| Arm | Mean / tick |
|---|---|
| TRANSFER | -0.0966 |
| PILOT-ONLY | -0.0470 |
| RANDOM-POLICY | +0.1027 |
| NONE | -0.0966 |
| ORACLE (upper bound) | +0.2340 |

| Contrast (98.75% interval) | Estimate |
|---|---|
| TRANSFER-PILOT-ONLY | -0.0496 [-0.0507, -0.0483] |
| TRANSFER-NONE | -0.0000 [-0.0000, +0.0000] |
| TRANSFER-RANDOM-POLICY | -0.1994 [-0.2040, -0.1941] |

Beats PILOT-ONLY, NONE and RANDOM-POLICY: **no**. Non-inferior to NONE: yes.

## person → agent_v2, pilot of 4

Transferred: `R`. Adopted by the TRANSFER pilot in 0/20 repetitions; PILOT-ONLY adopted a policy in 0/20.

| Arm | Mean / tick |
|---|---|
| TRANSFER | -0.0781 |
| PILOT-ONLY | -0.0781 |
| RANDOM-POLICY | -0.0781 |
| NONE | -0.0781 |
| ORACLE (upper bound) | +0.0130 |

| Contrast (98.75% interval) | Estimate |
|---|---|
| TRANSFER-PILOT-ONLY | +0.0000 [+0.0000, +0.0000] |
| TRANSFER-NONE | +0.0000 [-0.0000, +0.0000] |
| TRANSFER-RANDOM-POLICY | +0.0000 [+0.0000, +0.0000] |

Beats PILOT-ONLY, NONE and RANDOM-POLICY: **no**. Non-inferior to NONE: yes.

## person → agent_v2, pilot of 8

Transferred: `R`. Adopted by the TRANSFER pilot in 1/20 repetitions; PILOT-ONLY adopted a policy in 0/20.

| Arm | Mean / tick |
|---|---|
| TRANSFER | -0.0736 |
| PILOT-ONLY | -0.0781 |
| RANDOM-POLICY | -0.0754 |
| NONE | -0.0781 |
| ORACLE (upper bound) | +0.0130 |

| Contrast (98.75% interval) | Estimate |
|---|---|
| TRANSFER-PILOT-ONLY | +0.0046 [+0.0044, +0.0046] |
| TRANSFER-NONE | +0.0046 [+0.0044, +0.0046] |
| TRANSFER-RANDOM-POLICY | +0.0018 [+0.0018, +0.0019] |

Beats PILOT-ONLY, NONE and RANDOM-POLICY: **yes**. Non-inferior to NONE: yes.

## person → agent_v2, pilot of 16

Transferred: `R`. Adopted by the TRANSFER pilot in 1/20 repetitions; PILOT-ONLY adopted a policy in 0/20.

| Arm | Mean / tick |
|---|---|
| TRANSFER | -0.0736 |
| PILOT-ONLY | -0.0781 |
| RANDOM-POLICY | -0.0701 |
| NONE | -0.0781 |
| ORACLE (upper bound) | +0.0130 |

| Contrast (98.75% interval) | Estimate |
|---|---|
| TRANSFER-PILOT-ONLY | +0.0046 [+0.0044, +0.0046] |
| TRANSFER-NONE | +0.0046 [+0.0044, +0.0046] |
| TRANSFER-RANDOM-POLICY | -0.0034 [-0.0042, -0.0027] |

Beats PILOT-ONLY, NONE and RANDOM-POLICY: **no**. Non-inferior to NONE: yes.

**Primary criterion (pilot 8): FAIL.**

**W3c overall (primary and confirmation): FAIL.**

## What these results show

**W3c fails as registered**: at pilot size 8 only one direction met all three comparisons, and that one is an artifact (below).
With W3, G2 and W3b this is the fourth registered attempt at useful cross-substrate transfer, and none has passed.

**Why, in one line: the best whole policy differs by substrate, so what the source learns is usually the wrong thing to try.**
The source tables in the first table of this file show it. On the person, restoring or stabilising (both Bear) is best
(+0.239 per tick, against −0.088 for no change). On agents v1, stabilise when loaded and otherwise drive is best (+0.098).
On agents v2, driving is best (+0.002); restoring there is harmful (−0.135). Mapped through roles:
- agents → person sends "stabilise when loaded, else drive" or "drive", which on a person means deep identity work (Leopard)
  and is harmful; the gate kept it out in 19 of 20 and 20 of 20 repetitions;
- person → agents sends "restore always" (Leopard). On agents v1 that is a real gain: at pilot size 16 transfer adopted it in
  13 of 20 repetitions, against 1 of 20 for the pilot-only search, and beat no change by +0.047 per tick and the pilot-only
  search by +0.043. At pilot size 8 it was adopted in only 2 of 20 repetitions, so the gain was too small to pass;
- on agents v2, "restore always" is harmful. The single repetition that adopted something at pilot size 8 had misread the
  target's roles (RESTORE read as Tiger), so it deployed Tiger, which happens to be v2's best archetype. That is the "pass" in
  that direction: luck from a misreading, not transfer.

**What does hold, across all four attempts.**
- *No harm.* In every direction, size and attempt, the gated transfer was non-inferior to no change.
- *When the source is right, transfer is far more efficient than searching blind.* Person → agents v1 at 16 pilot targets is the
  clearest case. This is the efficiency the method was built for, but here it showed up in one direction of four, so it is not a
  general result.
- *Roles cross substrates* (W3b): a small pilot reads which archetype restores, drives or stabilises.

**Conclusion for this line of work.** In these models, cross-substrate transfer of policies is safe but rarely useful: the
source's best policy is valid on the target in 1 of 4 directions. A fifth variant tuned on these results would no longer be a
fair test. What remains open needs data that were not generated here: real agent traces and real human data.
