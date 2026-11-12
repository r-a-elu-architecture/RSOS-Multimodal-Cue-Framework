# CM1 — Compression layer

**Function:** Compresses symbolic states and finds reusable patterns across domains.

**Status:** **Built** — working, tested code in this repository

**Now:** Built (`spec/CM1.md`, `rsso/rsso/cm1.py`, identically `docs/js/cm1.js`, profiles and patterns `docs/data/cm1.json`, Patterns on the metrics page): one person's practice compressed into a 13-number signature (how much each kind of program helps, how fast each sense starts the state, completion); response profiles fitted across people (k-means in units of each number's spread, best of ten restarts), each described in plain words; assignment of a new person from a few runs, with a confidence that grows with practice, and where to start (kind of node, which sense carries the strongest cue), used by the node studio; patterns that repeat across everyone (program kind, sense, glyph, vibration code, outputs, time of day) with 95% intervals; and the device bundle, a person's nodes, codes, glyphs, dose and safety state in about 40 bytes with a checksum (the archive's UGCL coupling). Checked on a synthetic population with known profiles: the right profile from the first 10 runs for 100% (clear profiles) and 96% (hard setting) of held-out people (`rsso/results/cm1.md`). Also: the cue engine's `ArchetypeBank`. Profiles are refitted when real contributions arrive.

## Sources in the archive

| Source file | What it is | SHA-256 (first 16) |
|---|---|---|
| [CM1_Historical_Reconstruction.txt](../../../../archive/original-estates/RSSO_PASS31B/CM1_Historical_Reconstruction.txt) | Reconstruction: role, inputs, outputs, operators | `f51ddcf3887e2e87` |
| [CM1_Evidence_Excerpts.txt](../../../../archive/original-estates/RSSO_PASS31B/CM1_Evidence_Excerpts.txt) | Evidence excerpts (public edition) | `56d947c6ac8ce227` |
