# MACHINES: more channels, and one profile format for people and agents

Status: built and tested in simulation; effect unproven in people. Implementation: `rsso/rsso/machines.py` and `docs/js/machines.js` (identical, tested), pages `docs/device.html#channels` and `docs/agents.html`. Simulation results: [`rsso/results/machines.md`](../rsso/results/machines.md). Protocol kit: [`kits/MACHINES_PROTOCOL_KIT.md`](kits/MACHINES_PROTOCOL_KIT.md). Roadmap items 9, 10, 15, 19, 29, 36, 38, 42, 43 and 44; claims C14, C35, C56, C60, C67, C70, C71 and C72 (only C70 has a test built; the others stay recorded as claims to test).

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
| Wrist cooling and warming | thermal | draft protocol |
| Motors on several body sites | haptic | draft protocol |
| Smart glasses | display, sound | draft protocol |
| Sleep or EEG headband | EEG, sound | draft protocol (see NIGHT) |
| Implanted device | none | specification only |

The implant class is listed so the layer's boundary is explicit: RSOS programs, anchors and profiles sit above any hardware; an implant would need its own clinical and regulatory pathway, and nothing here drives one. The claims about implants (C56, C60, C67) are kept as claims and tracked against public data; none is tested here.

## 3. RDP/1.1 draft channel lines

Each is one ASCII line, at most 96 bytes, checked by `check()` before it may play:

```
T  <t_ms> <dur_ms> <delta_c>                                   temperature change
D  <t_ms> <dur_ms> <image_id>                                  an image on a display
HF <t_ms> <on_ms> <off_ms> <count> <amp> <carrier_hz> <mod_hz> <site>   vibration with carrier, rhythm and body site
```

Envelope (`ENVELOPE_X`): temperature change at most 4 °C either way, at most 2 minutes, at most 4 a run; an image at most 10 s, and at most 0.2 brightness at night; vibration strength at most 0.6; carrier 20-300 Hz; rhythm 1-40 Hz; at most three body sites at once. Sites: left wrist, right wrist, upper arm, chest, upper back, ankle. CONTAIN's rules hold unchanged: nothing on these channels starts a program the person did not start.

## 4. Channels

- **Posture (item 9).** Forward tilt from the gravity vector of a phone worn or held upright. A slouch is above 25 degrees for 5 seconds; it ends below 15 degrees (hysteresis, so it cannot flicker). Each slouch is cued once ("sit tall"); the live page vibrates at most every 20 seconds.
- **Temperature (item 9).** Specification and command check only; no thermal module is built.
- **Display (item 15).** A lock-screen image with a profile's symbol and phrase, generated on the page. AR glasses use the `D` line; not built.
- **Several body sites (item 38).** `spread(code, sites)` puts each group of a code on the next site, so a two-part code is felt in two places.
- **Carrier and rhythm (item 29).** The `HF` line carries both; the page plays them as sound. Claim C35 (that a felt rhythm changes the EEG at that frequency) is untested and nothing relies on it.
- **Pronunciation from the camera (item 10).** Specified, not built: face and lip landmarks compared with a native speaker's template, with feedback on the largest difference. Moving the person's muscles to match is out of scope. Claim C14 is untested.

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

## 9. Simulation results

From [`rsso/results/machines.md`](../rsso/results/machines.md), 50 runs per row:

- Consistency (C70): at choice noise 0.1, a plain agent chose the same option all five times in 29.8% of scenarios and broke a value in 64% of choices; the gated agent: 38.8% and 0%.
- Error signal: detected 80% of the time, disliked actions fell from 13.4% in the first third to 0% in the last, with 7.3 fine actions asked about of about 30.
- Posture: 100% of slouches cued, no false cues, 6.2 s after the slouch began.
- Glyph decoding: about 98% correct at 40 ms of timing jitter, about 80% at 70 ms.

The value check removes value-breaking choices by construction; what it shows is the size of the gap and the cost in asking. It only knows what its values name. Whether people trust or prefer such agents (C72) is untested.

## 10. Limits

- No new hardware is built; the draft lines are a specification for builders.
- The simulated agent's choices and the person's signals are modelled, with known answers; real error-related potentials are noisy and slow to detect.
- Claims C14, C35, C56, C60, C67, C71 and C72 stay recorded and untested.
