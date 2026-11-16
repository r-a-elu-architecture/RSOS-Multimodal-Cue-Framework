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
- `rsos.safety`: the safety mode in force, its last check-in and its history (§9);
- `rsos.plan.history`: approved node plans.

Reported events are included in a research contribution only with the `safety` scope
(spec/DATA_CONTRIBUTION.md).

## 8. Next

- Pauses learned from pooled contributions: thresholds fitted on real drift and adverse-event data.
- Signals from EEG and heart rate during runs (a run that raises arousal instead of lowering it).
- The envelope enforced in the firmware itself, in addition to the host.

## 9. Safety modes on the person side (S1, design fixed before code, 16 November 2026)

**Why.** The safety layer specified and tested in `rsxv/AGENTS.md` §3.1 (modes, screens, the past-crisis check-in
and the §11.14 rule fix) ran only in the agent World. The player, node studio and therapist mode used one screening
question and CONTAIN escalation. S1 makes one safety layer for both: the person-facing pages run the same rules as
the agents, and the stricter rule always wins.

**What is built (fixed now).**

1. `rsso/rsso/safety.py` and `docs/js/safety.js`, identical results: `screen(event)`, the fixed responses with a
   readable message for each screen, the mode machine as plain data (`new_state`, `observe`, `enter_stabilise`,
   `exit`), `MODE_ALLOWED`, `category(action)`, `may_start_deep_session`, `adjusted_effect`, the structured
   check-in (`CHECKIN` questions → `event_from_checkin(answers)`), and `spine_flags(text)`.
   `rsxv/rsxv/safety.py` becomes a re-export of `rsso.safety`, and `rsxv.agents.MODE_ALLOWED` is the same object:
   one rule set.
2. The rules are those of §3.1 exactly; no threshold or rule changes. Escalation is automatic and never
   downgrades on a lower screen; leaving CRISIS needs a clinician (or the owner); leaving STABILISE or
   PRACTICAL_CRISIS is the person's choice; `history_check_in` changes no mode.
3. **The structured check-in** replaces free-text reading in the browser (a keyword reader caught 13% in §11.12;
   the meaning-based reader needs a model). Questions, answered yes / no / prefer not to say: thoughts of harming
   yourself or not wanting to live right now (→ `self_harm_signal`); putting things in order or making arrangements
   for after you are gone (→ `arrangements_for_after`); alcohol or other drugs today while taking a prescribed
   sedative (→ `substances` + `sedative_prescribed`); job loss, losing your home or no income now (→
   `practical_crisis` fields); such thoughts in the past but not now (→ `history_reference`); plus distress 0–10
   and hours slept. The existing screening question answered yes counts as `self_harm_signal`.
4. **CONTAIN asks the mode.** `decide(action, state, timeline, now, safety=None)`: when a safety state is given and
   the action's category (`category(action)`) is not allowed in the mode in force, the action is blocked with the
   mode's reason, after the envelope, quarantine and escalation checks. Categories: a therapist-led or deep tier →
   `deep_processing`; paced breathing, interrupt-only and stillness programs → `regulating_cue`; other runs,
   cues and offers → `override_cue`; a new node plan → `module_work`. Without a safety state, `decide` behaves
   exactly as before.
5. **Spine flags in the browser.** `spine_flags(text)` finds, by fixed word lists, release through temperature
   extremes, pain, extreme breath-holding or sleep deprivation (Jin) and population ranks about the person
   (Makoto). LINX `route` rejects a proposed text field that raises a flag; the node studio shows the flag on a
   frame or rule. Warm water, ordinary breathing and rest raise nothing.
6. **Pages.** Safety page: the check-in, the mode in force and why, its history, and the exits each mode allows.
   Player, node studio and therapist mode: the mode is shown and passed to CONTAIN; a yes to the screening question
   enters CRISIS. Crisis help is pointed to local emergency services and an international helpline directory; no
   phone numbers are hard-coded.

**Acceptance (all must hold before the push to `main`).**

- A1 Python and JavaScript give identical results for `screen`, `observe` sequences, `exit`, `category`,
  `event_from_checkin`, `spine_flags`, `may_start_deep_session` and `decide` with a safety state, on a fixed set of
  cases covering every screen and every mode.
- A2 `rsxv` uses `rsso.safety`: its 130 tests pass unchanged.
- A3 Every existing test in `rsx`, `rsso` and `toolkit` passes; `decide` without a safety state is unchanged.
- A4 Each mode blocks exactly the categories §3.1 forbids, and CRISIS cannot be left by the person alone.
- A5 `spine_flags` flags each listed mechanism and rank wording, and none of 20 ordinary frames and rules (warm
  bath, golden light, calm breathing, sleep well…).
- A6 `scripts/check_all.sh` passes; page build numbers and the offline cache are raised.

This is engineering, not a test of effect: it changes no claim and no registered result.

## Autonomy gate

What a device may do on its own, one anchor at a time, is decided by the autonomy gate: [GATE.md](GATE.md).
