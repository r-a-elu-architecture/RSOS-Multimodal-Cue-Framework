"""Builds the UGCL glyph library: a grammar of glyphs, evolved by mutation with full genealogy, from which
the most mutually distinct glyphs are selected.

Why distinctness: a glyph is a conditioned cue. Cues that look, feel or sound alike generalise into each
other, so every glyph in the library is chosen to be as different as possible from the others across all
three forms: shape (chamfer distance between renderings), haptic rhythm and tone motif.

  python -m rsso.ugcl_library            # writes docs/ugcl/library.json, docs/ugcl/genealogy.json, rsso/results/ugcl_library.md
"""
from __future__ import annotations

import json
import math
import pathlib
import random

import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt, label

from .ugcl import FORMAT, expand, haptic_signature, stroke_length, tone_motif, validate

ROOT = pathlib.Path(__file__).resolve().parents[2]
GRID = [x / 4 for x in range(-4, 5)]          # coordinates snap to quarters
RADII = [0.25, 0.5, 0.75]
ANGLES = list(range(0, 360, 45))
RES = 64


def random_stroke(rng: random.Random) -> dict:
    k = rng.choices(["L", "A", "C", "D"], weights=[5, 3, 1.2, 1])[0]
    if k == "L":
        while True:
            p = [rng.choice(GRID) for _ in range(4)]
            if math.hypot(p[2] - p[0], p[3] - p[1]) >= 0.5:
                return {"k": "L", "p": p}
    if k == "A":
        r = rng.choice(RADII); a0 = rng.choice(ANGLES); span = rng.choice([90, 135, 180, 225, 270])
        return {"k": "A", "p": [rng.choice(GRID[2:7]), rng.choice(GRID[2:7]), r, a0, a0 + span]}
    if k == "C":
        return {"k": "C", "p": [rng.choice(GRID[2:7]), rng.choice(GRID[2:7]), rng.choice(RADII)]}
    return {"k": "D", "p": [rng.choice(GRID[1:8]), rng.choice(GRID[1:8]), 0.1]}


def random_glyph(rng, gid) -> dict:
    return {"id": gid, "sym": rng.choices([1, 2, 3, 4, 5, 6], weights=[2, 2, 2, 2, 1.5, 1])[0], "mirror": rng.random() < 0.4,
            "strokes": [random_stroke(rng) for _ in range(rng.choice([1, 2, 2, 3]))], "parent": None, "op": "seed"}


def mutate(g, rng, gid) -> dict:
    c = json.loads(json.dumps(g)); c.update(id=gid, parent=g["id"])
    op = rng.choice(["add-stroke", "remove-stroke", "change-symmetry", "toggle-mirror", "move-stroke", "replace-stroke"])
    if op == "add-stroke" and len(c["strokes"]) < 4:
        c["strokes"].append(random_stroke(rng))
    elif op == "remove-stroke" and len(c["strokes"]) > 1:
        c["strokes"].pop(rng.randrange(len(c["strokes"])))
    elif op == "change-symmetry":
        c["sym"] = rng.choice([s for s in (1, 2, 3, 4, 5, 6) if s != c["sym"]])
    elif op == "toggle-mirror":
        c["mirror"] = not c["mirror"]
    elif op == "move-stroke":
        s = rng.choice(c["strokes"]); i = rng.randrange(2)
        s["p"][i] = max(-1.0, min(1.0, s["p"][i] + rng.choice([-0.25, 0.25])))
    else:
        op = "replace-stroke"; c["strokes"][rng.randrange(len(c["strokes"]))] = random_stroke(rng)
    c["op"] = op
    return c


def raster(g) -> np.ndarray:
    img = np.zeros((RES, RES), bool)

    def put(x, y):
        i, j = int((1.2 - y) / 2.4 * (RES - 1) + 0.5), int((x + 1.2) / 2.4 * (RES - 1) + 0.5)
        if 0 <= i < RES and 0 <= j < RES:
            img[i, j] = True
    for s in expand(g):
        p = s["p"]
        if s["k"] == "L":
            n = max(2, int(math.hypot(p[2] - p[0], p[3] - p[1]) * 40))
            for t in np.linspace(0, 1, n):
                put(p[0] + t * (p[2] - p[0]), p[1] + t * (p[3] - p[1]))
        elif s["k"] in ("C", "A"):
            a0, a1 = (0, 360) if s["k"] == "C" else (p[3], p[4])
            for a in np.linspace(a0, a1, max(8, int(abs(a1 - a0) / 4))):
                put(p[0] + p[2] * math.cos(math.radians(a)), p[1] + p[2] * math.sin(math.radians(a)))
        else:
            for a in range(0, 360, 30):
                for rr in (0.0, 0.05, 0.1):
                    put(p[0] + rr * math.cos(math.radians(a)), p[1] + rr * math.sin(math.radians(a)))
    return img


