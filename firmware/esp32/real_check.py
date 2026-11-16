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
    return 0 if all(r[2] for r in res) else 1


def cmd_passkey(a):
    b = Band(a.port)
    boot = b.lines_for(a.boot_wait)
    pk = None
    for _ in range(a.hello_tries):
        pk = passkey_of(b.send("PASSKEY", 1.0))
        if pk is not None:
            break
    print(json.dumps({"boot": boot, "passkey": pk, "transcript": b.log}, indent=1))
    return 0 if pk is not None else 1


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
    a = ap.parse_args(argv)
    return {"compile": cmd_compile, "image": cmd_image, "usb": cmd_usb, "passkey": cmd_passkey}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
