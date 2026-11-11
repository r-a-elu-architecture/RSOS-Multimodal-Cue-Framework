# RSOS v1.4 — Context-stability and calibrated blending: falsification report

**Executed:** November 11, 2026. **Status:** independent-seed synthetic computational experiment; not an additional Zenodo deposit or peer-reviewed paper. **Author:** R. A. Elu. The archival [v1.0.0 research preview](https://doi.org/10.5281/zenodo.24143732) contains the v1.3 engine, **not** this later v1.4 successor.

## New observation

The proposed context-invariance-inspired successor reduced regret in the synthetic **unstructured-actions** environment, but its global performance did **not** beat the strongest existing generic cross-validation control. On independently seeded holdout, invariance-aware blending scored **0.189179**, original RSIA gating scored **0.194588**, and the generic 3-fold CV selector scored **0.187238** (lower is better). A generic implementation using **exactly the same** invariance penalty and blend ties the successor on every program choice and regret value.

**World-specific signal, standard holdout:** in *unstructured_actions*, invariance blend **0.300269** versus generic CV **0.343738** (12.65% lower artificial regret), original RSIA **0.351262**, generic equally informed **threeway_blend 0.300493**, and flat memory **0.296728**. The successor is not the world-specific winner, and its small distinction from generic blending is not an established effect.

**Counterexample:** in *idiosyncratic_glyphs*, invariance blend **0.191794** versus generic CV **0.170058**; in *novel_context_drift*, **0.233455** versus **0.212523**. The purported stability advantage is therefore not universal.

## Mechanism actually implemented

Three candidate action-value estimators use identical simulated feedback data: a cue-family relational model, an individual per-program memory model, and a generic all-pairs interaction model. Calibration is **24 observations/person** as in v1.3.

For each candidate, calculate out-of-fold predictive residuals using v1.3's seeded 3-fold partition:

- Calibration error: mean squared out-of-fold residual, MSE.
- Context instability: variance across **observed contexts** of each context's *mean signed residual*. A context not observed in calibration contributes nothing.
- **Guard score:** \`MSE + 0.5 × context_instability\`. Hard guard selects the model with minimum guard score.
- **Blend:** weights \`w_m ∝ exp(-(guard_score_m − min_guard_score)/0.025)\` and linearly combines the three predicted utility vectors before selecting the argmax program.
- **Identical generic controls:** \`generic_same_invariance\` and \`generic_same_blend\` use exactly the same data, selection logic and action space; both must tie.
- **Strong generic comparators:** original relational-versus-flat 3-fold CV selector, generic three-way CV hard selector, generic three-way CV blend, original RSIA gate, flat memory and all-pairs regression.

No policy is told its synthetic world label or the hidden test utility. The invented outcome generator is only consulted after a policy has selected its action, for regret scoring. This is not a new neural mechanism. Model-blending and stability penalties are generic statistical techniques.

The design was chosen after exploratory development checks, not pre-registered before all exploration. Weight 0.5 and temperature 0.025 are **frozen before independent holdout seeds**; do not treat development results as confirmatory.

## Exact executed cohorts

| Cohort | Independent seeds | Simulated persons/world/seed | Evaluations/person | Evaluations/policy | Total policy rows |
|---|---|---:|---:|---:|---:|
| Development | 65011, 65012, 65013 | 24 | 8 | 4,608 | 78,336 |
| Independent standard holdout | 66011, 66012, 66013 | 48 | 16 | 18,432 | 313,344 |
| Strict novel-context holdout | 67011, 67012, 67013 | 48 | 16 | 18,432 | 313,344 |

The strict condition **only** changes the *novel_context_drift* world: context 3 has zero calibration observations and occurs in every other evaluation; the seven other worlds use the standard calibration procedure. Each cohort uses eight artificially generated worlds and **17 policies**, including a diagnostic oracle. Repeated decisions from one fictional person are not independent subjects.

## Mean simulated regret (lower is better)

| Model | Development | Independent standard holdout | Strict novel-context holdout |
|---|---:|---:|---:|
| Original generic 3-fold CV | 0.189851 | **0.187238** | **0.192708** |
| Invariance hard guard | 0.195983 | 0.189162 | 0.195388 |
| **Invariance soft blend** | **0.186218** | 0.189179 | 0.197928 |
| Generic same-invariance blend | **0.186218** | 0.189179 | 0.197928 |
| Generic 3-way CV blend (no context penalty) | 0.185792 | 0.190627 | 0.198269 |
| Original RSIA evidence gate | 0.196271 | 0.194588 | 0.197555 |
| Generic same-RSIA gate | 0.196271 | 0.194588 | 0.197555 |
| Generic all-pairs | 0.215956 | 0.211797 | 0.215516 |
| Generic additive | 0.225499 | 0.223137 | 0.232259 |
| Shuffled cue-family relations | 0.236550 | 0.225131 | 0.235454 |
| Fixed global program | 0.529606 | 0.547956 | 0.541761 |
| Flat per-person memory | 0.213774 | 0.216710 | 0.218848 |

The development difference between the two best blended methods (generic 0.185792 vs invariance 0.186218) was very small. Holdout ranks change with independent seeds. The final policy was **not** selected using holdout scores.

## Cluster-resampled comparisons

Difference is **control regret minus invariance-blend regret**; positive favors invariance. Two-stage bootstrap: resample **24 seed × world clusters**, then fictional people inside each cluster. 2,500 resamples, deterministic bootstrap seed 9018, two-sided percentile 95% interval. Trial-level observations are not separately resampled.

| Independent cohort | Comparator | Difference | 95% cluster interval |
|---|---|---:|---:|
| Standard | Original generic CV | **−0.001941** | [−0.011735, +0.008957] |
| Standard | Original RSIA evidence gate | **+0.005409** | [−0.004429, +0.016217] |
| Standard | Identical generic invariance blend | **0.000000** | [0, 0] |
| Strict OOD | Original generic CV | **−0.005220** | [−0.016524, +0.009544] |
| Strict OOD | Original RSIA evidence gate | **−0.000373** | [−0.010094, +0.009878] |
| Strict OOD | Identical generic invariance blend | **0.000000** | [0, 0] |

Intervals crossing zero fail to establish positive or negative population-level differences under this synthetic cluster scheme. World-specific comparisons are exploratory, with only three independent seed-clusters per world. No multiple-testing correction; synthetic worlds do not represent a sample of real human settings.

## Failure analysis and successor hypothesis

The current penalty measures **bias variation across observed calibration contexts**. It cannot identify the actual response mechanism of a wholly unobserved future context. It often overweights plausible-looking relational predictions, while blending can dampen an incorrect large model prediction in unstructured worlds. The hard guard performs better on glyph-idiosyncratic examples than the soft blend; the blend helps unstructured action worlds. These are competing failure modes.

**Discriminating next experiment:** introduce controlled active calibration in the target context versus the best passive calibration at the *same total observation budget*. Randomize policy choice using only information available before target outcomes, and include a generic active learner with identical observations and decision rights. Compare reduction in negative transfer in strict context drift, with the cost of probing and abstention declared in advance. Without target-context observations or justified transport assumptions, a genuinely novel response reversal may be statistically unidentifiable.

No result here establishes world-first algorithmic superiority, therapeutic efficacy, EEG decoding or a human learning effect.

## Reproduce

Run from \`experiments/compositional-transfer-v1.3/\` (with Python, NumPy and pandas installed):

\`\`\`bash
python src/invariance_successor.py --seed 65011 65012 65013 --people 24 --tests 8 --output results/invariance_v14_dev
python src/invariance_successor.py --seed 66011 66012 66013 --people 48 --tests 16 --output results/invariance_v14_holdout
python src/invariance_successor.py --seed 67011 67012 67013 --people 48 --tests 16 --hard-ood --output results/invariance_v14_ood
python -m unittest discover -s src/tests -p test_invariance_successor.py -v
\`\`\`

Each command regenerates full trial-level outputs and per-person blocks. For exact bootstrap intervals see the [reproducibility appendix](REPRODUCE.md). A native local validation of **all eleven** original baseline policies showed identical chosen programs and regrets to v1.3, and the published successor file was checked for exact Git-blob content identity with the locally executed implementation. The v1.3 source remains unchanged in GitHub.

**Source:** [invariance_successor.py](../../experiments/compositional-transfer-v1.3/src/invariance_successor.py) · [v1.3 source](../../experiments/compositional-transfer-v1.3/src/transfer_benchmark.py) · [test suite](../../experiments/compositional-transfer-v1.3/src/tests/test_invariance_successor.py) · [interactive results explorer](../../docs/invariance-v14.html).