def chamfer(a: np.ndarray, b: np.ndarray, da=None, db=None) -> float:
    da = distance_transform_edt(~a) if da is None else da
    db = distance_transform_edt(~b) if db is None else db
    return float((db[a].mean() + da[b].mean()) / 2) / RES


def haptic_vec(g) -> np.ndarray:
    v = np.zeros(200)
    t = 0
    for on, off in haptic_signature(g):
        v[t // 10: min(200, (t + on) // 10)] = 1; t += on + off
    return v


def tone_dist(a, b) -> float:
    x, y = [n[0] for n in tone_motif(a)], [n[0] for n in tone_motif(b)]
    d = np.zeros((len(x) + 1, len(y) + 1)); d[:, 0] = range(len(x) + 1); d[0, :] = range(len(y) + 1)
    for i in range(1, len(x) + 1):
        for j in range(1, len(y) + 1):
            d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1, d[i - 1, j - 1] + (x[i - 1] != y[j - 1]))
    return d[-1, -1] / max(len(x), len(y))


def points(g):
    pts = []
    for s in expand(g):
        p = s["p"]
        if s["k"] == "L":
            pts += [(p[0], p[1]), (p[2], p[3])]
        elif s["k"] in ("C", "A"):
            a0, a1 = (0, 360) if s["k"] == "C" else (p[3], p[4])
            pts += [(p[0] + p[2] * math.cos(math.radians(a)), p[1] + p[2] * math.sin(math.radians(a))) for a in np.linspace(a0, a1, 24)]
        else:
            pts.append((p[0], p[1]))
    return np.array(pts)


def acceptable(g) -> bool:
    """A usable cue: valid, within the frame, centred, filling the space, cohesive, not cluttered."""
    try:
        validate(g)
    except ValueError:
        return False
    n = len(expand(g))
    if not 2 <= n <= 16 or sum(stroke_length(s) for s in g["strokes"]) <= 0.4:
        return False
    pts = points(g)
    if np.abs(pts).max() > 1.05 or np.ptp(pts[:, 0]) < 1.0 or np.ptp(pts[:, 1]) < 1.0:
        return False
    img = raster(g)
    ink = img.mean()
    if not 0.02 <= ink <= 0.12:
        return False
    ys, xs = np.nonzero(img)
    if abs(xs.mean() / (RES - 1) - 0.5) > 0.08 or abs(ys.mean() / (RES - 1) - 0.5) > 0.08:
        return False
    parts = label(binary_dilation(img, iterations=2))[1]
    return parts <= 2


