#pragma once
#include <string>
#include "Arduino.h"
class BLEServer;
class BLECharacteristic;
struct BLEServerCallbacks { virtual ~BLEServerCallbacks() {} virtual void onConnect(BLEServer*) {} virtual void onDisconnect(BLEServer*) {} };
struct BLECharacteristicCallbacks { virtual ~BLECharacteristicCallbacks() {} virtual void onWrite(BLECharacteristic*) {} };
struct BLEDescriptor { virtual ~BLEDescriptor() {} };
class BLECharacteristic {
 public:
  enum { PROPERTY_NOTIFY = 1, PROPERTY_WRITE = 2, PROPERTY_WRITE_NR = 4 };
  void addDescriptor(BLEDescriptor*) {}
  void setCallbacks(BLECharacteristicCallbacks*) {}
  void setValue(uint8_t*, size_t) {}
  void notify() {}
  std::string getValue() { return ""; }
};
struct BLEAdvertising { void start() {} void addServiceUUID(const char*) {} };
struct BLEService { BLECharacteristic* createCharacteristic(const char*, int) { return new BLECharacteristic(); } void start() {} };
class BLEServer {
 public:
  void setCallbacks(BLEServerCallbacks*) {}
  BLEService* createService(const char*) { return new BLEService(); }
  BLEAdvertising* getAdvertising() { static BLEAdvertising a; return &a; }
};
struct BLEDevice { static void init(const char*) {} static BLEServer* createServer() { return new BLEServer(); } };
