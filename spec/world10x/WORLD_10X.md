# WORLD_10X — the White Dragon over the World's failures (sealed plan, not a test)

Status: sealed 2026-11-18, before any run, any registration that follows from it and any control arm. Nothing here enters
the results register. Each row becomes evidence only through its own registered spec.

## 0. What this is

The owner's RSOS scene (the White Dragon visits each planet, lights the library of all knowledge and lands green
particles that become the nodes of each planet's 10× list) was applied to every failure or miss in the World, the agents
and the Person Lab that can be worked on **without a real person**. One planet per failure or miss.

- Program: [`white_dragon_world_failures.rsl`](white_dragon_world_failures.rsl), RSOS Language 0.2. Compiled with the
  RSOS-Language compiler (commit 7a9bcd3) against this repository's `dev` governance: **0 errors, 0 warnings, 55
  operations**.
- The owner's prompt is kept verbatim in the private record, not here.
- **Who supplied what.** The scene (the owner) set the task structure: a loop over every planet, a landing per planet and a
  10× target per planet. The assistant (Claude Opus 5.5) chose the particles and landings. The compiler checked form,
  not content. About half of the landings restate fixes the assistant had listed just before the scene was applied; the
  scene added coverage (every planet), a target per row and the grouping in §2.

## 1. The 16 landings

| # | Planet: miss (measured) | Particle → landing | 10× target | 10× honest? |
|---|---|---|---|---|
| 1 | Bear lock: adaptive loses to fixed Bear by 0.011–0.085 per tick (BASELINE_AUDIT) | Ecological niche → an environment where the best mode varies by context, fitted from row 8, not written | Adaptive regret ≤ 0.1× fixed-best regret, against a per-context oracle | Only after the environment is fitted from data |
| 2 | Cue loophole: 1 cue open at the end in 15/15 runs under Bear (STAB_DEFAULT §5) | Refractory period → a cue resolves on its own after a window | ≤ 1/15 runs; 10× fewer blocked ticks | Yes |
| 3 | Transfer: T-AP 0.133 below the oracle; 10/13 transfer rows fail; G1 equals "transfer nothing" | Rosetta Stone → map by measured function, not by name, in row 1's environment | Gap to the oracle ≤ 0.013 | Only where substrates differ; today Bear alone reaches the oracle |
| 4 | Repurposing: fails on both substrates, R1–R6 | Penicillin → screen failures at 10× the simulated episodes | Beats repair on both substrates | The 10× is the screen size, not the effect |
| 5 | Jam predictor J1: 0.754 vs 0.685, p = 0.054, n = 260 | Kalman filter → state-space forecast from the signal history; 2,600 simulated episodes | Significant at 0.01 | 10× data yes; 10× fewer errors no |
| 6 | Repair ceiling W1: method and greedy both 100% | NP-hard instances → a benchmark where greedy is provably suboptimal | Greedy ≤ 50%; meta repair measured there | Yes, as a harder benchmark |
| 7 | Attribution LIA-WW: decisive step 41.8% vs 45.1% | Counterfactual replay → rerun each log with one step corrected (model calls only) | Stretch: miss 58% → 6%. Pass: beat 45.1% | Stretch unlikely; recorded as a stretch |
| 8 | Outcome grain: Person Lab step 5, 100 final intensities; error 0.814 vs linear 0.681 | Microscope → the seeker's 1–5 rating after supporter turns | ≈10× more outcome events; beat persistence on the next rating | Yes, literally |
| 9 | Override moments: 3 of 560, 30 needed (step 5b) | Microscope → match by meaning, not word overlap, with a placebo | ≥ 30 moments | Yes |
| 10 | Stress validity: reader change vs own change ρ 0.03 (step 5c) | SI units → calibrate to self-report on development data; drop greeting and thanks turns; pilot look first | ρ 0.03 → ≥ 0.30 | Plausible, not certain |
| 11 | Rapport power: match +0.09 [−0.02, +0.20] (RAPPORT_ESCONV) | Meta-analysis → pool rated support corpora | 10× events | Partly: 10× events ≈ 3× narrower interval; 10× narrower needs 100× |
| 12 | Context data: personal prompts 128, 505, 185 of 200 (H-CTX 1–3) | Telescope → all 14 WildChat shards (3 used), LMSYS-Chat-1M, support corpora | ≥ 1,850 personal prompts | Yes |
| 13 | ADOPT-WC confound: placebo inflated by the AI echoing the person | Controlled trial → an echo-matched placebo | 10× smaller bias, measured as placebo-vs-placebo spread | Yes |
| 14 | Safety reader SR-3: recall 0.95, one critical turn missed, one record | Swiss-cheese model → two independent layers; hopelessness or arrangements alone triggers a check-in | Miss rate ≤ 0.5% on synthetic and public scenarios | Yes for this step; clinician validation needs people and is out of scope |
| 15 | Reader independence: κ 0.728 and 0.925 from two instances of one model | Replication → a second reader by a different method or model family | Measure the inflation | No 10× applies; a validity fix |
| 16 | Lineage gaps: C1, C2, C5 not testable; C5 AUC 0.49; MSE melody | Phylogenetics → multi-session public data (26,783 WildChat persons) | 10× events; C1, C2, C5 testable | Yes |

## 2. Three root nodes (the assistant's reading, not evidence)

- **B, measurement grain (rows 8–12).** Measure finer, or calibrate the reader.
- **A, a world that can disagree with Bear (rows 1–6).** Every agent and transfer miss traces to hand-written environments
  where one answer always wins. Nothing here moves until the environment is fitted from B's measurements.
- **C, independence and controls (rows 7, 13–15).**

Row 16 is a data step. Order: B first (row 8 first), row 14 in parallel, then A on an environment fitted from row 8.

## 3. What would make this evidence

- Each row through its own registered spec, with its threshold fixed before its code.
- The scene itself: fresh sessions given the same 16 misses, with this scene and with a plain instruction; count the
  concrete, testable levers per arm and the levers found only by the scene. This file is the sealed answer that test
  compares against.
