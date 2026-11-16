# FIXES_R6 — fixes from the sixth independent review

Status: registered 2026-11-16 (3966b05), before code; code dbb393c; results in §7. Review: branch `review/r6`, commit b423035 (reviewed dev at c3b1a55;
1 blocker, 7 should fix, 3 notes). This registration amends FIXES_R5 §2 and §3 and BLE_PAIRING P3, P4 and §4 as stated
below.

## 1. The running program cannot change (R6-1, blocker)

| ID | Rule |
|---|---|
| F1 | At Start, after the check-in, the player keeps the compiled timeline it decided on in the run (`run.tl`). Every frame reads `run.tl`, never the editor's timeline. |
| F2 | While a run plays, the program menu, the editor, the futures fields and the breath fields are disabled. They are enabled again when the run ends. |
| F3 | A change of program or text that arrives during a run anyway (a script, another input path) is not played. If it reaches `timeline`, the next frame stops the run with the message "The program changed while running; start it again." |

## 2. Lineage (amends FIXES_R5 §2; R6-2, R6-3a, R6-3c, R6-4, R6-9)

- **Share** is `shared / |origin|`: a run that contains at least 80% of an origin's elements inherits its flags, however
  much it adds. The registered "(shared / all)" read as Jaccard in R5's code; this is the corrected reading.
  - Consequence, recorded: with a diagnosed-depression plan, the built-in Lion and Observer nodes are held, the same as
    the plan's nodes. LOW_MOOD §1 says every node of such a plan is clinician-led, and this makes it so.
- **Text inside futures loops** is read with each `$future` removed, not skipped.
- **Joined text**: a distinctive text also counts when it appears as whole words in the run's texts joined in event
  order, so a sentence split over two events still counts.
- **Containment is checked against the built-ins too**: a distinctive text that appears as whole words inside the joined
  text of any built-in program counts only as an exact element, never by containment.
- **Failed built-in download (R6-9)**: if some built-in programs could not be loaded, lineage stays strict and says so.
  The player shows "Some built-in programs could not be loaded, so the content check is strict on this page."

## 3. Folding pinned to one Unicode version (amends FIXES_R5 §3; R6-3b, R6-6)

- `fold()` no longer calls the language's own NFKC. It uses a generated table, `scripts/gen_fold_table.py`, which
  writes `rsso/rsso/foldtable.py` and `docs/js/foldtable.js` from Python's Unicode data (15.1):
  - Every code point whose NFKD form, with nonspacing marks removed, is non-empty printable ASCII maps to that ASCII.
  - Every nonspacing mark maps to nothing.
  - The FIXES_R5 look-alike letters are kept.
  - Added look-alikes: ɑ→a, ɡ→g, ɩ→i, ȷ→j, օ→o, ս→u, ց→g, ⅼ→l.
- A code point not in the table is kept as it is. Folding is therefore identical in Python and in any browser,
  whatever their Unicode version.
- The other steps of FIXES_R5 §3 are unchanged: line ends, zero-width removal, whitespace and controls to a space,
  collapsed spaces, ASCII lowercase.
- `scripts/check_all.sh` checks that the generated files are current.

## 4. Sessions a page leaves held (R6-5)

| ID | Rule |
|---|---|
| H1 | Every page that opens a session keeps its handle. On `rsos-outlet-hold` it closes its own held sessions and says so. Pages: the device page ("Stopped by the Watchdog."), the player's automatic anchor, and trials. A new action after the hold is decided afresh. |

## 5. Wristband pairing (amends BLE_PAIRING P3, P4, §4; R6-7, R6-8, R6-10)

