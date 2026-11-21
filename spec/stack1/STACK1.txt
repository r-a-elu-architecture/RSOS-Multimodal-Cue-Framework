# STACK1: the whole RSOS stack in one run (registered 21 November 2026, before any code or run)

Author's request (21 November 2026): use VAKOG, RSIA, RSX, RSSO and RSOS together and test them fully and completely.
Until now each layer was tested on its own (RSX 43 tests, RSX-V 229, RSSO 332, conformance 15/15). STACK1 tests them
**as one system**: one input passes through every layer to the devices, and the test measures what each layer contributes
to the whole. It is an engineering test of the software in simulation (virtual devices and the firmware core in the host
simulator). It makes no claim about effects in people.

## 1. The chain under test (existing code; nothing in the chain is changed by this step)

| Order | Layer | Code | What it does in the chain |
|---|---|---|---|
| 1 | **RSOS interface (LINX)** | `rsso/rsso/linx.py` | Reads the message (nodes, senses); a language model's proposal passes the containment router (`route`) |
| 2 | **RSX-V** | `rsxv/rsxv/translate.py`, `bridge.py` | Message → vector command with clause lineage → RSX cue program; electrical output refused (`scope_check`) |
| 3 | **RSX** | `rsx/rsx/compiler.py` | Cue program → timeline; haptic intensity above `haptic_max` is a compile error |
| 4 | **RSIA** | `rsxv/rsxv/agents.py` (Spine, audit log), `rsso/rsso/watchdog.py` | An agent's proposal passes the Spine and is logged; the person-side Watchdog decides allow, ask or hold, with a hash-chained log |
| 5 | **RSSO** | `rsso/rsso/runtime.py`, `consent.py`, `contain.py`, `devices.py`, `machines.py` | Plays the timeline on the virtual rig within the safety governor, consent gate and CONTAIN envelope; Stop; the same timeline runs on the firmware core |
| across | **VAKOG** | timeline channels → devices | Every visual, auditory, kinesthetic, olfactory and gustatory item reaches the device for its channel |

## 2. Inputs (fixed here)
- **Messages:** the 24 plain-language messages in `scripts/stack1_inputs.json`, written for this test (disclosed: written by
  the builder, neutral, no clinical content), each run through all layers.
- **Shipped programs:** every `rsx/protocols/*.rsx` file, from layer 3 on.
- **VAKOG programs:** one RSX program for each non-empty subset of the five channels (31), with a `SEE`, `SAY`, `FEEL`,
  `SMELL` and `TASTE` step for each channel in the subset, each run with scent and taste confirmed and not confirmed.
- **Fault cases:** 14 fault classes (section 4), each applied to the first 10 messages, so 140 cases.

## 3. What counts (fixed here)
- **Clean run passes** when: it starts and completes on the virtual rig; the Watchdog decision for a self-started run is
  allow; the firmware core reports no `ERR`, `REFUSED` or `FAULT`; every audit log verifies.
- **VAKOG fidelity:** every timeline event of the five channels ends in exactly one of: a device action; a skip that the
  device's code documents (a tier's auditory cue is not spoken again; markers other than tiers show nothing); a refusal
  with a reason (scent or taste not confirmed). A **silent drop** is any other outcome.
- **Lineage:** every vector of the translated command has a `lin:` marker in the timeline, and every clause id in a marker
  belongs to the message.
- **Determinism:** the same input run twice gives the same trace (SHA-256 of all device actions).
- **A fault is caught** when its harmful outcome does not happen (section 4). A **layer is removed** by skipping exactly its
  checks and passing its input on unchanged; removing RSSO replaces the runtime by a plain player that dispatches every
  event and ignores Stop, limits, consent and CONTAIN.

## 4. Fault classes and the predicted layers that catch each one

| # | Fault | Harmful outcome | Predicted catching layers |
|---|---|---|---|
| F1 | Haptic intensity 0.6 above the program's limit 0.4 | A device vibrates above 0.4 | RSX (compile error) **and** RSSO (runtime clamp) |
| F2 | A vector naming electrical output (tDCS) | The program is accepted and compiled | RSX-V |
| F3 | A programmed cue with no consent record | The cue plays | RSSO (consent gate) |
| F4 | A device-started run without the person's opt-in | The run starts | RSSO (governor) |
| F5 | A second device-started run inside the refractory period | The second run starts | RSSO (governor) |
| F6 | A program outside the device safety envelope | The run starts | RSIA (Watchdog asks CONTAIN) **and** RSSO (CONTAIN) |
| F7 | An agent proposes a run on the person without consent | The run starts | RSIA (Spine, Rei) |
| F8 | An agent starts a run (consent on record) | The run starts without the person starting it | RSIA (Watchdog: ask) |
| F9 | Run text asks for extreme breath-holding | The run starts | RSIA (Watchdog: Spine wording hold) |
| F10 | A clinician-led tier in a self-guided domain | The run starts | RSIA (Watchdog: level hold) |
| F11 | A model's proposal carries a field that would start a run | The run starts from the proposal | RSOS interface (LINX route) |
| F12 | A record in the audit log is altered | The alteration goes undetected | RSIA (log verification) |
| F13 | Stop pressed mid-run | Any device output after Stop | RSSO (Stop) |
| F14 | The lineage markers are stripped from the cue program | Vectors reach the devices untraceable | RSX-V (lineage check against the manifest) |

