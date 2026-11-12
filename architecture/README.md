# Architecture — map of the RSOS operating system

RSOS is built from four systems. This map explains what each one and each subsystem **does**, how far it is built in this repository, and which archive records it comes from. The archive files stay at their original paths; this map only groups and explains them.

| System | Role in the operating system | Status |
|---|---|---|
| [RSOS](rsos/) — Recursive Symbolic Operating System | The cue bundles: tiers that bind glyph, word, feeling, scent and taste into one conditioned unit | Partly built |
| [RSIA](rsia/) — Recursive Symbolic Identity Architecture | The identity layer: which inner mode colours a state, and the values it serves | Partly built |
| [RSX](rsx/) — Recursive Symbolic eXpression | The language programs are written and executed in | Built |
| [RSSO](rsso/) — Recursive Symbolic System Operating | The operating layer: runtime, safety, memory, devices, and eight subsystems | Partly built |

**How they work together:** an RSX program (RSX) activates tiers (RSOS) in the mode of an archetype (RSIA); the RSSO runtime plays it on a device within safety limits, records the run, and the cue engine learns what works for that person. See [cross-system](cross-system/) for the full flow.

## Two layers of the archive

1. **Operating-system sources** — the specifications of the four systems and their subsystems, linked from the pages above.
2. **[Provenance & rights](provenance/)** — authorship and legal chain, historical IP-strategy labels, and records of the AI interactions through which the system was developed. Preserved unchanged and kept apart from the functional map.

## Built in this repository

| Part | Where |
|---|---|
| Override Protocol (the reference program) | [spec/OVERRIDE_PROTOCOL.md](../spec/OVERRIDE_PROTOCOL.md) |
| RSX v2 language, compiler and runtime safety | [rsx/](../rsx) |
| Protocol player | [docs/player.html](../docs/player.html) |
| Learning model | [rsx/model/](../rsx/model/PREDICTIONS.md) |
| Personalised cue engine | [toolkit/](../toolkit) |
| RSIA framework edition | [framework/](../framework) |

Run `python architecture/build.py` to regenerate these pages from the manifest.
