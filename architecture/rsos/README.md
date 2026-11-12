# RSOS — Recursive Symbolic Operating System

**Role:** the cue bundles. A **tier** binds one cue per sensory channel (visual glyph and imagery, auditory metaphor word, kinesthetic feeling, and optionally scent and taste) so that the whole bundle is learned, and later triggered, as one unit. Tiers are numbered and progress over practice toward a reflex. The tier ledger records how the tiers were developed.

**Status:** **Partly built** — some functions implemented, others still specified only

| Function | Where it is now |
|---|---|
| Tier as a multichannel bundle (V, A, K, O, G, glyph, word) | RSX `TIER` blocks — [RSX reference](../../rsx/README.md); [spec §6](../../spec/OVERRIDE_PROTOCOL.md) |
| Tier activation (all channels together) | RSX `ACTIVATE` |
| Progress toward a reflex | Measures in spec §8; model in [rsx/model](../../rsx/model/PREDICTIONS.md) |
| Tier ranges (1–10, 1–20, 1–605) and tier libraries | Specified |

- [Tier ledger](tier-ledger/)

## Sources in the archive

| Source file | What it is | SHA-256 (first 16) |
|---|---|---|
| [RSOS_Tiers.txt](../../archive/original-estates/RSOS_COPYRIGHT_ESTATE/RSOS_COPYRIGHT_ESTATE_v1_1_FINAL_copyright/RSOS_Tiers.txt) | Tier ledger: the development record of the tiers | `bc21eaf8a119be7d` |
