# HANDOFF_DEV — development record and review brief

One file for the work on the `dev` branch. The building account adds a section per step; the reviewing account
checks the newest section against the checklist in §3 and records findings in §5. Start here instead of from chat
history.

## 1. Rules

> **RELEASED v2.1.0 (2026-11-17).** Pull request #6 merged into `main` by the owner's decision (merge commit
> 9f60f4c); the live site shows this work. `dev` is open again; the rules below apply. Release notes: `releases/v2.1.0.md`.

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
  rsso/tests/test_fixes_r4.py rsso/tests/test_fixes_r5.py rsso/tests/test_fixes_r6.py rsso/tests/test_ble_pairing.py rsso/tests/test_arch_refresh.py rsso/tests/test_site_catchup.py rsxv/tests/test_levels.py rsxv/tests/test_site_agents.py rsxv/tests/test_ceiling.py
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
python3 scripts/check_site_catchup.py docs # spec/SITE_CATCHUP.md: System page, RSX-V page, results families
python3 scripts/check_evidence.py docs     # spec/EVIDENCE_LABELS.md: every live page shows its evidence label
python3 scripts/check_personlab.py docs    # spec/PERSONLAB.md §7d: Person Lab on the World page, its box on the System page
python3 scripts/check_site_night.py docs   # spec/SITE_NIGHT.md: Person Lab at the top of the World page, findings from data
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
Review status: **reviewed in RELEASE_1** (same-account review; §5).

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
Review status: **reviewed in RELEASE_1** (same-account review; §5).

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
Review status: **reviewed in RELEASE_1** (same-account review; §5).

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
Review status: **reviewed in RELEASE_1** (same-account review; §5).

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
Review status: **reviewed in RELEASE_1** (same-account review; §5).

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
Review status: **reviewed in RELEASE_1** (same-account review; §5).

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
Review status: **reviewed in RELEASE_1** (same-account review; §5).

### Step 5 — architecture map covers RSX-V and Steps 1–4 (spec/ARCH_REFRESH.md)

Registered 388f443 (B2 wording amended in 1703c61, before code); code 9cafcdb. New page `architecture/rsx/rsx-v/`; the
top-level table, RSIA Watchdog, CONTAIN, MICRO and cross-system pages describe the person-side Watchdog, session
states, guidance levels, domain profiles, output gate, level lineage, wristband pairing and the trial loop. Generated
by `architecture/build.py`. Test: `rsso/tests/test_arch_refresh.py`. Documentation only; no site page changed.
Review status: **reviewed in RELEASE_1** (same-account review; §5).

### Phase 2, Steps 6–8 — the site shows the system as it now is (spec/SITE_CATCHUP.md)

Registered ecac2ee. Built alongside the ESP32_TOOLS work without touching its files.
- **Step 6** (bfbc265): the System page's Safety box becomes "Watchdog and CONTAIN" (session states, guidance levels,
  domain profiles, output gate, level lineage); a new RSX-V box (AI → RSX-V → RSX program); Devices names pairing.
  A test keeps each box's status equal to the architecture map.
- **Step 7** (6686fff): new page `docs/rsxv.html` with one program in three forms (RSX-V command → RSX cue program →
  device lines), generated with the real bridge (`rsxv/rsxv/site_example.py`); RSX-V in every menu and on the home page.
- **Step 8** (7bc669f): the results page groups the 33 tests by family, shows each series as a chain coloured by
  outcome, and reads a new pass against the number of tests; "past-crisis" shown as "past high-distress".
Tests: `rsso/tests/test_site_catchup.py` (7), `scripts/check_site_catchup.py`.
- **Step 9** (345324b, spec/RSXV_LEVELS.md): RSX-V commands declare `LEVEL` and `MEMORY`; the effective level (declared
  or from content) travels into the RSX program as the person side's markers, NEXT never lowers it, and `run()` asks the
  Watchdog first (domain cap, session state, clinician presence, shared folded Spine check). Tests: `rsxv/tests/test_levels.py`.
