"""Virtual participants: simulated people who live with RSOS for weeks and produce real-format run logs.

This is a two-level simulation:
  1. Physiology (beat level): for each person, a calibration day is simulated with the virtual heart-rate
     strap and the stress detector, giving that person's own detection probability, detection latency
     and false-alarm rate.
  2. Daily life (event level): triggers happen; the person notices them (or the device does), runs a
     program, and rates distress and agency before and after. Learning follows rsx.conditioning
     (Rescorla-Wagner for the bundle and the trigger, an asymptotic habit curve for noticing and latency).

All effect sizes are ASSUMPTIONS set in StudyConfig. A synthetic study shows that the pipeline, the
analysis and the study design work, and what sample sizes are needed if effects are of the assumed size.
It does not show that the protocol helps anyone.
"""
from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass

import numpy as np

from .sensors import Event, HeartProfile, StressDetector, VirtualHeartRateStrap, score_detections

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "rsx"))
from rsx import conditioning as cm  # noqa: E402

CHANNELS = ["V", "A", "K", "O", "memory", "thought"]


@dataclass
class StudyConfig:
    # assumed effects (rating points on 0-10 scales), not findings
    override_relief: float = 2.0       # distress drop from one override run when the bundle is fully learned
    control_relief: float = 1.0        # distress drop from paced breathing alone
    agency_ratio: float = 0.8          # agency gain relative to distress drop
    rating_noise: float = 1.2
    # daily life
    triggers_per_day: tuple = (2.0, 5.0)
    notice_start: float = 0.45         # probability of noticing a trigger in time, before practice
    notice_end: float = 0.95           # ... once the routine is automatic
    self_latency_start_s: float = 90.0
    self_latency_end_s: float = 3.0
    habit_eta: tuple = (0.02, 0.06)    # per trigger-paired run
    practice_runs_per_day: int = 3     # stage A practice in the first week
    bundle: tuple = ("V", "A", "K")


class VirtualParticipant:
    def __init__(self, pid: str, cfg: StudyConfig, rng: np.random.Generator, device_arm: bool = False):
        self.pid, self.cfg, self.rng, self.device_arm = pid, cfg, rng, device_arm
        self.heart = HeartProfile.sample(rng)
        self.rate = float(rng.uniform(*cfg.triggers_per_day))
        self.eta = float(rng.uniform(*cfg.habit_eta))
        self.distress0 = float(np.clip(rng.normal(6.5, 1.2), 3, 9.5))
        scale = float(rng.lognormal(0, 0.25))
        self.alpha = {k: v * scale for k, v in cm.DEFAULT_ALPHA.items()}
        self.model = cm.RWModel(self.alpha, beta=0.5)
        self.V = {c: 0.0 for c in cfg.bundle}
        self.V["trigger"] = -0.8
        self.h = 0.0
        self.detection = self._calibrate_detector() if device_arm else None

    def _calibrate_detector(self):
        dur = 3 * 3600
        ev = [Event(float(t), "stress", float(self.rng.uniform(0.6, 1.2))) for t in np.sort(self.rng.uniform(600, dur - 300, 5))]
        ev += [Event(float(t), "activity", float(self.rng.uniform(0.5, 1)), float(self.rng.uniform(60, 600)))
               for t in np.sort(self.rng.uniform(600, dur - 300, 3))]
        rec = VirtualHeartRateStrap(self.heart, ev, seed=int(self.rng.integers(1 << 30))).record(dur)
        return score_detections(StressDetector().detect(rec), ev, dur)

    # ---- learning state
    def bundle_strength(self) -> float:
        return float(np.clip(sum(self.V[c] for c in self.cfg.bundle), 0, 1))

    def practice(self):
        self.model.run(self.V, list(self.cfg.bundle))

    def paired_run(self):
        self.model.run(self.V, list(self.cfg.bundle) + ["trigger"])
        self.h += self.eta * (1 - self.h)

    def automaticity(self) -> float:
        return self.h

    # ---- one trigger
    def trigger(self, t_day_s: float, protocol: str) -> dict | None:
        cfg, rng = self.cfg, self.rng
        noticed = rng.random() < cfg.notice_start + (cfg.notice_end - cfg.notice_start) * self.h
        lat_self = cfg.self_latency_end_s + (cfg.self_latency_start_s - cfg.self_latency_end_s) * (1 - self.h)
        lat_self *= float(rng.lognormal(0, 0.35))
        how, latency = None, None
        if noticed:
            how, latency = "self", lat_self
        if self.device_arm and self.detection and rng.random() < self.detection["sensitivity"]:
            dlat = self.detection["median_latency_s"] * float(rng.lognormal(0, 0.25))
            if how is None or dlat < latency:
                how, latency = "device", dlat
        if how is None:
            return None
        valence = self.V["trigger"]                       # -0.8 at start: trigger predicts distress
        sud0 = float(np.clip(self.distress0 * (0.55 + 0.45 * max(0.0, -valence) / 0.8) + rng.normal(0, 0.8), 0, 10))
        relief = (cfg.override_relief * (0.4 + 0.6 * self.bundle_strength()) if protocol == "override"
                  else cfg.control_relief) + rng.normal(0, cfg.rating_noise)
        ag0 = float(np.clip(rng.normal(3.5, 1.0), 0, 10))
        row = dict(participant=self.pid, protocol=protocol, trigger=how, trigger_channel=str(rng.choice(CHANNELS)),
                   sud_before=round(sud0), sud_after=int(np.clip(round(sud0 - relief), 0, 10)),
                   agency_before=round(ag0), agency_after=int(np.clip(round(ag0 + cfg.agency_ratio * relief + rng.normal(0, 0.6)), 0, 10)),
                   latency_s=round(latency, 1), completed=1, stopped_at_phase="", tier="LION" if protocol == "override" else "",
                   voice="own", trigger_note="")
        if protocol == "override":
            self.paired_run()
        return row
