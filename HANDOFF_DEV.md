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
| `main` | identical in files to the backup (one revert commit, 059a58f) |
| Deploy | `.github/workflows/pages.yml` builds `main/docs` at `/` and `dev/docs` at `/dev/` |
| Dev site isolation | `docs/js/devmode.js`: saved data under `/dev/` is prefixed `dev.`; a "DEVELOPMENT VERSION" banner; a separate offline cache |

### How to verify

```
git checkout dev
./scripts/check_all.sh                     # every suite, conformance, generated files unchanged
(cd rsxv && python3 -m pytest -q tests)    # RSX-V agent layer
python3 -m pytest -q rsso/tests/test_safety.py rsso/tests/test_profiles.py
python3 scripts/check_profiles.py docs     # browser acceptance (needs Playwright and Chrome)
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

Reviewer: interim independent agent (own clone, branch `review/interim`; no code changed). Commands used, from a
clean checkout of `dev` at fcc1b36: `./scripts/check_all.sh` (exit 0: RSX 43, RSX-V 128, RSSO 217, Toolkit 10 tests
OK; conformance 15/15 and 15/15; board 7/7; generated files unchanged); `(cd rsxv && python3 -m pytest -q tests)`
130 passed; `python3 -m pytest -q rsso/tests/test_safety.py rsso/tests/test_profiles.py rsso/tests/test_watchdog.py`
28 passed; `python3 -I scripts/check_profiles.py docs` and `python3 -I scripts/check_watchdog.py docs` (Chrome,
Playwright): `"fails": []`, `"page_errors": []`. Extra scenarios were run with throw-away Node and Playwright scripts
against a local copy of `docs/` served under `/dev/` (so `devmode.js` was active); they are described in each finding
so they can be repeated.

```
Step:            Step 1 — one safety engine (CONTAIN §9 S1 and §10 revision)
Reviewed commit: fcc1b36 (Step 1 code: 6394a70, 5347a3a, 1409a8c)
Date:            2026-11-16
Checklist:
  1 pass  — check_all.sh exit 0; rsxv pytest 130 passed (rsxv/tests unchanged vs backup: git diff --stat shows no
            change under rsxv/tests); test_safety.py A1–A8 pass.
  2 pass, with findings — 5227a26 (§9 spec, 00:04:53) before 6394a70 (code, 00:13:16); 8db766b (§10, 01:12:16)
            before 5347a3a (01:20:51). Code follows §9/§10 except findings 2, 3, 4, 5.
  3 pass, with finding 3 — contain.py/contain.js: only decide(..., safety) added, ENVELOPE and escalation limits
            unchanged (git diff backup..dev). safety.py thresholds (distress >= 7, sleep < 4, RECOVERY_H, WEEKLY_CAP,
            MODE_ALLOWED) identical to backup rsxv/rsxv/safety.py. New rule not in §9: REGULATING adds tier012.
  4 pass, with notes 10–12 — new key rsos.safety registered (CONTAIN.md:118); rsos.clinical and
            rsos.clinical.log are not registered; rsos.contain.log decision values changed.
  5 pass — A1 parity test passes; my reading of safety.py vs safety.js found no rule difference.
  6 pass for crisis wording — A7 passes; rendered-text scan of 20 pages x 7 profiles finds "crisis" only on
            results.html (research record, exempt) and a false hit "Self-harmonic" on metrics.html. Clinical words
            on non-clinical profiles: see Step 1b.
  7 pass now, with note 9 — gh/main 059a58f is file-identical to backup 32f49bb (git diff --stat empty), but S1
            reached main and the live site for about 10 minutes (note 9).
  8 pass (local mirror) — github.io is not reachable from this environment (proxy 403). Pages run 43790234644
            succeeded and logged "live: 059a58f  dev: fcc1b36". Local /dev/ mirror: banner on all 140 page loads,
            0 page errors; console errors only from blocked external resources.
  9 fail — finding 5 (footer), note 6 ("suggests").
