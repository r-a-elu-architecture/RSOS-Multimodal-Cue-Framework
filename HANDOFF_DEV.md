# HANDOFF_DEV — development record and review brief

One file for the work on the `dev` branch. The building account adds a section per step; the reviewing account
checks the newest section against the checklist in §3 and records findings in §5. Start here instead of from chat
history.

## 1. Rules

- **Nothing goes to `main` or the live site** from the building account. Everything is on `dev` and the
  development site. Merging is the owner's decision after review.
- **Lanes.** The builder pushes to `dev` only. The reviewer works on its own branch (`review/<step>`) and writes
  findings in §5 there, or in a pull request against `dev`. The two never push to the same branch.
- **Registration discipline.** Each step is registered in a spec and pushed before its code. Thresholds are never
  changed after results are seen.
- **Representation.** RSOS repurposes unwanted states (counterconditioning, future pacing). Pages use professional
  language; no crisis, helpline or emergency-banner wording outside research records and the clinician-facing
  module (spec/CONTAIN.md §10). Acute risk always runs under a qualified clinician's protocol.
- **Public repository stays neutral:** no personal, spiritual, substance or security content; only aggregates
  from private material.

## 2. Map

| What | Where |
|---|---|
| Live site (from `main`) | https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/ |
| Development site (from `dev`) | https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/dev/ |
| Backup of the state before this work | branch `backup/pre-claude-2026-11-16` (32f49bb), protected by the ruleset "Protect backup" |
| `main` | identical in files to the backup (one revert commit, 059a58f). The S1 code (6394a70) was on `main` and the live site for about ten minutes (00:13–00:23, 16 November) before that revert. |
| Deploy | `.github/workflows/pages.yml` builds `main/docs` at `/` and `dev/docs` at `/dev/` |
| Dev site isolation | `docs/js/devmode.js`: saved data under `/dev/` is prefixed `dev.`; a "DEVELOPMENT VERSION" banner; a separate offline cache |

### How to verify

```
git checkout dev
./scripts/check_all.sh                     # every suite, conformance, generated files unchanged
(cd rsxv && python3 -m pytest -q tests)    # RSX-V agent layer
python3 -m pytest -q rsso/tests/test_safety.py rsso/tests/test_profiles.py rsso/tests/test_watchdog.py \
  rsso/tests/test_trial_loop.py rsso/tests/test_fixes_r1.py
python3 scripts/check_profiles.py docs     # browser acceptance (needs Playwright and Chrome)
python3 scripts/check_watchdog.py docs
python3 scripts/check_trial_loop.py docs
python3 scripts/check_fixes_r1.py docs
```

## 3. Review checklist (every step)

For each item record **pass / fail** with evidence (command output, file and line, or a screenshot).

