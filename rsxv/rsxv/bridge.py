"""Bridge: an RSX-V command -> an RSX cue program (the repository's cue language) -> timeline -> device.

The cue program is what the existing player, the Python/JavaScript compilers and the device protocol
already understand, so RSX-V inherits their safety limits (haptic_max is a compile error) and runs in
the live editor. Closed-loop control stays in the RSX-V runtime: each RSX-V block becomes one breath
*cycle* of cue phases inside REPEAT n, and a manifest tells the runtime which cue phases belong to
which block, so it can stop a block early (UNTIL) or skip it (IF).

Lineage: every vector writes a MARK "lin:<clause ids>|v<k>:<Operator>" at the start of its cues, so
the compiled timeline carries the path message clause -> operator -> cue.

Scope rule: no electrical stimulation. Any operator or argument naming electrical, charge-based,
tDCS, tACS, TENS, EMS or galvanic output is refused.
"""
from __future__ import annotations
import json
import math
import re
import sys
from . import ops as O

import pathlib
_ROOT = pathlib.Path(__file__).resolve().parents[2]
REPO_RSX = str(_ROOT / "rsx")
REPO_RSSO = str(_ROOT / "rsso")
CYCLE_S = 10                     # one inhale (4 s) + one exhale (6 s)
ELECTRICAL = re.compile(r"electric|charge|tdcs|tacs|tens\b|\bems\b|galvan|current\s*stim", re.I)

TIERS = {   # neutral default bundles; a person's own tier (from an intake) replaces these
    "LION": ("A warm golden light", "I lead, calmly", "Steady strength in the chest"),
    "DRAGON": ("Deep red light turning to gold", "I hold the storm and breathe", "Slow heat rising along the spine"),
    "EAGLE": ("Clear sky seen from above", "I see the whole path", "Lightness behind the eyes"),
    "BEAR": ("A dark, quiet forest", "I hold. I carry.", "Heavy, grounded feet"),
    "RAVEN": ("Moonlit silver edges", "I notice what others miss", "Alert, still face"),
    "TIGER": ("Orange stripes in motion", "Now.", "Spring in the legs"),
    "LEOPARD": ("Spotted shadow between trees", "I adapt and move", "Loose, ready shoulders"),
}

# operator -> list of cue steps; {A} archetype, {B} second archetype, {S} symbol, {T} time horizon
CUES = {
    "BreathOverride": ["HAPTIC on=400ms off=600ms x=4 amp=0.3", 'FEEL "Breathe in slowly, out longer"'],
    "BreathSync": ['FEEL "Let the breath find its own slow rhythm"'],
    "BreathLock": ['FEEL "Keep this breath steady"'],
    "PostureShift": ['GESTURE "Spine tall, shoulders soft"'],
    "EmotionalLock": ['FEEL "Let calm settle in the chest"'],
    "StateReset": ['FEEL "Return to neutral"'],
    "MemoryRecall": ["ACTIVATE {A}"],
    "AssociativeExpand": ['SEE "Let the image open into everything it connects to"'],
    "CompressionRun": ['SEE "Fold it all into one symbol"'],
    "ArchetypeMerge": ["ACTIVATE {A}", "ACTIVATE {B}", 'SEE "The two become one form"'],
    "IdentityRebuild": ['SAY "This is who I am becoming"'],
    "IdentityShift": ['SAY "I step into this version of me"'],
    "SelfRevise": ['SAY "I choose what to keep"'],
    "FutureProjection": ["FOR FUTURE {", '  SEE "$future"', "  WAIT 2s", "}"],
    "FutureSelfLink": ['SEE "Your future self nods back at you"'],
    "FutureAnchor": ['FEEL "Set this as the place you return to"'],
    "MetaObserve": ['SEE "Watch yourself from a calm distance"'],
    "IntegrateAll": ['FEEL "Let every part settle into one"'],
    "RecursiveLawApply": ['SAY "What worked, I keep"'],
    "SymbolicLawApply": ['SAY "The pattern holds"'],
    "SymbolicEcho": ['SAY "Again, softer"'],
    "EchoLock": [], "EchoSeal": [], "EchoPropagationStop": ['FEEL "Let it end here"'],
    "MemoryUpdate": [], "MemoryPurge": [],
    "EthicsContain": [], "SymbolicDriftCheck": [], "DriftLock": [], "NullSafe": [],
    "DeviceOutput": ['SEE "{S}"'],
    "DeviceTrigger": ["HAPTIC on=200ms off=200ms x=3 amp=0.3"],
    "ARSymbolOutput": ['SEE "{S}"'],
    "SymbolicCommandExport": [],
}


class BridgeError(Exception):
    pass


def _q(s):
    return s.replace('"', "'")


