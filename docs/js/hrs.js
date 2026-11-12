/* Bluetooth Heart Rate Service driver and stress detector, JavaScript implementation.
 * Mirrors rsso/rsso/hrs.py (parser) and rsso/rsso/sensors.py StressDetector (detector);
 * rsso/tests/test_hrs.py checks that both give the same results on the same data.
 * Browser: window.RSOSHeart; Node: module.exports.
 */
(function (root) {
  "use strict";

  function parseHeartRateMeasurement(bytes) {
    const b = bytes instanceof DataView ? new Uint8Array(bytes.buffer, bytes.byteOffset, bytes.byteLength) : Uint8Array.from(bytes);
    if (b.length < 2) throw new Error("heart rate measurement too short");
    const flags = b[0];
    let i = 1, hr;
    if (flags & 0x01) { hr = b[i] | (b[i + 1] << 8); i += 2; } else { hr = b[i]; i += 1; }
    const contact = flags & 0x04 ? !!(flags & 0x02) : null;
    let energy = null;
    if (flags & 0x08) { energy = b[i] | (b[i + 1] << 8); i += 2; }
    const rr = [];
    if (flags & 0x10) while (i + 1 < b.length) { rr.push((b[i] | (b[i + 1] << 8)) * 1000 / 1024); i += 2; }
    return { hr, contact, energy_kj: energy, rr_ms: rr };
  }

  const DEFAULTS = { hr_rise_bpm: 8, rmssd_ratio: 0.7, sustain_s: 8, hr_window_s: 15, rmssd_window_s: 30,
    baseline_s: 300, baseline_gap_s: 60, rearm_s: 120, ignore_motion: true, step_s: 1 };

  function lowerBound(a, x, n) { let lo = 0, hi = n; while (lo < hi) { const m = (lo + hi) >> 1; if (a[m] < x) lo = m + 1; else hi = m; } return lo; }

  /* Streaming detector. push(rr_ms, moving) for every beat; it evaluates once per step_s of beat time
   * and calls onDetect(t_s) when a stress onset is detected. detect(rec) runs it over a whole recording. */
  class StressDetector {
    constructor(opts) {
      this.o = Object.assign({}, DEFAULTS, opts || {});
      this.t = []; this.rr = []; this.crr = [0]; this.cd2 = [0]; this.mot = [0];
      this.next = this.o.baseline_s + this.o.baseline_gap_s; this.held = 0; this.last = -1e9;
      this.detections = []; this.onDetect = null; this.state = null;
    }
    push(rr, moving, tBeat) {
      const n = this.t.length;
      const t = tBeat != null ? tBeat : (n ? this.t[n - 1] : 0) + rr / 1000;
      // evaluate every grid point strictly before this beat's time (matches the batch grid < t[-1])
      while (this.next < t && n >= 1) { this._eval(this.next); this.next += this.o.step_s; }
      this.t.push(t); this.rr.push(rr);
      const d2 = n ? (rr - this.rr[n - 1]) ** 2 : 0;
      this.crr.push(this.crr[n] + rr); this.cd2.push(this.cd2[n] + d2); this.mot.push(this.mot[n] + (moving ? 1 : 0));
    }
    _win(a, b) { const n = this.t.length; return [lowerBound(this.t, a, n), lowerBound(this.t, b, n)]; }
    _hr(a, b) { const [i, j] = this._win(a, b); return j - i >= 3 ? 60000 * (j - i) / (this.crr[j] - this.crr[i]) : NaN; }
    _rmssd(a, b) { const [i, j] = this._win(a, b); return j - i >= 4 ? Math.sqrt((this.cd2[j] - this.cd2[i + 1]) / (j - i - 1)) : NaN; }
    _eval(s) {
      const o = this.o;
      const b0 = s - o.baseline_gap_s - o.baseline_s, b1 = s - o.baseline_gap_s;
      const baseHr = this._hr(b0, b1), baseRm = this._rmssd(b0, b1);
      const hr = this._hr(s - o.hr_window_s, s), rm = this._rmssd(s - o.rmssd_window_s, s);
      const [i, j] = this._win(s - o.hr_window_s, s);
      const moving = o.ignore_motion && this.mot[j] - this.mot[i] > 0;
      const hit = !moving && hr - baseHr > o.hr_rise_bpm && rm < o.rmssd_ratio * baseRm;
      this.held = hit ? this.held + o.step_s : 0;
      this.state = { t: s, hr, rmssd: rm, base_hr: baseHr, base_rmssd: baseRm, moving };
      if (this.held >= o.sustain_s && s - this.last >= o.rearm_s) {
        this.detections.push(s); this.last = s; this.held = 0;
        if (this.onDetect) this.onDetect(s);
      }
    }
    static detect(rec, opts) {
      const d = new StressDetector(opts);
      for (let k = 0; k < rec.t.length; k++) d.push(rec.rr[k], rec.motion ? rec.motion[k] : false, rec.t[k]);
      return d.detections;
    }
  }

  /* Run-limit rules for device-triggered runs (mirrors rsx SafetyGovernor). */
  class Governor {
    constructor(safety, optedIn) { this.s = safety; this.optedIn = optedIn; this.starts = []; }
    check(nowMs) {
      if (!this.optedIn) return [false, "device triggering needs the person's opt-in"];
      const recent = this.starts.filter(t => nowMs - t < 86400000);
      if (recent.length && nowMs - recent[recent.length - 1] < this.s.refractory_ms) return [false, "refractory period"];
      if (recent.filter(t => nowMs - t < 3600000).length >= this.s.max_per_hour) return [false, "hourly limit"];
      if (recent.length >= this.s.max_per_day) return [false, "daily limit"];
      return [true, "ok"];
    }
    start(nowMs) { const r = this.check(nowMs); if (r[0]) this.starts.push(nowMs); return r; }
  }

  const api = { parseHeartRateMeasurement, StressDetector, Governor, DEFAULTS };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.RSOSHeart = api;
})(typeof self !== "undefined" ? self : this);
