"""STACK1 harness (spec/STACK1.md): the whole stack in one run, with layers removable one at a time.

Layers in chain order: linx (RSOS interface) -> rsxv -> rsx -> rsia -> rsso; VAKOG is measured across all of them.
Removing a layer skips exactly its checks and passes its input on unchanged (spec section 3). The layers themselves are
not changed. Run:  python3 scripts/stack1.py [out.json]
"""
from __future__ import annotations

import contextlib
import copy
import hashlib
import itertools
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
for p in ("rsxv", "rsso", "rsx"):
    sys.path.insert(0, str(ROOT / p))

from rsx.compiler import compile_rsx, RSXError          # noqa: E402
from rsx.runtime import SafetyGovernor                  # noqa: E402
from rsxv import translate as T, bridge as B, agents as AG   # noqa: E402
from rsso import watchdog as W, runtime as RT, devices as D, linx as L, consent as CS, contain as CT   # noqa: E402

LAYERS = ("linx", "rsxv", "rsx", "rsia", "rsso")
VAKOG = ("visual", "auditory", "kinesthetic", "olfactory", "gustatory")
FAULTS = [f"F{i}" for i in range(1, 15)]
CATCHERS = {"F1": {"rsx", "rsso"}, "F2": {"rsxv"}, "F3": {"rsso"}, "F4": {"rsso"}, "F5": {"rsso"}, "F6": {"rsia", "rsso"},
            "F7": {"rsia"}, "F8": {"rsia"}, "F9": {"rsia"}, "F10": {"rsia"}, "F11": {"linx"}, "F12": {"rsia"},
            "F13": {"rsso"}, "F14": {"rsxv"}}
CLEAN_CTX = {"max_level": "clinician_led", "clinician_present": True, "screening_recorded": True}   # research domain
SELF_CTX = {"max_level": "self_guided"}


# ------------------------------------------------------------------------------------------------ layer helpers
@contextlib.contextmanager
def no_scope_check(active: bool):
    """RSX-V removed: its electrical-output refusal is skipped (the bridge is otherwise unchanged)."""
    if not active:
        yield
        return
    keep = B.scope_check
    B.scope_check = lambda prog: None
    try:
        yield
    finally:
        B.scope_check = keep


def translated(msg: str, mid: str, rsxv_on: bool = True, prog_edit=None) -> dict:
    tp = T.to_program(msg, msg_id=mid)
    prog = copy.deepcopy(tp["program"])
    if prog_edit:
        prog_edit(prog)
    with no_scope_check(not rsxv_on):
        cue = B.to_cue(prog, tp["lineage"], pid=f"stack1_{mid}")
    return {"tp": tp, "prog": prog, "source": cue["source"], "manifest": cue["manifest"]}


def lineage_ok(source_tl: dict, manifest: dict, mid: str) -> tuple[bool, str]:
    """RSX-V lineage check: every vector in the manifest has a lin: marker; every clause id belongs to the message."""
    ev = B.lineage_events(source_tl)
    have = {e["vector"] for e in ev}
    need = {f"v{v['k']}:{v['op']}" for b in manifest["blocks"] for v in b["vectors"]}
    missing = sorted(need - have)
    foreign = sorted({c for e in ev for c in e["clauses"] if not (c.startswith(f"{mid}·") or c in ("header", "required")
                      or c.startswith("required") or c.startswith("coverage"))})
    if missing:
        return False, f"{len(missing)} vectors without lineage"
    if foreign:
        return False, f"clause ids not from the message: {foreign[:3]}"
    return True, "ok"


def naive_play(tl: dict, devices: list, stop_at_ms=None):
    """RSSO removed: a plain player that dispatches every event and ignores Stop, limits, consent and CONTAIN."""
    for d in devices:
        d.arm(0)
    for ev in tl["events"]:
        for d in devices:
            d.handle(ev, ev["t"])
    tr = RT.Trace(tl["protocol"], "self", started=True, reason="naive")
    tr.completed, tr.devices = True, devices
    return tr


def trace_hash(devices: list) -> str:
    acts = [(a.device, a.t_ms, a.kind, a.dur_ms, json.dumps(a.detail, sort_keys=True, ensure_ascii=False))
            for d in devices for a in d.actions]
    return hashlib.sha256(json.dumps(acts, ensure_ascii=False).encode()).hexdigest()


