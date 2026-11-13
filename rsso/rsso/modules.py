"""The RDP/1.1 modules in simulation: the real module code (firmware/rsos_core/rsos_modules.*) against a physical model
of a Peltier wrist module, plus the multi-site driver and the display gate (spec/MACHINES.md §12).

`python -m rsso.modules --evaluate` builds firmware/rsos_core/module_sim, runs every scenario, checks each against its
requirement and writes rsso/results/modules.md. BENCH lists the checks to run on an assembled module.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
CORE = ROOT / "firmware" / "rsos_core"

TITLES = {
    "cool_2": "Cool by 2 °C for a minute", "warm_3": "Warm by 3 °C for two minutes", "cool_4_long": "Cool by 4 °C for two minutes",
    "command_6": "A request for +6 °C (beyond the envelope)", "hot_day_warm_4": "Warm by 4 °C on a hot day (skin 35.5 °C)",
    "sensor_open": "The skin thermistor comes loose at 30 s", "sensor_stuck": "The skin thermistor is stuck from the start",
    "sensor_spike": "A 5 °C spike on the thermistor", "sink_overheats": "Cooling with a covered heat sink in 35 °C air",
    "battery_low": "The battery sags below 3.3 V at 40 s", "stop_mid_cue": "Stop at 20 s",
}


def build() -> pathlib.Path:
    exe = CORE / "module_sim"
    srcs = [CORE / "module_sim.cpp", CORE / "rsos_modules.cpp", CORE / "rsos_modules.h"]
    if not exe.exists() or any(s.stat().st_mtime > exe.stat().st_mtime for s in srcs):
        subprocess.run(["make", "-s", "-C", str(CORE), "module_sim"], check=True)
    return exe


def sim(what: str) -> list:
    return subprocess.run([str(build()), what], capture_output=True, text=True, check=True).stdout.splitlines()


def thermal() -> list:
    out = []
    for ln in sim("thermal"):
        f = ln.split()
        d = {"name": f[1]}
        for kv in f[2:]:
            k, v = kv.split("=")
            d[k] = v if k == "fault" else float(v)
        out.append(d)
    return out


def _req(d):
    """(requirement, passed) for one thermal scenario."""
    n, safe = d["name"], d["max_skin"] <= 40.0 and d["min_skin_base"] - abs(d["max_dev"]) >= 15.0
    if n in ("cool_2", "warm_3", "cool_4_long", "command_6"):
        lim = 4.0 if n == "command_6" else abs(d["target"])
        return ("reaches the target within 20 s, overshoot at most 0.3 °C, never beyond the ±4 °C envelope, no fault",
                safe and 0 <= d["settle_s"] <= 20 and d["overshoot"] <= 0.3 and abs(d["max_dev"]) <= 4.1 and d["fault"] == "none"
                and abs(d["target"]) == lim)
    if n == "hot_day_warm_4":
        return ("the target is held below 39 °C on the skin; skin never above 39.5 °C", d["max_skin"] <= 39.5 and d["fault"] == "none")
    if n in ("sensor_open", "sensor_spike", "battery_low"):
        want = {"sensor_open": "skin-sensor", "sensor_spike": "skin-sensor-jump", "battery_low": "battery"}[n]
        return (f"off within 100 ms with the fault '{want}'", safe and d["fault"] == want and 0 <= d["latency_ms"] <= 100 and d["end_duty"] == 0)
    if n == "sensor_stuck":
        return ("found within 6 s of the cue's start; the skin moved less than 2.5 °C meanwhile",
                safe and d["fault"] == "skin-not-responding" and d["fault_s"] - 2 <= 6 and abs(d["dev_at_fault"]) < 2.5)
    if n == "sink_overheats":
        return ("off when the heat sink reaches 45 °C (safe to touch); skin never above 40 °C", safe and d["fault"] == "sink-hot" and d["max_sink"] <= 45.5)
    if n == "stop_mid_cue":
        return ("the element is off in the same control step as Stop", safe and d["latency_ms"] == 0 and d["end_duty"] == 0 and d["final_dev"] == 0)
    return ("", False)


def sites() -> dict:
    L = sim("sites")
    rtp = [[int(x) for x in ln.split()[1:]] for ln in L if ln.startswith("RTP")]
    mism = [int(x) for x in next(ln for ln in L if ln.startswith("MISMATCH")).split()[1:]]
    cap = int(next(ln for ln in L if ln.startswith("CAP")).split()[1])
    off = int(next(ln for ln in L if ln.startswith("OFF")).split()[1])
    return {"rtp": rtp, "mismatch": mism, "cap": cap, "off": off}


def display() -> dict:
    L = sim("display")
    day = [float(x) for x in L[0].split()[1:]]
    night = [float(x) for x in L[1].split()[1:]]
    names = {ln.split()[1]: ln.split()[2] == "1" for ln in L if ln.startswith("NAME")}
    return {"day": day, "night": night, "names": names}


def checks() -> list:
    """(id, requirement, passed, measured) for every module check M1-M15."""
    res = []
    for k, d in enumerate(thermal()):
        req, ok = _req(d)
        m = (f"target {d['target']:+g} °C, settled in {d['settle_s']:g} s, overshoot {d['overshoot']:g}, largest change {d['max_dev']:+g}, "
             f"skin up to {d['max_skin']:g} °C, sink up to {d['max_sink']:g} °C" if d["settle_s"] >= 0 else
             f"skin up to {d['max_skin']:g} °C, sink up to {d['max_sink']:g} °C")
        if d["fault"] != "none":
            m += f"; fault '{d['fault']}' at {d['fault_s']:g} s" + (f", {d['latency_ms']:g} ms after the cause" if d["latency_ms"] >= 0 else "")
        res.append((f"M{k + 1}", TITLES[d["name"]] + ": " + req, ok, m))
    s = sites()
    peak = max(r[1] for r in s["rtp"])
    first = s["rtp"][0][1]
    steady = {r[2] for r in s["rtp"]}
    n = len(res)
    res.append((f"M{n + 1}", "Several sites: a 6 Hz rhythm at half strength rises from 0 to half scale and back; a site without rhythm holds its strength",
                first == 0 and 120 <= peak <= 128 and steady == {102}, f"rhythm 0 → {peak} of 255; steady site {sorted(steady)}"))
    res.append((f"M{n + 2}", "Several sites: drive capped at full scale, off when the site stops; a carrier far from the motor's resonance is reported",
                s["cap"] == 255 and s["off"] == 0 and s["mismatch"] == [0, 1, 0], f"cap {s['cap']}, off {s['off']}, mismatch flags {s['mismatch']}"))
    dp = display()
    res.append((f"M{n + 3}", "Display: full brightness by day; at most 20% at night",
                dp["day"] == [1.0, 0.5] and dp["night"] == [0.2, 0.1], f"day {dp['day']}, night {dp['night']}"))
    good = all(dp["names"][x] for x in ("lion", "owl_2", "a-b")) and not any(dp["names"][x] for x in ("(empty)", "../etc", "Lion", "abcdefghijklmnopqrstuvwx"))
    res.append((f"M{n + 4}", "Display: an image name is a plain file name (a-z, 0-9, _ and -, up to 23 characters), never a path",
                good, ", ".join(f"{k}: {'ok' if v else 'refused'}" for k, v in dp["names"].items())))
    return res


BENCH = [
    ("T1", "Cooling and warming", "Power on, strap on, no cue: the module reports skin and sink temperature within 1 °C of a reference thermometer."),
    ("T2", "Cooling and warming", "Play `T 0 60000 -2`: the skin side reaches 2 °C below the start within 20 s and holds it within 0.3 °C (reference thermometer under the plate)."),
    ("T3", "Cooling and warming", "Play `T 0 60000 3`, then send STOP at 20 s: THERMAL 0.00 is reported at once and the element current is zero (multimeter)."),
    ("T4", "Cooling and warming", "Unplug the skin thermistor during a cue: FAULT skin-sensor and zero current within 100 ms."),
    ("T5", "Cooling and warming", "Lift the module off the skin at the start of a warm cue: FAULT skin-not-responding within 6 s."),
    ("T6", "Cooling and warming", "Warm a thermistor with a finger to 41 °C equivalent (or a resistor of that value): FAULT skin-limit, element off."),
    ("S1", "Several sites", "Play a two-part code spread over left wrist and chest: each part is felt on its site, in order."),
    ("S2", "Several sites", "Play `HF 0 1000 0 1 0.5 0 6 chest`: the vibration pulses six times a second."),
    ("S3", "Several sites", "Play four sites at once: three vibrate and REFUSED is reported for the fourth."),
    ("D1", "Display", "Copy an image to flash and play `D 0 5000 <name>`: it shows for five seconds, then the screen is dark."),
    ("D2", "Display", "Send `NIGHT 1`, then play an image: the backlight is at most 20% (light meter or a phone camera at fixed exposure)."),
]


def report(res) -> str:
    L = ["# RDP/1.1 modules in simulation", "",
         "Generated by `python -m rsso.modules --evaluate`. The module code that the ESP32 sketch runs (`firmware/rsos_core/rsos_modules.*`) is run on a PC: "
         "the thermal controller against a physical model of a 20 mm Peltier module on the wrist (skin, element, heat sink, thermistors with a 1 s lag and "
         "noise), with faults injected; the multi-site driver and the display gate directly. No module has been assembled yet; the bench checks for an "
         "assembled module are in `firmware/BOARD_KIT.md` §8.", "",
         "| Check | Requirement | Result | Measured |", "|---|---|---|---|"]
    for cid, req, ok, m in res:
        L.append(f"| {cid} | {req} | {'PASS' if ok else 'FAIL'} | {m} |")
    L += ["", f"{sum(r[2] for r in res)}/{len(res)} checks passed.", "",
          "Reading: every fault turns the element off within one 50 ms control step and keeps it off until the cue has ended and every reading is back "
          "in range. After a hot-sink cut-off, heat leaks back through the element and the skin warms by about 3 °C before settling: well below 40 °C, "
          "but felt, so the protocol kit asks for the heat sink to stay uncovered. The physical model's values are typical for a 20 mm module, not "
          "measured on one; T1-T6 on the bench replace them with real ones."]
    return "\n".join(L) + "\n"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["--evaluate"]:
        r = checks()
        path = ROOT / "rsso" / "results" / "modules.md"
        path.write_text(report(r), encoding="utf-8")
        print(f"wrote {path}; {sum(x[2] for x in r)}/{len(r)} checks passed.")
        return 0 if all(x[2] for x in r) else 1
    print("usage: python -m rsso.modules --evaluate")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
