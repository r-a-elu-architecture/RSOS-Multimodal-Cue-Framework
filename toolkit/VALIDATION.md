# rsos_cue v0.1 — synthetic validation (2026-11-11)

Everything here is simulated. Regret is the true-utility gap between the chosen program and the best program in that context (lower is better). Intervals are paired two-stage cluster bootstraps over world × seed clusters (95%). Banks are trained only on development seeds; all tuning (CONTAIN/self settings, explore = 8, penalty = 2) was done on development seeds.

**Reproducibility note.** Sections A–C used the v1.3 simulator, which was retired from `main`; it remains at the `v1.0.0-research-preview` tag. Sections on random universes and real data (MovieLens-1M, goodbooks-10k) are reproduced by `validate/universes.py` and `validate/real_data.py`; the rating datasets are not redistributed and must be downloaded from their publishers.

## A. Original v1.3 simulator (8 worlds; test seeds 63011–3 and 64011–3)

| Controller | Holdout | Unseen context | World never seen by bank |
|---|---|---|---|
| v1.3 RSIA evidence gate | 0.1978 | 0.1985 | 0.1978 |
| v1.3 generic CV selector | 0.1951 | 0.1990 | — |
| rsos_cue without fallbacks | 0.1515 | 0.1534 | 0.1867 |
| **rsos_cue v0.1 (CONTAIN + self-archetype)** | **0.1523** | **0.1540** | **0.1634** |

- **vs v1.3 gate:** −23.0% holdout (CI 0.030–0.062), −22.4% unseen context (0.030–0.059), −17.4% unseen world (0.020–0.050).
- **What the fallbacks buy:** on unseen worlds they cut regret 12.5% (CI 0.007–0.043). On worlds the bank has seen they cost 0.5% (CI includes 0).
- **The two v1.4 failures are repaired:** unstructured actions 0.454 → 0.328 (v1.3: 0.358); noisy self-reports 0.249 → 0.203 (v1.3: 0.198).
- Bank plus active calibration (from the v1.4 report): 0.1222 / 0.1340.

## B. Harder simulator — worlds the model cannot represent (test seeds 72001–2)

The population mixes eight world types:
- linear (control)
- saturating outcomes
- glyph × sound × context triple interactions
- heavy-tailed noise (t, 2 degrees of freedom)
- effects that drift within the session
- self-ratings that point the wrong way
- a single hidden "jackpot" program per context
- null

| Controller | Random calibration | Active calibration |
|---|---|---|
| v1.3 RSIA evidence gate | 0.2516 | — |
| v1.3 relational ridge (no gate) | 0.2325 | — |
| rsos_cue generic (no families) | 0.2255 | 0.1970 |
| **rsos_cue v0.1** | **0.2223** | **0.1920** |

- **Active, explore-then-project:** −23.7% vs v1.3 gate (CI 0.019–0.100); −17.4% vs relational ridge (0.002–0.081).
- **Random calibration:** −11.6% vs gate (0.007–0.053); vs ridge −4.4%, not significant.
- **World type never seen by the bank:** 0.2335; not significantly better than the gate (−7.2%) and level with the ridge.

### Where rsos_cue still loses (open problems)

| World | rsos_cue (active) | Best | Note |
|---|---|---|---|
| Wrong-way self-ratings | 0.257 | ridge 0.176 | Learned trust helps (0.552 → 0.257) but the ridge, which fits the rating sign directly, is better |
| Within-session drift | 0.351 | ridge 0.330 | No model of change over time |
| Hidden jackpot program | 0.475 | all ≈ 0.48 | No method finds one program out of 180 in 24 trials |

## C. Is the RSOS structure itself the reason?

No, not on these benchmarks. The generic bank with no glyph families comes within 1–3% of the structured version, and the differences are not significant on the hard worlds.

What does the work is the set of mechanisms taken from the archive, and they also work without RSOS structure:
- archetype bank (RSIA Archetypes / RSSO MEMSTACK)
- soft Watchdog
- ratings treated as measurements, with learned trust
- CONTAIN and self-archetype fallbacks
- active probing (RSX FutureProjection)

Families add about 7% only on the original simulator with random calibration.

