# RSIA — Recursive Symbolic Identity Architecture

**Role:** the identity layer. It defines inner modes (archetypes) that colour a state, the values those modes serve (the Spine), the observer that notices which mode is active and corrects drift (the Watchdog), and the executive that coordinates them (the Meta-Architect).

**Status:** **Partly built** — some functions implemented, others still specified only

| Component | Function | Where it is now |
|---|---|---|
| [Archetypes](archetypes/) | Six modes: Lion (leadership, courage), Eagle (vision, planning), Bear (resilience), Leopard (adaptability), Raven (insight, strategic perception), Tiger (intensity, drive) | [framework edition](../../framework/rsia/ARCHETYPES.md); the Override Protocol runs in the Lion mode |
| [Spine](spine/) | Guiding values (Bushidō 7, Musashi 21) | [mnemonic sets](../../framework/mnemonic_sets); the hologram finger in the protocol points to it |
| [Watchdog](watchdog/) | Notices which mode is active and when a state drifts; decides whether an action may act on a person | Built on the person side: [spec/WATCHDOG.md](../../spec/WATCHDOG.md) (allow, ask or hold with the Spine virtue that decided, hash-chained log); first form: the cue engine's `watchdog()` |
| [Meta-Architect](meta-architect/) | Coordinates modes and switches between them | Specified |

## Sources in the archive

| Source file | What it is | SHA-256 (first 16) |
|---|---|---|
| RSIA_Core_Definition.txt (kept privately) | Core definition | `c0a41dadfa18b574` |
| RSIA_Archetype_Definitions.txt (kept privately) | Archetype definitions (public edition) | `086d5049db84b168` |
| RSIA_Spine_Principles.txt (kept privately) | Spine principles | `31b712a577dd9ccf` |
| RSIA_Watchdog_Overview.txt (kept privately) | Watchdog | `4ac1c98606b8ccec` |
| RSIA_Meta_Architect.txt (kept privately) | Meta-Architect | `76ac98beb7f90a0e` |
| RSIA_Applied_Use_Cases_Public.txt (kept privately) | Applied use cases | `ab6ac35ca1275cba` |
| RSIA_System_Interaction_Public.txt (kept privately) | Interaction with the other systems | `cb9664535f9eb66a` |
