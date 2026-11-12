# rsos_cue — the personalised cue engine

`rsos_cue` learns **which program, tier and voice work best for each person and each kind of trigger**, from a few runs, by borrowing strength from other people's run logs. It reads the run log exported by the [protocol player](../docs/player.html) (or written by `rsx.RunRecord`) directly:

| Run-log column | Engine dimension |
|---|---|
| `tier` (e.g. LION) | glyph / tier bundle |
| `voice` (own, computer, none) | sound |
| `protocol` (override, swish, interrupt_only, …) | plan |
| `trigger_channel` (V, A, K, O, G, thought, memory) | context |
| distress drop + agency gain | outcome |

**Status:** working software, tested on synthetic run logs and, as an outside check of the algorithm, on public movie and book ratings. No human outcome data exists yet; its purpose is to learn from such data as soon as it does.

## Install and run

```bash
pip install numpy scipy pandas
python -m unittest discover -s tests          # 10 tests
python examples/quickstart.py                 # pooled logs -> bank -> personalise a new person
python validate/runlog_eval.py                # synthetic evaluation (about 1 minute)
```

```python
import pandas as pd
from rsos_cue import ArchetypeBank, CueSession, space_from_runlog, histories_from_runlog, describe
log = pd.read_csv("runs.csv")                                   # pooled player exports
space, codebook = space_from_runlog(log)
bank = ArchetypeBank(space).fit(histories_from_runlog(log, codebook), K=3)
s = CueSession(bank)                                            # a new person
q = s.next_probe()                                              # what to try next
print(describe(codebook, (q["glyph"], q["sound"], q["plan"]), q["context"]))
# ... run it, then s.add(q["glyph"], q["sound"], q["plan"], q["context"], gain)
best = s.recommend(context=0, k=1)[0]; print(describe(codebook, best["program"]))
```

## How it works

| Archive concept | Implementation |
|---|---|
| RSOS tiers and glyph families, RSX programs | Hierarchical effect blocks: family → glyph → program, with context and plan interactions |
| RSIA Archetypes, RSSO MEMSTACK / CM1 | `ArchetypeBank.fit`: label-free EM compresses many people into K response modes |
| RSIA Watchdog | `CueSession.watchdog()`: one person's posterior over archetypes (soft switching) |
| RSX FutureProjection | `next_probe()`: the trial that most reduces uncertainty about current contenders |
| RSSO CONTAIN | Twins that ignore self-ratings and allow program-specific effects |
| RSIA Meta-Architect | The person's own archetype, including learned trust in their ratings (`report_trust()`) |
| LIA ancestry recovery | `discover_families()`: glyph families from population rating correlations |

All inference is exact linear-Gaussian algebra (numpy and scipy). `ProgramSpace(families=None)` gives the generic comparator with no family structure, which any claim about RSOS-specific value must beat.

## Data and studies

- `rsos_cue/runlog.py` reads the RSOS run log; `rsos_cue/data.py` defines a more general trials format for studies with other cue dimensions.
- `study_kit/PROTOCOL.md` is a study kit for testing the Override Protocol hypotheses; `study_kit/power.py` gives sample sizes.

## Validation

See `VALIDATION.md`.