def _args(v, prog):
    a = v["args"] or ""
    A = (re.search(r"Archetype=(\w+)", a) or re.search(r"^(\w+)\+", a))
    A = (A.group(1) if A else (prog["archetype"] or "LION")).upper()
    B = re.search(r"\+(\w+)", a); B = B.group(1).upper() if B else A
    S = re.search(r"symbol=([^,)]+)", a); S = S.group(1).strip() if S else (prog["archetype"] or "lion").lower()
    T = re.search(r"(\d+\s*\w+)", a); T = T.group(1) if T else "3 years"
    T = re.sub(r"(\d+)\s*([A-Za-z]+)", r"\1 \2", T).lower()
    return A, B, S, T


def scope_check(prog):
    bad = [f"@Vector{v['k']}:{v['op']}({v['args']})" for b in prog["blocks"] for v in b["vectors"]
           if ELECTRICAL.search(v["op"]) or ELECTRICAL.search(v["args"] or "")]
    if bad:
        raise BridgeError("electrical stimulation is out of scope: " + ", ".join(bad))


def to_cue(prog: dict, lineage: dict | None = None, seconds: dict | None = None, pid: str = "rsxv") -> dict:
    """lineage: {operator name: [clause ids]}; seconds: {block name: seconds actually run} (else MAX)."""
    scope_check(prog)
    lineage = lineage or {}
    arches, futures = set(), []
    for b in prog["blocks"]:
        for v in b["vectors"]:
            A, B, S, T = _args(v, prog)
            if v["op"] in ("MemoryRecall", "ArchetypeMerge"):
                arches |= {A, B}
            if v["op"] == "FutureProjection":
                futures = [f"Your future self in {T}", "A real moment where you will need this"]
    if prog["archetype"]:
        arches.add(prog["archetype"].upper())
    L = [f'PROTOCOL {pid} "{_q(prog["intent"]["text"] or "RSX-V command")[:60]}"', "VERSION 1.0",
         "SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4", "BREATH inhale=4s exhale=6s", ""]
    for n, a in enumerate(sorted(arches), 1):
        V, Au, K = TIERS.get(a, (f"The {a.lower()} as light", f"I carry the {a.lower()}", "Steady breath"))
        L += [f"TIER {n} {a} {{", f'  V "{V}"', f'  A "{Au}"', f'  K "{K}"', "}"]
    if futures:
        L.append("FUTURES " + " | ".join(f'"{f}"' for f in futures))
    L.append("")
    manifest = {"pid": pid, "blocks": [], "cycle_s": CYCLE_S}
    for b in prog["blocks"]:
        name = re.sub(r"\W", "_", b["name"])
        secs = (seconds or {}).get(b["name"], b["max_s"] if b["kind"] == "PHASE" else (5 if b["kind"] == "GATE" else 20))
        reps = max(1, min(100, round(secs / CYCLE_S)))
        breath = any(O.OPS[v["op"]][0] in ("body", "affect") for v in b["vectors"])
        steps = []
        for v in b["vectors"]:
            A, B, S, T = _args(v, prog)
            ids = ",".join(lineage.get(v["op"], [])) or "-"
            steps.append(f'MARK "lin:{ids}|v{v["k"]}:{v["op"]}"')
            for c in CUES.get(v["op"], []):
                steps.append(c.replace("{A}", A).replace("{B}", B).replace("{S}", _q(S)).replace("{T}", T))
        phases = []
        if b["kind"] == "GATE":
            phases.append(f"PHASE {name} dur={max(1, int(secs))}s {{")
            phases += ["  " + s for s in steps] + ['  FEEL "Check in: are you ready to begin?"', "}"]
        elif breath:
            first = [s for s in steps]
            phases.append(f"  PHASE {name}_in breath=inhale {{")
            phases += ["    " + s for s in first] + ["  }"]
            phases += [f"  PHASE {name}_out breath=exhale {{", '    FEEL "Breathe out"', "  }"]
            phases = [f"REPEAT {reps} {{"] + phases + ["}"]
        else:
            phases.append(f"  PHASE {name} dur={CYCLE_S}s {{")
            phases += ["    " + s for s in steps] + ["  }"]
            phases = [f"REPEAT {reps} {{"] + phases + ["}"]
        L += phases
        manifest["blocks"].append({"name": b["name"], "kind": b["kind"], "cue_phases": [f"{name}_in", f"{name}_out"] if (breath and b["kind"] != "GATE") else [name],
                                   "repeats": reps if b["kind"] != "GATE" else 1, "until": b.get("until"), "if": b.get("if"),
                                   "vectors": [{"k": v["k"], "op": v["op"], "clauses": lineage.get(v["op"], [])} for v in b["vectors"]]})
    src = "\n".join(L) + "\n"
    src, manifest["haptic_budget"] = _fit_haptic_budget(src)
    return {"source": src, "manifest": manifest}


