# Experiments and results — frozen v1.3

## 0. Evidence categories

1. **Archival specifications:** RSOS tiers/glyphs, RSIA supervision, RSX sequence operators, RSSO orchestration as described in `MODULE_PROVENANCE.csv`; source ZIP hashes included but source files remain private.
2. **Executed software measurements:** seeded model selection under independent synthetic worlds, compiler and routing stress, unit tests, source scope isolation.
3. **Synthetic causal assumptions:** the utility generator assigns artificial preferences, interactions, individual variations, reversals, and null effects. Its parameters have not been learned from human brains.
4. **Unverified hypotheses:** cue conditioning, counterconditioning, swish efficacy, resource-state transfer, identity/belief change, physiological benefit, neurofeedback efficacy.

## 1. Predeclared competitive task

Generate 12 possible glyphs, 5 sounds, 3 operator-plan tags, 4 voluntary contexts. Observe 24 random cue-program feedback scores per fictional person (measurement noise 0.2). Predict the highest utility program in 16 further contexts per person. The hidden outcome generator contains distinct world classes, including mechanisms where relation pooling helps and another where it is profoundly harmful. None of the controllers sees the hidden generator parameters.

The RSOS-inspired representation is **a declarative cue-family relationship encoding**. The RSIA-inspired watchdog is a conventional between-family explained-variance gate (`eta >= 0.23`), falling back to that person's observed cue memory when relationship support is low. RSSO design corresponds to contextual calibration/orchestration. RSX corresponds to selecting a typed chain; in this synthetic experiment chain is one of three predeclared categorical plans, not actual executed psychotherapy.

The strongest generic CV selector also chooses relational vs flat model on 3-fold calibration MSE. The `generic_same_gate` is exactly the same model and algorithm as RSIA watchdog, and is required to tie. If any mechanism were reported as inherently RSOS-exclusive despite this tie, that claim would be invalid.

## 2. New holdout: three independent seeds

Seeds 63011/12/13, 48 simulated persons × 8 world types per seed, 16 evaluation contexts/person. Exactly 18,432 evaluation decisions per policy, 11 policies. The 202,752 rows are **not** 202,752 independent people. The primary effective uncertainty blocks are 24 world–seed clusters; subject/probe dependence means inferential conclusions cannot be generalized to real people.

| Arm | Mean synthetic regret (lower is better) |
|---|---:|
| Fixed global program (index 0) | 0.525743 |
| Per-person flat cue average | 0.221336 |
| Generic additive | 0.240188 |
| Generic all-pairs | 0.226675 |
| Ungated cue relationship | 0.220643 |
| **RSOS + RSIA evidence gate** | **0.197825** |
| Generic 3-fold CV model selector | **0.195136** |
| Generic same-relationship & same-gate | **0.197825** |
| Correct relationship, no assumption gate | 0.220643 |
| Shuffled cue-group relationships | 0.235888 |

**Gate vs generic all-pairs:** absolute regret reduction 0.028850; 95% two-stage world/seed/subject bootstrap interval 0.011383 to 0.050399. Relative regret reduction 12.73%. **Gate vs per-person cue memory:** 0.023510 reduction; interval 0.005833 to 0.038650.

**Gate vs generic 3-fold selector:** regret difference 0.002689 *worse* for RSIA gate, with interval crossing zero. **Gate vs generic same gate:** exactly identical results. This falsifies a claim of RSOS-exclusive predictive superiority.

### By world: direction of advantage matters

| World | RSIA-gated regret | Generic all-pairs regret | Fixed cue-memory regret |
|---|---:|---:|---:|
| Cue-family transfer | 0.1645 | 0.1978 | 0.2138 |
| Family–operator synergy | 0.2010 | 0.2132 | 0.2261 |
| Context reversal | 0.2066 | 0.2208 | 0.2558 |
| Glyph idiosyncrasy | 0.1982 | 0.1958 | 0.2166 |
| Unstructured independent action effects | 0.3578 | 0.4888 | **0.3098** |
| Sensor-report noise | 0.1984 | 0.2010 | 0.2299 |
| Context drift | 0.2561 | 0.2960 | 0.3187 |
| Null effects | 0.0000 | 0.0000 | 0.0000 |

The worst family-transfer case is **unstructured independent action effects**; the gated model still trails direct memory there. The watchdog is not a universal oracle.

## 3. Strict out-of-context falsification

In the `novel_context_drift` scenario, **context 3 is excluded from all calibration observations**, and occurs in every other test position. Seeds 64011/12/13 were evaluated separately, 1,152 simulated person-world cases and 18,432 held-out decisions/policy.

- Average gated regret **0.198525** vs generic all-pairs **0.216869**, 8.46% relative improvement; paired improvement 0.018345, CI [0.003944, 0.035346].
- In the context-shift world only: gated 0.281141, generic all-pairs 0.309829, personal flat memory 0.324514.
- A generic same-gate controller again tied exactly. The generic CV model selector scored 0.198959, statistically indistinguishable.

This is **synthetic zero-calibration context transfer**, not real transfer of a conditioned response.

## 4. Did active, balanced cue calibration improve matters?

The matched-seed balanced-coverage design samples the same number of artificial calibration events per person and changes only the coverage over glyph family, sound, plan and context. The primary gated policy's simulated regret improved by **0.010586**, but its world-cluster CI **[-0.000847, 0.021778]** crosses zero. In contrast, the generic all-pairs comparator gained 0.017714 [0.006336, 0.029014]. Balanced coverage is **not a uniquely beneficial RSOS operator**.

## 5. Executable program & scope contract

The compiler supports user-specified tiers or no tiers; typed DAG operator sequences; optional branches requiring user choice; goal-map labels without claims of completion; consent/channel opt-in checks; low-context-confidence and signal-quality abstention; and user-reported high-distress manual grounding route. Regrouping glyph names does not imply their physiological meaning is known.

- Randomized graph compiler: 50,000 programs; exactly 37,500 valid accepted and 12,500 deliberately invalid rejected, zero discrepancies.
- Independent routing oracle: 100,000 synthetic decisions, 0 discrepancies.
- Versioned per-person/context glyph registry: 100,000 lookups, 0 discrepancies against independent dictionary oracle. A global-only map clashes with user/context reuse by construction; **this is not a state-of-the-art security baseline**.
- Unit tests: 24/24 pass.

## 6. What is still missing for an unprecedented mechanism?

The strongest generic CV model selector is competitive, identical graph models tie, and actual mechanism benefit comes from invented synthetic values. There is no real experiment establishing that a glyph/sound/kinesthetic/olfactory/VR combination implants a belief, rewrites neural associations, regulates trauma, or produces persistent counterconditioning. The data do not identify any world-first neurological mechanism. The new defensible computational claim is **evidence-gated compositional transfer can avoid some negative transfer and reduce decision regret under heterogeneous simulated environments**.

An exceptional scientific result would require measured intervention response in consenting participants: calibration, randomized equal-dose matched generic controller, objective memory/behavioral outcome, 24-hour and week-later recall, cross-context transfer, and optionally independently calibrated physiological features. See `NEXT_HUMAN_STUDY.md`.