# FIXES_R1 — fixes from the first independent review

Status: registered 2026-11-16, before code. Review: branch `review/interim`, commit 2b2cc3c, `HANDOFF_DEV.md` §5
(reviewed dev at fcc1b36). Every fix below gets a test that reproduces the reviewer's scenario; the test must fail on
the reviewed code and pass after the fix.

## 1. Withdrawn, corrected and recorded

- **Withdrawn:** spec/WATCHDOG.md §6, the interpretation that a therapist session's own screening step counts as a
  recorded screening. It made the screening always true, and it was added in a code commit after registration.
  Replaced by fix W-3 below.
- **Recorded late edits:** PROFILES §4 (the line on "distressing") and WATCHDOG §6 were edited in code commits
  (4358b02, fcc1b36) after registration. From now on a registered spec changes only in a registration commit.
- **Recorded deploy:** the S1 code (6394a70) was on `main` and the live site for about ten minutes on 16 November
  (00:13–00:23) before the revert 059a58f. `main` has matched the backup since.
- **Corrections:** CONTAIN §9 A1 names `event_from_check` (was `event_from_checkin`); HANDOFF's verification list
  includes the Watchdog and trial-loop tests.

## 2. Fixes

| ID | Finding | Fix |
|---|---|---|
| P-1 | "therapist-led" translated to coach-led, teacher-led, … (blocker) | In any text that names therapist-led or clinician-led work, "therapist" becomes "clinician" in every non-clinical profile; "therapist-led" becomes "clinician-led". No translated text may contain coach-, teacher-, facilitator-, investigator- or practitioner-led. |
| W-1 | Audit log fails after 502 decisions (blocker) | A record's number is the previous record's number + 1, not the log length; trimming keeps the chain valid. |
| W-2 | Research: an investigator checkbox satisfies the clinician rule (blocker) | `max_level(profile, clinical_on)`: Research allows clinician-led work only with the clinical module on (a study clinician); otherwise structured. Pages use it. |
| S-1 | Anyone can resume from the clinician-led protocol with any name | Enabling the clinical module sets a clinician PIN (stored only as a salted SHA-256 hash). Resuming from the clinician-led protocol needs that PIN. With no PIN set, the page says the responsible clinician must enable the module and set one. This is a local barrier, not authentication; a static site cannot verify identity. |
| S-2 | The clinical screening question appears in every domain; "yes" moves anyone into the clinician-led protocol | The screening question (node studio, player cues, therapist sessions) is shown only with the clinical vocabulary; clinician-led work is held outside it anyway (Watchdog). |
| S-3 | `tier012_breath_anchor` listed as regulating without registration | Removed from the regulating list (Python and JS); the list is again exactly CONTAIN §9.4's. |
| S-4 | Session-state decisions trust a caller-supplied category or an editable protocol name | (a) A caller-supplied category is ignored for person actions (`source` not `agent`); RSX-V agents keep passing theirs. (b) An action carries `edited: true` when the program source differs from the built-in file; an edited program, or any clinician-led action, is never regulating, whatever its name. The player sets `edited`. |
| S-5 | The not-a-medical-device line is on 4 of 24 pages | Every page carries it in its footer; a test checks all pages. |
| S-6 | A high self-check enters Stabilisation but the text says "suggested" | The message says it entered Stabilisation. |
| S-7 | The wording test scans only static HTML | The browser check also scans rendered text of every page, in every profile, for crisis and helpline wording. |
| S-8 | New storage keys and format changes not registered | Registered here: `rsos.clinical` `{on, pin_hash, pin_salt}`; `rsos.clinical.log` (practitioner name, instrument, result, flags, kept on the device only, never in contributions); `rsos.contain.log` decisions are allow / ask / hold since Step 2; new `rsos.screens` records carry `q: 2` (the clinical-screening question), older ones have none. |
| S-9 | CI does not run on `dev` | The CI workflow also runs on pushes to `dev`. |
| P-2 | Workplace: difficult-memory work still reachable | The Watchdog holds an action marked `memory_work` when the page passes `memory_work_allowed: false`; Workplace passes it. Pages mark memory work (node plans with the difficult-memories concern or observer memory nodes, the observer THERA session). The observer session, contribution and night mentions are hidden in Workplace. |
| P-3 | Clinical-word list misses some wording | Added: `clinical screening`, `clinical judgement`, `diagnos*`, `C-SSRS`, `PHQ-9`, `GAD-7`, `PCL-5`. The texts are shown only with the clinical vocabulary or reworded. |
| P-4 | Ungrammatical translations | Rules for "distress (SUD)", "therapy session(s)", "anxiety/panic disorder(s)", and "symptoms and what they feel like" → "{changes} (describe how it feels)". Test: no translated corpus text has a doubled word, "a" before a vowel or "an" before a consonant in a substituted term, or a duplicated term. |
| P-5 | Switching the Domain menu to Clinical lifts the limits | Switching into Clinical asks for confirmation ("for clinicians and people working with one"); clinician-led work still needs the clinician rule and the PIN to resume. Recorded as a limit of a static site. |
| P-6 | Profile browser check ignores console errors | It records console errors and fails on them. |
| W-3 | Screening interpretation (withdrawn) | A clinician-led THERA session starts only with a screening answer "no" given on the start panel. Inside the session, steps after the screening step stay locked until it is recorded "no"; a "yes" closes the session view. |
| W-4 | Clinician-led level not carried into runs | Runs of a clinician-led plan's observer nodes carry `therapist_led` and `memory_work`. The player shows, only for clinician-led programs in a domain that allows them, "The responsible clinician is present" and the screening question. |
| W-5 | Automatic anchor firing bypasses the Watchdog's firing rules | The firing check sends `auto`, the signals used and the consents; with fewer than two independent signals or no consent it becomes an offer. |
| W-6 | `plan_protocols` and `programmed` never passed | Device offers pass the plan's programs (when a plan exists) plus the program the person selected; programmed cues pass `programmed: true`. |
| W-7 | Regulating exemption by name only | As S-4(b). |
| W-8 | Unknown `max_level`: JS allows, Python raises | Missing → no domain limit (callers outside pages); unknown → `structured`, in both languages. |
| W-9 | Depression work treated as structured | The THERA low-mood session is clinician-led (CONTAIN §10.2: depression work). The node studio's "low energy or mood" concern stays structured (§10.2 lists low energy as everyday); flagged to the owner. |
| W-10 | Python and JS differ on empty states and consents without a start | A saved state without `mode` counts as none; a consent without a start time counts as given at 0; both languages. |
| W-11 | Signals not checked for independence | Two or more distinct signals. |
| W-12 | A Spine wording flag holds a regulating program | Kept, and WATCHDOG §2 amended: dangerous wording makes a program not a safe regulating program. Spine flags apply to every action. |
| W-13 | Tier 414/420/439/440 runs held even in Clinical with a clinician | As W-4: the player reports the clinician and the screening. |

## 3. Acceptance

- R1 Every fix has a test reproducing the reviewer's scenario; all pass. Existing suites pass.
- R2 Python and JavaScript identical for every changed function (safety, watchdog, profiles).
- R3 Browser checks (profiles, Watchdog, trial loop) pass with no page or console errors.
- R4 No threshold changes; the regulating list returns to CONTAIN §9.4's.
- R5 The independent review is repeated on the fixed code, including Step 3.
