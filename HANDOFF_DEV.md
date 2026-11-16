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
  rsso/tests/test_trial_loop.py rsso/tests/test_fixes_r1.py rsso/tests/test_fixes_r2.py rsso/tests/test_fixes_r3.py
python3 scripts/check_profiles.py docs     # browser acceptance (needs Playwright and Chrome)
python3 scripts/check_watchdog.py docs
python3 scripts/check_trial_loop.py docs
python3 scripts/check_fixes_r1.py docs
python3 scripts/check_fixes_r2.py docs
python3 scripts/check_outlet.py docs      # the output gate (FIXES_R3)
python3 scripts/check_low_mood.py docs    # spec/LOW_MOOD.md
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

Reviewer: fourth independent agent (R4). Own clone, branch `review/r4` from `dev` at 451a4df; no code changed. Third
review read on `review/r3` (15256fa). Date 2026-11-16. Commands on 451a4df: `./scripts/check_all.sh` exit 0 (RSX 43,
RSX-V 128, RSSO 246 OK with 1 expected failure, Toolkit 10, conformance 15/15 and 15/15, board 7/7, generated files
unchanged); `(cd rsxv && python3 -m pytest -q tests)` 130 passed; the seven step test files 56 passed, 1 xfailed;
`check_outlet.py`, `check_low_mood.py`, `check_profiles.py`, `check_watchdog.py`, `check_trial_loop.py`,
`check_fixes_r1.py`, `check_fixes_r2.py` (Chrome, Playwright, `python3 -I`) all exit 0 with `"fails": []` and
`"page_errors": []`. Extra scenarios: throw-away Playwright scripts (`attack1.py` … `attack3.py`, `lvl_fuzz.py`,
`parity.js`, not committed) against `docs/` served locally, with spies installed below the gate as in
`check_outlet.py`, and A2 without spies in real Chrome; each finding gives its repro. No HTTP 4xx and no page errors on
any page visited. `main` = 059a58f (backup in files); no threshold changed (only safety/watchdog changed in `rsso/rsso`
since 14d096c, and only the R3-c malformed-state guard).

