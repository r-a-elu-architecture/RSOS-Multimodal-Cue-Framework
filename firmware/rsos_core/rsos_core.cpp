#include "rsos_core.h"

#include <stdarg.h>
#include <stdio.h>
#include <string.h>

namespace rsos {

Core::Core(Output& out, const char* capabilities, float motor_max)
    : out_(out), caps_(capabilities), motor_max_(motor_max), haptic_max_(0), motor_now_(0),
      consent_(false), state_(kIdle), expected_(0), nh_(0), ns_(0), t0_(0), last_rel_(0), end_(0) {
  for (int i = 0; i < kMaxEvents; i++) valve_open_[i] = false;
}

void Core::sendf(const char* fmt, ...) {
  char buf[96];
  va_list ap;
  va_start(ap, fmt);
  vsnprintf(buf, sizeof buf, fmt, ap);
  va_end(ap);
  out_.send(buf);
}

static float minf(float a, float b) { return a < b ? a : b; }

void Core::line(const char* text, uint32_t now) {
  char cmd[12] = {0};
  if (sscanf(text, "%11s", cmd) != 1) return;
  if (!strcmp(cmd, "HELLO")) {
    sendf("HELLO RDP/1 %s %.2f", caps_, motor_max_);
  } else if (!strcmp(cmd, "CONSENT")) {
    int c;
    if (sscanf(text, "CONSENT %d", &c) == 1 && (c == 0 || c == 1)) { consent_ = c == 1; sendf("OK CONSENT"); }
    else sendf("ERR CONSENT syntax");
  } else if (!strcmp(cmd, "LOAD")) {
    int n; float hm;
    if (state_ == kPlaying) { sendf("ERR LOAD playing"); return; }
    if (sscanf(text, "LOAD %d %f", &n, &hm) != 2 || n < 0 || hm <= 0 || hm > 1) { sendf("ERR LOAD syntax"); return; }
    if (n > kMaxEvents) { sendf("ERR LOAD too-many-events"); state_ = kIdle; return; }
    expected_ = n; nh_ = ns_ = 0; end_ = 0; haptic_max_ = minf(hm, motor_max_);
    state_ = n == 0 ? kLoaded : kLoading;
    sendf("OK LOAD");
  } else if (!strcmp(cmd, "H") || !strcmp(cmd, "S")) {
    if (state_ != kLoading) { sendf("ERR %s not-loading", cmd); return; }
    if (cmd[0] == 'H') {
      unsigned long t, on, off, count; float amp;
      if (sscanf(text, "H %lu %lu %lu %lu %f", &t, &on, &off, &count, &amp) != 5 || count < 1 || count > 50 || on == 0) {
        sendf("ERR H syntax"); return;
      }
      float lim = minf(amp, haptic_max_);
      if (lim < amp) sendf("CLAMPED %lu %.2f %.2f", t, amp, haptic_max_);
      HEvent e = {(uint32_t)t, (uint32_t)on, (uint32_t)off, (uint16_t)count, lim < 0 ? 0 : lim};
      h_[nh_++] = e;
      uint32_t e_end = e.t + (e.on + e.off) * e.count;
      if (e_end > end_) end_ = e_end;
    } else {
      unsigned long t, dur; char ch;
      if (sscanf(text, "S %lu %lu %c", &t, &dur, &ch) != 3 || (ch != 'O' && ch != 'G')) { sendf("ERR S syntax"); return; }
      uint32_t d = dur > kMaxRelease ? kMaxRelease : (uint32_t)dur;
      SEvent e = {(uint32_t)t, d, ch, false};
      s_[ns_++] = e;
      if (e.t + d > end_) end_ = e.t + d;
    }
    if (nh_ + ns_ == expected_) state_ = kLoaded;
  } else if (!strcmp(cmd, "START")) {
    if (state_ != kLoaded) { sendf("ERR START not-loaded"); return; }
    for (int i = 0; i < ns_; i++) { s_[i].refused_reported = false; valve_open_[i] = false; }
    t0_ = now; last_rel_ = 0; state_ = kPlaying; motor_now_ = 0;
    sendf("OK START");
    apply(0);
  } else if (!strcmp(cmd, "STOP")) {
    if (state_ == kPlaying) { update(now); stop_outputs(now - t0_); sendf("STOPPED %lu", (unsigned long)(now - t0_)); }
    else sendf("OK STOP");
    if (state_ != kIdle) state_ = kIdle;
  } else if (!strcmp(cmd, "STATUS")) {
    const char* s = state_ == kPlaying ? "playing" : (state_ == kLoaded ? "loaded" : "idle");
    sendf("STATE %s %lu", s, (unsigned long)(state_ == kPlaying ? now - t0_ : 0));
  } else {
    sendf("ERR %s unknown", cmd);
  }
}

float Core::motor_at(uint32_t rel) const {
  float a = 0;
  for (int i = 0; i < nh_; i++) {
    const HEvent& e = h_[i];
    uint32_t period = e.on + e.off;
    if (rel < e.t || rel >= e.t + period * e.count) continue;
    if ((rel - e.t) % period < e.on && e.amp > a) a = e.amp;
  }
  return a;
}

bool Core::valve_at(const SEvent& s, uint32_t rel) const { return rel >= s.t && rel < s.t + s.dur; }

bool Core::next_boundary(uint32_t after, uint32_t* t) const {
  bool found = false; uint32_t best = 0;
  for (int i = 0; i < nh_; i++) {
    const HEvent& e = h_[i];
    uint32_t period = e.on + e.off;
    for (uint16_t k = 0; k < e.count; k++) {
      uint32_t a = e.t + k * period, b = a + e.on;
      if (a > after && (!found || a < best)) { best = a; found = true; }
      if (b > after && (!found || b < best)) { best = b; found = true; }
    }
  }
  for (int i = 0; i < ns_; i++) {
    uint32_t a = s_[i].t, b = s_[i].t + s_[i].dur;
    if (a > after && (!found || a < best)) { best = a; found = true; }
    if (b > after && (!found || b < best)) { best = b; found = true; }
  }
  *t = best;
  return found;
}

void Core::apply(uint32_t rel) {
  float m = motor_at(rel);
  if (m != motor_now_) { motor_now_ = m; out_.motor(m); sendf("MOTOR %lu %.2f", (unsigned long)rel, m); }
  for (int i = 0; i < ns_; i++) {
    bool want = valve_at(s_[i], rel);
    if (want && !consent_) {
      if (!s_[i].refused_reported) { s_[i].refused_reported = true; sendf("REFUSED %lu %c consent", (unsigned long)rel, s_[i].ch); }
      want = false;
    }
    if (want != valve_open_[i]) {
      valve_open_[i] = want; out_.valve(s_[i].ch, want);
      sendf("SCENT %lu %c %d", (unsigned long)rel, s_[i].ch, want ? 1 : 0);
    }
  }
}

void Core::update(uint32_t now) {
  if (state_ != kPlaying) return;
  uint32_t rel = now - t0_, b;
  while (next_boundary(last_rel_, &b) && b <= rel) { apply(b); last_rel_ = b; }
  if (rel >= end_) {
    stop_outputs(end_);
    sendf("DONE %lu", (unsigned long)end_);
    state_ = kIdle;
  }
}

void Core::stop_outputs(uint32_t rel) {
  if (motor_now_ != 0) { motor_now_ = 0; out_.motor(0); sendf("MOTOR %lu 0.00", (unsigned long)rel); }
  for (int i = 0; i < ns_; i++)
    if (valve_open_[i]) { valve_open_[i] = false; out_.valve(s_[i].ch, false); sendf("SCENT %lu %c 0", (unsigned long)rel, s_[i].ch); }
}

void Core::link_lost(uint32_t now) {
  if (state_ != kPlaying) return;
  update(now);
  stop_outputs(now - t0_);
  sendf("STOPPED %lu", (unsigned long)(now - t0_));
  state_ = kIdle;
}

}  // namespace rsos
