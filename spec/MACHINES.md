# MACHINES: more channels, and one profile format for people and agents

Status: built and tested in simulation; effect unproven in people. Implementation: `rsso/rsso/machines.py` and `docs/js/machines.js` (identical, tested), `rsso/rsso/pron.py` and `docs/js/pron.js` (identical, tested), `rsso/rsso/ssep.py` (EEG analysis), the firmware core (`firmware/rsos_core`), pages `docs/device.html#channels`, `docs/device.html#pron` and `docs/agents.html`. Simulation results: [`machines.md`](../rsso/results/machines.md), [`channels_firmware.md`](../rsso/results/channels_firmware.md), [`pron.md`](../rsso/results/pron.md), [`ssep.md`](../rsso/results/ssep.md). Protocol kit: [`kits/MACHINES_PROTOCOL_KIT.md`](kits/MACHINES_PROTOCOL_KIT.md). Roadmap items 9, 10, 15, 19, 29, 36, 38, 42, 43 and 44; claims C14, C35, C56, C60, C67, C70, C71 and C72: C14, C35, C70 and C72 have tests built; C56, C60, C67 and C71 are tracked against public evidence in [PRIOR_ART.md](PRIOR_ART.md#step-8-claims-tracked-against-public-evidence).

## 1. Why

RSOS programs, codes and profiles are defined above any hardware. This module does two things with that:

1. It adds channels beyond the phone and the wristband (posture, temperature, images, several body sites, carrier and rhythm of a vibration), each with a draft protocol line and safety limits, so a builder can implement them without changing a program.
2. It gives an AI agent or robot a profile in the same shape as a person's identity profile (symbol, code, values) and makes the values do work: every action is checked against them before it runs. The person and the agent can then signal to each other in the same glyph codes.

## 2. Device classes

| Class | Channels | State |
|---|---|---|
| Phone | haptic, sound, display, posture | works now |
| Wristband | haptic | works now (RDP/1) |
| Scent module | olfactory | works now (RDP/1) |
| Wrist cooling and warming | thermal | runs on the firmware core in simulation; module not built |
| Motors on several body sites | haptic | runs on the firmware core in simulation; module not built |
| Smart glasses | display, sound | the image line runs on the firmware core in simulation; not built |
| Sleep or EEG headband | EEG, sound | draft protocol (see NIGHT) |
| Implanted device | none | specification only |

The implant class is listed so the layer's boundary is explicit: RSOS programs, anchors and profiles sit above any hardware; an implant would need its own clinical and regulatory pathway, and nothing here drives one. The claims about implants (C56, C60, C67) are kept as claims and tracked against public data; none is tested here.

## 3. RDP/1.1 channel lines

Each is one ASCII line, at most 96 bytes, checked by `check()` on the host before it is sent, and enforced again by the firmware core on the device ([DEVICE_PROTOCOL.md §6](DEVICE_PROTOCOL.md#6-rdp11-channel-lines)):

```
T  <t_ms> <dur_ms> <delta_c>                                   temperature change
D  <t_ms> <dur_ms> <image_id>                                  an image on a display
HF <t_ms> <on_ms> <off_ms> <count> <amp> <carrier_hz> <mod_hz> <site>   vibration with carrier, rhythm and body site
```

Envelope (`ENVELOPE_X`): temperature change at most 4 °C either way, at most 2 minutes, at most 4 a run; an image at most 10 s, and at most 0.2 brightness at night; vibration strength at most 0.6; carrier 20-300 Hz; rhythm 1-40 Hz; at most three body sites at once. Sites: left wrist, right wrist, upper arm, chest, upper back, ankle. CONTAIN's rules hold unchanged: nothing on these channels starts a program the person did not start.

The firmware core runs these lines with the limits enforced on the device: the channel suite X1-X11 (`python -m rsso.machines --channels`) passes 11 of 11 in the host simulator, including 400 random commands on which the host check and the device never disagree (a command the host accepts plays unchanged; one it refuses is refused or clamped by the device). Parts and wiring for the modules are in [BOARD_KIT.md §8](../firmware/BOARD_KIT.md#8-rdp11-modules-not-yet-built).

## 4. Channels

- **Posture (item 9).** Forward tilt from the gravity vector of a phone worn or held upright. A slouch is above 25 degrees for 5 seconds; it ends below 15 degrees (hysteresis, so it cannot flicker). Each slouch is cued once ("sit tall"); the live page vibrates at most every 20 seconds.
- **Temperature (item 9).** The firmware core plays `T` lines and returns to neutral on Stop or link loss; no thermal module is built.
- **Display (item 15).** A lock-screen image with a profile's symbol and phrase, generated on the page. AR glasses use the `D` line; not built.
- **Several body sites (item 38).** `spread(code, sites)` puts each group of a code on the next site, so a two-part code is felt in two places.
- **Carrier and rhythm (item 29).** The `HF` line carries both; the page plays them as sound. Claim C35 (a 12 Hz vibration helps focus; 7.8 Hz gives a theta state) has two tests built: the EEG test in §11 and the TRIAL design `rhythm_focus` (2-back score with a 12 Hz rhythm against the same vibration without one). Nothing relies on the claim.
- **Pronunciation (item 10).** Built: see §10. Moving the person's muscles to match is out of scope.

## 5. An identity layer for agents (item 42)

```
{schema: "rsos-agent/1", id, name, symbol, code,
 values: [{id, name, forbid: [tags], prefer: [tags], weight}],
 watch: {tag: flags}, seen: {tag: count}, log: [...]}
```

`check_action(agent, action)` simulates an action (`{id, title, tags}`) against the values before it runs:

1. a tag a value forbids: **override** (not done), naming the value;
2. otherwise a tag the person has flagged on at least 60% of the actions that carried it: **ask** first;
3. otherwise **allow**, with the support of values that prefer its tags.

`act()` checks and logs. Nothing the agent decides starts a person's program.

## 6. The person's signals (item 44)

`human_signal(agent, ts, kind)` takes an error-related or stress signal from the person (from EEG, heart rate or a button) within 10 seconds of the agent's last allowed action and flags it; the tags of flagged actions count towards the watch list. The 60% rule means a tag shared with many fine actions is not blamed. `answer()` records the person's yes or no when the agent asked. `alignment()` summarises the log.

## 7. The glyph channel (item 43)

Agent states: ok `. .`, working `. -`, needs input `- .`, value conflict `- -`, stopped `---`. Person replies: yes `.`, no `-`, wait `..`, stop `---` (always obeyed at once). `code_pulses()` and `decode_pulses()` map codes to pulse timings (dot 100 ms, dash 300 ms, 100 ms within a group, 400 ms between groups; read as a dash from 200 ms, a new group from 250 ms).

## 8. Content packs (item 19)

```
{schema: "rsos-pack/1", id, title, center, rules: [{id, rule, words, response, code}], values: [...]}
```

At least three rules. `pack_matrices()` turns the rules into copilot matrices of three branches; `pack_issues()` reports rules without words and duplicated codes. A pack's values can be given to an agent. Two packs ship: "What is up to me" and "Safe lab practice".

## 9. Simulation results (agents and channels)

From [`rsso/results/machines.md`](../rsso/results/machines.md), 50 runs per row:

- Consistency (C70): at choice noise 0.1, a plain agent chose the same option all five times in 29.8% of scenarios and broke a value in 64% of choices; the gated agent: 38.8% and 0%.
- Error signal: detected 80% of the time, disliked actions fell from 13.4% in the first third to 0% in the last, with 7.3 fine actions asked about of about 30.
- Posture: 100% of slouches cued, no false cues, 6.2 s after the slouch began.
- Glyph decoding: about 98% correct at 40 ms of timing jitter, about 80% at 70 ms.

The value check removes value-breaking choices by construction; what it shows is the size of the gap and the cost in asking. It only knows what its values name. Whether people trust or prefer such agents (C72) is untested.

## 10. Pronunciation (item 10, claim C14)

`compare(learner, model)` compares a recording with a model at 8 kHz, syllable by syllable:

- **Melody**: pitch (autocorrelation of the centre-clipped frame; the shortest lag that repeats at twice the lag, so neither half the pitch nor a formant is read as it; octave slips folded towards the speaker's median) at five points of each syllable, in semitones from each speaker's own median.
- **Vowels**: the spectral envelope in 14 log-spaced bands (smoothed over 280 Hz so the voice's harmonics do not count) in the middle 60% of each syllable, with tilt removed and one shift for the whole recording (a longer or shorter vocal tract moves every formant by the same ratio).
- **Rhythm**: each syllable's share of the phrase.

The largest difference over its threshold (melody 2 semitones, vowels 5.5, rhythm a ratio of 1.43) becomes the feedback, naming the syllable. Drills are synthesised from a vowel and melody model (five drills). With the camera switched on (it loads Google's face model into the page; the video stays on the device), `mouth_feedback` compares each syllable's median mouth opening and lip rounding with the vowel's target.

Results (`rsso/results/pron.md`, 40 simulated learners each, all in another voice, vocal tract and speed): feedback on a correct learner 2.5%; a melody turned round found on the right syllable 90%; a wrong vowel 100%; a syllable held too long 92.5%; camera: a wrong mouth shape found on the right syllable 100%, correct shapes passed 100%. The TRIAL design `pronunciation_feedback` tests C14 in people, with clarity rated by a listener blind to the arm.

## 11. The EEG test for claim C35

`rsso/rsso/ssep.py` analyses EEG recorded in three conditions: vibration felt, a sham (the band driven identically but on foam beside the wrist, not felt) and rest. A vibration motor's drive leaks into EEG electrically at the same frequency, so vibration against rest finds "a response" even without one. Trials start at the motor's onset; the complex Fourier coefficient at the rhythm is compared between vibration and sham with phase, so the identical pickup cancels before the size is taken; permutation tests give p values; groups pool z scores.

Results (`rsso/results/ssep.md`, 10 groups of 20 simulated people, at 12 Hz and 7.8 Hz): with pickup and no brain response, the naive test claims a response in 99.5-100% of people and the phase-aware sham test in 3.5-7% (no group); a real response is found in 96.5-99.5% of people with or without pickup. Compared by power alone, the sham test misses most real responses (28.5-47.5% found) because a response and the pickup at different phases partly cancel. A response at the rhythm would not show better focus or a theta state: the TRIAL design `rhythm_focus` tests focus.

## 12. Limits

- No new module is built; the firmware core runs the channel lines in simulation, ready for a board.
- The simulated agent's choices and the person's signals are modelled, with known answers; real error-related potentials are noisy and slow to detect.
- Pronunciation is tested on synthetic vowel strings: real speech has consonants, noise and coarticulation, which will lower the numbers. The camera part could not be run here (no network in the build environment) and is marked built, untested.
- The EEG test uses simulated EEG; real recordings add movement, muscle and line noise.
- Claims C14, C35 and C72 have tests built and no result in people; C56, C60, C67 and C71 are tracked against public evidence, kept current; all stay on record.
