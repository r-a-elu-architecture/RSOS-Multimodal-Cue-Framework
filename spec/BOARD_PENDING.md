# BOARD_PENDING — what can be checked and prepared while no board is available

Status: registered 2026-11-16, before code. Results in §5, in a separate "Record results" commit. No threshold
changes after results. Follows spec/ESP32_TOOLS.md (results fb684a5). The owner has no ESP32 board; this step does
everything that does not need one and prepares the first board run by someone else.

## K1 — the firmware checks run on every push (GitHub Actions)

- A workflow `.github/workflows/firmware.yml` runs on pushes to `dev` and `main`, on pull requests and by hand
  (`workflow_dispatch`). It does not deploy anything and does not touch the Pages workflow.
- **Job `compile`**: arduino-cli 1.6.0; Arduino-ESP32 2.0.17, 3.2.1 and 3.3.12 in three data directories; GFX Library
  1.6.0 on 2.0.17 (ESP32_TOOLS §7.3) and the newest on 3.x; the 40-build matrix of ESP32_TOOLS (C1, C1b) with
  `firmware/esp32/real_check.py compile`.
- **Pass rule (K1-P):** the job passes when the 30 builds that compile today compile, and each of the ten ESP32-C3/-S3
  builds on 3.3.12 stops at the NimBLE guard (its log contains `RSOS: this core builds Bluetooth with NimBLE`).
  Anything else fails the job. `real_check.py compile --expect-nimble-guard` applies this rule and prints one line per
  build.
- **Job `emulator`**: the same arduino-cli and Arduino-ESP32 3.3.12; Espressif QEMU esp_develop_9.2.2_20260417. It
  builds the ESP32 emulator image (`FlashMode=dio`, `-DRSOS_EMULATOR`, ESP32_TOOLS A2) and runs, each on a fresh
  copy of the image: `real_check.py usb` (U1–U8, U3b) plus `real_check.py passkey` after a restart (U9);
  `python -m rsso.board --port socket://…` (B1–B7); and K3 below. Pass rule: everything passes except U3, which is
  expected not to (ESP32_TOOLS §7.4); B1–B7 thresholds unchanged.
- Results of the first run on GitHub (both jobs) are recorded in §5 with the run's link.

## K2 — a call for the first board report

- An issue form `.github/ISSUE_TEMPLATE/board_report.md` with the report block of `firmware/BOARD_TEST.md` and a
  link to the sheet on the `dev` branch.
- One public issue on the repository, "First board report wanted: RSOS wristband on an ESP32", saying in plain
  words: what to buy (about USD 15–20: ESP32-DevKitC, coin motor, MOSFET, diode, two resistors), how long it takes
  (about 1.5 hours), what is already verified (ESP32_TOOLS) and what only a board can show (radio, pairing, motor),
  with links to BOARD_KIT.md and BOARD_TEST.md. Neutral, technical wording; no personal content.
- BOARD_KIT.md §6 and BOARD_TEST.md "Report" point to the issue form.

## K3 — the motor's PWM output at the hardware register (emulated ESP32)

Espressif's QEMU models the ESP32 LED PWM controller (`hw/misc/esp32_ledc.c`): each duty-register write becomes an
intensity in percent, `100 * duty / (2^resolution - 1)` rounded down, visible through the trace events
`led_set_intensity` / `led_change_intensity` (`-trace "led_*"`). That is the value the firmware writes to the PWM
hardware that drives the motor pin. The emulated ESP32-C3 and -S3 have no such model, so K3 is ESP32 only (both
cores, 2.0.17 and 3.3.12, emulator image of ESP32_TOOLS A2). With 8-bit PWM, 0.40 is duty 102 → 40%, 0.60 is
duty 153 → 60%.

| ID | Send (after boot) | The intensity changes must be, in order |
|---|---|---|
| K3a | (nothing) | from boot until the first command, only 0% |
| K3b | `LOAD 1 0.40`, `H 0 300 300 3 0.40`, `START` | 0→40, 40→0, 0→40, 40→0, 0→40, 40→0 |
| K3c | `LOAD 1 0.40`, `H 0 200 100 1 0.90`, `START` (program limit) | 0→40, 40→0; never above 40 |
| K3d | `LOAD 1 0.90`, `H 0 300 100 1 0.90`, `START` (device envelope 0.6) | 0→60, 60→0; never above 60 |
| K3e | `LOAD 1 0.40`, `H 0 5000 0 1 0.40`, `START`, `STOP` after about 300 ms | 0→40, then 40→0 after `STOP` (the pulse would otherwise last 5 s), and `STOPPED <t>` is reported |

- Pass: every row as stated. The levels are exact (integers from the model).
- Recorded, not judged: the on-times measured on the host clock as the trace grows (QEMU does not run in step with
  real time; ESP32_TOOLS §3 E4 applies).
- What K3 does not show: that the GPIO matrix routes the channel to the motor pin (not modelled: the out-select
  register reads 0 in the emulator), the 20 kHz carrier, and anything after the pin (MOSFET, motor).

`real_check.py pwm --port <serial> --trace <file>` runs K3a–K3e and prints a table.

## Acceptance

- `scripts/check_all.sh` and all suites pass; `rsso/tests/test_ble_pairing.py` still finds no `RSOS_EMULATOR` in
  any board file (the workflow sets it only for the emulator job's image).
- The K1 workflow's first run on GitHub, the K3 results on both cores in the workspace, and the issue's link are
  recorded in §5. HANDOFF_DEV.md gets a section.

## 5. Results

(recorded after the runs, in a separate commit)
