# THERA — therapist mode and session protocols

Status: built and tested. `rsso/rsso/thera.py` and `docs/js/thera.js` give identical results (tested). The
protocols are data: `docs/data/thera.json`, written by `python -m rsso.thera`. The therapist mode is
`docs/therapist.html`.

RSOS supports the therapist's clinical judgement. It does not diagnose or treat, and no clinical efficacy is
claimed. The protocols are designed for ethics-approved study.

## 1. Role, as recovered from the archive

The archive (`THERA_Historical_Reconstruction.txt`) names THERA the "Therapy Protocol Deployment Engine": the
therapeutic branch of RSOS for identity, state and trauma-related protocols. It records these operators:
IdentityRebuild, BreathOverride, EmotionalLock, VIB-ANCHOR (300 ms on and off, 6 times) and FP-ANCHOR (150 ms on
and off, 8 times). It also records a safety envelope, a human in the loop, and closed-loop EEG and gaze triggers.
The protocol design survives; no validated clinical algorithm does. Here THERA is built as structured, measured
sessions. Each step carries the archive operator it serves.

| Operator | Session step |
|---|---|
| EthicsContain | Check-in, screening, close; every session start is checked by CONTAIN |
| BreathOverride | Paced breathing (the `paced_breathing` program) |
| IdentityRebuild | Building the node (senses, frame, glyph, code); observing a memory from the observer position |
| EmotionalLock | Anchoring the node at the peak of the state; rehearsing a trigger |
| VIB-ANCHOR | The node's vibration code at the peak; practice between sessions |
| FP-ANCHOR | Future pacing in the node's contexts |

## 2. Protocols

| Protocol | For | Steps | Distress ceiling | Notes |
|---|---|---|---|---|
| `stress` | stress, chronic stress, anxiety | check-in, breathing, build, anchor ×3, rehearse a trigger (up to 5 of 10) ×2, future pacing, practice, close | 9 | |
| `boundaries` | confidence | check-in, breathing, build, anchor, rehearse saying no aloud ×2, future pacing, practice, close | 9 | |
| `habits` | habits, focus | check-in, build, anchor, interrupt the loop (trigger → node → chosen action) ×3, future pacing, practice, close | 9 | |
| `low_mood` | depression | check-in, screening, breathing, build, anchor, plan one small action, practice, close | 9 | Screening first |
| `trauma_observer` | PTSD | check-in, screening, breathing, build the observer node, anchor it, observe the memory ×2, return to the able state, practice, close | 8 | Therapist-led; screening first; the memory is observed, never relived |

Every step gives three things:

- **Say:** the script for the client, filled with the client's own node, frame, code, contexts, trigger and dose.
- **Do:** the therapist's instruction.
- **Measure:** distress (0–10), agency (0–10), how believable the frame is, the screening answer, unpleasant events,
  CGI-S, CGI-I and engagement.

Steps that run a node or program link to the player with that program. Their runs are recorded there and counted
in the session.

## 3. Stop rules

`check(session)` gives the following:

| Situation | Level | What to do |
|---|---|---|
| Screening answered yes | stop | Stop the session work and follow the crisis procedure; no device practice. CONTAIN escalates for 7 days. |
| Distress at or above the protocol's ceiling (8 for trauma work, 9 otherwise) | return | Stop the current step and return to breathing and grounding; continue only below the ceiling − 2. |
| A moderate or serious unpleasant event | stop | Recorded; CONTAIN pauses the program it is linked to until the therapist restores it. |

## 4. Summary and the session record

`summary(session, runs, started, ended)` gives:

- the minutes and the steps done;
- fidelity: the required steps done, out of 10;
- distress at the start, at the end and at its peak, and its change;
- the change in agency;
- the runs recorded in the player during the session, and the nodes used;
- unpleasant events and any stop rules that applied;
- the session record for research, `{ts, minutes, nodes_used, fidelity, engagement, cgi_s, cgi_i, therapist_led}`.

The record can be added to the research contribution's clinician sessions (spec/DATA_CONTRIBUTION.md); the
client's consent is confirmed there. It can also be downloaded with the client code (a pseudonym), the steps and
every measurement.

`homework(plan, session)` writes the practice plan between sessions:

- each associated node with its dose and vibration code;
- observer nodes only as agreed in sessions;
- starting the node when the trigger happens;
- the weekly automaticity check;
- the "Something felt wrong" button.

## 5. Next

- Starts triggered by EEG and gaze (the archive's closed loop), through AUG and CONTAIN.
- Protocol variants fitted from pooled session records: which steps and doses go with the largest drop in distress, per concern.
- A client view of the session plan on the client's own device.
