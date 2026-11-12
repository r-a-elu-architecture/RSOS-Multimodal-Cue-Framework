# RSOS board kit: build, flash and check a wristband

This guide takes you from parts to a wristband that passes the RSOS device checks. The firmware
(`esp32/rsos_esp32/`) is the same C++ core that passes all 15 conformance checks in the host simulator. This kit
is how it gets onto real hardware and how you prove it behaves the same there.

Status: the sketch is compile-checked for Arduino-ESP32 2.x and 3.x. It has not yet been run on a board in this
repository. The first board you build is that test, so please record the result (§6).

## 1. Parts

| Part | Example | Notes |
|---|---|---|
| ESP32 board | ESP32-DevKitC (classic ESP32), ESP32-C3 SuperMini, ESP32-S3 Zero | Any ESP32 with USB and Bluetooth LE |
| Vibration motor | 10 mm coin ERM motor, 3 V, about 70–90 mA | The kind used in phones and fitness bands |
| Motor switch | Logic-level N-MOSFET (AO3400, 2N7000 for small motors) or a DRV2605L haptic driver in PWM mode | The pin cannot drive the motor directly |
| Flyback diode | 1N4148 or 1N5819 | Across the motor; protects the MOSFET |
| Resistors | 100 Ω (gate), 100 kΩ (gate to ground) | Keeps the motor off while the board boots |
| Battery (for wearing) | 3.7 V LiPo, 300–500 mAh, with a TP4056 charger, or a board with a charger | USB power is enough for the checks |
| Optional: scent or taste | A 5 V piezo atomiser module or a small valve, switched like the motor | Only with an allergy check; see §5 |
| Strap and case | A watch strap and a small printed or bought enclosure | The motor sits against the wrist |

## 2. Wiring

```
 ESP32 3V3 ──────────────┬──────────── motor (+)
                         │
                       diode (cathode to 3V3)
                         │
                         └──────────── motor (−) ── MOSFET drain
 ESP32 MOTOR_PIN ── 100 Ω ── MOSFET gate
                              │
                           100 kΩ
                              │
 ESP32 GND ───────────────────┴──────── MOSFET source
```

| Board | Motor | Scent | Taste |
|---|---|---|---|
| ESP32 DevKitC (default) | GPIO 25 | GPIO 26 | GPIO 27 |
| ESP32-C3 | GPIO 5 | GPIO 6 | GPIO 7 |
| ESP32-S3 | GPIO 4 | GPIO 5 | GPIO 6 |

Different pins: set `-DRSOS_MOTOR_PIN=…` (and `RSOS_SCENT_PIN`, `RSOS_TASTE_PIN`) in `esp32/platformio.ini`, or
change the defaults at the top of `rsos_esp32.ino`. The motor is driven by 20 kHz PWM, which is silent. The
firmware never drives it above the program's limit (0.4 by default) or the device safety envelope (0.6).

## 3. Flash

Choose one of the three routes.

**Arduino IDE (2.x):**

1. Install "esp32 by Espressif Systems" from Boards Manager. Version 3.x and 2.x both work.
2. Open `firmware/esp32/rsos_esp32/rsos_esp32.ino`.
3. Choose your board and port, then press Upload.

**arduino-cli:**

```bash
arduino-cli core install esp32:esp32
arduino-cli compile --fqbn esp32:esp32:esp32 firmware/esp32/rsos_esp32
arduino-cli upload  --fqbn esp32:esp32:esp32 -p /dev/ttyUSB0 firmware/esp32/rsos_esp32
```

**PlatformIO:**

```bash
cd firmware/esp32
pio run -e esp32dev -t upload        # or -e esp32-c3, -e esp32-s3
pio device monitor                   # 115200 baud
```

## 4. First signs of life

Open a serial monitor at 115200 baud, line ending "Newline", and type:

```
HELLO                      → HELLO RDP/1 haptic,olfactory,gustatory 0.60   (the band's hard cap: the safety envelope)
LOAD 1 0.40
H 0 300 300 3 0.40
START                      → the motor pulses three times; MOTOR lines report each change
STOP                       → STOPPED
```

The band also advertises over Bluetooth LE as `RSOS-band`, using the Nordic UART Service.

## 5. Check it

You can check the band in three ways.

- **From the browser.** Open the [Wristband page](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/device.html) in Chrome or Edge, choose "Connect by USB" (or "Bluetooth" on Android), then "Run the check".
- **From a computer:**

  ```bash
  pip install pyserial
  cd rsso
  python -m rsso.board --port /dev/ttyUSB0 --out results/board_<your-board>.md        # B1–B7, about 15 s
  python -m rsso.board --port /dev/ttyUSB0 --full                                     # plus all 15 conformance checks in real time
  ```

  On Windows the port is `COM3`, `COM5` and so on; on a Mac it is `/dev/cu.usbserial-…`.
- **Without a board.** `python -m rsso.board --sim` runs the same checks against the firmware core in real time, which is how the checks themselves are tested.

| Check | Requires |
|---|---|
| B1 | The band answers `HELLO` with `RDP/1` and its capabilities |
| B2 | Three 300 ms pulses, 300 ms apart, on the band's own clock (±15 ms) |
| B3 | A pulse asked at 0.9 under a limit of 0.4 is clamped to 0.4 and reported (`CLAMPED`) |
| B4 | After `STOP` the motor is off and `STOPPED` arrives within 100 ms, link included |
| B5 | Without `CONSENT 1` a scent release is refused |
| B6 | A 5 s release closes by 3 s |
| B7 | The Lion's vibration code `..-` plays as 100, 100 and 300 ms pulses |

`--full` then runs the conformance suite C1–C15 in real time with the band as the vibration and scent device
(virtual audio and display). This takes a few minutes, because every check runs the Override Protocol at its
real length.

**Scent and taste.** Use them only after the wearer has confirmed no allergy or aversion (`CONSENT 1`, which the
player asks for). Keep the atomiser away from the face. The firmware caps every release at 3 s.

## 6. Record the result

Add the report to `rsso/results/board_<board>.md` (the `--out` file). Include the board, the motor, the driver,
the Arduino-ESP32 version and the date, then open a pull request or an issue. The first real-board report moves
MICRO and AUG from "complete in simulation" to "built and checked on hardware" on the system map.

## 7. Troubleshooting

| Symptom | Likely cause |
|---|---|
| No `HELLO` reply | Wrong port or baud rate; the board resets on connect, so wait 2 s; on ESP32-C3/S3 set "USB CDC On Boot: Enabled" |
| B2 fails: pulses too long or merged | The motor spins down slowly: use a coin ERM rather than a cylinder motor, or a DRV2605L; check the flyback diode |
| B3 fails | Old firmware: reflash; the clamp is in `rsos_core` |
| B4 fails above 100 ms | A USB hub or Bluetooth link adds delay: retry on direct USB. The band itself stops on the next millisecond tick |
| The motor buzzes at boot | Add the 100 kΩ gate-to-ground resistor |
| The board browns out when the motor starts | Power the motor from 3V3 with a 10 µF capacitor nearby, or from the battery through the MOSFET |
