// Stand-in for the Arduino Wire (I2C) API, compile-check only.
#pragma once
#include <stdint.h>
struct TwoWire {
  void begin() {}
  void beginTransmission(uint8_t) {}
  size_t write(uint8_t) { return 1; }
  uint8_t endTransmission() { return 0; }
};
extern TwoWire Wire;
