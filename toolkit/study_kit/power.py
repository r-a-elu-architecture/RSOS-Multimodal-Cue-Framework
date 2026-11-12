"""Simulation-based sample-size planning for a within-person human study.

Each participant: 24 calibration trials, then n_test trials under each arm (personalized, comparator).
Per-participant true benefit is resampled from simulated people; human effects are assumed to be a
fraction `scale` of the simulated ones; each test trial adds outcome noise `trial_sd`.
Approximation: scaling is applied to the benefit, not re-learned under smaller effects (optimistic for small scale).

Usage: python power.py per_person_benefits.csv  (columns: person, benefit_vs_<arm>...)
"""
import sys, numpy as np, pandas as pd
from scipy import stats

def power(benefit, n, scale, n_test, trial_sd=.2, alpha=.05, reps=4000, seed=0):
    rng = np.random.default_rng(seed); b = np.asarray(benefit) * scale; hits = 0
    for _ in range(reps):
        d = rng.choice(b, n) + rng.normal(0, trial_sd * np.sqrt(2 / n_test), n)
        hits += stats.ttest_1samp(d, 0).pvalue < alpha and d.mean() > 0
    return hits / reps

def table(benefits: pd.DataFrame, Ns=(10, 20, 40, 80, 160), scales=(1, .5, .25), n_tests=(16, 48)):
    rows = []
    for col in [c for c in benefits if c.startswith('benefit_vs_')]:
        for sc in scales:
            for nt in n_tests:
                rows.append(dict(comparator=col[11:], effect_scale=sc, test_trials_per_arm=nt,
                                 mean_benefit=round(benefits[col].mean() * sc, 4),
                                 **{f'N={n}': power(benefits[col].dropna(), n, sc, nt) for n in Ns}))
    return pd.DataFrame(rows)

if __name__ == '__main__':
    print(table(pd.read_csv(sys.argv[1])).to_string(index=False))
