// RSOS wristband, scent module and RDP/1.1 modules for ESP32 (Arduino core 2.x or 3.x).
// Speaks RDP/1 with the RDP/1.1 channel lines (spec/DEVICE_PROTOCOL.md) over USB serial and over Bluetooth LE
// (Nordic UART Service).
//
// Always: a vibration motor through a MOSFET or driver on MOTOR_PIN (PWM); optional scent and taste valves or
// atomisers on SCENT_PIN / TASTE_PIN (on/off).
// Build flags add the modules (firmware/BOARD_KIT.md §8; their logic is rsos_modules.*, tested in simulation):
//   -DRSOS_THERMAL  wrist cooling and warming: Peltier element through a DRV8833 H-bridge (runs from the 3.7 V battery), skin and heat-sink thermistors,
//                   battery sense; the safety cut-offs act on every control step, whatever the host sends.
//   -DRSOS_SITES    up to six LRA motors, each with a DRV2605L, behind a TCA9548A I2C multiplexer.
//   -DRSOS_DISPLAY  a round 240x240 GC9A01 display; images are files /img/<name>.rgb (RGB565) in LittleFS.
//
// rsos_core.* and rsos_modules.* are copies of firmware/rsos_core/ (tested on the host with host_sim and module_sim);
// keep them identical (rsso/tests/test_firmware.py checks this).
// STATUS: compile-checked on a PC against stubs for Arduino-ESP32 2.x and 3.x, with and without the modules;
// not yet run on a board. Flash and check it with firmware/BOARD_KIT.md.
//
// Bluetooth is paired and encrypted (spec/BLE_PAIRING.md): LE Secure Connections with a six-digit passkey made on
// first start and kept in flash; new hosts can pair only in a 120 s window after power-on or USB PAIR; PASSKEY,
// PAIR, UNPAIR and NEWKEY act only over USB. The policy is rsos_link.* (a copy of firmware/rsos_core/, host-tested).
// Uses the Bluedroid BLE stack (not a NimBLE build).

#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLE2902.h>
#include <Preferences.h>
#include <esp_gap_ble_api.h>
#include "rsos_core.h"
#include "rsos_link.h"
#include "rsos_modules.h"
#ifdef RSOS_SITES
#include <Wire.h>
#endif
#ifdef RSOS_DISPLAY
#include <Arduino_GFX_Library.h>
#include <LittleFS.h>
#endif

// Pins: override with build flags, e.g. -DRSOS_MOTOR_PIN=5 (firmware/esp32/platformio.ini sets them per board)
#ifndef RSOS_MOTOR_PIN
#define RSOS_MOTOR_PIN 25
#endif
#ifndef RSOS_SCENT_PIN
#define RSOS_SCENT_PIN 26
#endif
#ifndef RSOS_TASTE_PIN
#define RSOS_TASTE_PIN 27
#endif
const int MOTOR_PIN = RSOS_MOTOR_PIN, SCENT_PIN = RSOS_SCENT_PIN, TASTE_PIN = RSOS_TASTE_PIN;
const int PWM_FREQ = 20000, PWM_BITS = 8, PWM_CHANNEL = 0;
#ifndef ESP_ARDUINO_VERSION_MAJOR
#define ESP_ARDUINO_VERSION_MAJOR 2
#endif
#define NUS_SERVICE "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
#define NUS_RX      "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
#define NUS_TX      "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

BLECharacteristic* txChar = nullptr;
BLEServer* bleServer = nullptr;
volatile bool bleConnected = false;
bool bleWasConnected = false;
// Link state (spec/BLE_PAIRING.md). Set in the Bluetooth task, read in loop().
volatile bool linkAuthed = false;      // P1: lines are accepted only on an authenticated, encrypted link
volatile bool newKeys = false;         // keys exchanged in this connection: a new host
volatile bool dropLink = false;        // a refused pairing: disconnect from loop()
volatile uint16_t bleConnId = 0;
volatile int8_t keyScreen = -1;      // 1 show the passkey, 0 clear it; drawn in loop(), not in the Bluetooth task
rsos::LinkPolicy link;
uint32_t passkey = 0;                  // never sent over Bluetooth (P2)
Preferences prefs;
// Bytes written by the host, handed from the Bluetooth task to loop() (one producer, one consumer).
const int RX_RING = 512;
uint8_t rxRing[RX_RING];
volatile int rxHead = 0, rxTail = 0;
rsos::LineBuffer usbBuf, bleBuf;

