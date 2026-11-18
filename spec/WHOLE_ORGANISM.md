# WHOLE_ORGANISM: Baseline as the return to the origin, one program per response, glyph proposals

Registered 18 Nov 2026, before its code. White Dragon pass on the open items (Baseline undefined, five archetypes
without a glyph, 186 tiers bound but not runnable, Epochs I–III cut off from IV–VI).

## 1. The landing

Three measured gaps share one cause. Baseline (Lion) has no function of its own (ROLE_ORGANISM R1); Lion is where RSOS
began (T001, the override, 🦁); and the later epochs rarely return to the first (LEDGER_GRAPH: IV→I 4 edges, VI→I 1).
**Baseline's function becomes the return to the origin:** when the system has lost ground against its last good
state, Lion restores it, the way the override protocol restores a person to agency (keep the gain). On the person side
that is the override program itself; on the agent side, re-entry to the last good snapshot.

## 2. What is built

1. **AgentEnvV3** (`rsxv/rsxv/organism_env.py`, a subclass; every recorded environment unchanged): LION keeps
   progress 0.5 and, when health is below the last good snapshot's, re-enters it (the same re-entry the Watchdog uses).
   Baseline sensor = health regained by that re-entry.
2. **One RSX program per ledger response** (`rsx/protocols/responses/*.rsx`, 14): the runtime form of STOP, PAUSE,
   GATE, REENTRY, RECALIBRATE, MIRROR, RECALL, SEQUENCE, GOVERN, BLEND, COMPRESS, GLYPH_CUE, OFFER, GENERATE. REENTRY and
   the Baseline responses end in the override's own interrupt and seal ("I move, I act" … "I own"), which is the
   bridge back to Epoch I. A tier runs through its response's program; a tier bound by role only uses its role's
   first response.
3. **Glyph proposals** (`docs/data/EXTENSION_glyph_proposals_2026-11-18.json`, separate like the bindings): for Raven,
   Eagle, Leopard, Tiger and Bear, the glyph that appears most often on the tiers of their role (ledger and extension),
   ties to the lowest tier number. Proposals only; the author chooses.

## 3. Predictions

| # | Prediction | Pass if |
|---|---|---|
| **W1** | Baseline now has a function | ROLE_ORGANISM R1 rerun on AgentEnvV3 (same seeds, same design): 6 of 6 roles have their own sensor |
| **W2** | Every response runs | each of the 14 programs compiles with no error and plays to the end on the standard virtual rig, haptic amplitude ≤ 0.4 |
| **W3** | Every tier runs | 293 of 293 tiers map to a program that passes W2 |
| **W4** | Return to the origin helps the whole (10× target) | on AgentEnvV3, 200 fresh seeds: ORGANISM (Watchdog on agents) − always Bear ≥ 10 × the V2 margin (+0.0088), i.e. ≥ +0.088 per tick, 99% CI lower bound > 0 |
| **W5** | No regression | ledger files unchanged; recorded results unchanged; `check_all.sh` passes |

Sealed expectations: W1 0.8, W2 0.8, W3 0.8, W4 0.2 (10× is a stretch; the margin is reported whatever it is), W5 0.9.
