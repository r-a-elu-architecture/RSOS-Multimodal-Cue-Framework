# REVIEW_R6_CHECK — targeted check of fix pass R6

Reviewer: independent agent (R6 check). Own clone `/home/claude/review-r6c`, branch `review/r6-check` from `dev` at 0304a0c
(`origin/dev` was 0304a0c when checked). No author code changed. This is a short, targeted check, not a full review.

```
Step:            Fix pass R6 (spec/FIXES_R6.md; registration 3966b05, code dbb393c, records 0304a0c) against REVIEW_R6.md
                 (origin/review/r6, b423035), findings R6-1 to R6-11
Reviewed commit: 0304a0c
Date:            2026-11-16
```

Reproduction (on this branch):

- R6 scripts rerun unchanged from `origin/review/r6`: `review/r6/attacks.py` (C1-C10), `ble_checks.sh` + `gap_sim.cpp`.
- New: `review/r6c/probe.py` (P1 run lock, P2 lineage over-blocking across every archetype, P3 fold parity over all code
  points U+0000-U+3FFFF in Chrome vs Python and fold performance), `review/r6c/plans_all.js`, `review/r6c/c7.py` (R6-9
  message), `review/r6c/plans.js` (copy of the R6 one).
  `python3 -I review/r6c/probe.py <abs docs dir> /usr/bin/google-chrome [P1,P2,P3]`
- Upstream sources read for the firmware findings (fetched by `git clone` of the public repositories): Arduino-ESP32
  `libraries/BLE/src/BLEDevice.cpp` and `BLECharacteristic.h` at tags 2.0.17 and 3.0.7; ESP-IDF v5.1.4 Bluedroid
  `stack/smp/smp_api.c`, `stack/smp/smp_act.c`, `stack/btm/btm_ble.c`.
- Author checks rerun: `scripts/check_fixes_r6.py` ("fails": [], "page_errors": []), `rsso` `test_fixes_r6.py` +
  `test_ble_pairing.py` 17 passed, `link_test` ok 52, `scripts/gen_fold_table.py` regenerated with Python 3.13.18 /
  Unicode 15.1: no diff.

## Findings R6-1 to R6-11

| ID | Status | Evidence |
|---|---|---|
| R6-1 blocker (program changes mid-run) | **Fixed** | C1a/C1b can no longer run: `#program` and `#source` are `disabled` during the run (Playwright: "element is not enabled"). P1a: menu change forced by script (value + `change` event) during an allowed `ssit_calm` run with the dx plan → run stopped, "The program changed while running; start it again.", only output after the change `vibrate:0`. P1b: editor text replaced by the held node and `recompile()` called (the cue "Load into the player" path does exactly this, player.html:1149) → same stop, no held output. Control C1c: CRISIS mid-run still stops it. P1c: editor set to an allowed text while the compiled timeline is still the held node (Start+Begin before the 250 ms debounce) → held at Start (protocol checked from `timeline`). No `storage`/`hashchange` listener changes the program; keyboard only has Escape (stop). |
| R6-2 (Jaccard share) | **Fixed** | `share = shared/|origin|` (lineage.js:79). C2: exact copy and copy + 1..9 own lines all `block clinician_led` from `plan:0`; run held. C2b unchanged (held). |
| R6-3 (a) `$future`, (b) accents/look-alikes, (c) split sentence | **Fixed** for the tested inputs | C5 → block (text with `$future` removed now counted); C3 → block; C4 → block. |
| R6-4 (over-blocking by containment) | **Fixed** | C6 with frame "I am steady": `ssit_higher` allow, own "I am steady today" allow; only the built-in `node_lion` held (the recorded consequence). |
| R6-5 (held sessions never closed) | **Fixed** (device reproduced; player anchor and trials by reading) | C8: after CRISIS→NORMAL the code sends `LOAD`/`H`/`START`, message "Stopped by the Watchdog.", sessions `["device:code"]`. Player anchor keeps `anchorHandle` and closes it on hold (player.html:665, :971); trials keeps `trialHandle` (trials.html:204-213). |
| R6-6 (fold parity, Unicode versions) | **Fixed** | C9: 0 differences (Chrome 153 vs Python 3.13). P3: every code point U+0000-U+3FFFF (except surrogates) folded in Chrome and in Python: 14 chunks, 0 differ. |
| R6-7 (3.x `getValue`) | **Fixed** | Arduino-ESP32 3.0.7 `BLECharacteristic.h:66 String getValue();`, 2.0.17 `std::string getValue();`; `String v = c->getValue().c_str();` (rsos_esp32.ino:274) compiles with both stub majors (`ble_checks.sh`: 2.x and 3.x compile). |
| R6-8 (attempts on the static passkey) | **Partly fixed** | B6 and B7 work in the sketch logic (`gap_sim`: no passkey screen with the window closed; success without KEY_EVT from an unbonded address refused). **B5 has no effect on the device**: see R6c-1. Passkey-entry attempts outside the window are still unlimited; BLE_PAIRING §4 as amended ("the window now also limit[s] pairing attempts") is not true of the code. |
| R6-9 (failed built-in download) | **Fixed** | `c7.py` (tier579_glyph.rsx → 404, dx plan, `override`): `RSOSLineage.strict` true, message ends "Some built-in programs could not be loaded, so the content check is strict on this page." (player only; the device page does not add the sentence — not required by §2.) |
| R6-10 (a) write without response | **Fixed** | rdp.js:56 writes with response; RX has `PROPERTY_WRITE` (rsos_esp32.ino:407). |
| R6-10 (b) link loss by sampling | Not fixed (not registered) | loop() still samples `bleConnected`. |
| R6-10 (c) ring / `link` race | Partly fixed | Ring emptied when loop() sees the link lost (:430), not "when a new host connects" (B9 wording); a disconnect+reconnect between two samples still carries bytes over (only fed while `linkAuthed`). `link` still written by two tasks without a lock. |
| R6-10 (d) refused re-pairing deletes the bond | Not fixed (not registered) | :320 unchanged. |
| R6-11 (checks only at Start) | **Fixed** | `check_fixes_r6.py` changes the program by menu and editor after Begin (C1a/C1b) and covers the short-frame case (C6). |

