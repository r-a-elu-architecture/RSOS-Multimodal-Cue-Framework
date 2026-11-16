# REVIEW_P2 — targeted check of phase 2 Steps 6–11 and ESP32_TOOLS

```
Step:            Phase 2 Steps 6-11 (SITE_CATCHUP, RSXV_LEVELS, AGENTS_PROVEN, CEILING) and ESP32_TOOLS (targeted, not a full audit)
Reviewed commit: 5060454 (dev; dev had not moved when cloned)
Date:            2026-11-16
Verdict:         changes needed (1 blocker, 4 should fix, 7 notes)
```

Reviewer scripts are not committed. They were run from `/tmp/p2` against a clean clone, and every finding below
gives a reproduction that a reader can type.

## Checklist (HANDOFF §3)

| # | Item | Result | Evidence |
|---|---|---|---|
| 1 | All tests pass | **pass** | `scripts/check_all.sh`: "All checks passed", generated files "unchanged". RSX 43, RSX-V 147 (unittest), rsso 292 OK (2 skipped, 1 expected failure), toolkit 10, conformance 15/15 ×2, board sim 7/7. `cd rsxv && python3 -m pytest -q tests`: 149 passed. The HANDOFF list of 16 pytest files: 119 passed, 1 xfailed. `check_site_catchup.py docs` and `check_profiles.py docs` exit 0 with no page errors and no fails. The other browser checks in "How to verify" were **not** run (time budget). |
| 2 | Spec before code | **pass with notes** | CEILING: registered a45ff0d (16:54:08), code 3a055c7 (16:55:04), results 49fb1bc (17:00:14). The spec is unchanged between registration and results except §5 and the status line (`git diff a45ff0d 49fb1bc -- spec/CEILING.md`). RSXV_LEVELS 86edfd5 → 345324b. AGENTS_PROVEN 5f25a1f → 305dc39. SITE_CATCHUP ecac2ee → bfbc265/6686fff/7bc669f. ESP32_TOOLS: 35d61d8 → c6b6af6 (R1 results) → 356991b (A1) → c4d9b8b → 22059eb → 183939d (A2) → 74fa4b2 → fb684a5. The order is correct in git. See P2-11 and P2-12 for the gaps. |
| 3 | No threshold changed | **pass** (CEILING) | Rule §2 is applied unchanged (`ceiling_experiments.py:41-49`). The 99% level, 200 deployment seeds and 20 reps match the registration. Other steps were not compared against the backup. |
| 4 | Stored data unchanged | not checked | Not in scope of this targeted check. |
| 5 | Python/JS parity | n/a | None of the reviewed logic has a JS twin, apart from the pages that read generated JSON. |
| 6 | Neutral wording | **pass** | `check_profiles.py docs` exit 0; `check_site_catchup.py` wording checks pass. P2-6 is about strength of claims, not excluded terms. |
| 7 | Nothing on `main` | **pass** | This review pushes only `review/p2`. |
| 8 | Dev site shows change, no page errors | **partly** | Local Chrome via the checks: no page errors. The deployed `/dev/` site was not opened. |
| 9 | Prose claims true in code | **fail** | P2-1, P2-2, P2-3, P2-6. |

## Reproduction of W5-CEILING

`cd rsxv && python3 -m rsxv.ceiling_experiments` took 52 s here. It rewrites `results/results_ceiling.json` and
`results/ceiling.md` byte-identically: `git status` is clean afterwards. The numbers reproduce exactly.

| Check | Result |
|---|---|
| Arms as registered | yes |
| Seeds | Disjoint. Truth 26000+/26200+/26400+ ×200; ORACLE role reading 25000+/25100+/25200+ ×50; pilot 21000–21311 / 22000–22311 / 23000–23311; deployment 24000–24199 / 24200–24399 / 24400–24599. No overlap between truth, role reading, pilot and deployment. They match W5 with `shift=0`. |
| Mapping rule §1 | Implemented as written (`map_table`). |
| Decision rule §2 | Applied correctly. ROOM lower bound for agent → person is +0.199 > 0, and no other direction has ROOM. "Pass for agent → person only" is the correct mechanical reading of the registered rule. |

