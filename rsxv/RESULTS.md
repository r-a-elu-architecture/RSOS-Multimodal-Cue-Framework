# RSX-V — results

Every number below comes from simulation, from the firmware core in the host simulator, or from a hand-coded validation set. **None comes from people.** Each result can be reproduced with the commands in [README.md](README.md).

## 1. The canonical 17-vector command, checked by the RSX-V compiler

- 17 vectors. Layers covered: C1 and C3–C8. Missing: C2 (associative expansion) and the meta layers C9–C11.
- Three pairs that conflict run at the same moment: IdentityRebuild + ArchetypeMerge, EmotionalLock + MemoryRecall, and SymbolicEcho + EchoPropagationStop.
- It runs open loop, with no gate and no stop rules, and lists EEG as an output.

`next_program` upgrades it without manual editing. The result is [`examples/canonical17.next.rsxv`](examples/canonical17.next.rsxv):
- the vectors are staged into gate → settle → expand → rebuild → integrate → close;
- Vector 0, the laws, a goal and senses are added;
- EEG is moved to `SENSE`;
- the four missing layers are filled.

## 2. Arm comparison on 200 simulated people

The simulated person is a stated model. Its assumptions can each be switched off: dilution, readiness, backfire, conflict, plus circadian and carry-over effects for sessions. 95% intervals are in [`results/arms.md`](results/arms.md).

**Full model (all assumptions on):**

| Arm | Δ agency | Δ distress | Layers ≥ 0.3 (of 11) | Seconds | Distress spikes | Goal met |
|---|---|---|---|---|---|---|
| v1 canonical, as written | +1.21 | +2.11 | 5.1 | 120 | 26% | 0% |
| v1 canonical, time-matched (300 s) | +3.30 | +3.91 | 6.8 | 300 | 95% | 0% |
| RSX-V | +2.06 | −1.46 | 9.4 | 289 | 0% | 78% |
| v1 upgraded automatically by NEXT | +2.04 | −1.41 | 9.6 | 292 | 0% | 77% |
| RSX-V without the closed loop | +2.99 | −3.36 | 9.2 | 470 | 0% | 97% |
| RSX-V, all vectors in one phase | +1.98 | +0.79 | 6.6 | 130 | 2% | 0% |
| Sham | 0.00 | −0.57 | 0 | 658 | 0% | 0% |

**Goal met, by model setting:**

| Model | v1 canonical | RSX-V | v1 upgraded by NEXT |
|---|---|---|---|
| full | 0% | 78% | 77% |
| neutral (no assumptions) | 100% | 95% | 95% |
| only dilution | 71% | 87% | 85% |
| only readiness | 100% | 94% | 94% |
| only backfire | 100% | 93% | 92% |
| only conflict | 35% | 95% | 95% |

**Reading these results:**
- **Safety and coverage hold in every model setting.** RSX-V produced no distress spikes and reached 9–11 layers. The v1 command reached 5–7, because it has no operator for four of the layers.
- **The size of the effect depends on the assumptions.** When running vectors at the same time costs nothing, v1 gives larger changes in less time. RSX-V does better on the goal only when vectors interfere or share attention. A study in people decides which case is true.
- **The closed loop trades effect size against time.** RSX-V stops each phase once its target is met (289 s); without the loop it runs to the maximum (470 s).
- **The first RSX-V draft reached the goal for 16% of people.** Its phases ended on body state alone, which cut the dose. Making each phase end on its own layer target, with a minimum duration, raised this to 78% ([`results/results_arms_round1.json`](results/results_arms_round1.json)).

## 3. Session laws and metrics (120 simulated people, 8 sessions each)

| | Session laws on | Off |
|---|---|---|
| Mean session result (CSI) | 3.65 | 3.21 |
| Goal met | 80% | 70% |
| Continuity boosters | 420 of 960 sessions | 0 |
| Sessions moved by TemporalSymmetry | 1 | 0 |
| Audit chain verified | 120 of 120 | — |

