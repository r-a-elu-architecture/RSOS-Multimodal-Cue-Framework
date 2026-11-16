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

### 6.1 Amendment A1 (registered after round 1, §7.1; before any code)

| ID | Error | Fix |
|---|---|---|
| F1 | R1-a | The sketch's `rsos::LinkPolicy` object is renamed from `link` to `linkPolicy`; every use is renamed with it, nothing else changes. The stub `Arduino.h` declares POSIX `int link(const char*, const char*);`, as the real cores do through `<unistd.h>`, so the stub check fails on any global named `link`. `rsso/tests/test_ble_pairing.py` reads the new name (its FIXES_R6C checks look for `linkPolicy.accept_request(millis())` and the same rules as before). |
| F2 | R1-b | Encryption level: `BLESecurity::setEncryptionLevel(ESP_BLE_SEC_ENCRYPT_MITM)` when `ESP_ARDUINO_VERSION >= ESP_ARDUINO_VERSION_VAL(3, 3, 0)`, otherwise `BLEDevice::setEncryptionLevel(…)` as now (2.0.17 to 3.2.x). Same level, same call order. The stubs define `ESP_ARDUINO_VERSION`, `ESP_ARDUINO_VERSION_VAL` and a minor version (2 → 2.0, 3 → 3.3 unless given), and declare `setEncryptionLevel` only where the real library has it. |
| F3 | R1-c | **Not a port.** A NimBLE build stops with a clear message instead of failing on a missing header: right after `#include <Arduino.h>`, `#if defined(CONFIG_BT_NIMBLE_ENABLED)` gives `#error` saying that the pairing rules (spec/BLE_PAIRING.md) are implemented for the Bluedroid stack only, and that ESP32-C3 and -S3 must be built with Arduino-ESP32 3.2.1 or 2.0.17. Writing the pairing rules for NimBLE (window, failure limit, bond limit, refusal before keys are exchanged, bonded-host check) is a security change that needs its own registration and review; it is listed as an open item, not done here. |
| F4 | R1-d | `firmware/esp32/platformio.ini`'s display build pins `moononournation/GFX Library for Arduino@1.6.1` (PlatformIO's espressif32 platform uses Arduino-ESP32 2.0.17). BOARD_KIT.md says: with core 2.x, install GFX Library 1.6.1; with 3.x, the newest. |

Consequential changes to §2 and §3 (no threshold changes):
- **C1b.** ESP32-C3 and -S3 are also built with Arduino-ESP32 3.2.1 (the last 3.x that builds them with Bluedroid),
  five flag sets each: 10 more builds, under the C2 pass rule. ESP32 is not added (3.3.12 already builds it with
  Bluedroid).
- **C5 as registered stays.** The ten ESP32-C3/-S3 builds on 3.3.12 are expected to stop at F3's `#error`; they are
  then recorded as not passing C5, with the reason. They are not removed from the matrix.