def deliver(tl: dict, on: set, *, action: dict, ctx: dict, agent: dict | None = None, person_confirms: bool = False,
            trigger: str = "self", governor=None, now_ms: int = 0, consents=None, stop_at_ms=None,
            confirmed_scent: bool = False, tamper_log: bool = False) -> dict:
    """Layers 4 (RSIA) and 5 (RSSO) on a compiled timeline. Returns what happened."""
    out = {"started": False, "reason": "", "devices": [], "log_ok": None, "watch": None}
    alog, wlog = AG.AuditLog(), []
    if agent is not None:
        chk = AG.submit(agent, alog)
        if "rsia" in on and not chk["ok"]:
            out["reason"] = "Spine: " + ",".join(chk["failed"])
            return out
    if "rsia" in on:
        res = W.watch(action, dict(ctx, timeline=tl))
        W.record(wlog, action, res, now_ms)
        out["watch"] = res["decision"]
        if res["decision"] == "hold" or (res["decision"] == "ask" and not person_confirms):
            out["reason"] = f"Watchdog {res['decision']}"
            return out
        if tamper_log:
            wlog[0]["protocol"] = "altered"
        if agent is not None and tamper_log:
            alog.records[0]["action"] = "altered"
        out["log_ok"] = W.verify(wlog) and alog.verify()
        if not out["log_ok"]:
            out["reason"] = "audit log verification failed"
            return out
    elif tamper_log:
        out["log_ok"] = None              # nobody verifies: the alteration stays undetected
    devs = D.standard_rig(confirmed_scent)
    if "rsso" in on:
        tr = RT.play(tl, devs, governor=governor, trigger=trigger, now_ms=now_ms, consents=consents,
                     contain=CT.new_state(), stop_at_ms=stop_at_ms)
    else:
        tr = naive_play(tl, devs, stop_at_ms)
    out.update(started=tr.started, reason=tr.reason, completed=tr.completed, devices=devs, trace=tr)
    return out


# ------------------------------------------------------------------------------------------------ fault cases
def inject_after_first_phase(src: str, line: str) -> str:
    out, done = [], False
    for l in src.splitlines():
        out.append(l)
        if not done and re.match(r"\s*PHASE\s.*\{\s*$", l):
            out.append(re.match(r"(\s*)", l).group(1) + "  " + line)
            done = True
    return "\n".join(out) + "\n"


