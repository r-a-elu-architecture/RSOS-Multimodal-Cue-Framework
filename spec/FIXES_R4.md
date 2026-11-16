# FIXES_R4 — fixes from the fourth independent review

Status: registered 2026-11-16, before code. Review: branch `review/r4`, commit 48d3aff (reviewed dev at 451a4df).
This registration commit also amends CONTAIN A4 (advisory wording) and LOW_MOOD §2 (3 different days).
Two design choices of FIXES_R3 were wrong and are replaced: the gate fell back to the page's own session when a
program was held, and text the person can edit carried a program's level.

## 1. Output gate (`docs/js/outlet.js`)

| ID | Finding | Fix |
|---|---|---|
| G1 | A held session falls back to the page's default session | An explicit session (opened or adopted for a run, offer, code or session) that becomes hold or expires stays held: no output until the page closes it or opens a new one. The page's declared session is used only when there is no explicit session; it is re-checked at every output. |
| G2 | The domain is read once at load | `window.RSOSDomain` is recomputed when `rsos.profile` or `rsos.clinical` change in any tab (storage events); the gate re-checks then. |
| G3 | Output already started keeps going | While a session is live the gate re-checks every second and on storage changes. When the decision turns to hold it stops everything: vibration (vibrate(0)), speech (cancel), running sound sources and unmuted media (stop, pause), all audio to the speakers (gain 0), and it dispatches `rsos-outlet-hold`; the player ends the run ("stopped by the Watchdog") and the device page sends STOP to the band. |
| G4 | Audio paths that bypass `start()` | As registered in FIXES_R3: every connection to a context's speakers goes through a per-context gate gain, 1 only while output is permitted. Autoplay and unmuting are caught (play and volumechange events): an unmuted element plays only while permitted. |
| G5 | Device- and agent-triggered outputs run as self-triggered | Posture vibration (device page) and the heart-rate offer's vibration (player) open sessions with `trigger: device`; agent status codes (agents page) with `trigger: agent`. They need the Watchdog's consent and two-signal rules or the person's confirmation; otherwise they stay silent (the visual prompt remains). |
| G6 | Fails open if outlet.js itself is missing | UGCL.feel, the voice module and the wristband gate refuse in a browser without the gate. |
| G7 | A held node's code typed into the code field is sent | A typed code equal to a plan node's code carries that node's level. |
| G9 | `"STOP\nSTART"` passes the wristband check | Any line of a sent text that starts with START is gated. |

## 2. Level from where a program came from

- The player keeps the **origin** of the loaded program (built-in, plan node, cue, therapist program) with the
  origin's level; edits never lower it (union of origin and content). Therapist programs store their level in their
  record; cues by their consent record; plan nodes by the plan.
- **Same text, same level:** a source whose normalised text (comments and spacing removed) equals a saved plan node's,
  cue's or therapist program's carries that one's level, whichever slot it is loaded in (so the built-in observer
  node identical to a held plan node is held too, while that plan is saved).
- Spine wording: every quoted string in a program is scanned (statements joined with `;`, FUTURES, any position).
- Source text is normalised before level patterns (line terminators to `\n`; ASCII-only patterns), identical in Python
  and JavaScript.
- The therapist page's re-living program is memory work: hidden in Workplace and memory work in the player.

## 3. Other fixes

| ID | Fix |
|---|---|
| LM1 | A diagnosed-depression plan is not memory work (memory work = the difficult-memories concern). |
| LM2 | Covered by "same text, same level". |
| LM3 | 3 different days (amendment above); the message counts days. |
| C1 | The advisory sentence is shown with the session state in every domain; CONTAIN A4 amended. |
| C3 | The instrument placeholder is neutral. |
| R1 | The therapist page declares its own output session (copilot sounds work in the Standard state). |
| P1 | `eventFromCheck` with a non-numeric intensity and `exit` with a malformed state behave the same in both languages. |
| N1 | Night page: the nightmare control and lede sentence are memory work (hidden in Workplace). |
| R2 | Script version strings raised for changed scripts. |
| H1 | HANDOFF §2 corrected: `pages.yml` exists on `dev` and reaches `main` at a merge. HANDOFF updates go in record commits. |
| — | Recorded: LM4 (saving a new plan replaces a clinician-led one; stopping is always allowed); G8 (declared sessions have no expiry by design); G10 (board check wording); C2 (the dev site keeps separate storage). |

## 4. Acceptance

- Q1 Every review-4 scenario listed above is reproduced in a browser test (`scripts/check_fixes_r4.py`) that fails on
  451a4df and passes after the fix.
- Q2 Python and JavaScript identical for the changed engine functions (level patterns, Spine text, eventFromCheck,
  exit), including the reviewer's adversarial sources.
- Q3 All suites and browser checks pass; built-in programs keep their levels and have no Spine flags; no threshold
  changes.