- **E1b.** ESP32-C3 and -S3 are emulated with their 3.2.1 build (3.3.12 cannot build them, F3).
- The stub check stays at 10 builds (plus §4's builds, if §4 applies); `rsso/tests/test_ble_pairing.py` also checks
  that the sketch has no global named `link`, has the F3 guard, and that `platformio.ini` pins GFX 1.6.1 for the
  display build.

## 7. Results

### 7.1 Round 1: the unchanged sketch (dev 35d61d8), 30 builds — 0 passed

Tools as in §1 (arduino-cli 1.6.0; cores 2.0.17 and 3.3.12; GFX Library 1.6.9, the newest). The full diagnostics, as
printed, are in `rsso/results/esp32_tools/round1_errors.md`.

| Error | Builds | Message (first line, exactly) |
|---|---|---|
| R1-a | every build that reached the sketch: ESP32, -C3, -S3 on 2.0.17 (band, thermal, sites) and ESP32 on 3.3.12 (all five) | `rsos_esp32.ino:69:18: error: 'rsos::LinkPolicy link' redeclared as different kind of symbol` (2.0.17; 3.3.12 says `entity`), then `request for member '…' in 'link', which is of non-class type 'int(const char*, const char*)'` at lines 269, 313, 316, 318, 335, 368 and 404. The global `link` collides with POSIX `int link(const char*, const char*)` from `<unistd.h>`, which both cores include through `Arduino.h`. |
| R1-b | ESP32 on 3.3.12 (all five) | `rsos_esp32.ino:406:14: error: 'setEncryptionLevel' is not a member of 'BLEDevice'` — in 3.3.12 it is `BLESecurity::setEncryptionLevel`. |
| R1-c | ESP32-C3 and -S3 on 3.3.12 (all ten) | `rsos_esp32.ino:28:10: fatal error: esp_gap_ble_api.h: No such file or directory` — Arduino-ESP32 3.3.12 builds these chips with the NimBLE host (`CONFIG_BT_NIMBLE_ENABLED=y` in their `sdkconfig`; the ESP32 keeps `CONFIG_BT_BLUEDROID_ENABLED=y`). The sketch's pairing code is written for Bluedroid. |
| R1-d | display and all-modules builds on 2.0.17 (six) | `Arduino_ESP32SPI.h:21:10: fatal error: esp32-hal-periman.h: No such file or directory` — inside GFX Library 1.6.9, which needs the 3.x core. |

The stubs hid R1-a (they do not declare POSIX `link`) and R1-b (they declare `BLEDevice::setEncryptionLevel` for 3.x).
R1-c and R1-d are outside what the stubs model. Builds that stopped at R1-c or R1-d did not reach later errors.

Library selection under §1: GFX Library 1.6.1 is the newest release that compiles on 2.0.17 (1.6.2, 1.6.3, 1.6.4 and
1.6.8 fail with R1-d; 1.6.1, 1.6.0, 1.5.9, 1.5.0 and 1.4.9 compile the display build, tried with R1-a and R1-b
corrected in a scratch copy).

Probe (a scratch copy, not committed, before the amendment in §6): with R1-a and R1-b corrected and a NimBLE stop,
ESP32 on 3.3.12 with all modules, ESP32 on 2.0.17 with thermal and sites, and ESP32-C3 on 3.2.1 compiled with no
other error; ESP32-C3 on 3.2.1 is built with Bluedroid (`CONFIG_BT_BLUEDROID_ENABLED=y`), as are -S3 on 3.2.1.

### 7.2 E2: the real images in QEMU (code c4d9b8b, no emulator flag)

Images: no module flags; ESP32 with 3.3.12 and 2.0.17, ESP32-C3 and -S3 with 3.2.1 (A1, E1b). QEMU
esp_develop_9.2.2_20260417, UART0 on a TCP socket, 45 s each. Boot logs: `rsso/results/esp32_tools/e2_*.txt`.

- **Flash mode.** With Arduino's default `FlashMode=qio` the ESP32 image never reaches the sketch:
  `E (…) qio_mode: Failed to set QIE bit, not enabling QIO mode`, then
  `assert failed: __esp_system_init_fn_init_flash startup_funcs.c:118 (flash_ret == ESP_OK)`, then a reset, in a loop.
  The emulated flash does not take QIO. All runs below use the board option `FlashMode=dio` (no code change).
- **Bluetooth start-up fails in the emulator, on every image.** Each reaches `setup()` and stops in
  `BLEDevice::init`, which resets the chip; this repeats.

  | Image | First failure, exactly | Resets in 45 s |
  |---|---|---|
  | ESP32, 3.3.12 | `assert failed: btdm_low_power_mode_init bt.c:1564 (select_src_ret && set_div_ret)`; decoded: `esp_bt_controller_init` ← `btStartMode` (esp32-hal-bt.c:130) ← `btStart` ← `BLEDevice::init(String)` (BLEDevice.cpp:306) ← `setup()` (rsos_esp32.ino:408) | 4 |
  | ESP32, 2.0.17 | `assert failed: esp_bt_controller_init bt.c:1555 (select_src_ret && set_div_ret)`; decoded: `esp_bt_controller_init` ← `btStart` (esp32-hal-bt.c:46) ← `BLEDevice::init` (BLEDevice.cpp:339) ← `setup()` (rsos_esp32.ino:408) | 6 |
  | ESP32-C3, 3.2.1 | `assert failed: btdm_low_power_mode_init bt.c:1680 (select_src_ret && set_div_ret)` | 156 |
  | ESP32-S3, 3.2.1 | `assert failed: 0x4201f22b <cached disabled>:1680 (<cached disabled>)` (the same assertion line, printed while the cache was off) | 5 |

  So §4 applies: the emulator has no Bluetooth controller, and the real build cannot reach `loop()` there.
  None of U1–U9 or E4 can run on the unchanged image.
- Other emulator behaviour seen: on the 3.3.12 ESP32 image, after several resets, a `LoadProhibited` panic in
  `task_wdt_isr` (task_wdt.c:478); without the QEMU option `-global driver=timer.esp32.timg,property=wdt_disable,value=true`
  it also appeared on the first boot. In one scratch run of an emulator-flag image without that option, the first boot
  panicked (`Cache error`) in `initArduino` → `nvs_flash_init_partition` → `spi_flash_disable_interrupts_caches_and_other_cpu`,
  before `setup()`, then booted normally. Both are in start-up code that runs before the sketch.

Environment note: the first 2.0.17 attempt failed inside the core's esptool (`ModuleNotFoundError: No module named
'serial'`) until pyserial was installed for the workspace's Python; that is a tool set-up step, not a sketch error.

## 8. Reproduce

`firmware/esp32/real_check.py` (added with the code of this step) runs the matrix and the emulator checks from a
workspace with arduino-cli, both cores and the QEMU binaries, and writes `rsso/results/esp32_tools.md`. The commands
it runs are listed in its header.

## 9. Documentation after results

HANDOFF_DEV.md gets a section for this step; BOARD_KIT.md's status line and MICRO's status on the architecture map
(`architecture/build.py`, regenerated) say what was checked with real compilers and in emulation, and keep "not yet
run on a board" for everything in E5. Nothing moves to "checked on hardware".