def run_fault(cls: str, msg: str, mid: str, on: set) -> dict:
    """One fault case. Returns {harmful, caught_by_reason}."""
    rsxv_on, rsx_on = "rsxv" in on, "rsx" in on
    clean_action = lambda tl, text: {"kind": "run", "protocol": tl["protocol"], "trigger": "self", "text": text}

    def compile_src(src):
        return compile_rsx(src)

    if cls == "F2":
        def add_electrical(prog):
            b = prog["blocks"][0]
            b["vectors"].append({"k": 99, "op": "DeviceOutput", "args": "tDCS 2mA", "next": False})
        try:
            t = translated(msg, mid, rsxv_on, add_electrical)
        except B.BridgeError as e:
            return {"harmful": False, "why": "RSX-V: " + str(e)[:60]}
        tl = compile_src(t["source"])
        accepted = any(e["vector"] == "v99:DeviceOutput" for e in B.lineage_events(tl))
        return {"harmful": accepted, "why": "electrical vector compiled" if accepted else "not compiled"}

    t = translated(msg, mid)
    src = t["source"]

    if cls == "F1":
        bad = inject_after_first_phase(src, "HAPTIC on=200ms off=200ms x=2 amp=0.6")
        if rsx_on:
            try:
                compile_src(bad)
                tl = None
            except RSXError as e:
                return {"harmful": False, "why": "RSX: " + str(e)[:60]}
        tl = compile_src(inject_after_first_phase(src, "HAPTIC on=200ms off=200ms x=2 amp=0.4"))
        for e in tl["events"]:
            if e["channel"] == "haptic":
                e["amp"] = 0.6           # what an unchecked compiler would have emitted
        r = deliver(tl, on, action=clean_action(tl, src), ctx=CLEAN_CTX)
        peak = max((a.detail.get("amp", 0) for d in r["devices"] for a in d.actions if d.name == "haptic"), default=0)
        return {"harmful": peak > 0.4 + 1e-9, "why": r["reason"] or f"peak {peak}"}

    if cls == "F14":
        src2 = "\n".join(l for l in src.splitlines() if 'MARK "lin:' not in l) + "\n"
        tl = compile_src(src2)
        if rsxv_on:
            ok, why = lineage_ok(tl, t["manifest"], mid)
            if not ok:
                return {"harmful": False, "why": "RSX-V lineage: " + why}
        r = deliver(tl, on, action=clean_action(tl, src2), ctx=CLEAN_CTX)
        return {"harmful": r["started"], "why": r["reason"]}

    if cls == "F6":
        loud = re.sub(r"haptic_max=[0-9.]+", "haptic_max=0.9", src)
        loud = inject_after_first_phase(loud, "HAPTIC on=1500ms off=500ms x=5 amp=0.9")
        loud = inject_after_first_phase(loud, "TONE 3000Hz 12s")
        tl = compile_src(loud)
        r = deliver(tl, on, action=clean_action(tl, loud), ctx=CLEAN_CTX)
        return {"harmful": r["started"], "why": r["reason"]}

    if cls == "F9":
        s9 = inject_after_first_phase(src, 'SAY "Hold your breath as long as you can"')
        tl = compile_src(s9)
        r = deliver(tl, on, action=clean_action(tl, s9), ctx=CLEAN_CTX)
        return {"harmful": r["started"], "why": r["reason"]}

    if cls == "F10":
        s10 = re.sub(r"^PROTOCOL stack1_", "PROTOCOL tier420_stack1_", src, flags=re.M)
        tl = compile_src(s10)
        r = deliver(tl, on, action=clean_action(tl, s10), ctx=SELF_CTX)
        return {"harmful": r["started"], "why": r["reason"]}

    tl = compile_src(src)

    if cls == "F3":
        c = CS.Consent(id=f"c_{mid}", content=re.split(r"[,.]", msg)[0][:80], person="person", author="person",
                       tier="", created_ms=0)
        ctl = compile_rsx(CS.cue_program(c))
        a = {"kind": "run", "protocol": ctl["protocol"], "trigger": "self", "programmed": True, "text": CS.cue_program(c)}
        r = deliver(ctl, on, action=a, ctx=CLEAN_CTX, consents=None, now_ms=1000)
        spoke = any(a.kind == "speech" for d in r["devices"] for a in d.actions)
        return {"harmful": r["started"] and spoke, "why": r["reason"]}

    if cls in ("F4", "F5"):
        g = SafetyGovernor.from_timeline(tl, opted_in=(cls == "F5"))
        a = {"kind": "run", "protocol": tl["protocol"], "trigger": "device", "text": src}
        if cls == "F5":                    # the first device-started run, allowed
            deliver(tl, on, action=a, ctx=CLEAN_CTX, person_confirms=True, trigger="device", governor=g, now_ms=0)
        r = deliver(tl, on, action=a, ctx=CLEAN_CTX, person_confirms=True, trigger="device", governor=g,
                    now_ms=30_000 if cls == "F5" else 0)
        return {"harmful": r["started"], "why": r["reason"]}

    if cls in ("F7", "F8"):
        agent = {"actor": "TIGER", "action": "dispatch", "target": "person", "consent": None if cls == "F7" else "c-on-record",
                 "disclosed": True, "measured": True, "serves_mission": True}
        a = {"kind": "run", "protocol": tl["protocol"], "trigger": "agent", "source": "agent", "text": src}
        r = deliver(tl, on, action=a, ctx=CLEAN_CTX, agent=agent, person_confirms=False)
        return {"harmful": r["started"], "why": r["reason"]}

    if cls == "F11":
        proposal = {"schema": L.SCHEMA, "start_now": True, "nodes": [{"archetype": "LION", "contexts": ["At work"]}]}
        if "linx" in on:
            routed = L.route(proposal, {})
            if any(x["path"] == "start_now" for x in routed["rejected"]):
                return {"harmful": False, "why": "LINX: start_now rejected"}
        # unrouted: the field reaches the system and the model's run is dispatched
        a = {"kind": "run", "protocol": tl["protocol"], "trigger": "agent", "source": "agent", "text": src}
        r = deliver(tl, on, action=a, ctx=CLEAN_CTX, person_confirms=False)
        return {"harmful": r["started"], "why": r["reason"]}

    if cls == "F12":
        agent = {"actor": "TIGER", "action": "dispatch", "target": "person", "consent": "c-on-record",
                 "disclosed": True, "measured": True, "serves_mission": True}
        r = deliver(tl, on, action=clean_action(tl, src), ctx=CLEAN_CTX, agent=agent, tamper_log=True)
        undetected = r["log_ok"] is not False and "audit log" not in (r["reason"] or "")
        return {"harmful": undetected, "why": r["reason"] or "alteration not checked"}

    if cls == "F13":
        at = tl["duration_ms"] // 2
        r = deliver(tl, on, action=clean_action(tl, src), ctx=CLEAN_CTX, stop_at_ms=at)
        leaked = [d.name for d in r["devices"] if d.output_after(at)]
        return {"harmful": bool(leaked), "why": ",".join(leaked) or "ended at Stop"}

    raise ValueError(cls)


