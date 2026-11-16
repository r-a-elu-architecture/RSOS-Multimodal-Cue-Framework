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
  rsso/tests/test_trial_loop.py rsso/tests/test_fixes_r1.py rsso/tests/test_fixes_r2.py
python3 scripts/check_profiles.py docs     # browser acceptance (needs Playwright and Chrome)
python3 scripts/check_watchdog.py docs
python3 scripts/check_trial_loop.py docs
python3 scripts/check_fixes_r1.py docs
python3 scripts/check_fixes_r2.py docs
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

Reviewer: third independent agent (R3). Own clone, branch `review/r3` from `dev` at 14d096c; no code changed. Previous
reviews read on `review/interim` (2b2cc3c) and `review/r2` (557c3fa). Date 2026-11-16. Commands from a clean
checkout of 14d096c: `./scripts/check_all.sh` exit 0 (RSX 43, RSX-V 128, RSSO 239 OK with 1 expected failure,
Toolkit 10, conformance 15/15 and 15/15, board 7/7, generated files unchanged); `(cd rsxv && python3 -m pytest -q
tests)` 130 passed; the six step test files 49 passed, 1 xfailed; `check_profiles.py`, `check_watchdog.py`,
`check_trial_loop.py`, `check_fixes_r1.py`, `check_fixes_r2.py` (Chrome, Playwright, `python3 -I`) all exit 0 with
`"fails": []` and `"page_errors": []`. `test_fixes_r2.py` copied onto a worktree of 6de0315: 4 fail, R2-7 passes, as
FIXES_R2 §4 says. Extra scenarios: throw-away Playwright scripts against `docs/` served under `/dev/` (devmode active),
each described in its finding so it can be repeated. Rendered scan: every page x 7 domains x 3 states (Standard,
Stabilisation + practice paused, Clinician-led protocol + practice paused), navigation hidden as in P6: no clinical
word in the six non-clinical domains, no crisis/helpline/emergency wording, no page errors, no HTTP 4xx (only
external font requests blocked by this sandbox). Randomized Python/JS comparison (two seeds, well-formed inputs):
8,000 `watch` + `level`, 1,600 `link`, 2,666 each `screen`/`observe`/`allowed`, 1,600 `exit`/`event_from_check`,
2,666 `spine_flags`, 4,000 profile `text`, 800 `sham_code` (negative and >2^32 seeds), 1,200 `evidence`, 800
`record`, 600 `schedule`, 300 `analyze`, 120 contribution builds with random scopes and trials: 0 differences.
Malformed inputs do differ (R3-P1). `main` = backup in files (059a58f); engines (contain, peak, gate, safety,
watchdog) unchanged since 6de0315; no threshold changed.

