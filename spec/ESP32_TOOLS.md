# ESP32_TOOLS — the wristband firmware checked with the real ESP32 compilers and Espressif's emulator

Status: registered 2026-11-16, before any compile or emulator run and before code. Results go in §7, in a separate
"Record results" commit. No threshold in this file or elsewhere changes after results are seen.

## 0. Why

Until now the sketch `firmware/esp32/rsos_esp32/` was compiled only against stand-in headers
(`firmware/esp32/stubs/`, `rsso/tests/test_firmware.py`). Stubs can hide real errors: wrong signatures, missing
headers, API changes between Arduino-ESP32 2.x and 3.x, chip differences. No ESP32 board is available, so this step
uses the real toolchains and Espressif's QEMU fork instead. It cannot replace a board for the radio, phone pairing
prompts or motor feel and timing (§5).

## 1. Tools (pinned)

| Tool | Version | Source |
|---|---|---|
| arduino-cli | 1.6.0 | downloads.arduino.cc |
| Arduino-ESP32 2.x | 2.0.17 (the last 2.x; the version the stubs and FIXES_R6C were read against) | Espressif's board index (`gh-pages` of espressif/arduino-esp32; espressif.github.io is not reachable from the workspace, so the same file is read from raw.githubusercontent.com) |
| Arduino-ESP32 3.x | 3.3.12 (the newest 3.x in that index on 2026-11-16) | the same |
| GFX Library for Arduino (display builds) | the newest release in the Arduino library index; if it fails to compile inside its own sources on 2.0.17, the newest release that does, recorded | downloads.arduino.cc |
| Espressif QEMU | esp_develop_9.2.2_20260417 (`qemu-system-xtensa` for ESP32 and ESP32-S3, `qemu-system-riscv32` for ESP32-C3) | the version pinned in ESP-IDF `tools/tools.json` |
| esptool | the one shipped with each core | — |

The two cores live in separate arduino-cli data directories, so neither build sees the other.

## 2. C — compile matrix (real compilers)

- **C1 Matrix.** 3 chips × 2 cores × 5 flag sets = 30 builds:
  - chips and FQBNs: `esp32:esp32:esp32` (ESP32-DevKitC), `esp32:esp32:esp32c3` with `CDCOnBoot=cdc`,
    `esp32:esp32:esp32s3`; the pin flags of `firmware/esp32/platformio.ini` for C3 and S3;
  - cores: 2.0.17 and 3.3.12;
  - flag sets: none, `-DRSOS_THERMAL`, `-DRSOS_SITES`, `-DRSOS_DISPLAY`, and all three together.
- **C2 Pass.** A build passes when `arduino-cli compile` exits 0 with the core's default warning level. Warnings in
  the sketch's own files at `--warnings all` are listed in the results, but do not decide pass or fail.
- **C3 Errors.** Every compiler error is recorded in §7 exactly as printed (file, line, message), with the build it
  came from, before anything is changed.
- **C4 Fixes.** Each fix is registered in §6 (an amendment commit) before the code commit that makes it. A fix:
  - keeps the band's behaviour and every RDP/1 and BLE_PAIRING rule;
  - changes no threshold or limit;
  - keeps `firmware/rsos_core/` and the sketch's copies byte-identical;
  - corrects the stubs where they hid the error, so the stub check would now catch it.
- **C5** After fixes, all 30 builds pass, and the existing stub check (`test_esp32_sketch_compiles_against_stubs`,
  10 builds) still passes.
- **C6** Flash use and static RAM of each build (the size lines arduino-cli prints) are recorded.

## 3. E — the real compiled firmware in the emulator

- **E1 Image.** For each emulated chip (ESP32 with 2.0.17 and 3.3.12; ESP32-C3 with 3.3.12; ESP32-S3 with 3.3.12 if
  the emulator boots it), the build from C1 without module flags is merged into one 4 MB flash image
  (bootloader, partition table, boot_app0, application) with `esptool merge_bin`. For the emulated ESP32-C3 the
  sketch is built with `CDCOnBoot=default`, so `Serial` is UART0, which the emulator connects (the board's USB
  peripheral is not emulated); this is a board option, not a code change. The first UART is a TCP socket
  (`-serial tcp::<port>,server`).
- **E2 Boot.** The real image boots in the emulator: the boot log reaches `setup()` and the band answers over the
  socket. If Bluetooth start-up (`BLEDevice::init` and what follows) crashes, resets in a loop or hangs, that is
  recorded exactly (the panic or the last log line), and §4 applies.
