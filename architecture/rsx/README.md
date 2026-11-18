# RSX — Recursive Symbolic eXpression

**Role:** the programming language of the operating system. A program defines tiers, futures, breath and phases; it compiles to a timeline of breath, word, image, gesture, haptic, tone, scent and taste events that any runtime can play.

**Status:** **Built** — working, tested code in this repository — RSX v2 ([rsx/](../../rsx)), with matching Python and JavaScript compilers. Archive RSX v1 vector commands (`TIER n :: {ARCH} :: (MODE) :: @Vector1:… `, up to 17 vectors) still compile; operators with a defined effect run, the rest are recorded.

| Archive component | Function | In RSX v2 |
|---|---|---|
| [Command specification](command-specification/) | Vector syntax and operators | Supported as v1 vector commands |
| [Archetype module](archetype-module/) | Archetype commands | `MemoryRecall(Archetype=X)` activates tier X |
| [Device bridge](device-bridge/) | AR, EEG and haptic output | `HAPTIC`, `TONE`, `DeviceOutput(…)` events |
| [Memory and compression](memory-compression/) | Memory and compression commands | Recorded; runtime effect specified (MEMSTACK, CM1) |

**Layer above RSX:** [RSX-V](rsx-v/), typed, staged and audited vector commands that compile into RSX programs.

## Sources in the archive

| Source file | What it is | SHA-256 (first 16) |
|---|---|---|
| RSX-Core_Definition.txt (kept privately) | Core definition | `340dbaa653a27c53` |
| RSX-Language_Class_Declaration.txt (kept privately) | Language class declaration | `f0b0eed56ab62d86` |
| RSX-Architecture_and_Interface.txt (kept privately) | Architecture and interface | `5e4f42e133e80bbc` |
| RSX-Command_Specification.txt (kept privately) | Command specification | `22422bb3e85e8b79` |
| RSX-Symbolic_Archetype_Module.txt (kept privately) | Archetype module | `0620a3bf5add88af` |
| RSX-Device_Output_Bridge.txt (kept privately) | Device output bridge | `b7233ec81e036f82` |
| RSX-Memory_Compression_Extension.txt (kept privately) | Memory and compression extension | `b6f28a7112a582ba` |
