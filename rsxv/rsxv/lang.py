"""RSX-V language: parse and validate.

    RSX-V TIER 8 :: {DRAGON} :: (OVERRIDE)
    INTENT "steady identity under pressure" <- V1 V8 V14
    GOAL agency>=+1 AND distress<=-2 AND drift<=+0
    SENSE EEG HRV DISTRESS
    LAWS InteractionMatrix ChronoGate GhostPass ConsentStack
    WINDOW 07:00-22:00
    @Vector0:NullSafe
    GATE
      @Vector7:EthicsContain(CONTAIN)
    PHASE settle UNTIL distress<=3 OR hrv>=+5 MAX 90s
      @Vector3:BreathOverride(6/min)
    PHASE rebuild IF distress<=3 MAX 60s
      @Vector1:IdentityRebuild
    CLOSE
      @Vector16:SymbolicCommandExport(RSX) -> NEXT

A value with an explicit sign (+5, -2) is a change from the person's baseline;
a plain value is an absolute level. Legacy RSX v1 commands (TIER n :: ... ::
@VectorK:Op ...) are accepted and become one open-loop phase.
"""
from __future__ import annotations
import re
from . import ops as O

VARS = {"arousal", "distress", "agency", "drift", "hrv", "alpha"} | {f"C{i}" for i in range(1, 12)}
SENSES = {"EEG", "HRV", "DISTRESS", "POSTURE"}
LAWS = {"InteractionMatrix", "ChronoGate", "GhostPass", "ConsentStack",
        "MultiSessionContinuity", "TemporalSymmetry", "Contingency", "ResonanceAudit"}
RESCUES = {"SHIELD", "ANCHOR_MAX", "MIRROR_RESET"}
VEC = re.compile(r"@Vector(\d+):(\w+)(?:\((.*?)\))?\s*(->\s*NEXT)?$")
TERM = re.compile(r"(\w+)\s*(<=|>=|<|>)\s*([+-]?)(\d+(?:\.\d+)?)$")


class RSXVError(Exception):
    pass


def parse_cond(text):
    """'a<=3 OR b>=+5 AND c<1' -> [[term,...], ...] (OR of ANDs)."""
    if not text:
        return None
    out = []
    for part in re.split(r"\s+OR\s+", text.strip()):
        conj = []
        for t in re.split(r"\s+AND\s+", part.strip()):
            m = TERM.match(t.replace(" ", ""))
            if not m or m.group(1) not in VARS:
                raise RSXVError(f"bad condition '{t}'")
            conj.append({"var": m.group(1), "op": m.group(2), "delta": bool(m.group(3)),
                         "value": float(m.group(3) + m.group(4)) if m.group(3) else float(m.group(4))})
        out.append(conj)
    return out


def cond_text(c):
    if not c:
        return ""
    def t(x):
        v = x["value"]; s = (("+" if v >= 0 else "") if x["delta"] else "") + (str(int(v)) if v == int(v) else str(v))
        return f"{x['var']}{x['op']}{s}"
    return " OR ".join(" AND ".join(t(x) for x in conj) for conj in c)


def _vector(tok):
    m = VEC.match(tok.strip())
    if not m:
        raise RSXVError(f"bad vector '{tok.strip()}'")
    k, op, args, nxt = int(m.group(1)), m.group(2), m.group(3) or "", bool(m.group(4))
    if op not in O.OPS:
        raise RSXVError(f"unknown operator {op}")
    return {"k": k, "op": op, "args": args, "next": nxt}


def _legacy(src):
    parts = [p.strip() for p in " ".join(src.split()).split("::") if p.strip()]
    head = parts[0].split()
    if len(head) != 2 or head[0] != "TIER":
        raise RSXVError("legacy command must start with TIER <n> ::")
    prog = new_program(int(head[1]))
    prog["legacy"] = True
    blk = {"kind": "PHASE", "name": "legacy", "until": None, "if": None, "max_s": 120, "vectors": []}
    for p in parts[1:]:
        if p.startswith("{"):
            prog["archetype"] = p.strip("{}")
        elif p.startswith("("):
            prog["mode"] = p.strip("()")
        else:
            blk["vectors"].append(_vector(p))
    prog["blocks"].append(blk)
    return prog


def new_program(tier=0):
    return {"version": "RSX-V", "tier": tier, "archetype": "", "mode": "", "intent": {"text": "", "vectors": []},
            "goal": None, "sense": [], "laws": [], "rescue": [], "window": None, "nullsafe": False, "blocks": [], "legacy": False}


