# RSX-V — RSX vector commands

**Role:** the command layer above RSX. An RSX-V command is a typed, staged and audited set of vector operators; it compiles into an RSX cue program, which compiles into a timeline and device lines. One program therefore exists in three forms: a vector command, a cue program and device lines.

**Status:** **Built** — working, tested code in this repository. Every result comes from simulation, the firmware core in the host simulator or hand-coded validation sets; none comes from people ([rsxv/RESULTS.md](../../../rsxv/RESULTS.md)).

| Part | What it does |
|---|---|
| Typed vectors | 34 operators (the canonical 17-vector set, extended operators, Vector 0 NullSafe and layer-filling operators), each typed by the cognitive layer it acts on (C1–C11) |
| Staged, closed-loop execution | A gate first; phases with conditions on body state and layer activation; at most 17 vectors at once |
| Laws | Ten laws, among them InteractionMatrix, ChronoGate, GhostPass (a simulation before every live run), ConsentStack, NullSafe and ResonanceAudit (a hash-chained log) |
| Measurement and NEXT | Every vector audited; operational definitions for six RSOS metrics; NEXT writes the successor command from the measured result and upgrades v1 commands |
| Translator and bridge | A message becomes vectors and a complete command, with lineage to the clause each operator came from; the bridge compiles to RSX, so the RSX compilers, the player, the device protocol and their safety limits apply unchanged |
| Archetype agents | Agents governed by the same Spine (7 virtues, 21 precepts) and Watchdog as the person side, with a hash-chained audit log and a repair loop ([rsxv/AGENTS.md](../../../rsxv/AGENTS.md)) |

- Specification: [rsxv/SPEC.md](../../../rsxv/SPEC.md)
- Overview and quick start: [rsxv/README.md](../../../rsxv/README.md)
- Results, with what they do and do not show: [rsxv/RESULTS.md](../../../rsxv/RESULTS.md)
- Agents: [rsxv/AGENTS.md](../../../rsxv/AGENTS.md)

Scope: no electrical stimulation; it is refused at compile time.

## Sources in the archive

| Source file | What it is | SHA-256 (first 16) |
|---|---|---|
| [RSX-Command_Specification.txt](../../../archive/original-estates/RSX_COPYRIGHT_ESTATE/BRANCH_B_CLAIMED_COPYRIGHT/RSX-Command_Specification.txt) | Command specification: the v1 vector commands RSX-V extends | `22422bb3e85e8b79` |