## Findings

### P2-1 — should fix (interpretation; close to a blocker for the successor design): the W5-CEILING "room" is not attributable to source knowledge, and the recorded caveat misidentifies its cause

Files:
- `spec/CEILING.md:89-95`
- `rsxv/RESULTS.md:169`
- `HANDOFF_DEV.md:306-309`
- `rsxv/rsxv/ceiling_experiments.py:48` (decision text "the method is the bottleneck there")

The registered design has no arm that holds the target's information fixed and removes the source. TGT-TRUE is
target-only, but it uses full truth (12,000 ticks). Reviewer controls (script `/tmp/p2/ctrl.py`, `/tmp/p2/ctrl2.py`)
show that the source adds nothing:

| Direction | SRC-TRUE | Target-only "STABILISE everywhere", roles read with full information | Target-only "STABILISE everywhere", roles read **from the PILOT-8 seeds' own 8 × 10 role-reading ticks**, no source, no gate (mean of 20 reps) |
|---|---|---|---|
| agent → person | +0.2402 | +0.2402 (difference 0.000 [0, 0]) | **+0.2402** |
| agent v2 → person | −0.0632 | +0.2402 | +0.2402 |
| person → agent | −0.0049 | −0.0049 | −0.0163 |
| person → agent v2 | −0.1294 | −0.1294 | −0.1294 |

- For agent → person, the pilot reads the target's STABILISE role correctly (BEAR) in **20 of 20** repetitions. A
  source-free rule using only those pilot roles reaches the full ceiling, +0.2402.
- So the caveat's claim is wrong, and so is the RESULTS row's claim. The caveat says "the gain depends on reading
  the target's roles well: 3,000 target ticks vs 240". In fact, roles read from the pilot suffice.
- PILOT-8 falls short (+0.027) because of its per-context estimation and the α = 0.0025 gate. Most pilot tables keep
  LION in 3 of 4 contexts. Role reading is not the cause.
- Also, the role reading uses 8 × 10 ticks (`read_target_roles`, `w5_experiments.py:172-178`), not 240. The 240 are
  the pilot's own 8 × 30 ticks.
- SRC-TRUE equals W5's own ORACLE policy "S" (+0.240 per tick, `spec/CEILING.md` §0), which is target-only.
- In agent v2 → person, the same target-only rule gives +0.240, while the "perfect" source gives −0.063. That is
  direct evidence that the ceiling's value comes from the target side.

What the result supports:
- In agent → person there is room between the 8-target pilot *method* and a simple "stabilise everywhere" table.
- The test does not show that source knowledge carries any value over a target-only rule. This is the question in
  §0 ("is perfect source knowledge worth anything to the target?"), and for agent → person the reviewer's control
  answers it in the negative.
