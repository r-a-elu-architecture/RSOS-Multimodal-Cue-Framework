// RSOS module logic (RDP/1.1 channels) — portable, no Arduino dependencies, no dynamic memory.
// The same code runs in the host simulator (firmware/rsos_core/module_sim) and in the ESP32 sketch.
//
//  * ThermalController: closed-loop control of a Peltier element from a skin thermistor, with safety cut-offs that
//    act on every step, independent of the control loop and of anything the host sends.
//  * SiteDriver: per-site drive values for up to six LRA motors (DRV2605L real-time playback), with the slower
//    rhythm as an amplitude envelope.
//  * DisplayGate: image names, and brightness capped at night.
//
// spec/MACHINES.md §3 and §12; checks in rsso/rsso/modules.py.
#pragma once
#include <stdint.h>

namespace rsos {

struct ThermalInputs {
  float skin_c, sink_c, battery_v;
  bool skin_ok, sink_ok;          // false when the driver reads an open or shorted thermistor
};

class ThermalController {
 public:
  static constexpr float kSkinMaxC = 40.0f, kSkinMinC = 15.0f, kSinkMaxC = 45.0f, kBatteryMinV = 3.3f;   // sink: safe to touch for long
  static constexpr float kEnvelopeC = 4.0f, kTripC = 4.5f, kJumpC = 3.0f;
  static constexpr float kKp = 0.3f, kKi = 0.04f, kLagS = 1.0f, kIMax = 0.6f, kSlewPerS = 0.25f, kDutyMax = 0.8f, kTargetMaxC = 39.0f;

  ThermalController() { reset(); }
  void reset();
  // From Output::thermal: the requested change from skin temperature, 0 = neutral (off at once).
  void command(float delta_c);
  // One control step (call every 20-100 ms). Returns the duty -1..1 (positive warms the skin, 0 = off).
  float step(const ThermalInputs& in, uint32_t now_ms);
  // A fault turns the element off at once; nothing runs again until the cue has ended (command 0) and a new one
  // starts with every reading in range.
  const char* fault() const { return fault_; }       // nullptr when none
  bool fault_new() { bool f = fault_new_; fault_new_ = false; return f; }
  float target() const { return target_; }
  float baseline() const { return baseline_; }

 private:
  float trip(const char* why);
  float delta_, baseline_, target_, integ_, duty_, last_skin_, watch_skin_, watch_sink_, rate_;
  bool active_, have_last_, fault_new_, need_zero_;
  uint32_t last_ms_, watch_ms_, start_ms_, far_ms_;
  const char* fault_;
};

class SiteDriver {
 public:
  static const int kSites = 6;
  explicit SiteDriver(int resonance_hz = 170) : res_(resonance_hz) { for (int i = 0; i < kSites; i++) { amp_[i] = 0; mod_[i] = 0; car_[i] = 0; t0_[i] = 0; } }
  void set(int site, float amp, int carrier_hz, int mod_hz, uint32_t now_ms);
  // DRV2605L real-time playback value (unsigned, 0-255) for a site at now_ms.
  uint8_t rtp(int site, uint32_t now_ms) const;
  // True when a requested carrier is more than 20% away from the motor's resonance (an LRA plays at resonance).
  bool carrier_mismatch(int site) const;
  int resonance() const { return res_; }

 private:
  int res_;
  float amp_[kSites];
  int mod_[kSites], car_[kSites];
  uint32_t t0_[kSites];
};

class DisplayGate {
 public:
  static constexpr float kNightMax = 0.2f;
  DisplayGate() : night_(false) {}
  void night(bool on) { night_ = on; }
  bool is_night() const { return night_; }
  float brightness(float requested) const;
  // An image name is 1-23 characters of a-z, 0-9, _ and -: it names a file in flash, never a path.
  static bool valid_name(const char* name);

 private:
  bool night_;
};

}  // namespace rsos