```
Step:            Fix pass R3 verification (spec/FIXES_R3.md; registration 25ea88d, code 5636f66, records 6ed776f, 18bacbc)
Reviewed commit: 451a4df
Date:            2026-11-16
Review r3 findings:
  Step 1 R3-1 (blocker, PIN via Record result)   FIXED — safety.html:375 refuses PIN creation in CRISIS on every path.
       Repro: CRISIS, no PIN, clinical: Set PIN, Record result none/low/moderate/high -> "A PIN cannot be set while the
       clinician-led protocol is active"; Resume -> "No clinician PIN was set … cannot be left here"; no pin_hash,
       mode stays CRISIS. No other writer of pin_hash or a lower rsos.safety exists in docs/.
  Step 1 R3-2 (anyone sets the PIN)              RECORDED — FIXES_R3 §3 and the Safety page hint; but see Clinician
       control R4-C1 (the hint is hidden in five domains, the specs were not amended).
  Step 1 R3-3 (Spine flags never reach Watchdog) PARTLY FIXED — the r3 repro (SAY on its own line) is now held
       (spine:temperature_extreme, breath_holding_extreme). Words on a ';'-joined line or in FUTURES are not read:
       Level R4-L2.
  Step 1 R3-4 (pin_set_older_state)              FIXED — value and path removed.
  Step 1 R3-5 (CONTAIN §9 note, hold styling)    FIXED — note at the top of §9 (in registration 25ea88d);
       safety.html:288 marks hold/block rows.
  Step 1 R3-P1 (malformed state parity)          PARTLY FIXED — observe/link with {} or {"mode":"BOGUS"} now identical
       (CRISIS / STABILISE both). Still different: eventFromCheck({intensity:"abc"}) JS distress null, Python
       ValueError; exit({}, "person") JS TypeError (safety.js, history undefined), Python ["NORMAL", ok false].
  Step 1b R3-1 (observer text pasted)            NOT FIXED IN EFFECT — the paste is held, but the clinician-led plan's
       observer node is byte-identical to the built-in program node_observer, which runs self-guided: Level R4-L1.
  Step 1b R3-2 (blocker, tier-414 cue)           FIXED for the reported path ("Load into the player" is held in
       Personal, Workplace and Clinical without a clinician); deleting two lines runs it self-guided: Level R4-L3.
  Step 1b R3-3 (Workplace memory)                PARTLY FIXED — every node of a ptsd plan is memory work (Lion node
       of a ptsd plan in Workplace -> hold [memory]); night.html per-code column hidden. night.html:94 lede ("Mark any
       code linked to a painful memory … If a nightmare is detected") and :99 "When a nightmare is detected" are still
       shown in Workplace.
  Step 1b R3-4 (Therapist link, wording)         RECORDED (R3-g) for the link; safety.js:80 "private psychotherapist or
       psychiatrist" and Performance "intensity" wording unchanged, not recorded.
  Step 2 R3-1 (anchors page ungated)             FIXED — anchors.html:286/291/299/315/319/361 and the gate; in CRISIS
       capture stores and plays nothing (check_outlet G1-4 repeated).
  Step 2 R3-2 (blocker, device codes)            FIXED for the reported path — device.html:355 opens a session per code;
       plan codes carry the plan's flags (dx plan node "Lion" -> held in Personal). The same pattern typed in the code
       field is sent (note R4-G7).
  Step 2 R3-3 (therapist resume)                 FIXED — therapist.html:363-369 re-asks; check_outlet G1-7 repeated.
       Note: the resume session is adopted without memory_work (:368) although the ask used it (:364).
  Step 2 R3-4 (trials R5-5, Play not re-asking)  Play: FIXED by the gate (output re-checked). Held in Stabilisation
       when nothing plays: RECORDED (R3-g, by design).
  Step 3 R3-1 (Lion/Dragon overlap)              FIXED — compiled haptics: lion 2000/2200/2400 ms, dragon 8000/8400/
       8800 ms (5.2 s gap; R3-a registers "1 s pause, >= 600 ms").
  Step 3 R3-2 (sham blinding nominal)            RECORDED-ONLY in FIXES_R3 R3-g; TRIAL_LOOP and trials.html silent.
  Process R3-1 (record edited registered row)    RECORDED (R3-g).
  Process R3-2 (pages.yml)                       RECORDED (R3-g); HANDOFF §2 still says it "builds main/docs at /".
Older items r3 marked not fixed / partly / not addressed:
  R2-1 (PIN via Resume/Record)  FIXED (as Step 1 R3-1).     Step 1 #7 (§9.3/§9.6 unmarked)  FIXED (§9 note).
  Step 1 #11 (hold styling)     FIXED.                      Step 1 #13 (pages.yml)          RECORDED-ONLY.
  Step 1 R5-2 (PIN offline brute force) RECORDED-ONLY.      Step 1b #7 (whoever sets PIN)   RECORDED (FIXES_R3 §3).
  Step 1b R5-1 (Performance "clinician present" vs "A coach is present") NOT FIXED / not recorded (safety.html:172,
       source "a new plan needs a therapist present", identical to 14d096c:171; not part of FIXES_R3).
  Step 2 R5-5                   RECORDED (by design).       Step 3 R5-2 (blinding)          RECORDED-ONLY.
  Step 3 R5-7 (tier013 pause)   FIXED (R3-a).
Verdict:         changes needed — the structural claims of FIXES_R3 §1 and §2 do not hold (output gate R4-G1..G5,
                 level from content R4-L1..L4).
```

