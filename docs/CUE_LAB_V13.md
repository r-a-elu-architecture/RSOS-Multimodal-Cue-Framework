# RSOS Cue Lab — live original v1.3 Python benchmark

**Launch:** https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/cue-lab-v13.html

## Mission, goals and success criteria

**Mission:** investigate whether cue relationships between visual glyphs, sounds, planned operators and contexts can be learned and transferred to new simulated situations without causing avoidable negative transfer. This is one experimental application within the wider RSOS research programme.

**Research question:** when does a relational model deserve trust over personal memory, and can evidence-gated selection improve held-out synthetic regret against equally informed generic alternatives?

**Goals:** (1) discover world types in which relationship transfer helps versus hurts; (2) quantify uncertainty and fallback behavior; (3) compare eleven original policies on equal observations and action options; (4) identify hypotheses for subsequent ethically reviewed, consenting-human research.

**Success criterion:** reproducibly lower regret than the strongest *non-identical* matched generic policy across independently seeded worlds, with world/person-level uncertainty, negative transfer accounted for and no unreported tradeoff. A proposed real-world conditioning effect would require direct human outcomes and appropriate controls; synthetic scores cannot establish it.

**Falsification already observed:** the generic controller with identical relation model and gate **ties exactly**; the three-fold generic CV selector is slightly better in the archived three-seed full holdout (0.195136 versus the RSIA gate's 0.197825 mean synthetic regret). This invalidates a claim of uniquely superior RSOS selection on this task.

**What visitors can do:** run the original byte-for-byte archived v1.3 Python simulation in a browser, compare all policies, inspect failures across eight synthetic worlds, and export their chosen synthetic run. The fixed published full-holdout summary is not recomputed by a small browser sample.

**Relationship to other research:** the [Architecture Benchmark Lab](architecture-benchmark.html) examines real *historical conversation* data and internal provenance engineering. Cue Lab does not validate ancestry-genealogy claims or physiological conditioning effects. [Full two-lab mission and evidence map](RESEARCH_MISSION.md).

## Original research executable, not a JavaScript approximation

The browser worker imports an unmodified byte-for-byte copy of the Python file from the archived release:

- Original source: [experiments/compositional-transfer-v1.3/src/transfer_benchmark.py](../experiments/compositional-transfer-v1.3/src/transfer_benchmark.py).
- Archived tag: [v1.0.0-research-preview](https://github.com/r-a-elu-architecture/RSOS-Multimodal-Cue-Framework/tree/v1.0.0-research-preview).
- Browser copy: [docs/v13-runtime/transfer_benchmark.py](v13-runtime/transfer_benchmark.py).
- Git blob SHA-1 checked by the worker: `eb05bc81bf448bc1b47226b65aee251c313c958b`.

A browser Web Worker loads pinned Pyodide version 0.27.7 from jsDelivr and installs NumPy/pandas in-browser. The worker calculates the Git-style content blob hash before importing the archived file. It calls the original `run()` function, not a reimplementation, and groups its returned data frame for display. The source itself is unchanged.

**Requirements:** modern browser with JavaScript, web worker, WebAssembly, network access to the jsDelivr CDN, and sufficient memory. If the external runtime is blocked, the live run cannot start. The frozen full-holdout reference data remains visible.

## All policies compared on the same simulated data

- RSIA family-support evidence gate vs equally informed generic same gate (**must tie**).
- Generic 3-fold CV model selector.
- Generic all-pairs, additive, flat cue memory, shuffled-family relation, ungated relation, generic exact same relation, fixed global program, and unattainable oracle diagnostic.

Every synthetic person is evaluated over the same 180 candidate cue programs and four contexts. The policy comparison uses 24 calibration scores with noise 0.20 and the original ANOVA family-support threshold (default 0.23). The worker checks both regret and program-selection identity for the required same-gate negative control; it refuses to report a run if this control fails.

## Scope of the live demo

The browser selects **one seed**, 1–12 fictional people per world, 2–16 evaluation contexts, random or balanced calibration, and the standard or strict unseen-context task. The frozen published holdout instead uses *three seeds × 48 people per world × 8 worlds × 16 trials*. Its reported mean regret is **0.197825 for RSIA**, **0.197825 for identical generic same-gate**, **0.195136 for generic CV**, and **0.226675 for all-pairs**. The smaller browser sample is not expected to reproduce these aggregate figures exactly.

The native Python benchmark was independently re-executed in the current development session with all three holdout seeds, 48 simulated people/world, 24 calibrations, and 16 contexts. It reproduced **202,752 policy rows** and the above model regrets. This is a computational reproduction, not an independent scientific replication by an outside laboratory.

## Reproduction outside browser

Clone the GitHub repository and run:

```bash
cd experiments/compositional-transfer-v1.3
bash run_benchmark.sh
```

The run script reproduces both standard holdout and strict context-shift experiments. Scripts write CSV reports under ignored `results/`. Do not interpret evaluations as independent patients or physiological measurements.

## Limitations and provenance

- Synthetic outcome generator and feature relationships are specified by the experiment itself. True clinical/behavioral outcomes are not collected.
- Identical generic same-gate performance is an explicit **negative finding** against exclusive superiority claims.
- The generic 3-fold selector can outperform the RSIA gate.
- A browser subset is a demonstration, not a replacement for a fully powered/clustered experiment or a statistical uncertainty interval.
- Runtime dependencies load from a third-party CDN; no backend receives experiment data. The source code and mathematical outcomes are synthetic.
- The DOI [10.5281/zenodo.24143732](https://doi.org/10.5281/zenodo.24143732) identifies the original archival tag; these later interactive website changes are **post-release additions** and are not inside that archived ZIP.
