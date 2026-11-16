# REVIEW_R5 — fifth independent review (fix pass R4 and Low mood)

Reviewer: fifth independent agent (R5). Own clone, branch `review/r5` from `dev` at 2dacc02; no author code changed.
Read: HANDOFF_DEV.md, spec/FIXES_R4.md, spec/LOW_MOOD.md, FIXES_R3, WATCHDOG, PROFILES, CONTAIN, and the R4 review
(`origin/review/r4`, c00c867 / 48d3aff, HANDOFF §5 there).

Reproduction scripts added on this branch (not part of the author's suites):

- `review/r5/attacks.py` — 15 browser scenarios (A1–A14) in headless Chrome against `docs/` served locally, with spies
  installed *below* the output gate (as in `scripts/check_outlet.py`), so `__out` lists only what passed the gate.
  `python3 -I review/r5/attacks.py docs [chrome] [A1,A4,…]`
- `review/r5/parity.py` — Python/JavaScript parity on adversarial inputs. `python3 -I review/r5/parity.py .`

```
Step:            Fix pass R4 (spec/FIXES_R4.md; registration c7a8e39, code fea4ef6, record 2dacc02) and Low mood
                 (spec/LOW_MOOD.md; 1ec57e4, 5878bc5, 7dd8d6b, amendment in c7a8e39)
Reviewed commit: 2dacc02
Date:            2026-11-16
Checklist:
  1 pass — every "How to verify" command run on 2dacc02:
      ./scripts/check_all.sh                    exit 0: RSX 43 OK, RSX-V 128 OK, RSSO 250 OK (expected failures=1, TRIAL_LOOP
                                                T4), Toolkit 10 OK, conformance 15/15 and 15/15, board 7/7, generated
                                                files unchanged, "All checks passed."
      (cd rsxv && python3 -m pytest -q tests)   130 passed
      pytest of the eight step files            60 passed, 1 xfailed
      check_profiles / check_watchdog / check_trial_loop / check_fixes_r1 / check_fixes_r2 / check_outlet /
      check_low_mood / check_fixes_r4 (python3 -I, Chrome)   all exit 0, "fails": [], "page_errors": []
      The tests pass; see 2, 5, 9 and R5-10 for what they do not test.
  2 fail — order is right (c7a8e39 09:13 registers only specs; fea4ef6 09:29 touches no spec; 2dacc02 records). The code
      does not do what the registration says for G1, G2, G3 (R5-1, R5-2), §2 "same text, same level" / origin
      (R5-3, R5-4, R5-7), §2 "every quoted string is scanned" (R5-6), and LOW_MOOD §1 "every one of its nodes is
      clinician-led" (R5-3, R5-11).
  3 fail (process) — no numeric constant changed in rsso/rsso or docs/js between c7a8e39^ and 2dacc02 (git diff), and
      the TRIAL_LOOP T4 expected failure is unchanged. But the LOW_MOOD §2 escalation criterion was changed after its
      results were recorded (7dd8d6b): "3 checks in 7 days" became "3 different days in 7 days", which makes the
      escalation less sensitive (R5-8), while FIXES_R4 §5 says "No threshold changed".
  4 pass — no new storage keys; rsos.thera.programs records gain `level` and `memory` (registered in §2).
  5 fail — Python and JavaScript differ on adversarial input for level patterns, Spine, eventFromCheck and exit (R5-9);
      Q2's "including the reviewer's adversarial sources" is not true of rsso/tests/test_fixes_r4.py.
  6 pass with notes — check_profiles passes; the advisory sentence is shown in all seven domains (C1); the instrument
      placeholder is neutral (C3); no crisis/helpline wording added by R4 or Low mood; banned words appear only as the
      pre-existing exclusion regex in rsx/tests/test_roadmap.py:11 (00b6f4b, out of scope). Two memory-work sentences
      still show in Workplace (R5-15).
  7 pass — origin/main = 059a58f (unchanged); origin/dev = 2dacc02; this review pushes only review/r5.
  8 partial — no page errors in any scenario here (15 scenarios, 8 suites). The "Pages (main + dev)" workflow for
      2dacc02 succeeded (run 43840267797), but github.io is not reachable from this sandbox (proxy 403), so the
      development site itself was not loaded.
  9 fail — HANDOFF/FIXES_R4 claims not true in the code: "no fallback to the page session once a session is held",
      "domain re-read on storage events" (for real runs), "a hold … sends STOP to the band", "the same text keeps the
      same level", "every quoted string goes to the Spine check", Q1/Q2 "met", "No threshold changed".
Findings:
  R5-1 should fix — G2 is not fixed on the real paths; the acceptance test hides it. outlet.js:21-23 (ctxFor) prefers the
       session's own extra (`x.max_level || D.max_level`, `x.memory_work_allowed !== undefined ? x… : D…`) over the
       live RSOSDomain, and every real caller puts the load-time DOMAIN() into that extra: player.html:747 (safetyDecide
       → adopt at :629), therapist.html:358 and :368, player.html:916/:963/:970. So the recomputed RSOSDomain is never
       consulted for a run. check_fixes_r4.py:66 (G2) adopts with an empty extra `{}`, which is the only case that works.
       Repro (A3): player.html?profile=personal&program=plan:0 with a ptsd plan (Lion node, memory_work), click Start and
       Begin; session extra = {memory_work_allowed: true, max_level: "structured"}; open safety.html?profile=workplace in
       a second tab -> RSOSDomain becomes workplace/false, a fresh watch() of the run says hold, but no rsos-outlet-hold,
       the run keeps going and outputs pass for the next 6 s (vibrate [100,100] ×2, [300,100], speech "I breathe fully
       and completely…"). Same for a THERA trauma_observer session (A7: permit stays true after the switch).
  R5-2 should fix — G1/G3: a refused open() drops the held or running session and falls back to the page's declared
       session. outlet.js:30 sets `session = null` when the Watchdog refuses; permit() (:57-59) then opens the <body>
       declaration, and the 1-second re-check (:85) and the storage re-check (:86) stop watching. Repro (A4, device.html,
       Personal, dx plan saved): "Play on the band" (override) sends START; tap/type the dx node's code "..-" (held,
       nothing sent, session -> null); set rsos.safety CRISIS -> no hold event, no STOP is sent, the band keeps playing
       the run (control without the refused code: STOP is sent). Repro (A6, player): adopt an override run, quarantine
       override -> permit false (held, as G1 wants); a refused open (the heart-rate offer's vibration, :916) -> session
       "player:preview", permit("vibration") -> true. Fix direction: a refused open must not clear an existing session.
  R5-3 should fix — "same text, same level" (FIXES_R4 §2, player.html:701-724) compares exact normalised text and is
       defeated by any no-op edit: a trailing comment ("VERSION 1.0 # copy"; normText strips only whole-line comments
       while RSX also strips trailing ones, rsx.js:46-55) or ";" separators. The slot's origin is then the built-in that
       was selected. Repro (A1, Personal): dx plan (LOW_MOOD) with a Lion node; plan:0 -> block; exact copy into "swish"
       -> block; copy with " # copy" on one line -> allow, level self_guided; Start -> speech "I move, I act" and three
       vibrations in 6 s. Repro (A1b, Workplace): ptsd plan, plan:0 -> block [memory]; the same copy into swish -> allow,
       no rules. This is R4-LM2 / R4-L1 with one extra character; LOW_MOOD §1 ("every one of its nodes is clinician-led
       in the player") and the Workplace memory rule do not hold.
  R5-4 should fix — the cue origin is forgotten when another program is chosen (player.html:404 `loadOrigin = null` in
       selectProgram). Repro (A2, Personal): a tier-414 cue (therapist present, screened) in rsos.cues; click "Load into
       the player" -> block; remove the "#" and MARK lines in the same slot -> block (works); select "swish" in the
       program menu, paste the same edited text -> allow, self_guided, SAY "I let the old fear go" kept. check_fixes_r4.py
       :128 (L3) assigns loadOrigin by hand and never changes the slot, so it cannot see this. Same class as R4-L3.
  R5-5 should fix (regression introduced by R4) — the ASCII-only OBSERVER_RX (watchdog.js:28, watchdog.py:47,
       `MODE[ \t]+"observer"`) misses MODE followed by NBSP, VT, FF, U+2003 or U+3000, which RSX (JS \s tokenising)
       still compiles as mode "observer". So the FIXES_R3 "edited observer text is clinician-led memory work" rule no
       longer fires. Repro (A13, Workplace, ptsd plan with an observer node): plan:1 -> block; copy into node_observer
       with " # x" -> block (rule works); copy with MODE<U+00A0>"observer" -> allow, compiled mode observer. On 451a4df
       the same input is blocked (`\s+` matched NBSP). The patterns should follow the RSX tokeniser's whitespace.
  R5-6 should fix — Spine is not applied to the person's three futures. runFlags (player.html:726-735) scans
       $("source").value, but the run is compiled from effectiveSource() (:420-425), which writes the f0–f2 fields into
       FUTURES. Repro (A9): player.html?profile=personal&program=override, type "Hold your breath until you almost pass
       out, then take an ice bath" into the first future -> decision allow, rules []; the timeline shows it as a "see"
       event. This is the R4-L2 FUTURES case through the normal input fields.
  R5-7 should fix — the device page ignores origin and same-text levels for "Play on the band" (device.html:377-386 asks
       only {kind run, protocol}). Repro (A5): with a clinician-led ptsd plan saved, choose "Observer node" and play ->
       START sent in Workplace and in Personal; the player blocks the same built-in (L1) in both. R4-L1 named the device
       page; FIXES_R4 §2 says "whichever slot it is loaded in".
  R5-8 should fix (owner decision, process) — LOW_MOOD §2 was amended in c7a8e39 after its results were recorded
       (7dd8d6b): "3 or more checks" -> "3 or more different days". R4-LM3 found that the *message* said "several days";
       the criterion was changed instead, so 6 high checks over 2 days no longer recommend a practitioner. HANDOFF §1:
       "Thresholds are never changed after results are seen"; FIXES_R4 §5: "No threshold changed". Also stale after the
       amendment: LOW_MOOD §3 L4 ("3 high self-checks in 7 days show the recommendation"), §4 L4 result, HANDOFF_DEV.md
       :211. Either keep the registered count and fix the wording, or record this as a registered threshold change.
  R5-9 should fix — Python/JS parity (P1, Q2) on adversarial input (review/r5/parity.py; 1060 of 6037 sources differ):
       (a) Python re.I folds Unicode case, JS /i (no u flag) does not: "PROTOCOL tıer414", "PROTOCOL TİER414",
       MODE "obſerver" -> led in Python only; "# KTier 414" (Kelvin sign) -> led in JS only; Spine "ıce bath", "İce bath",
       "ſcalding" flagged in Python only. (b) eventFromCheck: "0x10" JS 16 / Py none, "0b111" and "0o7" JS 7 / Py none,
       "﻿8" JS 8 / Py none, "7_0" Py 70 / JS none, "1_000" Py 1000 / JS none, "٨" and "８" Py 8 / JS none, [8] JS 8,
       [] JS 0 / Py none. (c) exit with a malformed history: {"mode": "STABILISE", "history": null|"x"|{}|3} -> JS repairs
       and exits, Python TypeError (safety.py:195 setdefault keeps a non-list). test_fixes_r4.py's generator contains none
       of R4-L5's inputs (U+2028, U+FEFF, \x1c, "ид", non-ASCII digits), so "including the reviewer's adversarial sources"
       is not met.
  R5-10 should fix — check_fixes_r4.py does not exercise the real code paths for most items: G1/G2/G3 build a session
       with RSOSOutlet.adopt(…, {}) instead of the player's start() (hides R5-1); G3 never checks that the player run
       ends; L3 sets loadOrigin by hand (hides R5-4); LM2 tests only a byte-exact copy (hides R5-3); G5 tests only that
       the outputs are refused (see R5-13); G7 tests only an exact typed code (R5-11). Q1 "met" rests on these.
  R5-11 note — G7 partial. Repro (A14, dx plan, Personal, device.html): typed "..-" -> held; typed "..- ..-" or "..- -",
       and the built-in "Lion + Dragon" button (device.html:371-374 passes `{}` flags, so the typed-code lookup at :362 is
       skipped) -> START sent with the dx node's Lion pattern.
  R5-12 note — G6 covers only UGCL.feel, voice and the band. Direct output paths still play without outlet.js:
       device.html:459-462 (carrier), glyphs.html:128 and :172, trials.html:310. Repro (A11): block js/outlet.js, CRISIS,
       device.html "carrier" Play -> two sources start.
  R5-13 note — G5 makes these outputs permanently silent rather than "following the firing rules": the posture cue
       (device.html:422) and the heart-rate offer (player.html:916) pass one signal, so p3 always asks and they never
       vibrate; agent status codes (agents.html:195) are never confirmed. Safe, but a silent feature change; say so in
       the spec or drop the code.
  R5-14 note — Spine word lists are evaded by spacing or look-alike letters (A10: "ice  bath", "ice<TAB>bath",
       "ice<NBSP>bath", Cyrillic "іce bath" -> allow; "ice bath" -> block). Record as a known limit, or normalise
       whitespace before matching.
  R5-15 note — Workplace still shows memory-work wording: night.js:44 summary "…; a nightmare gets the safety code."
       and therapist.html:137 "Also on this page: … re-living with the symbol …" (A12).
  R5-16 note — the run's output session starts before the check-in dialog (player.html:629 adopt, then askCheckin).
       If the dialog stays open longer than the program + 120 s, the hold fires while `run` is null and the run then
       starts with a held session (silent run, no message). Repro (A8) with the window shortened to 2 s.
  R5-17 note — the "read-only" test accessors are not read-only: RSOSOutlet.session() (outlet.js:133) returns the live
       session object, so `.held = false` or `.action` can be changed from any script. Page code is trusted (FIXES_R4
       §5), so this is about the wording.
  R5-18 note — process: results text in the code commit message (fea4ef6: "fails on 451a4df, passes now"); record commit
       26 s after the code commit. LOW_MOOD L1: check_low_mood checks Clinical, Personal, Performance, Workplace only
       (Research with the module on was verified by R4 at 451a4df; nodes.html dx code unchanged since).
Verdict:         changes needed — R5-1 to R5-10. The structural claims of FIXES_R4 §1 (G1–G3) and §2 (origin, same text,
                 every quoted string) do not hold on real page paths, R4 itself introduced a level regression (R5-5), and
                 the R4 acceptance test checks synthetic sessions that avoid the defects.
```

## What could not be tested

- The development site at github.io (sandbox proxy refuses it); only the workflow status was checked.
- Real hardware: band behaviour is inferred from the lines the page sends (a fake transport) and from the firmware
  parser (`firmware/rsos_core/rsos_core.cpp:38-40`, `rsos_esp32.ino:250, 290`). G9 holds against that parser: any
  line that sscanf reads as START begins with START after JS `\s`.
- Real motion sensors and heart-rate straps (R5-13 is from the code and from Watchdog decisions).
- Audible output: spies record calls below the gate; nothing was listened to.
