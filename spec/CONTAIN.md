# CONTAIN — the safety layer

Status: built and tested. `rsso/rsso/contain.py` and `docs/js/contain.js` give identical results (tested). It is
used by the Python runtime (`play(..., contain=state)`), the player, the heart-rate offers, the node studio and the
safety page (`docs/safety.html`). The conformance suite checks it (C14, C15: 15/15 on the virtual rig and on the
firmware core).

## 1. Role, as recovered from the archive

The archive (`CONTAIN_Historical_Reconstruction.txt`) describes CONTAIN as follows:

- **Names:** "drift-lock propagation engine" and "ethical drift and propagation control".
- **Purpose:** governance across modules.
- **Outputs:** allow, block, quarantine, rollback and drift-lock decisions.
- **Operators:** containment, propagation stop, rollback, quarantine and guard insertion.
- **Protocols:** human in the loop, reversibility and a device safety envelope.
- **Gap:** the policy architecture is specified, but no standalone executable policy engine survives.

This document specifies that engine, and the code builds it.

| Archive | Built as |
|---|---|
| Device safety envelope | `ENVELOPE`, `check_envelope(timeline)` |
| Drift lock | `drift(runs, protocol)` and the quarantine in `review` |
| Containment and propagation stop | `decide(action, state, timeline, now)`: one gate every module asks |
| Quarantine | `review(state, runs, adverse, screens, now)` pauses a program or node |
| Rollback | `rollback(history)`: the previous approved node plan |
| Human in the loop and reversibility | `release(state, protocol, by, now)`: the person restores, or the therapist when harm was involved; nothing starts by itself |
| (LAW, ETH, MOR gates) | `escalation(...)`: practice pauses and the person is pointed to a therapist or crisis help |

## 2. The device safety envelope

No program can exceed these limits, whoever wrote it. A program may set stricter limits for itself, never looser
ones.

| Rule | Limit |
|---|---|
| Vibration strength (`haptic_amp_max`) | 0.6 of the motor |
| One pulse | 1 s |
| One pattern (pulses and gaps) | 6 s |
| All vibration in one run | 20 s |
| Tone pitch | 60–2000 Hz |
| One tone / all tones in a run | 10 s / 60 s |
| Scent bursts | 3 a run, 20 s apart |
| Taste cues | 2 a run |
| Run length | 15 minutes |
| Program SAFETY line | at most 6 an hour, 20 a day, at least 90 s apart |

All 13 built-in programs are inside the envelope (tested). A program outside it does not start (C14). The
envelope adds to the existing safety mechanisms and does not replace them: the RSX compile-time haptic limit,
`SafetyGovernor` (opt-in, refractory period, hourly and daily limits), the runtime intensity clamp, and Stop
within 100 ms on the device.

## 3. Drift: when a program or node stops helping

`drift(runs, protocol, since)` uses a program's runs. After a restore, only runs after the restore count.

| Signal | Rule | Effect |
|---|---|---|
| Worse after | Mean change in distress (after − before) ≥ +0.5 over the last 4–5 rated runs | Drift |
| Agency falls | Mean change in agency ≤ −1 over the last 4–5 runs | Drift |
| Rising distress | Mean distress after the last 5 rated runs ≥ the 5 before + 1.5 | Watch |
| Stopped often | Stopped 4 of the last 6 runs | Watch |

The status is `drift` with "worse after" or "agency falls", or with any two signals. It is `watch` with one
other signal, and `ok` otherwise. `review` pauses (quarantines) a program in `drift`. It also pauses at once any
program that a moderate or serious adverse event is possibly or likely related to; that pause needs the therapist
to restore it.

## 4. Escalation: when practice needs a therapist

`escalation(runs, adverse, screens, now)` is active after any of the following:

- a serious adverse event in the last 30 days;
- two or more moderate adverse events possibly or likely related to practice in 14 days;
- the screening question answered "yes" in the last 7 days;
- distress at 8 or more after 3 of the last 5 rated runs within a week.

While it is active:

- device offers stop;
- therapist-led work needs a therapist present;
- a new node plan needs a therapist present;
- the player and the safety page point the person to their therapist, and to emergency services or a crisis line when at risk.

Self-started runs of programs that are not paused remain the person's choice.

## 5. The gate

`decide(action, state, timeline, now)` returns `{decision: allow | block, reasons[]}`. An action is
`{kind: run | offer | cue | plan, protocol, trigger, therapist_led, therapist_present}`. Its checks are, in order:

1. the envelope (when a timeline is given);
2. the quarantine;
3. escalation.

Every reason is a sentence the person can read. The player and the node studio log every decision with its
time, action and reasons (in this browser, the last 200), and the safety page shows them. The Python runtime
refuses what CONTAIN blocks and reports the reasons in its trace.

## 6. Restore and rollback

`release(state, protocol, by, now)` restores a paused program. The person can restore it, except after an adverse
event or while escalation is active; then the therapist must ("needs the therapist"). After a restore, the
earlier evidence no longer counts, but new evidence can pause the program again.

`rollback(history)` returns the previous approved node plan. The node studio keeps the last six approved
versions, and the safety page can restore the previous one.

## 7. Data

All CONTAIN state stays in the browser:

- `rsos.contain`: quarantine, restores and escalation;
- `rsos.contain.log`: the decisions;
- `rsos.adverse`: reported events, from the player's "Something felt wrong" or the safety page;
- `rsos.screens`: screening answers from the node studio;
- `rsos.plan.history`: approved node plans.

Reported events are included in a research contribution only with the `safety` scope
(spec/DATA_CONTRIBUTION.md).

## 8. Next

- Pauses learned from pooled contributions: thresholds fitted on real drift and adverse-event data.
- Signals from EEG and heart rate during runs (a run that raises arousal instead of lowering it).
- The envelope enforced in the firmware itself, in addition to the host.

## Autonomy gate

What a device may do on its own, one anchor at a time, is decided by the autonomy gate: [GATE.md](GATE.md).
