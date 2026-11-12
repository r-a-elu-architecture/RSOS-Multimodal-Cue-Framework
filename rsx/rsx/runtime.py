"""RSSO runtime pieces: the safety governor and the session log.

The governor enforces the limits in spec/OVERRIDE_PROTOCOL.md section 9 for
device-triggered runs. Self-initiated runs are always allowed: a person may
practise whenever they choose, and may always stop.
"""
from __future__ import annotations

import csv
import io
import time
from dataclasses import dataclass, field

HOUR_MS = 3_600_000
DAY_MS = 86_400_000


@dataclass
class SafetyGovernor:
    max_per_hour: int = 6
    max_per_day: int = 20
    refractory_ms: int = 90_000
    opted_in: bool = False
    _device_starts: list = field(default_factory=list)

    @classmethod
    def from_timeline(cls, timeline: dict, opted_in: bool = False) -> "SafetyGovernor":
        s = timeline["safety"]
        return cls(s["max_per_hour"], s["max_per_day"], s["refractory_ms"], opted_in)

    def check(self, now_ms: int, trigger: str = "self") -> tuple[bool, str]:
        """Return (allowed, reason). ``trigger`` is 'self' or 'device'."""
        if trigger == "self":
            return True, "self-initiated"
        if trigger != "device":
            return False, f"unknown trigger {trigger}"
        if not self.opted_in:
            return False, "device triggering needs the person's opt-in"
        recent = [t for t in self._device_starts if now_ms - t < DAY_MS]
        if recent and now_ms - recent[-1] < self.refractory_ms:
            return False, "refractory period"
        if sum(1 for t in recent if now_ms - t < HOUR_MS) >= self.max_per_hour:
            return False, "hourly limit"
        if len(recent) >= self.max_per_day:
            return False, "daily limit"
        return True, "ok"

    def start(self, now_ms: int, trigger: str = "self") -> tuple[bool, str]:
        ok, why = self.check(now_ms, trigger)
        if ok and trigger == "device":
            self._device_starts.append(now_ms)
        return ok, why


LOG_FIELDS = ["timestamp", "participant", "protocol", "trigger", "trigger_channel", "trigger_note",
              "sud_before", "sud_after", "agency_before", "agency_after", "latency_s",
              "completed", "stopped_at_phase"]


@dataclass
class RunRecord:
    participant: str
    protocol: str
    trigger: str = "self"
    trigger_channel: str = ""
    trigger_note: str = ""
    sud_before: float | None = None
    sud_after: float | None = None
    agency_before: float | None = None
    agency_after: float | None = None
    latency_s: float | None = None
    completed: bool = True
    stopped_at_phase: str = ""
    timestamp: float = field(default_factory=time.time)

    def validate(self) -> None:
        for name in ("sud_before", "sud_after", "agency_before", "agency_after"):
            v = getattr(self, name)
            if v is not None and not 0 <= v <= 10:
                raise ValueError(f"{name} must be 0..10")
        if self.trigger not in ("self", "device"):
            raise ValueError("trigger must be 'self' or 'device'")
        if self.trigger_channel and self.trigger_channel not in ("V", "A", "K", "O", "G", "thought", "memory"):
            raise ValueError("trigger_channel must be V, A, K, O, G, thought or memory")


def write_log(records: list[RunRecord]) -> str:
    """Return the session log as CSV text (schema: LOG_FIELDS)."""
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=LOG_FIELDS, lineterminator="\n")
    w.writeheader()
    for r in records:
        r.validate()
        row = {k: getattr(r, k) for k in LOG_FIELDS}
        row["completed"] = int(r.completed)
        w.writerow({k: ("" if v is None else v) for k, v in row.items()})
    return buf.getvalue()
