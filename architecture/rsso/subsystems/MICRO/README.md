# MICRO — Edge runtime

**Function:** Runs symbolic reflexes on edge devices (watches, wearables, IoT): receives RSX commands and context, executes them locally.

**Status:** **Complete in simulation** — built and tested end to end with virtual and simulated hardware; awaiting a check on real devices

**Now:** Built: the runtime that plays RSX timelines on any set of devices; the portable C++ device core and an ESP32 wristband sketch (`firmware/`); the installable offline player app; the conformance suite, which the firmware core passes 15/15 in the host simulator; the board kit (`firmware/BOARD_KIT.md`: parts, wiring, Arduino IDE, arduino-cli and PlatformIO builds for ESP32, -C3 and -S3, the sketch compiled with the real toolchains, Arduino-ESP32 2.0.17 and 3.3.12 for the ESP32 and 2.0.17 and 3.2.1 for the -C3 and -S3, with and without the modules, and capped in hardware at the safety envelope) and the board check (`python -m rsso.board --port`, B1–B7 plus the whole conformance suite in real time; the same check in the browser on the Wristband page over USB or Bluetooth), passing 7/7 against the firmware core in real time. Bluetooth is paired and encrypted (`spec/BLE_PAIRING.md`, `spec/FIXES_R6.md` §5): LE Secure Connections with a six-digit passkey made on the band and never sent over the air, new pairings only in a two-minute window, USB-only pairing commands; compiled with the real toolchains, with the pairing policy tested on the host. In Espressif's QEMU emulator the compiled firmware, built without Bluetooth (QEMU has none), passes the USB commands and the board check (`spec/ESP32_TOOLS.md`). Awaiting: the first run on a real board, for the radio, pairing with a phone and the motor's feel and timing.

## Sources in the archive

| Source file | What it is | SHA-256 (first 16) |
|---|---|---|
| [MICRO_Historical_Reconstruction.txt](../../../../archive/original-estates/RSSO_PASS31B/MICRO_Historical_Reconstruction.txt) | Reconstruction: role, inputs, outputs, operators | `99291f25925d31b4` |
| [MICRO_Evidence_Excerpts.txt](../../../../archive/original-estates/RSSO_PASS31B/MICRO_Evidence_Excerpts.txt) | Evidence excerpts (public edition) | `c22c20d2341b9abc` |