```
Step:            Output gate (docs/js/outlet.js, rdp.js gate, guard.js, RSOSDomain)
Reviewed commit: 451a4df
Date:            2026-11-16
Checklist:       1 pass | 2 fail (G1, G2) | 3 pass | 4 pass | 5 n/a | 6 pass | 7 pass | 8 pass (no page errors, no 404) |
                 9 fail (G1, G2, G4)
Findings:
  R4-G1 should fix — a held session falls back to the page's declared generic session. outlet.js:46-53: check()
       sets session = null on hold and permit() then calls ensure(), which opens the <body> declaration (player:preview,
       a plain self-guided run) and allows the output. Repro (Chrome, Standard): player.html?profile=personal;
       RSOSOutlet.adopt({kind:"run",protocol:"override",…}); quarantine "override" in rsos.contain; watch() for the run
       -> hold, but RSOSOutlet.permit("vibration") -> true, session now "player:preview". Every hold that is specific
       to the running action (CONTAIN quarantine, level, memory, Spine text, clinician rule) is lost this way; only
       holds that also apply to the generic declaration (CRISIS, Stabilisation) still stop output.
  R4-G2 should fix — "a change of … domain stops output on every page" (FIXES_R3 §1, HANDOFF) is false. profiles.js:123
       freezes RSOSDomain at page load and the player stores DOMAIN() in the session extra (player.html:628 with
       safetyDecide's x). Repro: player.html?profile=personal, adopt a memory_work run, permit -> true; in a second tab
       open safety.html?profile=workplace (rsos.profile = "workplace"); the first tab's permit -> still true, while
       watch() with the Workplace context -> hold.
  R4-G3 should fix — outputs already started are not stopped when the state changes; the gate is consulted only at
       start. device.html:371-378 sends a whole timeline and START; the band plays it on its own clock for the program's
       length (override: minutes) and nothing sends STOP when the session state becomes CRISIS. Same for a running
       oscillator (TONE length set by the program), queued speech (anchors.html:199 speaks without cancel) and long
       vibration patterns (player.html:553-556, count from the program). In the player, after CRISIS is set in another
       tab, new outputs are refused (0 outputs in 6 s) but the run view continues and the status line still says
       "All clear." (finish(), player.html:644, runs only on Stop or completion).
  R4-G4 should fix — the registered design is not what was built, and the built wrapper leaves channels open.
       FIXES_R3 §1 registers "AudioNode.connect to a context's destination … routed to a silent gain"; outlet.js:80-86
       wraps AudioScheduledSourceNode.start instead (connect is native). Sound that never calls start() passes in the
       clinician-led protocol. Repro (real Chrome, no spies, rsos.safety CRISIS, index.html): <audio autoplay> element
       plays (currentTime 0.84 s); new Audio(wav), muted = true, play(), muted = false -> plays unmuted (0.90 s);
       createScriptProcessor connected to destination processes 39 buffers (AudioWorklet and MediaElementSource are the
       same class). outlet.js:78 checks muted only at play(). No current page uses these paths (omission risk only).
  R4-G5 should fix — device- and agent-triggered outputs run under "self" declarations, so precept 3 (consent, two
       signals) is bypassed. device.html:119 declares trigger self; the posture sensor (device.html:415) vibrates
       [300,100,300] on a slouch with no consent record and one signal (repro: click #tiltGo, dispatch devicemotion
       events tilting the phone -> vibrate passes, session device:manual/self, rsos.consents null). The player's
       heart-rate offer vibration (player.html:888) runs under player:preview; agents.html:196-200 plays agent status
       codes under "agents:demo"/self. FIXES_R3 §1 says device- or agent-triggered declarations do not count as
       confirmed; the pages declare them as self.
  R4-G6 note — fails closed only when the safety scripts are missing, not when outlet.js is. Repro: block
       js/outlet.js, CRISIS: vibrate, speak and UGCL.feel reach the person on index, glyphs, night, anchors, player and
       trials (only the RDP START fails closed, rdp.js:28). sw.js:10 precaches with .catch(() => null), so an offline
       page can lack outlet.js. With guard.js blocked the gate is closed (glyphs: nothing passes).
  R4-G7 note — device code field: a plan node's code that is held (dx plan, observer of a clinician-led plan) is sent
       when typed (device.html:359 -> playCode without flags): STOP, LOAD 3, three H lines, START sent in Personal.
  R4-G8 note — session expiry does nothing on declared pages: an expired session is reopened silently at the next
       output (glyphs.html: open with 1 ms, permit after 50 ms -> true, new 900 s session).
  R4-G9 note — rdp.js:28 tests only the start of the line: send("STOP\nSTART") and send("LOAD 1 0.40\nH …\nSTART")
       pass the gate; over USB the firmware splits on "\n" (rsos_esp32.ino:290) and starts. No page sends joined
       lines today.
  R4-G10 note — RDP quick check in CRISIS: the START lines are refused silently, so B2–B7 report "Fail" (a broken
       band) instead of "held" (code reading, rdp.js:28 and device.html:344-349).
  Stop: always works — vibrate(0)/[]/[0,0], speechSynthesis.cancel, stop() on a never-started node, RDP STOP pass
       in CRISIS (check_outlet G2 repeated). Script order: outlet.js is the third script on all 24 pages, after
       devmode.js and profiles.js, neither of which captures an output function; no page uses iframes; the service
       worker has no output channel.
Verdict:         changes needed (G1–G5)
```

