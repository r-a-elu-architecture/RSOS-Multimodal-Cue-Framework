"""RSX-V runtime: laws, gate, closed-loop phases, NullSafe, per-vector audit,
firmware lines, and the NEXT command built from the measured result."""
from __future__ import annotations
import copy
import math
import random
import sys
from . import ops as O
from . import lang as Lg
from . import sim as S

GHOST_RUNS = 30
GHOST_MAX_STOP = 0.30
STOP_RISE = 2.5          # NullSafe when distress rises this much above baseline
STOP_ABS = 9.0
UNTIL_MIN_S = 10
RESCUE_RISE = 1.8        # Contingency: rescue before NullSafe
MAX_RESCUES = 2
TEMPORAL_FLOOR = 0.7
RESCUE_OPS = {"SHIELD": ["StateReset", "BreathLock", "EmotionalLock"],
              "ANCHOR_MAX": ["BreathOverride", "PostureShift", "DeviceTrigger"]}


def rescue(prog, body, R, snap, phase):
    """Contingency archetypes: pull back toward baseline without wiping memory (layers are kept)."""
    used = [x["archetype"] for x in R["rescues"]]
    order = [a for a in ("SHIELD", "ANCHOR_MAX", "MIRROR_RESET") if a in prog["rescue"] and a not in used]
    if not order:
        return
    a = order[0]
    before = body.s["distress"]
    if a == "MIRROR_RESET":
        body.s["drift"] = snap["drift"]
        for _ in range(15):
            body.step(["StateReset"])
    else:
        for _ in range(30):
            body.step(RESCUE_OPS[a])
    R["rescues"].append({"archetype": a, "phase": phase, "t": body.t, "distress_before": round(before, 2), "distress_after": round(body.s["distress"], 2)})
    R["log"].append(f"{body.t}s Contingency {{{a}}} in {phase}: distress {before:.1f} → {body.s['distress']:.1f}")


def temporal_best(history, hour):
    """Mean session result (CSI) per hour of day from earlier sessions: (best hour, mean, n), (mean here, n here)."""
    by = {}
    for h in history:
        if h.get("hour") is None or h["status"] == "refused" or h.get("csi") is None:
            continue
        by.setdefault(h["hour"], []).append(h["csi"])
    if not by:
        return None, None
    m = {k: sum(v) / len(v) for k, v in by.items()}
    bh = max(m, key=lambda k: (m[k], len(by[k])))
    here = (m[hour], len(by[hour])) if hour in by else None
    return (bh, m[bh], len(by[bh])), here


def _holds(cond, read, base):
    """read may carry layer activations C1..C11 (estimated from the senses in real use)."""
    if not cond:
        return True
    for conj in cond:
        ok = True
        for t in conj:
            v = read[t["var"]] - (base[t["var"]] if t["delta"] else 0)
            ok &= {"<=": v <= t["value"], ">=": v >= t["value"], "<": v < t["value"], ">": v > t["value"]}[t["op"]]
        if ok:
            return True
    return False


def _split_conflicts(vectors):
    """InteractionMatrix: keep the higher-priority member of each conflicting pair, defer the other."""
    keep, later = list(vectors), []
    for pair in O.CONFLICTS:
        inb = [v for v in keep if v["op"] in pair]
        if len({v["op"] for v in inb}) == 2:
            inb.sort(key=lambda v: (O.PRIORITY[O.OPS[v["op"]][0]], v["k"]))
            keep.remove(inb[1]); later.append(inb[1])
    return keep, later