- **Step 10** (305dc39, spec/AGENTS_PROVEN.md): the Agents page shows the passing RSX-V agent results working, from the real
  code (`rsxv/rsxv/site_agents.py` → `docs/data/agents_proven.json`): W1 trials step by step, the H-SWITCH policy comparison
  with its distress caveat, and W4, J1, T-AP cards. Tests: `rsxv/tests/test_site_agents.py`, `check_site_catchup.py` Step 10.
- **Step 11** (spec/CEILING.md; registered a45ff0d, code 3a055c7): W5-CEILING. Perfect source knowledge, mapped through
  fully read roles, against an 8-target pilot. By the registered rule agent → person passes (+0.213 per tick over the
  pilot). **Corrected by FIXES_P2 (review P2-1):** that room cannot be credited to the source, because a source-free rule
  reaches the same +0.240; the first caveat ("3,000 against 240 ticks") was wrong. The register shows the row as an
  analysis, and **the W5 transfer line stops in all four directions**; no successor is planned. The repurposing family's
  ceiling still needs its own registered design.
Phase 2 (Steps 6–11) is complete and checked (review P2, branch `review/p2`, commit 3248364).

### Fix pass P2 (spec/FIXES_P2.md; registered c586a03, code c17b0b4 and e6fbc73)
- E1/E2 (blocker P2-2): the sketch makes no library encryption request; the only `esp_ble_set_encryption` call sits under
  `linkPolicy.accept_request(...)`. A test checks the code with comments removed. BOARD_TEST T5 says why it matters.
- L1: memory work is read from the command's words too (folded, so look-alike letters do not hide them); `MEMORY no`
  does not lift it. L2: the domain is normalised, an unknown domain is refused, and no domain means Personal.
  L3: `source` and `confirmed` remain the caller's assertions (recorded, not changed).
- C1–C3: the ceiling record corrected (CEILING §5, `rsxv/RESULTS.md`, the decision text, `results/ceiling.md`, whose
  numbers are unchanged). The register has a new status, `analysis`, shown in neutral grey on the results page.
- A1/A2: the Agents page shows the W1 row's meaning beside the counts; the heading reads "Passed in simulation".
- §5: references corrected (SITE_CATCHUP Step 6 → bfbc265; RSXV_LEVELS → 345324b).
- Checks: RSX-V 152 passed; `rsso` 290 passed, 2 skipped, 1 xfailed; `check_all.sh` passed; all 11 browser checks exit 0;
  10 stub builds compile. No threshold changed.
- **Open notes:** P2-10, the emulator flag's test covers the sketch, not the build. P2-11, the NimBLE guard's macro.
  Both are left as they are until a real compiler can check the change.
Review status: **reviewed in RELEASE_1** (same-account review; §5).

### BASELINE_AUDIT (spec/BASELINE_AUDIT.md; registered 0f5ba72, code ee01c84 and 59539cf)
- Each passed register row was compared against its simplest baseline, re-running each test's own procedure and seeds.
  Every reproduction check passed.
- **None of the six audited rows beats its baseline:**
  - W1 ties greedy repair.
  - H-SWITCH and H-CFIT-M lose to fixed Bear (−0.011 and −0.085 per tick).
  - G1's gate equals transferring nothing.
  - J1 is not significantly above never-jam (p = 0.054).
  - T-AP loses to "Bear everywhere" with no source (−0.133 and −0.140 per tick).
- W4 keeps its label: no baseline applies.
- The register: 1 pass (W4), 11 mixed, 21 fail, 1 analysis. The original verdicts are kept in each row's text.
- Meaning: in these models one fixed stabilising archetype beats every adaptive method. The models cannot show the value
  of switching or transfer. Future tests need a model where the best archetype depends on context, with FIXED-BEST and
  STAB-ONLY as registered comparators.
- Disclosed: the smoke run used subsets of the registered seeds; its labels matched the full run's.
- Checks: RSX-V 156 passed; `rsso` 290 passed, 2 skipped, 1 xfailed; `check_all.sh` passed; all 11 browser checks exit 0.
- Agents page (§7, code a775ffa): retitled "Tested in simulation: the RSX-V agents", owner's decision 17 November. A line
  under the lede gives the audit's outcome per row, built from the audit's result file.
