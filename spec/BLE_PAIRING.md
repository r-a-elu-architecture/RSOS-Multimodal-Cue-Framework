# BLE_PAIRING — the wristband accepts commands only from paired hosts (roadmap Step 4)

Status: registered 2026-11-16 (c898386), before code; code 661165e; results in §5.

## 0. Problem

`firmware/esp32/rsos_esp32/rsos_esp32.ino` advertises the Nordic UART Service with an open RX characteristic
(`PROPERTY_WRITE | PROPERTY_WRITE_NR`, no encryption, no pairing). Any device in radio range can connect and send
`LOAD` / `H` / `START`, so the band can be made to vibrate (or open a scent valve) without the person's host. The BLE
line buffer also has no length limit (USB serial stops at 95 characters).

## 1. Rules

| ID | Rule |
|---|---|
| P1 | **Encrypted, authenticated link.** RX (write) and the TX notification descriptor need an encrypted link with man-in-the-middle protection (LE Secure Connections, passkey entry, bonding). Lines that arrive while the link is not authenticated are dropped and never reach the core. |
| P2 | **Passkey.** Six digits, made once from the hardware random generator on first start and kept in flash (NVS). Never 000000 and never a trivial pattern (all one digit, 123456, 654321). Never sent over Bluetooth. Shown only over USB serial (`PASSKEY`) and, with `-DRSOS_DISPLAY`, on the band's screen while a pairing is in progress. |
| P3 | **Pairing window.** A new host can bond only within 120 s after power-on, or within 120 s after `PAIR` sent over USB. Outside the window a new pairing is refused: its bond is removed and the link is closed. Already-bonded hosts reconnect at any time. |
| P4 | **Failed attempts.** After 3 failed pairings the window closes until the next power-on or USB `PAIR`. |
| P5 | **Bond limit.** At most 4 bonded hosts; a 5th new pairing is refused (USB `UNPAIR` clears all). |
| P6 | **USB-only commands.** `PASSKEY`, `PAIR`, `UNPAIR`, `NEWKEY` (new passkey, clears all bonds) act only over USB. Over Bluetooth they are answered `ERR LINK usb-only` and change nothing. Physical access to the cable is the authorisation. |
| P7 | **Line length.** Over both USB and Bluetooth, a line longer than 95 characters is dropped whole and answered `ERR LINE too-long` (USB used to keep the first 95 characters). |
| P8 | **Unchanged.** Link loss still stops all output (DEVICE_PROTOCOL §4.6); the device safety envelope and every RDP/1 rule are unchanged; the web pages' output gate is unchanged. |

## 2. Design

- Portable policy `firmware/rsos_core/rsos_link.{h,cpp}` (window, failures, bond limit, passkey rules, USB-only
  commands, bounded line buffer), copied byte-identical into `firmware/esp32/rsos_esp32/`.
- The ESP32 sketch sets the ESP-IDF security parameters (static passkey, `ESP_LE_AUTH_REQ_SC_MITM_BOND`,
  `ESP_IO_CAP_OUT`, only the specified authentication accepted), sets `ESP_GATT_PERM_*_ENC_MITM` on RX and on the TX
  descriptor, and uses a GAP handler: a new pairing is one in which keys were exchanged (`ESP_GAP_BLE_KEY_EVT`) before
  `ESP_GAP_BLE_AUTH_CMPL_EVT`; the policy decides it; a refused pairing has its bond removed and is disconnected.
- `docs/device.html` and `firmware/BOARD_KIT.md` say how to pair (the system asks for the six-digit passkey; read it
  with `PASSKEY` over USB or on the band's screen).

## 3. Acceptance

- B1 Host test `firmware/rsos_core/link_test.cpp` (built by the Makefile, run by `rsso/tests/test_ble_pairing.py`):
  window open at 0 and 119.999 s, closed at 120 s; `PAIR` reopens it; 3 failures close it; 4 bonds then refusal;
  passkeys never 0 or trivial and always 6 digits; the four USB-only commands refused over Bluetooth and accepted over
  USB; a 96-character line dropped with `ERR LINE too-long`, a 95-character line kept; lines before authentication
  dropped; millis() wrap-around handled.
- B2 The sketch compiles against the stubs for Arduino-ESP32 2.x and 3.x, with and without the modules (existing test,
  stubs extended with the security calls used).
- B3 Static checks on the sketch: RX and TX descriptor permissions are `_ENC_MITM`; RX has no open write; the passkey
  variable appears in no BLE send path; `rsos_link.*` copies identical.
- B4 All existing suites and browser checks pass; no threshold changes.

## 4. Limits recorded in advance

- Not run on a board: compile-checked against stubs only. Arduino-ESP32 3.3 and later reorganised the BLE library
  (NimBLE option); the ESP-IDF calls used here are Bluedroid's, so a NimBLE build is not covered.
- A static passkey is weaker than a fresh passkey per pairing: an attacker who watches about 20 pairing attempts can
  recover it. The window (P3), the failure limit (P4) and `NEWKEY` reduce this; a band with a screen could show a
  fresh passkey each time (not done here).
- Pairing dialogs belong to the operating system and differ between Android, Windows, macOS, ChromeOS and Linux.
- The web page cannot see or check the passkey; it relies on the operating system's pairing.

## 5. Results (recorded after the code commit 661165e)

- B1 met. `link_test`: 47 checks passed (window edges at 0, 119.999 s and 120 s; PAIR reopens; 3 failures close;
  4 bonds then refusal; 100 000 generated passkeys all valid; USB-only commands; 95/96-character lines; a START hidden
  past the limit not run; millis() wrap-around). "Lines before authentication dropped" is enforced in the sketch, not
  in the portable policy, so B1 covers it only through the static check in B3.
- B2 met. The sketch compiles against the extended stubs for Arduino-ESP32 2.x and 3.x, alone and with each module and
  all modules (10 builds).
- B3 met. `rsso/tests/test_ble_pairing.py`: 7 passed (copies identical; RX and the TX descriptor `_ENC_MITM`; no open
  write permission; lines and notifications need `linkAuthed`; the passkey in no Bluetooth send path; USB-only
  commands refused over Bluetooth; no unbounded line buffers).
- B4 met. `rsso` suite 256 passed, 1 expected failure (TRIAL_LOOP T4, unchanged); `rsxv` 130 passed;
  `scripts/check_all.sh` all passed; the 8 browser checks exit 0. No threshold changed.
- The §4 limits stand: not run on a board; the stubs are written to the Bluedroid API, so the security calls are
  checked for syntax only, not against the real headers.