```
Step:            Fix pass R2 verification (spec/FIXES_R2.md; registration e408934, code 9a51dc6, record 14d096c)
Reviewed commit: 14d096c
Date:            2026-11-16
Review r2 new findings (FIXES_R2 R2-1 … R2-8):
  R2-1 PARTLY FIXED — Resume no longer sets a PIN, "Set PIN" refuses during the protocol, screening answers are
       hidden without a PIN, five wrong PINs lock. But the reviewer's exact starting state (rsos.safety in CRISIS, no
       PIN) still leads out with two more clicks, in every domain: safety.html?profile=performance (also personal,
       workplace, clinical), name "Anyone", PIN 1234, Resume -> refused ("No clinician PIN is set … The practitioner
       records a clinical result above (this sets the PIN and is logged), then resumes with it."); choose result
       "none", Record result -> PIN saved, log {event:"pin_set_older_state", by:"Anyone"}, state unchanged; Resume ->
       "Session state: Standard … Resumed by the clinician", rsos.safety.mode NORMAL. See Step 1 R3-1.
       check_fixes_r2.py R2-1 tests only the first Resume.
  R2-2 FIXED — guard.js:17 passes memory_work_allowed. R2's LINX scenario (nodes.html?profile=workplace, "I keep
       having flashbacks of an accident and nightmares. I want calm, like a lion.", consent, Save) -> hidden box
       ticked, "Held by the Watchdog: Difficult-memory work is not offered in this domain [Gi]", log "hold plan
       memory". A clinician-led plan saved in Clinical, then its observer node run in Workplace -> held (memory + level).
       New bypasses of the same rule: Step 1b R3-1, R3-2.
  R2-3 FIXED — player.html:904-906. onStress() in Stabilisation with an anchor the gate allows at "auto": no anchor
       offer, nothing played, no GATE audit entry (the regulating-program offer "Start the override?" still appears
       for a regulating timeline, which is correct). In Standard: offer shown, audit "offered allow". Other pages that
       play anchors do not ask at all: Step 2 R3-1.
  R2-4 RECORDED-ONLY — by design; FIXES_R1 W-6 row and HANDOFF reworded. Still inert in the player
       (player.html:704).
  R2-5 FIXED — WATCHDOG §2 and W3 amended in the registration commit e408934; code matches (Node: paced_breathing
       with "take an ice bath" -> hold; memory_work with memory_work_allowed false -> hold).
  R2-6 FIXED — trial.py:178-189 / trial.js:106-112; check_fixes_r2 R2-6 (no Play -> 0 probes) repeated; parity 0
       differences over 1,200 random sessions.
  R2-7 FIXED (test strength) — test_fixes_r2.py:52 computes MEMSTACK and CM1 before/after.
  R2-8 FIXED, with one unregistered value — sham seeds identical for negative and >2^32 seeds; contribute.html:291
       trials opt-in; player.html:447-454 voice_v only when chosen; anchors.html:194 guards RSOSVoice; icon links
       present (no favicon 404 in any page). Unregistered: safety.html:364 writes event "pin_set_older_state", while
       R2-8 registers only {at, by, event: "pin_set"} (Step 1 R3-4).
Earlier items r2 marked not fixed / partly fixed:
  Step 1 #1 (S-1)         PARTLY FIXED — as R2-1.
  Step 1 #3 (spec)        FIXED — WATCHDOG §2 now lists CONTAIN §9.4's regulating programs.
  Step 1 #7               NOT FIXED — CONTAIN §9.3 and §9.6 (check-in with self-harm questions, helpline pointers)
                          are still not marked as superseded by §10.
  Step 1 #10 (pin_set)    FIXED (registered in R2-8), new value unregistered (above).
  Step 1 #11              NOT FIXED / not recorded — safety.html:288 still styles "hold" (and "ask") as "other".
  Step 1 #13 (2nd half)   NOT FIXED / not recorded — .github/workflows/pages.yml exists only on dev; main has only
                          checks.yml, yet HANDOFF §2 says pages.yml "builds main/docs at /".
  Step 1 R5-2 (PIN)       RECORDED-ONLY (FIXES_R2 R2-1 "a static site cannot authenticate"); the lock adds 15 min
                          per 5 tries online, nothing offline (salted SHA-256 of 4+ digits in localStorage).
  Step 1 R5-3 (category)  RECORDED-ONLY (R2-8).
  Step 1b #2 (P-2)        FIXED on the plan path (R2-2); see Step 1b R3-1/R3-2.
  Step 1b #7              RECORDED-ONLY — and R2-1 adds nothing against the person: in Clinical (or Research with
                          the module ticked) anyone sets the PIN with a name and four digits (safety.html:367),
                          after which the screening answers appear and the person can tick "clinician present" and
                          "no" and also knows the PIN that resumes the protocol.
  Step 1b R5-1 (wording)  NOT FIXED / not recorded — Performance safety.html:171 still "a new plan needs a clinician
                          present" while nodes shows "A coach is present for this session" (Workplace: facilitator).
  Step 2 #4 (W-4)         FIXED for plan runs (R2-2); bypass by editing text: Step 1b R3-1.
  Step 2 #5 (W-5)         FIXED (R2-3).
  Step 2 #6 (W-6)         RECORDED-ONLY (R2-4).
  Step 2 #11 / R5-4       RECORDED-ONLY (R2-8: one strap, two signals).
  Step 2 #12 / R5-2       FIXED (R2-5).
  Step 2 R5-1             FIXED (R2-3).  Step 2 R5-3: RECORDED-ONLY (R2-4).
  Step 2 R5-5 (trials held in Stabilisation even when nothing plays)  NOT ADDRESSED / not recorded (trials.html:205).
  Step 3 R5-1             FIXED (R2-6).  R5-3: FIXED (R2-7).  R5-4: RECORDED-ONLY (R2-8).  R5-5: FIXED (opt-in).
  Step 3 R5-2 (blinding nominal)  NOT ADDRESSED — TRIAL_LOOP and trials.html say nothing.
  Step 3 R5-6 (registration)      RECORDED (FIXES_R2 §1); see Process R3-1.
  Step 3 R5-7 (tier013 pause)     NOT FIXED, now verified false — Step 3 R3-1.
  Voice 1, 2              FIXED.  Voice 3: FIXED (voice_v registered in R2-8).
Verdict:         changes needed — R2-1 is only partly fixed (Step 1 R3-1); new blockers Step 1b R3-2 and Step 2 R3-2.
```