- To attribute anything to the source, a control arm was needed: target roles read with the same information plus
  the target-only best function (or W5's ORACLE "S"), with no source. That arm equals SRC-TRUE.

Requested:
- Correct the caveat in `spec/CEILING.md` §5, `rsxv/RESULTS.md:169` and HANDOFF Step 11. Say that the room is
  reachable without any source by the pilot's own roles plus a constant stabilising table, so the room measures the
  pilot method (gate/estimation), not source knowledge.
- Change the verdict to "pass by the registered rule". The interpretation should be: "no evidence that source
  knowledge adds value over a target-only rule".
- Require the permitted agent → person successor to include this source-free arm as a comparator in its
  registration. Otherwise a "transfer" success would only re-discover the target-only rule.

The registered rule itself was followed, so no threshold changed. The fault is the design's missing control and the
wording around it.

### P2-2 — blocker (firmware pairing; needs a board to confirm): on Arduino-ESP32 2.0.17 and 3.2.1 the library requests encryption on every connection, so FIXES_R6C S2 does not hold

Files:
- `firmware/esp32/rsos_esp32/rsos_esp32.ino:418-422`: `BLEDevice::setEncryptionLevel(ESP_BLE_SEC_ENCRYPT_MITM)` on cores before 3.3.
- `firmware/esp32/rsos_esp32/rsos_esp32.ino:275`: the sketch's own request, made only in the window.

The library code, read upstream at tags 2.0.17 and 3.2.1 (`libraries/BLE/src/BLEDevice.cpp`):
- `setEncryptionLevel` stores `m_securityLevel`.
- `BLEDevice`'s GATTS handler then runs `case ESP_GATTS_CONNECT_EVT: if (BLEDevice::m_securityLevel) esp_ble_set_encryption(remote_bda, m_securityLevel);`.
  This is 2.0.17 lines 107-114 and 3.2.1 lines 104-105, and it runs **on every connection, in or out of the window**.
- FIXES_R6C's own analysis (`spec/FIXES_R6C.md:9-16`) says that when the band starts encryption, the phone's pairing
  goes ahead without `SEC_REQ_EVT`, so `onSecurityRequest()` is never asked.

Consequences on 2.0.17 (ESP32, -C3, -S3) and 3.2.1 (-C3, -S3) builds, which are the builds the docs recommend:
- An unknown host outside the window is invited to pair.
- Passkey-entry attempts outside the window are no longer refused at the request. `on_auth_fail`
  (`rsos_link.cpp:12-15`) only closes a window that is already closed, so attempts are unlimited across reconnects.
- On a correct guess, `on_new_bond` refuses outside the window and the bond is removed. The host still learns that
  the guess was right.
- With a static passkey reused across LE Secure Connections passkey-entry attempts, the 20 commitment rounds leak the
  passkey bit by bit. Unlimited attempts outside the window defeat the purpose of P4 and the window ("pairing
  attempts, and so passkey guesses, limited to the open window", FIXES_R6 §4).

The 3.3.12 library (read at tag 3.3.12) only calls `startSecurity` when `BLESecurity::m_securityEnabled`. The sketch
never sets that, so S2 holds there. The two cores therefore behave differently, contrary to A1 F2's "same level, same
call order".

Why the existing tests miss it: they are static text tests of the sketch (`test_ble_pairing.py`: "esp_ble_set_encryption
only under link.accept_request("). They cannot see the library's hidden call. This is the same pattern as the stubs
hiding R1-a/R1-b.

Suggested fix, to register first: do not call `setEncryptionLevel` at all. The GATT permissions are already
`*_ENC_MITM`, and the sketch sets the SM parameters itself. Add a check against the real library source, or a note in
BOARD_TEST.

This is not new in ESP32_TOOLS (it dates from Step 4/FIXES_R6C). The step touched this exact call and kept it, so it is
reported here.

### P2-3 — should fix: an RSX-V command doing difficult-memory work runs in Workplace unless its author declares `MEMORY yes`

Files: `rsxv/rsxv/bridge.py:153-160`, `rsxv/rsxv/run.py:107-125`.

V2's content level is computed only from markers and clinician tiers in the bridged program. The INTENT, the
translator's output and vector arguments never set memory work.

Reproduction:
```
T.to_program("Help me relive the accident so I can process it.", tier=8)
```
run with `domain="workplace"` gives status `done`, with effective level self_guided and memory False. Omitting
`MEMORY` is enough to "lower" it.

This conforms to the letter of RSXV_LEVELS V2. But HANDOFF says "the effective level (declared or from content)", and
the Workplace rule (no difficult-memory work) is then only as strong as the command author's honesty. Agents and the
translator are exactly the authors who will not declare it.

Requested: either a content rule for memory work in RSX-V (the INTENT and the translator's request text, using the
person side's memory-work patterns), or a statement in the spec and on the RSX-V page that memory work is
declaration-only.

### P2-4 — should fix: an unknown or mis-cased domain fails open to Personal

Files: `rsxv/rsxv/run.py:118-121`, `rsso/rsso/profiles.py:97-98` (`valid()` falls back to `personal`).

With `MEMORY yes`:
- `domain="workplace"` → refused.
- `domain="Workplace"` or `"workplace "` → **done**.

On the site the domain comes from a menu. For RSX-V, `ctx` comes from the caller (agent or script), so a typo
silently grants Personal's allowances. Also, `ctx` with neither `domain` nor `max_level` caps at clinician-led
(`watch()` default), which is more permissive than the site's default domain. A clinician-led command runs with only
`clinician_present=True, screening_recorded=True`.

Requested: reject unknown domains in `_watch` (refuse the run), and default to the Personal cap when no domain and no
`max_level` are given.

### P2-5 — note: `confirmed` and `source` are self-asserted by the caller

`run()` with `source="agent"` gives `ask` → refused. The same call with `confirmed=True` runs (`run.py:122-124`). This
is V5 as registered, but "the person starts every run" is enforced only by the caller's honesty. A run with no
`source` is treated as the person. Worth a sentence in the spec.

### P2-6 — should fix: the Agents page shows W1 without the register's own caveat

Files: `docs/agents.html:185-196, 328`.

The "Proven in simulation" section shows "meta repair fixed 40, local retry 20" (cross-agent 20 vs 0) as an agent
result that works. The register row for W1 (`rsxv/RESULTS.md:129`) says: "The gain comes from the global view: an
equal-information greedy baseline also fixes 100%". The page's cards show `meaning` only for W4, J1 and T-AP. The
H-SWITCH caveat is shown, but the W1 one is not.

The page therefore states more than the record: it credits the archetype meta-repair, while the record attributes the
gain to information alone. Show the W1 register row's meaning beside the counts.

The heading "Proven in simulation" is registered (AGENTS_PROVEN P2) and is followed by "not tested with people", so it
is not a finding by itself. But "proven" is stronger than "passed its registered test".

### P2-7 — note: W5-CEILING counted as a "mixed" result of the transfer family

`docs/data/results_register.json` puts W5-CEILING in the transfer family as the next link after W5e (W5 → … → W5e →
W5-CEILING), with status "mixed". The transfer family counts are now 2 pass / 1 mixed / 10 fail.

A ceiling analysis is not a transfer attempt. Given P2-1, a reader will take "mixed" as partial evidence for transfer.
Consider its own status (e.g. "analysis") or a note on the results page.

Family and series rules otherwise file every row as SITE_CATCHUP S8.1/S8.2 says. 34 rows, none in "other". The G2
ambiguity in S8.1 vs S8.2 ("G2, a case where transfer can be valid" vs "LIA-G2") resolves correctly because the rules
match on the start of the ID.

### P2-8 — note: Spine check covers words, not identifiers

The following are refused, including after `effective()` is cached and the prog dict is then edited (the cache is
keyed by `to_text`, so there is no poisoning):
- INTENT, vector arguments and archetype carrying "ice bath";
- zero-width, full-width and Cyrillic variants;
- an escaped quote inside an argument.

A PHASE name like `ice_bath` passes (status done). It appears in the cue program only as an identifier
(`PHASE ice_bath_in`), not as quoted text, so it is consistent with the person side's "quoted strings" rule. Noted in
case phase names are ever displayed.

### P2-9 — note: Step 9 level-lowering attempts that failed (good)

These were all refused in Personal or kept clinician-led:
- tier 414 with `LEVEL self_guided`;
- `TIER 0414`;
- legacy v1 `TIER 414 :: …`;
- editing `prog["tier"]` after caching;
- NEXT and NEXT-of-NEXT, which keep `clinician_led` and `MEMORY yes` through `to_text`/`parse`.

Clinician-led work in `clinical` without a clinician is refused even with `confirmed=True`, because it is a hold, not
an ask.

Duplicate header lines are accepted and the last one wins: `LEVEL clinician_led` then `LEVEL self_guided`, or `MEMORY
yes` then `MEMORY no`. This only lowers the author's own declaration, never content. V1 should still make duplicates a
parse error.

V7 is confirmed against 86edfd5 (a worktree at the registration commit, before the code):
- `python3 -m rsxv examples/dragon.rsxv` output is identical;
- `canonical17.rsx` and `dragon_full.rsxv` outputs are identical (md5);
- `python3 -m rsxv.evaluate_laws examples/dragon.rsxv` JSON is byte-identical;
- `check_all.sh` regenerates `docs/data/*.json` unchanged.

The `dragon.run.txt` staleness predates Step 9 (confirmed: 86edfd5 output differs from the committed file too).

### P2-10 — note: the RSOS_EMULATOR test pins the sketch, not the build

The test `test_ble_pairing.py:116-135` does check:
- exactly two `#ifdef RSOS_EMULATOR` guards in the `.ino`, with the expected bodies and positions;
- that `platformio.ini`, BOARD_KIT and BOARD_TEST do not contain `-DRSOS_EMULATOR`.

It does not cover:
- a `#define RSOS_EMULATOR` in `rsos_core.h`, `rsos_link.h` or `rsos_modules.h`;
- a sketch-folder `build_opt.h`;
- `real_check.py --extra`.

The flag fails safe (no Bluetooth at all), so the impact is low. Two side effects:
- In an emulator build `UNPAIR`/`NEWKEY` print success but remove no bonds. If such an image is ever flashed on a
  board that has bonds, they survive until a normal build.
- The only runtime marker is the boot NOTE line. Consider adding it to the `HELLO` answer.

### P2-11 — note: the NimBLE guard keys on a different macro from the library

`rsos_esp32.ino:27` tests `CONFIG_BT_NIMBLE_ENABLED` after `<Arduino.h>`. The 3.3.12 BLE library selects its backend by
`CONFIG_NIMBLE_ENABLED` / `CONFIG_BLUEDROID_ENABLED` (`BLEDevice.h:37,82`). The recorded run shows that the guard fires
for -C3/-S3 on 3.3.12, so it works today.

A guard on `!defined(CONFIG_BLUEDROID_ENABLED)` would state the actual requirement, which is Bluedroid, and would not
depend on which NimBLE macro a future core defines. The docs (sketch STATUS, HANDOFF, §6 open items) are honest that
NimBLE builds do not work.

### P2-12 — note: traceability

- `spec/SITE_CATCHUP.md:49` cites "code 8ed086f" and `spec/RSXV_LEVELS.md:3` cites "code 0d91a09". Neither object
  exists in the repository. The real commits are bfbc265 and 345324b (HANDOFF has the right ones).
- ESP32_TOOLS round-1 results (c6b6af6) were produced with `firmware/esp32/real_check.py`, which entered the
  repository only with the fix commit c4d9b8b. The round-1 numbers cannot be reproduced from the commit that records
  them.
- CEILING's 136-line code commit came 56 s after its registration. The git order is correct, but the code was
  evidently drafted before the registration was pushed. That is acceptable only because the design text is unchanged.

## What could not be tested

- **ESP32 toolchains and QEMU are not installed here.**
  - No real compile or emulator run was repeated.
  - ESP32_TOOLS was reviewed by reading the sketch, tests and spec.
  - The Arduino BLE library was read upstream (GitHub raw, tags 2.0.17, 3.2.1, 3.3.12, plus 3.3.2) rather than from
    the installed cores the author used.
- P2-2 rests on the library source plus FIXES_R6C's own reading of Bluedroid. Its effect on a phone needs a board
  (BOARD_TEST T3–T7).
- Browser checks other than `check_site_catchup.py` and `check_profiles.py` were not run. The deployed `/dev/` site was
  not opened.
- Checklist items 4 and 5, and the threshold comparison against the backup branch for Steps 6–10, were not done.
- `site_agents` fidelity was checked through `check_all.sh` regeneration (unchanged) and by reading the page script.
  The 40 W1 trials were not re-derived independently of `world_experiments.w1_trial`.

## Verdict

**Changes needed.**
- W5-CEILING's verdict follows the registered rule, but its interpretation and caveat must be corrected (P2-1)
  before the agent → person successor is registered.
- The wristband's pairing window is not enforced on the recommended 2.x/3.2.1 builds (P2-2).
- RSX-V levels hold against every lowering attempt tried (P2-9). Memory work there is declaration-only (P2-3), and
  unknown domains fail open (P2-4).
