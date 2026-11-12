// Minimal stand-ins for the Arduino-ESP32 API, used only to compile-check rsos_esp32.ino on a PC.
#pragma once
#include <stdint.h>
#include <string>
#define HIGH 1
#define LOW 0
#define OUTPUT 1
class String {
 public:
  String() {}
  String(const char* s) : s_(s) {}
  String(const std::string& s) : s_(s) {}
  size_t length() const { return s_.size(); }
  const char* c_str() const { return s_.c_str(); }
  char operator[](size_t i) const { return s_[i]; }
  String& operator+=(char c) { s_ += c; return *this; }
  String operator+(const char* o) const { return String(s_ + o); }
  String& operator=(const char* o) { s_ = o; return *this; }
 private:
  std::string s_;
};
struct SerialT { void begin(long) {} void println(const char*) {} int available() { return 0; } char read() { return 0; } };
extern SerialT Serial;
inline uint32_t millis() { return 0; }
inline void delay(int) {}
inline void pinMode(int, int) {}
inline void digitalWrite(int, int) {}
#ifndef ESP_ARDUINO_VERSION_MAJOR
#define ESP_ARDUINO_VERSION_MAJOR 3
#endif
inline bool ledcAttach(int, int, int) { return true; }
inline double ledcSetup(int, int, int) { return 0; }
inline void ledcAttachPin(int, int) {}
inline void ledcWrite(int, int) {}
