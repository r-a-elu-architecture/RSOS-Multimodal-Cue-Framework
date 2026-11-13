// RSOS Device Protocol (RDP/1, with the RDP/1.1 channel lines) — portable device core.
// Plays RSX haptic and scent/taste events, and the RDP/1.1 temperature, image and multi-site vibration events, on the device's own clock, enforces the safety rules of
// spec/DEVICE_PROTOCOL.md §4, and reports every output change. No dynamic memory, no exceptions,
// no dependencies: the same code runs in the host simulator and on a microcontroller.
#pragma once
#include <stdint.h>

namespace rsos {

// What the hardware (or the simulator) must provide.
class Output {
 public:
  virtual ~Output() {}
  virtual void motor(float amp) = 0;              // 0..1 of hardware maximum
  virtual void valve(char channel, bool open) = 0; // 'O' scent, 'G' taste
  virtual void send(const char* line) = 0;        // one protocol line to the host (no newline)
  // RDP/1.1 channels. Defaults do nothing, so a band without these outputs needs no change.
  virtual void thermal(float delta_c) { (void)delta_c; }                  // change from skin temperature, °C
  virtual void display(const char* image, bool on) { (void)image; (void)on; }
  virtual void site(int site, float amp, int carrier_hz, int mod_hz) { (void)site; (void)amp; (void)carrier_hz; (void)mod_hz; }
};

// RDP/1.1 envelope, enforced on the device whatever the host sends (spec/MACHINES.md §3).
static const float kThermalMaxC = 4.0f;
static const uint32_t kThermalMaxMs = 120000, kDisplayMaxMs = 10000;
static const int kThermalPerRun = 4, kSitesAtOnce = 3, kSites = 6;
extern const char* const kSiteNames[kSites];

struct TEvent { uint32_t t, dur; float delta; };
struct DEvent { uint32_t t, dur; char image[24]; };
struct FEvent { uint32_t t, on, off; uint16_t count; float amp; uint16_t carrier, mod; uint8_t site; bool refused_reported; };

struct HEvent { uint32_t t, on, off; uint16_t count; float amp; };
struct SEvent { uint32_t t, dur; char ch; bool refused_reported; };

class Core {
 public:
  static const int kMaxEvents = 64;
  static const uint32_t kMaxRelease = 3000;

  Core(Output& out, const char* capabilities, float motor_max);
  void line(const char* text, uint32_t now_ms);   // a line received from the host
  void update(uint32_t now_ms);                   // call often (every 1-5 ms on hardware)
  void link_lost(uint32_t now_ms);                // the host connection dropped

  enum State { kIdle, kLoading, kLoaded, kPlaying };
  State state() const { return state_; }

 private:
  void stop_outputs(uint32_t rel);
  void apply(uint32_t rel);
  bool next_boundary(uint32_t after, uint32_t* t) const;
  float motor_at(uint32_t rel) const;
  bool valve_at(const SEvent& s, uint32_t rel) const;
  float site_at(int site, uint32_t rel, int* carrier, int* mod) const;
  bool caps_has(const char* c) const;
  void sendf(const char* fmt, ...);

  Output& out_;
  const char* caps_;
  float motor_max_, haptic_max_, motor_now_;
  bool consent_, valve_open_[kMaxEvents];
  State state_;
  int expected_, nh_, ns_;
  HEvent h_[kMaxEvents];
  SEvent s_[kMaxEvents];
  int nt_, nd_, nf_;
  TEvent t_[8];
  DEvent d_[16];
  FEvent f_[32];
  float thermal_now_, site_now_[kSites];
  bool disp_on_[16];
  uint32_t t0_, last_rel_, end_;
};

}  // namespace rsos