// PWM on both Arduino-ESP32 APIs: 3.x by pin, 2.x by channel.
static void pwmAttach(int pin, int channel, int freq) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  (void)channel; ledcAttach(pin, freq, PWM_BITS);
#else
  ledcSetup(channel, freq, PWM_BITS); ledcAttachPin(pin, channel);
#endif
}
static void pwmWrite(int pin, int channel, float level) {
  int duty = (int)(level * ((1 << PWM_BITS) - 1) + 0.5f);
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  (void)channel; ledcWrite(pin, duty);
#else
  (void)pin; ledcWrite(channel, duty);
#endif
}

void sendLine(const char* line);

// ------------------------------------------------------------------ cooling and warming (-DRSOS_THERMAL)
#ifdef RSOS_THERMAL
#ifndef RSOS_PELTIER_IN1
#define RSOS_PELTIER_IN1 16       // H-bridge (DRV8833, both bridges in parallel: AIN1+BIN1, AIN2+BIN2): IN1 high = warm the skin side, IN2 high = cool it
#endif
#ifndef RSOS_PELTIER_IN2
#define RSOS_PELTIER_IN2 17
#endif
#ifndef RSOS_SKIN_NTC_PIN
#define RSOS_SKIN_NTC_PIN 34      // 10 kΩ NTC (B 3950) to ground, 10 kΩ from 3V3: on the plate, against the skin
#endif
#ifndef RSOS_SINK_NTC_PIN
#define RSOS_SINK_NTC_PIN 35      // the same, glued to the heat sink
#endif
#ifndef RSOS_BATTERY_PIN
#define RSOS_BATTERY_PIN 32       // battery through a 100 kΩ / 100 kΩ divider
#endif
rsos::ThermalController thermalCtl;
uint32_t thermalLast = 0;

// Thermistor from the divider voltage; false when the reading is at a rail (open or shorted wire).
static bool ntcRead(int pin, float* c) {
  float mv = analogReadMilliVolts(pin);
  if (mv < 80 || mv > 3220) return false;
  float r = 10000.0f * mv / (3300.0f - mv);
  *c = 1.0f / (1.0f / 298.15f + logf(r / 10000.0f) / 3950.0f) - 273.15f;
  return true;
}
static void peltier(float duty) {             // duty -1..1, positive warms the skin
  float a = duty > 0 ? duty : 0, b = duty < 0 ? -duty : 0;
  pwmWrite(RSOS_PELTIER_IN1, 2, a);
  pwmWrite(RSOS_PELTIER_IN2, 3, b);
}
static void thermalLoop(uint32_t now) {
  if (now - thermalLast < 50) return;         // 20 control steps a second
  thermalLast = now;
  rsos::ThermalInputs in;
  in.skin_ok = ntcRead(RSOS_SKIN_NTC_PIN, &in.skin_c);
  in.sink_ok = ntcRead(RSOS_SINK_NTC_PIN, &in.sink_c);
  in.battery_v = analogReadMilliVolts(RSOS_BATTERY_PIN) * 2.0f / 1000.0f;
  peltier(thermalCtl.step(in, now));
  if (thermalCtl.fault_new()) {
    char buf[64]; snprintf(buf, sizeof buf, "FAULT %lu thermal %s", (unsigned long)now, thermalCtl.fault()); sendLine(buf);
  }
}
#endif

// ------------------------------------------------------------------ several body sites (-DRSOS_SITES)
#ifdef RSOS_SITES
const uint8_t MUX = 0x70, DRV = 0x5A;
rsos::SiteDriver siteDrv(170);                // the LRA's resonance; set it to your motors' rated frequency
bool sitePresent[rsos::SiteDriver::kSites];
uint32_t siteLast = 0;

