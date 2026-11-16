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
| Deploy | `.github/workflows/pages.yml` (on `dev`; reaches `main` only at a merge) builds `main/docs` at `/` and `dev/docs` at `/dev/` |
| Dev site isolation | `docs/js/devmode.js`: saved data under `/dev/` is prefixed `dev.`; a "DEVELOPMENT VERSION" banner; a separate offline cache |

### How to verify

```
git checkout dev
./scripts/check_all.sh                     # every suite, conformance, generated files unchanged
(cd rsxv && python3 -m pytest -q tests)    # RSX-V agent layer
python3 -m pytest -q rsso/tests/test_safety.py rsso/tests/test_profiles.py rsso/tests/test_watchdog.py \
  rsso/tests/test_trial_loop.py rsso/tests/test_fixes_r1.py rsso/tests/test_fixes_r2.py rsso/tests/test_fixes_r3.py \
  rsso/tests/test_fixes_r4.py rsso/tests/test_fixes_r5.py rsso/tests/test_fixes_r6.py rsso/tests/test_ble_pairing.py rsso/tests/test_arch_refresh.py
python3 scripts/check_profiles.py docs     # browser acceptance (needs Playwright and Chrome)
python3 scripts/check_watchdog.py docs
python3 scripts/check_trial_loop.py docs
python3 scripts/check_fixes_r1.py docs
python3 scripts/check_fixes_r2.py docs
python3 scripts/check_outlet.py docs      # the output gate (FIXES_R3)
python3 scripts/check_low_mood.py docs    # spec/LOW_MOOD.md
python3 scripts/check_fixes_r4.py docs    # spec/FIXES_R4.md (synthetic sessions; see FIXES_R5)
python3 scripts/check_fixes_r5.py docs    # spec/FIXES_R5.md: real page paths
python3 scripts/check_fixes_r6.py docs    # spec/FIXES_R6.md: changes after Begin, lineage, held pages
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
The repeat review (`review/r2`, 557c3fa) found that two of these were not really fixed on the pages (the PIN could be
set by Resume; guard.js dropped the Workplace memory-work setting) and five smaller gaps; see Fix pass R2. WATCHDOG §6 is withdrawn. Late spec
edits recorded (PROFILES §4, WATCHDOG §6). Voice: one American-English voice on every page (9b551d9).
Tests: `rsso/tests/test_fixes_r1.py` (fail on fcc1b36, pass now), `scripts/check_fixes_r1.py` (page scenarios).
Decision flagged to the owner: the node studio's "low energy or mood" concern stays structured; the THERA low-mood
session is clinician-led (FIXES_R1 W-9).
Review status: **awaiting the repeat review (R5)**, which also covers Step 3.

### Fix pass R2 — findings of the repeat review

Review: branch `review/r2`, commit 557c3fa (reviewed 6de0315). Registration: `spec/FIXES_R2.md` (e408934), which also
amends WATCHDOG §2 and W3.
- R2-1 PIN: Resume never sets a PIN; no PIN can be set during the clinician-led protocol (except the logged
  older-data path through Record result); screening questions appear only once a PIN exists; five wrong PINs lock it
  for 15 minutes.
- R2-2 guard.js passes `memory_work_allowed` (and a test compares its keys with the Watchdog's).
- R2-3 every anchor offer asks the Watchdog: hold means no offer.
- R2-4 plan membership: by design it cannot hold in the player (every offer is the person's selection or a plan node);
  it applies to agents and devices proposing other programs.
- R2-6 trial evidence only when a code was played; R2-7 MEMSTACK/CM1 computed with and without trials (this held
  before too; the finding was the test's strength).
- R2-8 notes: sham seeds normalised; trials scope opt-in; voice saved only when chosen; icon links on six pages that
  lacked them (browsers asked for a missing favicon).
Tests: `rsso/tests/test_fixes_r2.py`, `scripts/check_fixes_r2.py`; the Watchdog and R1 browser checks now set a
clinician PIN first, as a clinician would.
Review status: **awaiting review**.

### Fix pass R3 — structural (after the third review)

Review: branch `review/r3`, commit 15256fa (reviewed 14d096c). Registration: `spec/FIXES_R3.md` (25ea88d).
- **Output gate** `docs/js/outlet.js` on every page: sound starts, unmuted media, speech, vibration and the wristband
  START pass only inside an allowed session; the Watchdog is asked again at every output; stop always works; pages
  declare their action on `<body>` or open sessions. Without the safety scripts nothing plays.
- **Level from content**: `level_of_program` (Python and JS) reads clinician tiers, programmed cues' tiers, markers and
  edited observer text; program words go to the Spine check.
- **Honest clinician control**: no PIN can be set during the clinician-led protocol, by any path; the Safety page and
  specs say the control is advisory on a person's own device.
- Smaller: Lion and Dragon codes 5 s apart; therapist sessions re-checked on resume; malformed saved states alike in
  both languages; night memory column hidden in Workplace; hold rows marked; CONTAIN §9 note.
Tests: `rsso/tests/test_fixes_r3.py`; `scripts/check_outlet.py` (14 failures on 14d096c, 0 now).
Review status: **awaiting the fourth review**.

### Low mood — owner's decision (spec/LOW_MOOD.md)

Registered 1ec57e4. The node studio's "low energy or mood" stays structured. With the clinical vocabulary only, a
separate "Depression (diagnosed or under treatment)" choice makes the plan clinician-led, and every node of it is
clinician-led in the player and on the device page. Self-checks are kept (`rsos.selfchecks`); with a low-mood plan,
3 or more checks of intensity 7 or more in 7 days recommend involving a practitioner (recorded on the plan).
Test: `scripts/check_low_mood.py` (L1–L4). Built after review 4 started, so review 4 does not cover it.
Review status: **awaiting review**.

### Fix pass R4 (spec/FIXES_R4.md)

Review: branch `review/r4`, commit 48d3aff (reviewed 451a4df; no blockers, 13 should-fix). Registration c7a8e39
(also amends CONTAIN A4 and LOW_MOOD §2); code fea4ef6.
- **Gate**: no fallback to the page session once a session is held; domain re-read on storage events; a hold stops
  running sound, speech, media and vibration, ends the run and sends STOP to the band; speaker connections pass a
  per-context gate gain; device- and agent-triggered outputs follow the firing rules; typed codes inherit the plan
  node's flags; any START line is gated; ugcl and voice fail closed.
- **Level from origin**: plan, saved program or cue sets the level; the same text keeps the same level; every quoted
  string goes to the Spine check; re-living counts as memory work.
- Smaller: a diagnosed low-mood plan is clinician-led, not memory work; escalation counts distinct days; the advisory
  sentence is always shown; therapist copilot outputs work in Standard; malformed check answers are dropped.
Tests: `rsso/tests/test_fixes_r4.py`; `scripts/check_fixes_r4.py` (16 failures on 451a4df, 0 now).
Review status: reviewed in review 5 (`review/r5`, c21e634): 0 blockers, 10 should fix → fix pass R5.

### Fix pass R5 (spec/FIXES_R5.md)

Review: branch `review/r5`, commit c21e634 (reviewed 2dacc02). Registration d633b5a (also restores the LOW_MOOD §2
count, owner's decision); code 9ab5f78.
- **Gate**: a list of sessions with handles; a refused open changes nothing; the stricter of the saved and the live
  domain; expired sessions removed, held ones kept until closed; copies from `session()`; the run's session opens after
  the check-in.
- **Level from compiled content** (`docs/js/lineage.js`): a run inherits the level of a plan node, saved program or cue
  whose distinctive content it carries or whose content it mostly shares; player and device page alike; a held node's
  code is held in any sequence; futures fields and compiled words go through Spine.
- **Folding and parity**: one `fold()` in both languages for level patterns and Spine (NFKC, zero-width removed,
  look-alike letters, Unicode spaces, ASCII lowercase); strict numeric check answers; exit repairs bad history.
- Smaller: direct sound paths fail closed without the gate; two memory-work sentences hidden in Workplace; the
  escalation count restored; FIXES_R4's "No threshold changed" and Q1 claims corrected in its record.
Tests: `rsso/tests/test_fixes_r5.py`; `scripts/check_fixes_r5.py` (16 failures on 4f4b6d8, 0 now).
Review status: reviewed in review 6 (`review/r6`, b423035): 1 blocker, 7 should fix → fix pass R6.

### Fix pass R6 (spec/FIXES_R6.md)

Review: branch `review/r6`, commit b423035 (reviewed c3b1a55). Registration 3966b05 (amends FIXES_R5 §2/§3 and
BLE_PAIRING P3/P4/§4); code dbb393c.
- **Blocker R6-1**: the run plays the timeline decided at Start; menu, editor, futures and breath fields are locked
  while it plays; a program that changes anyway stops the run.
- **Lineage**: share = shared / |origin|; `$future` removed, not skipped; joined text catches split sentences; texts that
  a built-in also has count only exactly; strict mode explained. Consequence: with a diagnosed-depression plan the
  built-in Lion/Observer nodes are held too.
- **Folding pinned** to Unicode 15.1 by a generated table (`scripts/gen_fold_table.py`), the same in Python and every
  browser; accents and more look-alikes folded.
- **Held pages**: device page, automatic anchor and trials close their held sessions and say so.
- **Wristband**: pairing requests answered only in the window; passkey shown only in it; no-key authentication only
  for bonded hosts; receive line portable to 3.x (stubs now catch the old error); ring emptied on link loss; the page
  writes with response.
Tests: `rsso/tests/test_fixes_r6.py`; `scripts/check_fixes_r6.py` (8 failures on c3b1a55, 0 now); link_test 52.
Review status: targeted check `review/r6-check` (1ae33e3, 7171f77): R6-1–R6-7, R6-9, R6-11 confirmed fixed; R6c-1 (B5 had no
effect) → fix pass R6C (registration 0ab05ea, code 69bfb2f): the library's security callback answers host-started
pairing with the window rule, the band requests encryption only in the window, and the player compiles at Start.
R6c-2 resolved by reading ESP-IDF v5.1.4 (FIXES_R6C §5): a reconnect reports the record's original address, the same one the bond list holds. **Still only on hardware:** radio behaviour, phone pairing prompts and motor timing (`firmware/BOARD_TEST.md`).

### Step 4 — paired, encrypted wristband Bluetooth (spec/BLE_PAIRING.md)

Registered c898386; code 661165e. The band accepts commands only over an LE Secure Connections link with a six-digit
passkey (made on first start, kept in flash, never sent over Bluetooth; read with `PASSKEY` over USB or on the
screen). New hosts pair only within 120 s of power-on or USB `PAIR`; 3 failures close the window; at most 4 bonds;
`PASSKEY`, `PAIR`, `UNPAIR`, `NEWKEY` only over USB; lines over 95 characters dropped whole. Policy
`firmware/rsos_core/rsos_link.*` (host test `link_test`, 47 checks), copied into the sketch.
Tests: `rsso/tests/test_ble_pairing.py`; sketch compile check (10 builds). **Not run on a board.**
Review status: **awaiting review**.

### Step 5 — architecture map covers RSX-V and Steps 1–4 (spec/ARCH_REFRESH.md)

Registered 388f443 (B2 wording amended in 1703c61, before code); code 9cafcdb. New page `architecture/rsx/rsx-v/`; the
top-level table, RSIA Watchdog, CONTAIN, MICRO and cross-system pages describe the person-side Watchdog, session
states, guidance levels, domain profiles, output gate, level lineage, wristband pairing and the trial loop. Generated
by `architecture/build.py`. Test: `rsso/tests/test_arch_refresh.py`. Documentation only; no site page changed.
Review status: **awaiting review**.

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

## 6. Open items

- Step 4 on a board: flash, pair from Android Chrome and a computer, check the window, the failure limit and USB-only commands (BOARD_KIT §4 Pairing); first, whether a bonded phone reconnects after its private address changes (R6c-2), and that a phone outside the window cannot start pairing (FIXES_R6C S1/S2).
