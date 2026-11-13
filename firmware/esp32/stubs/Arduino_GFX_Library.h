// Stand-in for the Arduino_GFX library (moononournation/Arduino_GFX), compile-check only.
#pragma once
#include <stdint.h>
class Arduino_DataBus {};
class Arduino_ESP32SPI : public Arduino_DataBus { public: Arduino_ESP32SPI(int8_t, int8_t, int8_t, int8_t, int8_t) {} };
class Arduino_GFX {
 public:
  virtual ~Arduino_GFX() {}
  bool begin() { return true; }
  void fillScreen(uint16_t) {}
  void draw16bitRGBBitmap(int16_t, int16_t, uint16_t*, int16_t, int16_t) {}
};
class Arduino_GC9A01 : public Arduino_GFX { public: Arduino_GC9A01(Arduino_DataBus*, int8_t, uint8_t, bool) {} };