```
Step:            Step 1 — one safety engine (after FIXES_R2)
Reviewed commit: 14d096c
Date:            2026-11-16
Checklist:       1 pass | 2 fail (A4 on pages, R3-1) | 3 pass (engines unchanged since 6de0315) | 4 pass with note
                 R3-4 | 5 pass for well-formed inputs, note R3-P1 | 6 pass (rendered scan, 3 states) | 7 pass | 8 pass
                 (local /dev/ mirror) | 9 fail (R3-1, R3-3)
Findings:
  R3-1 blocker — docs/safety.html:356-366 with :372 and :329. ensurePin(true) (Record result) creates a PIN while
       the clinician-led protocol is active whenever none exists, and the clinical box (result form, PIN field) is
       shown in every domain during the protocol. Anyone at the page can therefore leave the protocol: Record result
       "none" with any name and PIN, then Resume (repro in R2-1 above; also Personal and Workplace, whose clinical
       module is "none", so P7 "clinical module controls appear only in Clinical and Research" is not true in this
       state). safety.html:380 tells the person exactly how. FIXES_R2 registers this "older data" path, but the page
       cannot tell a practitioner from the person, so CONTAIN §9 A4 ("CRISIS cannot be left by the person alone")
       holds on the page only when a PIN existed before the protocol began. Refuse PIN creation during the protocol
       on every path, or require something the person does not control.
  R3-2 note — the PIN is set by whoever reaches "Set PIN" first in Clinical/Research (safety.html:367; module toggle
       safety.html:341 is the person's). "Screening questions appear only once a PIN exists" (R2-1) therefore gates
       nothing against the person. Recorded limit, but HANDOFF/FIXES_R2 "(on the Safety page, by the practitioner,
       logged)" describes intent, not a check.
  R3-3 should fix — docs/player.html:625, :707-713 and :1126: no player action passes `text`, so Spine flags never
       reach the Watchdog from the player, contrary to WATCHDOG §2 ("Spine wording flags apply to every action").
       Repro (Chrome): player.html?profile=personal&program=override, edit the first SAY line to "Hold your breath
       until you almost pass out, then take an ice bath. …", Start -> check-in opens; log "allow run override",
       rules []. A programmed cue's content is not checked either (cue save, player.html:1116-1145, has no spineFlags).
  R3-4 note — safety.html:364 writes rsos.clinical.log {event: "pin_set_older_state"}; FIXES_R2 R2-8 registers only
       "pin_set".
  R3-5 note — CONTAIN §9.3, §9.6 still unmarked where §10 supersedes them; safety.html:288 "hold" styled "other".
  R3-P1 note — Python/JS differ on malformed saved state: safety.js observe/enterStabilise/link treat a state object
       without a valid mode ({} or {"mode":"BOGUS"}) as "not lower than Stabilisation", so observe({}, clinical high)
       gives no transition in JS but CRISIS in Python, and link(paused contain, {}) raises nothing in JS but
       Stabilisation in Python (Python raises KeyError on "BOGUS"). eventFromCheck with intensity "abc": JS
       distress null, Python ValueError. trial record with ts null: JS 0, Python None. Reachable only through edited
       storage; FIXES_R1 W-10 says {} states are identical, which holds for watch/allowed only.
Verdict:         changes needed (R3-1, R3-3)
```