HAPTIC_BUDGET_MS = 18000      # 90% of CONTAIN's haptic_on_ms_per_run (20 s): vibration per run stays inside the envelope


def _fit_haptic_budget(src: str) -> tuple[str, dict]:
    """Thin the haptic pulses so that, at full dose, the total vibration of one run stays inside the envelope.
    Pulses are shortened first (not below 150 ms), then their count is reduced (not below 1)."""
    def total(s):
        tot, mult, stack = 0, 1, []
        for line in s.splitlines():
            t = line.strip()
            m = re.match(r"REPEAT (\d+) \{", t)
            if m:
                stack.append(int(m.group(1))); mult *= int(m.group(1)); continue
            if t == "}" and stack and not re.match(r"\s{4}", line):
                if line.startswith("}"):
                    mult //= stack.pop()
                continue
            m = re.match(r"HAPTIC on=(\d+)ms off=(\d+)ms x=(\d+) amp=", t)
            if m:
                tot += mult * int(m.group(1)) * int(m.group(3))
        return tot
    before = total(src)
    s = src
    for on in (400, 300, 250, 200, 150):
        if total(s) <= HAPTIC_BUDGET_MS:
            break
        s = re.sub(r"HAPTIC on=(\d+)ms", lambda m: f"HAPTIC on={min(int(m.group(1)), on)}ms", s)
    for x in (3, 2, 1):
        if total(s) <= HAPTIC_BUDGET_MS:
            break
        s = re.sub(r"(HAPTIC on=\d+ms off=\d+ms) x=(\d+)", lambda m: f"{m.group(1)} x={min(int(m.group(2)), x)}", s)
    return s, {"planned_ms": before, "final_ms": total(s), "limit_ms": HAPTIC_BUDGET_MS}


def compile_cue(source: str) -> dict:
    if REPO_RSX not in sys.path:
        sys.path.insert(0, REPO_RSX)
    from rsx.compiler import compile_rsx
    return compile_rsx(source)


def device_lines(timeline: dict) -> list[str]:
    if REPO_RSSO not in sys.path:
        sys.path.insert(0, REPO_RSSO)
    from rsso.protocol import encode
    return encode(timeline)


def run_on_firmware(timeline: dict) -> dict:
    if REPO_RSSO not in sys.path:
        sys.path.insert(0, REPO_RSSO)
    from rsso.machines import fw_run
    lines = device_lines(timeline)
    out = fw_run(lines + ["START", f"TICK {timeline['duration_ms'] + 2000}", "STOP"])
    return {"lines": lines, "out": out, "errors": [x for x in out if x.startswith(("ERR", "REFUSED", "FAULT"))]}


def lineage_events(timeline: dict) -> list[dict]:
    """The MARK events that carry clause -> operator lineage, with their time in the timeline."""
    out = []
    for e in timeline["events"]:
        lab = e.get("label") or e.get("text") or ""
        if e["channel"] == "marker" and str(lab).startswith("lin:"):
            ids, op = lab[4:].split("|", 1)
            out.append({"t": e["t"], "clauses": [] if ids == "-" else ids.split(","), "vector": op})
    return out


def realized(prog: dict, R: dict, lineage: dict | None = None, pid: str = "rsxv_run") -> dict:
    """The cue program that actually ran: blocks in executed order (ELSE repeats, deferred blocks included),
    each with the seconds it really lasted; skipped blocks left out. Returns cue source, timeline,
    firmware result and the lineage events."""
    by = {b["name"]: b for b in prog["blocks"]}
    blocks = []
    for i, rec in enumerate(R["blocks"]):
        if not rec.get("ran", True) or not rec.get("vectors"):
            continue
        base = by.get(rec["name"].rstrip("*+")) or by.get(rec["name"].rstrip("*").rstrip("+"))
        if base is None:
            continue
        vecs = [v for v in base["vectors"] if v["op"] in rec["vectors"]]
        if rec["name"].endswith("+"):
            vecs = [v for b in prog["blocks"] for v in b["vectors"] if v["op"] in rec["vectors"]]
        blocks.append({**base, "name": f"{re.sub(r'[^A-Za-z0-9_]', '_', rec['name'])}_{i}", "vectors": vecs, "max_s": max(1, rec.get("seconds", 1))})
    p2 = {**prog, "blocks": blocks}
    cue = to_cue(p2, lineage=lineage, seconds={b["name"]: b["max_s"] for b in blocks}, pid=pid)
    tl = compile_cue(cue["source"])
    return {"cue": cue, "timeline": tl, "firmware": run_on_firmware(tl), "lineage": lineage_events(tl)}
