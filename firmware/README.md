# RSOS firmware

Device-side reference implementation of the [RSOS Device Protocol (RDP/1)](../spec/DEVICE_PROTOCOL.md).

| Folder | What it is | Status |
|---|---|---|
| `rsos_core/` | Portable C++11 device core: plays haptic and scent/taste events on the device's own clock; stop, intensity limit, consent, 3 s release cap, stop on link loss. No dynamic memory or dependencies. `host_sim` runs it on a PC with simulated time. | Tested: passes the 15-check conformance suite through the host simulator (`python -m rsso.conformance --firmware`), plus protocol, link-loss and timing tests (`rsso/tests/test_firmware.py`); pulse timing matches the RSX timeline to the millisecond |
| `esp32/rsos_esp32/` | Arduino-ESP32 sketch for a wristband or scent module: USB serial and Bluetooth LE (Nordic UART Service), PWM vibration motor, scent and taste outputs. Uses an identical copy of the core. | Compile-checked on a PC against API stubs (`esp32/stubs/`) for Arduino-ESP32 2.x and 3.x; builds with Arduino IDE, arduino-cli or PlatformIO (`esp32/platformio.ini`); **not yet flashed or run on a board**: [board kit](BOARD_KIT.md) |

```bash
cd firmware/rsos_core && make && printf 'HELLO\nLOAD 1 0.4\nH 0 300 300 3 0.4\nSTART\nTICK 2000\nQUIT\n' | ./host_sim
```

## Building and checking a wristband

See the **[board kit](BOARD_KIT.md)**: parts, wiring, flashing (Arduino IDE, arduino-cli, PlatformIO), and the board check `python -m rsso.board --port …` (B1–B7, plus the whole conformance suite in real time with `--full`), also available in the browser on the [Wristband page](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/device.html).

Keep `esp32/rsos_esp32/rsos_core.*` identical to `rsos_core/`; a test checks this.