| ID | Rule |
|---|---|
| B5 (R6-8) | **Pairing requests outside the window are refused at the request.** On `ESP_GAP_BLE_SEC_REQ_EVT` the band answers `esp_ble_gap_security_rsp(addr, accept)`, with accept only while the window is open (P3) and the failure limit is not reached (P4). Already-bonded hosts reconnect by encryption with their stored key, without a pairing request. Every failed pairing counts toward P4. |
| B6 (R6-8) | The passkey is shown on the screen only while the window is open. |
| B7 (R6-8) | A successful authentication without a key exchange is accepted only if the peer's address is in the bond list. Otherwise it is refused and disconnected. |
| B8 (R6-7) | The receive handler reads the value as `String v = c->getValue().c_str();`, which works on 2.x (`std::string`) and 3.x (Arduino `String`). The stubs return `std::string` for 2.x and `String` for 3.x. |
| B9 (R6-10) | The ring buffer is emptied when a new host connects. The web page writes with response where the browser offers it, so a write refused before pairing is reported instead of lost. |
| §4 | BLE_PAIRING §4 is corrected: P4 and the window now also limit pairing attempts, and so passkey guesses, to the open window. Within an open window an attacker can still try up to 3 times per power-on or `PAIR`. Whether Bluedroid raises `SEC_REQ_EVT` on the peripheral for every pairing request, and whether the address in `AUTH_CMPL` is the identity address, must be confirmed on a board. |

## 6. Acceptance

- Q1 `scripts/check_fixes_r6.py` drives real page paths. It covers C1 (change the program by menu and by editor after
  Begin), C2 (copy plus an added phase), C5 (`$future`), C3 (accents and look-alikes), C4 (split sentence), C6
  (`ssit_higher` and an own program with a short frame), C7 (one built-in fails to load), C8 (device page after a
  hold), and the controls (no plan: every built-in allowed; the built-in Observer plays on the band). It fails on c3b1a55
  and passes after the fix.
- Q2 The parity test adds code points from Unicode 16 (U+1CCD6 to U+1CCF9) and every table entry: fold, levels and
  Spine are identical. `link_test` adds the request rule: a request is accepted only in the window and below the
  failure limit, and the passkey is shown only in the window. The stubs give the 3.x `getValue` type, and the sketch
  compiles in all 10 builds.
- Q3 All suites and browser checks pass. No threshold changes.

## 7. Results (recorded after the code commit dbb393c)

- Q1 met. `scripts/check_fixes_r6.py` (real page paths; the program changed after Begin) on c3b1a55: 8 failures (C1a, C1b,
  C2, C3-C5, C6, C7, C8, and the recorded Lion-node consequence). On dbb393c: 0 failures, 0 page errors. Controls pass:
  CRISIS during a run stops it; with no plan every built-in is allowed and the built-in Observer plays on the band; with
  a short frame "I am steady" the built-in `ssit_higher` and an own "I am steady today" are allowed, and an own "I am
  steady" (exact) is held.
- Q2 met. `rsso/tests/test_fixes_r6.py`: 5 passed (every table entry and mark range, the Unicode 16 outlined letters and
  digits, and accents/look-alike samples: fold, levels and Spine identical in Python and JavaScript; newer code points
  kept as they are). `review/r5/parity.py`: 0 differences. `link_test`: 52 checks (5 new: requests and the passkey
  screen only in the window, none after the failure limit, 50 attempts outside the window refused). The new stubs give
  `String` for 3.x: the c3b1a55 sketch fails on 3.x with the reviewer's error ("conversion from 'String' to non-scalar
  type 'std::string'") and compiles on 2.x; the fixed sketch compiles in all 10 builds. `test_ble_pairing.py`: 12 passed.
- Q3 met. `rsso` suite 273 passed, 1 expected failure (TRIAL_LOOP T4, unchanged); `rsxv` 130 passed;
  `scripts/check_all.sh` all passed; the 10 browser checks exit 0. No threshold changed.
- Recorded:
  - The fold table is pinned to Unicode 15.1 (Python 3.13). `check_all.sh` regenerates it only with a matching Python.
    Characters newer than the table are kept as they are in both languages, so they never match a wording or level
    pattern.
  - B5 and B7 rest on Bluedroid raising `ESP_GAP_BLE_SEC_REQ_EVT` for each pairing request on the peripheral, and on
    `AUTH_CMPL` carrying an address that the bond list has. Both are to be confirmed on a board. If the address is a
    private one, a bonded host that reconnects without new keys is refused (fails closed).
  - Within an open window, 3 passkey guesses remain possible per power-on or `PAIR`.
