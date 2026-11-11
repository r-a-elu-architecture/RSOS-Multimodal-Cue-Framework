# Executable research benchmarks

## v1.3 compositional transfer and personalized cue programs

[**Run the flagship research source**](compositional-transfer-v1.3/README.md). This directory contains the actual synthetic benchmark generator, fixed and adaptive policies, direct negative controls, cue-program compiler, context/permission router and software tests.

The current experiment does **not** decode neural states or establish human conditioning. Its outcome is **synthetic selection regret**, whose causal effects are defined by code. An equally informed generic evidence-gated model matches the source-inspired controller.

```bash
cd experiments/compositional-transfer-v1.3
python -m pip install -r requirements.txt
bash run_smoke.sh
# For the original larger-sample studies:
bash run_all.sh
```

Large per-trial CSV tables are generated locally and not stored in Git history. See [the paper](../research/compositional-transfer-v1.3/PREPRINT_DRAFT.md) and [result definitions](../docs/BENCHMARKS.md).
