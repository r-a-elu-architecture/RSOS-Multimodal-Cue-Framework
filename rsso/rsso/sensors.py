"""AUG sensors: a virtual heart-rate strap and the stress-trigger detector.

VirtualHeartRateStrap produces beat-to-beat (RR) intervals the way a chest strap or watch reports them
(Bluetooth Heart Rate Service delivers RR intervals in the same form). The model is deliberately simple
and every parameter is exposed:

  RR(t) = 60000 / HR(t)  +  RSA(t)  +  beat noise
  HR(t)        = resting HR + stress response + activity response
  RSA(t)       = respiratory sinus arrhythmia: amplitude ~ vagal tone, at the breathing frequency;
                 slow paced breathing (about 6 breaths/min, as in the Override Protocol's 4 s in / 6 s out)
                 raises it (resonance breathing)
  stress event = HR rises and vagal tone falls with a fast onset, then recovers exponentially
  activity     = HR rises and vagal tone falls too (the main source of false alarms), with motion reported
  override run = paced breathing for the run's length and a faster recovery (the hypothesised effect,
                 a parameter you set, not a finding)

StressDetector flags a likely negative-state onset from RR intervals alone: heart rate clearly above the
person's recent baseline together with a drop in RMSSD, sustained for a few seconds; optionally ignoring
periods with motion.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class Event:
    t_s: float
    kind: str              # "stress", "activity" or "override"
    magnitude: float = 1.0
    dur_s: float = 60.0    # activity bout length, or override run length


@dataclass
class HeartProfile:
    rest_hr: float = 70.0            # bpm
    vagal_rr_sd: float = 30.0        # ms, beat-noise SD at rest (scales with vagal tone)
    rsa_ms: float = 25.0             # ms, RSA amplitude at rest, spontaneous breathing
    breath_hz: float = 0.25          # spontaneous breathing
    stress_hr: float = 18.0          # bpm rise for a magnitude-1 stress event
    stress_vagal_drop: float = 0.6   # fraction of vagal tone lost at magnitude 1
    onset_tau_s: float = 8.0
    recovery_tau_s: float = 120.0
    activity_hr: float = 30.0
    override_recovery_factor: float = 0.5   # hypothesised: recovery runs this much faster during/after a run
    paced_rsa_gain: float = 2.5             # RSA amplitude multiplier at about 0.1 Hz paced breathing

    @classmethod
    def sample(cls, rng) -> "HeartProfile":
        return cls(rest_hr=float(rng.normal(70, 8)), vagal_rr_sd=float(rng.lognormal(np.log(28), 0.35)),
                   rsa_ms=float(rng.lognormal(np.log(25), 0.4)), stress_hr=float(rng.normal(18, 5)),
                   stress_vagal_drop=float(np.clip(rng.normal(0.6, 0.12), 0.2, 0.9)),
                   recovery_tau_s=float(rng.lognormal(np.log(120), 0.3)))


class VirtualHeartRateStrap:
    def __init__(self, profile: HeartProfile, events: list[Event], seed: int = 0):
        self.p, self.events, self.rng = profile, sorted(events, key=lambda e: e.t_s), np.random.default_rng(seed)

    def _state(self, t):
        p = self.p
        hr, vagal, motion, breath_hz, rsa_gain = p.rest_hr, 1.0, False, p.breath_hz, 1.0
        overrides = [e for e in self.events if e.kind == "override" and e.t_s <= t]
        for e in self.events:
            if e.t_s > t:
                break
            dt = t - e.t_s
            if e.kind == "stress":
                tau = p.recovery_tau_s
                o = next((x for x in overrides if x.t_s >= e.t_s), None)
                if o is not None:   # a run after this stress event speeds recovery from the run onward
                    dt_pre = o.t_s - e.t_s
                    level = (1 - np.exp(-dt_pre / p.onset_tau_s)) * np.exp(-max(0, dt_pre - 3 * p.onset_tau_s) / tau)
                    level *= np.exp(-(dt - dt_pre) / (tau * p.override_recovery_factor))
                else:
                    level = (1 - np.exp(-dt / p.onset_tau_s)) * np.exp(-max(0, dt - 3 * p.onset_tau_s) / tau)
                hr += e.magnitude * p.stress_hr * level
                vagal *= 1 - e.magnitude * p.stress_vagal_drop * level
            elif e.kind == "activity" and dt < e.dur_s + 60:
                level = min(1, dt / 20) if dt < e.dur_s else np.exp(-(dt - e.dur_s) / 30)
                hr += e.magnitude * p.activity_hr * level
                vagal *= 1 - 0.7 * e.magnitude * level
                motion = motion or dt < e.dur_s
            elif e.kind == "override" and dt < e.dur_s:
                breath_hz, rsa_gain = 0.1, p.paced_rsa_gain
        return hr, max(vagal, 0.05), motion, breath_hz, rsa_gain

    def record(self, duration_s: float) -> dict:
        """Returns beat times (s), RR intervals (ms) and a per-beat motion flag."""
        t, beats, rrs, motion = 0.0, [], [], []
        phase = 0.0
        while t < duration_s:
            hr, vagal, mov, bhz, gain = self._state(t)
            rr = 60000.0 / hr + gain * vagal * self.p.rsa_ms * np.sin(phase) + self.rng.normal(0, self.p.vagal_rr_sd * vagal)
            rr = float(np.clip(rr, 300, 2000))
            t += rr / 1000
            phase += 2 * np.pi * bhz * rr / 1000
            beats.append(t); rrs.append(rr); motion.append(mov)
        return {"t": np.array(beats), "rr": np.array(rrs), "motion": np.array(motion)}


@dataclass
class StressDetector:
    hr_rise_bpm: float = 8.0         # heart rate above baseline
    rmssd_ratio: float = 0.7         # RMSSD below this fraction of baseline
    sustain_s: float = 8.0           # both conditions held this long
    hr_window_s: float = 15.0
    rmssd_window_s: float = 30.0
    baseline_s: float = 300.0        # baseline from the preceding 5 minutes...
    baseline_gap_s: float = 60.0     # ...excluding the last minute
    rearm_s: float = 120.0           # no second detection within this time
    ignore_motion: bool = True
    step_s: float = 1.0

    def detect(self, rec: dict) -> list[float]:
        t, rr = rec["t"], rec["rr"]
        if len(t) < 10:
            return []
        d2 = np.r_[0.0, np.diff(rr) ** 2]
        c_rr, c_d2 = np.r_[0.0, np.cumsum(rr)], np.r_[0.0, np.cumsum(d2)]
        mot = np.r_[0, np.cumsum(rec.get("motion", np.zeros(len(t), bool)).astype(int))]

        def win(a, b):
            i, j = np.searchsorted(t, a), np.searchsorted(t, b)
            return i, j

        def hr(a, b):
            i, j = win(a, b)
            return 60000 * (j - i) / (c_rr[j] - c_rr[i]) if j - i >= 3 else np.nan

        def rmssd(a, b):
            i, j = win(a, b)
            return np.sqrt((c_d2[j] - c_d2[i + 1]) / (j - i - 1)) if j - i >= 4 else np.nan

        out, held, last = [], 0.0, -1e9
        grid = np.arange(self.baseline_s + self.baseline_gap_s, t[-1], self.step_s)
        for s in grid:
            b0, b1 = s - self.baseline_gap_s - self.baseline_s, s - self.baseline_gap_s
            base_hr, base_rm = hr(b0, b1), rmssd(b0, b1)
            cur_hr, cur_rm = hr(s - self.hr_window_s, s), rmssd(s - self.rmssd_window_s, s)
            i, j = win(s - self.hr_window_s, s)
            moving = self.ignore_motion and mot[j] - mot[i] > 0
            hit = (not moving and cur_hr - base_hr > self.hr_rise_bpm and cur_rm < self.rmssd_ratio * base_rm)
            held = held + self.step_s if hit else 0.0
            if held >= self.sustain_s and s - last >= self.rearm_s:
                out.append(float(s)); last = s; held = 0.0
        return out


def score_detections(detections: list[float], events: list[Event], duration_s: float, window_s: float = 120.0) -> dict:
    """Sensitivity, latency and false alarms per hour against the true stress events."""
    stress = [e.t_s for e in events if e.kind == "stress"]
    matched, lat, used = 0, [], set()
    for s in stress:
        hits = [d for d in detections if s <= d <= s + window_s and d not in used]
        if hits:
            matched += 1; lat.append(hits[0] - s); used.add(hits[0])
    fa = len([d for d in detections if d not in used])
    return {"stress_events": len(stress), "detected": matched,
            "sensitivity": matched / len(stress) if stress else float("nan"),
            "median_latency_s": float(np.median(lat)) if lat else float("nan"),
            "false_alarms_per_hour": fa / (duration_s / 3600)}
