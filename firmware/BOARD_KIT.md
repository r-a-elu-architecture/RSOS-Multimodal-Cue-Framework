# RSOS board kit: build, flash and check a wristband

This guide takes you from parts to a wristband that passes the RSOS device checks. The firmware
(`esp32/rsos_esp32/`) is the same C++ core that passes all 15 conformance checks in the host simulator. This kit
is how it gets onto real hardware and how you prove it behaves the same there.

Status: the sketch is compile-checked for Arduino-ESP32 2.x and 3.x. It has not yet been run on a board in this
repository. The first board you build is that test, so please record the result (§6).

## Which wristbands work

RSOS needs a band whose software you can replace, so that it can play RSOS vibration codes on its own clock and
stop on command. **Most brand watches do not allow that.**

| Device | Works | How |
|---|---|---|
| A band built from this kit (ESP32 and a coin motor) | Yes | Flash the RSOS firmware and run the board check |
| ESP32 wearables you can flash: LilyGO T-Watch, M5StickC and M5Stack, Watchy | Yes | The same firmware; set `RSOS_MOTOR_PIN` for the device |
| Any device that implements RDP/1 (spec/DEVICE_PROTOCOL.md) | Yes | The board check shows whether it complies |
| Android phones | Vibration only | The player vibrates the phone |
| Standard Bluetooth heart-rate straps and watches (Polar H10, Garmin HRM…) | As the stress trigger | They measure; they do not play RSOS codes |
| Open watches: PineTime, Bangle.js | Not yet | Open software: a port is possible and planned |
| Wear OS watches (Samsung Galaxy Watch, Pixel Watch, TicWatch) | Not yet | Needs an RSOS app on the watch, published on Google Play |
| Apple Watch | Not yet | Needs an RSOS app on the watch, published on the App Store |
| Fitbit, Garmin, Xiaomi Mi Band, Huawei, Whoop and other closed bands | No | The software cannot be replaced and there is no way to play custom patterns |
| iPhone | No vibration from the web | iPhone browsers do not let web pages vibrate |

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

- **From the browser.** Open the [Phones and wristbands page](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/device.html) in Chrome or Edge, choose "Connect by USB" (or "Bluetooth" on Android), then "Run the check".
- **From a computer:**

  ```bash
  pip install pyserial
  cd rsso
  python -m rsso.board --port /dev/ttyUSB0 --out results/board_<your-board>.md        # B1–B7, about 15 s
  python -m rsso.board --port /dev/ttyUSB0 --full                                     # plus all 15 conformance checks in real time
  ```

  On Windows the port is `COM3`, `COM5` and so on; on a Mac it is `/dev/cu.usbserial-…`.
- **Without a board.** `python -m rsso.board --sim` runs the same checks against the firmware core in real time, which is how the checks themselves are tested. With `--full` it passes all 22 checks, B1–B7 and C1–C15, in real time ([report](../rsso/results/board_check_sim_realtime.md)).

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

## 8. RDP/1.1 modules (software built, not yet assembled)

The firmware core runs the RDP/1.1 lines (11 of 11 channel checks, `rsso/results/channels_firmware.md`). The module code (`rsos_modules.*`: the thermal controller with its safety cut-offs, the multi-site driver, the display gate) passes 15 of 15 checks in simulation, the thermal controller against a physical model of the module (`rsso/results/modules.md`). The sketch drives each module when built with its flag; it is compile-checked for Arduino-ESP32 2.x and 3.x, but not yet run on a board.