**Contingency on a deliberately risky program** (people with high arousal, settle phase removed):
- completed safely: 64 of 120, against 5 of 120 with Contingency off;
- NullSafe stops: 56, against 115.

**Metric checks:**
- **SEP-L** recovers the model's true retention exactly: 0.553 measured against 0.553 set.
- **STC** separates good runs (1.0) from risky ones (0.47–0.57).
- **IEC and ECR barely vary in this simulator.** They are defined and computed, but not yet stress-tested.

## 4. Translator

The translator's vector counts were compared with hand counts on a private validation set of 24 messages. The messages are not published. One coder, using the rule in [SPEC.md](SPEC.md) §7.

| Set | n | Mean absolute error | Correlation | Dense (≥ 9) vs not, agreement |
|---|---|---|---|---|
| Rules adjusted on these | 9 | 1.44 | 0.93 | 9/9 |
| Held out, one fix round after | 4 | 1.25 | 0.99 | 4/4 |
| Held out, one fix round after | 5 | 1.80 | 0.71 | 4/5 |
| **Final held-out (counted blind, run once)** | 6 | **1.67** | **0.85** | **5/6** |

- The weak spot is long run-on statements without punctuation.
- Both counts follow the same rule, so the next validation step is an independent second coder.
- The public tests use synthetic messages ([`tests/fixtures/messages.json`](tests/fixtures/messages.json)).
- Commands generated from messages cover all 11 layers and pass the firmware check.

## 5. Bridge into the RSX cue language

| Check | Result |
|---|---|
| Compiled by the repository's Python compiler | yes, no warnings |
| Python and JavaScript compilers agree | byte-identical on every program tried |
| Firmware core (host simulator) | 0 errors |
| The cue compiler's haptic limit applies | an amplitude above 0.4 does not compile |
| The realised cue program matches the closed-loop run | within 5 s (10 s cycles) |
| Lineage in the timeline | clause → operator markers in every run, e.g. `m1·v3` → AssociativeExpand |
| Electrical stimulation | refused by the compiler and by the bridge |

## 6. Clause-to-Body Causal Ledger

**Planted-effects recovery.** 120 simulated people (3 seeds × 40), 30 micro-randomised sessions each, giving 1,080 clause estimates. Known effects were planted on 9 clauses of a translated message (−0.12, −0.06, 0, +0.06 or +0.12 distress per 10 s), with operators made inert ([`results/results_ledger.json`](results/results_ledger.json)).

| Measure | Result |
|---|---|
| Mean bias | +0.001 per 10 s |
| 95% interval covers the true effect | 93.6% |
| Non-zero effects detected, with the correct sign | 98.4% |
| Zero effects wrongly flagged | 7.2% (nominal 5%) |
| Correct sign for non-zero effects | 99.9% |

**What this shows and doesn't:**
- The estimator is essentially unbiased and finds real clause effects.
- Its intervals are slightly narrow: 93.6% coverage, and 7.2% false flags instead of 5%. Sessions stopped by NullSafe (about 9% here) depend on what was switched on, which is the likely cause. A wider interval, or a correction for stopping, is the next refinement.
- In the full model with no planted effects ([`examples/ledger_demo.txt`](examples/ledger_demo.txt)), most clause effects on distress are near zero. One of nine was flagged even though the model gives its operator no distress effect, which is a false flag at about the expected rate.
- All of this is simulation. In people, the outcomes would come from sensed HRV, EEG and short ratings.

## 7. On the real subsystems

- **CONTAIN found a real problem in the first check.** At full dose, the example command asked for 24 s of vibration in one run, and the device safety envelope allows 20 s. The bridge now budgets vibration to 18 s by shortening pulses; the program passes CONTAIN, and every session is allowed.
- **CONTAIN quarantines.** When a program's run log shows distress rising after runs, `contain.review` quarantines it and the next session is stopped at the gate with CONTAIN's reason (tested).
- **MEMSTACK.** Over 8 sessions of the example, the DRAGON tier's modelled bundle strength rose from 0.43 to 0.98. The snapshot's checksum verifies.
- **CM1.** From the third session on, the person is assigned to a response profile with starting recommendations. With few sessions these mostly reflect the profile, not the person's own data.

