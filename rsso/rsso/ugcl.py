"""UGCL — the native glyph layer of RSOS (spec/GLYPH_FORMAT.md).

A glyph is a few base strokes plus symmetry. From that one compact definition UGCL derives every form
the glyph takes, so a tier's glyph can be seen, felt and heard as one cue:

  * vector form at any resolution (SVG), for screens, watch faces and AR;
  * a haptic signature (a pulse rhythm) for wristbands, so the glyph can be felt;
  * a tone motif (a short pentatonic phrase), so it can be heard;
  * a genealogy: every library glyph records its parent and the mutation that produced it.

docs/js/ugcl.js implements the same derivations for the player; rsso/tests/test_ugcl.py checks that the
two give identical SVG, signatures and motifs.
"""
from __future__ import annotations

import math

FORMAT = "rsos-ugcl/1"
STROKE_W = 0.09
PENTATONIC = [261.63, 293.66, 329.63, 392.0, 440.0, 523.25, 587.33]

# Vibration codes (tactons): . short 100 ms, - long 300 ms, 100 ms between pulses; a space joins two codes
# (a recombination) with a 400 ms pause. Every original glyph has its own code (spec/GLYPH_FORMAT.md §7).
TACTON_SHORT, TACTON_LONG, TACTON_GAP, TACTON_WORD = 100, 300, 100, 400
TACTON_RE = r"[.\-]{1,6}( [.\-]{1,6}){0,2}"
# glyph text, as on the ledger pages: symbol fonts first, then colour emoji
EMOJI_FONTS = "'Noto Color Emoji','Apple Color Emoji','Segoe UI Emoji',sans-serif"
SYMBOL_FONTS = "'Noto Sans Symbols','Noto Sans Symbols 2','Noto Sans Math','Segoe UI Symbol','Apple Symbols',Symbola"
GLYPH_FONTS = SYMBOL_FONTS + "," + EMOJI_FONTS
JOINERS = ("\ufe0f", "\ufe0e", "\u200d")


def tacton_pulses(code: str) -> list[list[int]]:
    """[[on_ms, off_ms], ...] for a vibration code; the last off is 0."""
    out: list[list[int]] = []
    for c in code:
        if c == " ":
            if out:
                out[-1][1] = TACTON_WORD
            continue
        out.append([TACTON_SHORT if c == "." else TACTON_LONG, TACTON_GAP])
    if out:
        out[-1][1] = 0
    return out


def glyph_font_size(char: str) -> int:
    """Font size in a 64-unit box by how many symbols the glyph has (identical in JavaScript)."""
    n = len([c for c in char if c not in JOINERS])
    return 44 if n <= 1 else 32 if n == 2 else 24 if n == 3 else rint(76 / n)


def _joined(t: str, color: str) -> str:
    """A recorded pair ("🦁+🐉") keeps its plus sign, drawn in the glyph colour."""
    return t.replace("+", f'<tspan fill="{color}" font-family="sans-serif" dx="1">+</tspan>')


def _xml(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def rint(x: float) -> int:
    """Round half up (identical in JavaScript: Math.floor(x + 0.5))."""
    return int(math.floor(x + 0.5))


def fmt(x: float) -> str:
    """Fixed 3-decimal formatting shared with JavaScript (-0 printed as 0)."""
    v = rint(x * 1000) / 1000
    return "0" if v == 0 else f"{v:.3f}".rstrip("0").rstrip(".")


def _rot(x, y, deg):
    a = math.radians(deg)
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)


def expand(g: dict) -> list[dict]:
    """Apply rotational symmetry (order g['sym']) and optional mirroring to the base strokes."""
    out = []
    sym = int(g.get("sym", 1))
    for k in range(sym):
        ang = 360.0 * k / sym
        for s in g["strokes"]:
            for mir in ((False, True) if g.get("mirror") else (False,)):
                out.append(_transform(s, ang, mir))
    return out


def _transform(s, ang, mir):
    k, p = s["k"], list(s["p"])
    if k == "L":
        x1, y1, x2, y2 = p
        if mir:
            x1, x2 = -x1, -x2
        (x1, y1), (x2, y2) = _rot(x1, y1, ang), _rot(x2, y2, ang)
        return {"k": "L", "p": [x1, y1, x2, y2]}
    if k in ("C", "D"):
        cx, cy, r = p
        if mir:
            cx = -cx
        cx, cy = _rot(cx, cy, ang)
        return {"k": k, "p": [cx, cy, r]}
    if k == "A":
        cx, cy, r, a0, a1 = p
        if mir:
            cx, a0, a1 = -cx, 180 - a1, 180 - a0
        cx, cy = _rot(cx, cy, ang)
        return {"k": "A", "p": [cx, cy, r, a0 + ang, a1 + ang]}
    raise ValueError(f"unknown stroke kind {k}")


def _svg_original(g: dict, size: int, color: str, background: str | None) -> str:
    """An original ledger glyph as text, exactly as recorded and drawn as on the ledger pages: the symbol fonts
    first, then the emoji fonts, in `color` (emoji keep their own colours); crisp at any size. The stored image is
    kept as the reference the rhythm and melody were derived from."""
    bg = f'<rect width="64" height="64" fill="{background}"/>' if background else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 64 64" role="img" '
            f'aria-label="{_xml(g["char"])}">{bg}<text x="32" y="33" text-anchor="middle" dominant-baseline="central" '
            f'font-size="{glyph_font_size(g["char"])}" font-family="{GLYPH_FONTS}" fill="{color}">{_joined(_xml(g["char"]), color)}</text></svg>')


