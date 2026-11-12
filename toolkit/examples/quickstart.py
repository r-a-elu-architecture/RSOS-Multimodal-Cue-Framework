"""Quickstart: fit a bank from pooled studies, then personalize for a new person."""
import pathlib, sys
import numpy as np, pandas as pd
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from rsos_cue import ProgramSpace, ArchetypeBank, CueSession, load_trials, load_reports, histories_from_frames

space = ProgramSpace(n_glyph=12, n_sound=5, n_plan=3, n_context=4, families=[0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3])

# 1. Population: pooled trials.csv / reports.csv from previous participants (schema in rsos_cue/data.py)
try:
    hist = histories_from_frames(space, load_trials('trials.csv'), load_reports('reports.csv'))
    bank = ArchetypeBank(space).fit(hist, K=8)
except FileNotFoundError:
    bank = ArchetypeBank.load(HERE / 'bank_v13sim.json')   # bank fitted on the v1.3 simulator (synthetic)

# 2. A new person: prior ratings of 12 glyphs + 5 sounds (standardized), then trials
s = CueSession(bank, reports=np.zeros(17))
for _ in range(24):
    q = s.next_probe()                       # which (glyph, sound, plan, context) to try next
    outcome = np.random.normal(.5, .2)       # <- replace with the measured outcome
    s.add(q['glyph'], q['sound'], q['plan'], q['context'], outcome)

print('best programs in context 0:', s.recommend(0, k=3))
H, w = s.watchdog(); print('archetype posterior:', np.round(w, 2))