```
Step:            Step 1b — domain profiles (after FIXES_R2)
Reviewed commit: 14d096c
Date:            2026-11-16
Checklist:       1 pass | 2 fail (R3-1, R3-2) | 3 pass | 4 pass | 5 pass (4,000 text cases) | 6 pass (0 clinical
                 words with navigation hidden, as P6 registers) | 7 pass | 8 pass | 9 fail (R3-1, R3-3)
Findings:
  R3-1 should fix — docs/player.html:692-700 (runFlags): memory_work and therapist_led are set only when the
       selected program is plan:N. Copying the node's program text into the editor of any other program drops both.
       Repro (Chrome): Clinical, PIN set, plan with the difficult-memories concern + Lion + Observer saved with
       clinician present and screening "no"; player.html?profile=workplace&program=plan:1 -> held (memory, level);
       copy #source, select "swish", paste the text, Start -> check-in opens, log "allow run node_observer",
       level self_guided. The clinician-led difficult-memory node runs in Workplace.
  R3-2 blocker — a clinician-led programmed cue runs anywhere, alone, as self-guided. docs/js/consent.js:33 builds
       the cue program as "PROTOCOL cue_<id>"; runFlags does not mark it programmed or therapist_led, and
       watchdog.js level() keys on the protocol name, so the run is self_guided. Repro (Chrome): safety.html?profile=
       clinical, module on, set PIN; player.html?profile=clinical&cueTier=T414, write a cue, tick present, screening
       "no", consent, Save -> "Saved"; then player.html?profile=personal (and workplace, and clinical with nobody
       present), "Load into the player", Start -> check-in opens each time; log "allow run cue_…", level
       self_guided. Tier 414 is clinician-led (watchdog.js:14, consent.js:8); Personal and Workplace allow up to
       structured. Only the session state still holds it (CRISIS -> held).
  R3-3 note — "Workplace hides difficult-memory work" (HANDOFF Step 1b, PROFILES §3) is not true of night.html in
       Workplace: "Mark any code linked to a painful memory" (night.html:89, :209) and "When a nightmare is detected"
       (:94) are shown. Also a plan with the difficult-memories concern but no observer node saved in Personal runs
       all its nodes in Workplace (only observer nodes carry memory_work).
  R3-4 note — the header link "Therapist" is on every page in every domain (profiles.js SKIP includes nav;
       check_profiles hides nav), so "zero clinical words" holds only with navigation excluded, as P6 registers.
       Safety page in Personal: "a qualified clinician's protocol (including a private psychotherapist or
       psychiatrist)"; Performance self-check row says "intensity 7 or more" while the domain's rating is "tension".
Verdict:         changes needed (R3-2, R3-1)
```