```
Step:            Level from content (level_of_program, rsso/rsso/watchdog.py:44-60, docs/js/watchdog.js:26-37; player runFlags)
Reviewed commit: 451a4df
Date:            2026-11-16
Checklist:       1 pass | 2 fail (L1–L4) | 3 pass | 4 pass | 5 fail on adversarial input (L5) | 6 pass | 7 pass | 8 pass |
                 9 fail (L1–L4)
Findings:
  R4-L1 should fix — the level depends on where the text comes from, not on the text. A clinician-led plan's observer
       node program equals docs/protocols/node_observer.rsx byte for byte (RSOSNodes.plan({concerns:["ptsd"],
       nodes:[{archetype:"OBSERVER"}]}).nodes[0].program === the built-in file), and the built-in is in the player's
       list (player.html:356-357) and not "edited". Repro (Chrome): plan above saved approved;
       player.html?profile=workplace&program=plan:0 -> block [memory, level]; choose "node_observer" -> allow,
       self_guided, Start opens the check-in. Same in Personal (plan node block [level], built-in allow). The device
       page "Run" offers the same program. The conservative edited-observer rule of FIXES_R3 §2 is bypassed by not
       editing.
  R4-L2 should fix — program words outside line-initial SAY/SEE/… are not passed to the Spine check. TEXT_RX is
       anchored at line start, but RSX splits statements on ';' (rsx.js:62-67) and FUTURES strings are spoken through
       $future. Repro: player.html?profile=personal&program=override, append
       PHASE x dur=2s {; SAY "Hold your breath until you almost pass out, then take an ice bath"; }  -> compiles with
       the text, decision allow, rules []; the same on separate lines -> block (spine). Replacing FUTURES with
       FUTURES "hold your breath until you almost pass out, then an ice bath" -> allow, rules [].
  R4-L3 should fix — a clinician tier is a removable comment and MARK line. Repro: tier-414 cue (consent record
       present/screened) in rsos.cues, player.html?profile=personal, RSOSConsent.cueProgram -> block; delete the "#"
       line and the MARK "programmed:…" line -> allow, self_guided, SAY "I let the old fear go" still played.
       (The cue's own consent gate is also skipped, since it keys on the MARK.)
  R4-L4 should fix — therapist programs: (a) "Re-living with the symbol" (therapist.html:216-219, copilot.js:688-697,
       imagery of a past event = difficult-memory work) is sent without any marker when no clinician-led session is
       open, and runs in Workplace: therapist.html?profile=workplace shows it; Open in the player -> allow,
       self_guided. (b) A marked program (# rsos-level: clinician_led) loses its level when the marker line is deleted:
       thera:core in Personal block [level] -> after deleting the two "# rsos-" lines allow, self_guided.
  R4-L5 note — Python/JS level_of_program differ on 31 of 6,035 adversarial sources (lvl_fuzz.py): "x\r# Tier 414"
       and "x # Tier 414" (JS ^ treats \r and U+2028 as line ends: led; Python not; rsx splits on \r, so JS is
       right), MARK "programmed:ид" (Python \w is Unicode: led; JS not), "﻿SAY …" / "\x1cSAY …" (\s differs) for
       the text. Well-formed ASCII sources: 0 differences. Python's \d in (?!\d) also differs for non-ASCII digits.
Verdict:         changes needed (L1–L4)
```

```
Step:            Honest clinician control (FIXES_R3 §3)
Reviewed commit: 451a4df
Date:            2026-11-16
Findings:
  PIN during the protocol: no path left (Set PIN, Record result with each result, Resume, other pages: none write
       pin_hash or lower rsos.safety; guard.link never lowers). Verified in the browser (Fix pass block, Step 1 R3-1).
  R4-C1 should fix — "the specs and the Safety page say plainly … advisory" (FIXES_R3 §3, HANDOFF) holds only on the
       Safety page in Clinical and Research. The sentence is inside #clinHead (safety.html:137-140), hidden when the
       domain's clinical module is "none" (safety.html:329): Personal, Coaching, Performance, Learning, Workplace never
       show it, while every domain shows "the responsible clinician resumes it". The specs were not amended: CONTAIN
       §9 A4 still says "CRISIS cannot be left by the person alone" (CONTAIN.md:180), §10.3 and WATCHDOG say nothing
       about advisory control.
  R4-C2 note — the /dev/ site keeps its own storage (devmode.js prefixes every key with "dev."), so a person in the
       clinician-led protocol on one copy of the site is in Standard on the other. Not recorded beside "clearing
       browser data resets it".
  R4-C3 note — during CRISIS the clinical box is shown in every domain (safety.html:330) with the placeholder
       "e.g. C-SSRS screener" (safety.html:142) in Personal, Performance and Workplace: a clinical instrument name in
       non-clinical domains, and PROFILES P7 ("clinical module controls only in Clinical and Research") is not true
       in this state (r3 Step 1 R3-1, not recorded).
Verdict:         changes needed (C1: the claim, not the mechanism)
```