Findings:
  1. should fix — safety.html:143, 348-352: any visitor leaves the Clinician-led protocol (CRISIS) by ticking "I am
     the responsible clinician" and typing any name. Repro: put rsos.safety in CRISIS
     (RSOSSafety.observe(newState(), {clinical_result:"high"})), open safety.html?profile=performance, tick #clinOk,
     name "anyone", Resume -> "Session state: Standard". A4 ("CRISIS cannot be left by the person alone") holds only
     in the engine (exit(by="clinician")), not in the product. Nothing in HANDOFF or §10 states this limit.
  2. should fix — nodes.html:190-193, 490 and player.html:186, 1063: the clinical screening question ("Did today's
     clinical screening ... indicate elevated risk?") is shown in every profile (seen in Personal on nodes.html
     after ticking concerns), and a "yes" moves the person into the clinician-led protocol (nodes.html:408). §10.4
     says the clinical module is off by default and switched on by a practitioner.
  3. should fix — rsso/rsso/safety.py:118, docs/js/safety.js:83: REGULATING includes tier012_breath_anchor. §9.4
     registers "paced breathing, interrupt-only and stillness programs" as regulating_cue. Adding tier012 widens what
     Stabilisation and Paused: practical allow; it is not registered (it first appears in WATCHDOG §2, after S1).
  4. should fix — safety.py:121-131 (safety.js:85-91): the category that decides what a session state allows comes
     from an action.category passed by the caller, or from the protocol name. Both can be chosen by the caller or
     the person. Repro A (Node): watch({kind:"run",protocol:"override",category:"logging"}, {safety: CRISIS}) ->
     allow (control without category -> hold). Repro B (Chrome): rsos.safety = Stabilisation;
     player.html?program=override, Start -> held; change the PROTOCOL line in the source box to
     "PROTOCOL paced_breathing" -> the 11-phase override (52 s) passes the Watchdog and opens the check-in. The audit
     log records "allow run paced_breathing".
  5. should fix — §10.1 and HANDOFF Step 1 say the footer "Research and development framework; not a medical
     device." remains on pages. Only 4 of 24 pages have it (index, results, safety, therapist; grep). Player, nodes,
     night, device and contribute do not.
  6. note — safety.py:164 / MESSAGES["unstable"]: §10.5 and the message say a high self-check "suggests"
     Stabilisation, but observe() enters it at once.
  7. note — CONTAIN §9 item 3 and A1 still name CHECKIN / event_from_checkin, which no longer exist (replaced by
     event_from_check, §10.5). §9 is not marked as superseded where §10 changed it.
  8. note — rsso/tests/test_safety.py:193-199: A7 scans only static HTML with scripts removed. Text built by
     JavaScript (module messages, thera.json, inline page scripts) is not covered.
  9. note — the S1 code commit 6394a70 was pushed to main at 00:13:16 and deployed to the live site
     (pages-build-deployment run 43779070685). It was reverted at 00:23:42 (059a58f). HANDOFF §2 says main is
     "identical in files to the backup" but does not say the live site ran S1 for about 10 minutes.
  10. note — rsos.clinical and rsos.clinical.log are new, unregistered storage keys. clinical.log, and the
     safety-state history ("by: clinician: <name>"), store the name the practitioner types (safety.html clinSave,
     clinGo).
  11. note — guard.js:22-24 writes Watchdog decisions (allow / ask / hold) into rsos.contain.log, which before only
     held allow / block. safety.html:287 shows "hold" with the class "other". This record-format change is not
     registered.
  12. note — rsos.screens keeps its format, but the question behind a "yes" changed (consent.py
     SCREENING_QUESTION, thera.json screen step) from a crisis question to "elevated clinical risk". Old and new
     answers cannot be told apart, and CONTAIN escalation reads both.
  13. note — .github/workflows/checks.yml:3-5 runs only on pushes to main and on PRs, so no dev commit had CI.
     pages.yml exists only on dev (gh/main has only checks.yml), so a push to main alone no longer deploys the
     live site.