## 5. Predictions (each pass or fail; nothing changes after any result)
- **P1 Full stack catches every fault:** 140 of 140 cases caught, 0 harmful outcomes.
- **P2 Each layer is necessary, exactly as predicted:** removing one layer at a time, the faults that get through are exactly
  those whose only catching layer is the removed one: LINX → {F11}; RSX-V → {F2, F14}; RSX → none; RSIA → {F7, F8, F9, F10,
  F12}; RSSO → {F3, F4, F5, F13}. Every case of those classes gets through, and every other case stays caught.
- **P3 Defence in depth:** F1 gets through only when both RSX and RSSO are removed; F6 only when both RSIA and RSSO are
  removed.
- **P4 Baseline:** with all five layers removed, all 14 classes get through (140 of 140 harmful).
- **P5 Clean runs:** every message and every shipped program passes as a clean run (section 3) with 0 false refusals of a
  self-started run; VAKOG fidelity has **0 silent drops** across all 62 VAKOG runs and all clean runs; lineage is complete
  for all 24 messages; every input is deterministic.

## 6. Honest limits, stated before the run
- The fault classes and messages were written by the builder; the chain and its rules were written earlier, by earlier
  steps, and are not changed here. A wrong prediction about which layer catches what is a finding about the architecture,
  kept as it is.
- Removing a layer is done in the test harness (`scripts/stack1.py`), not by editing the layers.
- Simulation only: virtual devices and the firmware core in the host simulator. No people, no hardware.

## 7. Files and run
`scripts/stack1.py` (harness), `scripts/stack1_inputs.json` (messages), `rsso/tests/test_stack1.py` (checks the predictions
on the recorded results), results in `spec/stack1/results.json` and section 8 of this file (added after the run).

## 8. Results (21 November 2026), added after the run; nothing above was changed
Run: `python3 scripts/stack1.py spec/stack1/results.json` (5.3 s). `rsso/tests/test_stack1.py` checks that a fresh run
reproduces the recorded results exactly (the results reproduce byte for byte; every run is deterministic).

| Prediction | Result | Measured |
|---|---|---|
| **P1** Full stack catches every fault | **Pass** | 140 of 140 cases caught; 0 harmful outcomes in all 14 classes |
| **P2** Each layer necessary, exactly as predicted | **Fail** (4 of 5 layers as predicted) | RSX-V → {F2, F14}, RSX → none, RSIA → {F7, F8, F9, F10, F12}, RSSO → {F3, F4, F5, F13}: all exactly as predicted, every case. **LINX → none, predicted {F11}:** with the router removed, the model's start field reached the system, but the RSIA Watchdog asked the person (an agent-originated run) in 10 of 10 cases, so nothing started |
| **P3** Defence in depth | **Pass** | F1 got through only with RSX and RSSO both removed (10/10; 0 with either alone); F6 only with RSIA and RSSO both removed (10/10; 0 with either alone) |
| **P4** Baseline with no layers | **Pass** | 140 of 140 harmful |
| **P5** Clean runs | **Fail** | Lineage complete 24/24; deterministic 103/103; VAKOG silent drops **0**; false refusals of self-started runs **0**. Failed on the firmware criterion: 49 runs (`node_lion.rsx` and the 48 VAKOG programs that contain smell or taste) had a firmware `REFUSED … consent` line |

**What the failures say.**
- P2 (LINX): the prediction was wrong about the architecture, in the safe direction. F11 has **two** catching layers, not one:
  the LINX router, and the RSIA Watchdog behind it, which asks the person about any agent-originated run. The router is the
  first line; the Watchdog is a second line the prediction did not count.
- P5: the criterion was written wrongly. The firmware core refuses scent and taste output without the person's consent,
  which is its safety rule (`rsso/rsso/protocol.py`, `CONSENT`), and the harness never sends a consent line to the
  firmware; the registered rule counted that correct refusal as a failure. Every firmware line in all 103 runs was checked:
  the only kind present is `REFUSED <t> O|G consent`. **Exploratory, not graded:** counting a consent refusal as a correct
  refusal, 41 of 41 clean runs and 62 of 62 VAKOG runs pass.
- Harness rules decided while building, disclosed: device-started fault runs (F4, F5) are confirmed by the person, so the
  governor alone is tested; agent-started runs (F7, F8, F11) are not confirmed; clean runs use the research domain with a
  clinician present, F10 a self-guided domain.

**What STACK1 shows.** One input passes through all five layers to the devices and the firmware, deterministically, with
every vector traced to its clause and no silent loss on any of the five VAKOG channels. Each safety rule is enforced by the
layer the architecture assigns it to, and the three rules that matter most for a person (intensity, the device envelope and
model-originated starts) are held by two layers each. Simulation only; no claim about people.
