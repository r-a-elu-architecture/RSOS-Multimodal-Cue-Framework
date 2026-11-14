"""Round 7 (AGENTS.md §11.12): person model v3 — hand-set vs fitted on the owner's record — and safety-layer recall.

    python3 -m rsxv.v3_person handset OUT.json            # hand-set transition table by simulation (no record needed)
    python3 -m rsxv.v3_person run TURNS.json LABELS.json HANDSET.json PRIVATE_DIR PUBLIC.json

Operational choices (fixed before labels were read):
- Bands: low = distress < 4, moderate = 4–6.99, high ≥ 7 (simulated distress on its 0–10 scale).
- HAND-SET simulation: at every tick the mode is BEAR with probability 0.5, else LION (independent of state), so every
  condition (band, trigger, override) is populated; the transition table is conditional on those, so the rate does not
  enter the prediction. "Trigger" = the simulated environment started a trigger episode on that tick.
- Conditions with no simulated (or development) data fall back to the band-only row, then the overall marginal.
- A held-out prediction needs the current and next user turns both labelled with a band (not unclear); a turn's
  condition uses its own trigger and override labels.
- SR-ORACLE maps labels to events: band high → distress 8; screen label → its structured flags. It is a consistency check of
  the rules given a perfect reading.
"""
from __future__ import annotations

import collections
import json
import math
import pathlib
import random
import sys

BANDS = ("low", "moderate", "high")


def band_of(d):
    return "low" if d < 4 else "moderate" if d < 7 else "high"


def handset(out):
    from .person2 import PersonEnvV2
    cnt = collections.defaultdict(lambda: collections.Counter())
    for seed in range(300000, 302000):
        env = PersonEnvV2(seed, safety_on=False)
        rng = random.Random(seed + 7)
        b = band_of(env.body.s["distress"])
        for _ in range(200):
            mode = "BEAR" if rng.random() < 0.5 else "LION"
            n_ev = len(env.events)
            env.step(mode)
            trig = len(env.events) > n_ev
            nb = band_of(env.body.s["distress"])
            cnt[(b, trig, mode == "BEAR")][nb] += 1
            b = nb
    tab = {f"{k[0]}|{int(k[1])}|{int(k[2])}": dict(v) for k, v in cnt.items()}
    pathlib.Path(out).write_text(json.dumps(tab, indent=1))
    print(json.dumps(tab, indent=1))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "handset":
        handset(a[1])
