// Stand-in for the Arduino-ESP32 Preferences (NVS) library; compile-check only.
#pragma once
#include <stdint.h>
class Preferences {
 public:
  bool begin(const char*, bool) { return true; }
  uint32_t getUInt(const char*, uint32_t d) { return d; }
  size_t putUInt(const char*, uint32_t) { return 4; }
};
