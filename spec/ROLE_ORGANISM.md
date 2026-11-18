# ROLE_ORGANISM: role sensors, tier bindings, role profiles and a plan per person

Registered 18 Nov 2026, before its code. Follows ORGANISM §5.1 (the metrics do not tell the roles apart; 186 tiers carry
no response; Baseline has no built tier). Status label for everything here: built and tested in software, ready for
people and companies to use; effect in people not yet measured.

## 1. Profiles: what they lack (measured on the 100 Lab persons before this step)

| Part of a profile | Present in |
|---|---|
| Environment / Behaviour / Beliefs | 81 / 92 / 69 |
| Skills / Identity / **Mission** | 44 / 38 / **14** |
| A desired state | **55** (45 have none) |
| Signals (load, loss, conflict, change, other) | 75 / 56 / 47 / 15 / 30 |

Without a desired state the agents have no target; without mission and identity the higher levels (where RSOS's deep
identity work sits) cannot be planned. This step does not invent them: a plan **asks for** what is missing (a LINX
intake question per missing level) and states which steps wait for the answer.

## 2. What is built

1. **Role sensors** (`rsxv/rsxv/roles.py`): one signature measure per role, read from the agent environment around each
   tick: Monitor = silent faults made visible; Stabilise = pressure removed beyond its drift; Plan = the next repair
   armed with noise-free readings; Repair = faulty modules fixed; Drive = progress; Baseline = progress net of added
   load (progress − 3 × added pressure).
2. **Tier bindings, proposed** (`docs/data/bindings_proposed.json`; `docs/data/tier_map.json` unchanged): for each of the
   186 tiers without a response, a proposed response and role read from the tier's own record (its function, logic
   and application lines; never the glyph line or the model-impact block), with the matched words shown. Rule (fixed
   now): keyword families per response; the response with most matches wins; ties go to the safer response in the
   order STOP, PAUSE, GATE, REENTRY, RECALIBRATE, MIRROR, RECALL, SEQUENCE, GOVERN, BLEND, COMPRESS, GLYPH_CUE, OFFER,
   GENERATE; no match → flagged "by hand". Every proposal waits for the author's confirmation.
3. **Role profiles** (in `docs/data/organism.json`): per role its archetype, glyph and vibration code (from the nodes
   module), sensor, responses, built tiers, proposed tiers and leading metrics.
4. **A plan per person** (`rsxv/rsxv/personlab/organism_plan.py`): from the profile to ordered role steps. Stabilise
   first when initial intensity ≥ 4 or a load or conflict signal is present; then Monitor (map the current
   statements), Plan (beliefs, identity, mission), Repair (behaviour), Drive (skills, environment), Baseline
   (maintenance). Each step: up to 3 **built** tiers of that role, the archetype's glyph and vibration code, the role
   sensor, and person measures with a threshold (intensity 1–5, progress toward the desired state, feedback 1–5).
   Missing levels and a missing desired state become intake questions.

## 3. Predictions

| # | Prediction | Pass if |
|---|---|---|
| **R1** | Each role has its own sensor | On `AgentEnvV2` with a uniformly random mode each tick (200 seeds × 120 ticks), each role's sensor has its highest mean when its own mode runs (6 of 6) |
| **R2** | Bindings read from the tiers | All 186 tiers get a proposal; ≥ 80% matched by the rule with the matched words shown, the rest flagged by hand; `tier_map.json` unchanged |
| **R3** | Every role has a body | All six role profiles complete; Baseline has ≥ 1 proposed tier |
| **R4** | A valid plan for every person | 100 of 100 plans: every referenced tier exists and is built, every step carries a measure with a threshold, every missing level or desired state appears as an intake question; deterministic |
| **R5** | 10× smaller search | Candidate tiers per plan step (role-scoped) ≤ 29.3 on average (0.1 × 293) |
| **R6** | No regression | `check_all.sh` passes; recorded results unchanged; new texts pass the wording rule |

Sealed note: R1 is largely true by construction (each sensor reads its role's defined effect); it checks the
instrument, not a discovery. R2 is the real uncertainty.

## 4. Results (18 Nov 2026)

Code: `rsxv/rsxv/roles.py` (`rsxv/results/role_sensors.json`), `architecture/bindings.py`
(`docs/data/bindings_proposed.json`), role profiles in `architecture/organism.py` (`docs/data/organism.json`),
`rsxv/rsxv/personlab/organism_plan.py` (`rsxv/results/organism_plans.json`); tests `rsxv/tests/test_role_organism.py`.

| # | Result | Verdict |
|---|---|---|
| R1 | 5 of 6 roles have their own sensor (Monitor 0.41 vs 0; Stabilise 0.29 vs 0; Plan 1.0 vs 0.50; Repair 0.22 vs 0.06; Drive 1.0 vs 0.50). **Baseline fails**: Lion 0.50, Drive 0.65 on Baseline's own sensor, because pressure saturates at its ceiling and Drive then adds no measured load | **fail** (kept as a visible registered failure) |
| R2 | 186 of 186 tiers have a proposal; **185 by rule (99.5%)** with the matched words, 1 flagged by hand; `tier_map.json` unchanged. Proposed: Monitor 50, Stabilise 42, Drive 40, Plan 32, Baseline 19, Repair 2 | **pass** |
| R3 | Six complete role profiles; Baseline 19 proposed tiers | **pass** |
| R4 | 100 of 100 plans valid (every tier built, every step measured with a target, every missing level and desired state asked); deterministic; 5.6 steps per plan | **pass** |
| R5 | 5.4 candidate tiers per step on average, against 293 (**54× smaller**; largely by construction of role scoping) | **pass** |
| R6 | `check_all.sh` passes; no recorded result changed; new texts pass the wording rule | **pass** |

**What the organism now lacks, measured.**
1. **Baseline is undefined as a function.** In the agent environment Lion is "progress 0.5, no other effect"; no
   sensor can tell it apart, and it has 0 built tiers. It needs its own function (for example keeping the gain: a
   relapse-prevention check) before it can be measured.
2. **Five archetypes have no ledger glyph** in the nodes module (Raven, Eagle, Leopard, Tiger, Bear; only Lion 🦁).
   The plans carry the vibration codes; the glyphs should come from the tier ledger, chosen by the author.
3. **Repair is thin**: 2 built and 2 proposed tiers.
4. **Profiles:** 45 of 100 have no desired state, 86 no mission, 62 no identity. The plans ask for them; until answered,
   progress toward the desired state cannot be measured for those persons.
5. **The 185 proposals wait for the author.** Confirmed bindings move tiers from record to specified; a test per tier
   then moves them to built.
