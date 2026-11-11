# Reproducibility and evidence boundaries

The v1.4 source is an additive experiment layered over the v1.3 Python module, not a mutation of the DOI-archived v1.3 tag. Published tests were evaluated locally on November 11, 2026.

### Synthetic benchmark command

From \`experiments/compositional-transfer-v1.3/\`, install \`requirements.txt\` into an isolated Python environment and run the commands in [REPORT.md](REPORT.md). For each run, the successor writes \`trials.csv\` (one program choice and regret per policy × fictional person × trial), \`means.csv\`, \`world_means.csv\`, and \`person_blocks.csv\`. These are generated outputs, not human measurements.

### Cluster bootstrap algorithm

Given the \`person_blocks.csv\` generated for one cohort:

\`\`\`python
import numpy as np
import pandas as pd
df = pd.read_csv("results/invariance_v14_holdout/person_blocks.csv")
pivot = df.pivot(index=["seed","world","person"], columns="model", values="regret").reset_index()
groups = [(g["generic_cv_selector"]-g["invariance_blend"]).to_numpy()
          for _,g in pivot.groupby(["seed","world"],sort=True)]
rng=np.random.default_rng(9018)
draws=[]
for _ in range(2500):
    ix=rng.integers(0,len(groups),len(groups))
    draws.append(np.mean([
        np.mean(groups[j][rng.integers(0,len(groups[j]),len(groups[j]))])
        for j in ix
    ]))
print(np.quantile(draws,[.025,.975]))
\`\`\`

The published multicomparison CIs used the same two-stage procedure, looping through candidate/comparator pairs with one RNG stream initialized to 9018. To recreate the exact numeric CI for a given comparison, reproduce the full comparison ordering or independently re-initialize the RNG for that specific comparison and document the changed bootstrap sample. Only the direction of results, not a particular last decimal of a resampling interval, is inferentially meaningful.

### Interpretation

- **Falsification:** equally informed generic same-invariance control must tie the RSOS-labeled policy exactly.
- **Causal scope:** artificial response-generating worlds; no real behavioral, clinical, or neural evidence.
- **Same observation budget:** 24 synthetic observations and the same action and context labels for all arms. Additional fold fitting costs compute, not extra observations.
- **Strict novel-context variant:** exclusion of context 3 applies only to the novel-context-drift world, not to all eight worlds.
- **Selection provenance:** one exploratory development cohort, then two independent-seed holdouts. No external laboratory, participant replication or peer review.
- **Archive boundary:** Zenodo DOI 10.5281/zenodo.24143732 identifies the earlier tagged v1.0.0 research archive, not v1.4 results added later to the live repository.