## D. Families can be learned

`discover_families` recovered the 4 glyph families from population ratings exactly (adjusted Rand index 1.0) on the v1.3 simulator.

## E. Human-study planning (`study_kit/power_table.txt`)

This assumes humans behave like the simulator at 25–100% of its effect size.

| Comparison | Participants needed for 80% power |
|---|---|
| vs a fixed program | 10–20 |
| vs a v1.3-style adaptive controller | ~80 (160+ at quarter effect) |
| vs the generic bank | no difference in simulation; only a real-data study can show one |

## F. External tests (added 2026-11-12): standard methods, real human data, random universes

### F1. Real human ratings, reframed as cue choice
- **Data:** MovieLens-1M (100 most-rated movies; families = primary genre) and goodbooks-10k (150 most-rated books; families = author).
- **Design:** 400 test users per dataset. Each user's 16 rated items form a fixed decision set. Every method gets 24 other ratings, either random or chosen by the method's probing, then picks one item from the decision set.
- **Metric:** regret = best rating in the set − rating of the pick (stars). Intervals are bootstrapped over users.

| | MovieLens | goodbooks |
|---|---|---|
| Best standard method, random ratings | matrix factorization 0.435 | user-KNN 0.433 |
| Hierarchical Bayes + Thompson sampling (standard bandit) | 0.483 | 0.370 |
| rsos_cue with learned links, random ratings | 0.443 (tie with MF) | 0.440 (tie with KNN) |
| **Best with rsos_cue probes** | **MF on rsos_cue-chosen ratings 0.333** | **rsos_cue UCB 0.363** |
| Best vs best standard | **−23.6%** (CI of diff 0.035–0.172) | **−16.2%** (0.003–0.138) |

- **Probes matter on real data.** Choosing which 24 items to ask about beats asking at random:
  - MovieLens: MF −23.6% (significant).
  - goodbooks: rsos_cue −15.3% (significant); MF −13.6% (not significant).
- **Not better than standard Thompson sampling.** rsos_cue's projection probes differ from hierarchical-Bayes Thompson sampling by −2% (MovieLens) and −5% (goodbooks), both not significant.
- **Prediction alone only ties.** Learned links (RSSO LINX) close the gap to matrix factorization and KNN but do not beat them.
- **Families from real metadata help; archetypes do not.** Genre and author structure beats the generic no-family model by 8% (MovieLens) and 21% (goodbooks). A single-prior model with families does as well as the 8-archetype bank.

### F2. 24 random universes (not designed around the model)

Each universe randomizes:
- program-space size
- shared population effects
- 1–8 hidden person types
- trust in self-ratings, from inverted to reliable
- noise type (Gaussian, t, skewed)
- link (linear, saturating, threshold)
- binary outcomes in 30% of universes
- wrong declared families in half of the universes

| Method | Regret |
|---|---|
| **rsos_cue, projection probes** | **0.0739** |
| Hierarchical Bayes + Thompson | 0.0818 |
| rsos_cue + Thompson | 0.0825 |
| rsos_cue + UCB | 0.0993 |
| rsos_cue generic, random | 0.1034 |
| Hierarchical Bayes K=1, random | 0.1095 |
| rsos_cue, random | 0.1110 |
| Per-person GP / ridge | 0.154 / 0.164 |

- **Against the standard bandit:** projection probes beat hierarchical-Bayes Thompson sampling by 9.7%, winning 16/24 universes, but the interval includes 0.
- **Against random probes:** projection beats random probes by 33–50% (significant). It beats UCB by 26% (significant) and per-person GP/ridge by 52–55%.
- **With random calibration**, the 8-archetype bank equals single-prior hierarchical Bayes (−1.4%, not significant).

### F3. Verdict

**Established, including on external real-human data:**
- Probe selection gives large, significant gains over random calibration and over per-person GP, ridge, popularity and MF/KNN fed random data.
- Population pooling with real metadata families beats the generic model.

**Not established:**
- Any advantage over a standard hierarchical-Bayes Thompson-sampling bandit (ties everywhere).
- Any advantage of the archetype bank over a single population prior.
- Any advantage of rsos_cue's predictor over matrix factorization or KNN on real ratings.
