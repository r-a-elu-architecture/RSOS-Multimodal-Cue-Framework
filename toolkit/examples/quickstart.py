"""Quickstart: learn from pooled run logs, then personalise for a new person.

1. Pool the run logs (CSV from the protocol player, or rsx RunRecord) of earlier participants.
2. Fit a bank of response modes.
3. For a new person, let the engine choose which program, tier and voice to try next,
   then recommend the best combination for each trigger type.

Without real logs it uses synthetic ones (examples/simulate_runlog.py) and says so.
"""
import pathlib
import sys

import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from rsos_cue import ArchetypeBank, CueSession, space_from_runlog, histories_from_runlog, describe  # noqa: E402
import simulate_runlog as sim  # noqa: E402

real = HERE / "runs.csv"
if real.exists():
    log = pd.read_csv(real); print(f"Using {real.name}: {len(log)} runs")
else:
    log = sim.simulate(); print(f"No runs.csv found: using {len(log)} SYNTHETIC runs from {log.participant.nunique()} invented people")

space, codebook = space_from_runlog(log)
bank = ArchetypeBank(space).fit(histories_from_runlog(log, codebook), K=3, iters=8)

# A new person of hidden type 0 (synthetic). Replace `measure` with real runs.
rng = np.random.default_rng(1); t = sim.TYPES[0]
def measure(q):
    names = describe(codebook, (q["glyph"], q["sound"], q["plan"]), q["context"])
    return sim.benefit(t, names["protocol"], names["tier"], names["voice"], names["trigger_channel"]) + rng.normal(0, 1.0)

s = CueSession(bank, seed=0)
for _ in range(15):
    q = s.next_probe()
    s.add(q["glyph"], q["sound"], q["plan"], q["context"], measure(q))

print("\nBest settings for this person, by trigger type:")
for c, trig in enumerate(codebook["context"]):
    best = s.recommend(c, k=1)[0]
    print(f"  {trig:8s} -> {describe(codebook, best['program'])}  (predicted gain {best['predicted']:+.1f})")
H, w = s.watchdog(); print("\nResponse-mode posterior (Watchdog):", np.round(w, 2))
