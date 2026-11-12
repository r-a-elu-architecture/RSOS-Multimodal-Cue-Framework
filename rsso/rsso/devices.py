"""MICRO / AUG device layer: one interface for every output device, with virtual implementations.

A device receives timeline events from the runtime and acts on them. Real hardware (a watch, an ESP32
with a vibration motor, a scent atomiser, a display) implements the same `Device` interface; the
virtual devices here record exactly what they would have done, with timestamps, so that the runtime,
the conformance suite and the synthetic studies can be checked without hardware.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Action:
    """One thing a device did: at time t_ms it started `kind` for dur_ms (0 = instantaneous)."""
    t_ms: int
    device: str
    kind: str
    dur_ms: int = 0
    detail: dict = field(default_factory=dict)


class Device:
    """Base class. Subclasses declare which timeline channels they handle and implement `_act`.

    Contract (checked by rsso.conformance):
      * `handle(event, t_ms)` acts only while the device is armed (between `arm()` and `stop()`);
      * `stop(t_ms)` ends all ongoing output at once and returns the time output actually ended;
      * nothing is emitted after `stop()` until the device is armed again.
    """
    name = "device"
    channels: tuple = ()

    def __init__(self):
        self.actions: list[Action] = []
        self.armed = False
        self._busy_until = 0

    def arm(self, t_ms: int = 0):
        self.armed = True

    def accepts(self, event: dict) -> bool:
        return event["channel"] in self.channels

    def handle(self, event: dict, t_ms: int) -> None:
        if not self.armed or not self.accepts(event):
            return
        a = self._act(event, t_ms)
        if a is not None:
            self.actions.append(a)
            self._busy_until = max(self._busy_until, a.t_ms + a.dur_ms)

    def _act(self, event: dict, t_ms: int) -> Action | None:
        raise NotImplementedError

    def stop(self, t_ms: int) -> int:
        """Stop all output now. Returns when output actually ended (virtual devices: immediately)."""
        self.armed = False
        for a in self.actions:
            if a.t_ms + a.dur_ms > t_ms:
                a.dur_ms = max(0, t_ms - a.t_ms)
                a.detail["truncated"] = True
        self._busy_until = min(self._busy_until, t_ms)
        return t_ms

    def output_after(self, t_ms: int) -> list[Action]:
        """Actions still producing output after t_ms (used to verify stopping)."""
        return [a for a in self.actions if a.t_ms + a.dur_ms > t_ms or a.t_ms > t_ms]


class VirtualHaptic(Device):
    """A vibration motor. Amplitude is a fraction of the device maximum (0..1)."""
    name = "haptic"
    channels = ("haptic",)

    def __init__(self, max_amp: float = 1.0):
        super().__init__()
        self.max_amp = max_amp

    def _act(self, e, t):
        amp = min(e["amp"], self.max_amp)
        pulses = [(t + k * (e["on"] + e["off"]), e["on"]) for k in range(e["count"])]
        return Action(t, self.name, "pattern", (e["on"] + e["off"]) * e["count"],
                      {"amp": amp, "pulses": pulses, "requested_amp": e["amp"]})


class VirtualAudio(Device):
    """Speech and tones. Speech is only produced for `say` steps (a tier's auditory cue is not spoken again)."""
    name = "audio"
    channels = ("auditory",)

    def _act(self, e, t):
        if e["kind"] == "tone":
            return Action(t, self.name, "tone", e["dur"], {"hz": e["hz"]})
        if e["kind"] == "say":
            return Action(t, self.name, "speech", e["dur"], {"text": e["text"]})
        return None


class VirtualDisplay(Device):
    """Screen, AR overlay or watch face: shows imagery, feelings, gestures and tier glyphs."""
    name = "display"
    channels = ("visual", "kinesthetic", "marker", "breath")

    def _act(self, e, t):
        if e["channel"] == "marker":
            return Action(t, self.name, "glyph", 0, {"glyph": e.get("glyph", "")}) if e["kind"] == "tier" else None
        if e["channel"] == "breath":
            return Action(t, self.name, "breath-" + e["kind"], e["dur"], {})
        return Action(t, self.name, e["kind"], e["dur"], {"text": e.get("text", "")})


class VirtualScent(Device):
    """A scent (or taste) delivery device. It refuses to release anything until the person has confirmed
    they have no allergy or aversion (spec section 9)."""
    name = "scent"
    channels = ("olfactory", "gustatory")

    def __init__(self, confirmed_no_allergy: bool = False, max_release_ms: int = 3000):
        super().__init__()
        self.confirmed = confirmed_no_allergy
        self.max_release_ms = max_release_ms

    def _act(self, e, t):
        if not self.confirmed:
            return Action(t, self.name, "refused", 0, {"reason": "allergy/aversion not confirmed", "text": e.get("text", "")})
        return Action(t, self.name, "release", min(e["dur"], self.max_release_ms), {"text": e.get("text", "")})


def standard_rig(confirmed_scent: bool = False) -> list[Device]:
    """The default virtual device set: haptic, audio, display, scent."""
    return [VirtualHaptic(), VirtualAudio(), VirtualDisplay(), VirtualScent(confirmed_scent)]
