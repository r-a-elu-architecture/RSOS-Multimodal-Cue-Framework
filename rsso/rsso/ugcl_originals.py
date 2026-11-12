"""The original glyphs of the tier ledger, as UGCL glyphs of kind "original".

Every glyph the ledger records in a tier's glyph field or glyph mutation (🦁, ·⁂⊚, ∴, 🜂, 🝡 …) becomes one
glyph, in order of first appearance (O001 = 🦁, Tier 001). Each keeps:

  - the symbol itself, exactly as recorded, and every tier where it appears;
  - its ancestry from the ledger's own mutation chain: the glyphs it mutated from and into, with the tier;
  - an image: the symbol rendered once with fixed fonts (Noto Color Emoji for emoji, DejaVu Sans, GNU Unifont
    and Unifont Upper for the rest), stored as a PNG, so it looks the same on every device;
  - a vibration rhythm and a melody derived from that image (below), so the original glyphs can move between
    the senses like every UGCL glyph.

Derivation (deterministic; the stored values are the reference, JavaScript only reads them):
  image   → 64×64 ink mask, cropped to the ink and centred
  rhythm  → one pulse per quadrant holding at least a tenth of the ink (clockwise from top left), 60–220 ms
            by its share; 80 ms apart, 140 ms if the glyph encloses space; the whole pattern twice if the glyph
            is mirror-symmetric; a short 40 ms accent if it is dense; at most 2 s
  melody  → the directions in which the glyph's ink lies from the centre, in sevenths of a circle: one
            pentatonic note (C4 D4 E4 G4 A4 C5 D5) per strong direction, strongest first (2–4 notes), 140, 180
            or 240 ms by how much ink lies that way; mirror-symmetric glyphs end with their first note an
            octave up

  python -m rsso.ugcl_originals      # writes docs/ugcl/originals.json and rsso/results/ugcl_originals.md
"""
from __future__ import annotations

import base64
import io
import json
import math
import re
import unicodedata

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import binary_dilation, label

from .ledger import ROOT, build
from .ugcl import PENTATONIC