static void muxSelect(int ch) { Wire.beginTransmission(MUX); Wire.write((uint8_t)(1 << ch)); Wire.endTransmission(); }
static bool drvWrite(uint8_t reg, uint8_t v) { Wire.beginTransmission(DRV); Wire.write(reg); Wire.write(v); return Wire.endTransmission() == 0; }
static void sitesBegin() {
  Wire.begin();
  for (int s = 0; s < rsos::SiteDriver::kSites; s++) {
    muxSelect(s);
    sitePresent[s] = drvWrite(0x01, 0x00);     // MODE: out of standby (an answer means a driver is there)
    if (!sitePresent[s]) continue;
    drvWrite(0x1A, 0xB6);                       // FEEDBACK: LRA, closed loop
    drvWrite(0x16, 0x3E);                       // RATED_VOLTAGE for a 2 V rms LRA
    drvWrite(0x17, 0x8C);                       // OD_CLAMP
    drvWrite(0x1D, 0xA8);                       // CONTROL3: real-time playback data unsigned
    drvWrite(0x01, 0x05);                       // MODE: real-time playback
    drvWrite(0x02, 0);                          // RTP input: off
  }
}
static void sitesLoop(uint32_t now) {
  if (now - siteLast < 5) return;               // the rhythm as an envelope, updated every 5 ms
  siteLast = now;
  for (int s = 0; s < rsos::SiteDriver::kSites; s++) {
    if (!sitePresent[s]) continue;
    muxSelect(s);
    drvWrite(0x02, siteDrv.rtp(s, now));
  }
}
#endif

// ------------------------------------------------------------------ display (-DRSOS_DISPLAY)
#ifdef RSOS_DISPLAY
#ifndef RSOS_TFT_DC
#define RSOS_TFT_DC 33
#endif
#ifndef RSOS_TFT_CS
#define RSOS_TFT_CS 15
#endif
#ifndef RSOS_TFT_SCK
#define RSOS_TFT_SCK 18
#endif
#ifndef RSOS_TFT_MOSI
#define RSOS_TFT_MOSI 23
#endif
#ifndef RSOS_TFT_RST
#define RSOS_TFT_RST 4
#endif
#ifndef RSOS_TFT_BL
#define RSOS_TFT_BL 13
#endif
Arduino_DataBus* tftBus = new Arduino_ESP32SPI(RSOS_TFT_DC, RSOS_TFT_CS, RSOS_TFT_SCK, RSOS_TFT_MOSI, -1);
Arduino_GFX* tft = new Arduino_GC9A01(tftBus, RSOS_TFT_RST, 0, true);
rsos::DisplayGate dispGate;
uint16_t rowBuf[240];

static void backlight(float level) { pwmWrite(RSOS_TFT_BL, 1, level); }
static bool showImage(const char* name) {
  if (!rsos::DisplayGate::valid_name(name)) return false;
  char path[40]; snprintf(path, sizeof path, "/img/%s.rgb", name);
  File f = LittleFS.open(path, "r");
  if (!f || f.size() != 240 * 240 * 2) { if (f) f.close(); return false; }
  for (int y = 0; y < 240; y++) {
    f.read((uint8_t*)rowBuf, sizeof rowBuf);
    tft->draw16bitRGBBitmap(0, y, rowBuf, 240, 1);
  }
  f.close();
  return true;
}
#endif

class Hardware : public rsos::Output {
 public:
  void motor(float amp) override { pwmWrite(MOTOR_PIN, PWM_CHANNEL, amp); }
#ifdef RSOS_SITES
  void site(int s, float amp, int carrier_hz, int mod_hz) override {
    if (s < 0 || s >= rsos::SiteDriver::kSites) return;
    siteDrv.set(s, amp, carrier_hz, mod_hz, millis());
    if (!sitePresent[s] && s == 0) motor(amp);   // no driver on the left wrist: the band's own motor plays it
    if (amp > 0 && siteDrv.carrier_mismatch(s)) {
      char buf[64]; snprintf(buf, sizeof buf, "NOTE carrier %s plays at %d Hz", rsos::kSiteNames[s], siteDrv.resonance()); send(buf);
    }
  }
#else
  // A single-motor band plays every site on its one motor (carrier and rhythm need an LRA driver: -DRSOS_SITES).
  void site(int, float amp, int, int) override { motor(amp); }
#endif
#ifdef RSOS_THERMAL
  void thermal(float delta_c) override { thermalCtl.command(delta_c); if (delta_c == 0) peltier(0); }
#endif
#ifdef RSOS_DISPLAY
  void display(const char* image, bool on) override {
    if (!on) { backlight(0); tft->fillScreen(0); return; }
    if (showImage(image)) backlight(dispGate.brightness(1.0f));
    else { char buf[64]; snprintf(buf, sizeof buf, "NOTE image %s missing", image); send(buf); }
  }
  void night(bool on) override { dispGate.night(on); }
#endif
  void valve(char ch, bool open) override { digitalWrite(ch == 'O' ? SCENT_PIN : TASTE_PIN, open ? HIGH : LOW); }
  void send(const char* line) override {
    Serial.println(line);
    if (bleConnected && linkAuthed && txChar) { String s = String(line) + "\n"; txChar->setValue((uint8_t*)s.c_str(), s.length()); txChar->notify(); }
  }
};