Review status: **reviewed in RELEASE_1** (same-account review; §5).

### CTX_PREF (spec/CTX_PREF.md; registered 0b0337c, code 6869870, GitHub job 44061366439)
- Real arena votes (lmarena-ai/arena-human-preference-140k, CC BY 4.0), analysed on GitHub's runner. Only aggregates
  were printed; they are read back from the job log.
- **Inconclusive:** 128 of 35,858 prompts were PERSONAL. Length-matched, no style wins or loses clearly in CODE or OTHER.
- The question (does the best response depend on context?) is still open. It needs data where personal-difficulty prompts
  are common.
- **CTX_PREF_HH** (registered c78c128, code 8668c32, run 44064375403): hh-rlhf helpfulness pairs, the same fixed patterns.
  **Inconclusive** again: 505 personal prompts, 11 and 22 usable pairs. In everyday prompts, asking back loses (0.413).
  Information only: the stabilising reply was chosen in 9 of 11 personal pairs.
- Two datasets, both inconclusive for the same reason: the fixed patterns find too few personal prompts. A third attempt
  needs a dataset made of personal conversations, or a meaning-based reader registered before it reads any data.
- **CTX_PREF_WC** (registered 2cb5ea2, code 39941b0, run 44068403883): WildChat-1M, all 14 files, 536,786 reactions.
  **Inconclusive** a third time: only 185 stabilising replies to personal messages. In everyday requests, asking back is
  followed by worse reactions (−0.011 [−0.020, −0.002]), in the same direction as CTX_PREF_HH. Association, not cause.
- Released to main on the owner's instruction: PR #9 (merge 0aa965c), 17 November, with **CTX_PREF and CTX_PREF_HH
  only**. The live Agents page now reads "Tested in simulation". CTX_PREF_WC (below) came after that merge and is on
  `dev` only.

### Phase 3 (website and agents), step 12: STAB_DEFAULT (registered 2349a85, amendment dd54544, code c4f3bd0)
- Found first: no person-facing page switches archetypes. Switching exists only in the simulation and the World page.
  The asking-back finding is not applied, because it covers everyday requests only.
- The World page shows always-Bear beside the Watchdog on the same simulated person, with the cue counts.
- **Person model v2 loophole:** under Bear, 1 cue in all 15 runs, never interrupted, blocking later cues. Recorded in
  BASELINE_AUDIT §8: it affects T-AP's confirmation run only.
- `world.person_world` is the stabilise-first default for new person-facing uses.
- Open: person model v3 (cues that can resolve without the module).
- Next: step 13, evidence labels.

### ADOPT_WC (registered 8b0c08e, code 84b660f, run 44084235343)
- Do the AI's words become the person's own across conversations? WildChat-1M, 26,783 persons, future-placebo design.
- **Fail:** -0.0046 [-0.0059, -0.0032]. The placebo is probably inflated by the AI echoing the
  person's own words.
- Information only: positive under 1 day; a dose effect (+0.013).
- A corrected design would be a new test on new data.

### PERSONLAB (the Person Lab; registered b6b2ff7, amended d9af1ac and 23d17c6)
- Owner's design: simulated persons with six-level identity profiles from real stories, and autonomous agents working
  toward each person's desired state, as a lab for researchers. A module, not a new language.
- Step 1 (eb39498): the schema in `rsxv/rsxv/personlab/schema.py`.
- Step 2: `SOURCES.md`. ESConv is primary, Hippocorpus and EmpatheticDialogues secondary.
- Step 3 (c324fa1, frozen 2d1f9c5): 100 ESConv profiles from two readers (separate instances of the same model; see the record review note in spec/PERSONLAB.md). **Kappa 0.728, passes.** Environment
  agreed worst (0.412); desired states are weak (46% matched). Stored privately (private repo `dev`, bbb3faa).