## New findings

```
R6c-1 should fix (Step 4) — B5 ("pairing requests outside the window are refused at the request") cannot work as written.
      firmware/esp32/rsos_esp32/rsos_esp32.ino:310-312, :267, :398.
      (1) On the normal path the event never fires. onConnect (:267) calls esp_ble_set_encryption(..., ESP_BLE_SEC_ENCRYPT_MITM)
          for every connection. In Bluedroid (ESP-IDF v5.1.4 btm_ble.c:1586) a peripheral then calls SMP_Pair(), which sets
          SMP_PAIR_FLAGS_WE_STARTED_DD (smp_api.c:160). When the central answers with a Pairing Request, smp_proc_pair_cmd
          (smp_act.c:585-630) takes the "pairing started with this side (slave) sending Security Request" branch and sends
          the Pairing Response directly; SMP_SEC_REQUEST_EVT (ESP_GAP_BLE_SEC_REQ_EVT) is raised only in the other branch
          (smp_act.c:591, peer-initiated without our Security Request).
      (2) When it does fire, the Arduino library has already accepted it. BLEDevice::gapEventHandler answers
          ESP_GAP_BLE_SEC_REQ_EVT with esp_ble_gap_security_rsp(addr, true) when no BLESecurityCallbacks are set
          (Arduino-ESP32 3.0.7 BLEDevice.cpp:199-209; same in 2.0.17), and calls the custom handler (the sketch's gapEvent,
          registered with setCustomGapHandler, :398) only afterwards (BLEDevice.cpp:256-258). The sketch sets no security
          callbacks. SMP_SecurityGrant ignores a second answer once the state has left SMP_STATE_WAIT_APP_RSP
          (smp_api.c:279-283), so the sketch's `false` is dropped.
      Effect: R6-8's main point stands — any device in range can run passkey-entry attempts outside the window and after
      the failure limit; each failure is only counted (on_auth_fail) and dropped. link_test checks LinkPolicy::accept_request
      in isolation, so it passes; gap_sim calls gapEvent directly, so it cannot see this either.
      Reproduction: reading only (no board). Fix direction: decide at connection, not at the request — in onConnect, when
      the window is closed (or the limit reached) and the peer is not bonded, do not call esp_ble_set_encryption and
      disconnect; and/or register BLESecurityCallbacks whose onSecurityRequest() returns link.accept_request(millis()).
      Correct the §4/B5 record until confirmed on a board.

R6c-2 note (Step 4, availability) — B7 and any address-based fix rest on the address Bluedroid reports for a bonded host
      that uses a resolvable private address (every current phone). If AUTH_CMPL carries the RPA rather than the identity
      address, every bonded phone that reconnects without new keys is refused and disconnected (fails closed, recorded in
      FIXES_R6 §7). This is a likely day-one breakage of the normal reconnect, not an edge case; it should be the first
      thing confirmed on a board.

R6c-3 note — the recorded share consequence (FIXES_R6 §2: built-in Lion held with a dx plan) also applies to the
      Observer: P2 over every archetype default node × {stress, depression, ptsd} (Personal profile, 16 built-ins and two
      own programs): with an OBSERVER node and either depression or ptsd, the built-in node_observer becomes
      clinician-led (block); with LION + depression, node_lion. No other built-in is affected by any plan, no built-in is
      affected by any non-clinical (stress) plan, and an ordinary own program ("I breathe slowly and I am here", haptic,
      exhale) is allowed under every plan. (My second own program reused the planner-default sentence "Spine straight,
      warmth in the belly" and was held under every depression plan — correct by the rule.) Record the Observer case with
      the Lion one.

R6c-4 note — player decision vs. played timeline. start() decides on runFlags() (the editor text, effectiveSource()) and on
      `timeline.protocol`, but plays `run.tl = timeline`, which can lag the editor by the 250 ms debounce (player.html:871).
      P1c could not exploit it (the held node was caught by protocol identity, and F3 would stop the run when the debounced
      recompile lands), but the content check and the played content are still two different inputs. Compiling once at
      Start (recompile() synchronously before the decision) would remove the gap.

R6c-5 note — trials: after a hold, the open session UI stays; "Play your anchor" then plays nothing (the gate refuses, no
      session) with no new message beyond the one prepended to the first `.stage` (trials.html:205). Fails closed;
      by reading only.
```

