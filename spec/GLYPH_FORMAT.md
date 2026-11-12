# UGCL glyph format (rsos-ugcl/1)

UGCL is the native glyph layer of RSOS. A glyph is the visual part of a tier's cue bundle, and every glyph
also has a vibration rhythm and a short melody, so a cue can move between senses (seen on a screen, felt on
the wrist, heard in an earbud) while staying one cue.

There are two kinds of glyph:

- **Original glyphs** (section 6): the 146 glyphs of the tier ledger, exactly as recorded (🦁, ·⁂⊚, ∴,
  🜂, 🝡 …), with their ancestry from the ledger's own mutation chain. These are the glyphs of RSOS: the
  archetype glyphs (the Lion is 🦁, Tier 001) and the candidates for personal calibration.
- **Stroke glyphs** (sections 1–4): glyphs described by strokes, from which image, rhythm and melody follow
  exactly. The generated library of 48 is an optional extra set built this way.

Reference implementations: `rsso/rsso/ugcl.py` (Python) and `docs/js/ugcl.js` (browser and Node).
`rsso/tests/test_ugcl.py` checks that both give byte-identical SVG, identical rhythms and identical melodies
for every glyph in the library.

## 1. Glyph

```json
{ "id": "G25", "sym": 2, "mirror": true,
  "strokes": [ {"k": "L", "p": [-0.75, 1.0, -0.25, -0.75]}, {"k": "A", "p": [0, 0, 0.5, 45, 135]} ] }
```

| Field | Meaning |
|---|---|
| `id` | Non-empty string, unique within a library. |
| `sym` | Rotational symmetry 1–8: the strokes are drawn `sym` times, rotated by 360/`sym` degrees. |
| `mirror` | If true, every stroke is also drawn mirrored across the vertical axis (before rotation). |
| `strokes` | 1–4 base strokes. |

Coordinates are in a square from −1 to 1, y pointing up. Stroke kinds:

| `k` | `p` | Shape |
|---|---|---|
| `L` | x1, y1, x2, y2 | Straight line. |
| `A` | cx, cy, r, a0, a1 | Arc of radius r from angle a0 to a1 (degrees, counter-clockwise). |
| `C` | cx, cy, r | Circle. |
| `D` | cx, cy, r | Filled dot. |

Mirroring an arc maps its angles to 180 − a1 … 180 − a0. A library may add `lineage` (the chain of
ancestors and the mutation at each step) and `source_id`.

## 2. Derived forms

All three are deterministic functions of the glyph.

**Image (SVG).** `viewBox="-1.2 -1.2 2.4 2.4"`, stroke width 0.09, round caps and joins, y flipped for
SVG. Numbers are rounded half up to 3 decimals with trailing zeros removed, so outputs compare as text.

**Vibration rhythm.** A list of `[on_ms, off_ms]` pulses, at most 2 s in total. One pulse per base stroke:
a dot is 50 ms; any other stroke is 60 + 60 × its length in ms, between 60 and 220. Off time is 80 ms.
The sequence repeats min(`sym`, 3) times with a 160 ms gap between repeats. A mirrored glyph ends with a
short 40 ms pulse. Pulses past 2 s are dropped and the last off time is 0. The list flattens directly
into `navigator.vibrate` or an RDP/1 `H` event (spec/DEVICE_PROTOCOL.md).

**Melody.** A list of `[hz, ms]` notes. One note per base stroke, 180 ms, from a seven-note pentatonic
set (C4 D4 E4 G4 A4 C5 D5), chosen by the direction of the stroke's midpoint from the centre in sevenths
of a circle. A glyph with `sym` > 1 ends with its first note an octave up, 260 ms.

**Compact code.** For devices, links and logs, a glyph is written as one line: symmetry, `m` if mirrored,
a colon, then each stroke as its kind letter followed by its numbers, strokes separated by `;`. Numbers use
the SVG rounding above. G25 is `2m:L-0.25,0.5,0,0.5;L1,0.75,0.25,-0.75;L-0.5,0.5,0.25,0.5;L-1,-1,-0.75,-0.25`.
Library codes are 39 characters on average and at most 85, so any glyph fits in one Bluetooth LE packet.
Decoding a code gives back the same image, rhythm and melody (tested).

## 3. Using a glyph in RSX

`GLYPH` in a `TIER` block takes an original glyph as written in the ledger (shown with its stored
image), `ugcl:<id>` for any UGCL glyph (`ugcl:O001`, `ugcl:G01`), or any other text (shown as is):