- Step 4 (registered 17650e5, code 06fa583): `ProfilePerson`; all 100 build. Cues never block. The parameters are placeholders.
- Step 5 (registered 49c8277, code b439c7c): **FAIL.** Final-intensity error: PERSON 0.814; persistence 2.030;
  mean change 0.771; linear 0.681. The fit gives all actions the same effect, and the profile makes it
  worse (+0.144). Whole-conversation final intensity in ESConv does not separate strategies.
- Step 5b (registered dd1d360, code 72c303e): stress per turn, kappa **0.925** over 1,584 turns, reliable. Override
  test **NOT TESTABLE**: 3 targeted blocks of 560, with 30 needed. Information only: questions are followed by the smallest
  stress drop.
- Step 5c (registered 8b8f069, code 948aaef): **NOT VALID.** Reader stress does not track the seekers' own intensity
  ratings (change ρ +0.03). It appears to track tone rather than self-reported state (100 conversations; wide intervals). The confirmatory test on reader stress is cancelled.
- RAPPORT_ESCONV (registered f4bbc63, code 3ce406c): on the seekers' own ratings, VAKOG matching **no effect**
  (+0.094), echo **no effect** (-0.023), both together not testable (96 events). Neither enters the agents' defaults.
Review status: **awaiting review**.

### Phase 3, step 13: EVIDENCE_LABELS (registered d0a6967, code 88c0eae; spec/EVIDENCE_LABELS.md)
- Before it, a record review of the PERSONLAB and RAPPORT records (1387719): PR #9's scope corrected (CTX_PREF_WC is on
  `dev` only), same-model readers disclosed, the 5c and RAPPORT readings worded to their intervals. No number or verdict
  changed.
- One scale on every live page, under the lede: E0 Written, E1 Built, E2 Checked on simulated people, E3 Tested in
  simulation, E4 Tested on recorded data, E5 Tested with people using RSOS. Each label ends "Not yet tested with people
  using RSOS."
- Generated by `architecture/evidence.py` from `architecture/evidence_map.json` and the results register. Every register
  row must be placed by source, or the build fails. Counts on the labels come from the register at build time.
- 21 pages: 6 at E1, 6 at E2, 3 at E4 (agents, World, RSX-V: 27 simulation tests with 1 pass; 7 recorded-data tests
  with 0 pass), 3 summary, 3 record. README gains an "Evidence levels" section.
- L5 caught "proven strength against sham" in the README; reworded.
- Checks: test_evidence 7 passed; check_evidence 168/168 views, 0 page errors; `check_all.sh` passed (rsso 301); the
  12 browser checks and check_release (75/75) exit 0.
- Click: `/dev/` (summary label under the intro), `/dev/anchors.html` (E2), `/dev/agents.html` (E4 with counts),
  `/dev/tiers.html` (record).
- Open: World page E3 or E4 (§7). Next: step 14, the Agents page board.
Review status: **awaiting review**.

### PERSONLAB §7d: the Person Lab on the World page (registered 0882e83, code 094b5c3; owner's decision)
- Rebuilt in this session: the earlier session's work on this (TARGET, mirrors, World section) was never pushed and was lost.
- RSX-V `TARGET <level>:<node>`; 100 public mirror lab persons (private structure, invented statements, 0 shared 4-word
  runs); step 4's person in Python and the browser (identical on 600 sessions); agents (Bear / Raven / Tiger / Lion by the
  Watchdog rule), always Bear and no support; equal (registered) and invented effects.
- Result by construction: equal effects → agents tie always Bear on all 100; invented effects → agents ahead on all 100.
  The page says plainly that this is architecture, the person model failed validation, and VAKOG and echo showed no effect.
- Click: `/dev/world.html#lab` (pick a lab person, switch effects and policy, click a tick for its RSX-V program);
  `/dev/system.html` → Person Lab box.