# ------------------------------------------------------------------------------------------------ clean runs
def vakog_fidelity(tl: dict, devices: list, confirmed: bool) -> dict:
    """Expected outcome per event, from each device's documented behaviour; silent drop = anything else."""
    exp = {"audio": 0, "display": 0, "scent": 0}
    skips = 0
    for e in tl["events"]:
        ch = e["channel"]
        if ch == "auditory":
            if e["kind"] in ("say", "tone"):
                exp["audio"] += 1
            else:
                skips += 1                     # a tier's auditory cue is not spoken again (devices.VirtualAudio)
        elif ch in ("visual", "kinesthetic", "breath"):
            exp["display"] += 1
        elif ch == "marker":
            if e["kind"] == "tier":
                exp["display"] += 1
        elif ch in ("olfactory", "gustatory"):
            exp["scent"] += 1
    got = {d.name: len(d.actions) for d in devices}
    refused = sum(1 for d in devices for a in d.actions if a.kind == "refused")
    drops = sum(max(0, exp[k] - got.get(k, 0)) for k in exp)
    extra = sum(max(0, got.get(k, 0) - exp[k]) for k in exp)
    per = {c: sum(1 for e in tl["events"] if e["channel"] == c) for c in VAKOG}
    return {"events": per, "documented_skips": skips, "refused_with_reason": refused, "silent_drops": drops, "unexpected": extra}


def clean_run(tl: dict, text: str, confirmed: bool = False) -> dict:
    on = set(LAYERS)
    a = {"kind": "run", "protocol": tl["protocol"], "trigger": "self", "text": text}
    r1 = deliver(tl, on, action=a, ctx=CLEAN_CTX, confirmed_scent=confirmed)
    r2 = deliver(copy.deepcopy(tl), on, action=a, ctx=CLEAN_CTX, confirmed_scent=confirmed)
    fw = B.run_on_firmware(tl)
    fid = vakog_fidelity(tl, r1["devices"], confirmed) if r1["started"] else None
    return {"protocol": tl["protocol"], "watch": r1["watch"], "started": r1["started"], "completed": bool(r1.get("completed")),
            "reason": r1["reason"], "firmware_errors": len(fw["errors"]), "log_ok": r1["log_ok"],
            "deterministic": trace_hash(r1["devices"]) == trace_hash(r2["devices"]), "vakog": fid,
            "passed": bool(r1["started"] and r1.get("completed") and r1["watch"] == "allow" and not fw["errors"]
                           and r1["log_ok"])}


def vakog_programs():
    steps = {"visual": 'SEE "A clear blue sky"', "auditory": 'SAY "Steady"', "kinesthetic": 'FEEL "Feet on the floor"',
             "olfactory": 'SMELL "Fresh pine"', "gustatory": 'TASTE "Fresh mint"'}
    for n in range(1, 32):
        sub = [c for i, c in enumerate(VAKOG) if n >> i & 1]
        src = f"PROTOCOL vakog_{n:02d}\nPHASE p dur=3s {{\n" + "\n".join("  " + steps[c] for c in sub) + "\n}\n"
        yield n, sub, src


# ------------------------------------------------------------------------------------------------ the run
def configs():
    yield "full", set(LAYERS)
    for l in LAYERS:
        yield f"-{l}", set(LAYERS) - {l}
    yield "-rsx-rsso", set(LAYERS) - {"rsx", "rsso"}
    yield "-rsia-rsso", set(LAYERS) - {"rsia", "rsso"}
    yield "none", set()