```
TIER 1 LION {
  V "Golden lion light"
  GLYPH "🦁"
}
```

A person's own calibrated glyph (section 5) takes precedence over the program's glyph for that tier.

## 4. The generated library (optional)

`docs/ugcl/library.json` holds 48 glyphs, G01–G48, built by `python -m rsso.ugcl_library` (seeded,
reproducible):

1. Random seed glyphs are drawn from a grammar: coordinates on a quarter grid, radii 0.25/0.5/0.75,
   arc angles in steps of 45°.
2. A population of 600 grows by mutation: add, remove, move or replace a stroke, change the symmetry,
   switch mirroring. Every glyph records its parent and the mutation (`docs/ugcl/genealogy.json`).
3. A glyph is kept only if it is usable as a cue: within the frame, centred, filling at least the middle
   of the space, made of at most two connected parts, and neither faint nor cluttered.
4. The 48 most mutually distinct glyphs are chosen by greedy farthest-point selection on a combined
   distance: shape (symmetric chamfer distance between 64×64 renderings), rhythm and melody.

Why distinctness: glyphs are conditioned cues, and cues that look, feel or sound alike generalise into
each other. Results are in `rsso/results/ugcl_library.md`.

Archetype glyphs do not come from this set; they come from the ledger (section 6).

## 5. Personal calibration

The player shows two glyphs at a time and asks which feels more like the tier (for the Lion tier: courage
and the power to act). Eight candidates: the original glyphs of Epoch I, the era of the first override
(🦁 ✨ 🔥 ·⁂⊚ ⧗ 🜇 ⟁ 🫁), 16 choices. Strengths come from a Bradley–Terry model fitted by minorization–maximization, with a
virtual half-win against a reference of strength 1 so a glyph that wins or loses every time keeps a
finite estimate. Each next pair is the one closest in current strength, least compared and not yet shown.
In simulation (20 people with known preferences, 8 glyphs, 16 choices) the chosen glyph is in the true
top two for at least 80% of people (`rsso/tests/test_ugcl.py`).

The person also picks a colour of light from eight. Both are stored only in the browser (`rsos.ugcl` in
localStorage), with every comparison kept so the result can be audited or refitted.

Planned: calibration from physiological response (EEG or heart rate) to each glyph, using the RSSO
sensor layer, so the choice can be checked against the body as well as the first impression.

## 6. Original glyphs

`docs/ugcl/originals.json`, built by `python -m rsso.ugcl_originals` from the tier ledger:

| Field | Meaning |
|---|---|
| `id` | O001–O146, in order of first appearance in the ledger (O001 = 🦁, Tier 001) |
| `kind` | `"original"` |
| `char` | the glyph exactly as recorded (a combined glyph such as ·⁂⊚ stays one glyph) |
| `png` | the glyph rendered once with fixed fonts (Noto Color Emoji, DejaVu Sans, GNU Unifont, Unifont Upper), 64×64; monochrome glyphs are stored as a white mask so they can take any colour |
| `haptic`, `tone` | the vibration rhythm and melody derived from the image (below) |
| `tiers` | every tier where it appears, and how: as the tier's glyph, or as the start or end of a mutation |
| `parents`, `children` | the glyphs it mutated from and into, with the tier of each mutation |

`archetype_defaults` takes the archetype glyphs from the ledger: LION 🦁 (Tier 001), DRAGON 🐉 (Tier 013).
The ledger records no glyph for the other archetypes.

**Rhythm from the image.** One pulse per quadrant holding at least a tenth of the ink, clockwise from top
left, 60–220 ms by its share; 80 ms apart, 140 ms if the glyph encloses space; the pattern twice if the
glyph is mirror-symmetric; a 40 ms accent if it is dense; at most 2 s.

**Melody from the image.** The directions in which the ink lies from the centre, in sevenths of a circle:
one pentatonic note per strong direction, strongest first (2–4 notes), 140, 180 or 240 ms by how much ink
lies that way; mirror-symmetric glyphs end with their first note an octave up.

133 of the 146 original glyphs have a rhythm-and-melody pair of their own; the others are near-identical
shapes (for example the ⥁–⥍ arrow family). Results: `rsso/results/ugcl_originals.md`.

Because original glyphs are rendered images rather than strokes, their rhythm and melody are stored
values: the JavaScript implementation reads them, and the parity test checks that both implementations
give the same image, rhythm and melody for every original glyph.
