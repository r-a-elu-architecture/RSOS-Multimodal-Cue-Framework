"""RSSO runtime: plays a compiled RSX timeline on a set of devices, within the safety envelope.

Two clocks share one code path:
  * VirtualClock — deterministic, instantaneous; for tests, conformance runs and synthetic studies;
  * RealTimeClock — sleeps until each event is due; for real hardware. Dispatch lateness is measured
    so that conformance can be checked on the actual machine.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from .devices import Device


class VirtualClock:
    def __init__(self, t0_ms: int = 0):
        self.t = t0_ms

    def now(self) -> int:
        return self.t

    def wait_until(self, t_ms: int) -> int:
        self.t = max(self.t, t_ms)
        return self.t


class RealTimeClock:
    def __init__(self):
        self._t0 = time.monotonic()

    def now(self) -> int:
        return int(round((time.monotonic() - self._t0) * 1000))

    def wait_until(self, t_ms: int) -> int:
        while True:
            left = t_ms - (time.monotonic() - self._t0) * 1000
            if left <= 0:
                return self.now()
            time.sleep(min(left / 1000, 0.02) if left > 2 else 0)


@dataclass
class Trace:
    protocol: str
    trigger: str
    started: bool
    reason: str = ""
    completed: bool = False
    stopped_at_ms: int | None = None
    stopped_at_phase: str = ""
    stop_latency_ms: int | None = None
    dispatched: int = 0
    max_lateness_ms: int = 0
    safety_corrections: list = field(default_factory=list)
    devices: list = field(default_factory=list)


def phase_at(timeline: dict, t_ms: int) -> str:
    name = ""
    for p in timeline["phases"]:
        if p["t"] <= t_ms:
            name = p["name"]
    return name


def play(timeline: dict, devices: list[Device], clock=None, stop_at_ms: int | None = None,
         governor=None, trigger: str = "self", now_ms: int = 0, consents=None) -> Trace:
    """Play `timeline` on `devices`.

    stop_at_ms: simulate the person pressing Stop at this time (relative to the run start).
    governor:   an rsx SafetyGovernor; device-triggered runs are refused if it says no.
    consents:   an rsso.consent.ConsentStore; a program with programmed cues is refused without valid consent.
    """
    tr = Trace(timeline["protocol"], trigger, started=False, devices=devices)
    from .consent import gate        # programmed cues run only with a valid consent record (C12)
    ok, why = gate(timeline, consents, now_ms)
    if not ok:
        tr.reason = why
        return tr
    if governor is not None:
        ok, why = governor.start(now_ms, trigger)
        if not ok:
            tr.reason = why
            return tr
    tr.started, tr.reason = True, "ok"
    clock = clock or VirtualClock()
    t0 = clock.now()
    for d in devices:
        if hasattr(d, "load"):          # devices that play the whole timeline on their own clock (RDP/1)
            d.load(timeline)
        d.arm(t0)
    hmax = timeline["safety"]["haptic_max"]
    for ev in timeline["events"]:
        due = t0 + ev["t"]
        if stop_at_ms is not None and ev["t"] >= stop_at_ms:
            break
        actual = clock.wait_until(due)
        tr.max_lateness_ms = max(tr.max_lateness_ms, actual - due)
        if ev["channel"] == "haptic" and ev["amp"] > hmax + 1e-12:     # defence in depth: never exceed the program limit
            tr.safety_corrections.append(f"haptic amp {ev['amp']} clamped to {hmax}")
            ev = dict(ev, amp=hmax)
        for d in devices:
            d.handle(ev, actual - t0)
        tr.dispatched += 1
    if stop_at_ms is not None and stop_at_ms < timeline["duration_ms"]:
        press = t0 + stop_at_ms
        clock.wait_until(press)
        ended = max(d.stop(press - t0) for d in devices) if devices else press - t0
        tr.stopped_at_ms, tr.stop_latency_ms = stop_at_ms, ended - stop_at_ms
        tr.stopped_at_phase = phase_at(timeline, stop_at_ms)
        return tr
    clock.wait_until(t0 + timeline["duration_ms"])
    for d in devices:
        d.stop(timeline["duration_ms"])
    tr.completed = True
    return tr