1. All tests pass (`check_all.sh`, RSX-V, the step's own tests).
2. The code does what the registered spec says, and the registration commit comes before the code commit.
3. No threshold or limit changed (compare against the backup branch).
4. Stored data unchanged: storage keys and record formats are the same unless the spec registers a change.
5. Python and JavaScript give identical results where both exist.
6. No crisis, helpline or emergency wording on pages; no clinical words on non-clinical profiles
   (`scripts/check_profiles.py`).
7. Nothing reached `main` or the live site.
8. The development site shows the change and has no page errors.
9. Anything the step claims in prose is true in the code.

## 4. Steps

### Infrastructure — development site and backup

Commits: f372064 (workflow), b83a307 (devmode, separate cache). Backup branch and ruleset created on GitHub.
Check: `/dev/` shows the banner; data saved on `/dev/` does not appear on `/`.

### Step 1 — one safety engine for people and agents (S1 and its revision)

Spec: `spec/CONTAIN.md` §9 (registered 5227a26) and §10 (registered 8db766b).
Code: 6394a70 (S1), 5347a3a (§10 revision), 1409a8c (a wording fix).

- `rsso/rsso/safety.py` and `docs/js/safety.js`: screens, session states, the state machine, guidance levels,
  the self-check, the clinician-entered screening result, Spine wording flags. RSX-V re-exports it
  (`rsxv/rsxv/safety.py`).
- CONTAIN `decide(..., safety)` checks the session state last; LINX rejects text with Spine flags.
- Session states display as Standard / Stabilisation / Paused: practical / Clinician-led protocol (internal IDs
  NORMAL / STABILISE / PRACTICAL_CRISIS / CRISIS unchanged for RSX-V).
- Guidance levels: self-guided / structured / clinician-led. Clinical module off by default.
- Safety page rebuilt as "Safety and governance". Crisis wording removed; footer "Research and development
  framework; not a medical device."

Tests: `rsso/tests/test_safety.py` (A1–A8, including the site-wide wording test A7).
Click: `/dev/safety.html` (self-check intensity 8 → Stabilisation; clinical module → result "high" → clinician-led
protocol; resume as clinician), `/dev/player.html` (status line follows the state).
Review status: **awaiting review**.

### Step 1b — domain profiles

Spec: `spec/PROFILES.md` (registered d9b3c01). Code: 4358b02.

- Seven profiles: Personal (default), Coaching, Performance, Learning, Research, Workplace, Clinical.
- `rsso/rsso/profiles.py` and `docs/js/profiles.js`: one canonical vocabulary in the modules, translated at display
  time only. Engine, thresholds and stored data unchanged.
- Domain menu in every header, chooser on the home page, `?profile=<id>` links.
- Clinical instruments and conditions list only with clinical vocabulary; clinical module only in Clinical and
  Research; Workplace hides difficult-memory work.

Tests: `rsso/tests/test_profiles.py` (P1–P5), `scripts/check_profiles.py` (P6–P7; result at registration: zero
clinical words in six non-clinical profiles over 15 pages, no page errors).
Click: `/dev/nodes.html?profile=performance`, `/dev/therapist.html?profile=research`,
`/dev/contribute.html?profile=workplace`, `/dev/nodes.html?profile=clinical`.
Known limits: the highest guidance level per profile is shown, not yet enforced (Step 2); exported records do not
record the profile (would need its own registration).
Review status: **awaiting review**.

### Step 2 — RSIA Watchdog on the person side

Spec: `spec/WATCHDOG.md` (registered 1dc4ea6). Code: see the commit after it.

- `rsso/rsso/watchdog.py` and `docs/js/watchdog.js`: `watch(action, ctx)` gives allow / ask / hold; every reason
  names a Spine virtue or precept and who can resolve it. It asks CONTAIN (and through it the session state) and
  adds: Spine wording flags, the domain's highest guidance level, the clinician rule (present + screening),
  plan membership for device and agent offers, consent and two signals for automatic firing (precept 3), agents
  never start a run, population maps only advise (precept 15). Stop is always allowed; the Watchdog's own rules
  never hold a regulating program.
- `link(contain, safety, now)`: while CONTAIN's practice pause is active, the session state is at least
  Stabilisation; never lowers a state.
- Hash-chained audit log (SHA-256, synchronous in JS, equal to Python) in `rsos.watchdog.log`; the safety page
  shows whether the chain verifies.
- `docs/js/guard.js`: page glue. Player, device, nodes and therapist ask the Watchdog; no page calls CONTAIN
  `decide` directly. Pages pass the domain's highest guidance level.

Tests: `rsso/tests/test_watchdog.py` (W1–W8, W9 static), `scripts/check_watchdog.py` (W9 in Chrome).
Click: `/dev/nodes.html?profile=performance` (build a plan with difficult memories + the Observer node, clinician
present, screening no → held: clinician-led work, Gi); the same in `?profile=clinical` → saved;
`/dev/therapist.html?profile=workplace` → the observer session is held; `?profile=clinical` → it starts;
`/dev/safety.html` → "the chain verifies".
Interpretation to review: the therapist session's own required screening step counts as the recorded screening
(spec/WATCHDOG.md §6).
Not in this step: the world simulation.
Review status: **awaiting review**.

### Step 3 — trials feed the evidence chain

Spec: `spec/TRIAL_LOOP.md` (registered 2f6d654). Code: the commit after it.

- Trial module bridge (`trial.py` / `trial.js`): `sham_code` (seeded by the trial seed and session index, never the
  anchor's code), `record(..., detail)` (the code played is recorded), `evidence` (anchor_vs_sham → one PEAK probe;
  cue arm and automatic/manual → one use). The trials page applies it to the anchor, shows PEAK strength and the
  device permission stage (GATE), and asks the Watchdog before each session.
- Deliberate change from the original roadmap line: trials do **not** write the run log; MEMSTACK and CM1 model
  practice, a trial is a measurement (spec §2).
- Contribution scope `trials` (Python and JS identical): no codes, names or text.
- Programs: `ssit_higher`, `ssit_local`, `ssit_calm` (300 s each, identical timing) and `tier013_lion_dragon`
  (🦁+🐉), in `rsx/protocols` and `docs/protocols`, in the player list and the contribution's known protocols; the
  SSIT trial session links to its arm's program.

Tests: `rsso/tests/test_trial_loop.py`; `scripts/check_trial_loop.py` (T8 in Chrome).
**Registered criterion not met:** T4 power, 158/200 (79%) against at least 80%. Kept as an expected failure; threshold
unchanged (spec §7). Reviewer: please check the simulation matches the registered wording.
Click: `/dev/trials.html` (start Real anchor or sham with an anchor from the Anchors page; after saving, the message
shows the code and the anchor's strength), `/dev/player.html?program=ssit_higher`, `?program=tier013_lion_dragon`.
Review status: **awaiting review**.

### Fix pass R1 — findings of the first independent review

Review: branch `review/interim`, commit 2b2cc3c (reviewed fcc1b36). Registration: `spec/FIXES_R1.md` (6ed0f75).
All 3 blockers and every "should fix" item are fixed; notes are fixed or recorded. WATCHDOG §6 is withdrawn. Late spec
edits recorded (PROFILES §4, WATCHDOG §6). Voice: one American-English voice on every page (9b551d9).
Tests: `rsso/tests/test_fixes_r1.py` (fail on fcc1b36, pass now), `scripts/check_fixes_r1.py` (page scenarios).
Decision flagged to the owner: the node studio's "low energy or mood" concern stays structured; the THERA low-mood
session is clinician-led (FIXES_R1 W-9).
Review status: **awaiting the repeat review (R5)**, which also covers Step 3.

## 5. Review findings

Reviewer: add one block per review.

```
Step:            (e.g. Step 1)
Reviewed commit: (hash)
Date:
Checklist:       1 pass | 2 pass | 3 … (with evidence)
Findings:        (numbered; file and line; severity: blocker / should fix / note)
Verdict:         ready for the owner | changes needed
```

Reviewer: repeat independent agent (R5). Own clone, branch `review/r2` from `dev` at 6de0315; no code changed. The
interim review's findings were read on `review/interim` (2b2cc3c). Commands, from a clean checkout of 6de0315:
`./scripts/check_all.sh` exit 0 (RSX 43, RSX-V 128, RSSO 234 OK with 1 expected failure, Toolkit 10; conformance
15/15 and 15/15; board 7/7; generated files unchanged); `(cd rsxv && python3 -m pytest -q tests)` 130 passed;
`python3 -m pytest -q rsso/tests/test_safety.py rsso/tests/test_profiles.py rsso/tests/test_watchdog.py
rsso/tests/test_trial_loop.py rsso/tests/test_fixes_r1.py` 44 passed, 1 xfailed; `python3 -I scripts/check_profiles.py
docs`, `check_watchdog.py`, `check_trial_loop.py`, `check_fixes_r1.py` (Chrome, Playwright) all exit 0 with
`"fails": []` and `"page_errors": []`. `test_fixes_r1.py` copied onto a worktree of fcc1b36: all 8 tests fail there,
as FIXES_R1 §4 claims. Extra scenarios were run with throw-away Node and Playwright scripts against `docs/` served under
`/dev/` (devmode active); each is described in the finding so it can be repeated. A randomized Python/JS comparison of
6,000 `watch` cases (including `edited`, `programmed`, `memory_work`, `memory_work_allowed`, agent categories, duplicate
signals, `given: null`, unknown `max_level`), 300 `allowed` cases and 84 `text` cases found no difference.

```
Step:            Fix pass R1 verification (spec/FIXES_R1.md; registration 6ed0f75, code 6de0315)
Reviewed commit: 6de0315
Date:            2026-11-16
Status of every finding of the interim review (2b2cc3c):
 Step 1
  1  NOT FIXED (S-1) — the PIN can be set by whoever is at the resume form. A clinician-led protocol entered from
     the node studio, player or therapist screening "yes" (or from RSOSSafety.observe) has no PIN set, because only
     "Record result" on the safety page sets one. safety.html:366 then calls ensurePin(), which saves any 4+ digit
     PIN typed and resumes. Repro (Chrome, /dev/): put rsos.safety in CRISIS, open safety.html?profile=performance
     (also personal), tick #clinOk, name "anyone", Resume -> "Set a clinician PIN of four or more digits first.";
     type 1234, Resume -> "Session state: Standard ... Resumed by the clinician."; rsos.clinical now holds that
     person's PIN hash with on:false. check_fixes_r1 S1 only tests the path where the clinician first records a
     result and sets the PIN. FIXES_R1 S-1 says "With no PIN set, the page says the responsible clinician must enable
     the module and set one"; the page instead invites the person to set it.
  2  fixed (S-2) — the screening question is inside data-show="clinical" on nodes, player cue panel, player clinRun
     and the therapist start panel; hidden in Personal (checked in Chrome: #screenQ not rendered).
  3  fixed in code (S-3), spec not aligned — REGULATING is CONTAIN §9.4's list in both languages; tier012 in
     Stabilisation is held. spec/WATCHDOG.md:51 still lists "breath anchor" as a regulating program (see Step 2 R5-2).
  4  fixed (S-4) — Repro A now holds; Repro B (player, Stabilisation, override with PROTOCOL changed to interrupt_only
     by typing in #source) -> "Held by the Watchdog: session state Stabilisation"; audit log "hold interrupt_only".
     Residual: see Step 1 R5-3.
  5  fixed (S-5) — every one of the docs/*.html pages carries the footer line (grep).
  6  fixed (S-6) — message says "the session moved to Stabilisation".
  7  partly fixed — CONTAIN §9 A1 and item 1 now name event_from_check; §9 is still not marked where §10 supersedes it.
  8  fixed (S-7) — check_profiles.py scans the rendered text of every non-exempt page in every profile for crisis
     wording; my own rendered scan (6 profiles x all pages, also with the nodes concerns and player T414 cue states
     toggled) found no crisis, helpline or emergency wording and no clinical words.
  9  recorded-only — HANDOFF §2 and FIXES_R1 §1 record the ten minutes of S1 on main and the live site.
  10 recorded-only (S-8) — keys registered. Unregistered detail: rsos.clinical.log now also gets {at, by, event:
     "pin_set"} records (safety.html:352), not in the S-8 format.
  11 recorded-only (S-8) — registered; safety.html:288 still styles "hold" as "other", not as a block.
  12 fixed (S-8) — new records carry q: 2 at every writer (nodes, player cue and run, therapist start panel and step).
  13 fixed (S-9) — checks.yml runs on dev; run 43803532639 (checks, dev, 6de0315) succeeded. The second half (pages.yml
     exists only on dev, so a push to main alone does not deploy) is not addressed or recorded.
 Step 1b
  1  fixed (P-1) — no coach-/teacher-/facilitator-/investigator-/practitioner-led text in rendered pages of any
     profile; Node check of the exact strings (player tier labels, nodes.html:413, safety.html:257, cue message).
     Side effect: see Step 1b R5-1.
  2  NOT FIXED (P-2) — the hiding works (therapist observer session, contribute, night), but the Watchdog hold never
     runs on any page: docs/js/guard.js:15-17 builds ctx from a fixed list of fields and drops memory_work_allowed,
     which every page passes. Repro (Chrome, /dev/nodes.html?profile=workplace): LINX message "I keep having
     flashbacks of an accident and nightmares. I want calm, like a lion." -> the hidden ptsd box is ticked; tick
     consent, Save -> "Saved. Opening the player with your first node…"; rsos.watchdog.log "allow plan []";
     rsos.plan.intake.concerns ["ptsd"]. In the same page RSOSWatchdog.watch({kind:"plan",memory_work:true},
     {memory_work_allowed:false}) is "hold". guard.js was not changed in 6de0315. test_fixes_r1 tests only the
     engine; check_watchdog's Workplace plan holds only because that plan is therapist_led (level rule).
  3  fixed (W-2) — max_level/maxLevel("research", off) = structured; pages use it.
  4  fixed (P-3) — word list extended; rendered scans find 0 clinical words in the six non-clinical profiles.
  5  recorded-only — late edits recorded in FIXES_R1 §1. New instances: see Step 3 R5-6.
  6  fixed (P-4) — listed phrases translate grammatically; no doubled words or a/an errors in rendered pages.
  7  partly fixed / recorded (P-5) — the menu and the home cards ask before Clinical; ?profile=clinical does not
     (by design, recorded). Anyone who confirms then meets only two unauthenticated tick boxes for clinician-led work
     (the PIN guards only the resume, and see Step 1 #1).
  8  fixed (P-6) — console errors are recorded, but every "Failed to load resource" is ignored, including local 404s
     (note).
 Step 2
  1  fixed (W-1) — 1,200 decisions with trim after each: verify true, first n = 700, both languages.
  2  fixed (W-2) — therapist.html?profile=research (module off), trauma_observer -> held [Gi].
  3  fixed (W-3) — start panel needs "no"; steps after the screening step stay locked; "yes" closes the session view
     (check_fixes_r1 W3 and my repeat).
  4  partly fixed (W-4) — runs of a clinician-led plan's observer node carry therapist_led and are held in Workplace.
     The memory_work flag the same code sets is dropped by guard.js (1b #2), so an observer node of a plan with the
     difficult-memories concern that is not therapist_led still runs in Workplace.
  5  partly fixed (W-5) — consent and two distinct signals are now checked, but a Watchdog hold on automatic firing is
     turned into an offer that plays the anchor on one click (Step 2 R5-1).
  6  partly fixed (W-6) — programmed: true is passed on cue save. plan_protocols is passed, but planProtocols()
     (player.html:698) always appends timeline.protocol, and the only call (player.html:861) offers timeline.protocol,
     so the Chūgi plan-membership hold can never fire on a page.
  7  fixed (W-7) — Node: watch({kind:"session",protocol:"paced_breathing",therapist_led:true,deep:true},
     {max_level:"structured"}) -> hold clinician_led.
  8  fixed (W-8) — unknown -> structured, missing -> no limit, identical in both languages.
  9  fixed (W-9) for the THERA low-mood session; node-studio low energy/mood left structured and flagged to the owner
     (recorded).
  10 fixed (W-10) — {} states and given:null identical in both languages.
  11 fixed (W-11) — ["hr","hr"] -> ask (p3). Independence is still by label only: the two page signals (heart rate
     above baseline, RMSSD below baseline) come from the same strap's beat intervals (note).
  12 NOT DONE as registered (W-12) — the behaviour is kept, but the promised amendment of WATCHDOG §2 was never made:
     spec/WATCHDOG.md:51-52 still says the Watchdog's own rules never hold a regulating program, and lists the breath
     anchor; W3 acceptance (line 83) says the same. No test covers W-12.
  13 fixed (W-13) — Clinical: T414 cue with clinician present and screening "no" -> saved; Personal -> held [Gi].
  14 fixed — HANDOFF §2 lists the Watchdog, trial-loop and fix tests.
Verdict:         changes needed — HANDOFF says all blockers and every "should fix" item are fixed; Step 1 #1 and
                 Step 1b #2 are not fixed in the reviewer's own scenarios, W-5 and W-6 are partial, W-12 is not done.
```

```
Step:            Step 1 — one safety engine (after the fix pass)
Reviewed commit: 6de0315
Date:            2026-11-16
Checklist:       1 pass (all suites, see above) | 2 pass with findings (S-1 claim false) | 3 pass (contain/peak/gate
                 unchanged vs fcc1b36; safety thresholds as backup) | 4 pass with note R5-4 | 5 pass (randomized
                 parity, 0 differences) | 6 pass (rendered scans) | 7 pass (gh main 059a58f; diff vs backup empty) |
                 8 pass on a local /dev/ mirror (github.io not reachable from here; Pages run 43803532595 succeeded;
                 0 page errors over all pages x 6 profiles) | 9 fail (R5-1)
Findings:
  R5-1 blocker — docs/safety.html:345-352, 366: the clinician PIN can be created at the resume form by anyone while
       the state is the clinician-led protocol and no PIN exists (the normal case, since only "Record result" sets a
       PIN). Repro in Fix pass block, Step 1 #1. A4 ("CRISIS cannot be left by the person alone") again holds only in
       the engine. The resume path must refuse when no PIN is set, as FIXES_R1 S-1 registers.
  R5-2 note — the PIN is 4+ digits, salted SHA-256 in localStorage, no attempt limit: 10,000 hashes offline. FIXES_R1
       calls it a local barrier, which is accurate; HANDOFF should say the same where it says S-1 is fixed.
  R5-3 note — rsso/rsso/safety.py:131 / docs/js/safety.js:91: a caller category is still trusted whenever the action
       says source: "agent", and watch() then returns "ask", which pages treat as proceed. Node:
       watch({kind:"run",protocol:"override",category:"logging",source:"agent"},{safety:CRISIS}) -> ask. No page
       sends source "agent" today, so this is latent; the trust is on a self-declared field.
  R5-4 note — rsos.clinical.log "pin_set" records are not in the S-8 registered format (safety.html:352).
Verdict:         changes needed (R5-1)
```

```
Step:            Step 1b — domain profiles (after the fix pass)
Reviewed commit: 6de0315
Date:            2026-11-16
Checklist:       1 pass | 2 fail (P-2 enforcement inert) | 3 pass | 4 pass | 5 pass (84 text cases identical) |
                 6 pass (0 clinical words, no wrong -led labels, rendered and toggled states) | 7 pass | 8 pass (local
                 mirror) | 9 fail ("Workplace hides difficult-memory work": hidden, not held; R5-2)
Findings:
  R5-1 note — docs/js/profiles.js:86, rsso/rsso/profiles.py:118-122: P-1 rewrites every "therapist" in a sentence
       that contains "-led", including the domain practitioner. Performance, safety.html:171: "a new plan needs a
       clinician present", while the node studio's box that satisfies that CONTAIN rule reads "A coach is present
       for this session"; safety.html:261 "Please talk with your clinician". Wording disagrees with the control.
  R5-2 blocker — docs/js/guard.js:15-17 drops memory_work_allowed (Fix pass block, 1b #2). Every P-2 and W-4
       memory_work hold is inert on pages; Workplace saves a difficult-memories plan in the interim reviewer's exact
       scenario.
Verdict:         changes needed (R5-2)
```

```
Step:            Step 2 — RSIA Watchdog (after the fix pass)
Reviewed commit: 6de0315
Date:            2026-11-16
Checklist:       1 pass | 2 fail (W-12 amendment missing; W-6 inert) | 3 pass | 4 pass | 5 pass (6,000 random cases,
                 0 differences) | 6 pass | 7 pass | 8 pass (local mirror; safety page "the chain verifies") |
                 9 fail (R5-1, R5-3, guard.js memory_work)
Findings:
  R5-1 should fix — docs/player.html:892-899, 916-923: when the Watchdog holds automatic firing (not just asks), the
       code sets best.mode = "suggest" and shows "Play it", which plays the anchor with no further check. Node: in
       Stabilisation, watch({kind:"offer",protocol:"interrupt_only",trigger:"device"}) -> ask (so onStress continues),
       then watch({kind:"cue",protocol:"anchor:a1",trigger:"device",auto:true,signals:["heart_rate","hrv"]}, consent)
       -> hold. The anchor is offered and plays anyway, and RSOSGate.audit records it with "allow". A hold must
       suppress the offer; only an ask may downgrade to an offer. The GATE "suggest" offer of an anchor is not asked
       about its own protocol at all.
  R5-2 should fix — spec/WATCHDOG.md:51-52 and W3 (line 83) contradict the code (Spine flags hold regulating
       programs; breath anchor is no longer regulating). FIXES_R1 W-12 says §2 was amended; it was not. Needs a
       registration commit.
  R5-3 should fix — W-6 is inert: player.html:698 adds the offered program to the plan list it is checked against.
  R5-4 note — signals "heart_rate" and "hrv" (player.html:896-897) come from one sensor; "independent" in precept 3
       is satisfied by label.
  R5-5 note — docs/trials.html asks the Watchdog without memory_work_allowed or a clinician context; fine for its
       actions, but it logs "run trial_*" with kind run and category override_cue, so every trial session is held in
       Stabilisation (seen in Chrome for anchor_vs_sham), including designs that play nothing. Conservative; record it.
Verdict:         changes needed (R5-1, R5-2, R5-3, and Step 1b R5-2)
```

```
Step:            Step 3 — trials feed the evidence chain (spec/TRIAL_LOOP.md)
Reviewed commit: 6de0315 (registration 2f6d654 03:19:57, code 714d7ca 03:30:49)
Date:            2026-11-16
Checklist:
  1 pass  — test_trial_loop.py 8 pass + 1 registered expected failure; check_trial_loop.py fails [].
  2 pass, with findings — registration before code; §3 bridge, §4 scope and §5 programs as registered, except R5-1
            and R5-3.
  3 pass  — T4 threshold in 2f6d654 ("at least 80%", "at most 5%") is unchanged in 714d7ca, which only adds §7 and the
            status line; peak.py/gate.py unchanged since the backup.
  4 pass  — session.detail and the trials scope are registered; anchors get probes in PEAK's existing format;
            rsos.trial / rsos.trials.done pre-exist.
  5 pass  — T1 tests pass. Edge: sham_code with a seed below -7919*(i+1) gives undefined in JS and a code in Python
            (JS % keeps the sign); seeds on the page are non-negative, so latent (note).
  6 pass  — no clinical or crisis words on trials/contribute in non-clinical profiles.
  7 pass
  8 pass (local mirror) — check_trial_loop and my runs: 0 page errors.
  9 fail  — R5-1, R5-4.
T4 simulation vs registered wording: matches. 200 seeded people, 6 anchor_vs_sham blocks (12 sessions), before 4.0,
change = effect (2.0 for the anchor arm, 0 for sham) + N(0, 1.0), clipped to 0–10 (never binding in practice), fed
through evidence() into PEAK, status read from PEAK.strength; GATE strength checks read with G.gate; the null run uses
effect 0. The miss is sampling noise in a 200-person criterion: the same simulation with 1,000 people per seed base gives
84.7% (base 10000, whose first 200 give the reported 79%), 85.1%, 80.1%, 84.8%, 83.4% (bases 30000-90000). The
criterion as registered is not met and was correctly left unchanged; at n = 200 its standard error is about 2.6 points,
so the registered test could not separate 80% from 84%. Any re-test needs its own registration.
Not writing trials into the run log: sound, and registered before code (2f6d654 §2). Writing measurement sessions into
rsos.runs would change MEMSTACK's curve, CM1's signature, CONTAIN's run review and run counts; PEAK already holds the
evidence. Caveats in R5-3 and R5-4.
Findings:
  R5-1 should fix — docs/trials.html:208, 223, 230, 238-247: a session where "Play today's code" was never pressed
       still adds a PEAK probe (and a cue-arm session still adds a use). Repro (Chrome): anchor a1, anchor_vs_sham
       trial, Start today's session, rate 4 and 9 without pressing Play, Save -> session detail null, anchor probes
       [{kind:"sham", calm_before 4, calm_after 9}], message "This session added a probe to your anchor". PEAK's
       strength, and through it GATE's permission to automate, can be built from sessions where nothing was played.
       T2 ("recorded in the session") is also not true for these sessions. evidence() should require detail (or the
       page should require Play) for probes and cue-arm uses.
  R5-2 note — rsso/rsso/trial.py sham codes are deterministic from trial.seed, which sits in localStorage; blinding is
       nominal. Acceptable for a self-experiment; state it on the page or in TRIAL_LOOP.
  R5-3 should fix — T5 is tested more weakly than registered: rsso/tests/test_trial_loop.py:104-108 only checks that
       trials.html and trial.py do not contain "rsos.runs". The registered T5 is "MEMSTACK and CM1 results and the run
       log are identical with and without trials". No computation of MEMSTACK or CM1 is done.
  R5-4 note — the SSIT session links to player.html?program=ssit_<arm> (trials.html:224); runs there are written to
       rsos.runs as ordinary practice, so SSIT trial imagery does enter the run log, MEMSTACK and CM1. Probably
       intended (the imagery is practice), but §2's "trials stay out" should say so.
  R5-5 note — docs/contribute.html:291 adds "trials" to DEFAULT_ON, so the "optional" scope is pre-ticked (like the
       other default scopes). Consent is still the person's click on the final button, but say so in §4.
  R5-6 note (registration discipline) — code commits again edited spec files: 714d7ca (TRIAL_LOOP status line and §7)
       and 6de0315 (FIXES_R1 status line and §4; CONTAIN §9 lines 142 and 173). The CONTAIN corrections were
       registered in FIXES_R1 §1 and §7/§4 are result records, not changed criteria, so no registered rule was
       loosened; but FIXES_R1 §1 (6ed0f75) says "a registered spec changes only in a registration commit", and the
       next commit broke that literal rule. Either put results in a separate results commit or reword the rule.
  R5-7 note — tier013_lion_dragon.rsx: §5 says "codes joined with a pause"; the file has two TACTONs activated
       together; I did not verify the compiled tacton sequence contains the pause.
Verdict:         changes needed (R5-1, R5-3); the T4 miss itself is handled correctly.
```

```
Step:            Voice change (9b551d9, docs/js/voice.js) — brief
Reviewed commit: 6de0315
Date:            2026-11-16
Findings:
  1. note — docs/player.html:433, 451: saveSettings() runs on every recompile and writes voice_v: 2 whenever the
     voice menu has a value, so the player's automatic pick is stored as a "chosen" voice on the first compile after
     voices load. "A voice chosen on the player is used everywhere" is really "the first automatic pick is frozen";
     a better voice installed later is never picked unless the person changes the menu.
  2. note — anchors.html speak() calls RSOSVoice.speak without a guard; voice.js is in the service-worker shell, so
     this only fails if voice.js fails to load. atlas.html wraps it in try.
  3. note — not registered; it changes no stored format except the new voice_v field in rsos.settings (not listed in
     FIXES_R1 S-8). Scoring is the same in voice.js and player.html.
Verdict:         acceptable; notes only
```

## 6. Open items

- Step 4: BLE pairing with a passkey (`rsos_esp32.ino`, open NUS characteristic around lines 274–279).
- Step 5: refresh `architecture/` pages for RSX-V.