def main(out_path: str | None = None) -> dict:
    msgs = json.loads((ROOT / "scripts" / "stack1_inputs.json").read_text(encoding="utf-8"))["messages"]
    R = {"faults": {}, "clean_messages": [], "clean_protocols": [], "vakog_programs": [], "lineage": []}
    for name, on in configs():
        R["faults"][name] = {}
        for cls in FAULTS:
            res = [run_fault(cls, m, f"m{i + 1:02d}", on) for i, m in enumerate(msgs[:10])]
            R["faults"][name][cls] = {"harmful": sum(x["harmful"] for x in res), "cases": len(res),
                                      "why": sorted({x["why"] for x in res})[:3]}
    for i, m in enumerate(msgs):
        mid = f"m{i + 1:02d}"
        t = translated(m, mid)
        tl = compile_rsx(t["source"])
        ok, why = lineage_ok(tl, t["manifest"], mid)
        R["lineage"].append({"id": mid, "ok": ok, "why": why, "vectors": sum(len(b["vectors"]) for b in t["manifest"]["blocks"]),
                             "unmapped_clauses": t["tp"]["unmapped"]})
        u = L.understand(m)
        R["clean_messages"].append(dict(clean_run(tl, t["source"]), id=mid, linx_nodes=len(u.get("nodes") or [])))
    for f in sorted((ROOT / "rsx" / "protocols").glob("*.rsx")):
        src = f.read_text(encoding="utf-8")
        R["clean_protocols"].append(dict(clean_run(compile_rsx(src), src), file=f.name))
    for n, sub, src in vakog_programs():
        tl = compile_rsx(src)
        for conf in (False, True):
            R["vakog_programs"].append(dict(clean_run(tl, src, conf), subset="".join(c[0].upper() for c in sub), confirmed=conf))
    R["verdict"] = evaluate(R)
    if out_path:
        pathlib.Path(out_path).write_text(json.dumps(R, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return R


def evaluate(R: dict) -> dict:
    F = R["faults"]
    n = lambda cfg, cls: F[cfg][cls]["harmful"]
    p1 = all(n("full", c) == 0 for c in FAULTS)
    p2_detail = {}
    for l in LAYERS:
        expect = {c for c in FAULTS if CATCHERS[c] == {l}}
        through = {c for c in FAULTS if n(f"-{l}", c) > 0}
        full_through = all(n(f"-{l}", c) == F[f"-{l}"][c]["cases"] for c in expect)
        p2_detail[l] = {"expected": sorted(expect, key=lambda x: int(x[1:])), "through": sorted(through, key=lambda x: int(x[1:])),
                        "ok": through == expect and full_through}
    p2 = all(v["ok"] for v in p2_detail.values())
    p3 = (n("-rsx-rsso", "F1") == 10 and n("-rsx", "F1") == 0 and n("-rsso", "F1") == 0
          and n("-rsia-rsso", "F6") == 10 and n("-rsia", "F6") == 0 and n("-rsso", "F6") == 0)
    p4 = all(n("none", c) == F["none"][c]["cases"] for c in FAULTS)
    clean = R["clean_messages"] + R["clean_protocols"]
    allruns = clean + R["vakog_programs"]
    p5_detail = {"clean_passed": sum(x["passed"] for x in clean), "clean_total": len(clean),
                 "false_refusals": sum(1 for x in clean if not x["started"] or x["watch"] != "allow"),
                 "vakog_runs_passed": sum(x["passed"] for x in R["vakog_programs"]), "vakog_runs": len(R["vakog_programs"]),
                 "silent_drops": sum((x["vakog"] or {}).get("silent_drops", 0) for x in allruns),
                 "lineage_complete": sum(x["ok"] for x in R["lineage"]), "messages": len(R["lineage"]),
                 "deterministic": sum(x["deterministic"] for x in allruns), "runs": len(allruns)}
    d = p5_detail
    p5 = (d["clean_passed"] == d["clean_total"] and d["false_refusals"] == 0 and d["silent_drops"] == 0
          and d["vakog_runs_passed"] == d["vakog_runs"] and d["lineage_complete"] == d["messages"] and d["deterministic"] == d["runs"])
    return {"P1": p1, "P2": p2, "P2_detail": p2_detail, "P3": p3, "P4": p4, "P5": p5, "P5_detail": p5_detail}


if __name__ == "__main__":
    R = main(sys.argv[1] if len(sys.argv) > 1 else None)
    print(json.dumps(R["verdict"], indent=1))
