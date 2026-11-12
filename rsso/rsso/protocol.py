"""Host side of the RSOS Device Protocol (RDP/1, spec/DEVICE_PROTOCOL.md).

`encode(timeline)` turns a compiled RSX timeline into the RDP lines a device needs.
`ProtocolDevice` is an rsso Device that drives any RDP/1 device through a transport:

  * SimTransport — runs the real firmware core (firmware/rsos_core) in the host simulator, with simulated
    time. This is software-in-the-loop testing: the conformance suite checks the exact C++ code that runs
    on the wristband.
  * a serial or Bluetooth transport for real hardware only needs `send(line)` and `read_until(prefix)`.
"""
from __future__ import annotations

import pathlib
import subprocess

from .devices import Action, Device

ROOT = pathlib.Path(__file__).resolve().parents[2]
CORE = ROOT / "firmware" / "rsos_core"


def encode(timeline: dict, capabilities=("haptic", "olfactory", "gustatory")) -> list[str]:
    ev = []
    for e in timeline["events"]:
        if e["channel"] == "haptic" and "haptic" in capabilities:
            ev.append(f"H {e['t']} {e['on']} {e['off']} {e['count']} {e['amp']:.2f}")
        elif e["channel"] in ("olfactory", "gustatory") and e["channel"] in capabilities:
            ev.append(f"S {e['t']} {e['dur']} {'O' if e['channel'] == 'olfactory' else 'G'}")
    if len(ev) > 64:
        raise ValueError("RDP/1 devices hold at least 64 events; this program needs more")
    return [f"LOAD {len(ev)} {timeline['safety']['haptic_max']:.2f}"] + ev


def build_host_sim() -> pathlib.Path:
    exe = CORE / "host_sim"
    srcs = [CORE / "host_sim.cpp", CORE / "rsos_core.cpp", CORE / "rsos_core.h"]
    if not exe.exists() or any(s.stat().st_mtime > exe.stat().st_mtime for s in srcs):
        subprocess.run(["make", "-s", "-C", str(CORE)], check=True)
    return exe


class SimTransport:
    """The firmware core in the host simulator. Time advances only with tick()."""

    def __init__(self):
        self.p = subprocess.Popen([str(build_host_sim())], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
        self.now = 0

    def send(self, line: str):
        self.p.stdin.write(line + "\n"); self.p.stdin.flush()

    def tick(self, t_ms: int) -> list[str]:
        self.now = max(self.now, t_ms)
        self.send(f"TICK {self.now}")
        out = []
        while True:
            line = self.p.stdout.readline().strip()
            if line.startswith("TOCK") or not line:
                return out
            out.append(line)

    def close(self):
        if self.p.poll() is None:
            self.send("QUIT"); self.p.wait(timeout=5)
        for f in (self.p.stdin, self.p.stdout):
            if f and not f.closed:
                f.close()


class ProtocolDevice(Device):
    """An RDP/1 device behind a transport. It plays the whole timeline on its own clock after START."""
    name = "rdp"
    channels = ("haptic", "olfactory", "gustatory")

    def __init__(self, transport=None, consent: bool = False):
        super().__init__()
        self.tx = transport or SimTransport()
        self.consent = consent
        self.log: list[str] = []
        self._open: dict = {}
        self.hello = self._cmd("HELLO")

    def _cmd(self, *lines) -> list[str]:
        for ln in lines:
            self.tx.send(ln)
        out = self.tx.tick(self.tx.now)
        self._ingest(out)
        return out

    def _ingest(self, lines):
        for ln in lines:
            self.log.append(ln)
            f = ln.split()
            if f[0] == "MOTOR":
                t, amp = int(f[1]), float(f[2])
                if "m" in self._open:
                    a = self._open.pop("m"); a.dur_ms = t - a.t_ms
                if amp > 0:
                    a = Action(t, self.name, "pulse", 0, {"amp": amp}); self.actions.append(a); self._open["m"] = a
            elif f[0] == "SCENT":
                t, ch, on = int(f[1]), f[2], f[3] == "1"
                if ch in self._open:
                    a = self._open.pop(ch); a.dur_ms = t - a.t_ms
                if on:
                    a = Action(t, self.name, "release", 0, {"channel": ch}); self.actions.append(a); self._open[ch] = a
            elif f[0] == "REFUSED":
                self.actions.append(Action(int(f[1]), self.name, "refused", 0, {"channel": f[2], "reason": f[3]}))

    def load(self, timeline: dict):
        self._cmd(f"CONSENT {int(self.consent)}", *encode(timeline))

    def arm(self, t_ms: int = 0):
        super().arm(t_ms)
        self.tx.tick(t_ms)
        self._cmd("START")

    def handle(self, event: dict, t_ms: int):
        # The device plays from its own clock; the host only lets simulated time advance.
        if self.armed:
            self._ingest(self.tx.tick(t_ms))

    def stop(self, t_ms: int) -> int:
        self.armed = False
        self._ingest(self.tx.tick(t_ms))
        out = self._cmd("STOP")
        ended = next((int(x.split()[1]) for x in out if x.startswith("STOPPED")), t_ms)
        for a in self._open.values():
            a.dur_ms = ended - a.t_ms
        self._open.clear()
        return ended

    def close(self):
        self.tx.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