- **E3 USB tests (BOARD_TEST.md T1 and the USB-only commands).** Over the socket, each must hold:

  | ID | Send | Must get |
  |---|---|---|
  | U1 | `HELLO` | exactly `HELLO RDP/1 haptic,olfactory,gustatory 0.60` |
  | U2 | `LOAD 1 0.40`, `H 0 300 300 3 0.40`, `START` | `MOTOR` lines forming 3 pulses at amplitude 0.40, then the motor at 0.00 |
  | U3 | `STOP` | a line starting `STOPPED` |
  | U4 | `PASSKEY` | `PASSKEY ` and six digits, a valid passkey under rsos_link (`valid_passkey`) |
  | U5 | `PAIR` | exactly `PAIR open 120` |
  | U6 | `UNPAIR` | exactly `UNPAIR all` |
  | U7 | `NEWKEY`, then `PASSKEY` | exactly `NEWKEY done; read it with PASSKEY`, then a valid passkey different from U4's |
  | U8 | a line of 100 letters | exactly `ERR LINE too-long`, and the next `HELLO` is answered normally |
  | U9 | restart the emulator on the same flash file, then `PASSKEY` | the passkey from U7 (kept in flash, P2) |

- **E4 Board check.** `python -m rsso.board --port socket://localhost:<port>` (B1–B7), then the same with `--full`
  (B1–B7 plus the conformance suite in real time). The thresholds stay as they are (B2 ±15 ms, B4 ≤ 100 ms, and every
  conformance limit). QEMU does not run in step with real time, so a timing result in emulation is recorded as an
  emulation result: it is not a claim about a board, in either direction.
- **E5 What emulation does not show.** Results never claim radio behaviour, pairing, phone prompts, the window
  with a real host, link loss on a real link, PWM on a pin, the motor's feel or timing on a board, the thermal,
  site or display hardware.

## 4. Emulator-only build flag (only if E2 shows Bluetooth start-up failing in the emulator)

The emulator has no Bluetooth controller. If E2 records a crash, a reset loop or a hang in Bluetooth start-up with the
unchanged real image, then:

- **Q1** The sketch gains one flag, `RSOS_EMULATOR`. With it, `setup()` makes or reads the passkey exactly as now,
  prints `NOTE emulator build: Bluetooth off`, and returns before `link.begin` and `BLEDevice::init`, as the existing
  "no passkey" path already does. Nothing else changes: USB lines, the core, USB-only commands and the line limit run
  the same code. The bond functions called by `UNPAIR` and `NEWKEY` (`esp_ble_get_bond_device_num` and the
  others) must not be called without a started Bluetooth stack in this build, so under the flag `removeAllBonds()`
  returns at once (there are no bonds without Bluetooth).
- **Q2** The flag is never set by default: not in `platformio.ini`, not in the board kit, not in any C1 build. Without
  it the real build is byte-for-byte the code it is now apart from the guarded lines, and keeps every Bluetooth rule.
- **Q3** `rsso/tests/test_ble_pairing.py` checks that the flag appears only as `#ifdef RSOS_EMULATOR` guards around
  the Bluetooth start-up and the bond removal, that `platformio.ini` and the C1 builds do not set it, and the stub
  check compiles both with and without it.
- **Q4** Emulator images in §3 that need it are built with `-DRSOS_EMULATOR` and are labelled so in the results.

If Bluetooth start-up does not fail in the emulator, §4 is not applied and nothing is added.

## 5. B — board check over a socket

`rsso/rsso/board.py` opens the port with `serial.Serial(path)`, which does not accept pyserial URLs such as
`socket://`. **B1** `open_port` uses `serial.serial_for_url(path, baudrate=baud, timeout=0.01)`, which opens plain port
names exactly as before and also URLs. The 2 s wait and the input flush stay. A test in `rsso/tests/test_board.py`
checks that a `socket://` URL reaches a listening socket and that a plain name goes through the same call.

## 6. Fix registrations (amendments, each committed before its fix)

(none yet)

## 7. Results

(recorded after the runs, in a separate commit)

## 8. Reproduce

`firmware/esp32/real_check.py` (added with the code of this step) runs the matrix and the emulator checks from a
workspace with arduino-cli, both cores and the QEMU binaries, and writes `rsso/results/esp32_tools.md`. The commands
it runs are listed in its header.

## 9. Documentation after results

HANDOFF_DEV.md gets a section for this step; BOARD_KIT.md's status line and MICRO's status on the architecture map
(`architecture/build.py`, regenerated) say what was checked with real compilers and in emulation, and keep "not yet
run on a board" for everything in E5. Nothing moves to "checked on hardware".
