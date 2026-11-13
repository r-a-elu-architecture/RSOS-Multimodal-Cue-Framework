#include "rsos_modules.h"

#include <math.h>

namespace rsos {

static float absf(float x) { return x < 0 ? -x : x; }
static float clampf(float x, float lo, float hi) { return x < lo ? lo : (x > hi ? hi : x); }

// ------------------------------------------------------------------ thermal

void ThermalController::reset() {
  delta_ = baseline_ = target_ = integ_ = duty_ = last_skin_ = watch_skin_ = watch_sink_ = rate_ = 0;
  active_ = have_last_ = fault_new_ = need_zero_ = false;
  last_ms_ = watch_ms_ = start_ms_ = far_ms_ = 0;
  fault_ = nullptr;
}

void ThermalController::command(float delta_c) {
  float d = clampf(delta_c, -kEnvelopeC, kEnvelopeC);       // the envelope, again, on the module itself
  if (d == 0) { delta_ = 0; active_ = false; duty_ = 0; integ_ = 0; need_zero_ = false; return; }
  if (need_zero_) return;                                   // after a fault, nothing runs until the cue has ended
  if (!active_) { delta_ = d; active_ = true; baseline_ = -1000; integ_ = 0; return; }   // baseline taken on the next step
  delta_ = d;
}

float ThermalController::trip(const char* why) {
  if (!fault_) { fault_ = why; fault_new_ = true; }
  duty_ = 0; integ_ = 0; active_ = false; need_zero_ = true;
  return 0;
}

float ThermalController::step(const ThermalInputs& in, uint32_t now) {
  float dt = have_last_ ? (now - last_ms_) / 1000.0f : 0.05f;
  if (dt <= 0 || dt > 1) dt = 0.05f;
  last_ms_ = now;
  // Safety first, on every step, whether or not a cue is playing.
  if (!in.skin_ok) return trip("skin-sensor");
  if (!in.sink_ok) return trip("sink-sensor");
  if (have_last_ && absf(in.skin_c - last_skin_) > kJumpC) { last_skin_ = in.skin_c; return trip("skin-sensor-jump"); }
  if (have_last_) rate_ += 0.1f * ((in.skin_c - last_skin_) / dt - rate_);     // smoothed rate of change, °C/s
  last_skin_ = in.skin_c; have_last_ = true;
  if (in.skin_c > kSkinMaxC || in.skin_c < kSkinMinC) return trip("skin-limit");
  if (in.sink_c > kSinkMaxC) return trip("sink-hot");
  if (in.battery_v < kBatteryMinV) return trip("battery");
  if (!active_) { duty_ = 0; return 0; }
  if (baseline_ < -999) {
    fault_ = nullptr;     // a new cue after the last one ended, with every reading back in range (checked above)
    baseline_ = in.skin_c; watch_ms_ = start_ms_ = far_ms_ = now; watch_skin_ = in.skin_c; watch_sink_ = in.sink_c;
  }
  if (absf(in.skin_c - baseline_) > kTripC) return trip("envelope");
  target_ = clampf(baseline_ + delta_, kSkinMinC + 1.0f, kTargetMaxC);
  float e = target_ - in.skin_c, since = (now - start_ms_) / 1000.0f;
  // A sensor that does not respond while the element works hard at the start of a cue: stuck, or off the skin.
  // (Later in a cue, holding a temperature needs a steady duty too, so this watches only the first 15 s.)
  if (since > 15.0f || absf(duty_) < 0.4f || absf(e) < 0.5f || absf(in.skin_c - watch_skin_) >= 0.2f) { watch_ms_ = now; watch_skin_ = in.skin_c; watch_sink_ = in.sink_c; }
  else {
    float held = (now - watch_ms_) / 1000.0f;
    if ((held >= 3.0f && absf(in.sink_c - watch_sink_) >= 0.5f) || held >= 5.0f) return trip("skin-not-responding");
  }
  // A module that cannot reach or hold the target (a covered heat sink, a loose strap) stops instead of working on.
  if (absf(e) < 1.5f || since < 20.0f) far_ms_ = now;
  else if ((now - far_ms_) / 1000.0f >= 20.0f) return trip("cannot-hold");
  // The thermistor lags the skin by about a second: control on where the skin will read a second from now.
  float ep = target_ - (in.skin_c + kLagS * rate_);
  float raw = kKp * ep + integ_;
  if (!((raw >= kDutyMax && ep > 0) || (raw <= -kDutyMax && ep < 0)))          // no integration while saturated: no wind-up
    integ_ = clampf(integ_ + kKi * ep * dt, -kIMax, kIMax);
  float want = clampf(kKp * ep + integ_, -kDutyMax, kDutyMax);
  float step_max = kSlewPerS * dt;                           // no thermal shock: the duty moves at most 0.25 a second
  duty_ = clampf(want, duty_ - step_max, duty_ + step_max);
  return duty_;
}

// ------------------------------------------------------------------ multi-site vibration

void SiteDriver::set(int site, float amp, int carrier_hz, int mod_hz, uint32_t now) {
  if (site < 0 || site >= kSites) return;
  if (amp > 0 && amp_[site] == 0) t0_[site] = now;
  amp_[site] = clampf(amp, 0, 1); car_[site] = carrier_hz; mod_[site] = mod_hz;
}

uint8_t SiteDriver::rtp(int site, uint32_t now) const {
  if (site < 0 || site >= kSites || amp_[site] <= 0) return 0;
  float env = 1;
  if (mod_[site] > 0) {
    float t = (now - t0_[site]) / 1000.0f;
    env = 0.5f - 0.5f * cosf(2.0f * 3.14159265f * mod_[site] * t);     // full-depth rhythm, starting from 0
  }
  int v = (int)(255.0f * amp_[site] * env + 0.5f);
  return (uint8_t)(v > 255 ? 255 : v);
}

bool SiteDriver::carrier_mismatch(int site) const {
  if (site < 0 || site >= kSites || car_[site] == 0) return false;
  return absf((float)car_[site] - res_) > 0.2f * res_;
}

// ------------------------------------------------------------------ display

float DisplayGate::brightness(float requested) const {
  float b = clampf(requested, 0, 1);
  return night_ && b > kNightMax ? kNightMax : b;
}

bool DisplayGate::valid_name(const char* name) {
  if (!name || !name[0]) return false;
  int n = 0;
  for (const char* p = name; *p; p++, n++) {
    char c = *p;
    if (n >= 23) return false;
    if (!((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '_' || c == '-')) return false;
  }
  return true;
}

}  // namespace rsos