def parse(src: str) -> dict:
    lines = [re.sub(r"#.*$", "", l).rstrip() for l in src.splitlines()]
    lines = [l for l in lines if l.strip()]
    if not lines:
        raise RSXVError("empty program")
    if lines[0].strip().startswith("TIER"):
        return validate(_legacy(src))
    m = re.match(r"RSX(?:-V|/2)\s+TIER\s+(\d+)\s*(?:::\s*\{(\w+)\})?\s*(?:::\s*\((\w+)\))?\s*$", lines[0].strip())
    if not m:
        raise RSXVError("first line must be 'RSX-V TIER <n> :: {ARCHETYPE} :: (MODE)'")
    prog = new_program(int(m.group(1)))
    prog["archetype"], prog["mode"] = m.group(2) or "", m.group(3) or ""
    blk = None
    for raw in lines[1:]:
        s = raw.strip()
        word = s.split()[0]
        if word == "INTENT":
            mm = re.match(r'INTENT\s+"([^"]*)"\s*(?:<-\s*(.*))?$', s)
            if not mm:
                raise RSXVError("INTENT needs a quoted text")
            prog["intent"] = {"text": mm.group(1), "vectors": (mm.group(2) or "").split()}
        elif word == "GOAL":
            prog["goal"] = parse_cond(s[4:])
        elif word == "SENSE":
            prog["sense"] = s.split()[1:]
            bad = set(prog["sense"]) - SENSES
            if bad:
                raise RSXVError(f"unknown sense {sorted(bad)}")
        elif word == "LAWS":
            prog["laws"] = s.split()[1:]
            bad = set(prog["laws"]) - LAWS
            if bad:
                raise RSXVError(f"unknown law {sorted(bad)}")
        elif word == "RESCUE":
            prog["rescue"] = [x.strip("{}") for x in s.split()[1:]]
            bad = set(prog["rescue"]) - RESCUES
            if bad:
                raise RSXVError(f"unknown rescue archetype {sorted(bad)}")
        elif word == "WINDOW":
            mm = re.match(r"WINDOW\s+(\d\d):(\d\d)-(\d\d):(\d\d)$", s)
            if not mm:
                raise RSXVError("WINDOW hh:mm-hh:mm")
            a = int(mm.group(1)) * 60 + int(mm.group(2)); b = int(mm.group(3)) * 60 + int(mm.group(4))
            prog["window"] = [a, b]
        elif word in ("GATE", "CLOSE"):
            blk = {"kind": word, "name": word.lower(), "until": None, "if": None, "max_s": 15 if word == "GATE" else 30, "vectors": []}
            prog["blocks"].append(blk)
        elif word == "PHASE":
            mm = re.match(r"PHASE\s+(\w+)(?:\s+IF\s+(.+?))?(?:\s+ELSE\s+(\w+))?(?:\s+UNTIL\s+(.+?))?(?:\s+MIN\s+(\d+)s)?(?:\s+MAX\s+(\d+)s)?$", s)
            if not mm:
                raise RSXVError(f"bad PHASE line: {s}")
            blk = {"kind": "PHASE", "name": mm.group(1), "if": parse_cond(mm.group(2)), "else": mm.group(3),
                   "until": parse_cond(mm.group(4)), "min_s": int(mm.group(5) or 0), "max_s": int(mm.group(6) or 60), "vectors": []}
            if blk["min_s"] > blk["max_s"]:
                raise RSXVError(f"{blk['name']}: MIN above MAX")
            prog["blocks"].append(blk)
        elif s.startswith("@Vector"):
            v = _vector(s)
            if v["op"] == "NullSafe":
                if v["k"] != 0:
                    raise RSXVError("NullSafe is Vector 0")
                prog["nullsafe"] = True
                continue
            if blk is None:
                raise RSXVError(f"@Vector{v['k']} outside a GATE, PHASE or CLOSE block")
            blk["vectors"].append(v)
        else:
            raise RSXVError(f"unexpected line: {s}")
    return validate(prog)


