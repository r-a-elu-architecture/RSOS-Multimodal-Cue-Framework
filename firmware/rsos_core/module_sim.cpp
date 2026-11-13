// Host simulator for the RDP/1.1 modules (rsos_modules.*): a physical model of a Peltier wrist module (skin, plate,
// heat sink, thermistors) driven by the real ThermalController, plus the SiteDriver and DisplayGate.
// Used by rsso/rsso/modules.py. Usage: module_sim thermal | sites | display
#include <math.h>
#include <stdio.h>
#include <string.h>

#include <initializer_list>

#include "rsos_modules.h"

using rsos::ThermalController;
using rsos::ThermalInputs;

struct Lcg { uint32_t x; explicit Lcg(uint32_t s) : x(s) {} float u() { x = 1664525u * x + 1013904223u; return x / 4294967296.0f; } };

// Lumped model: a skin node (skin under the plate) and a heat-sink node, joined by the element. Duty u in -1..1;
// positive pumps heat from the sink into the skin. Joule heat splits between the two sides.
struct Plant {
  float Qmax = 4.0f, Jmax = 1.5f, K = 0.15f, Cs = 6.0f, Gbody = 0.2f, Tbody = 33.0f, Ch = 12.0f, Gamb = 0.1f, Tamb = 24.0f;
  float Ts, Th, sensor, sink_sensor;
  void init() { Ts = (Gbody * Tbody + 0 * Tamb) / Gbody; Th = Tamb; sensor = Ts; sink_sensor = Th;
    for (int i = 0; i < 20000; i++) step(0, 0.05f); }        // settle to the resting state
  void step(float u, float dt) {
    float q = Qmax * u, J = Jmax * u * u;
    float dTs = (q + 0.5f * J + K * (Th - Ts) + Gbody * (Tbody - Ts)) / Cs;
    float dTh = (-q + 0.5f * J + K * (Ts - Th) + Gamb * (Tamb - Th)) / Ch;
    Ts += dTs * dt; Th += dTh * dt;
    sensor += (Ts - sensor) * dt / 1.0f;                      // thermistor lag about 1 s
    sink_sensor += (Th - sink_sensor) * dt / 1.0f;
  }
};

struct Scenario {
  const char* name; float delta; float on_s, off_s, end_s;
  float Tbody, Tamb, Gamb;
  float open_at, stuck_at, battery_at, spike_at, stop_at;     // fault injections (-1 = none)
};

static void run(const Scenario& sc) {
  Plant p; p.Tbody = sc.Tbody; p.Tamb = sc.Tamb; p.Gamb = sc.Gamb; p.init();
  ThermalController c; Lcg r(7);
  const float dt = 0.05f;
  float base_true = p.Ts, max_dev = 0, max_skin = p.Ts, max_sink = p.Th, settle = -1, overshoot = 0, final_dev = 0;
  float stuck_val = 0, fault_t = -1, cause_t = -1, last_duty = 0, true_at_fault = 0, tgt_seen = 0;
  bool on = false;
  for (int k = 0; k * dt <= sc.end_s; k++) {
    float t = k * dt; uint32_t ms = (uint32_t)(t * 1000 + 0.5f);
    if (!on && t >= sc.on_s && t < sc.off_s) { c.command(sc.delta); on = true; base_true = p.Ts; }
    if (on && (t >= sc.off_s || (sc.stop_at >= 0 && t >= sc.stop_at))) { c.command(0); on = false; if (sc.stop_at >= 0 && cause_t < 0) cause_t = t; }
    ThermalInputs in;
    in.skin_c = p.sensor + (r.u() - 0.5f) * 0.06f;
    in.sink_c = p.sink_sensor + (r.u() - 0.5f) * 0.06f;
    in.battery_v = (sc.battery_at >= 0 && t >= sc.battery_at) ? 3.2f : 3.9f;
    in.skin_ok = !(sc.open_at >= 0 && t >= sc.open_at);
    in.sink_ok = true;
    if (sc.stuck_at >= 0 && t >= sc.stuck_at) { if (stuck_val == 0) stuck_val = in.skin_c; in.skin_c = stuck_val; }
    if (sc.spike_at >= 0 && fabsf(t - sc.spike_at) < dt / 2) in.skin_c += 5.0f;
    for (float inj : {sc.open_at, sc.stuck_at, sc.battery_at, sc.spike_at}) if (inj >= 0 && t >= inj && cause_t < 0) cause_t = t;
    float u = c.step(in, ms);
    if (c.fault_new()) { fault_t = t; true_at_fault = p.Ts - base_true; }
    last_duty = u;
    p.step(u, dt);
    float dev = p.Ts - base_true;
    if (t >= sc.on_s && t < sc.off_s) {
      if (fabsf(dev) > fabsf(max_dev)) max_dev = dev;
      float tgt = c.target() - c.baseline();
      if (c.baseline() > -999 && fabsf(tgt) < 10) tgt_seen = tgt;
      if (settle < 0 && fabsf(dev - tgt) < 0.3f && c.fault() == nullptr) settle = t - sc.on_s;
      if (sc.delta != 0 && dev * (sc.delta > 0 ? 1 : -1) - fabsf(tgt) > overshoot) overshoot = dev * (sc.delta > 0 ? 1 : -1) - fabsf(tgt);
      final_dev = dev;
    }
    if (p.Ts > max_skin) max_skin = p.Ts;
    if (p.Th > max_sink) max_sink = p.Th;
  }
  float lat = (fault_t >= 0 && cause_t >= 0) ? (fault_t - cause_t) * 1000 : -1;
  if (sc.stop_at >= 0) lat = 0;   // Stop: command(0) zeroes the duty in the same step
  printf("SCN %s target=%.2f settle_s=%.2f overshoot=%.2f max_dev=%.2f final_dev=%.2f max_skin=%.2f min_skin_base=%.2f max_sink=%.2f "
         "fault=%s fault_s=%.2f latency_ms=%.0f dev_at_fault=%.2f end_duty=%.2f\n",
         sc.name, tgt_seen, settle, overshoot, max_dev, final_dev, max_skin, base_true, max_sink,
         c.fault() ? c.fault() : "none", fault_t, lat, true_at_fault, last_duty);
}

