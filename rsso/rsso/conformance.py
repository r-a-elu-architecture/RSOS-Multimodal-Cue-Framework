"""RSOS conformance suite: what any runtime + device set must do to be called RSOS-compatible.

Run it against the virtual rig:      python -m rsso.conformance
Run it against your own hardware:    write a factory returning your Device objects (same interface as
                                     rsso.devices) and call run_suite(factory, clock_factory=RealTimeClock).

Each check returns (id, requirement, passed, measured). The requirements follow spec/OVERRIDE_PROTOCOL.md §9.
"""
from __future__ import annotations

import copy
import pathlib
import sys

from .devices import standard_rig
from .runtime import VirtualClock, play

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "rsx"))
from rsx import compile_rsx, SafetyGovernor  # noqa: E402

MAX_LATENESS_MS = 10
MAX_STOP_LATENCY_MS = 100


def _override():
    return compile_rsx((ROOT / "rsx" / "protocols" / "override.rsx").read_text(encoding="utf-8"))


def run_suite(device_factory=standard_rig, clock_factory=VirtualClock) -> list[tuple]:
    res = []
    tl = _override()

    # C1 timing and C8 completeness
    devs = device_factory(); tr = play(tl, devs, clock_factory())
    res.append(("C1", f"every event dispatched within {MAX_LATENESS_MS} ms of its time", tr.max_lateness_ms <= MAX_LATENESS_MS, f"{tr.max_lateness_ms} ms"))
    handled = {ch for d in devs for ch in d.channels}
    needed = {e["channel"] for e in tl["events"] if e["channel"] not in ("annotation", "device")}
    res.append(("C8", "every output channel in the program has a device", needed <= handled, ", ".join(sorted(needed - handled)) or "all covered"))
    says = [a.detail["text"] for d in devs for a in d.actions if a.kind == "speech"]
    res.append(("C10", '"I move, I act" spoken exactly once, then "I own" once', says == ["I move, I act", "I own"], " | ".join(says)))
    res.append(("C11", "a run that is not stopped completes", tr.completed, "completed" if tr.completed else "not completed"))

    # C2, C3 stopping, in every phase
    worst, leaked = 0, []
    for p in tl["phases"]:
        at = p["t"] + p["dur"] // 2
        devs = device_factory(); tr = play(tl, devs, clock_factory(), stop_at_ms=at)
        worst = max(worst, tr.stop_latency_ms)
        leaked += [f"{d.name}@{p['name']}" for d in devs if d.output_after(at)]
    res.append(("C2", f"output ends within {MAX_STOP_LATENCY_MS} ms of Stop, in every phase", worst <= MAX_STOP_LATENCY_MS, f"worst {worst} ms"))
    res.append(("C3", "no device output after Stop", not leaked, ", ".join(leaked) or "none"))

    # C4 intensity limit, even if a timeline was tampered with after compiling
    bad = copy.deepcopy(tl)
    for e in bad["events"]:
        if e["channel"] == "haptic":
            e["amp"] = 0.95
    devs = device_factory(); tr = play(bad, devs, clock_factory())
    peak = max((a.detail["amp"] for d in devs for a in d.actions if "amp" in a.detail), default=0)
    res.append(("C4", "haptic intensity never exceeds the program's haptic_max", peak <= tl["safety"]["haptic_max"] + 1e-12, f"peak {peak} (limit {tl['safety']['haptic_max']})"))

    # C5, C6 triggering rules
    g = SafetyGovernor.from_timeline(tl, opted_in=False)
    tr = play(tl, device_factory(), clock_factory(), governor=g, trigger="device", now_ms=0)
    res.append(("C5", "no device-triggered run without opt-in", not tr.started, tr.reason))
    g = SafetyGovernor.from_timeline(tl, opted_in=True); refused = []
    for t in (0, 30_000, 200_000, 400_000, 600_000, 800_000, 1_000_000, 1_200_000):
        tr = play(tl, device_factory(), clock_factory(), governor=g, trigger="device", now_ms=t)
        if not tr.started:
            refused.append((t // 1000, tr.reason))
    ok = refused[:1] == [(30, "refractory period")] and refused[-1:] == [(1200, "hourly limit")]
    res.append(("C6", "refractory period and hourly limit enforced for device-triggered runs", ok, "; ".join(f"{a}s {b}" for a, b in refused)))
    tr = play(tl, device_factory(), clock_factory(), governor=g, trigger="self", now_ms=1_210_000)
    res.append(("C9", "a self-initiated run is always allowed", tr.started, tr.reason))

    # C7 scent requires confirmation
    scent_src = 'PROTOCOL s\nTIER 1 LION {\nV "a"\nA "b"\nK "c"\nO "cedar"\n}\nPHASE p {\nACTIVATE LION\n}'
    stl = compile_rsx(scent_src)
    devs = device_factory(); play(stl, devs, clock_factory())
    released = [a for d in devs for a in d.actions if a.kind == "release"]
    res.append(("C7", "no scent or taste is released before the person confirms no allergy or aversion", not released, f"{len(released)} releases"))
    # C12, C13 consented programming
    from .consent import Consent, ConsentStore, cue_program
    store = ConsentStore()
    c = Consent(id="c1", content="When doubt appears, I move", person="client", author="therapist", tier="422", created_ms=0)
    ctl = compile_rsx(cue_program(c))
    no_record = play(ctl, device_factory(), clock_factory(), consents=None, now_ms=1000)
    store.add(c)
    with_record = play(ctl, device_factory(), clock_factory(), consents=store, now_ms=1000)
    led = Consent(id="c2", content="The old pattern ends", person="client", author="therapist", tier="420", created_ms=0)
    store.add(led)
    led_alone = play(compile_rsx(cue_program(led)), device_factory(), clock_factory(), consents=store, now_ms=1000)
    ok12 = (not no_record.started) and with_record.started and with_record.completed and not led_alone.started
    res.append(("C12", "no programmed cue runs without a consent record naming its content (therapist-led tiers: therapist present and screening passed)",
                ok12, f"without record: {no_record.reason}; with record: {with_record.reason}; therapist-led alone: {led_alone.reason}"))
    listed = [x.id for x in store.list()]
    store.revoke("c1", 2000)
    after = play(ctl, device_factory(), clock_factory(), consents=store, now_ms=2001)
    res.append(("C13", "the person can list every programmed cue and revoke any of them; a revoked cue never runs",
                listed == ["c1", "c2"] and not after.started, f"listed {', '.join(listed)}; after revoking: {after.reason}"))
    return res


def report(results) -> str:
    lines = ["| Check | Requirement | Result | Measured |", "|---|---|---|---|"]
    for cid, req, ok, measured in sorted(results, key=lambda r: int(r[0][1:])):
        lines.append(f"| {cid} | {req} | {'PASS' if ok else 'FAIL'} | {measured} |")
    n = sum(r[2] for r in results)
    return "\n".join(lines) + f"\n\n{n}/{len(results)} checks passed."


def firmware_rig(consent: bool = False):
    """The real firmware core (firmware/rsos_core) in the host simulator, plus virtual audio and display."""
    from .devices import VirtualAudio, VirtualDisplay
    from .protocol import ProtocolDevice
    return [ProtocolDevice(consent=consent), VirtualAudio(), VirtualDisplay()]


if __name__ == "__main__":
    use_fw = "--firmware" in sys.argv
    r = run_suite(firmware_rig if use_fw else standard_rig)
    print(("Firmware core (RDP/1, host simulator) + virtual audio and display\n\n" if use_fw else "Virtual rig\n\n") + report(r))
    sys.exit(0 if all(x[2] for x in r) else 1)