def validate(prog: dict) -> dict:
    errs, warns = [], []
    seen = {}
    for b in prog["blocks"]:
        if len(b["vectors"]) > O.MAX_CONCURRENT:
            errs.append(f"{b['name']}: {len(b['vectors'])} concurrent vectors (at most {O.MAX_CONCURRENT})")
        for v in b["vectors"]:
            if v["k"] in seen:
                errs.append(f"@Vector{v['k']} used twice")
            seen[v["k"]] = v["op"]
            if v["next"] and v["op"] != "SymbolicCommandExport":
                errs.append(f"-> NEXT only on SymbolicCommandExport (@Vector{v['k']})")
        names = [v["op"] for v in b["vectors"]]
        for pair, why in O.CONFLICTS.items():
            if pair <= set(names):
                warns.append(f"{b['name']}: {' + '.join(sorted(pair))}: {why}")
    for b in prog["blocks"]:
        for v in b["vectors"]:
            if re.search(r"electric|charge|tdcs|tacs|tens\b|\bems\b|galvan", v["args"] or "", re.I):
                errs.append(f"@Vector{v['k']}: electrical stimulation is out of scope")
    names_so_far = []
    for b in prog["blocks"]:
        if b.get("else") and b["else"] not in names_so_far:
            errs.append(f"{b['name']}: ELSE {b['else']} must name an earlier phase")
        names_so_far.append(b["name"])
    total = sum(len(b["vectors"]) for b in prog["blocks"]) + (1 if prog["nullsafe"] else 0)
    if not prog["legacy"]:
        if total < 9:
            errs.append(f"{total} vectors: RSX needs at least 9")
        kinds = [b["kind"] for b in prog["blocks"]]
        if "GATE" not in kinds or kinds[0] != "GATE":
            errs.append("the first block must be GATE")
        elif "EthicsContain" not in [v["op"] for v in prog["blocks"][0]["vectors"]]:
            errs.append("GATE must contain EthicsContain")
        if not prog["nullsafe"]:
            errs.append("@Vector0:NullSafe is required")
    else:
        if total < 9:
            warns.append(f"legacy command has {total} vectors (spec: 9-17)")
        warns.append("legacy command: open loop, no gate, no stop rules")
    deep = [v["op"] for b in prog["blocks"] for v in b["vectors"] if O.OPS[v["op"]][1] in O.DEEP]
    covered = sorted({O.OPS[v["op"]][1] for b in prog["blocks"] for v in b["vectors"]} & set(O.LAYERS), key=lambda c: int(c[1:]))
    prog["check"] = {"errors": errs, "warnings": warns, "vectors": total, "deep_ops": len(deep),
                     "layers_covered": covered, "layers_missing": [c for c in O.LAYERS if c not in covered]}
    if errs:
        raise RSXVError("; ".join(errs))
    return prog


def to_text(prog: dict) -> str:
    """Program -> RSX-V source (used for NEXT)."""
    L = [f"RSX-V TIER {prog['tier']}" + (f" :: {{{prog['archetype']}}}" if prog["archetype"] else "") + (f" :: ({prog['mode']})" if prog["mode"] else "")]
    if prog["intent"]["text"]:
        L.append(f'INTENT "{prog["intent"]["text"]}"' + (" <- " + " ".join(prog["intent"]["vectors"]) if prog["intent"]["vectors"] else ""))
    if prog["goal"]:
        L.append("GOAL " + cond_text(prog["goal"]))
    if prog["sense"]:
        L.append("SENSE " + " ".join(prog["sense"]))
    if prog["laws"]:
        L.append("LAWS " + " ".join(prog["laws"]))
    if prog.get("rescue"):
        L.append("RESCUE " + " ".join("{" + x + "}" for x in prog["rescue"]))
    if prog["window"]:
        a, b = prog["window"]; L.append(f"WINDOW {a//60:02d}:{a%60:02d}-{b//60:02d}:{b%60:02d}")
    L.append("@Vector0:NullSafe")
    for b in prog["blocks"]:
        if b["kind"] == "PHASE":
            L.append(f"PHASE {b['name']}" + (f" IF {cond_text(b['if'])}" if b["if"] else "") + (f" ELSE {b['else']}" if b.get("else") else "")
                     + (f" UNTIL {cond_text(b['until'])}" if b["until"] else "") + (f" MIN {b['min_s']}s" if b.get("min_s") else "") + f" MAX {b['max_s']}s")
        else:
            L.append(b["kind"])
        for v in b["vectors"]:
            L.append(f"  @Vector{v['k']}:{v['op']}" + (f"({v['args']})" if v["args"] else "") + (" -> NEXT" if v["next"] else ""))
    return "\n".join(L) + "\n"
