# FIXES_R6C — fixes from the targeted check of fix pass R6

Status: registered 2026-11-16, before code. Check: branch `review/r6-check`, commits 1ae33e3 and 7171f77 (checked dev at
0304a0c). R6-1 to R6-7, R6-9 and R6-11 were confirmed fixed. There was 1 should fix (R6c-1) and 4 notes. This
registration amends FIXES_R6 B5 and corrects BLE_PAIRING §4 as amended by FIXES_R6.

## 1. Why B5 did nothing (R6c-1)

FIXES_R6 B5 answered `ESP_GAP_BLE_SEC_REQ_EVT` in the sketch's own GAP handler. Read against ESP-IDF
(`components/bt/host/bluedroid/stack/smp/smp_act.c`, `smp_proc_pair_cmd`) and Arduino-ESP32 2.0.17 and 3.0.7
(`BLEDevice.cpp`):
- When the band starts pairing, it asks nobody. The band sent a security request at every connect
  (`esp_ble_set_encryption` in `onConnect`), so the phone's pairing request went ahead with no question to the app.
- When the phone starts pairing, the stack raises `SMP_SEC_REQUEST_EVT` and the Arduino library answers it in
  `BLEDevice`'s own handler: with `onSecurityRequest()` of the registered `BLESecurityCallbacks`, or `true` when none is
  registered. The sketch registered none, so every request was accepted before its own answer.

## 2. Rules

| ID | Rule |
|---|---|
| S1 | The sketch registers `BLESecurityCallbacks` (`BLEDevice::setSecurityCallbacks`). `onSecurityRequest()` returns `link.accept_request(millis())`, so a pairing the phone starts is accepted only inside the window and below the failure limit. `onConfirmPIN` returns false (numeric comparison is not used). `onPassKeyRequest` returns 0 (the band does not enter keys). `onPassKeyNotify` and `onAuthenticationComplete` do nothing; the GAP handler keeps that work. The interface is the same in 2.0.17 and 3.0.7. |
| S2 | The band asks for encryption in `onConnect` only while the window is open. Outside it, a bonded host encrypts with its stored key when it reads or writes (the characteristics require it). An unknown host must start pairing itself, and S1 refuses it. |
| S3 | The sketch's own `ESP_GAP_BLE_SEC_REQ_EVT` case is removed, so the library's answer is the only one. |
| S4 | The stubs declare `BLESecurityCallbacks` and `BLEDevice::setSecurityCallbacks` with the real signatures, so a wrong override fails to compile. |
| P1 (R6c-4) | At Start the player compiles the editor's current text at once (no 250 ms wait). The decision, the check-in re-decision and the run all use that one compiled timeline. |
| N1 (R6c-3) | Recorded: the built-in Observer is held whenever an Observer node is in a depression or PTSD plan, the same as the built-in Lion with a Lion node. |
| §4 | BLE_PAIRING §4 is corrected again. Pairing attempts are limited to the open window by S1 and S2, read from the library and stack sources but not run on a board. Within a window, 3 attempts remain per power-on or `PAIR`. R6c-2 is still open: B7's bond-list check uses the address in `AUTH_CMPL`, and if that is a phone's private address, bonded phones are refused on reconnect. It is the first board test. |

## 3. Acceptance

- Q1 `rsso/tests/test_ble_pairing.py` checks:
  - The sketch registers the security callbacks, and `onSecurityRequest` returns `link.accept_request(millis())`.
  - `esp_ble_set_encryption` is called only under `link.accept_request(` or `link.window_open(`.
  - The sketch has no `ESP_GAP_BLE_SEC_REQ_EVT` case.
  - The stubs declare the five pure virtual methods with the real signatures.
  - All 10 builds compile.
- Q2 `scripts/check_fixes_r6.py` gains P1: text typed and Started within 250 ms is decided and played as typed. A
  held node typed into an allowed program's editor and Started at once is held.
- Q3 All suites and browser checks pass. No threshold changes.
