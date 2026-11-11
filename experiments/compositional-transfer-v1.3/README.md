# RSOS v1.3 — Synthetic compositional cue-transfer benchmark

This directory exposes the source of the **simulation benchmark** used in the v1.3 research draft. No behavioral, neural or clinical benefit has been measured.

## Quick smoke test

```bash
cd experiments/compositional-transfer-v1.3
bash run_smoke.sh
```

## Independent-seed holdout and context-shift evaluation

```bash
bash run_benchmark.sh
```

The benchmark varies eight artificial response-generating environments and compares fixed programs, individual memory, additive models, an all-pairs baseline, source-inspired relations, shuffled relations, a standard ANOVA-style evidence watchdog, and equally informed generic controllers. All policies receive the same simulated observations and action options.

Results are generated into `results/`. These files may be large and are intentionally ignored by Git.

**Scientific boundary:** The learning effects are defined in `src/transfer_benchmark.py`. The simulation does not validate RSOS therapeutic conditioning, personal glyph efficacy, EEG decoding, or a neurological mechanism. Equal-model ties and negative cases are central findings.

[Full paper draft](../../research/compositional-transfer-v1.3/PREPRINT_DRAFT.md) · [Detailed reported results](../../research/compositional-transfer-v1.3/RESULTS_REPORT.md).
