#include "rsos_core.h"

#include <stdarg.h>
#include <stdio.h>
#include <string.h>

namespace rsos {

const char* const kSiteNames[kSites] = {"wrist_left", "wrist_right", "upper_arm", "chest", "upper_back", "ankle"};

Core::Core(Output& out, const char* capabilities, float motor_max)
    : out_(out), caps_(capabilities), motor_max_(motor_max), haptic_max_(0), motor_now_(0),
      consent_(false), state_(kIdle), expected_(0), nh_(0), ns_(0), nt_(0), nd_(0), nf_(0), thermal_now_(0),
      t0_(0), last_rel_(0), end_(0) {
  for (int i = 0; i < kMaxEvents; i++) valve_open_[i] = false;
  for (int i = 0; i < kSites; i++) site_now_[i] = 0;
  for (int i = 0; i < 16; i++) disp_on_[i] = false;
}

bool Core::caps_has(const char* c) const {
  size_t n = strlen(c);
  for (const char* p = caps_; (p = strstr(p, c)) != 0; p += n)
    if ((p == caps_ || p[-1] == ',') && (p[n] == 0 || p[n] == ',')) return true;
  return false;
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
  } else if (!strcmp(cmd, "NIGHT")) {
    int v;
    if (sscanf(text, "NIGHT %d", &v) == 1 && (v == 0 || v == 1)) { out_.night(v == 1); sendf("OK NIGHT"); }
    else sendf("ERR NIGHT syntax");
  } else if (!strcmp(cmd, "LOAD")) {
    int n; float hm;
    if (state_ == kPlaying) { sendf("ERR LOAD playing"); return; }
    if (sscanf(text, "LOAD %d %f", &n, &hm) != 2 || n < 0 || hm <= 0 || hm > 1) { sendf("ERR LOAD syntax"); return; }
    if (n > kMaxEvents) { sendf("ERR LOAD too-many-events"); state_ = kIdle; return; }
    expected_ = n; nh_ = ns_ = nt_ = nd_ = nf_ = 0; end_ = 0; haptic_max_ = minf(hm, motor_max_);
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
    if (nh_ + ns_ + nt_ + nd_ + nf_ == expected_) state_ = kLoaded;
  } else if (!strcmp(cmd, "T") || !strcmp(cmd, "D") || !strcmp(cmd, "HF")) {
    if (state_ != kLoading) { sendf("ERR %s not-loading", cmd); return; }
    const char* need = cmd[0] == 'T' ? "thermal" : (cmd[0] == 'D' ? "display" : "haptic");
    if (!caps_has(need)) { sendf("ERR %s not-capable", cmd); return; }
    if (cmd[0] == 'T') {
      unsigned long t, dur; float dc;
      if (sscanf(text, "T %lu %lu %f", &t, &dur, &dc) != 3 || dur == 0) { sendf("ERR T syntax"); return; }
      if (dc > kThermalMaxC || dc < -kThermalMaxC) { sendf("ERR T envelope"); return; }
      if (nt_ >= kThermalPerRun) { sendf("ERR T too-many"); return; }
      uint32_t d = dur > kThermalMaxMs ? kThermalMaxMs : (uint32_t)dur;
      if (d < dur) sendf("CLAMPED %lu dur %lu", t, (unsigned long)d);
      TEvent e = {(uint32_t)t, d, dc};
      t_[nt_++] = e;
      if (e.t + d > end_) end_ = e.t + d;
    } else if (cmd[0] == 'D') {
      unsigned long t, dur; char img[24] = {0};
      if (sscanf(text, "D %lu %lu %23s", &t, &dur, img) != 3 || dur == 0) { sendf("ERR D syntax"); return; }
      if (nd_ >= 16) { sendf("ERR D too-many"); return; }
      uint32_t d = dur > kDisplayMaxMs ? kDisplayMaxMs : (uint32_t)dur;
      if (d < dur) sendf("CLAMPED %lu dur %lu", t, (unsigned long)d);
      DEvent e; e.t = (uint32_t)t; e.dur = d; memcpy(e.image, img, sizeof img);
      d_[nd_++] = e;
      if (e.t + d > end_) end_ = e.t + d;
    } else {
      unsigned long t, on, off, count, car, mod; float amp; char site[16] = {0};
      if (sscanf(text, "HF %lu %lu %lu %lu %f %lu %lu %15s", &t, &on, &off, &count, &amp, &car, &mod, site) != 8 || count < 1 || count > 50 || on == 0) {
        sendf("ERR HF syntax"); return;
      }
      int si = -1;
      for (int i = 0; i < kSites; i++) if (!strcmp(site, kSiteNames[i])) si = i;
      if (si < 0) { sendf("ERR HF site"); return; }
      if ((car && (car < 20 || car > 300)) || (mod && (mod < 1 || mod > 40))) { sendf("ERR HF envelope"); return; }
      if (nf_ >= 32) { sendf("ERR HF too-many"); return; }
      float lim = minf(amp, haptic_max_);
      if (lim < amp) sendf("CLAMPED %lu %.2f %.2f", t, amp, haptic_max_);
      FEvent e = {(uint32_t)t, (uint32_t)on, (uint32_t)off, (uint16_t)count, lim < 0 ? 0 : lim, (uint16_t)car, (uint16_t)mod, (uint8_t)si, false};
      f_[nf_++] = e;
      uint32_t e_end = e.t + (e.on + e.off) * e.count;
      if (e_end > end_) end_ = e_end;
    }
    if (nh_ + ns_ + nt_ + nd_ + nf_ == expected_) state_ = kLoaded;
  } else if (!strcmp(cmd, "START")) {
    if (state_ != kLoaded) { sendf("ERR START not-loaded"); return; }
    for (int i = 0; i < ns_; i++) { s_[i].refused_reported = false; valve_open_[i] = false; }
    for (int i = 0; i < nf_; i++) f_[i].refused_reported = false;
    for (int i = 0; i < nd_; i++) disp_on_[i] = false;
    for (int i = 0; i < kSites; i++) site_now_[i] = 0;
    thermal_now_ = 0;
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

float Core::site_at(int site, uint32_t rel, int* carrier, int* mod) const {
  float a = 0;
  for (int i = 0; i < nf_; i++) {
    const FEvent& e = f_[i];
    if (e.site != site) continue;
    uint32_t period = e.on + e.off;
    if (rel < e.t || rel >= e.t + period * e.count) continue;
    if ((rel - e.t) % period < e.on && e.amp > a) { a = e.amp; *carrier = e.carrier; *mod = e.mod; }
  }
  return a;
}

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
  for (int i = 0; i < ns_ + nt_ + nd_; i++) {
    uint32_t a, b;
    if (i < ns_) { a = s_[i].t; b = a + s_[i].dur; }
    else if (i < ns_ + nt_) { a = t_[i - ns_].t; b = a + t_[i - ns_].dur; }
    else { a = d_[i - ns_ - nt_].t; b = a + d_[i - ns_ - nt_].dur; }
    if (a > after && (!found || a < best)) { best = a; found = true; }
    if (b > after && (!found || b < best)) { best = b; found = true; }
  }
  for (int i = 0; i < nf_; i++) {
    const FEvent& e = f_[i];
    uint32_t period = e.on + e.off;
    for (uint16_t k = 0; k < e.count; k++) {
      uint32_t a = e.t + k * period, b = a + e.on;
      if (a > after && (!found || a < best)) { best = a; found = true; }
      if (b > after && (!found || b < best)) { best = b; found = true; }
    }
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
  // temperature: the strongest active change wins; back to neutral (0) when none is active
  float th = 0;
  for (int i = 0; i < nt_; i++) {
    float d = t_[i].delta, ad = d < 0 ? -d : d, ath = th < 0 ? -th : th;
    if (rel >= t_[i].t && rel < t_[i].t + t_[i].dur && ad > ath) th = d;
  }
  if (th != thermal_now_) { thermal_now_ = th; out_.thermal(th); sendf("THERMAL %lu %.2f", (unsigned long)rel, th); }
  for (int i = 0; i < nd_; i++) {
    bool want = rel >= d_[i].t && rel < d_[i].t + d_[i].dur;
    if (want != disp_on_[i]) { disp_on_[i] = want; out_.display(d_[i].image, want); sendf("DISPLAY %lu %s %d", (unsigned long)rel, d_[i].image, want ? 1 : 0); }
  }
  // body sites: at most kSitesAtOnce vibrate together; a further site is refused, not queued
  int active = 0;
  for (int s = 0; s < kSites; s++) if (site_now_[s] > 0) active++;
  for (int s = 0; s < kSites; s++) {
    int car = 0, mod = 0;
    float a = site_at(s, rel, &car, &mod);
    if (a > 0 && site_now_[s] == 0 && active >= kSitesAtOnce) {
      for (int i = 0; i < nf_; i++)
        if (f_[i].site == s && !f_[i].refused_reported) { f_[i].refused_reported = true; sendf("REFUSED %lu %s sites", (unsigned long)rel, kSiteNames[s]); }
      continue;
    }
    if (a != site_now_[s]) {
      if (site_now_[s] == 0) active++; else if (a == 0) active--;
      site_now_[s] = a; out_.site(s, a, car, mod);
      sendf("SITE %lu %s %.2f %d %d", (unsigned long)rel, kSiteNames[s], a, car, mod);
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
  if (thermal_now_ != 0) { thermal_now_ = 0; out_.thermal(0); sendf("THERMAL %lu 0.00", (unsigned long)rel); }
  for (int i = 0; i < nd_; i++)
    if (disp_on_[i]) { disp_on_[i] = false; out_.display(d_[i].image, false); sendf("DISPLAY %lu %s 0", (unsigned long)rel, d_[i].image); }
  for (int s = 0; s < kSites; s++)
    if (site_now_[s] != 0) { site_now_[s] = 0; out_.site(s, 0, 0, 0); sendf("SITE %lu %s 0.00 0 0", (unsigned long)rel, kSiteNames[s]); }
}

void Core::link_lost(uint32_t now) {
  if (state_ != kPlaying) return;
  update(now);
  stop_outputs(now - t0_);
  sendf("STOPPED %lu", (unsigned long)(now - t0_));
  state_ = kIdle;
}

}  // namespace rsos