```
Step:            Low mood (spec/LOW_MOOD.md; registration 1ec57e4, code 5878bc5, record 7dd8d6b)
Reviewed commit: 451a4df
Date:            2026-11-16
Checklist:       1 pass (check_low_mood exit 0) | 2 fail (LM1, LM2) | 3 pass | 4 pass (rsos.selfchecks, plan.dx,
                 practitioner_recommended registered) | 5 n/a (JS only) | 6 note LM4 | 7 pass | 8 pass | 9 fail (LM2)
Findings:
  L1 holds in all eight configurations: the diagnosed choice is visible only in Clinical and Research with the module
       on (hidden in Personal, Coaching, Performance, Learning, Research without module, Workplace). The record
       (§4 L1) lists only three of the six domains; L2's record does not mention the device page.
  R4-LM1 should fix — a diagnosed-depression plan is marked difficult-memory work: memory = !!plan.therapist_led in
       nodes.html:430, player.html:698 and device.html:362, and a dx plan sets therapist_led. In Workplace its nodes
       are held with "Difficult-memory work is not offered in this domain" (rule memory) besides the level reason;
       the logged rule and the person's reason are wrong.
  R4-LM2 should fix — "every one of its nodes is clinician-led in the player" holds only for plan:N. Repro: dx plan
       (Lion node) approved in rsos.plan; player.html?profile=personal&program=plan:0 -> block [level]; copy the
       source, select swish, paste -> allow, self_guided (no observer mode, so the edited rule does not apply). Same
       class as R4-L1/L3. Device: the node's code typed by hand is sent (R4-G7).
  R4-LM3 note — escalation (safety.html:341-348): off-by-one and window are right (2 -> none, 3 -> recommendation;
       rolling 7 x 24 h; null intensities excluded). But three checks saved within seconds give "Your intensity
       ratings have stayed high on several days this week" (spec §2 counts checks, not days); the message is not
       translated per domain (Performance shows "intensity" and "low energy or mood", where the domain says "tension"
       and "low drive"); it keys on plan.intake.concerns, so a dx plan without intake (file-loaded or edited) never
       triggers it.
  R4-LM4 note — the clinician-led status lives only in rsos.plan; a new everyday plan saved in Personal with the same
       nodes replaces it with no hold (self-declaration; the everyday option is by design structured).
Verdict:         changes needed (LM1, LM2)
```

```
Step:            Regressions and process since 14d096c
Reviewed commit: 451a4df
Date:            2026-11-16
Findings:
  Standard state, outputs reach the person (spies, Personal): glyphs, night, identity, atlas (speech + code), agents,
       anchors, contribute (recognition), trials, nodes (preview), device (carrier tone), player (recording preview;
       a paced_breathing run produced sound, speech and vibration). No "hold outlet" entries. Node picture (451a4df)
       renders; no page errors or 4xx on the pages visited.
  R4-R1 should fix — therapist.html has no <body> declaration (:129) and opens sessions only for a THERA session, so
       the copilot's outputs outside a session are silenced in Standard: fbBurst ("burst" code) and the code played
       when an utterance matches a branch (therapist.html:519, :621). Repro: therapist.html?profile=personal, click
       #fbBurst -> 0 outputs, log "hold outlet vibration", "hold outlet sound". check_outlet G2's static test passes
       because the page does open sessions elsewhere.
  R4-R2 note — script version strings not raised for changed files: player, nodes, device, therapist, trials and
       safety still load watchdog.js?v=1.0.0 and guard.js?v=1.0.0 (both changed in 5636f66), profiles.js?v=1.0.0
       everywhere (changed). Network-first service worker limits the effect; a stale cached watchdog.js without
       levelOfProgram would make runFlags throw.
  R4-R3 note — wording: escalation message (R4-LM3), CRISIS placeholder (R4-C3), night lede in Workplace (Step 1b
       R3-3). check_profiles passes (navigation hidden, as P6 registers).
  R4-R4 note — parity: profiles, trial and contribution code unchanged since 14d096c; safety/watchdog differences only
       on malformed or adversarial input (Step 1 R3-P1, R4-L5).
  R4-P1 note — registration discipline since 25ea88d: registration commits touch only specs (25ea88d: FIXES_R3 and
       the CONTAIN §9 note; 1ec57e4: LOW_MOOD); code commits touch no spec; record commits (6ed776f, 18bacbc, 7dd8d6b)
       change only status lines and results sections. Results still appear in code commits' HANDOFF text
       (5636f66: "14 failures on 14d096c, 0 now"; 5878bc5: "seven browser checks pass" in HANDOFF and the commit
       message), and each record commit follows its code commit by 3 s (06:00:16/06:00:19, 08:35:55/08:35:58).
       451a4df is an unregistered display fix (one line in nodes.html), acceptable as not a step.
Verdict:         changes needed (R1)
```

## 6. Open items

- Step 4: BLE pairing with a passkey (`rsos_esp32.ino`, open NUS characteristic around lines 274–279).
- Step 5: refresh `architecture/` pages for RSX-V.
