"""Board kit: check a real RSOS wristband (or any RDP/1 device) over USB serial (firmware/BOARD_KIT.md).

  python -m rsso.board --port /dev/ttyUSB0          # quick board check, about 15 s (pyserial needed)
  python -m rsso.board --port COM5 --full           # plus the whole conformance suite in real time (a few minutes)
  python -m rsso.board --sim                        # the same checks against the firmware core in real time, no board

The quick check runs on the device itself and reads back what it reports:

  B1  the device answers HELLO with RDP/1 and its capabilities
  B2  a 3-pulse pattern plays on the device's own clock: 3 pulses of 300 ms, 300 ms apart (±15 ms)
  B3  the intensity limit: a pulse asked at 0.9 under a limit of 0.4 is clamped and reported
  B4  Stop: after STOP the motor is off and STOPPED arrives within 100 ms (host round trip, link included)
  B5  consent: without CONSENT 1 a scent release is refused
  B6  the release cap: a 5 s scent release closes by 3 s
  B7  a glyph's vibration code: the Lion (..-) plays as 100, 100 and 300 ms pulses

`SerialTransport` also lets the whole conformance suite (python -m rsso.conformance) run against the board:
`run_full(port)` uses it for every check. `SimSerialPort` is a stand-in serial port backed by the firmware core
in real time, so this module is tested without hardware.
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import subprocess
import sys
import time

from .protocol import ROOT, ProtocolDevice, build_host_sim

SETTLE_MS = 25      # a reply is complete when the line has been quiet this long


class SimSerialPort:
    """A serial port backed by the firmware core (host_sim) running in real time: a board without a board."""

    def __init__(self):
        self.p = subprocess.Popen([str(build_host_sim())], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
        self.t0 = time.monotonic()
        self.buf: list[str] = []

    def _now(self) -> int:
        return int((time.monotonic() - self.t0) * 1000)

    def _pump(self):
        self.p.stdin.write(f"TICK {self._now()}\n")
        self.p.stdin.flush()
        while True:
            line = self.p.stdout.readline().strip()
            if not line or line.startswith("TOCK"):
                return
            self.buf.append(line)

    def write(self, data: bytes):
        for line in data.decode().splitlines():
            self._pump()                           # the device's clock reaches now before the command
            self.p.stdin.write(line + "\n")
            self.p.stdin.flush()

    def readline(self) -> bytes:
        self._pump()
        if not self.buf:
            time.sleep(0.002)
            return b""
        return (self.buf.pop(0) + "\n").encode()

    def close(self):
        if self.p.poll() is None:
            self.p.stdin.write("QUIT\n")
            self.p.stdin.flush()
            self.p.wait(timeout=5)


def open_port(path: str, baud: int = 115200):
    try:
        import serial  # pyserial
    except ImportError:
        raise SystemExit("Install pyserial first: pip install pyserial")
    port = serial.Serial(path, baud, timeout=0.01)
    time.sleep(2.0)                                # many ESP32 boards reset when the port opens
    port.reset_input_buffer()
    return port


class SerialTransport:
    """An RDP/1 transport over a real (or simulated) serial port, in real time. Shared by every device the
    conformance suite creates, so close() does not close the port; shutdown() does."""

    def __init__(self, port):
        self.port = port
        self.now = 0
        self.t0 = time.monotonic()

    def send(self, line: str):
        self.port.write((line + "\n").encode())

    def read_for(self, ms: int) -> list[str]:
        out, end = [], time.monotonic() + ms / 1000
        while time.monotonic() < end:
            raw = self.port.readline()
            if raw:
                out.append(raw.decode(errors="replace").strip())
        return [x for x in out if x]

    def tick(self, t_ms: int) -> list[str]:
        """Collect what the device says until it has been quiet for SETTLE_MS."""
        self.now = max(self.now, t_ms)
        out, quiet_since = [], time.monotonic()
        while (time.monotonic() - quiet_since) * 1000 < SETTLE_MS:
            raw = self.port.readline()
            if raw:
                line = raw.decode(errors="replace").strip()
                if line:
                    out.append(line)
                quiet_since = time.monotonic()
        return out

    def close(self):
        pass

    def shutdown(self):
        self.port.close()


def _motor(lines):
    return [(int(f[1]), float(f[2])) for f in (x.split() for x in lines) if f and f[0] == "MOTOR"]


def _pulses(motor):
    """[(start, length)] of motor-on intervals."""
    out, on = [], None
    for t, a in motor:
        if a > 0 and on is None:
            on = t
        elif a == 0 and on is not None:
            out.append((on, t - on))
            on = None
    return out


def quick_check(tx: SerialTransport) -> list[tuple]:
    res = []
    tx.send("HELLO")
    hello = next((x for x in tx.read_for(300) if x.startswith("HELLO")), "")
    res.append(("B1", "the device answers HELLO with RDP/1 and its capabilities", hello.startswith("HELLO RDP/1"), hello or "no answer"))

    tx.send("STOP"); tx.read_for(100)
    for ln in ("LOAD 1 0.40", "H 0 300 300 3 0.40", "START"):
        tx.send(ln)
    out = tx.read_for(2200)
    p = _pulses(_motor(out))
    ok = len(p) == 3 and all(abs(l - 300) <= 15 for _, l in p) and all(abs((p[i + 1][0] - p[i][0]) - 600) <= 15 for i in range(len(p) - 1))
    res.append(("B2", "a 3-pulse pattern plays on the device's own clock: 300 ms pulses, 300 ms apart (±15 ms)", ok,
                ", ".join(f"{s}+{l}" for s, l in p) or "no pulses"))

    for ln in ("LOAD 1 0.40", "H 0 200 100 1 0.90", "START"):
        tx.send(ln)
    out = tx.read_for(600)
    clamped = any(x.startswith("CLAMPED") for x in out)
    amps = [a for _, a in _motor(out)]
    res.append(("B3", "a pulse asked at 0.9 under a limit of 0.4 is clamped to 0.4 and reported", clamped and amps and max(amps) <= 0.4 + 1e-9,
                f"CLAMPED {'reported' if clamped else 'missing'}; highest motor {max(amps) if amps else 0:.2f}"))

    for ln in ("LOAD 1 0.40", "H 0 2000 0 1 0.40", "START"):
        tx.send(ln)
    tx.read_for(300)
    sent = time.monotonic()
    tx.send("STOP")
    got, stopped, off = None, False, False
    while (time.monotonic() - sent) < 1.0:
        raw = tx.port.readline()
        line = raw.decode(errors="replace").strip() if raw else ""
        off = off or (line.startswith("MOTOR") and line.endswith(" 0.00"))
        if line.startswith("STOPPED"):
            got = (time.monotonic() - sent) * 1000
            stopped = True
            break
    res.append(("B4", "after STOP the motor is off and STOPPED arrives within 100 ms (host round trip)", stopped and off and got <= 100,
                f"{got:.0f} ms" if got is not None else "no STOPPED"))

    for ln in ("CONSENT 0", "LOAD 1 0.40", "S 0 500 O", "START"):
        tx.send(ln)
    out = tx.read_for(700)
    refused = any(x.startswith("REFUSED") for x in out)
    opened = any(x.startswith("SCENT") and x.endswith(" 1") for x in out)
    res.append(("B5", "without consent a scent release is refused", refused and not opened, "refused" if refused else ("released" if opened else "no report")))

    for ln in ("CONSENT 1", "LOAD 1 0.40", "S 0 5000 O", "START"):
        tx.send(ln)
    out = tx.read_for(3600)
    sc = [(int(f[1]), f[3]) for f in (x.split() for x in out) if f and f[0] == "SCENT" and f[2] == "O"]
    closes = [t for t, v in sc if v == "0"]
    res.append(("B6", "a 5 s scent release closes by 3 s", bool(closes) and closes[0] <= 3000, f"closed at {closes[0]} ms" if closes else "did not close"))
    tx.send("STOP"); tx.read_for(100)
    tx.send("CONSENT 0"); tx.read_for(100)

    for ln in ("LOAD 3 0.40", "H 0 100 100 1 0.40", "H 200 100 100 1 0.40", "H 400 300 100 1 0.40", "START"):
        tx.send(ln)
    out = tx.read_for(1100)
    lengths = [l for _, l in _pulses(_motor(out))]
    ok = len(lengths) == 3 and all(abs(a - b) <= 15 for a, b in zip(lengths, (100, 100, 300)))
    res.append(("B7", "the Lion's vibration code ..- plays as 100, 100 and 300 ms pulses", ok, ", ".join(map(str, lengths)) or "no pulses"))
    return res


def run_full(port) -> list[tuple]:
    """The whole conformance suite in real time against the device behind `port` (virtual audio and display)."""
    from .conformance import run_suite
    from .devices import VirtualAudio, VirtualDisplay
    from .runtime import RealTimeClock
    tx = SerialTransport(port)

    def factory(consent: bool = False):
        return [ProtocolDevice(transport=tx, consent=consent), VirtualAudio(), VirtualDisplay()]
    return run_suite(factory, clock_factory=RealTimeClock)


def report(name: str, hello: str, results: list[tuple]) -> str:
    lines = [f"# Board check: {name}", "", f"Date: {datetime.date.today().isoformat()}. Device: `{hello}`.", "",
             "| Check | Requirement | Result | Measured |", "|---|---|---|---|"]
    for cid, req, ok, measured in results:
        lines.append(f"| {cid} | {req} | {'PASS' if ok else 'FAIL'} | {measured} |")
    lines += ["", f"{sum(1 for r in results if r[2])}/{len(results)} checks passed."]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check an RSOS wristband (RDP/1) over USB serial.")
    ap.add_argument("--port", help="serial port, e.g. /dev/ttyUSB0 or COM5")
    ap.add_argument("--sim", action="store_true", help="check the firmware core in real time instead of a board")
    ap.add_argument("--full", action="store_true", help="also run the whole conformance suite (a few minutes)")
    ap.add_argument("--out", help="write the report to this file")
    a = ap.parse_args(argv)
    if not a.port and not a.sim:
        ap.error("give --port (a board) or --sim")
    port = SimSerialPort() if a.sim else open_port(a.port)
    tx = SerialTransport(port)
    res = quick_check(tx)
    hello = res[0][3]
    if a.full:
        res += run_full(port)
    text = report("firmware core in real time (no board)" if a.sim else a.port, hello, res)
    print(text)
    if a.out:
        pathlib.Path(a.out).write_text(text, encoding="utf-8")
    tx.shutdown()
    return 0 if all(r[2] for r in res) else 1


if __name__ == "__main__":
    sys.exit(main())