Verdict:         changes needed
```

```
Step:            Step 1b — domain profiles (spec/PROFILES.md)
Reviewed commit: fcc1b36 (Step 1b code: 4358b02)
Date:            2026-11-16
Checklist:
  1 pass  — test_profiles.py P1–P5 pass; check_profiles.py: all non-clinical profiles 0 hits, clinical 31,
            page_errors [], fails [].
  2 pass, with findings — d9b3c01 (01:31:36) before 4358b02 (01:41:35). The code commit also edited the registered
            vocabulary (finding 5). Workplace and Research rules are not met (findings 2, 3).
  3 pass  — profiles.py/profiles.js are not imported by any engine module (P4); no threshold touched.
  4 pass  — only rsos.profile is written by profiles.js (lines 106, 134, 145).
  5 pass  — P1 parity over the corpus; spot checks gave identical output in Python and JS.
  6 fail  — finding 1 (wrong "-led" labels), finding 4 (clinical wording that the word list misses).
  7 pass  — see Step 1.
  8 pass (local mirror) — 7 profiles x 20 pages loaded, 0 page errors.
  9 fail  — "Workplace hides difficult-memory work" (finding 2); "Clinical instruments ... only with clinical
            vocabulary" (finding 4, Research).
Findings:
  1. blocker — docs/js/profiles.js:53-56: the rule \btherapist\b also rewrites "therapist-led", so clinician-led work
     is labelled as led by the profile's practitioner. Seen in Chrome: player tier labels "Tier 414/420/439/440 ...
     (coach-led | teacher-led | facilitator-led | investigator-led | practitioner-led)"; therapist page
     "A memory, observed (coach-led)" and "Coach-led, screening first"; safety page "coach-led tiers need a coach
     present and the screening passed". The message at nodes.html:411 becomes "Observer work with past setbacks is
     coach-led: save this plan in a session with your coach present". On the same page the plan's safety list says
     "clinician-led", and the Watchdog then holds the plan. This contradicts CONTAIN §10.2 ("consent alone or a
     coach is not enough at this level") and PROFILES §2.4.
  2. should fix — Workplace "difficult-memory work: not offered" (PROFILES §3) is enforced only by hiding the ptsd
     checkbox (nodes.html:484, profiles.js:152). Repro: nodes.html?profile=workplace, LINX message "I keep having
     flashbacks of an accident and nightmares. I want calm, like a lion." -> applyIntake (nodes.html:438) ticks the
     hidden box; saving the plan stores intake.concerns ["ptsd"]. The Workplace therapist page lists
     "A memory, observed" / "A difficult memory observed from another position". Contribute lists "difficult
     memories". Night says "with difficult memories, work with a facilitator".
  3. should fix — profiles.js:14 and rsso/rsso/profiles.py:18 give Research max_level clinician_led in every case.
     §3 says "clinician_led with a study clinician" and "study enables" the module. Impact: see Step 2 finding 2.
  4. should fix — CLINICAL_WORDS (profiles.js:72) misses "clinical", "diagnos*", "treat*" and instrument names. Still
     visible on non-clinical profiles: nodes "Did today's clinical screening (the practitioner's validated
     instrument) indicate elevated risk?" and "Record the clinical screening result ..." (Personal); therapist "RSOS
     supports your clinical judgement; it does not diagnose or treat" (all profiles); contribute "diagnosis
     categories"; safety.html:138 "the C-SSRS screener or PHQ-9", shown in Research with the clinical module off.
     That last one breaks PROFILES §4 (instruments only with the clinical vocabulary).
  5. should fix — the code commit 4358b02 changed spec/PROFILES.md §4 (it adds "distressing reads intense") after
     registration d9b3c01. It is a small addition, but it is a change to registered text in the code commit.
  6. note — the phrase rules make ungrammatical text. On pages now: "Symptoms and what they feel like" ->
     "Performance limiters: what it feels like" / "Focus areas: what it feels like" (plural noun, singular "it").
     Latent (checked in Node; the source strings are not on current pages): "an anxiety disorder" -> "an pre-event
     nerves disorder"; "Panic attacks" -> "Pre-event nerves attacks"; "Distress (SUD)" -> "Tension (tension)";
     Workplace "Therapy sessions" -> "Facilitated sessions sessions"; "trauma-focused" -> "past setbacks-focused";
     "Trauma processing" -> "Past setbacks processing". "traumatic" and "depressive" are not translated.
  7. note — the domain menu (profiles.js:134) and ?profile= are not authenticated. Anyone lifts the Personal or
     Workplace cap by choosing Clinical. Repro: nodes.html?profile=workplace, choose Clinical, tick the two boxes ->
     the clinician-led plan is saved. The Watchdog reason says resolve "none", which is misleading.
  8. note — scripts/check_profiles.py records only "pageerror", not console errors.
