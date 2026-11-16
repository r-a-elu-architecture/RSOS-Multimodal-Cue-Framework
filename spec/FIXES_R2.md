# FIXES_R2 — fixes from the repeat independent review

Status: registered 2026-11-16, before code. Review: branch `review/r2`, commit 557c3fa (reviewed dev at 6de0315).
This registration commit also amends spec/WATCHDOG.md §2 and W3 (finding 5).

## 1. Process rule, clarified

Registered content (design, rules, acceptance criteria) changes only in a registration commit, before its code.
Status lines and results sections are records: they are written in a separate commit after the code ("record results"),
never in the code commit. Commits 714d7ca and 6de0315 broke the earlier wording of this rule (status and results edits
in code commits; nothing was loosened); recorded here.

## 2. Fixes

| ID | Finding | Fix | Test |
|---|---|---|---|
| R2-1 | Blocker: Resume saves any typed PIN when none exists | Resume never sets a PIN. A PIN can be set only while the session is not in the clinician-led protocol (on the Safety page, by the practitioner, logged). Every screening question (node studio, player, therapist start panel) is shown only when a clinician PIN exists on the device; otherwise it says the responsible clinician sets one on the Safety page first, and clinician-led work stays held. Recording a clinical result still needs the PIN (set before the result, so before the protocol starts). Five wrong PINs lock the PIN for 15 minutes. A state entered before any PIN existed (older data) can be left only after the practitioner records a clinical result, which sets the PIN, and then resumes with it; this is logged. A static site cannot authenticate; recorded. | Browser: the reviewer's scenario (screening yes, then Resume with any PIN) stays in the clinician-led protocol in Performance, Personal and Clinical. |
| R2-2 | Blocker: guard.js drops `memory_work_allowed` | guard.js passes every context key the Watchdog reads (`memory_work_allowed` included); a test compares guard.js's keys with the Watchdog's. | Browser: Workplace, difficult-memories concern ticked (as LINX does), plan save is held and logged "hold plan [gi]". |
| R2-3 | A held automatic anchor is still offered and played | Every anchor offer asks the Watchdog (auto or not). Hold: no offer at all. Ask: offer only. | Browser: in Stabilisation no anchor offer appears. |
| R2-4 | Plan-membership check cannot trigger in the player | Recorded as by design: in the player every offer is the person's own selection or a plan node, so the rule cannot hold there; it applies to agents and devices proposing other programs. HANDOFF and FIXES_R1 W-6 wording corrected. | — |
| R2-5 | WATCHDOG §2 and W3 contradict the code | Amended in this registration commit. | — |
| R2-6 | Trial sessions feed PEAK without a code played | `evidence()` gives a probe (anchor_vs_sham) or a use (cue_vs_none cue arm) only when the session records the code played (`detail`); auto_vs_manual unchanged (the person fires the anchor either way). Python and JS. | Unit (both languages) and browser: a session saved without pressing play adds no probe. |
| R2-7 | T5 tested only by text search | A test computes MEMSTACK and CM1 on a run log before and after the whole trial flow (record, evidence, anchor feeding, contribution build) and requires identical results and an unchanged run log. | Unit. |
| R2-8 | Notes | Sham-code seeds normalised the same way in both languages; the `trials` contribution scope is off by default (opt-in); the player saves a voice as chosen only when the person changes it; the anchors page guards a missing voice module; the console-error filter in the profiles browser check ignores only blocked network requests, not 404s. Registered formats: `rsos.clinical.log` may hold `{at, by, event: "pin_set"}`; `rsos.clinical` may hold `pin_fail`, `pin_lock_until`; `rsos.settings.voice_v` = 2 marks a voice the person chose. Recorded limits: heart rate and HRV from one strap count as two distinct signals but are not fully independent; a caller-supplied category is trusted only from agents; SSIT programs run in the player are practice and enter the run log as any program does. | Unit / browser where testable. |

## 3. Acceptance

- Q1 Each test above fails on 6de0315 and passes after the fix (the R2-1 and R2-2 browser scenarios included).
- Q2 All suites and the browser checks pass; Python and JavaScript identical for changed functions.
- Q3 No threshold changes.