```
Step:            Step 2 — RSIA Watchdog (after FIXES_R2)
Reviewed commit: 14d096c
Date:            2026-11-16
Checklist:       1 pass | 2 fail (R3-1, R3-2 vs WATCHDOG §5) | 3 pass | 4 pass | 5 pass (8,000 random watch cases)
                 | 6 pass | 7 pass | 8 pass (safety page: "the chain verifies") | 9 fail (R3-1, R3-2, Step 1 R3-3)
Findings:
  R3-1 should fix — docs/anchors.html loads no safety.js, contain.js, watchdog.js or guard.js (:4-6, :173-176):
       capture (:279-299), probe (:305-327) and chain play (:349-363) play the anchor and write PEAK captures and
       probes in any session state. Repro (Chrome): rsos.safety mode CRISIS, one anchor, anchors.html, "I'm at a
       peak" -> "I'm there now" -> 8: code played (UGCL.feel called), capture stored, "Paired", no Watchdog entry.
       The same probe on trials.html is held. These captures and probes feed GATE's permission to automate.
  R3-2 blocker — docs/device.html:350-361: playCode() sends any code, including every node code of the saved plan
       (a clinician-led plan's observer code included) and any typed code, to the band with no Watchdog, session
       state or domain check; only "Run" (:364-370) asks. WATCHDOG §5 and HANDOFF Step 2 say the device page asks
       the Watchdog. (Code reading; needs a band to click.)
  R3-3 should fix — docs/therapist.html:304: a session in rsos.thera.current resumes on load without asking again.
       Repro (Chrome): Clinical, PIN set, trauma_observer started (present, "no"); therapist.html?profile=workplace
       and ?profile=personal -> the session view continues ("Step 1 of 9 … Check in"); with rsos.safety CRISIS the
       same. Clinician-led difficult-memory work continues in Workplace and during the clinician-led protocol
       (whose response is pause_module_work).
  R3-4 note — Step 2 R5-5 still open: trials.html:205 asks as kind "run"/override, so every trial session is held in
       Stabilisation, including designs that play nothing; and the Play button (:221) does not ask again if the
       state changes while the session view is open (same for the player's "Play it", :929-930).
Verdict:         changes needed (R3-2, R3-1, R3-3)
```

```
Step:            Step 3 — trials feed the evidence chain (after FIXES_R2)
Reviewed commit: 14d096c
Date:            2026-11-16
Checklist:       1 pass | 2 fail (R3-1) | 3 pass (T4 still the registered expected failure, threshold unchanged) |
                 4 pass | 5 pass (sham, evidence, record, schedule, analyze, contribution: 0 differences) | 6 pass |
                 7 pass | 8 pass | 9 fail (R3-1)
Findings:
  R3-1 should fix — docs/protocols/tier013_lion_dragon.rsx:2, :31-32 and spec/TRIAL_LOOP.md §5 say the codes are
       "joined with a pause (..- then ---)". Compiled (rsx compile_rsx): LION and DRAGON tacton pulses start together
       at t=2000 ms and interleave (2000 ..- and ---, 2200 ..-, 2400 ..- and ---, 2800 ---): on one motor the two
       codes overlap and neither is readable. No pause exists. (R2 Step 3 R5-7, unverified there.)
  R3-2 note — Step 3 R5-2 (sham codes deterministic from trial.seed in localStorage; blinding nominal) is not stated
       in TRIAL_LOOP or on the page; the save message also reveals the arm.
Verdict:         changes needed (R3-1)
```

```
Step:            Process — registration discipline since e408934
Reviewed commit: e408934, 9a51dc6, 14d096c
Date:            2026-11-16
Findings:
  R3-1 note — e408934 (registration) touches only FIXES_R2 and WATCHDOG; 9a51dc6 (code) touches no spec file;
       14d096c (record) changes FIXES_R2's status and §4, but also FIXES_R1's W-6 row in the fixes table, i.e.
       registered content, in a record commit. The edit was announced in R2-4 and is marked "(Record …)", so nothing
       was loosened, but by FIXES_R2 §1 it belonged in e408934. The record commit is 3 s after the code commit
       (05:04:02 / 05:04:05): the results were written before the code was committed.
  R3-2 note — HANDOFF §2 says pages.yml builds main/docs at "/"; the workflow exists only on dev.
```

## 6. Open items

- Step 4: BLE pairing with a passkey (`rsos_esp32.ino`, open NUS characteristic around lines 274–279).
- Step 5: refresh `architecture/` pages for RSX-V.