def svg(g: dict, size: int = 120, color: str = "#e8b04a", background: str | None = None) -> str:
    if g.get("kind") == "original":
        return _svg_original(g, size, color, background)
    parts = []
    for s in expand(g):
        k, p = s["k"], s["p"]
        if k == "L":
            parts.append(f'<line x1="{fmt(p[0])}" y1="{fmt(-p[1])}" x2="{fmt(p[2])}" y2="{fmt(-p[3])}"/>')
        elif k == "C":
            parts.append(f'<circle cx="{fmt(p[0])}" cy="{fmt(-p[1])}" r="{fmt(p[2])}"/>')
        elif k == "D":
            parts.append(f'<circle cx="{fmt(p[0])}" cy="{fmt(-p[1])}" r="{fmt(p[2])}" fill="{color}" stroke="none"/>')
        else:
            cx, cy, r, a0, a1 = p
            x0, y0 = cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0))
            x1, y1 = cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1))
            large = 1 if (a1 - a0) % 360 > 180 else 0
            parts.append(f'<path d="M{fmt(x0)} {fmt(-y0)}A{fmt(r)} {fmt(r)} 0 {large} 0 {fmt(x1)} {fmt(-y1)}"/>')
    bg = f'<rect x="-1.2" y="-1.2" width="2.4" height="2.4" fill="{background}"/>' if background else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-1.2 -1.2 2.4 2.4" width="{size}" height="{size}">{bg}'
            f'<g fill="none" stroke="{color}" stroke-width="{STROKE_W}" stroke-linecap="round" stroke-linejoin="round">'
            + "".join(parts) + "</g></svg>")


def stroke_length(s: dict) -> float:
    k, p = s["k"], s["p"]
    if k == "L":
        return math.hypot(p[2] - p[0], p[3] - p[1])
    if k == "C":
        return 2 * math.pi * p[2]
    if k == "A":
        return math.radians(abs(p[4] - p[3])) * p[2]
    return 0.0


def haptic_signature(g: dict) -> list[list[int]]:
    """Pulse rhythm [[on_ms, off_ms], ...], at most 2 s. One pulse per base stroke (length sets duration),
    repeated min(sym, 3) times; a final short pulse if the glyph is mirrored. Original glyphs carry their own."""
    if g.get("kind") == "original":
        return tacton_pulses(g["tacton"]) if g.get("tacton") else [list(x) for x in g["haptic"]]
    base = []
    for s in g["strokes"]:
        on = 50 if s["k"] == "D" else min(220, max(60, rint(60 + 60 * stroke_length(s))))
        base.append([on, 80])
    seq = []
    for r in range(min(int(g.get("sym", 1)), 3)):
        seq += [list(x) for x in base]
        seq[-1][1] = 160
    if g.get("mirror"):
        seq.append([40, 80])
    out, total = [], 0
    for on, off in seq:
        if total + on > 2000:
            break
        out.append([on, off]); total += on + off
    out[-1][1] = 0
    return out


def tone_motif(g: dict) -> list[list[float]]:
    """[[hz, ms], ...]: one pentatonic note per base stroke, chosen by the stroke's direction from the
    centre; rotational symmetry above 1 adds the glyph's first note an octave up. Original glyphs carry their own."""
    if g.get("kind") == "original":
        return [list(x) for x in g["tone"]]
    notes = []
    for s in g["strokes"]:
        p = s["p"]
        mx, my = ((p[0] + p[2]) / 2, (p[1] + p[3]) / 2) if s["k"] == "L" else (p[0], p[1])
        ang = (math.degrees(math.atan2(my, mx)) + 360) % 360 if (mx or my) else 0.0
        notes.append([PENTATONIC[int(ang // (360 / 7)) % 7], 180])
    if int(g.get("sym", 1)) > 1:
        notes.append([round(notes[0][0] * 2, 2), 260])
    return notes


def encode(g: dict) -> str:
    """Compact text form for devices and links, e.g. "2m:L-0.75,1,-0.25,-0.75;A0,0,0.5,45,135" (no id)."""
    head = str(int(g.get("sym", 1))) + ("m" if g.get("mirror") else "")
    return head + ":" + ";".join(s["k"] + ",".join(fmt(v) for v in s["p"]) for s in g["strokes"])


def decode(code: str, gid: str = "glyph") -> dict:
    head, body = code.split(":", 1)
    g = {"id": gid, "sym": int(head.rstrip("m")), "mirror": head.endswith("m"),
         "strokes": [{"k": part[0], "p": [float(v) for v in part[1:].split(",")]} for part in body.split(";")]}
    validate(g)
    return g


def validate(g: dict) -> None:
    if not isinstance(g.get("id"), str) or not g["id"]:
        raise ValueError("glyph needs an id")
    if g.get("kind") == "original":
        if not g.get("char") or not str(g.get("png", "")).startswith("data:image/png;base64,"):
            raise ValueError("an original glyph needs its symbol and image")
        if not g.get("haptic") or not g.get("tone"):
            raise ValueError("an original glyph needs its rhythm and melody")
        if "tacton" in g and not __import__("re").fullmatch(TACTON_RE, g["tacton"]):
            raise ValueError("a vibration code is 1 to 6 dots and dashes, up to three joined by spaces")
        return
    if not 1 <= int(g.get("sym", 1)) <= 8:
        raise ValueError("sym must be 1..8")
    if not 1 <= len(g.get("strokes", [])) <= 4:
        raise ValueError("a glyph has 1 to 4 base strokes")
    n = {"L": 4, "C": 3, "D": 3, "A": 5}
    for s in g["strokes"]:
        if s.get("k") not in n or len(s.get("p", [])) != n[s["k"]]:
            raise ValueError(f"bad stroke {s}")
        coords = s["p"][:4] if s["k"] == "L" else s["p"][:2]
        if any(abs(c) > 1.0001 for c in coords):
            raise ValueError("stroke coordinates must lie in [-1, 1]")