- Checks: RSX-V 220, rsso 304, `check_all.sh`, `check_personlab` 31/31, all browser checks and `check_release` exit 0.
- **Amendment §7d-B′** (registered df50bc2, code 5aefd70; owner: RSOS is open like Linux): lab persons are now drawn from
  published summary statistics (`rsxv/results/personlab_aggregates.json`), CC BY 4.0 with ESConv cited; no per-profile
  copy. Equal effects: tie on all 100; invented effects: agents ahead on 99, behind on 1.
Review status: **awaiting review**.

### ESP32_TOOLS — the wristband firmware with the real ESP32 compilers and Espressif's QEMU (spec/ESP32_TOOLS.md)

Registered 35d61d8; round-1 results c6b6af6; amendment A1 356991b; code c4d9b8b; E2 results 22059eb; amendment A2
183939d; code 74fa4b2; results fb684a5. Tools: arduino-cli 1.6.0, Arduino-ESP32 2.0.17, 3.2.1 and 3.3.12, QEMU
esp_develop_9.2.2_20260417. Reproduce with `firmware/esp32/real_check.py` (needs those tools; not part of `check_all.sh`).
- **Round 1, unchanged sketch: 0 of 30 builds compiled.** Real errors the stubs had hidden: the global `link` collides
  with POSIX `link()` (every build); `BLEDevice::setEncryptionLevel` moved to `BLESecurity` in 3.3; Arduino-ESP32 3.3+
  builds the ESP32-C3/-S3 with NimBLE, not Bluedroid; GFX Library 1.6.9 needs core 3.x. Exact output in
  `rsso/results/esp32_tools/round1_errors.md`.
- **Fixes (A1):** rename to `linkPolicy`; version-dependent encryption call; a clear `#error` for NimBLE builds (not a
  port: the pairing rules on NimBLE need their own registration and review); GFX pinned for 2.x. The stubs now include
  `<unistd.h>` and model the 3.3 API, so they catch the first two errors.
- **Round 2: 30 of 40 builds compile** (ESP32 on 2.0.17 and 3.3.12; -C3 and -S3 on 2.0.17 and 3.2.1; each alone, with
  each module and with all). The ten -C3/-S3 builds on 3.3.12 stop at the guard. No warnings in the sketch's files.
  Largest build 93% of the default app partition (ESP32, 3.3.12, all modules).
