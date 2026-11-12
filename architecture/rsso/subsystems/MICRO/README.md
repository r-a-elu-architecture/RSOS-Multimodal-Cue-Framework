# MICRO — Edge runtime

**Function:** Runs symbolic reflexes on edge devices (watches, wearables, IoT): receives RSX commands and context, executes them locally.

**Status:** **Complete in simulation** — built and tested end to end with virtual and simulated hardware; awaiting a check on real devices

**Now:** Built: the runtime that plays RSX timelines on any set of devices; the portable C++ device core and an ESP32 wristband sketch (`firmware/`); the installable offline player app; the conformance suite, which the firmware core passes 15/15 in the host simulator; the board kit (`firmware/BOARD_KIT.md`: parts, wiring, Arduino IDE, arduino-cli and PlatformIO builds for ESP32, -C3 and -S3, the sketch compile-checked for Arduino-ESP32 2.x and 3.x and capped in hardware at the safety envelope) and the board check (`python -m rsso.board --port`, B1–B7 plus the whole conformance suite in real time; the same check in the browser on the Wristband page over USB or Bluetooth), passing 7/7 against the firmware core in real time. Awaiting: the first run on a real board.

## Sources in the archive

| Source file | What it is | SHA-256 (first 16) |
|---|---|---|
| [MICRO_Historical_Reconstruction.txt](../../../../archive/original-estates/RSSO_PASS31B/MICRO_Historical_Reconstruction.txt) | Reconstruction: role, inputs, outputs, operators | `99291f25925d31b4` |
| [MICRO_Evidence_Excerpts.txt](../../../../archive/original-estates/RSSO_PASS31B/MICRO_Evidence_Excerpts.txt) | Evidence excerpts (public edition) | `c22c20d2341b9abc` |
