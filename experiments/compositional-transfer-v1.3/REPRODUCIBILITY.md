# Reproducibility and audit instructions

All artifact results were produced in Python 3.13 with NumPy, pandas, scikit-learn, SciPy and mne available. No external network access or device was used for the benchmark. The source archives are omitted from the public package; the supplied synthetic test is completely self-contained.

- `src/transfer_benchmark.py` is the generator + all tested policies. Its `generate_world` and `actual` functions explicitly enumerate the fabricated effects; reviewers should inspect these *first* to see where assumptions favor relational models.
- `src/program_graph.py`, `src/runtime.py`, `src/scoped_cue_registry.py`: user-controlled module composition, gating and scope.
- `src/compiler_stress.py`, `src/stress_test.py`, `src/scoped_stress.py`: three independent test harnesses.
- `src/signal_adapter.py`: spectral features only; optional EDF reading; emotions and beliefs are always `None`.
- `results/gate_dev/`: one pre-confirmation seeded experiment, 62001.
- `results/gate_holdout/`: three independent benchmark seeds, 63011/12/13.
- `results/ood/`: fresh three-seed context-holdout, 64011/12/13.
- `results/gate_balanced/`: alternative calibration design on matched seeds, 63011/12/13.
- `results/random/`, `results/balanced/`, `results/pilot/`: earlier exploratory experiments. These are not promoted as independent confirmations.
- `results/*/watchdog_vs_baselines.csv`: paired world-seed cluster bootstrap intervals.

`bash run_all.sh` recomputes the unit tests, all three stress harnesses, the development experiment, the confirmatory holdout, strict context holdout, and equal-budget balanced design. When comparing outputs across hardware, compare numeric means to reported precision rather than elapsed seconds.

Data leakage controls: simulation mechanism parameters never enter policy features; future outcomes are generated after policy choice; every policy receives identical calibration data within each person. The strong generic exactly equivalent policy serves as a strict positive control of comparator fairness. Synthetic person draws within a world are not equivalent to a new independently collected human subject.