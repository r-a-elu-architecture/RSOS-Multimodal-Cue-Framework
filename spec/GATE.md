# GATE: the autonomy gate

Status: built and tested in simulation; effect unproven in people. Implementation: `rsso/rsso/gate.py` and `docs/js/gate.js` (identical, tested), shown on the Safety page (`docs/safety.html#autonomy`), used by the player and the Anchors page. Simulation results: [`rsso/results/gate.md`](../rsso/results/gate.md). Protocol kit: [`kits/GATE_PROTOCOL_KIT.md`](kits/GATE_PROTOCOL_KIT.md). Part of [CONTAIN](CONTAIN.md). Roadmap items 4, 26 and 56; claims C13 and C63.

## 1. Why

A device that detects stress and fires an anchor by itself is the most powerful thing RSOS can do, and the most dangerous. An anchor that was never trained, that has no effect, or that has started to carry stress would be played again and again without the person choosing it. The gate makes automatic use something an anchor earns from evidence, one anchor at a time, and loses again when the evidence weakens.

## 2. Stages

| Stage | What the device may do |
|---|---|
| Manual | Nothing by itself. The person fires the anchor. |
| Suggest | When it detects stress, offer the anchor. The person confirms, declines or marks it "not needed". |
| Automatic | Fire the anchor by itself, within CONTAIN's dose and intensity limits, and ask afterwards whether it helped. |
| Under pressure | Also fire during deliberate pressure practice (stress inoculation). Only with an explicit opt-in. |

## 3. What each stage needs

| Stage | Requirement | Threshold |
|---|---|---|
| Suggest | Paired at a peak by hand (PEAK captures) | 5 |
| | Probes show an effect (PEAK strength) | present or strong |
| | Not taking on stress (PEAK contamination) | risk not high |
| Automatic | Paired at a peak by hand | 8 |
| | Probes show a strong effect | strong |
| | Enough confirmed offers at suggest | 10 |
| | Few false alarms (offers marked "not needed", last 30) | at most 25% |
| | Not worn out (uses since the last pairing) | under 25 |
| | Not taking on stress | risk low |
| | Consent to automatic firing on record | given, not withdrawn |
| Under pressure | The person opted in | yes |
| | Automatic for | 30 days |
| | Confirmed offers | 30 |
| | False alarms | at most 15% |
| | Uses since the last pairing | under 10 |

Stages are cumulative: an anchor reaches a stage only when every requirement of that stage and the ones below it is met. The stage is computed again at every decision, so the gate closes by itself when strength falls, contamination rises, false alarms grow or the anchor wears out.

## 4. Wear-out (claims C13 and C63)

Each use of a cue outside training teaches a little that the cue predicts nothing in particular (latent inhibition and extinction). The gate counts uses since the anchor's last pairing at a peak: from 15 it warns and asks for a new pairing; from 25 it removes automatic use; a new pairing resets the count. This is the testable form of "the same scent all the time has both positive and negative effects" (C13), and the safety side of high cue doses (C63): a dose-response trial (TRIAL) can then measure how many unpaired uses a real anchor tolerates.

## 5. Consent, flags and audit (item 56)

- **Consent records** for each scope: speech profiling, emotion detection, cueing at night, automatic firing and research sharing. Each record holds who gave it, when, and when it was withdrawn. Withdrawal applies at once.
- **Flags** on anything that works below the person's awareness: playing during sleep, blind probes, automatic firing and speech analysis. The flag is shown whenever such an action happens.
- **Audit log** of every automatic decision: time, actor (device or person), action, anchor, decision (allow or deny), reasons and flag. The Safety page shows it and summarises it by action and decision.

`may_fire(anchor, mode, …)` is the single question a device asks before it offers or fires: it returns allow or deny, the stage, the reasons for a denial, and the flag.

## 6. Simulation

`python -m rsso.gate --evaluate` simulates 40 people for each of four anchor kinds (strong; weak; no effect; strong until an outside stressor from day 25) over 60 days, with a stress detector of 85% precision, with and without the gate. Results ([gate.md](../rsso/results/gate.md)):

- strong anchors reached automatic use in all simulated people, around day 11;
- anchors with no effect never fired by themselves (180 firings each without the gate); weak anchors reached automatic in 15% and briefly;
- contaminated anchors lost automatic use within a day of the stressor in 75% of people (the rest were already back at suggest), and none were automatic at day 60;
- a noisy detector (70% precision) keeps most anchors at suggest, where the person confirms each offer.

The simulation shows the gate behaves as designed on known answers. It does not show that automatic firing helps real people; that is the protocol kit's question.

## 7. Limits

- The thresholds are design choices, set so the simulation behaves sensibly; real data should tune them.
- The false-alarm rate depends on people marking offers honestly.
- Stress detection itself (heart rate, EEG, speech) is outside the gate; the gate only decides what may follow a detection.
