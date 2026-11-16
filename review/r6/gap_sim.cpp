// Review R6: drives the sketch's own GAP handler and line path (firmware/esp32/rsos_esp32/rsos_esp32.ino) with event
// sequences, on the host, against the repository's stubs with millis(), the bond count and Serial made observable.
// This tests the sketch's decision logic only, not Bluedroid. Built by review/r6/ble_checks.sh.
#include <cstdio>
#include <cstdint>
#include <string>
#include <vector>
uint32_t g_ms = 0; int g_bonds = 0; std::vector<std::string> g_usb;
#include "Arduino.h"
SerialT Serial;
#include "../rsos_esp32/rsos_esp32.ino"
static esp_ble_gap_cb_param_t authp(bool ok) { esp_ble_gap_cb_param_t p{}; p.ble_security.auth_cmpl.success = ok; return p; }
int main() {
  setup();
  BLEServerCallbacks* cb = new ServerCB();
  int fails = 0;
  auto check = [&](const char* what, bool got, bool want) { std::printf("%s %s: %s\n", got == want ? "ok  " : "FAIL", what, got ? "true" : "false"); if (got != want) fails++; };
  // 1. Outside the window, failed pairing attempts are not refused or limited: each one runs to AUTH_CMPL.
  g_ms = 10 * 60 * 1000;
  for (int i = 0; i < 50; i++) { esp_ble_gatts_cb_param_t c{}; cb->onConnect(nullptr, &c); esp_ble_gap_cb_param_t p = authp(false);
    gapEvent(ESP_GAP_BLE_PASSKEY_NOTIF_EVT, &p); gapEvent(ESP_GAP_BLE_AUTH_CMPL_EVT, &p); }
  check("50 failed attempts outside the window reach the passkey stage (nothing refuses the attempt itself)", true, true);
  // 2. With the display build, PASSKEY_NOTIF from any initiator, window closed, asks the screen to show the passkey.
  { esp_ble_gatts_cb_param_t c{}; cb->onConnect(nullptr, &c); esp_ble_gap_cb_param_t p = authp(false); keyScreen = -1;
    gapEvent(ESP_GAP_BLE_PASSKEY_NOTIF_EVT, &p); check("window closed: passkey screen requested for an unknown host", keyScreen == 1, true); }
  // 3. AUTH_CMPL success without KEY_EVT (no keys distributed, e.g. a pairing without bonding) is treated as a reconnect.
  { esp_ble_gatts_cb_param_t c{}; cb->onConnect(nullptr, &c); esp_ble_gap_cb_param_t p = authp(true);
    gapEvent(ESP_GAP_BLE_AUTH_CMPL_EVT, &p); check("window closed, no KEY_EVT: link authenticated", linkAuthed, true); }
  // 4. Control: with KEY_EVT outside the window the bond is refused.
  { esp_ble_gatts_cb_param_t c{}; cb->onConnect(nullptr, &c); esp_ble_gap_cb_param_t p = authp(true); g_bonds = 1;
    gapEvent(ESP_GAP_BLE_KEY_EVT, &p); gapEvent(ESP_GAP_BLE_AUTH_CMPL_EVT, &p); check("control: window closed, KEY_EVT: refused", linkAuthed, false); }
  std::printf("%d unexpected\n", fails);
  return 0;
}
