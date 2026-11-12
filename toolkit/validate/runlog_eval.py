"""Does the cue engine find each person's best program, tier and voice from run logs?

Synthetic, from examples/simulate_runlog.py (invented response types). For each held-out person the
engine gets a budget of runs, chosen by its own probing or at random, then recommends one setting per
trigger type. Regret = true best gain in that trigger context minus true gain of the recommendation
(rating points; lower is better). Baseline: the setting that is best on average in the pooled logs.

Usage: python validate/runlog_eval.py [n_test_people] [seeds]
"""
import itertools
import pathlib
import sys

import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parent / "examples")]
from rsos_cue import ArchetypeBank, CueSession, space_from_runlog, histories_from_runlog, describe  # noqa: E402
import simulate_runlog as sim  # noqa: E402

N_TEST = int(sys.argv[1]) if len(sys.argv) > 1 else 30
SEEDS = int(sys.argv[2]) if len(sys.argv) > 2 else 3
BUDGETS = (5, 10, 20)


def true_gain(t, names):
    return sim.benefit(t, names["protocol"], names["tier"], names["voice"], names["trigger_channel"])


rows = []
for seed in range(SEEDS):
    log = sim.simulate(n_people=60, seed=100 + seed)
    space, cb = space_from_runlog(log)
    bank = ArchetypeBank(space).fit(histories_from_runlog(log, cb), K=3, iters=8, seed=seed)
    pooled = log.assign(g=(log.sud_before - log.sud_after) + (log.agency_after - log.agency_before))
    pop_best = {trig: pooled[pooled.trigger_channel == trig].groupby(["protocol", "tier", "voice"]).g.mean().idxmax()
                for trig in cb["context"]}
    rng = np.random.default_rng(seed)
    for person in range(N_TEST):
        k = int(rng.integers(len(sim.TYPES))); t = sim.TYPES[k]
        def gain(g, s, p, c):
            return true_gain(t, describe(cb, (g, s, p), c))
        best = {c: max(gain(g, s, p, c) for g, s, p in itertools.product(*map(range, (space.n_glyph, space.n_sound, space.n_plan))))
                for c in range(space.n_context)}
        for c, trig in enumerate(cb["context"]):
            proto, tier, voice = pop_best[trig]
            pick = (cb["glyph"].index(tier), cb["sound"].index(voice), cb["plan"].index(proto))
            for B in BUDGETS:
                rows.append(dict(seed=seed, person=person, budget=B, method="population best (fixed)", regret=best[c] - gain(*pick, c)))
        for method in ("engine, own probes", "engine, random runs"):
            s = CueSession(bank, explore=4 if "own" in method else 10**6, seed=person + 1000 * seed)
            done = 0
            for B in BUDGETS:
                while done < B:
                    q = s.next_probe()
                    s.add(q["glyph"], q["sound"], q["plan"], q["context"], gain(q["glyph"], q["sound"], q["plan"], q["context"]) + rng.normal(0, 1.0))
                    done += 1
                for c in range(space.n_context):
                    g, sd, p = s.recommend(c, 1)[0]["program"]
                    rows.append(dict(seed=seed, person=person, budget=B, method=method, regret=best[c] - gain(g, sd, p, c)))

df = pd.DataFrame(rows)
out = df.groupby(["budget", "method"]).regret.agg(["mean", "sem"]).round(3)
print(out.to_string())
(HERE / "results").mkdir(exist_ok=True)
out.to_csv(HERE / "results" / "runlog_eval.csv")