| Module | Parts (about) | Build | Wiring (default pins, ESP32-DevKitC) |
|---|---|---|---|
| Wrist cooling and warming | Peltier element 20 × 20 mm (TEC1-03105 or similar, 3-5 W); DRV8871 H-bridge; two 10 kΩ NTC thermistors (B 3950) and two 10 kΩ resistors; aluminium heat sink 20 × 20 × 10 mm; 3.7 V LiPo 1000 mAh; 2 × 100 kΩ for battery sense. About $25-40 | `pio run -e thermal -t upload` | H-bridge IN1 → GPIO16, IN2 → GPIO17, output to the element (IN1 high warms the skin side; swap the element's wires if it cools). Skin thermistor: 3V3 → 10 kΩ → GPIO34 → NTC → GND, NTC glued to the plate's skin side with thermal paste. Heat-sink thermistor the same on GPIO35. Battery + → 100 kΩ → GPIO32 → 100 kΩ → GND |
| Several body sites | Up to six 10 mm LRA motors (170-235 Hz); a DRV2605L board per motor; a TCA9548A multiplexer; elastic straps. About $30-60 | `pio run -e sites -t upload` | SDA → GPIO21, SCL → GPIO22 to the TCA9548A; its channels 0-5 to the drivers in site order (left wrist, right wrist, upper arm, chest, upper back, ankle); each driver's output to its motor. Set the motors' rated frequency in `SiteDriver siteDrv(170)` |
| Image on a display | A 1.28 in round GC9A01 240 × 240 display. About $8-15 | `python make_image.py lion.png lion`, then `pio run -e display -t uploadfs` and `pio run -e display -t upload` | DC → GPIO33, CS → GPIO15, SCK → GPIO18, MOSI (SDA) → GPIO23, RST → GPIO4, backlight → GPIO13. All three modules can share one board: no pin is used twice (on ESP32-WROVER boards, move the H-bridge off GPIO16/17, which the PSRAM uses) |

Safety in the thermal module does not depend on the host: the element is off at once, and stays off until the cue ends and every reading is back in range, when the skin reads above 40 °C or below 15 °C, the heat sink above 45 °C (safe to touch), the battery below 3.3 V, a thermistor is open, shorted or jumps by more than 3 °C, the skin moves more than 4.5 °C from where the cue started, the skin does not respond at the start of a cue, or the target cannot be held for 20 s. Each fault is reported as `FAULT <t> thermal <reason>`. Keep the heat sink uncovered: after a hot-sink cut-off, heat leaks back and warms the skin by about 3 °C for a while.

### Bench checks for an assembled module

| Check | Module | What to do and what must happen |
|---|---|---|
| T1 | Cooling and warming | Power on, strap on, no cue: the module reports skin and sink temperature within 1 °C of a reference thermometer. |
| T2 | Cooling and warming | Play `T 0 60000 -2`: the skin side reaches 2 °C below the start within 20 s and holds it within 0.3 °C (reference thermometer under the plate). |
| T3 | Cooling and warming | Play `T 0 60000 3`, then send STOP at 20 s: THERMAL 0.00 is reported at once and the element current is zero (multimeter). |
| T4 | Cooling and warming | Unplug the skin thermistor during a cue: FAULT skin-sensor and zero current within 100 ms. |
| T5 | Cooling and warming | Lift the module off the skin at the start of a warm cue: FAULT skin-not-responding within 6 s. |
| T6 | Cooling and warming | Warm a thermistor with a finger to 41 °C equivalent (or a resistor of that value): FAULT skin-limit, element off. |
| S1 | Several sites | Play a two-part code spread over left wrist and chest: each part is felt on its site, in order. |
| S2 | Several sites | Play `HF 0 1000 0 1 0.5 0 6 chest`: the vibration pulses six times a second. |
| S3 | Several sites | Play four sites at once: three vibrate and REFUSED is reported for the fourth. |
| D1 | Display | Copy an image to flash and play `D 0 5000 <name>`: it shows for five seconds, then the screen is dark. |
| D2 | Display | Send `NIGHT 1`, then play an image: the backlight is at most 20% (light meter or a phone camera at fixed exposure). |

Record each result as a contribution (the Contribute page) with the module, parts and readings; the module's status then moves to "built and checked on hardware".