FORMAT = "rsos-ugcl/1"
FONTS = [("emoji", "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109),
         ("dejavu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 96),
         ("unifont", "/usr/share/fonts/opentype/unifont/unifont.otf", 96),
         ("upper", "/usr/share/fonts/opentype/unifont/unifont_upper.otf", 96)]
RES = 64
JOINERS = {"️", "‍"}
NOT_GLYPH = set("→←↔↑↓⇄+=×|—–-·•*\"“”'’,.:;()[]{}!?/\\<>")


def _cmaps():
    from fontTools.ttLib import TTFont
    return {name: set(TTFont(path, fontNumber=0).getBestCmap()) for name, path, _ in FONTS}


def is_glyph_token(tok: str) -> bool:
    chars = [c for c in tok if c not in JOINERS]
    if not chars or any(unicodedata.category(c)[0] in "LN" for c in chars):
        return False
    return any(c not in NOT_GLYPH for c in chars)


def tokens(text: str) -> list[str]:
    """Glyph tokens in a glyph field: '🦁 + 🐉' -> ['🦁', '🐉']; '·⁂⊚' stays one glyph."""
    out = []
    for part in re.split(r"[\s,/|+→←()\[\]:;]+", text):
        part = part.strip("\"“”'’.-—–*•")
        if part and is_glyph_token(part):
            out.append(part)
    return out


def collect(ledger: dict | None = None) -> list[dict]:
    led = ledger or build()
    seen: dict[str, dict] = {}
    order = []

    def note(tok, tid, number, how):
        if tok not in seen:
            seen[tok] = dict(char=tok, tiers=[], parents=[], children=[])
            order.append(tok)
        g = seen[tok]
        if not g["tiers"] or g["tiers"][-1]["id"] != tid:
            g["tiers"].append(dict(id=tid, number=number, how=how))

    for r in led["records"]:
        if r["kind"] != "tier":
            continue
        chain = [t for g in r["glyph_chain"] for t in tokens(g)[:1]]
        for t in tokens(r["fields"].get("glyph", "")):
            note(t, r["id"], r["number"], "glyph")
        for i, t in enumerate(chain):
            note(t, r["id"], r["number"], "from" if i == 0 and len(chain) > 1 else "to")
        for a, b in zip(chain, chain[1:]):
            if a != b:
                seen[a]["children"].append(dict(char=b, tier=r["id"], number=r["number"]))
                seen[b]["parents"].append(dict(char=a, tier=r["id"], number=r["number"]))
    return [seen[t] for t in order]


def render(tok: str, cmaps) -> tuple[np.ndarray, Image.Image, bool]:
    """(64×64 ink mask in 0..1, RGBA image for display, colour?) for a glyph token."""
    pieces, colour = [], False
    for ch in [c for c in tok if c not in JOINERS]:
        name, path, size = next(((n, p, s) for n, p, s in FONTS if ord(ch) in cmaps[n]), FONTS[-1])
        font = ImageFont.truetype(path, size)
        canvas = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
        d = ImageDraw.Draw(canvas)
        if name == "emoji":
            d.text((10, 10), ch, font=font, embedded_color=True)
            colour = True
        else:
            d.text((10, 10), ch, font=font, fill=(255, 255, 255, 255))
        box = canvas.getchannel("A").getbbox()
        if box:
            pieces.append(canvas.crop(box))
    if not pieces:
        raise ValueError(f"cannot render {tok!r}")
    h = max(p.height for p in pieces)
    gap = max(4, h // 8)
    strip = Image.new("RGBA", (sum(p.width for p in pieces) + gap * (len(pieces) - 1), h), (0, 0, 0, 0))
    x = 0
    for p in pieces:
        strip.paste(p, (x, (h - p.height) // 2))
        x += p.width + gap
    side = max(strip.size)
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.paste(strip, ((side - strip.width) // 2, (side - strip.height) // 2))
    img = sq.resize((RES, RES), Image.LANCZOS)
    mask = np.asarray(img.getchannel("A"), dtype=float) / 255.0
    return mask, img, colour


def features(mask: np.ndarray) -> dict:
    ink = mask > 0.35
    parts_lab, n = label(binary_dilation(ink, iterations=1))
    sizes = sorted((int((parts_lab == k).sum()) for k in range(1, n + 1)), reverse=True)
    total = float(sum(sizes)) or 1.0
    sym = 1.0 - float(np.abs(mask - mask[:, ::-1]).sum()) / (2.0 * float(mask.sum()) or 1.0)
    ys, xs = np.nonzero(ink)
    cy, cx = (RES - 1) / 2, (RES - 1) / 2
    bins = [0.0] * 7
    for y, x in zip(ys, xs):
        a = math.degrees(math.atan2(cy - y, x - cx)) % 360
        bins[int(a / (360 / 7)) % 7] += 1
    h = RES // 2
    q = [float(mask[:h, :h].sum()), float(mask[:h, h:].sum()), float(mask[h:, h:].sum()), float(mask[h:, :h].sum())]
    qt = sum(q) or 1.0
    holes = int(label(~binary_dilation(ink, iterations=1))[1]) - 1
    return dict(parts=len(sizes), shares=[s / total for s in sizes], symmetry=round(sym, 4),
                density=round(float(ink.mean()), 4), angles=bins, quadrants=[x / qt for x in q], holes=max(0, holes))


def rint(x: float) -> int:
    return int(math.floor(x + 0.5))


def haptic_from(f: dict) -> list[list[int]]:
    # one pulse per quadrant that holds ink, clockwise from top left; length by its share of the ink (10 ms steps);
    # a glyph with enclosed spaces (holes) pauses longer between pulses
    off = 80 if f["holes"] == 0 else 140
    pulses = [[min(220, max(60, 10 * rint((60 + 480 * (qs - 0.1)) / 10))), off] for qs in f["quadrants"] if qs >= 0.1] or [[120, off]]
    seq = []
    for k in range(2 if f["symmetry"] >= 0.85 else 1):
        if k:
            seq[-1][1] = 160
        seq += [list(p) for p in pulses]
    if f["density"] >= 0.25:
        seq.append([40, 80])
    out, t = [], 0
    for on, off in seq:
        if t + on > 2000:
            break
        out.append([on, off])
        t += on + off
    out[-1][1] = 0
    return out


def tone_from(f: dict) -> list[list[float]]:
    # the strongest directions of the ink from the centre, strongest first (2–4 notes); a direction holding
    # much of the ink sounds longer
    tot = sum(f["angles"]) or 1.0
    rank = sorted(range(7), key=lambda b: (-f["angles"][b], b))
    k = max(2, min(4, sum(1 for b in range(7) if f["angles"][b] >= 0.6 * f["angles"][rank[0]])))
    notes = [[PENTATONIC[b], 240 if f["angles"][b] / tot >= 0.22 else 180 if f["angles"][b] / tot >= 0.12 else 140] for b in rank[:k]]
    if f["symmetry"] >= 0.85:
        notes.append([round(notes[0][0] * 2, 2), 260])
    return notes


def png_data(img: Image.Image, colour: bool) -> str:
    if not colour:   # monochrome glyphs are stored as a white mask so pages can colour them
        a = img.getchannel("A")
        img = Image.merge("RGBA", (Image.new("L", img.size, 255),) * 3 + (a,))
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def build_originals() -> dict:
    cmaps = _cmaps()
    glyphs = []
    for i, g in enumerate(collect(), start=1):
        mask, img, colour = render(g["char"], cmaps)
        f = features(mask)
        glyphs.append(dict(id=f"O{i:03d}", kind="original", char=g["char"], name=" ".join(unicodedata.name(c, "?").title() for c in g["char"] if c not in JOINERS),
                           colour=colour, png=png_data(img, colour), haptic=haptic_from(f), tone=tone_from(f),
                           features=dict(parts=f["parts"], symmetry=f["symmetry"], density=f["density"]),
                           tiers=g["tiers"], parents=g["parents"], children=g["children"]))
    by = {g["char"]: g["id"] for g in glyphs}
    defaults = {"LION": by.get("🦁"), "DRAGON": by.get("🐉")}
    hap = {json.dumps(g["haptic"]) for g in glyphs}
    ton = {json.dumps(g["tone"]) for g in glyphs}
    return dict(format=FORMAT, source="Tier ledger (spec/TIER_LEDGER.md)", glyphs=glyphs,
                archetype_defaults={k: v for k, v in defaults.items() if v},
                stats=dict(glyphs=len(glyphs), occurrences=sum(len(g["tiers"]) for g in glyphs),
                           mutations=sum(len(g["children"]) for g in glyphs), distinct_haptic=len(hap), distinct_tone=len(ton),
                           distinct_both=len({json.dumps([g["haptic"], g["tone"]]) for g in glyphs})))


def main():
    data = build_originals()
    (ROOT / "docs" / "ugcl" / "originals.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    s = data["stats"]
    lines = ["# UGCL original glyphs (from the tier ledger)", "",
             f"- Glyphs: {s['glyphs']} distinct glyphs recorded in tier glyph fields and glyph mutations, {s['occurrences']} tier occurrences, {s['mutations']} recorded mutations between different glyphs.",
             f"- Distinct vibration rhythms: {s['distinct_haptic']}; distinct melodies: {s['distinct_tone']}; distinct rhythm-and-melody pairs: {s['distinct_both']}.",
             f"- Archetype glyphs taken from the ledger: " + ", ".join(f"{k} {next(g['char'] for g in data['glyphs'] if g['id'] == v)} ({v})" for k, v in data["archetype_defaults"].items()) + ".",
             "", "| Id | Glyph | Tiers | First tier | Mutated from | Mutated into |", "|---|---|---|---|---|---|"]
    for g in data["glyphs"]:
        lines.append(f"| {g['id']} | {g['char']} | {len(g['tiers'])} | {g['tiers'][0]['number']} | {' '.join(sorted({p['char'] for p in g['parents']}))} | {' '.join(sorted({c['char'] for c in g['children']}))} |")
    (ROOT / "rsso" / "results" / "ugcl_originals.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:5]))


if __name__ == "__main__":
    main()
