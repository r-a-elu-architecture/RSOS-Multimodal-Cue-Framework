#!/bin/sh
# Review R6: host checks of the ESP32 sketch beyond the author's stubs. Usage: sh review/r6/ble_checks.sh <repo>
# 1. getValue() with the Arduino-ESP32 3.x return type (String) instead of the stub's std::string.
# 2. The sketch's GAP decision logic driven with event sequences (review/r6/gap_sim.cpp).
set -e
REPO=$(cd "$1" && pwd); HERE=$(cd "$(dirname "$0")" && pwd); W=$(mktemp -d)
cp -r "$REPO/firmware/esp32/stubs" "$REPO/firmware/esp32/rsos_esp32" "$W/"
cd "$W"
python3 - <<'PY'
s = open('stubs/BLEDevice.h').read()
s = s.replace('  std::string getValue() { return ""; }', '#if ESP_ARDUINO_VERSION_MAJOR >= 3\n  String getValue() { return String(""); }\n#else\n  std::string getValue() { return ""; }\n#endif')
open('stubs/BLEDevice.h', 'w').write(s)
a = open('stubs/Arduino.h').read().replace('inline uint32_t millis() { return 0; }', 'extern uint32_t g_ms; inline uint32_t millis() { return g_ms; }')
open('stubs/Arduino.h', 'w').write(a)
e = open('stubs/esp_gap_ble_api.h').read().replace('inline int esp_ble_get_bond_device_num() { return 0; }', 'extern int g_bonds; inline int esp_ble_get_bond_device_num() { return g_bonds; }')
open('stubs/esp_gap_ble_api.h', 'w').write(e)
PY
for M in 2 3; do
  if g++ -std=c++17 -fsyntax-only -DESP_ARDUINO_VERSION_MAJOR=$M -Istubs -Irsos_esp32 stubs/check.cpp -o /dev/null 2>err.txt; then echo "getValue as in Arduino-ESP32 $M.x: compiles"; else echo "getValue as in Arduino-ESP32 $M.x: $(grep -m1 error err.txt)"; fi
done
mkdir r && cp "$HERE/gap_sim.cpp" r/
g++ -std=c++17 -DESP_ARDUINO_VERSION_MAJOR=2 -Istubs -Irsos_esp32 r/gap_sim.cpp rsos_esp32/rsos_link.cpp rsos_esp32/rsos_core.cpp rsos_esp32/rsos_modules.cpp -o gap_sim
./gap_sim