def _device_lines(v, t_ms, dur_ms, arche):
    tpl = O.OPS[v["op"]][4]
    a = (v["args"] or "").upper()
    img = (arche or "lion").lower()
    if "symbol=" in v["args"]:
        img = v["args"].split("symbol=")[1].split(",")[0].strip().lower() or img
    if tpl == "breath":
        n = max(1, dur_ms // 10000)
        return [f"HF {t_ms} 4000 6000 {n} 0.3 170 0 chest"]
    if tpl == "posture":
        return [f"HF {t_ms} 300 200 2 0.4 170 0 upper_back"]
    if tpl == "warm":
        return [f"T {t_ms} {min(dur_ms, 120000)} 1"]
    if tpl == "image":
        return [f"D {t_ms} {min(dur_ms, 8000)} {img}"]
    if tpl == "device":
        if "EEG" in a:
            return []                       # EEG is a sensor in RSX-V (SENSE EEG), not an output
        if "VIBRATION" in a:
            return [f"HF {t_ms} 200 0 1 0.4 170 0 wrist_left"]
        return [f"D {t_ms} {min(dur_ms, 8000)} {img}"]
    return []


def run(prog: dict, p: dict, ctx: dict | None = None) -> dict:
    ctx = dict(ctx or {})
    rng = random.Random(ctx.get("seed", 1))
    model = ctx.get("model", S.FULL)
    body = S.Body(p, rng, model, sham=ctx.get("sham", False))
    body.hf = S.hour_factor(p, ctx.get("hour"))
    base = body.read()
    base.update({c: 0.0 for c in O.LAYERS})
    base_true = dict(body.s)
    laws = set(prog["laws"])
    R = {"person": p["id"], "status": "done", "log": [], "blocks": [], "vectors": {}, "device_lines": [],
         "stopped": None, "ghost": None, "base": {k: round(v, 3) for k, v in base_true.items()}}

    def stop(why):
        R["status"] = "stopped"; R["stopped"] = {"t": body.t, "why": why}
        R["log"].append(f"{body.t}s NullSafe: {why}; all output halted, state locked")

    # ---- laws before anything runs
    if "ChronoGate" in laws and prog["window"] and "now_min" in ctx:
        a, b = prog["window"]
        if not (a <= ctx["now_min"] <= b):
            R["status"] = "refused"; R["log"].append("ChronoGate: outside the allowed window"); return _finish(R, prog, body, base_true)
    if "ConsentStack" in laws:
        need = ["subject", "operator"] + (["auditor"] if prog["tier"] >= 8 or prog["mode"] == "OVERRIDE" else [])
        miss = [k for k in need if k not in ctx.get("consent", ())]
        if miss:
            R["status"] = "refused"; R["log"].append(f"ConsentStack: missing {', '.join(miss)}"); return _finish(R, prog, body, base_true)
    if "TemporalSymmetry" in laws and ctx.get("history") and ctx.get("hour") is not None and not ctx.get("override_time"):
        best, here = temporal_best(ctx["history"], ctx["hour"])
        if best and here is not None and here[1] >= 2 and best[2] >= 2 and best[0] != ctx["hour"] and here[0] < TEMPORAL_FLOOR * best[1]:
            R["status"] = "refused"; R["reschedule_to"] = best[0]
            R["log"].append(f"TemporalSymmetry: mean result at {ctx['hour']}:00 is {here[0]:.2f} against {best[1]:.2f} at {best[0]}:00; reschedule to {best[0]}:00")
            return _finish(R, prog, body, base_true)
    if "GhostPass" in laws and not ctx.get("ghost"):
        g = ghost(prog, p, ctx)
        R["ghost"] = g
        if g["p_stop"] > GHOST_MAX_STOP:
            R["status"] = "refused"; R["log"].append(f"GhostPass: predicted stop {g['p_stop']:.0%} > {GHOST_MAX_STOP:.0%}"); return _finish(R, prog, body, base_true)

    guarded = prog["nullsafe"] and not prog["legacy"]
    queue = [copy.deepcopy(b) for b in prog["blocks"]]
    while queue and R["status"] == "done":
        b = queue.pop(0)
        rec = {"name": b["name"], "kind": b["kind"], "start": body.t, "ran": True, "ended": "max", "vectors": [v["op"] for v in b["vectors"]]}
        if b["kind"] == "PHASE" and b["if"] and not _holds(b["if"], _sense(body), base) and b.get("else") and b.get("_retries", 0) < 2:
            back = next((x for x in prog["blocks"] if x["name"] == b["else"]), None)
            if back is not None:
                R["log"].append(f"{body.t}s {b['name']}: IF false, ELSE repeats {b['else']}")
                queue.insert(0, {**b, "_retries": b.get("_retries", 0) + 1})
                queue.insert(0, {**copy.deepcopy(back), "name": back["name"] + "*", "if": None, "else": None})
                continue
        if b["kind"] == "PHASE" and b["if"] and not _holds(b["if"], _sense(body), base):
            rec["ran"] = False; rec["ended"] = "skipped (IF false)"; R["blocks"].append(rec)
            R["log"].append(f"{body.t}s {b['name']} skipped: IF {Lg.cond_text(b['if'])} is false"); continue
        if b["kind"] == "GATE":
            if any(v["op"] == "EthicsContain" for v in b["vectors"]) and (base_true["distress"] >= 8.5):
                stop("EthicsContain: screening failed (distress at start ≥ 8.5)"); rec["ended"] = "refused"; R["blocks"].append(rec); break
        vecs = b["vectors"]
        if "InteractionMatrix" in laws:
            vecs, later = _split_conflicts(vecs)
            if later:
                queue.insert(0, {**b, "name": b["name"] + "+", "if": None, "max_s": max(20, b["max_s"] // 2), "vectors": later})
                R["log"].append(f"{body.t}s InteractionMatrix: deferred {', '.join(v['op'] for v in later)} out of {b['name']}")
                rec["vectors"] = [v["op"] for v in vecs]
        active = [v["op"] for v in vecs]
        dur = b["max_s"] if b["kind"] == "PHASE" else (5 if b["kind"] == "GATE" else 20)
        t0 = body.t
        rec["drift_start"] = body.s["drift"]
        snap = {"drift": body.s["drift"]}
        body_done = any(x["ran"] and x["kind"] == "PHASE" and any(O.OPS[o][0] in ("body", "affect") for o in x["vectors"]) for x in R["blocks"])
        for sec in range(dur):
            c = body.step(active)
            deep = [o for o in active if O.OPS[o][1] in O.DEEP]
            if deep:
                R["_deep"] = R.get("_deep", 0) + 1
                R["_deep_ready"] = R.get("_deep_ready", 0) + (body.s["arousal"] <= 0.6)
                R["_deep_after_body"] = R.get("_deep_after_body", 0) + (body_done or any(O.OPS[o][0] in ("body", "affect") for o in active))
            R["_rec_s"] = R.get("_rec_s", 0) + sum(1 for o in active if O.OPS[o][0] == "recursion")
            R["_content_s"] = R.get("_content_s", 0) + sum(1 for o in active if O.OPS[o][0] not in ("safety", "export"))
            for v in vecs:
                a = R["vectors"].setdefault(v["k"], {"op": v["op"], "block": b["name"], "seconds": 0, "agency": 0.0, "distress": 0.0,
                                                     "arousal": 0.0, "drift": 0.0, "layer": 0.0, "trace": []})
                d = c.get(v["op"], {})
                a["seconds"] += 1
                a["agency"] += d.get("agency", 0); a["distress"] += d.get("distress", 0); a["arousal"] += d.get("arousal", 0); a["drift"] += d.get("drift", 0)
                a["layer"] += sum(x for k, x in d.items() if k.startswith("layer"))
                a["trace"].append(d.get("agency", 0) - d.get("distress", 0))
            r = body.read()
            R["peak_rise"] = max(R.get("peak_rise", 0.0), r["distress"] - base_true["distress"])
            if ("Contingency" in laws and prog.get("rescue") and r["distress"] - base_true["distress"] >= RESCUE_RISE
                    and len(R.setdefault("rescues", [])) < MAX_RESCUES):
                rescue(prog, body, R, snap, b["name"]); r = body.read()
            if guarded and (r["distress"] - base_true["distress"] >= STOP_RISE or r["distress"] >= STOP_ABS):
                stop(f"distress {r['distress']:.1f} (start {base_true['distress']:.1f}) in {b['name']}"); rec["ended"] = "NullSafe"; break
            if b["until"] and sec + 1 >= max(UNTIL_MIN_S, b.get("min_s", 0)) and _holds(b["until"], _sense(body, r), base):
                rec["ended"] = "UNTIL met"; break
        rec["seconds"] = body.t - t0
        rec["drift_end"] = body.s["drift"]
        for v in vecs:
            for line in _device_lines(v, t0 * 1000, rec["seconds"] * 1000, prog["archetype"]):
                if line not in R["device_lines"]:
                    R["device_lines"].append(line)
        R["blocks"].append(rec)
        R["log"].append(f"{t0}s {b['name']}: {rec['seconds']} s, ended by {rec['ended']}")
    return _finish(R, prog, body, base_true)


def _sense(body, r=None):
    r = dict(r or body.read())
    r.update(body.layer)
    return r


def _corr(x, y):
    n = min(len(x), len(y))
    if n < 3:
        return 0.0
    x, y = x[:n], y[:n]
    mx, my = sum(x) / n, sum(y) / n
    sx = math.sqrt(sum((a - mx) ** 2 for a in x)); sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return 0.0 if sx < 1e-12 or sy < 1e-12 else sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def _finish(R, prog, body, base_true):
    s = body.s
    R["outcome"] = {"agency": round(s["agency"] - base_true["agency"], 3), "distress": round(s["distress"] - base_true["distress"], 3),
                    "arousal": round(s["arousal"] - base_true["arousal"], 3), "drift": round(s["drift"] - base_true["drift"], 3),
                    "seconds": body.t, "layers": {c: round(v, 3) for c, v in body.layer.items()}}
    R["outcome"]["peak_rise"] = round(R.get("peak_rise", 0.0), 3)
    from . import metrics as Mx
    R["metrics"] = Mx.run_metrics(R, body)
    R["outcome"]["coverage"] = sum(1 for v in body.layer.values() if v >= 0.3)
    end = body.read()
    R["goal_met"] = R["status"] == "done" and (_holds(prog["goal"], end, {**base_true, "hrv": end["hrv"], "alpha": end["alpha"]}) if prog["goal"] else None)
    # per-vector audit
    vs = R["vectors"]
    conflicts = []
    by_block = {}
    for k, a in vs.items():
        by_block.setdefault(a["block"], []).append(k)
    for blk, ks in by_block.items():
        for i in range(len(ks)):
            for j in range(i + 1, len(ks)):
                a, b = vs[ks[i]], vs[ks[j]]
                if frozenset({a["op"], b["op"]}) in O.CONFLICTS:
                    conflicts.append([a["op"], b["op"], blk])
    total = sum(len(b["vectors"]) for b in prog["blocks"])
    ran = len(vs)
    clean = ran - len({x for c in conflicts for x in c[:2]})
    benefit = {k: a["agency"] - a["distress"] for k, a in vs.items()}
    R["audit"] = {"MCI": round(clean / total, 3) if total else 0.0, "ran": ran, "planned": total,
                  "VEC": round(1 - len(conflicts) / max(1, ran), 3), "conflicts": conflicts,
                  "per_vector": [{"k": k, "op": a["op"], "block": a["block"], "seconds": a["seconds"], "agency": round(a["agency"], 3),
                                  "distress": round(a["distress"], 3), "drift": round(a["drift"], 3), "layer": round(a["layer"], 3), "benefit": round(benefit[k], 3)}
                                 for k, a in sorted(vs.items())]}
    for a in vs.values():
        a.pop("trace", None)
    return R


def ghost(prog, p, ctx):
    rng = random.Random(ctx.get("seed", 1) * 7919 + 13)
    stops, goals = 0, 0
    runs = ctx.get("ghost_runs", GHOST_RUNS)
    for i in range(runs):
        q = S.perturb(p, rng)
        r = run(prog, q, {**ctx, "ghost": True, "seed": rng.randrange(10 ** 9)})
        stops += r["status"] == "stopped"; goals += bool(r["goal_met"])
    return {"runs": runs, "p_stop": stops / runs, "p_goal": goals / runs}


def firmware_check(lines, root=None):
    """Run the device lines through the real firmware core (host simulator)."""
    import pathlib
    root = str(root or pathlib.Path(__file__).resolve().parents[2] / "rsso")
    if root not in sys.path:
        sys.path.insert(0, root)
    from rsso.machines import fw_run, _load
    ev = sorted(lines, key=lambda x: int(x.split()[1]))
    end = max([int(x.split()[1]) + int(x.split()[2]) for x in ev] + [1000])
    out = fw_run(_load(ev) + ["START", f"TICK {end + 1000}", "STOP"])
    return {"lines": ev, "out": out, "errors": [x for x in out if x.startswith(("ERR", "REFUSED", "CLAMPED", "FAULT"))]}


STAGES = [  # name, families, IF, ELSE, UNTIL, MIN, MAX
    ("settle", ("body", "affect"), None, None, "arousal<=0.4 AND distress<=-1", 45, 150),
    ("expand", ("memory", "symbol"), "arousal<=0.55", "settle", "C2>=0.5 AND C3>=0.5", 20, 90),
    ("rebuild", ("identity", "future", "device"), "arousal<=0.6 AND distress<=6", "settle", "C7>=0.5 AND C4>=0.5", 20, 120),
    ("integrate", ("recursion", "meta"), None, None, "C9>=0.4 AND C10>=0.4 AND C11>=0.4", 20, 90),
]


def stage(vectors):
    """Order a flat vector list into gate -> settle -> expand -> rebuild -> integrate -> close."""
    gate = [v for v in vectors if O.OPS[v["op"]][0] == "safety"]
    close_ops = {"MemoryUpdate", "EchoPropagationStop", "SymbolicCommandExport"}
    close = [v for v in vectors if v["op"] in close_ops]
    for v in close:
        if v["op"] == "SymbolicCommandExport":
            v["next"] = True
    blocks = [{"kind": "GATE", "name": "gate", "until": None, "if": None, "max_s": 15, "vectors": gate}]
    have = {"gate"}
    for name, fams, cif, els, until, mn, mx in STAGES:
        vs = [v for v in vectors if O.OPS[v["op"]][0] in fams and v["op"] not in close_ops and v not in gate]
        vs = [v for v in vs if not ("EEG" in (v["args"] or "").upper() and v["op"] in ("DeviceOutput", "DeviceTrigger"))]
        blocks.append({"kind": "PHASE", "name": name, "if": Lg.parse_cond(cif), "else": els if els in have else None,
                       "until": Lg.parse_cond(until), "min_s": mn, "max_s": mx, "vectors": vs})
        have.add(name)
    blocks = [b for b in blocks if b["vectors"] or b["name"] in ("gate", "expand", "integrate")]
    blocks.append({"kind": "CLOSE", "name": "close", "until": None, "if": None, "max_s": 30, "vectors": close})
    return blocks


def next_program(prog, R):
    """LSGPA step: build the successor command from this run's measurements."""
    n = copy.deepcopy(prog)
    n["legacy"] = False
    notes = []
    if not n["nullsafe"]:
        n["nullsafe"] = True; notes.append("added Vector 0 NullSafe")
    if prog["legacy"]:
        n["blocks"] = stage(n["blocks"][0]["vectors"]); notes.append("legacy single phase staged into gate → settle → expand → rebuild → integrate → close")
        n["laws"] = ["InteractionMatrix", "GhostPass", "ConsentStack"]; notes.append("laws added: InteractionMatrix, GhostPass, ConsentStack")
        if not n["goal"]:
            n["goal"] = Lg.parse_cond("agency>=+1 AND distress<=-1 AND drift<=+0"); notes.append("goal added")
        if not n["sense"]:
            n["sense"] = ["EEG", "HRV", "DISTRESS"]; notes.append("EEG moved from output to SENSE")
    elif not n["blocks"] or n["blocks"][0]["kind"] != "GATE":
        n["blocks"].insert(0, {"kind": "GATE", "name": "gate", "until": None, "if": None, "max_s": 15, "vectors": []})
    gate = n["blocks"][0]
    if "EthicsContain" not in [v["op"] for v in gate["vectors"]]:
        k = max([v["k"] for b in n["blocks"] for v in b["vectors"]] + [0]) + 1
        gate["vectors"].insert(0, {"k": k, "op": "EthicsContain", "args": "CONTAIN", "next": False}); notes.append("added EthicsContain to the GATE")
    pv = {x["k"]: x for x in R["audit"]["per_vector"]}
    ended = {b["name"]: b for b in R["blocks"]}
    used = {v["k"] for b in n["blocks"] for v in b["vectors"]}
    nk = max(used | {0}) + 1
    for b in n["blocks"]:
        e = ended.get(b["name"])
        if b["kind"] == "PHASE" and e and e["ended"] == "max" and b["until"]:
            b["max_s"] = min(180, int(b["max_s"] * 1.5)); notes.append(f"{b['name']}: UNTIL not reached, MAX raised to {b['max_s']}s")
        keep = []
        for v in b["vectors"]:
            x = pv.get(v["k"])
            fam = O.OPS[v["op"]][0]
            if x and fam not in ("safety", "export", "device") and x["seconds"] >= 10 and abs(x["benefit"]) < 0.02 and x["layer"] < 0.05 and abs(x["drift"]) < 0.02:
                notes.append(f"dropped {v['op']} (no measurable contribution)")
                continue
            keep.append(v)
        b["vectors"] = keep
    missing = [c for c in O.LAYERS if R["outcome"]["layers"].get(c, 0) < 0.3]
    add = {"C2": "AssociativeExpand", "C9": "MetaObserve", "C10": "SelfRevise", "C11": "IntegrateAll"}
    new = [c for c in missing if c in add and add[c] not in {v["op"] for b in n["blocks"] for v in b["vectors"]}]
    home = {"AssociativeExpand": "expand", "MetaObserve": "integrate", "SelfRevise": "integrate", "IntegrateAll": "integrate"}
    for c in new:
        op = add[c]
        blk = next((b for b in n["blocks"] if b["name"] == home[op]), None)
        if blk is None:
            close = next((i for i, b in enumerate(n["blocks"]) if b["kind"] == "CLOSE"), len(n["blocks"]))
            blk = {"kind": "PHASE", "name": home[op], "if": Lg.parse_cond("arousal<=0.55"), "until": None, "max_s": 45, "vectors": []}
            n["blocks"].insert(close, blk)
        if len(blk["vectors"]) < O.MAX_CONCURRENT:
            blk["vectors"].append({"k": nk, "op": op, "args": "", "next": False}); nk += 1
            notes.append(f"added {op} to {blk['name']} for uncovered layer {c}")
    n["blocks"] = [b for b in n["blocks"] if b["vectors"] or b["kind"] != "PHASE"]
    if R["stopped"]:
        for b in n["blocks"]:
            if b["kind"] == "PHASE" and not b["if"] and any(O.OPS[v["op"]][1] in O.DEEP for v in b["vectors"]):
                b["if"] = Lg.parse_cond("distress<=3"); notes.append(f"{b['name']}: gated on distress<=3 after a NullSafe stop")
    n["tier"] = n["tier"]
    txt = Lg.to_text(n)
    return {"text": txt, "notes": notes, "program": Lg.parse(txt)}