Checked and fine: finish() always calls `lock(false)` (Escape, Stop, hold, F3 stop, completion — P1a/P1b/P1d/P1e all
show the fields enabled after the run); a run started from the device offer (`start("device")`) locks and unlocks the
same way, and a second run starts normally (P1d). `lock(false)` cannot re-enable a field that was disabled for another
reason: none of the seven locked fields is disabled anywhere else in player.html. Fold performance in Chrome 153:
20 KB 2 ms, 200 KB 15 ms, 1 MB 78 ms; `levelOfProgram` on a 200 KB SAY 11 ms; `RSOSLineage.flags` on it 13 ms.
Generated fold tables are current. Ring clearing and `bonded()` are logically correct for what they do.

Process: registration 3966b05 (14:24, spec/FIXES_R6.md only) after the review b423035 (14:18) and before code dbb393c
(14:43; touches no spec/ or HANDOFF file; message describes changes, no results); records 0304a0c (HANDOFF_DEV.md and
spec/FIXES_R6.md only). Order respected. The record commit follows the code by 21 s, so the results were obtained before
the code was committed — allowed by the rule as stated, noted only.

## What could not be tested

- Real hardware and radio: no ESP32, no BLE. R6c-1 and R6c-2 come from reading the sketch against the Arduino-ESP32
  (2.0.17, 3.0.7) and ESP-IDF v5.1.4 Bluedroid sources; the exact versions a builder uses may differ (Arduino-ESP32 3.x
  ships ESP-IDF 5.1/5.3; NimBLE builds not considered). Whether AUTH_CMPL carries identity or private addresses was not
  determined.
- The development site on github.io (not reachable from here); other browsers than Chrome 153 (fold parity was shown for
  Chrome and Python only; the table makes other engines' Unicode versions irrelevant by construction).
- Audible output and real vibration (spies below the gate), real heart-rate straps, the automatic anchor firing and the
  trials hold path (read, not run).
- Storage events from a second real tab were not driven; by reading, player.html has no `storage` listener that changes
  the program or the plan in use mid-run, and lineage reads plans at decision time only.
- Full suites (`check_all.sh`, all ten browser checks) were not rerun; only the R6-specific author checks listed above.

Verdict: **changes needed, minor** — R6-1 (the blocker) is fixed and holds against every page path tried; R6-2 to R6-7,
R6-9 and R6-11 are fixed; R6-8 is only partly fixed because B5 cannot take effect on the device (R6c-1, should fix — or
record that out-of-window passkey attempts remain unlimited and drop the §4 claim). Notes R6c-2 to R6c-5 need no code
before the board test, but R6c-2 should be the first board check.
