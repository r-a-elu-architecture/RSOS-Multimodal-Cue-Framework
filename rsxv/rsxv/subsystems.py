"""RSX-V on the repository's real subsystems: CONTAIN, MEMSTACK and CM1 (rsso/).

CONTAIN   The gate asks rsso.contain.decide before anything runs. The command is compiled to its RSX cue
          timeline at full dose (every phase at MAX) and checked against the device safety envelope, the
          program's quarantine state and the escalation state. After each session, rsso.contain.review
          updates the state from the run log: a program that stops helping is quarantined, and repeated
          high distress pauses device offers.
MEMSTACK  MemoryUpdate(MEMSTACK) appends the session to the person's run log in the shared run-log format
          (rsx LOG_FIELDS) and keeps a checksummed rsso.memstack snapshot. MemoryRecall reads the tier's
          summary (bundle strength, distress drop, reflex criterion).
CM1       CompressionRun(CM1) compresses the run log to an rsso.cm1 signature, assigns the person to a
          response profile and returns where to start (kind of program, strongest sense).

The person's state lives in one dict, `world`, so it can move between sessions and devices:
{"contain": state, "runs": [run-log rows], "memstack": snapshot, "cm1": suggestion}.
"""
from __future__ import annotations
import functools
import sys
from . import bridge as B

if B.REPO_RSSO not in sys.path:
    sys.path.insert(0, B.REPO_RSSO)
from rsso import contain as C, memstack as MS, cm1 as CM   # noqa: E402

THERAPIST_MODES = {"THERAPIST", "THERA"}


def new_world() -> dict:
    return {"contain": C.new_state(), "runs": [], "memstack": MS.snapshot([]), "cm1": None, "srbai": []}


def protocol_id(prog: dict) -> str:
    return "rsxv_" + "_".join(x for x in [str(prog["tier"]), (prog["archetype"] or "").lower()] if x)


def full_dose_timeline(prog: dict) -> dict:
    return B.compile_cue(B.to_cue(prog, pid=protocol_id(prog))["source"])


def contain_gate(prog: dict, world: dict, now: float, ctx: dict | None = None) -> dict:
    ctx = ctx or {}
    action = {"kind": "run", "protocol": protocol_id(prog), "trigger": ctx.get("trigger", "self"),
              "therapist_led": (prog["mode"] or "").upper() in THERAPIST_MODES, "therapist_present": bool(ctx.get("therapist_present"))}
    return C.decide(action, world["contain"], full_dose_timeline(prog), now)


def run_row(prog: dict, R: dict, participant: str, ts: float) -> dict:
    """One row of the shared run log (rsx LOG_FIELDS) for an RSX-V session."""
    b, o = R["base"], R["outcome"]
    stopped = next((x["name"] for x in R["blocks"] if x.get("ended") == "NullSafe"), "")
    return {"timestamp": ts, "participant": participant, "protocol": protocol_id(prog), "trigger": "self",
            "trigger_channel": "", "trigger_note": "rsxv", "sud_before": round(b["distress"], 2),
            "sud_after": round(b["distress"] + o["distress"], 2), "agency_before": round(b["agency"], 2),
            "agency_after": round(b["agency"] + o["agency"], 2), "latency_s": "", "completed": 1 if R["status"] == "done" else 0,
            "stopped_at_phase": stopped, "tier": (prog["archetype"] or "").upper(), "voice": "none"}


@functools.lru_cache(maxsize=1)
def profiles() -> tuple:
    """CM1 response profiles, fitted once on the repository's synthetic population."""
    return tuple(CM.fit([CM.signature(p["runs"]) for p in CM.synthetic_population()], K=4))


def after_session(prog: dict, R: dict, world: dict, participant: str, ts: float) -> dict:
    """MemoryUpdate, CONTAIN review and CompressionRun after one session. Returns what changed."""
    ops = {v["op"] for b in prog["blocks"] for v in b["vectors"]}
    changes = {}
    if R["status"] in ("done", "stopped"):
        world["runs"].append(run_row(prog, R, participant, ts))
    if "MemoryUpdate" in ops:
        world["memstack"] = MS.snapshot(world["runs"], world.get("srbai"))
        changes["memstack"] = MS.summarize(world["runs"], world.get("srbai"))["tiers"].get((prog["archetype"] or "").upper())
    world["contain"], ch = C.review(world["contain"], world["runs"], now=ts)
    changes["contain"] = ch
    if "CompressionRun" in ops and len(world["runs"]) >= 3:
        sig = CM.signature(world["runs"])
        world["cm1"] = CM.suggest(sig, list(profiles()))
        changes["cm1"] = world["cm1"]["recommendations"]
    return changes


def recall(world: dict, archetype: str) -> dict | None:
    """What MemoryRecall(Archetype=X) reads: the tier's MEMSTACK summary."""
    runs, srbai = MS.restore(world["memstack"])
    return MS.summarize(runs, srbai)["tiers"].get(archetype.upper())