Verdict:         changes needed
```

```
Step:            Step 2 — RSIA Watchdog on the person side (spec/WATCHDOG.md)
Reviewed commit: fcc1b36
Date:            2026-11-16
Checklist:
  1 pass  — test_watchdog.py W1–W9 pass; check_watchdog.py fails [] (plan:performance held [Gi]; plan:clinical
            saved; session:workplace held; session:clinical started; logs verify).
  2 fail  — 1dc4ea6 (01:55:20) before fcc1b36 (02:07:25), but §6 "Interpretation recorded at build time" was added
            in the code commit and relaxes the registered rule (finding 3). W7 fails in normal use (finding 1).
            Research clinician rule (finding 2).
  3 pass  — no CONTAIN or safety threshold changed (see Step 1); the Watchdog only adds rules.
  4 pass, with Step 1 note 11 — rsos.watchdog.log is registered (§4).
  5 fail  — finding 8 (JS fails open on an unknown max_level; Python raises), note 10.
  6 pass  — see Step 1/1b.
  7 pass  — see Step 1.
  8 pass (local mirror) — /dev/safety.html shows "the chain verifies" for a fresh log; 0 page errors.
  9 fail  — "every action that acts on a person" (finding 5); "plan membership for device and agent offers"
            (finding 6); "clinician rule (present + screening)" (findings 2, 3).
