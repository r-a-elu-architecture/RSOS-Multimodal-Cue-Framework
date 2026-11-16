# REVIEW_R6 — sixth independent review (fix pass R5 and Step 4 BLE pairing)

Reviewer: sixth independent agent (R6). Own clone `/home/claude/review-r6`, branch `review/r6` from `dev` at c3b1a55
(`git fetch` before writing: `origin/dev` still c3b1a55, `origin/main` 059a58f). No author code changed.
Read: HANDOFF_DEV.md, spec/FIXES_R5.md, REVIEW_R5.md (`origin/review/r5`, c21e634), spec/BLE_PAIRING.md, FIXES_R4 (with
its corrections), LOW_MOOD, WATCHDOG, CONTAIN, DEVICE_PROTOCOL.

Reproduction scripts on this branch (not part of the author's suites):

- `review/r6/attacks.py` — 13 browser scenarios (C1–C10) in headless Chrome against `docs/` served locally, through real
  page paths: the program menu (`select_option`), typing in the editor (`fill`, which fires the page's input handler),
  the futures fields, Start and Begin, the device page's Play and code buttons. Spies sit below the output gate (as in
  `scripts/check_outlet.py`); the device page's transport is a fake that applies the same START gate as
  `docs/js/rdp.js:28`. Plans come from `docs/js/nodes.js` via `review/r6/plans.js`.
  `python3 -I review/r6/attacks.py docs [chrome] [C1,C3,…]`
- `review/r6/ble_checks.sh` + `review/r6/gap_sim.cpp` — host checks of the ESP32 sketch: (1) the stubs with the
  Arduino-ESP32 3.x return type of `BLECharacteristic::getValue()`; (2) the sketch's own GAP handler driven with event
  sequences (decision logic only, not Bluedroid). `sh review/r6/ble_checks.sh .`
- The R5 scripts (`review/r5/attacks.py`, `review/r5/parity.py`) were re-run unchanged on c3b1a55.

```
Step:            Fix pass R5 (spec/FIXES_R5.md; registration d633b5a, code 9ab5f78, record c3b1a55) and Step 4 BLE pairing
                 (spec/BLE_PAIRING.md; registration c898386, code 661165e, record 4f4b6d8)
Reviewed commit: c3b1a55
Date:            2026-11-16
Checklist:
  1 pass — every "How to verify" command on c3b1a55:
      ./scripts/check_all.sh                    exit 0: RSX 43 OK, RSX-V 128 OK, RSSO 264 OK (expected failures=1, TRIAL_LOOP
                                                T4), Toolkit 10 OK, conformance 15/15 and 15/15, board 7/7, generated files
                                                unchanged, "All checks passed."
      (cd rsxv && python3 -m pytest -q tests)   130 passed
      pytest of the ten step files              74 passed, 1 xfailed
      check_profiles / check_watchdog / check_trial_loop / check_fixes_r1 / check_fixes_r2 / check_outlet /
      check_low_mood / check_fixes_r4 / check_fixes_r5 (python3 -I, Chrome)   all exit 0, "fails": [], "page_errors": []
      review/r5/attacks.py: A1–A14 show holds (A9 script error only because the run no longer starts);
      review/r5/parity.py: "level diffs: 0 of 6037".
      The suites pass; see 2, 5, 9 for what they do not test.
  2 fail — order is right: d633b5a (10:57, specs only) < 9ab5f78 (11:22, no spec file touched) < c3b1a55 (records);
      c898386 (09:35, spec only) < 661165e (09:52) < 4f4b6d8. But the code does not do what the registrations say:
      FIXES_R5 §2 "a run inherits … whose content it mostly shares (shared / all)" is implemented as Jaccard (R6-2);
      "the run's elements come from the source actually compiled for the run" holds only at Start (R6-1); §3 parity
      (R6-6); BLE_PAIRING P4/§4 "the failure limit reduces" passkey recovery (R6-8); B2 for 3.x (R6-7).
  3 pass — no numeric limit in rsso/rsso or docs/js changed between 2dacc02 and c3b1a55 besides the registered new
      constants SHARE = 0.8 and LONG = 8 (lineage.js:15) and the registered R5-8 restoration (safety.html: 3 checks in 7 days,
      any days; LOW_MOOD §2 restored in d633b5a). link policy constants (120 s, 3, 4, 95) match BLE_PAIRING P3–P7.
  4 pass — no new storage keys; outlet sessions and lineage are in memory only.
  5 fail — the registered inputs give 0 differences, but fold() is not identical across the two runtimes: Python 3.13
      unicodedata is Unicode 15.1, Chrome 153 / Node ICU 78 are Unicode 16+/17, so NFKC differs for the Unicode 16
      "outlined" letters and digits (R6-6). eventFromCheck: a 400-digit string gives distress inf in both (accepted as
      "ASCII digits"; JSON.stringify writes null, Python json writes Infinity) — note only.
  6 pass — check_profiles passes; no crisis/helpline/hospital/depressive wording added to non-clinical views by these
      commits (added lines contain only internal mode IDs); banned words appear only as the exclusion regex in
      rsx/tests/test_roadmap.py:11 (pre-existing); the pairing text (device.html, BOARD_KIT §Pairing) is neutral and contains
      no secret (the BOARD_KIT passkey "482913" is an example output line). R5-15 sentences hidden in Workplace (A12).
  7 pass — origin/main = 059a58f (unchanged); origin/dev = c3b1a55; this review pushes only review/r6.
  8 partial — no page errors in any scenario (13 scenarios here, 15 from R5, 9 suites). github.io is not reachable from
      this sandbox, so the development site itself was not loaded.
  9 fail — claims not true in the code: HANDOFF "a run inherits the level of a plan node … whose content it mostly
      shares" and "player and device page alike" (R6-1, R6-2, R6-4); lineage.js:4 "comments, separators, spacing and
      look-alike letters do not change them" (R6-3); FIXES_R5 §6 Q1/Q2 "met" (R6-1, R6-6); BLE_PAIRING §4 "The window (P3), the
      failure limit (P4) and NEWKEY reduce this" (R6-8); §5 B2 "compiles … for Arduino-ESP32 2.x and 3.x" (R6-7).
Findings:
  R6-1 blocker — the program changes under a running, allowed session. player.html:857 recompiles on every editor/futures
       input and player.html:855 (program menu change → selectProgram → recompile, :435-438) replaces the global `timeline`
       while `run` is active; frame() (:578-590) reads `timeline.events` every frame. The run's gate session (:641) keeps
       the action and flags computed at Start, and the 1-second re-check (outlet.js:106, :66) re-watches that stored action,
       so nothing notices. The menu and editor stay enabled during a run (only #start is hidden, :83-84).
       Repro C1a (Personal, diagnosed-depression plan, Lion node): plan:0 -> block (clinician_led). Select ssit_calm, Start,
       Begin; during the run select "plan:0" in the menu -> run continues with timeline node_lion, 0 hold events, session
       still "ssit_calm"; in the next 12 s: vibrate [100,100] ×2, [300,100], speech "I breathe fully and completely, and I
       hold my ground". Repro C1b (Workplace, ptsd plan): start ssit_calm, type the observer node's program into the editor
       -> timeline mode "observer", speech "Nothing binds. Nothing holds. Only observed", vibration [300,100], no hold.
       Control C1c: a CRISIS set during the run is caught (run ended, 1 hold event). Neither check_fixes_r5 nor
       review/r5/attacks.py changes the program after Begin. Fix direction: compile the run's timeline once at Start and keep
       it in `run`, or lock the menu/editor/futures/breath inputs while running, or re-derive flags from the playing timeline.
  R6-2 should fix — "mostly shares" is Jaccard, not "shared / all", so adding lines lowers the level. lineage.js:64 computes
       shared / (|run| + |origin| − shared); FIXES_R5 §2 registers "at least 80% the same as the origin's (shared / all)".
       A superset of the origin therefore falls below 0.8 by adding one quarter of its size. The planner's default Lion
       node has one distinctive element (the default K "Spine straight, warmth in the belly"; all else is in built-ins).
       Repro C2 (Personal, dx plan): copy plan:0 into ssit_calm -> block; reword that one K sentence -> still block (11/13);
       add one PHASE with one SAY of one's own -> allow, self_guided; Start/Begin: "I move, I act", three vibrations, "I
       breathe fully and completely, and I hold my ground" — 11 of the node's 12 elements play. Related: the built-in
       node_lion (Jaccard 0.65 with that node, same tier, code, frame) is self_guided with the dx plan in the player and
       plays on the band (C10: "Lion node" START sent), while its code "..-" alone is held (C10) — LOW_MOOD §1 "every one
       of its nodes is clinician-led in the player and on the device page" rests on one planner-default sentence.
       (A ptsd observer node is still held after any number of added lines because the edited-observer rule applies, C2b.)
  R6-3 should fix — lineage elements miss text that the run plainly says. (a) lineage.js:25 skips every event whose text
       still contains "$future" after substitution, so a future field set to "$future" hides any sentence put inside FOR
       FUTURE. Repro C5 (Personal, dxOwn plan "I am steady and I choose my next step"): type "$future" in the first futures
       field, in the swish slot paste the node with its frame inside FOR FUTURE (tier renamed, code changed) -> allow,
       self_guided; speech "I am steady and I choose my next step $future". (b) Spelling that keeps the words: accents and
       look-alike letters outside the fold list (U+0251, U+0585, ę, ï) — C3 -> allow, speech "I am stéady and I choose my
       next stép"; (c) one sentence split over two SAY events (whole-word containment only works one way, lineage.js:65-69)
       — C4 -> allow, speech "I am steady and" / "I choose my next step". (b) and (c) also need the tier renamed and the code
       changed, so they sit near the recorded limit (§2, §6); (a) does not — the exact sentence is in the compiled program.
       lineage.js:4 "look-alike letters do not change them" holds only for the listed letters; record it or fold further.
  R6-4 should fix (over-blocking) — a distinctive text of 8+ characters held as whole words inside any longer text also
       holds built-ins and the person's own programs. Repro C6 (Personal, dx plan whose Lion node has the frame "I am
       steady"): built-in ssit_higher (an SSIT trial arm; its text "I am steady and clear") -> block, clinician_led; an own
       program SAY "I am steady today" -> block. Other built-ins allowed. The R5 control ("every built-in allowed with no
       plan saved", check_fixes_r5.py:213) cannot see this. Distinctiveness is tested by exact element (lineage.js:50), but
       inheritance by containment (:69); test containment against built-in texts too.
  R6-5 should fix — a held session that its page never closes blocks that page until reload, silently. O3 keeps held
       sessions "until its page closes it"; device.html:359 only sends STOP on hold and never closes runHandle;
       player.html:957 (automatic anchor, 30 s) and trials.html:209 (30 min) adopt without keeping a handle.
       Repro C8 (device.html, Personal): Play on the band "override" -> START; set CRISIS -> STOP (correct); back to NORMAL;
       type code "-.-" and Play -> LOAD/H lines sent but START refused, the message still reads "Playing Override Protocol
       (52 s)", sessions ["override held", "device:code"]; control on a fresh page: START sent. Only another "Play on the
       band" (which closes runHandle) or a reload recovers.
  R6-6 should fix — fold() differs between Python and the browser on Unicode 16+ characters (FIXES_R5 §3 "identical in both
       languages"). Python 3.13 unicodedata 15.1; Chrome 153 normalises the outlined letters/digits (U+1CCD6…U+1CCF9).
       Repro C9: "<outlined ICE> bath" -> Chrome spine temperature_extreme, Python none; "PROTOCOL tier<outlined 414>" ->
       Chrome therapist_led, Python not; MODE "<outlined O>bserver" -> folds to "observer" only in Chrome. The Python side
       (RSX-V agents) is the weaker one. The parity test runs Node, not the browser, and generates no such characters.
       Fix direction: reject or map code points unassigned in the older table, or pin both to one Unicode version.
  R6-7 should fix (Step 4) — the sketch no longer compiles on Arduino-ESP32 3.x, and the stubs hide it. rsos_esp32.ino:274
       `std::string v = c->getValue();` — in Arduino-ESP32 3.x (Bluedroid BLE) BLECharacteristic::getValue() returns
       Arduino `String`, which has no conversion to std::string (the well-known "conversion from 'String' to non-scalar
       type 'std::string'" error). Before 661165e the line was `String v = c->getValue().c_str();`, which works on both.
       stubs/BLEDevice.h:19 returns std::string for both majors, so B2's "3.x" builds prove nothing for this call.
       Repro: `sh review/r6/ble_checks.sh .` -> 2.x compiles; 3.x: rsos_esp32.ino:274:32 error. (From API knowledge, not from
       the real headers: they could not be fetched here.)
  R6-8 should fix (Step 4) — the window and failure limit do not limit attempts to learn the static passkey. Nothing in
       the sketch refuses a pairing before the passkey stage: P3/P4/P5 are applied only after AUTH_CMPL success with
       KEY_EVT (rsos_esp32.ino:305-313). Outside the window, or after 3 failures, any device in range can still run LE SC
       passkey-entry attempts without limit; with a static passkey an active initiator learns it bit by bit in about 20
       attempts (the weakness BLE_PAIRING §4 records for a passive observer), then bonds at the next power-on. With
       -DRSOS_DISPLAY, ESP_GAP_BLE_PASSKEY_NOTIF_EVT (:304) shows the passkey on the screen for any initiator at any time,
       window closed or not. Also: an AUTH_CMPL success without KEY_EVT is treated as a bonded reconnect (:308, :312) and
       skips window and bond limit; whether Bluedroid lets a peer complete SC passkey pairing with no key distribution
       under ESP_BLE_ONLY_ACCEPT_SPECIFIED_AUTH is not verified here (if it rejects the missing bond bit, this path is
       closed; it should not rest on that). Repro (logic only): review/r6/gap_sim.cpp — 50 failed attempts outside the
       window all reach PASSKEY_NOTIF/AUTH_CMPL; window closed -> keyScreen = 1; window closed, success without KEY_EVT ->
       linkAuthed true; control with KEY_EVT -> refused. Fix direction: disconnect unbonded peers on connect when the window
       is closed (check the address against the bond list), show the passkey only inside the window, and say in §4 that P4
       limits bonds, not guesses.
  R6-9 note — one failed protocol fetch makes lineage permanently strict. lineage.js:35 sets `builtin` only when every
       fetch succeeds, otherwise every origin element counts as distinctive for the page's life. Repro C7 (Personal, dx
       plan, tier579_glyph.rsx -> 404): interrupt_only and override -> block clinician_led (control with all fetched: allow).
       Fails closed, as intended, but unrecorded and unexplained to the person ("clinician-led work").
  R6-10 note (Step 4, hardware-dependent) — (a) The web page sends commands with writeValueWithoutResponse (rdp.js:56);
       writes without response to an ENC_MITM characteristic are dropped silently before pairing, so "HELLO" sent right
       after connect may be lost and the page reports "did not answer as an RSOS band" until the OS pairing (triggered by
       the CCCD write in startNotifications or the band's security request) completes. (b) loop() detects link loss only by
       sampling `bleConnected` (rsos_esp32.ino:418); a disconnect and reconnect between two samples would skip
       core.link_lost (P8), unlikely given advertising intervals. (c) `link` is written by loop() (USB PAIR) and the
       Bluetooth task without a lock; rxRing bytes of a dropped host can be fed to the next authenticated host's buffer.
       (d) A refused re-pairing of an already bonded host removes its existing bond (:310).
  R6-11 note — FIXES_R5 §6 Q1 "covers every R5-1 to R5-7 … reproduction" is true, but check_fixes_r5.py, like R4's check,
       checks the state at Start only; no check changes the program, the futures fields or the menu after Begin (R6-1), and
       none saves a plan with a short generic frame (R6-4).
Verdict:         changes needed — R6-1 (blocker) lets held clinician-led and memory-work content play through the normal menu
                 or editor during an allowed run; R6-2 to R6-8 should be fixed or recorded. The gate's session list (O1, O2,
                 O5), the refused-open fix, Spine on futures and compiled words, R5-15 and R5-8 work as registered on the
                 paths tested.
```

## What could not be tested

- Real hardware: no ESP32, no BLE radio. Pairing, KEY_EVT/AUTH_CMPL ordering, whether the new bond is stored before
  AUTH_CMPL (`bondCount() - 1`), how Bluedroid applies ESP_BLE_ONLY_ACCEPT_SPECIFIED_AUTH to a peer without the bonding
  bit or without key distribution, and the operating systems' pairing dialogs. R6-7, R6-8 and R6-10 are from reading the
  sketch against the Bluedroid / Arduino-ESP32 API as I know it; the ESP-IDF and Arduino-ESP32 sources could not be
  fetched (proxy 403), so the 3.x `getValue()` return type and the SMP behaviour are stated with that uncertainty.
  Arduino-ESP32 3.3+ NimBLE builds were not considered (recorded in BLE_PAIRING §4).
- The development site at github.io (unreachable from this sandbox).
- Audible output and real vibration: spies record calls below the gate; band behaviour is inferred from the lines sent to
  a fake transport with rdp.js's START gate.
- Real motion sensors, heart-rate straps and automatic anchor firing (R6-5's player and trials paths are from the code;
  only the device path was reproduced).
- Other browsers' Unicode versions (R6-6 used Chrome 153 and Node ICU 78).