Hardware hw;
// Capabilities follow the build; the hardware cap (0.6) is the device safety envelope (spec/CONTAIN.md), whatever a host asks.
rsos::Core core(hw, "haptic,olfactory,gustatory"
#ifdef RSOS_THERMAL
                    ",thermal"
#endif
#ifdef RSOS_DISPLAY
                    ",display"
#endif
                , 0.6f);
void sendLine(const char* line) { hw.send(line); }

class ServerCB : public BLEServerCallbacks {
  void onConnect(BLEServer*, esp_ble_gatts_cb_param_t* param) override {
    bleConnId = param->connect.conn_id; linkAuthed = false; newKeys = false; bleConnected = true;
    // FIXES_R6C S2: the band asks for encryption only while the window is open. Outside it a bonded host encrypts with
    // its stored key when it reads or writes; an unknown host must start pairing itself, and SecurityCB refuses it.
    if (link.accept_request(millis())) esp_ble_set_encryption(param->connect.remote_bda, ESP_BLE_SEC_ENCRYPT_MITM);
  }
  void onDisconnect(BLEServer* s) override { linkAuthed = false; newKeys = false; bleConnected = false; s->getAdvertising()->start(); }
};
class RxCB : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic* c) override {
    if (!linkAuthed) return;                                   // P1: dropped, never reaches the core
    String v = c->getValue().c_str();   // std::string on 2.x, Arduino String on 3.x (FIXES_R6 B8)
    for (size_t i = 0; i < v.length(); i++) {
      int next = (rxHead + 1) % RX_RING;
      if (next == rxTail) return;                              // full: the rest is dropped; the line will be too long or malformed
      rxRing[rxHead] = (uint8_t)v[i]; rxHead = next;
    }
  }
};

int bondCount() { return esp_ble_get_bond_device_num(); }
bool bonded(const uint8_t* addr) {   // FIXES_R6 B7
  int n = bondCount(); if (n <= 0) return false;
  esp_ble_bond_dev_t list[16]; if (n > 16) n = 16;
  esp_ble_get_bond_device_list(&n, list);
  for (int i = 0; i < n; i++) if (memcmp(list[i].bd_addr, addr, 6) == 0) return true;
  return false;
}
void removeAllBonds() {
  int n = bondCount(); if (n <= 0) return;
  esp_ble_bond_dev_t list[16]; if (n > 16) n = 16;
  esp_ble_get_bond_device_list(&n, list);
  for (int i = 0; i < n; i++) esp_ble_remove_bond_device(list[i].bd_addr);
}

#ifdef RSOS_DISPLAY
void showPasskey(bool on) {
  if (!on) { backlight(0); tft->fillScreen(0); return; }
  char buf[8]; snprintf(buf, sizeof buf, "%06lu", (unsigned long)passkey);
  tft->fillScreen(0); tft->setTextColor(0xFFFF); tft->setTextSize(4); tft->setCursor(48, 104); tft->print(buf);
  backlight(dispGate.brightness(1.0f));
}
#endif

