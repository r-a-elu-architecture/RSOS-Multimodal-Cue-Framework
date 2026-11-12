"""Shared data format so studies run by different groups are comparable and poolable.

trials.csv   (one row per trial)
  study_id, person_id, trial_index, context, glyph, sound, plan, outcome, outcome_name,
  timestamp_utc, consent_version, condition
reports.csv  (optional; one row per prior rating)
  study_id, person_id, kind ('glyph'|'sound'), index, rating

All ids are integers starting at 0 within the study's declared ProgramSpace. 'outcome' must be
oriented so higher is better (e.g. recall accuracy, or minus reaction time) and standardised
within study before pooling. No names, free text or raw physiological streams belong in these files.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

TRIAL_COLUMNS = ['study_id', 'person_id', 'trial_index', 'context', 'glyph', 'sound', 'plan', 'outcome',
                 'outcome_name', 'timestamp_utc', 'consent_version', 'condition']
REPORT_COLUMNS = ['study_id', 'person_id', 'kind', 'index', 'rating']


def load_trials(path):
    d = pd.read_csv(path)
    missing = [c for c in ['person_id', 'context', 'glyph', 'sound', 'plan', 'outcome'] if c not in d]
    if missing: raise ValueError(f'trials file missing columns: {missing}')
    return d


def load_reports(path):
    d = pd.read_csv(path)
    if not {'person_id', 'kind', 'index', 'rating'} <= set(d): raise ValueError('reports file missing columns')
    return d


def histories_from_frames(space, trials, reports=None):
    out = []
    for pid, t in trials.sort_values(['person_id', 'trial_index'] if 'trial_index' in trials else ['person_id']).groupby('person_id'):
        h = dict(person_id=pid, programs=t[['glyph', 'sound', 'plan']].to_numpy(int), contexts=t['context'].to_numpy(int),
                 outcomes=t['outcome'].to_numpy(float))
        if reports is not None:
            r = reports[reports.person_id == pid]
            vec = np.full(space.n_glyph + space.n_sound, np.nan)
            for _, row in r.iterrows():
                vec[int(row['index']) + (0 if row['kind'] == 'glyph' else space.n_glyph)] = row['rating']
            if np.isnan(vec).any(): continue  # complete report vectors only in v0.1
            h['reports'] = vec
        out.append(h)
    return out


def discover_families(glyph_reports, max_k=8, min_gain=0.02):
    """LIA: group glyphs whose population ratings co-vary. glyph_reports: (people, n_glyph)."""
    from scipy.cluster.hierarchy import linkage, fcluster
    from scipy.spatial.distance import squareform
    C = np.corrcoef(np.asarray(glyph_reports, float).T); D = 1 - C; np.fill_diagonal(D, 0)
    Z = linkage(squareform(D, checks=False), 'average'); n = C.shape[0]; best = None
    for k in range(2, min(max_k, n - 1) + 1):
        lab = fcluster(Z, k, 'maxclust') - 1
        iu = np.triu_indices(n, 1); same = lab[iu[0]] == lab[iu[1]]
        if same.sum() == 0 or (~same).sum() == 0: continue
        gap = C[iu][same].mean() - C[iu][~same].mean()
        if best is None or gap > best[0] + min_gain: best = (gap, k, lab)
    return (best[2].tolist(), dict(k=best[1], within_minus_between_corr=float(best[0]))) if best else (None, {})
