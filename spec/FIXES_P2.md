# FIXES_P2 — fixes from the targeted review of phase 2 and ESP32_TOOLS

Status: registered 2026-11-16, before code. Review: branch `review/p2`, commit 3248364 (reviewed dev at 5060454;
1 blocker, 4 should fix, 7 notes). This registration amends FIXES_R6C S2, CEILING §5 (record wording only),
RSXV_LEVELS V2 and V5, and AGENTS_PROVEN P2 as stated below.

## 1. Wristband: no encryption request outside the window (P2-2, blocker)

| ID | Rule |
|---|---|
| E1 | The sketch makes no `setEncryptionLevel` call, on any core. On 2.0.17 and 3.2.1, `BLEDevice::setEncryptionLevel` makes the library call `esp_ble_set_encryption` on **every** connection (`BLEDevice.cpp`, `ESP_GATTS_CONNECT_EVT`; read upstream by the review). That bypasses `onSecurityRequest()` and so the window. The only encryption request left is the sketch's own, in `onConnect`, inside the window (FIXES_R6C S2). The characteristics still require an encrypted, authenticated link (`*_ENC_MITM`), and the security parameters are still set by `esp_ble_gap_set_security_param`. |
| E2 | `test_ble_pairing.py` checks that no `setEncryptionLevel` call, and no `BLESecurity` call that starts security on connect, appears in the sketch. `BOARD_TEST.md` T5 states that the result rests on reading the library at 2.0.17, 3.2.1 and 3.3.12, and must be confirmed on a board. |

## 2. W5-CEILING: the record says what the evidence shows (P2-1, P2-7)

No threshold, arm or verdict changes. The run's numbers stay as recorded.

| ID | Rule |
|---|---|
| C1 | The recorded caveat is replaced (CEILING §5, the `rsxv/RESULTS.md` row, HANDOFF, the decision text in `ceiling_experiments.py` and the regenerated `ceiling.md`) by the review's finding. **The room in agent → person cannot be credited to the source.** A source-free rule reaches the same +0.240: the target's stabilising archetype in every context, read from the 8-target pilot's own role-reading ticks (20 of 20 repetitions). The pilot falls short because of its per-context estimates and its gate, not its role reading. The earlier "3,000 against 240 ticks" explanation was wrong. |
| C2 | The line's decision: **the W5 transfer line stops in all four directions.** The registered rule allows one agent → person successor. No successor is planned, because a source-free rule already reaches the ceiling. Any future transfer test must include a source-free arm with the same target information. |
| C3 | The register row starts with **Analysis** rather than Pass, so the results page shows it as an analysis and not as partial transfer evidence. `site_results.py` maps "Analysis" to status `analysis`. The page shows it in neutral grey, and the family counts gain an `analysis` count. |

## 3. RSX-V levels (amends RSXV_LEVELS V2 and V5; P2-3, P2-4, P2-5)

| ID | Rule |
|---|---|
| L1 | **Memory work from content.** A command also counts as memory work when its folded INTENT or vector arguments match: `re-?liv(e\|es\|ed\|ing)`, `re-?experienc`, `flashback`, `traumati[cz]`, `trauma`, `reprocess`, `memory work`, `the accident`, `old memor`. The match uses ASCII patterns on folded text, so look-alike letters are caught. A declaration can still add memory work, and `MEMORY no` cannot remove content memory work. |
| L2 | **Domain fails closed.** `ctx["domain"]` is stripped and lowercased. A value that is not one of the seven domains makes the run `refused`, with the reason "unknown domain". With neither `domain` nor `max_level`, the cap is Personal's (structured, memory work allowed), the same as the site's default. Clinician-led commands therefore need `domain="clinical"` with the clinical module. |
| L3 | **Recorded:** `source` and `confirmed` are asserted by the caller, as on the person side, where the page is trusted. A run without `source` counts as the person's. |

## 4. Agents page (amends AGENTS_PROVEN P2; P2-6)

| ID | Rule |
|---|---|
| A1 | The repair panel shows the W1 register row's meaning beside the counts. The meaning says that the gain comes from the global view, and that an equal-information greedy baseline also fixes 100%. |
| A2 | The section heading becomes "Passed in simulation: the RSX-V agents", and the tags say "passed its registered test". |

## 5. Records (P2-12)

The wrong commit references are corrected in record commits: SITE_CATCHUP "8ed086f" → bfbc265, RSXV_LEVELS "0d91a09"
→ 345324b.

The notes P2-10 (the emulator flag's test covers the sketch, not the build) and P2-11 (the NimBLE guard's macro) are
recorded as open. Changing the guard without a real compiler here could break builds that work today.

## 6. Acceptance

- Q1 `rsso/tests/test_ble_pairing.py` E2 passes. All 10 builds compile against the stubs.
- Q2 `rsxv/tests/test_levels.py` gains these cases:
  - L1: the reviewer's "Help me relive the accident…" translator command is refused in Workplace, also with a
    Cyrillic look-alike letter; `MEMORY no` does not lift it.
  - L2: "Workplace" and "workplace " behave as workplace, "workplce" is refused, and with no domain a clinician-led
    command is refused.
  - V7 still holds for commands without levels: the dragon example is unchanged.
- Q3 `scripts/check_site_catchup.py`:
  - Step 10 checks that the W1 meaning is shown and the new heading is used.
  - Step 8 checks that W5-CEILING shows as an analysis.
- Q4 All suites, `scripts/check_all.sh` and the browser checks pass. No threshold changes.