// GAP events from the Bluetooth task: decide new pairings with the policy (P3-P5).
void gapEvent(esp_gap_ble_cb_event_t event, esp_ble_gap_cb_param_t* param) {
  switch (event) {
    case ESP_GAP_BLE_KEY_EVT: newKeys = true; break;
    case ESP_GAP_BLE_PASSKEY_NOTIF_EVT: if (link.show_passkey(millis())) keyScreen = 1; break;   // B6
    case ESP_GAP_BLE_AUTH_CMPL_EVT: {
      keyScreen = 0;
      if (!param->ble_security.auth_cmpl.success) { link.on_auth_fail(millis()); linkAuthed = false; dropLink = true; break; }
      if (newKeys) {
        rsos::LinkPolicy::Decision d = link.on_new_bond(millis(), bondCount() - 1);   // the new bond is already stored
        if (d != rsos::LinkPolicy::kAccept) { esp_ble_remove_bond_device(param->ble_security.auth_cmpl.bd_addr); linkAuthed = false; dropLink = true; break; }
      } else if (!bonded(param->ble_security.auth_cmpl.bd_addr)) {   // B7: no keys exchanged and not a known host
        linkAuthed = false; dropLink = true; break;
      }
      linkAuthed = true;
      break;
    }
    default: break;
  }
}

// FIXES_R6C S1: the library answers a pairing the host starts with onSecurityRequest(); without these callbacks it
// answers true. Same interface in Arduino-ESP32 2.0.17 and 3.0.7.
class SecurityCB : public BLESecurityCallbacks {
  uint32_t onPassKeyRequest() override { return 0; }              // the band does not enter keys
  void onPassKeyNotify(uint32_t) override {}                       // shown by gapEvent (B6)
  bool onSecurityRequest() override { return link.accept_request(millis()); }
  void onAuthenticationComplete(esp_ble_auth_cmpl_t) override {}  // decided by gapEvent (P3-P5, B7)
  bool onConfirmPIN(uint32_t) override { return false; }          // numeric comparison is not used
};

void setSecurity() {
  uint32_t pk = passkey;
  esp_ble_gap_set_security_param(ESP_BLE_SM_SET_STATIC_PASSKEY, &pk, sizeof pk);
  esp_ble_auth_req_t auth = ESP_LE_AUTH_REQ_SC_MITM_BOND;
  esp_ble_gap_set_security_param(ESP_BLE_SM_AUTHEN_REQ_MODE, &auth, sizeof auth);
  esp_ble_io_cap_t io = ESP_IO_CAP_OUT;
  esp_ble_gap_set_security_param(ESP_BLE_SM_IOCAP_MODE, &io, sizeof io);
  uint8_t only = ESP_BLE_ONLY_ACCEPT_SPECIFIED_AUTH_ENABLE;
  esp_ble_gap_set_security_param(ESP_BLE_SM_ONLY_ACCEPT_SPECIFIED_SEC_AUTH, &only, sizeof only);
  uint8_t size = 16, keys = ESP_BLE_ENC_KEY_MASK | ESP_BLE_ID_KEY_MASK;
  esp_ble_gap_set_security_param(ESP_BLE_SM_MAX_KEY_SIZE, &size, sizeof size);
  esp_ble_gap_set_security_param(ESP_BLE_SM_SET_INIT_KEY, &keys, sizeof keys);
  esp_ble_gap_set_security_param(ESP_BLE_SM_SET_RSP_KEY, &keys, sizeof keys);
}

uint32_t newPasskey() {
  uint32_t pk = rsos::LinkPolicy::make_passkey(esp_random);
  prefs.putUInt("passkey", pk);
  return pk;
}

// USB-only commands (P6): physical access to the cable is the authorisation. Answers go to USB only.
void usbCommand(const char* line, uint32_t now) {
  char out[48];
  while (*line == ' ' || *line == '\t') line++;
  if (strncmp(line, "PASSKEY", 7) == 0) { snprintf(out, sizeof out, "PASSKEY %06lu", (unsigned long)passkey); Serial.println(out); }
  else if (strncmp(line, "UNPAIR", 6) == 0) { removeAllBonds(); dropLink = true; Serial.println("UNPAIR all"); }
  else if (strncmp(line, "NEWKEY", 6) == 0) { passkey = newPasskey(); setSecurity(); removeAllBonds(); dropLink = true; Serial.println("NEWKEY done; read it with PASSKEY"); }
  else if (strncmp(line, "PAIR", 4) == 0) { link.open_window(now); snprintf(out, sizeof out, "PAIR open %lu", (unsigned long)(rsos::LinkPolicy::kWindowMs / 1000)); Serial.println(out); }
}

