#!/usr/bin/env python3
"""The wristband firmware with the real ESP32 compilers and Espressif's QEMU (spec/ESP32_TOOLS.md).

Needs: arduino-cli with Arduino-ESP32 2.0.17, 3.3.12 and 3.2.1 in three data directories (one config file each), the GFX
Library for Arduino in both, and Espressif's qemu-system-xtensa and qemu-system-riscv32.

  python3 real_check.py compile --cfg2 ac2/cfg.yaml --cfg3 ac3/cfg.yaml --cfg32 ac32/cfg.yaml --out builds/
                                                         # C1: 30 builds, C1b: 10 more (C3, S3 on 3.2.1)
  python3 real_check.py image   --build builds/build/<build> --chip esp32 --esptool <core's esptool> \
                                --core-dir <core's hardware dir> --out flash.bin       # E1: one 4 MB image
  python3 real_check.py usb     --port 5555                                              # E3: U1-U8, U3b over a socket
  python3 real_check.py passkey --port 5555                                              # U9: read the passkey
  python3 real_check.py pwm     --port 5555 --trace led.log     # spec/BOARD_PENDING.md K3 (qemu ... -trace "led_*" -D led.log)

`compile` runs, for each build:
  arduino-cli --config-file <cfg> compile --fqbn <fqbn> --build-path <dir> --warnings default \
      --build-property compiler.cpp.extra_flags=<flags> <sketch copy>
and writes builds/<name>.log (the whole compiler output) and builds/summary.json. `image` runs the core's
esptool `merge_bin`. `usb` and `passkey` speak to the band over a TCP socket (`qemu ... -serial tcp::<port>,server`).
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import pathlib
import re
import shutil
import socket
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
SKETCH = HERE / "rsos_esp32"
CHIPS = {   # FQBN and the pin flags of platformio.ini
    "esp32": ("esp32:esp32:esp32", []),
    "esp32c3": ("esp32:esp32:esp32c3:CDCOnBoot=cdc", ["-DRSOS_MOTOR_PIN=5", "-DRSOS_SCENT_PIN=6", "-DRSOS_TASTE_PIN=7"]),
    "esp32s3": ("esp32:esp32:esp32s3", ["-DRSOS_MOTOR_PIN=4", "-DRSOS_SCENT_PIN=5", "-DRSOS_TASTE_PIN=6"]),
}
NIMBLE_GUARD = "RSOS: this core builds Bluetooth with NimBLE"
FLAGSETS = {"band": [], "thermal": ["-DRSOS_THERMAL"], "sites": ["-DRSOS_SITES"], "display": ["-DRSOS_DISPLAY"],
            "all": ["-DRSOS_THERMAL", "-DRSOS_SITES", "-DRSOS_DISPLAY"]}


def sketch_copy(dest: pathlib.Path) -> pathlib.Path:
    d = dest / "rsos_esp32"
    if d.exists():
        shutil.rmtree(d)
    shutil.copytree(SKETCH, d)
    return d


def compile_one(cli, cfg, fqbn, flags, sketch, build, warnings="default"):
    cmd = [cli, "--config-file", cfg, "compile", "--fqbn", fqbn, "--build-path", str(build), "--warnings", warnings]
    if flags:
        cmd += ["--build-property", "compiler.cpp.extra_flags=" + " ".join(flags)]
    t = time.time()
    r = subprocess.run(cmd + [str(sketch)], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr, time.time() - t


def sizes(text):
    f = re.search(r"Sketch uses (\d+) bytes \((\d+)%\) of program storage space", text)
    m = re.search(r"Global variables use (\d+) bytes \((\d+)%\) of dynamic memory", text)
    return {"flash": int(f.group(1)) if f else None, "flash_pct": int(f.group(2)) if f else None,
            "ram": int(m.group(1)) if m else None, "ram_pct": int(m.group(2)) if m else None}


def cmd_compile(a):
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    sketch = sketch_copy(out / "src")
    summary = []
    only = set(a.only.split(",")) if a.only else None
    cores = [("2.0.17", a.cfg2), ("3.3.12", a.cfg3)] + ([("3.2.1", a.cfg32)] if a.cfg32 else [])
    for core, cfg in cores:
        for chip, (fqbn, pins) in CHIPS.items():
            if core == "3.2.1" and chip == "esp32":      # C1b: only C3 and S3 (3.3.12 builds the ESP32 with Bluedroid)
                continue
            for fs, flags in FLAGSETS.items():
                name = f"{chip}-{core}-{fs}"
                if only and name not in only:
                    continue
                build = out / "build" / name
                code, text, secs = compile_one(a.cli, cfg, fqbn, pins + flags + a.extra, sketch, build, a.warnings)
                (out / f"{name}.log").write_text(text, encoding="utf-8")
                row = {"build": name, "core": core, "chip": chip, "flags": pins + flags + a.extra, "exit": code,
                       "seconds": round(secs), **sizes(text),
                       "errors": [ln for ln in text.splitlines() if re.search(r"\berror\b", ln)]}
                summary.append(row)
                print(f"{name:28s} exit {code}  {secs:5.0f}s  flash {row['flash']}  ram {row['ram']}", flush=True)
                if not a.keep and code == 0 and chip != a.keep_chip:
                    shutil.rmtree(build, ignore_errors=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    if a.expect_nimble_guard:   # spec/BOARD_PENDING.md K1-P
        ok = True
        for r in summary:
            nimble = r["chip"] in ("esp32c3", "esp32s3") and r["core"] == "3.3.12"
            log = (out / f"{r['build']}.log").read_text(encoding="utf-8")
            good = (r["exit"] != 0 and NIMBLE_GUARD in log) if nimble else r["exit"] == 0
            ok = ok and good
            print(f"K1-P {r['build']:28s} {'ok' if good else 'UNEXPECTED'} "
                  f"({'stops at the NimBLE guard' if nimble else 'compiles'} expected; exit {r['exit']})")
        print(f"K1-P {'pass' if ok else 'FAIL'}: {len(summary)} builds")
        return 0 if ok else 1
    return 0 if all(r["exit"] == 0 for r in summary) else 1


def cmd_image(a):
    build = pathlib.Path(a.build)
    app = next(build.glob("*.ino.bin"))
    boot = next(build.glob("*.ino.bootloader.bin"))
    parts = next(build.glob("*.ino.partitions.bin"))
    boot0 = glob.glob(os.path.join(a.core_dir, "tools/partitions/boot_app0.bin"))
    boot_at = "0x1000" if a.chip == "esp32" else "0x0"
    tool = [sys.executable, a.esptool] if a.esptool.endswith(".py") else [a.esptool]
    args = [*tool, "--chip", a.chip, "merge_bin" if not a.esptool5 else "merge-bin", "-o", a.out,
            "--fill-flash-size", "4MB",
            boot_at, str(boot), "0x8000", str(parts)]
    if boot0:
        args += ["0xe000", boot0[0]]
    args += ["0x10000", str(app)]
    print(" ".join(map(str, args)))
    return subprocess.run(args).returncode


class Band:
    def __init__(self, port, connect_s=60):
        end = time.time() + connect_s
        while True:
            try:
                self.s = socket.create_connection(("localhost", port), timeout=2)
                break
            except OSError:
                if time.time() > end:
                    raise
                time.sleep(0.5)
        self.s.settimeout(0.05)
        self.buf = b""
        self.log = []

    def lines_for(self, secs):
        end, out = time.time() + secs, []
        while time.time() < end:
            try:
                d = self.s.recv(4096)
                if d:
                    self.buf += d
            except socket.timeout:
                pass
            while b"\n" in self.buf:
                ln, self.buf = self.buf.split(b"\n", 1)
                t = ln.decode(errors="replace").strip()
                if t:
                    out.append(t)
                    self.log.append("< " + t)
        return out

    def send(self, line, wait=1.0):
        self.log.append("> " + line)
        self.s.sendall((line + "\n").encode())
        return self.lines_for(wait)


def valid_passkey(pk: int) -> bool:   # the rule of rsos_link.cpp valid_passkey (BLE_PAIRING P2)
    s = f"{pk:06d}"
    return 0 < pk <= 999999 and len(set(s)) > 1 and s not in ("123456", "654321")


def passkey_of(lines):
    for x in lines:
        m = re.fullmatch(r"PASSKEY (\d{6})", x)
        if m:
            return int(m.group(1))
    return None


def cmd_usb(a):
    b = Band(a.port)
    boot = b.lines_for(a.boot_wait)
    res = []
    hello = None
    for _ in range(a.hello_tries):
        got = b.send("HELLO", 1.0)
        hello = next((x for x in got if x.startswith("HELLO")), None)
        if hello:
            break
    res.append(("U1", "HELLO", hello == "HELLO RDP/1 haptic,olfactory,gustatory 0.60", hello or "no answer"))
    b.send("STOP", 0.5)
    b.send("LOAD 1 0.40", 0.3); b.send("H 0 300 300 3 0.40", 0.3)
    got = b.send("START", 3.0)
    motor = [x for x in got if x.startswith("MOTOR")]
    ons = [x for x in motor if x.endswith(" 0.40")]
    res.append(("U2", "LOAD 1 0.40 / H 0 300 300 3 0.40 / START", len(ons) == 3 and bool(motor) and motor[-1].endswith(" 0.00"),
                "; ".join(motor) or "no MOTOR lines"))
    got = b.send("STOP", 1.0)
    st = next((x for x in got if x.startswith("STOPPED")), None)
    res.append(("U3", "STOP", st is not None, st or "; ".join(got) or "no answer"))
    b.send("LOAD 1 0.40", 0.3); b.send("H 0 2000 0 1 0.40", 0.3)
    b.send("START", 0.3)
    got = b.send("STOP", 1.0)
    st = next((x for x in got if x.startswith("STOPPED ")), None)
    off = any(x.startswith("MOTOR") and x.endswith(" 0.00") for x in got)
    res.append(("U3b", "STOP while a 2 s pulse plays", st is not None and off, "; ".join(got) or "no answer"))
    got = b.send("PASSKEY", 1.0)
    pk1 = passkey_of(got)
    res.append(("U4", "PASSKEY", pk1 is not None and valid_passkey(pk1), "; ".join(got) or "no answer"))
    got = b.send("PAIR", 1.0)
    res.append(("U5", "PAIR", "PAIR open 120" in got, "; ".join(got) or "no answer"))
    got = b.send("UNPAIR", 1.0)
    res.append(("U6", "UNPAIR", "UNPAIR all" in got, "; ".join(got) or "no answer"))
    got = b.send("NEWKEY", 2.0)
    got2 = b.send("PASSKEY", 1.0)
    pk2 = passkey_of(got2)
    res.append(("U7", "NEWKEY then PASSKEY", "NEWKEY done; read it with PASSKEY" in got and pk2 is not None and valid_passkey(pk2) and pk2 != pk1,
                "; ".join(got + got2) or "no answer"))
    got = b.send("A" * 100, 1.0)
    got2 = b.send("HELLO", 1.0)
    res.append(("U8", "a line of 100 letters, then HELLO", got == ["ERR LINE too-long"] and any(x.startswith("HELLO RDP/1") for x in got2),
                "; ".join(got + got2) or "no answer"))
    report = {"boot": boot, "results": res, "passkeys": [pk1, pk2], "transcript": b.log}
    if a.out:
        pathlib.Path(a.out).write_text(json.dumps(report, indent=1), encoding="utf-8")
    for r in res:
        print(f"{r[0]} {'PASS' if r[2] else 'FAIL'}  {r[1]}  ->  {r[3]}")
    failed = {r[0] for r in res if not r[2]}
    if a.expected_fail is not None:   # spec/BOARD_PENDING.md K1: U3 is expected not to pass (ESP32_TOOLS §7.4)
        want = set(x for x in a.expected_fail.split(",") if x)
        print(f"failed {sorted(failed)}, expected {sorted(want)}: {'as expected' if failed == want else 'UNEXPECTED'}")
        return 0 if failed == want else 1
    return 0 if not failed else 1


def cmd_passkey(a):
    b = Band(a.port)
    boot = b.lines_for(a.boot_wait)
    pk = None
    for _ in range(a.hello_tries):
        pk = passkey_of(b.send("PASSKEY", 1.0))
        if pk is not None:
            break
    print(json.dumps({"boot": boot, "passkey": pk, "transcript": b.log}, indent=1))
    if a.expect_from:   # U9: the key U7 made, read back after a restart on the same flash
        want = json.loads(pathlib.Path(a.expect_from).read_text(encoding="utf-8"))["passkeys"][1]
        print(f"U9 {'PASS' if pk == want else 'FAIL'}  passkey after restart {pk}, U7 made {want}")
        return 0 if pk == want else 1
    return 0 if pk is not None else 1


class LedTrace:
    """The emulated ESP32 LEDC duty writes, from QEMU's led_* trace events (spec/BOARD_PENDING.md K3)."""
    SET = re.compile(r"led_set_intensity .*intensity: (\d+)%")
    CHG = re.compile(r"led_change_intensity .*intensity (\d+)% -> (\d+)%")

    def __init__(self, path):
        self.path, self.pos, self.rest = pathlib.Path(path), 0, ""

    def read(self):
        """New events since the last call: ("set", level) or ("change", old, new), with the host time seen."""
        if not self.path.exists():
            return []
        with self.path.open("r", errors="replace") as f:
            f.seek(self.pos)
            data = f.read()
            self.pos = f.tell()
        data, out, now = self.rest + data, [], time.time()
        lines = data.split("\n")
        self.rest = lines.pop()
        for ln in lines:
            m = self.CHG.search(ln)
            if m:
                out.append((now, "change", int(m.group(1)), int(m.group(2))))
                continue
            m = self.SET.search(ln)
            if m:
                out.append((now, "set", int(m.group(1))))
        return out


