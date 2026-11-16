# LOW_MOOD — everyday low energy and clinical depression, kept apart

Status: registered 2026-11-16, before code (1ec57e4); code 5878bc5; results in §4. Owner's decision: keep the node studio's "low energy or mood" structured,
with two safeguards.

## 1. Rule

- **Low energy or mood** (the planner concern `depression`, labelled by domain: low drive, low motivation, low affect,
  low energy) stays **structured** (CONTAIN §10.2 lists everyday low energy as self-guided or structured).
- **Depression (diagnosed or under treatment)** is a separate choice, shown **only with the clinical vocabulary**
  (Clinical, or Research with the clinical module on). A plan with it is **clinician-led** (CONTAIN §10.2: depression
  work), and every one of its nodes is clinician-led in the player and on the device page. Stored as
  `plan.dx = ["depression"]` and `plan.therapist_led = true`.
- The THERA "low mood" session stays clinician-led (FIXES_R1 W-9).

## 2. Escalation

The self-check (Safety page) is kept in `rsos.selfchecks` (`[{at, intensity, sleep_h}]`, last 60). A single check with
intensity 7 or more already moves the session to Stabilisation (unchanged). New: when the active plan has the low
energy or mood concern and **self-checks with intensity 7 or more fall on 3 or more different days within the last 7
days** (amended by spec/FIXES_R4.md; previously 3 checks, which could be seconds apart), the page
says the ratings have stayed high on several days and recommends involving a practitioner, and the plan records
`practitioner_recommended` with the time. No crisis wording; no new block (Stabilisation already applies).

## 3. Acceptance

- L1 The diagnosed-depression choice is visible only with the clinical vocabulary; the six other domains show only the
  everyday option.
- L2 A diagnosed-depression plan is held without the clinician present, a recorded screening and a PIN, and saved with
  them; its nodes are clinician-led in the player (held without a clinician) and on the device page.
- L3 An everyday low-mood plan stays structured: saved without a clinician in Personal.
- L4 Escalation: with a low-mood plan, 3 high self-checks in 7 days show the recommendation and record it; 2 do not;
  without the concern, none do.
- L5 All suites and browser checks pass; no threshold changes.

## 4. Results (record)

- L1: the diagnosed choice is shown in Clinical only (hidden in Personal, Performance, Workplace).
- L2: held without a clinician; saved with the clinician present, a recorded screening and a PIN (`plan.dx` =
  `["depression"]`); its node is clinician-led in the player and held without a clinician.
- L3: an everyday low-mood plan is saved in Personal without a clinician and is not clinician-led.
- L4: 2 high checks: no recommendation; 3: the recommendation is shown and recorded; without the concern, none.
- L5: all suites and seven browser checks pass; no threshold changed.
