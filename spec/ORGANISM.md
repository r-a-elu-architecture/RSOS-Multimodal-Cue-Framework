# ORGANISM: the tiers, metrics and Echo metrics as one map, and one fused agent system

Registered 18 Nov 2026, before its code and before any number is computed.

## 1. Planets (the atlas, `architecture/organism.py` → `docs/data/organism.json`)

| Planet | Sub-planet | Sub-sub-planet | Source |
|---|---|---|---|
| **Epochs I–VI** | the tiers of each epoch (placed by the ledger's order of epoch headers and tier records) | each tier's layers, channels, role, response, operator, status | `docs/data/ledger.json`, `docs/data/tier_map.json` |
| **Metrics** | the 6 families | each metric's values per tier and epoch | `docs/data/metrics.json` |
| **Echo metrics** | the family "Language-model claims" (22 metrics: the model-side claims, Echo among them) | values per tier and epoch, and the tier records that name Echo | same files |
| **World agents** | the six roles of the agent system | their archetype and the ledger responses they carry | `rsxv/rsxv/world.py` (AgentEnv) |

**Bindings fixed now (design, stated before computing).** Role ↔ archetype, from `AgentEnv`: Monitor = Raven,
Stabilise = Bear, Plan = Eagle, Repair = Leopard, Drive = Tiger, Baseline = Lion. Role ↔ ledger response (each of the
14 responses to one role): Monitor: MIRROR, RECALL · Stabilise: STOP, PAUSE, GATE, REENTRY · Plan: SEQUENCE, GOVERN ·
Repair: RECALIBRATE, BLEND · Drive: GLYPH_CUE, OFFER · Baseline: COMPRESS, GENERATE. Metric ↔ role is **not** set by
hand: it is read from the data (the roles of the tiers a metric's values sit on).

## 2. The fused agent system (the organism)

AGENTS_ANCHOR found that switching helps agents (Watchdog beats always Bear by +0.0155) and costs persons (always Bear
beats the Watchdog). The organism fuses the measured best of each side, and replaces live exploration on persons with
replay:

- **Person side:** the anchored rule (Bear unless the ledger's interval rules Bear out) with **no live exploration**;
  its ledger starts from **replayed** runs of 50 other persons (seeds 281000–281049, Watchdog policy, model v3), so it
  learns without trying modes on the person.
- **Agent side:** the Watchdog, unchanged.

## 3. Predictions

Person model v3 (R = 6) and `AgentEnvV2`, 120 ticks, mission score, **200 fresh seeds 280000–280199**; paired bootstrap
99% CIs (2,000 resamples, seed 12345). Combined = person score + agent score for the same seed.

| # | Prediction | Pass if |
|---|---|---|
| **O1** | The atlas is complete | all 293 tiers placed in exactly one epoch; ≥ 99% of the 2,442 metric values attach to a tier in the map; every tier with a response bound to exactly one role |
| **O2** | Persons: never worse than the safe default (the 10× target A1 missed) | ORGANISM − BEAR (person): CI lower bound ≥ −0.00193 |
| **O3** | Agents: keeps the switching advantage | ORGANISM − BEAR (agent): CI lower bound > 0 |
| **O4** | The whole beats every single policy | combined ORGANISM − X: CI lower bound > 0 for X = BEAR, WATCHDOG and ANCHORED |
| **O5** | Safety | 0 Spine violations, intact audit chains; no recorded result changed; `check_all.sh` passes |

**Sealed expectations (written now):** O1 0.8; O2 0.7 (replay may still rule Bear out where it should not: W3-style
transfer has failed before); O3 0.8; O4 0.6; O5 0.9. O3 and O4 follow largely from AGENTS_ANCHOR's measured
directions; they are a replication on fresh seeds of a fusion, not a new mechanism.

## 4. Not in this step

The Person Lab (its action effects are placeholders, equal for every action, so no policy can differ there on
progress until effects are measured) and the World page's display of the organism. Stated models only.
