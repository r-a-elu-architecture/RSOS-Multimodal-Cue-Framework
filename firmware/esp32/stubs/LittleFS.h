// Stand-in for the ESP32 LittleFS API, compile-check only.
#pragma once
#include <stddef.h>
#include <stdint.h>
class File {
 public:
  explicit operator bool() const { return false; }
  size_t size() const { return 0; }
  size_t read(uint8_t*, size_t n) { return n; }
  void close() {}
};
struct LittleFSFS { bool begin(bool) { return true; } File open(const char*, const char*) { return File(); } };
extern LittleFSFS LittleFS;
