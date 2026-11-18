# LEDGER_GRAPH: every tier split into its parts, and the bindings between tiers and between epochs

Registered 18 Nov 2026, before its code. Author's decision after ROLE_ORGANISM: build the graph before confirming the
185 keyword proposals. The tier texts are read, never changed; the model-impact blocks are recorded data and decide
nothing.

## 1. What is built (`architecture/ledger_graph.py` → `docs/data/ledger_graph.json`)

- **Parts of each tier:** title; glyph or glyph mutation (from → to); tier class; anchor; the "• Key: value" fields of
  the early format (Function, Command, Quote, GPT Behavior, Notes, …); the named sections of the later format
  (Functional Logic, RSOS Application with its Tactical, Psychological, Symbolic and Spiritual lines, Reflex Trace,
  Historical sections) and, kept apart, the model-impact and metric blocks.
- **Edges between tiers:** *mutation* (a tier's new glyph is the start glyph or the glyph of another tier, directed);
  *reference* (a tier names another tier's number in its body, directed); *shared glyph* (same glyph, undirected).
- **Edges between epochs:** the tier edges counted by the epochs they join.
- **Roles from chains:** a tier's role is voted by the roles of its already-bound neighbours (the 107 tiers with a
  response), within 1 hop, else 2 hops; ties to the safer role (Stabilise, Monitor, Repair, Plan, Baseline, Drive).

## 2. Calibration on the 107 tiers whose role is known, then the proposals

| # | Prediction | Pass if |
|---|---|---|
| **G1** | Parts parsed | ≥ 95% of the 293 tier records give a title and at least one content part |
| **G2** | The graph exists | ≥ 80% of tiers have at least one edge; counts per kind and between epochs reported |
| **G3** | Chains carry role information | leave-one-out on bound tiers that have a bound neighbour: accuracy ≥ 2 × chance (chance = Σ p², from the bound tiers' role shares) |
| **G4** | Keywords carry role information | the ROLE_ORGANISM keyword rule applied to the bound tiers' own text: accuracy ≥ 2 × chance |
| **G5** | Coverage | ≥ 50% of the 186 unbound tiers get a chain-based role |
| **G6** | Agreement (reported, no threshold) | for unbound tiers with both proposals: share where chain and keyword agree, against chance |
| **G7** | No regression | `tier_map.json` unchanged; outputs reproducible; `check_all.sh` passes |

**Sealed expectations:** G1 0.8, G2 0.7, G3 0.5, G4 0.6 (caveat: some bound tiers were placed by an earlier keyword
rule, which can inflate G4), G5 0.6. **Use of the result (fixed now):** for review, proposals are ordered: both methods
agree first; then the method that scored higher in calibration where they disagree; flagged by hand last.