def cmd_pwm(a):
    tr = LedTrace(a.trace)
    b = Band(a.port)
    boot = b.lines_for(a.boot_wait)
    ev = tr.read()
    res = [("K3a", "only 0% from boot to the first command", bool(ev) and all(e[-1] == 0 and (e[1] == "set" or e[2] == 0) for e in ev),
            f"{len(ev)} events, levels {sorted({e[-1] for e in ev})}")]

    b.s.settimeout(0.002)
    evs = []

    def pump(sec):   # read the band and the trace together, so each change gets the host time it appeared
        out, end = [], time.time() + sec
        while time.time() < end:
            out += b.lines_for(0.005)
            evs.extend(tr.read())
        return out

    def case(lines, wait, stop_after=None):
        tr.read()
        evs.clear()
        got = []
        for ln in lines:
            b.log.append("> " + ln)
            b.s.sendall((ln + "\n").encode())
            got += pump(0.05)
        if stop_after is not None:
            got += pump(stop_after)
            b.log.append("> STOP")
            b.s.sendall(b"STOP\n")
        got += pump(wait)
        ch = [e for e in evs if e[1] == "change"]
        on_ms = [round((ch[i + 1][0] - ch[i][0]) * 1000) for i in range(0, len(ch) - 1, 2)]
        return [(e[2], e[3]) for e in ch], on_ms, got

    ch, on, got = case(["LOAD 1 0.40", "H 0 300 300 3 0.40", "START"], 3.0)
    res.append(("K3b", "three pulses: 0->40, 40->0 three times", ch == [(0, 40), (40, 0)] * 3, f"{ch}; on-times (host) {on} ms"))
    ch, on, got = case(["LOAD 1 0.40", "H 0 200 100 1 0.90", "START"], 1.5)
    res.append(("K3c", "0.9 under a program limit of 0.4: 0->40, 40->0", ch == [(0, 40), (40, 0)], f"{ch}; on-times (host) {on} ms"))
    ch, on, got = case(["LOAD 1 0.90", "H 0 300 100 1 0.90", "START"], 1.5)
    res.append(("K3d", "0.9 under the device envelope 0.6: 0->60, 60->0", ch == [(0, 60), (60, 0)], f"{ch}; on-times (host) {on} ms"))
    ch, on, got = case(["LOAD 1 0.40", "H 0 5000 0 1 0.40", "START"], 0.5, stop_after=0.3)
    stopped = next((x for x in got if x.startswith("STOPPED ")), None)
    res.append(("K3e", "STOP during a 5 s pulse: 0->40, 40->0, STOPPED", ch == [(0, 40), (40, 0)] and stopped is not None,
                f"{ch}; {stopped or 'no STOPPED'}; on-time (host) {on} ms"))
    if a.out:
        pathlib.Path(a.out).write_text(json.dumps({"boot": boot, "results": res, "transcript": b.log}, indent=1), encoding="utf-8")
    for r in res:
        print(f"{r[0]} {'PASS' if r[2] else 'FAIL'}  {r[1]}  ->  {r[3]}")
    return 0 if all(r[2] for r in res) else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compile")
    c.add_argument("--cli", default="arduino-cli")
    c.add_argument("--cfg2", required=True)
    c.add_argument("--cfg3", required=True)
    c.add_argument("--cfg32", help="config of the Arduino-ESP32 3.2.1 data directory (C1b)")
    c.add_argument("--out", required=True)
    c.add_argument("--only", help="comma-separated build names, e.g. esp32-3.3.12-band")
    c.add_argument("--extra", nargs="*", default=[], help="extra flags for every build (e.g. -DRSOS_EMULATOR for E1)")
    c.add_argument("--warnings", default="default")
    c.add_argument("--keep", action="store_true", help="keep every build directory")
    c.add_argument("--keep-chip", default="", help="keep build directories of this chip")
    c.add_argument("--expect-nimble-guard", action="store_true",
                   help="pass when every build compiles except C3/S3 on 3.3.12, which must stop at the NimBLE guard (K1-P)")
    i = sub.add_parser("image")
    i.add_argument("--build", required=True)
    i.add_argument("--chip", required=True)
    i.add_argument("--esptool", required=True)
    i.add_argument("--esptool5", action="store_true", help="esptool 5 command names")
    i.add_argument("--core-dir", required=True)
    i.add_argument("--out", required=True)
    for name, fn in (("usb", cmd_usb), ("passkey", cmd_passkey)):
        u = sub.add_parser(name)
        u.add_argument("--port", type=int, required=True)
        u.add_argument("--boot-wait", type=float, default=8.0)
        u.add_argument("--hello-tries", type=int, default=10)
        u.add_argument("--out")
        if name == "usb":
            u.add_argument("--expected-fail", help="comma-separated checks expected to fail, e.g. U3; exit 0 only if exactly these fail")
        else:
            u.add_argument("--expect-from", help="the usb --out file whose U7 passkey must come back (U9)")
    w = sub.add_parser("pwm")
    w.add_argument("--port", type=int, required=True)
    w.add_argument("--trace", required=True, help="the file given to qemu -D, with -trace \"led_*\"")
    w.add_argument("--boot-wait", type=float, default=12.0)
    w.add_argument("--out")
    a = ap.parse_args(argv)
    return {"compile": cmd_compile, "image": cmd_image, "usb": cmd_usb, "passkey": cmd_passkey, "pwm": cmd_pwm}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