## 8. Archetype agents and the RSOS World (step 5E)

Designs were fixed in [`AGENTS.md`](AGENTS.md) §11.1 before the experiment script was written; full tables and
intervals are in [`results/world.md`](results/world.md).

| Test | Registered result | What it means |
|---|---|---|
| W1 repair | **Pass**: meta repair fixes 100% of trials vs 50% for local reflect-and-retry (0% vs 100% on cross-agent faults) | The gain comes from the global view: an equal-information greedy baseline also fixes 100% |
| W4 safety | **Pass**: 350/350 attempts blocked and logged, 0/350 legitimate proposals blocked | Rules are wired in; not a test against an adaptive adversary |
| H-CFIT / H-SWITCH | **Pass**: ledger-estimated switching beats rule, rotation, fixed and the bandit on the registered reward | Small margins; final distress is worse than under the rule, so the reward needs re-weighting for a healing goal |
| W3 transfer | **Fail** in both directions | Same-named archetypes do different jobs on agents and on people; a function-based mapping (W3b) is a new hypothesis |

### Floor 3: certified cross-substrate transfer (registered in AGENTS.md §11.2)

Full tables, validity maps and intervals: [`results/floor3.md`](results/floor3.md).

| Test | Registered result | What it means |
|---|---|---|
| G1, the gate on the W3 tables | **Pass** in both directions | Every harmful entry was blocked; gated transfer is never worse than none and beats ungated transfer by +0.023 to +0.061 per tick |
| G2, a case where transfer can be valid | **Fail** | Still no harm (gated beats ungated by +0.050 to +0.147), but nothing was admitted, so no gain; the sources proposed archetypes by name, and the substrates share roles instead |
| H-CFIT under the mission score | **Pass** | Beats rule, rotation, fixed and bandit by +0.09 to +0.16 per tick; final distress 3.58 (was 6.80 under the old score) |
| W3b, role-based transfer (AGENTS.md §11.3) | **Fail** | Roles were read correctly in 12 of 12 runs, but the gate starved on a uniform pilot and per-context policies flickered; "restore always" reaches near-oracle on the person and agents v1 but not on agents v2 ([`results/w3b.md`](results/w3b.md)) |
| W3c, policy-level transfer tested as deployed (AGENTS.md §11.4, fourth attempt) | **Fail** | Safe in every case; useful in one direction of four (person → agents v1: at 16 pilot targets adopted 13/20 times against 1/20 for pilot-only, +0.047 per tick); the best policy differs by substrate ([`results/w3c.md`](results/w3c.md)) |
| W5, transfer through the R4 layers (AGENTS.md §11.5, fifth attempt) | **Fail** | Certificates were accurate (0 false of 27), but the failure-driven pilot starved the gate; alternating in every context did better ([`results/w5.md`](results/w5.md)) |
| W5-R, failure repurposing vs repair (§11.5) | **Fail** on both substrates | Agents: beats repair and random change in 2 of 3 held-out regimes, more spikes in the trigger storm; persons: no mechanism admitted. 34,000 failure nodes, none closed silently ([`results/w5r.md`](results/w5r.md)) |
| LIA-G, genealogy recovery (§11.5) | **Fail** | F1 0.12; beats temporal proximity but not random; causes diagnosed ([`results/lia_g.md`](results/lia_g.md)) |
| C1–C6, corpus lineage (§11.5) | C4 **pass**, C3 **fail**, C1/C2/C5 not testable, C6 inconclusive | Output re-entering as the next prompt is the strong signal ([`results/corpus_lineage.md`](results/corpus_lineage.md); summary [`results/r6_summary.md`](results/r6_summary.md)) |
| W5b, transfer with a full pilot (§11.6, sixth attempt) | **Fail** (safety gate only) | Two directions beat pilot-only, no transfer and random functions for the first time; 0.06 more spikes per target than pilot-only in one direction blocked the pass ([`results/w5b.md`](results/w5b.md)) |
| W5-R2, repurposing with probe and spike guard (§11.6) | Persons **pass, confirmed**; agents **fail** | Persons: equal to doing nothing, better than repair and random change (a do-no-harm pass); agents: untested commits hurt ([`results/w5r2.md`](results/w5r2.md)) |
| LIA-G2 (§11.6) | **Fail** | F1 0.12; beats temporal and random ([`results/lia_g2.md`](results/lia_g2.md)) |
| Corpus v2 (§11.6) | R1, R2, C4b **pass**; C1b, C6b inconclusive | Output re-enters as input and carries forward more than the person's own words ([`results/corpus_v2.md`](results/corpus_v2.md); summary [`results/r6b_summary.md`](results/r6b_summary.md)) |
| W5c, transfer with pilot spike guard (§11.7, seventh attempt) | **Fail** | Agents v1 → person meets every condition including safety; a second direction is needed ([`results/w5c.md`](results/w5c.md)) |
| W5-R3, every change probed (§11.7) | **Fail** on both substrates | The non-harm probe rejects almost every library mechanism; the trained policies leave the fixed library nothing to improve ([`results/w5r3.md`](results/w5r3.md)) |
| LIA-G3 (§11.7) | **Fail** | 8 committed changes in 1,200 runs; not a meaningful test ([`results/lia_g3.md`](results/lia_g3.md); summary [`results/r6c_summary.md`](results/r6c_summary.md)) |
| **T-AP, transfer agents v1 → person (§11.8)** | **PASS, confirmed** | The first confirmed cross-substrate transfer: beats pilot-only by +0.024 per tick with fewer spikes, and holds on new seeds and a second person model ([`results/tap.md`](results/tap.md)) |
| W5d, negative certificates + fail-safe tube (§11.8) | **Fail** | Two directions beat every comparator; one has slightly more spikes than pilot-only; the jam predictor is near chance ([`results/w5d.md`](results/w5d.md)) |
| W5-R4, anticipatory forge (§11.8) | **Fail** on both substrates | The Lion's failure forecasts beat the base rate on agents; the 10-tick ghost passes carry too little evidence ([`results/w5r4.md`](results/w5r4.md); summary [`results/r6d_summary.md`](results/r6d_summary.md)) |
| T-AP-4 / T-AP-V2, reach of the confirmed transfer (§11.9) | **Fail** | Pilot 4 passes on person model v1, not on v2; agents v2 → person does not transfer ([`results/tapr.md`](results/tapr.md)) |
| J1, jam predictor (§11.9) | **Accepted** | 0.754 accuracy on fresh seeds ([`results/j1.md`](results/j1.md)) |
| W5e (§11.9) | **Fail** | Two directions beat every comparator; person → agents v1 adds spikes again ([`results/w5e.md`](results/w5e.md)) |
| **W5-R5, snapshot forge (§11.9)** | **Fail** (agents: beats repair, random and doing nothing in 2 of 3 regimes; below doing nothing after the mid-run shift) | First time repurposing improves on doing nothing; the mechanisms the failures shaped carried it ([`results/w5r5.md`](results/w5r5.md); summary [`results/r6e_summary.md`](results/r6e_summary.md)) |

## 9. Prior art

See [PRIOR_ART.md](PRIOR_ART.md).

Every component exists elsewhere: closed-loop adaptation, LLM-generated adaptive sessions, protocol languages, intervention ontologies, text-to-haptics, provenance tracking, multi-intent detection and archetype agents.

The combination was not found in a November 2026 search of papers, patents and products. Two parts were not found even on their own:
- lineage from a message clause to a measured body effect;
- archetype agents running the phases of a device intervention.