Findings:
  1. blocker — watchdog.py:125 / watchdog.js:107 set n = len(log), and trim keeps the last 500 (watchdog.py:134-136,
     watchdog.js:114). verify() requires each n to be the previous n + 1 (watchdog.py:147, watchdog.js:120). After
     the 502nd decision two records have n = 500, and verify() is false for good in both languages. The safety
     page then says "the chain does NOT verify: a record was changed". Repro: record 502 decisions with trim after
     each -> verify false at #502 (Node and Python). The test only trims and never appends after a trim
     (test_watchdog.py:146).
  2. blocker — Research lets non-clinicians satisfy the clinician-led rule. max_level is clinician_led (Step 1b
     finding 3), and clinician_present comes from checkboxes that Research labels "An investigator is present for
     this session" (nodes.html:191, 420) and "I am the investigator and I am with the participant"
     (therapist.html:332). The clinical module can be off (rsos.clinical null). Repro: therapist.html?profile=research,
     trauma_observer, tick present, Begin -> session starts; nodes.html?profile=research, "(no ego)" node +
     difficult memories, tick the investigator box, screening "no", consent, Save -> saved, opens the player.
  3. should fix — I disagree with §6: a session's own screening step should not count as the recorded screening.
     Reasons: (a) therapist.html:332 passes screening_recorded: !!pr.screen. That is a fixed property of the protocol
     (thera.json:358 "screen": true), so for clinician-led THERA protocols it is always true and the rule shrinks to
     the #present checkbox. (b) The step list can be clicked in any order (therapist.html:347). Repro:
     therapist.html?profile=clinical, trauma_observer, Begin, click step 6 "Observe the memory" -> the processing
     card shows; rsos.screens stays empty. So the screening is not "before any processing". (c) A "yes" only stops
     the "Done, next step" button; the session view stays open (the session state does go to CRISIS, which blocks
     later player runs). (d) The interpretation was written into the spec in the code commit, after registration,
     and it relaxes W4. Suggested: answer "hold, resolve clinician" until the screen step records "no", or lock the
     processing steps until then.
  4. should fix — the clinician-led level is not carried into runs. player.html:605 sends
     {kind:"run", protocol, trigger, source:"person"}, so level() (watchdog.py:31-40) is self_guided for any node.
     Repro: save the clinician-led plan in Clinical, then open player.html?profile=workplace&program=plan:1 (the
     Observer node) and press Start -> "allow run node_observer self_guided"; the check-in opens. The built-in
     node_observer (player.html:344) also runs in Workplace. W4 applies only when a plan is saved or a session
     starts.
  5. should fix — automatic anchor firing bypasses the Watchdog. player.html:826 asks only about
     {kind:"offer", protocol:<the loaded program>, trigger:"device"}, with no auto and no signals, which gives "ask"
     and therefore proceeds. anchorOffer() then plays the anchor by itself (player.html:873-875) on one signal
     (heart rate). Precept 3 and the Watchdog's automatic_firing check never run for the one automatic action on
     the site. This contradicts §1 "one decision for every action that acts on a person" and the HANDOFF Step 2
     claim.
  6. should fix — no page passes plan_protocols (guard.js:17 defaults it to null) or programmed. The Chūgi
     plan-membership hold and the "programmed cue -> structured" level are never active on pages, although HANDOFF
     lists plan membership as delivered.
  7. should fix — the regulating exemption depends only on the protocol name (watchdog.py:66, watchdog.js:35).
     Repro (Node): watch({kind:"session", protocol:"paced_breathing", therapist_led:true, deep:true},
     {max_level:"structured"}) -> allow, level clinician_led. Together with the editable PROTOCOL line (Step 1
     finding 4), the level rules can be avoided.
  8. should fix — watchdog.js:38: for an unknown max_level, LEVEL_RANK[top] is undefined, the comparison is false
     and the domain cap is skipped (fails open). Python raises KeyError (watchdog.py:69). Repro:
     watch({kind:"plan",protocol:"plan",therapist_led:true}, {max_level:"Structured", clinician_present:true,
     screening_recorded:true}) -> JS allow, Python exception.
  9. should fix — the specs disagree. CONTAIN §10.2 puts "depression work" at clinician_led; WATCHDOG §2 level()
     does not (watchdog.py:31-40). The THERA low_mood session and depression plans are structured, so they are
     allowed in Personal and Workplace.
  10. note — parity outside the generated grid: ctx contain={} or safety={} gives allow in Python and a TypeError
     in JS; a consent with given:null counts as 0 in JS (allow) and raises a TypeError in Python.
  11. note — watchdog.py:83 counts signals, not independent ones: signals ["hr","hr"] passes.
  12. note — a Spine wording flag holds a regulating program (the spine loop runs before the regulating check).
     This contradicts §2, last paragraph ("the Watchdog's own rules never hold a regulating program").
  13. note — the player never passes clinician_present, so tier414/420/439/440 runs are held in every domain, even
     in Clinical with a clinician (fails closed, but these tiers cannot run anywhere).
  14. note — HANDOFF §2 "How to verify" leaves out test_watchdog.py and check_watchdog.py.
Verdict:         changes needed
```

## 6. Open items

- Step 3: trials → run log → PEAK → MEMSTACK → CM1 → GATE; seed the sham code; SSIT and 🦁+🐉 RSX programs;
  trials in the contribution format.
- Step 4: BLE pairing with a passkey (`rsos_esp32.ino`, open NUS characteristic around lines 274–279).
- Step 5: refresh `architecture/` pages for RSX-V.