static void thermal() {
  const Scenario S[] = {
    {"cool_2", -2, 2, 62, 90, 33, 24, 0.1f, -1, -1, -1, -1, -1},
    {"warm_3", 3, 2, 122, 150, 33, 24, 0.1f, -1, -1, -1, -1, -1},
    {"cool_4_long", -4, 2, 122, 150, 33, 24, 0.1f, -1, -1, -1, -1, -1},
    {"command_6", 6, 2, 122, 150, 33, 24, 0.1f, -1, -1, -1, -1, -1},
    {"hot_day_warm_4", 4, 2, 122, 150, 36.5f, 32, 0.1f, -1, -1, -1, -1, -1},
    {"sensor_open", 3, 2, 122, 150, 33, 24, 0.1f, 30, -1, -1, -1, -1},
    {"sensor_stuck", 3, 2, 122, 150, 33, 24, 0.1f, -1, 2, -1, -1, -1},
    {"sensor_spike", -2, 2, 62, 90, 33, 24, 0.1f, -1, -1, -1, 30, -1},
    {"sink_overheats", -4, 2, 302, 330, 33, 35, 0.004f, -1, -1, -1, -1, -1},
    {"battery_low", 3, 2, 122, 150, 33, 24, 0.1f, -1, -1, 40, -1, -1},
    {"stop_mid_cue", 3, 2, 122, 150, 33, 24, 0.1f, -1, -1, -1, -1, 20},
  };
  for (const Scenario& s : S) run(s);
}

static void sites() {
  rsos::SiteDriver d(170);
  d.set(3, 0.5f, 170, 6, 1000);
  d.set(0, 0.4f, 0, 0, 1000);
  for (uint32_t t = 1000; t <= 1250; t += 25) printf("RTP %u %u %u\n", t, d.rtp(3, t), d.rtp(0, t));
  d.set(1, 0.5f, 250, 0, 0);
  printf("MISMATCH %d %d %d\n", d.carrier_mismatch(3), d.carrier_mismatch(1), d.carrier_mismatch(0));
  d.set(2, 1.4f, 0, 0, 0);
  printf("CAP %u\n", d.rtp(2, 5));
  d.set(3, 0, 0, 0, 2000);
  printf("OFF %u\n", d.rtp(3, 2100));
}

static void display() {
  rsos::DisplayGate g;
  printf("DAY %.2f %.2f\n", g.brightness(1.0f), g.brightness(0.5f));
  g.night(true);
  printf("NIGHT %.2f %.2f\n", g.brightness(1.0f), g.brightness(0.1f));
  const char* names[] = {"lion", "owl_2", "a-b", "", "../etc", "Lion", "abcdefghijklmnopqrstuvwx"};
  for (const char* n : names) printf("NAME %s %d\n", n[0] ? n : "(empty)", rsos::DisplayGate::valid_name(n));
}

int main(int argc, char** argv) {
  const char* what = argc > 1 ? argv[1] : "thermal";
  if (!strcmp(what, "thermal")) thermal();
  else if (!strcmp(what, "sites")) sites();
  else if (!strcmp(what, "display")) display();
  return 0;
}
