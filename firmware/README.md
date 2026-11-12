# RSOS firmware

Device-side reference implementation of the [RSOS Device Protocol (RDP/1)](../spec/DEVICE_PROTOCOL.md).

| Folder | What it is | Status |
|---|---|---|
| `rsos_core/` | Portable C++11 device core: plays haptic and scent/taste events on the device's own clock; stop, intensity limit, consent, 3 s release cap, stop on link loss. No dynamic memory or dependencies. `host_sim` runs it on a PC with simulated time. | Tested: passes the 11-check conformance suite through the host simulator (`python -m rsso.conformance --firmware`), plus protocol, link-loss and timing tests (`rsso/tests/test_firmware.py`); pulse timing matches the RSX timeline to the millisecond |
| `esp32/rsos_esp32/` | Arduino-ESP32 sketch for a wristband or scent module: USB serial and Bluetooth LE (Nordic UART Service), PWM vibration motor, scent and taste outputs. Uses an identical copy of the core. | Compile-checked on a PC against API stubs (`esp32/stubs/`); **not yet flashed or run on a board** |

```bash
cd firmware/rsos_core && make && printf 'HELLO\nLOAD 1 0.4\nH 0 300 300 3 0.4\nSTART\nTICK 2000\nQUIT\n' | ./host_sim
```

## Building a wristband

Parts: an ESP32 board (e.g. ESP32-DevKitC or a small ESP32-S3/C3 board), a coin vibration motor with a logic-level MOSFET or a motor driver (e.g. DRV2605L in PWM mode), flyback diode, LiPo battery and charger; optionally a piezo atomiser or valve driver for scent on GPIO 26.

1. Open `esp32/rsos_esp32/rsos_esp32.ino` in the Arduino IDE with the ESP32 core (3.x; on 2.x replace `ledcAttach` with `ledcSetup` + `ledcAttachPin`).
2. Set `MOTOR_PIN`, `SCENT_PIN` and `TASTE_PIN` for your wiring, flash, and open the serial monitor at 115200.
3. Type `HELLO` and `LOAD 1 0.4`, `H 0 300 300 3 0.4`, `START`: the motor should pulse three times and report `MOTOR` lines.
4. Run the conformance suite against the real board with a serial transport (see `rsso/rsso/protocol.py`; a transport needs `send(line)` and a way to read lines).

Keep `esp32/rsos_esp32/rsos_core.*` identical to `rsos_core/`; a test checks this.
