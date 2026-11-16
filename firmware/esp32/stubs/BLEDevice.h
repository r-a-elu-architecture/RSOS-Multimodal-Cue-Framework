#pragma once
#include <string>
#include <stdint.h>
#include "Arduino.h"
#include "esp_gap_ble_api.h"
class BLEServer;
class BLECharacteristic;
struct BLEServerCallbacks { virtual ~BLEServerCallbacks() {} virtual void onConnect(BLEServer*) {} virtual void onConnect(BLEServer*, esp_ble_gatts_cb_param_t*) {} virtual void onDisconnect(BLEServer*) {} };
struct BLECharacteristicCallbacks { virtual ~BLECharacteristicCallbacks() {} virtual void onWrite(BLECharacteristic*) {} };
struct BLEDescriptor { virtual ~BLEDescriptor() {} void setAccessPermissions(esp_gatt_perm_t) {} };
class BLECharacteristic {
 public:
  enum { PROPERTY_NOTIFY = 1, PROPERTY_WRITE = 2, PROPERTY_WRITE_NR = 4 };
  void addDescriptor(BLEDescriptor*) {}
  void setCallbacks(BLECharacteristicCallbacks*) {}
  void setAccessPermissions(esp_gatt_perm_t) {}
  void setValue(uint8_t*, size_t) {}
  void notify() {}
#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
  String getValue() { return String(); }        // Arduino-ESP32 3.x (FIXES_R6 B8)
#else
  std::string getValue() { return ""; }       // Arduino-ESP32 2.x
#endif
};
struct BLEAdvertising { void start() {} void addServiceUUID(const char*) {} };
struct BLEService { BLECharacteristic* createCharacteristic(const char*, int) { return new BLECharacteristic(); } void start() {} };
class BLEServer {
 public:
  void setCallbacks(BLEServerCallbacks*) {}
  BLEService* createService(const char*) { return new BLEService(); }
  BLEAdvertising* getAdvertising() { static BLEAdvertising a; return &a; }
  void disconnect(uint16_t) {}
};
struct BLEDevice {
  static void init(const char*) {}
  static BLEServer* createServer() { return new BLEServer(); }
  static void setEncryptionLevel(esp_ble_sec_act_t) {}
  static void setCustomGapHandler(void (*)(esp_gap_ble_cb_event_t, esp_ble_gap_cb_param_t*)) {}
};
