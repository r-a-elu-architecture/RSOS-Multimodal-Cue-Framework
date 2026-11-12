"""RSX compiler: RSX source text -> timeline (a JSON-serialisable dict).

The JavaScript implementation in ``docs/js/rsx.js`` follows this file
statement for statement; ``tests/test_conformance.py`` checks that both
produce identical output for every protocol in ``protocols/``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

LANGUAGE_VERSION = "2.0"

CHANNELS = ("V", "A", "K", "O", "G")
CHANNEL_NAMES = {"V": "visual", "A": "auditory", "K": "kinesthetic", "O": "olfactory", "G": "gustatory"}

TACTON_SHORT, TACTON_LONG, TACTON_GAP, TACTON_WORD = 100, 300, 100, 400
DEFAULT_SAFETY = {"max_per_hour": 6, "max_per_day": 20, "refractory_ms": 90000, "haptic_max": 0.4}
DEFAULT_BREATH = {"inhale": 4000, "exhale": 6000, "hold": 0}
SAY_MS = 1500          # how long a spoken / shown word is presented
CUE_MS = 2000          # default presentation time of a cue without its own duration

# Legacy RSX v1 vector operators (archive/RSX-Command_Specification) with a runtime effect.
VECTOR_OPS = {"BreathOverride", "MemoryRecall", "EmotionalLock", "FutureProjection",
              "DeviceOutput", "PostureShift"}


class RSXError(Exception):
    def __init__(self, line: int, message: str):
        super().__init__(f"line {line}: {message}")
        self.line = line
        self.message = message


# ---------------------------------------------------------------- lexing helpers

_TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"|\S+')


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text)


def unquote(tok: str, line: int) -> str:
    if len(tok) < 2 or tok[0] != '"' or tok[-1] != '"':
        raise RSXError(line, f"expected a quoted string, got {tok}")
    return tok[1:-1].replace('\\"', '"').replace("\\\\", "\\")


def parse_duration(tok: str, line: int) -> int:
    m = re.fullmatch(r"(\d+(?:\.\d+)?)(ms|s|m)", tok)
    if not m:
        raise RSXError(line, f"bad duration {tok} (use e.g. 300ms, 4s, 1.5s, 2m)")
    value = float(m.group(1))
    factor = {"ms": 1, "s": 1000, "m": 60000}[m.group(2)]
    return int(round(value * factor))


def parse_number(tok: str, line: int) -> float:
    try:
        return float(tok)
    except ValueError:
        raise RSXError(line, f"expected a number, got {tok}") from None


def parse_kv(tokens: list[str], line: int) -> dict[str, str]:
    out = {}
    for t in tokens:
        if "=" not in t:
            raise RSXError(line, f"expected key=value, got {t}")
        k, v = t.split("=", 1)
        out[k] = v
    return out


def strip_comment(raw: str) -> str:
    out, inq = [], False
    i = 0
    while i < len(raw):
        c = raw[i]
        if c == "\\" and inq and i + 1 < len(raw):
            out.append(raw[i:i + 2]); i += 2; continue
        if c == '"':
            inq = not inq
        if c == "#" and not inq:
            break
        out.append(c); i += 1
    return "".join(out).strip()


# ---------------------------------------------------------------- parsing

@dataclass
class Line:
    no: int
    text: str


def split_lines(source: str) -> list[Line]:
    lines = []
    for no, raw in enumerate(source.splitlines(), start=1):
        text = strip_comment(raw)
        if not text:
            continue
        # allow several statements on one line separated by ';' (outside quotes)
        parts, buf, inq = [], [], False
        for c in text:
            if c == '"':
                inq = not inq
            if c == ";" and not inq:
                parts.append("".join(buf)); buf = []
            else:
                buf.append(c)
        parts.append("".join(buf))
        for p in parts:
            p = p.strip()
            if p:
                lines.append(Line(no, p))
    return lines


def parse_block(lines: list[Line], i: int, opener: Line) -> tuple[list[Line], int]:
    """Collect lines up to the matching '}' . ``i`` points after the opener."""
    depth, body = 1, []
    while i < len(lines):
        ln = lines[i]
        if ln.text == "}":
            depth -= 1
            if depth == 0:
                return body, i + 1
        if ln.text.endswith("{"):
            depth += 1
        body.append(ln); i += 1
    raise RSXError(opener.no, "missing closing }")


def compile_rsx(source: str) -> dict:
    """Compile RSX source to a timeline dict. Raises RSXError on any problem."""
    lines = split_lines(source)
    prog = {
        "rsx": LANGUAGE_VERSION,
        "protocol": None, "title": "", "version": "",
        "safety": dict(DEFAULT_SAFETY),
        "breath": dict(DEFAULT_BREATH),
        "tiers": {}, "futures": [],
        "phases": [], "events": [], "warnings": [],
        "duration_ms": 0,
    }
    state = {"t": 0}
    i = 0
    while i < len(lines):
        ln = lines[i]
        toks = tokenize(ln.text)
        kw = toks[0]
        if kw == "PROTOCOL":
            if len(toks) < 2:
                raise RSXError(ln.no, "PROTOCOL needs an id")
            prog["protocol"] = toks[1]
            prog["title"] = unquote(toks[2], ln.no) if len(toks) > 2 else toks[1]
            i += 1
        elif kw == "VERSION":
            prog["version"] = toks[1] if len(toks) > 1 else ""
            i += 1
        elif kw == "SAFETY":
            for k, v in parse_kv(toks[1:], ln.no).items():
                if k in ("max_per_hour", "max_per_day"):
                    prog["safety"][k] = int(parse_number(v, ln.no))
                elif k == "refractory":
                    prog["safety"]["refractory_ms"] = parse_duration(v, ln.no)
                elif k == "haptic_max":
                    a = parse_number(v, ln.no)
                    if not 0 < a <= 1:
                        raise RSXError(ln.no, "haptic_max must be in (0, 1]")
                    prog["safety"][k] = a
                else:
                    raise RSXError(ln.no, f"unknown SAFETY key {k}")
            i += 1
        elif kw == "BREATH":
            for k, v in parse_kv(toks[1:], ln.no).items():
                if k not in DEFAULT_BREATH:
                    raise RSXError(ln.no, f"unknown BREATH key {k}")
                prog["breath"][k] = parse_duration(v, ln.no)
            i += 1
        elif kw == "FUTURES":
            items = [t for t in toks[1:] if t != "|"]
            prog["futures"] = [unquote(t, ln.no) for t in items]
            if not prog["futures"]:
                raise RSXError(ln.no, "FUTURES needs at least one quoted context")
            i += 1
        elif kw == "TIER" and "::" in toks:
            _vector_command(prog, state, ln, toks)
            i += 1
        elif kw == "TIER":
            if toks[-1] != "{" or len(toks) != 4:
                raise RSXError(ln.no, 'tier syntax: TIER <number> <NAME> {')
            body, i = parse_block(lines, i + 1, ln)
            _tier(prog, ln, toks, body)
        elif kw in ("PHASE", "FOR", "REPEAT"):
            if toks[-1] != "{":
                raise RSXError(ln.no, f"{kw} must open a block with {{")
            body, i = parse_block(lines, i + 1, ln)
            _block(prog, state, ln, toks, body, ctx={})
        else:
            raise RSXError(ln.no, f"unknown statement {kw}")
    if prog["protocol"] is None:
        raise RSXError(1, "missing PROTOCOL statement")
    prog["duration_ms"] = state["t"]
    prog["events"].sort(key=lambda e: (e["t"], e["seq"]))
    for e in prog["events"]:
        del e["seq"]
    return prog


def _tier(prog, ln, toks, body):
    try:
        number = int(toks[1])
    except ValueError:
        raise RSXError(ln.no, "tier number must be an integer") from None
    name = toks[2]
    if name in prog["tiers"]:
        raise RSXError(ln.no, f"tier {name} defined twice")
    tier = {"number": number, "name": name, "glyph": "", "word": "", "channels": {}}
    for b in body:
        bt = tokenize(b.text)
        key = bt[0]
        if len(bt) != 2:
            raise RSXError(b.no, f"{key} takes one quoted value")
        val = unquote(bt[1], b.no)
        if key in CHANNELS:
            tier["channels"][key] = val
        elif key == "GLYPH":
            tier["glyph"] = val
        elif key == "WORD":
            tier["word"] = val
        elif key == "FRAME":          # node: the mental frame held in this state (spec/NODES.md)
            tier.setdefault("frames", []).append(val)
            if len(tier["frames"]) > 5:
                raise RSXError(b.no, "a tier holds at most 5 frames")
        elif key == "MODE":
            if val not in ("associated", "observer"):
                raise RSXError(b.no, 'MODE is "associated" or "observer"')
            tier["mode"] = val
        elif key == "TACTON":         # vibration code: . short (100 ms), - long (300 ms); a space joins codes (400 ms pause)
            if not re.fullmatch(r"[.\-]{1,6}( [.\-]{1,6}){0,2}", val):
                raise RSXError(b.no, 'TACTON is 1 to 6 dots and dashes, up to three joined by spaces, e.g. "..-" or "..- ---"')
            tier["tacton"] = val
        else:
            raise RSXError(b.no, f"unknown tier field {key}")
    missing = [c for c in ("V", "A", "K") if c not in tier["channels"]]
    if missing:
        raise RSXError(ln.no, f"tier {name} needs channels V, A and K (missing {', '.join(missing)})")
    prog["tiers"][name] = tier


def _emit(prog, state, t, dur, channel, kind, phase, **params):
    ev = {"t": t, "dur": dur, "channel": channel, "kind": kind, "phase": phase}
    ev.update(params)
    ev["seq"] = len(prog["events"])
    prog["events"].append(ev)
    return t + dur


def _subst(text, ctx):
    if "$future" in text:
        if "future" not in ctx:
            raise RSXError(ctx.get("_line", 0), "$future used outside FOR FUTURE")
        text = text.replace("$future", ctx["future"])
    return text


def _block(prog, state, ln, toks, body, ctx):
    kw = toks[0]
    if kw == "FOR":
        if toks[1:] != ["FUTURE", "{"]:
            raise RSXError(ln.no, "loop syntax: FOR FUTURE {")
        if not prog["futures"]:
            raise RSXError(ln.no, "FOR FUTURE used before FUTURES")
        for k, f in enumerate(prog["futures"]):
            _run_body(prog, state, body, dict(ctx, future=f, future_index=k))
    elif kw == "REPEAT":
        if len(toks) != 3:
            raise RSXError(ln.no, "loop syntax: REPEAT <n> {")
        n = int(parse_number(toks[1], ln.no))
        if n < 1 or n > 100:
            raise RSXError(ln.no, "REPEAT count must be 1..100")
        for _ in range(n):
            _run_body(prog, state, body, ctx)
    else:
        _phase(prog, state, ln, toks, body, ctx)


def _run_body(prog, state, body, ctx):
    j = 0
    while j < len(body):
        b = body[j]
        bt = tokenize(b.text)
        if bt[0] in ("PHASE", "FOR", "REPEAT") and bt[-1] == "{":
            inner, j = parse_block(body, j + 1, b)
            _block(prog, state, b, bt, inner, ctx)
        elif bt[0] == "TIER" and "::" in bt:
            _vector_command(prog, state, b, bt); j += 1
        else:
            raise RSXError(b.no, f"{bt[0]} must be inside a PHASE")


def _phase(prog, state, ln, toks, body, ctx):
    if len(toks) < 3:
        raise RSXError(ln.no, "phase syntax: PHASE <name> [breath=inhale|exhale|hold|none] [dur=4s] {")
    name = toks[1]
    opts = parse_kv(toks[2:-1], ln.no)
    breath = opts.pop("breath", "none")
    min_dur = parse_duration(opts.pop("dur"), ln.no) if "dur" in opts else 0
    if opts:
        raise RSXError(ln.no, f"unknown PHASE option {next(iter(opts))}")
    if breath not in ("inhale", "exhale", "hold", "none"):
        raise RSXError(ln.no, f"bad breath {breath}")
    start = state["t"]
    index = len(prog["phases"])
    extra = {}
    if "future_index" in ctx:
        extra["future_index"] = ctx["future_index"]
    end = start
    if breath != "none":
        bd = prog["breath"][breath]
        end = max(end, _emit(prog, state, start, bd, "breath", breath, name, **extra))
    end = max(end, _steps(prog, state, body, name, start, ctx, extra)[0])
    end = max(end, start + min_dur)
    if end == start:
        end = start + CUE_MS
    rec = {"name": name, "t": start, "dur": end - start, "breath": breath, "index": index}
    rec.update(extra)
    prog["phases"].append(rec)
    state["t"] = end


def _steps(prog, state, body, phase, cursor, ctx, extra):
    """Run the steps of a phase body. Returns (latest end time, cursor)."""
    end, j = cursor, 0
    while j < len(body):
        b = body[j]
        bt = tokenize(b.text)
        if bt[0] == "FOR" and bt[-1] == "{":
            if bt[1:] != ["FUTURE", "{"]:
                raise RSXError(b.no, "loop syntax: FOR FUTURE {")
            if not prog["futures"]:
                raise RSXError(b.no, "FOR FUTURE used before FUTURES")
            if "future" in ctx:
                raise RSXError(b.no, "FOR FUTURE cannot be nested")
            inner, j = parse_block(body, j + 1, b)
            for k, f in enumerate(prog["futures"]):
                e, cursor = _steps(prog, state, inner, phase, cursor, dict(ctx, future=f, future_index=k), extra)
                end = max(end, e)
            continue
        end = max(end, _step(prog, state, b, bt, phase, cursor, dict(ctx, _line=b.no), extra))
        if bt[0] == "WAIT":
            cursor += parse_duration(bt[1], b.no)
            end = max(end, cursor)
        j += 1
    return end, cursor


def _step(prog, state, b, bt, phase, t, ctx, extra):
    kw = bt[0]
    simple = {"SAY": ("A", "say"), "SEE": ("V", "see"), "FEEL": ("K", "feel"),
              "GESTURE": ("K", "gesture"), "SMELL": ("O", "smell"), "TASTE": ("G", "taste")}
    if kw in simple:
        if len(bt) != 2:
            raise RSXError(b.no, f"{kw} takes one quoted value")
        ch, kind = simple[kw]
        dur = SAY_MS if kw == "SAY" else CUE_MS
        return _emit(prog, state, t, dur, CHANNEL_NAMES[ch], kind, phase,
                     text=_subst(unquote(bt[1], b.no), ctx), **extra)
    if kw == "WAIT":
        if len(bt) != 2:
            raise RSXError(b.no, "WAIT takes a duration")
        parse_duration(bt[1], b.no)
        return t
    if kw == "HAPTIC":
        kv = parse_kv(bt[1:], b.no)
        on = parse_duration(kv.pop("on", "300ms"), b.no)
        off = parse_duration(kv.pop("off", "300ms"), b.no)
        count = int(parse_number(kv.pop("x", "1"), b.no))
        amp = parse_number(kv.pop("amp", str(prog["safety"]["haptic_max"])), b.no)
        if kv:
            raise RSXError(b.no, f"unknown HAPTIC key {next(iter(kv))}")
        if amp > prog["safety"]["haptic_max"] + 1e-12:
            raise RSXError(b.no, f"haptic amp {amp} exceeds SAFETY haptic_max {prog['safety']['haptic_max']}")
        if count < 1 or count > 50:
            raise RSXError(b.no, "haptic x must be 1..50")
        return _emit(prog, state, t, (on + off) * count, "haptic", "pulse", phase,
                     on=on, off=off, count=count, amp=amp, **extra)
    if kw == "TONE":
        if len(bt) != 3 or not bt[1].endswith("Hz"):
            raise RSXError(b.no, "TONE syntax: TONE <freq>Hz <duration>")
        hz = parse_number(bt[1][:-2], b.no)
        if not 20 <= hz <= 4000:
            raise RSXError(b.no, "tone frequency must be 20..4000 Hz")
        return _emit(prog, state, t, parse_duration(bt[2], b.no), "auditory", "tone", phase, hz=hz, **extra)
    if kw == "ACTIVATE":
        if len(bt) != 2:
            raise RSXError(b.no, "ACTIVATE takes a tier name")
        tier = _find_tier(prog, bt[1], b.no)
        return _activate(prog, state, tier, phase, t, extra)
    if kw == "MARK":
        if len(bt) != 2:
            raise RSXError(b.no, "MARK takes one quoted label")
        return _emit(prog, state, t, 0, "marker", "mark", phase, text=unquote(bt[1], b.no), **extra)
    raise RSXError(b.no, f"unknown step {kw}")


def _find_tier(prog, ref, line):
    if ref in prog["tiers"]:
        return prog["tiers"][ref]
    for tier in prog["tiers"].values():
        if str(tier["number"]) == ref:
            return tier
    raise RSXError(line, f"unknown tier {ref}")


def _activate(prog, state, tier, phase, t, extra):
    node = {k: tier[k] for k in ("frames", "mode", "tacton") if k in tier}
    end = _emit(prog, state, t, 0, "marker", "tier", phase, tier=tier["name"], number=tier["number"],
                glyph=tier["glyph"], word=tier["word"], **node, **extra)
    for ch in CHANNELS:
        if ch in tier["channels"]:
            end = max(end, _emit(prog, state, t, CUE_MS, CHANNEL_NAMES[ch], "cue", phase,
                                 text=tier["channels"][ch], tier=tier["name"], **extra))
    off = 0
    for sym in tier.get("tacton", ""):
        if sym == " ":
            off += TACTON_WORD - TACTON_GAP
            continue
        on = TACTON_SHORT if sym == "." else TACTON_LONG
        end = max(end, _emit(prog, state, t + off, on + TACTON_GAP, "haptic", "pulse", phase, on=on, off=TACTON_GAP,
                             count=1, amp=prog["safety"]["haptic_max"], tacton=tier["tacton"], **extra))
        off += on + TACTON_GAP
    return end


def _vector_command(prog, state, ln, toks):
    """Legacy RSX v1 command: TIER n :: {ARCH} :: (MODE) :: @VectorK:Op(args) :: ..."""
    parts = [p.strip() for p in " ".join(toks).split("::")]
    head = parts[0].split()
    if len(head) != 2 or head[0] != "TIER":
        raise RSXError(ln.no, "vector command must start with TIER <n> ::")
    number = head[1]
    arch = mode = None
    vectors = []
    for p in parts[1:]:
        if not p:
            continue
        if p.startswith("{") and p.endswith("}"):
            arch = p[1:-1]
        elif p.startswith("(") and p.endswith(")"):
            mode = p[1:-1]
        elif p.startswith("@"):
            m = re.fullmatch(r"@Vector(\d+):(\w+)(?:\((.*)\))?", p)
            if not m:
                raise RSXError(ln.no, f"bad vector {p}")
            vectors.append((int(m.group(1)), m.group(2), m.group(3) or ""))
        else:
            raise RSXError(ln.no, f"unexpected element {p}")
    if not vectors:
        raise RSXError(ln.no, "vector command has no @Vector elements")
    if len(vectors) > 17:
        raise RSXError(ln.no, "RSX supports at most 17 concurrent vectors")
    name = f"tier-{number}"
    start = state["t"]
    index = len(prog["phases"])
    end = _emit(prog, state, start, 0, "marker", "vector-command", name, number=number,
                archetype=arch or "", mode=mode or "", vectors=len(vectors))
    for k, op, arg in vectors:
        tag = {"vector": k}
        if op == "BreathOverride":
            t1 = _emit(prog, state, start, prog["breath"]["inhale"], "breath", "inhale", name, **tag)
            end = max(end, _emit(prog, state, t1, prog["breath"]["exhale"], "breath", "exhale", name, **tag))
        elif op == "MemoryRecall":
            target = arg.split("=", 1)[1] if "=" in arg else arg
            key = target.capitalize() if target.capitalize() in prog["tiers"] else target
            if key in prog["tiers"]:
                end = max(end, _activate(prog, state, prog["tiers"][key], name, start, tag))
            else:
                end = max(end, _emit(prog, state, start, CUE_MS, "visual", "see", name,
                                     text=f"Recall the {target.title()} archetype", **tag))
        elif op == "EmotionalLock":
            end = max(end, _emit(prog, state, start, 0, "marker", "state", name, text=arg, **tag))
        elif op == "FutureProjection":
            end = max(end, _emit(prog, state, start, CUE_MS, "visual", "see", name,
                                 text=f"See your future self {arg}".strip(), **tag))
        elif op == "DeviceOutput":
            end = max(end, _emit(prog, state, start, 0, "device", "output", name, text=arg, **tag))
        elif op == "PostureShift":
            end = max(end, _emit(prog, state, start, CUE_MS, "kinesthetic", "feel", name,
                                 text="Shift into an upright, open posture", **tag))
        else:
            prog["warnings"].append(f"line {ln.no}: @Vector{k}:{op} has no runtime effect (recorded only)")
            end = max(end, _emit(prog, state, start, 0, "annotation", "vector", name, text=op, **tag))
    end = max(end, start + CUE_MS)
    prog["phases"].append({"name": name, "t": start, "dur": end - start, "breath": "none", "index": index})
    state["t"] = end