- **QEMU:** every real image reaches `setup()` and then asserts in the Bluetooth controller start-up (no Bluetooth in
  QEMU), resetting in a loop. Emulator-only flag `-DRSOS_EMULATOR` (§4: skips Bluetooth start-up and bond removal; never
  set for a board; a test checks this). With it, on ESP32 (3.3.12, 2.0.17), -C3 and -S3 (3.2.1): BOARD_TEST T1 and
  the USB-only commands pass (HELLO, three pulses, STOP while playing, PASSKEY, PAIR, UNPAIR, NEWKEY, long line,
  passkey kept in flash across a restart); `python -m rsso.board --port socket://…` 7/7 and `--full` 22/22 on all four.
  Registered U3 not met: STOP after the pattern ended answers `OK STOP`, which is what the protocol specifies (the
  test's wording was wrong; BOARD_TEST T1 corrected).
- `rsso.board` accepts pyserial URLs (`socket://`), so the board check can run against an emulator or a network port.
- **Still needs a board:** radio and pairing with a phone or computer (BOARD_TEST T3–T7), link loss (T8), bond removal
  (T9), PWM on a pin, motor feel and timing, scent/taste outputs, module hardware. Emulator timings are the emulated
  clock over a local socket, not a board's.
Docs: BOARD_KIT status and version table, BOARD_TEST T0/T1, firmware README, the sketch's STATUS comment, MICRO on the
architecture map (status stays "complete in simulation").
Review status: **reviewed in RELEASE_1** (same-account review; §5).

### BOARD_PENDING — checks and preparation while no board is available (spec/BOARD_PENDING.md)

Registered 4f32dc2; code 9cb1d8a, 6041243; results da31d1f.
- **K1 firmware CI** (`.github/workflows/firmware.yml`, separate from `checks` and Pages; deploys nothing). Job `compile`:
  the 40-build matrix on Arduino-ESP32 2.0.17, 3.2.1 and 3.3.12, passing when 30 compile and the ten C3/S3 builds on
  3.3.12 stop at the NimBLE guard. Job `emulator`: the ESP32 3.3.12 emulator build in QEMU runs U1–U9, U3b (U3
  expected to fail), board check B1–B7 and K3. First complete run 43941331355: both jobs passed, compile in 19 min.
  Any sketch change, from either session, is now compiled with the real toolchains on every push.
- **K2** issue form "Board report" and public issue #5 asking for the first board report (parts, 1.5 h, T5 and T7 first).
- **K3** the motor's PWM duty at the emulated ESP32's LEDC register (QEMU trace): 40% for 0.4, 60% for a 0.9 request
  under the 0.6 envelope, 0% after STOP and at boot, on 2.0.17 and 3.3.12, locally and on GitHub. Not shown: routing to
  the pin, the 20 kHz carrier, the MOSFET and motor.
- Observed for FIXES_P2 E1: the 2.0.17 and 3.2.1 library sources do call `esp_ble_set_encryption` on every connection
  when `setEncryptionLevel` was used; on 3.3.12 the call only stores the level. ESP32_TOOLS F2 had kept the call.
Review status: **reviewed in RELEASE_1** (same-account review; §5).

**Wristband firmware lane: parked (2026-11-17).** Nothing more is done here without a board. Done: the real-toolchain
compile, the emulator checks, the PWM-register check, CI on every push (`firmware` workflow), and the call for
a tester (issue #5). Resumes when a board report arrives (issue #5 or the Board report form): register the result
first, then fix. Open items stay as listed in §6: the NimBLE port for C3/S3 on 3.3+, and the first board run.

### WORLD_10X, TURN_RATINGS and CUE_RESOLVE (18 November 2026, night)

- WORLD_10X (spec/world10x/): sealed plan, not a test (ea1b5f7).
- TURN_RATINGS (planet 8): registered 90298e7, code fca11ec, pilot e0da9ed, results 2e6c334. Q1 and Q2 NULL (equivalence):
  the supporter's action adds nothing to the person's own next rating in ESConv. Register row Round 8e.
- CUE_RESOLVE (planet 2): registered e32e281, code 5749ddb, results in the next commit. Part A FAIL by its 10× rule (stuck
  cues 15/15 → 0/15, open ticks only 1.8× fewer); Part B: always Bear still beats the Watchdog on person model v3; half of
  its v2 margin was the loophole. Register row Round 8f.
- CUE_RESOLVE follow-up B (adopt v3): registered 354b807, code 93a1cbf: PASS, cue exposure is policy-independent on
  v3 (Bear ÷ Watchdog 0.90 [0.87, 0.94]); `person2.V3` is the default for new person-side tests. Register row Round 8f-B.
- SITE_NIGHT (pages): registered e23a960, code 083d18a, results 330eb55; check_site_night 20/20.
- Checks: listed in each spec's results. The reviewer should check that the registration commit precedes the code commit
  in both, and the disclosed smoke run in CUE_RESOLVE.

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

### RELEASE_1 review (2026-11-17, spec/RELEASE_1.md)

Reviewer: the building account's model family (Claude Opus 5.5), not an independent reviewer. Reviewed commit: 475b9d2
(`dev`), against `main` 059a58f. Checks on 475b9d2:
- `check_all.sh`: pass.
- rsso: 292 passed, 1 expected failure. RSX-V: 156 passed.
- Browser checks: 11 of 11 pass, after F1.
- `check_release.py`: 75 of 75 page views pass (25 pages: desktop, phone, and under /dev/).
- `firmware` workflow: pass.

```
Area:       1 wristband security (BLE_PAIRING, FIXES_R6C, FIXES_P2)
Checklist:  1 pass (suites; firmware workflow 40 builds + emulator) | 2 pass | 3 pass (only added constants:
            kWindowMs 120000, line limit) | 4 n/a | 5 pass (rsos_core host tests) | 6 n/a | 7 pass | 8 n/a | 9 pass
Findings:   1 note: FIXES_P2 E1 confirmed in the 2.0.17 and 3.2.1 library sources (BOARD_PENDING §5).
            2 note: ESP32_TOOLS A1 F2 had kept setEncryptionLevel on every core; FIXES_P2 removed it.
            3 note: everything about pairing rests on reading library sources; it needs a board (§6, issue #5).
Verdict:    ready for the owner, with the hardware items open
```
```
Area:       2 safety engine and wording (Step 1, CONTAIN, LOW_MOOD, R1-R6, output gate)
Checklist:  1 pass | 2 pass (spec before code in each step's record) | 3 pass (no changed limit lines against main;
            new SSIT programs carry their own SAFETY lines) | 4 pass (keys only added: rsos.clinical, rsos.settings,
            rsos.watchdog.log; none removed) | 5 pass (suites) | 6 pass (check_profiles; no crisis, helpline or
            emergency wording in any page's text, only internal mode names) | 7 pass | 8 pass | 9 pass
Findings:   1 note -> fixed (owner's decision, RELEASE_1 A2): README.md had "If you are in crisis, contact local
            emergency services or a crisis line"; README, SECURITY, release notes and the protocol's contraindication
            now say acute risk belongs under a qualified clinician's protocol (test_release.py).
Verdict:    ready for the owner
```
```
Area:       3 claims against evidence (RSX-V levels, W5-CEILING, BASELINE_AUDIT)
Checklist:  1 fail -> pass (RF1) | 2 pass | 3 pass | 6 pass | 9 fail -> pass (RF1)
Findings:   1 blocker (RF1, fixed in 475b9d2): check_site_catchup failed on dev ("H-SWITCH meaning shown"); the page
              was right (the profile wording rule), the check compared raw text. BASELINE_AUDIT Q4 recorded that
              the browser checks pass; that was not true when recorded.
            2 pass: no "proven", "validated", "clinically" or similar claim beyond the evidence on any page; the
              Agents page heading reads "Passed in simulation".
Verdict:    ready for the owner
```
```
Area:       4 site (SITE_CATCHUP, ARCH_REFRESH) and usability (RELEASE_1 U1-U4)
Checklist:  1 pass | 6 pass | 8 pass (75/75 views; the dev banner only under /dev/)
Findings:   1 should fix -> fixed: no guided entry on the home page (23 menu entries). Added "Start here", and status
              lines on the player, practitioner, devices and results pages.
            2 note (RF3, open): pages load Google Fonts from a third party on every visit; no glyph fonts offline.
Verdict:    ready for the owner
```
```
Area:       5 firmware and CI (ESP32_TOOLS, BOARD_PENDING)
Checklist:  1 pass | 2 pass | 3 pass | 7 pass | 9 pass
Findings:   1 note: this account built these steps and reviewed them; the firmware workflow's runs are the
              independent evidence (runs 43941331355, 43945771906).
Verdict:    ready for the owner
```
Release blocker found outside the steps: `main` holds 059a58f (a revert of S1). A plain merge would keep the revert;
RELEASE_1 §1 M1/M2 handles it before the pull request.

## 6. Open items

- Step 4 on a board: flash, pair from Android Chrome and a computer, check the window, the failure limit and USB-only commands (BOARD_KIT §4 Pairing); first, whether a bonded phone reconnects after its private address changes (R6c-2), and that a phone outside the window cannot start pairing (FIXES_R6C S1/S2).
- Wristband on Arduino-ESP32 3.3+ for the ESP32-C3/-S3: the pairing rules (window, failure limit, bond limit, refusal before keys are exchanged, bonded-host check) need a NimBLE implementation, registered and reviewed on its own (ESP32_TOOLS A1 F3). Until then those chips build with 3.2.1 or 2.0.17.
- First board run (BOARD_TEST.md): the firmware now compiles with the real toolchains and passes the USB checks in QEMU, so a failure on a board points at the radio, the pins or the motor rather than the build. Call for a tester: issue #5.