void onLine(rsos::LinkSource src, rsos::LineBuffer::Result r, const char* line, uint32_t now) {
  if (r == rsos::LineBuffer::kTooLong) { sendLine("ERR LINE too-long"); return; }   // P7
  if (r != rsos::LineBuffer::kLine) return;
  if (rsos::LinkPolicy::usb_only(line)) {
    if (src == rsos::kUsb) usbCommand(line, now);
    else sendLine("ERR LINK usb-only");
    return;
  }
  core.line(line, now);
}

void setup() {
  Serial.begin(115200);
  pwmAttach(MOTOR_PIN, PWM_CHANNEL, PWM_FREQ);
  pinMode(SCENT_PIN, OUTPUT); pinMode(TASTE_PIN, OUTPUT);
  digitalWrite(SCENT_PIN, LOW); digitalWrite(TASTE_PIN, LOW);
  hw.motor(0);
#ifdef RSOS_THERMAL
  pwmAttach(RSOS_PELTIER_IN1, 2, PWM_FREQ); pwmAttach(RSOS_PELTIER_IN2, 3, PWM_FREQ);
  peltier(0);
#endif
#ifdef RSOS_SITES
  sitesBegin();
#endif
#ifdef RSOS_DISPLAY
  pwmAttach(RSOS_TFT_BL, 1, 5000); backlight(0);
  LittleFS.begin(true);
  tft->begin(); tft->fillScreen(0);
#endif
  prefs.begin("rsos", false);
  passkey = prefs.getUInt("passkey", 0);
  if (!rsos::LinkPolicy::valid_passkey(passkey)) passkey = newPasskey();
  if (!rsos::LinkPolicy::valid_passkey(passkey)) { Serial.println("NOTE no passkey; Bluetooth off"); return; }   // USB still works
  link.begin(millis());
  BLEDevice::init("RSOS-band");
  BLEDevice::setEncryptionLevel(ESP_BLE_SEC_ENCRYPT_MITM);
  BLEDevice::setCustomGapHandler(gapEvent);
  BLEDevice::setSecurityCallbacks(new SecurityCB());   // S1
  setSecurity();
  BLEServer* srv = BLEDevice::createServer(); srv->setCallbacks(new ServerCB()); bleServer = srv;
  BLEService* svc = srv->createService(NUS_SERVICE);
  txChar = svc->createCharacteristic(NUS_TX, BLECharacteristic::PROPERTY_NOTIFY);
  txChar->setAccessPermissions(ESP_GATT_PERM_READ_ENC_MITM);
  BLE2902* cccd = new BLE2902();
  cccd->setAccessPermissions(ESP_GATT_PERM_READ_ENC_MITM | ESP_GATT_PERM_WRITE_ENC_MITM);
  txChar->addDescriptor(cccd);
  BLECharacteristic* rx = svc->createCharacteristic(NUS_RX, BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_WRITE_NR);
  rx->setAccessPermissions(ESP_GATT_PERM_WRITE_ENC_MITM);
  rx->setCallbacks(new RxCB());
  svc->start(); srv->getAdvertising()->addServiceUUID(NUS_SERVICE); srv->getAdvertising()->start();
}

void loop() {
  uint32_t now = millis();
  while (Serial.available()) {
    char c = Serial.read();
    rsos::LineBuffer::Result r = usbBuf.push(c);
    onLine(rsos::kUsb, r, usbBuf.line(), now);
  }
  while (rxTail != rxHead) {
    char c = (char)rxRing[rxTail]; rxTail = (rxTail + 1) % RX_RING;
    if (!linkAuthed) continue;
    rsos::LineBuffer::Result r = bleBuf.push(c);
    onLine(rsos::kBle, r, bleBuf.line(), now);
  }
#ifdef RSOS_DISPLAY
  if (keyScreen >= 0) { showPasskey(keyScreen == 1); keyScreen = -1; }
#endif
  if (dropLink) { dropLink = false; if (bleServer && bleConnected) bleServer->disconnect(bleConnId); }
  if (bleWasConnected && !bleConnected) { core.link_lost(now); bleBuf = rsos::LineBuffer(); rxTail = rxHead; }   // B9: nothing carries over   // spec §4.6: stop on link loss
  bleWasConnected = bleConnected;
  core.update(now);
#ifdef RSOS_THERMAL
  thermalLoop(now);
#endif
#ifdef RSOS_SITES
  sitesLoop(now);
#endif
  delay(1);
}
