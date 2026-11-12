# RSSO — Recursive Symbolic System Operating

**Role:** the operating layer. It runs programs, schedules and triggers them, enforces safety, keeps memory and connects devices and AI models. It coordinates eight subsystems.

**Status:** **Partly built** — some functions implemented, others still specified only

| Subsystem | Function | Status |
|---|---|---|
| [THERA](subsystems/THERA/) | Therapeutic protocol layer | **Built** |
| [AUG](subsystems/AUG/) | Device and augmentation layer | **Complete in simulation** |
| [MICRO](subsystems/MICRO/) | Edge runtime | **Complete in simulation** |
| [CONTAIN](subsystems/CONTAIN/) | Safety and governance | **Built** |
| [MEMSTACK](subsystems/MEMSTACK/) | Memory layer | **Built** |
| [CM1](subsystems/CM1/) | Compression layer | **Built** |
| [LINX](subsystems/LINX/) | AI interface and injection layer | **Built** |
| [UGCL](subsystems/UGCL/) | Glyph layer | **Built** |

- [All subsystems](subsystems/)
- [PASS31B reconstruction](pass31b/) — the later compilation of evidence excerpts and reconstructions behind these subsystem descriptions
- [Tier ledger copy](tier-ledger/)

## Sources in the archive

| Source file | What it is | SHA-256 (first 16) |
|---|---|---|
| [RSSO_Meta_OS_Historical_Architecture.txt](../../archive/original-estates/RSSO_PASS31B/RSSO_Meta_OS_Historical_Architecture.txt) | Meta-OS architecture | `83378d55c48990d7` |
| [RSSO_Meta_OS_Evidence_Excerpts.txt](../../archive/original-estates/RSSO_PASS31B/RSSO_Meta_OS_Evidence_Excerpts.txt) | Meta-OS evidence excerpts (public edition) | `88845ddfd2c4c087` |