def build(population=600, select=48, seed=7):
    rng = random.Random(seed)
    pop = [g for g in (random_glyph(rng, f"s{k:03d}") for k in range(3000)) if acceptable(g)][:12]
    k = 0
    while len(pop) < population:
        child = mutate(rng.choice(pop), rng, f"m{k:05d}"); k += 1
        if acceptable(child):
            pop.append(child)
    imgs = [raster(g) for g in pop]
    dts = [distance_transform_edt(~im) for im in imgs]
    hv = [haptic_vec(g) for g in pop]
    # farthest-point selection on combined distance
    chosen = [0]
    dmin = np.full(len(pop), np.inf)
    while len(chosen) < select:
        c = chosen[-1]
        for i in range(len(pop)):
            if np.isfinite(dmin[i]) and dmin[i] == 0:
                continue
            d = chamfer(imgs[c], imgs[i], dts[c], dts[i]) + 0.05 * np.abs(hv[c] - hv[i]).mean() + 0.03 * tone_dist(pop[c], pop[i])
            dmin[i] = min(dmin[i], d)
        dmin[chosen] = 0
        chosen.append(int(np.argmax(dmin)))
    by_id = {g["id"]: g for g in pop}

    def lineage(g):
        out = []
        while g is not None:
            out.append({"id": g["id"], "op": g["op"]}); g = by_id.get(g["parent"])
        return out[::-1]
    lib = []
    for n, i in enumerate(chosen, 1):
        g = dict(pop[i]); g["source_id"] = g.pop("id"); g["id"] = f"G{n:02d}"; g["lineage"] = lineage(pop[i])
        g.pop("parent"); g.pop("op")
        lib.append(g)
    # pairwise minimum distance of the selected set, per form
    sel = [pop[i] for i in chosen]
    vis = [[chamfer(imgs[a], imgs[b], dts[a], dts[b]) for b in chosen] for a in chosen]
    min_vis = min(vis[a][b] for a in range(select) for b in range(select) if a != b)
    rand = random.Random(1).sample(range(len(pop)), select)
    rvis = min(chamfer(imgs[a], imgs[b], dts[a], dts[b]) for a in rand for b in rand if a != b)
    return lib, pop, {"population": len(pop), "selected": select, "min_visual_distance_selected": min_vis,
                      "min_visual_distance_random_set": rvis, "distinct_haptic": len({json.dumps(haptic_signature(g)) for g in sel}),
                      "distinct_tone": len({json.dumps(tone_motif(g)) for g in sel})}


def archetype_defaults(lib) -> dict:
    """Not used for the published library: archetype glyphs come from the tier ledger. Kept for reference.
    Starting glyph per archetype, by shape character (each person can recalibrate):
    Lion radiant (high symmetry), Eagle winged (mirrored, low symmetry), Bear solid (4-fold),
    Leopard agile (3-fold), Raven pointed (mirrored with a dot), Tiger striped (2-fold, lines)."""
    used, out = set(), {}
    rules = [
        ("LION", lambda g: g["sym"] >= 5),
        ("EAGLE", lambda g: g["mirror"] and g["sym"] == 1),
        ("BEAR", lambda g: g["sym"] == 4),
        ("LEOPARD", lambda g: g["sym"] == 3),
        ("RAVEN", lambda g: g["mirror"] and any(s["k"] == "D" for s in g["strokes"])),
        ("TIGER", lambda g: g["sym"] == 2 and all(s["k"] == "L" for s in g["strokes"])),
    ]
    for name, rule in rules:
        pick = next((g for g in lib if g["id"] not in used and rule(g)), None) or next(g for g in lib if g["id"] not in used)
        used.add(pick["id"]); out[name] = pick["id"]
    return out


def main():
    lib, pop, stats = build()
    defaults = {}   # archetype glyphs come from the tier ledger (docs/ugcl/originals.json); this set is optional
    out = ROOT / "docs" / "ugcl"; out.mkdir(parents=True, exist_ok=True)
    (out / "library.json").write_text(json.dumps({"format": FORMAT, "glyphs": lib, "archetype_defaults": defaults,
                                                  "stats": stats}, indent=1) + "\n", encoding="utf-8")
    (out / "genealogy.json").write_text(json.dumps({"format": FORMAT, "glyphs": [{k: g[k] for k in ("id", "parent", "op")} for g in pop]})
                                        + "\n", encoding="utf-8")
    rep = ROOT / "rsso" / "results" / "ugcl_library.md"
    rep.write_text("\n".join([
        "# UGCL glyph library build", "",
        f"- Population evolved by mutation from seed glyphs: {stats['population']} glyphs, each with its parent and mutation recorded.",
        f"- Selected for maximal mutual distinctness: {stats['selected']} glyphs (G01–G{stats['selected']:02d}).",
        f"- Smallest visual distance between any two selected glyphs: {stats['min_visual_distance_selected']:.4f} "
        f"(a random set of the same size: {stats['min_visual_distance_random_set']:.4f}).",
        f"- Distinct haptic rhythms among the selected: {stats['distinct_haptic']} of {stats['selected']}; distinct tone motifs: {stats['distinct_tone']} of {stats['selected']}.",
        "- Archetype glyphs come from the tier ledger (the original glyphs, `docs/ugcl/originals.json`); this generated set is an optional extra.",
        "", "Visual distance is the symmetric chamfer distance between 64×64 renderings, as a fraction of the image width."]) + "\n",
        encoding="utf-8")
    print(rep.read_text())


if __name__ == "__main__":
    main()
