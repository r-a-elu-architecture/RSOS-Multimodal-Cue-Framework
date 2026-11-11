# Results: RSOS Verifiable Cue-Routing v0.6

**Timestamp:** 2026-11-11 UTC. **Evidence class:** fully executed reproducible *software* tests and completely synthetic behavioral-state observations. NOT a clinical trial, real BCI recording, neural plasticity assay, or efficacy comparison with EMDR/CBT.

## Strongest new finding

A Grok user-supplied four-branch *narrative* described tier handoff only when proxy EEG is calm and aligned and token absent; it seals on agitated input. Therefore the reported Grok test of the gate does not directly demonstrate repurposing during a negative state. The rebuilt design offers voluntary grounding during observed high arousal and only permits resource-cue offers and later user-confirmed consolidation when signal/permission checks pass. The protocol is a bounded software contract, not an actual trauma processing mechanism.

## Executed verification

* Primary finite grid: **24,576** cases, **0** contract violations.
* Dual-observation finite grid: **73,728** cases, **0** contract violations, including absent corroborating input.
* Combined bounded checks: **98,304** cases. The enum varies 10 Boolean flags, a 3-valued arousal proxy, two qualities, two confidence levels, two quiet-history levels and (in the dual version) three corroborator states. Real continuous sensor streams and arbitrarily long temporal sequences are **not covered**.
* Random observation fuzz: **14,000** cases, **0** contract violations.
* Authenticated audit replay: clean 14,000-event chain verifies; **1,800 / 1,800** deliberately corrupted short logs were rejected. Assumes the HMAC key remains secret.
* Unit tests: **10 / 10** passed.
* An initial dropout fallback defect produced 128 contract violations in a development run; it was fixed **before final verification**. This issue and fix are openly reported here.

## Synthetic head-to-head (ALL eight scenarios)

**Eight scenarios × 180 synthetic participants × 96 encounters = 138,240 observations *per policy*, paired by identical underlying observations**. The simulated 'latent arousal' is used for scoring only; none of the policies sees it. 'Appropriate grounding' means a `grounding_offer` while the latent *synthetic proxy* exceeded 0.68. 'High-arousal resource action' means a resource-like or consolidation action when the latent proxy exceeded 0.68. **Neither is an empirically measured therapeutic benefit or medical adverse event.**

| Policy | Grounding offers on high arousal ↑ | Resource-type output on high arousal ↓ | Intervention frequency | Software contract violations |
|---|---:|---:|---:|---:|
| grok_text_reconstruction | 0.00% | 9.44% | 59.51% | 78219 |
| permissive_threshold | 0.00% | 100.00% | 42.31% | 32467 |
| fixed_source_with_consent | 0.00% | 96.21% | 36.58% | 24542 |
| matched_generic_safety | 78.58% | 17.41% | 35.92% | 0 |
| RSOS_staged_contract | 78.58% | 17.41% | 35.92% | 0 |
| conventional_dual_sensor | 87.63% | 7.41% | 34.55% | 0 |
| RSIA_dual_sensor | 87.63% | 7.41% | 34.55% | 0 |

**Paired participant-cluster bootstrap**, dual-channel RSIA-inspired minus single-channel staged RSOS:

* High-arousal resource-type output: **−10.00 percentage points**, 95% CI **[−11.12, −8.99]** points; relative proxy reduction 57.4%.
* High-arousal grounding offer: **+9.05 percentage points**, 95% CI **[+7.98, +10.15]** points.
* Intervention frequency: 35.92% single vs 34.55% dual; **not exactly dose-matched**.
* **Matched conventional dual-sensor policy has identical routing results**. The innovation is a publicly inspectable specialized protocol and audit pipeline, not unique algorithmic superiority.

## Adversarial scenario effects

| Scenario | One channel: high-arousal resource action ↓ | Two channels: same ↓ | One: grounding ↑ | Two: grounding ↑ |
|---|---:|---:|---:|---:|
| ordinary | 18.97% | 6.90% | 78.45% | 90.52% |
| high_decoder_noise | 30.51% | 16.95% | 65.25% | 78.81% |
| misleading_genealogy | 29.41% | 8.24% | 65.88% | 88.24% |
| benign_arousal_shift | 18.04% | 7.11% | 79.07% | 90.00% |
| burst_load | 14.87% | 6.21% | 81.17% | 89.93% |
| sensor_dropout | 20.00% | 8.24% | 57.65% | 69.41% |
| correlated_artifact | 26.37% | 24.18% | 69.23% | 71.43% |
| secondary_dropout | 22.66% | 7.03% | 75.78% | 62.50% |

**Counterevidence:** on strongly correlated artifacts, the two-channel proxy reduction shrinks substantially; when the second channel is absent, conservative abstention reduces intervention availability. Correct-by-construction *observable* software rules cannot guarantee safety under mismeasured latent human state: single-channel software had zero contract violations but 17.41% high-latent-state resource-type actions. Even dual had 7.41% of the same proxy mismatch. Those figures show a sensor-model problem, not proven patient harm or safety rates.

## Causal and novelty boundaries

1. **Same-information conventional comparators tie RSOS** on safety routing and grounding coverage. Adding symbolic terminology does not, by itself, change output correctness.
2. **No distinct longitudinal cue-genealogy effect** is established by this test; source confidence is simulated and can be wrong. Existing v0.5 genealogy shuffles also failed to show an effect.
3. **The protocol never simulates a person's mental state changing after a prompt.** Thus no memory reconsolidation, emotional healing, symptom reduction, reconditioning durability or BCI clinical advantages are measured.
4. **Grok reconstruction is incomplete:** no original Grok scripts, real signals, input sequence or authorization definition were provided. We cannot attribute the reconstruction's policy mismatch counts to Grok's actual runtime.
5. **Existing prior art:** NASA RTA/Simplex and other safety shielding already provide rigorous runtime fallback. BrainFlow already provides sensor acquisition and replay. Novelty would have to come from a validated, substantive source-aware and outcome-aware intervention benefit, not a standalone seal/residual gate.
6. **Timestamps and privacy:** Archive SHA256 strings in `ARCHIVE_HASHES.json` establish version custody of the provided private documents, not originality or efficacy. Public package contains no private chat messages or copyright texts.

## Strong public research claim and experimental next step

**Supported public claim:** “We release a consent-gated, provenance-configurable, auditable, two-phase human–AI cue-routing controller and adversarial sensor-stress benchmark. Finite grid checks and tamper tests found no contract violations under tested assumptions; independent-signal corroboration improved modeled risk routing, while a matched generic controller performed identically. The current system is research software, not validated treatment.”

**Next distinctive experiment:** recruit a medically supervised partner to collect real longitudinal cue/context/sensor data with voluntary interventions, verified cue histories, delayed responses and randomized state-only vs origin-aware scheduling at fixed dose; preregister delayed recurrence, no-intervention decisions and adverse events. Until then a stronger simulation score does not yield clinical evidence.