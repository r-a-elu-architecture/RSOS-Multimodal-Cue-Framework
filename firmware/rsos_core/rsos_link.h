// Pairing and line policy for the RSOS wristband link (spec/BLE_PAIRING.md). Portable C++11, no Arduino calls;
// tested on the host by link_test.cpp. The ESP32 sketch keeps a byte-identical copy.
#pragma once
#include <stdint.h>
#include <stddef.h>

namespace rsos {

enum LinkSource { kUsb, kBle };

class LinkPolicy {
 public:
  static const uint32_t kWindowMs = 120000;   // P3
  static const int kMaxFails = 3;             // P4
  static const int kMaxBonds = 4;             // P5
  enum Decision { kAccept, kRefuseClosed, kRefuseFull };

  void begin(uint32_t now) { open_window(now); }
  void open_window(uint32_t now) { until_ = now + kWindowMs; open_ = true; fails_ = 0; }   // power-on or USB PAIR
  bool window_open(uint32_t now) const { return open_ && (int32_t)(now - until_) < 0; }
  Decision on_new_bond(uint32_t now, int bonds_before) const;   // keys were exchanged: a new host
  // FIXES_R6 B5/B6: a pairing request is answered, and the passkey shown, only while the window is open (it closes
  // after kMaxFails failures), so passkey guesses are limited to the window too.
  bool accept_request(uint32_t now) const { return window_open(now); }
  bool show_passkey(uint32_t now) const { return window_open(now); }
  void on_auth_fail(uint32_t now);
  int fails() const { return fails_; }

  static bool valid_passkey(uint32_t pk);                        // P2
  static uint32_t make_passkey(uint32_t (*rnd)());
  static bool usb_only(const char* line);                        // P6: PASSKEY, PAIR, UNPAIR, NEWKEY

 private:
  uint32_t until_ = 0;
  bool open_ = false;
  int fails_ = 0;
};

// A bounded line buffer (P7): a line longer than kMax characters is dropped whole.
class LineBuffer {
 public:
  static const size_t kMax = 95;
  enum Result { kMore, kLine, kTooLong };
  Result push(char c);              // kLine: line() holds the line until the next push
  const char* line() const { return buf_; }

 private:
  char buf_[kMax + 1] = {0};
  size_t n_ = 0;
  bool over_ = false;
};

}  // namespace rsos
