// RSOS wristband / scent module for ESP32 (Arduino core 2.x or 3.x).
// Speaks RDP/1 (spec/DEVICE_PROTOCOL.md) over USB serial and over Bluetooth LE (Nordic UART Service).
// Hardware: vibration motor through a MOSFET or driver on MOTOR_PIN (PWM); optional scent and taste
// valves or atomisers on SCENT_PIN / TASTE_PIN (on/off).
//
// rsos_core.cpp / rsos_core.h are copies of firmware/rsos_core/ (tested on the host with host_sim);
// keep them identical (rsx/tests/test_repository.py checks this).
// STATUS: written for the ESP32 Arduino core; not yet compiled or run on a board in this repository.

#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLE2902.h>
#include "rsos_core.h"

const int MOTOR_PIN = 25, SCENT_PIN = 26, TASTE_PIN = 27;
const int PWM_FREQ = 20000, PWM_BITS = 8;
#define NUS_SERVICE "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
#define NUS_RX      "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
#define NUS_TX      "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

BLECharacteristic* txChar = nullptr;
bool bleConnected = false, bleWasConnected = false;
String bleLine;
volatile bool bleLineReady = false;

class Hardware : public rsos::Output {
 public:
  void motor(float amp) override { ledcWrite(MOTOR_PIN, (int)(amp * ((1 << PWM_BITS) - 1))); }
  void valve(char ch, bool open) override { digitalWrite(ch == 'O' ? SCENT_PIN : TASTE_PIN, open ? HIGH : LOW); }
  void send(const char* line) override {
    Serial.println(line);
    if (bleConnected && txChar) { String s = String(line) + "\n"; txChar->setValue((uint8_t*)s.c_str(), s.length()); txChar->notify(); }
  }
};

Hardware hw;
rsos::Core core(hw, "haptic,olfactory,gustatory", 1.0f);

class ServerCB : public BLEServerCallbacks {
  void onConnect(BLEServer*) override { bleConnected = true; }
  void onDisconnect(BLEServer* s) override { bleConnected = false; s->getAdvertising()->start(); }
};
class RxCB : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic* c) override {
    String v = c->getValue().c_str();
    for (size_t i = 0; i < v.length(); i++) {
      if (v[i] == '\n') { bleLineReady = true; return; }
      bleLine += v[i];
    }
  }
};

void setup() {
  Serial.begin(115200);
  ledcAttach(MOTOR_PIN, PWM_FREQ, PWM_BITS);          // Arduino-ESP32 3.x API; on 2.x use ledcSetup + ledcAttachPin
  pinMode(SCENT_PIN, OUTPUT); pinMode(TASTE_PIN, OUTPUT);
  digitalWrite(SCENT_PIN, LOW); digitalWrite(TASTE_PIN, LOW);
  hw.motor(0);
  BLEDevice::init("RSOS-band");
  BLEServer* srv = BLEDevice::createServer(); srv->setCallbacks(new ServerCB());
  BLEService* svc = srv->createService(NUS_SERVICE);
  txChar = svc->createCharacteristic(NUS_TX, BLECharacteristic::PROPERTY_NOTIFY);
  txChar->addDescriptor(new BLE2902());
  BLECharacteristic* rx = svc->createCharacteristic(NUS_RX, BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_WRITE_NR);
  rx->setCallbacks(new RxCB());
  svc->start(); srv->getAdvertising()->addServiceUUID(NUS_SERVICE); srv->getAdvertising()->start();
}

String serialLine;

void loop() {
  uint32_t now = millis();
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') { core.line(serialLine.c_str(), now); serialLine = ""; }
    else if (c != '\r' && serialLine.length() < 95) serialLine += c;
  }
  if (bleLineReady) { core.line(bleLine.c_str(), now); bleLine = ""; bleLineReady = false; }
  if (bleWasConnected && !bleConnected) core.link_lost(now);   // spec §4.6: stop on link loss
  bleWasConnected = bleConnected;
  core.update(now);
  delay(1);
}
