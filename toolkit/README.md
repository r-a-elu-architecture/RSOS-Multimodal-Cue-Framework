# rsos_cue — few-shot personalization of multimodal cue programs

`rsos_cue` picks the best **cue program** for one person from a few noisy trials. A program is a glyph × sound × rehearsal plan, used in a context. It does this by borrowing strength from other people's histories.

It is the open, runnable core of the RSOS / RSIA / RSX / RSSO framework, packaged so other groups can run it with real participants and pool data in one format.

**Status:** research software, validated on synthetic benchmarks only. No human, neural or clinical efficacy has been measured. Its purpose is to make that measurement possible.

## Install and run

```bash
pip install numpy scipy pandas
python -m unittest discover -s tests          # 8 tests
python examples/quickstart.py
```

```python
from rsos_cue import ProgramSpace, ArchetypeBank, CueSession
space = ProgramSpace(n_glyph=12, n_sound=5, n_plan=3, n_context=4, families=[0,0,0,1,1,1,2,2,2,3,3,3])
bank  = ArchetypeBank(space).fit(histories, K=8)      # pooled data from earlier participants
s = CueSession(bank, reports=ratings)                  # a new person's glyph/sound ratings (optional)
q = s.next_probe(); s.add(q['glyph'], q['sound'], q['plan'], q['context'], outcome)
s.recommend(context=0, k=3); s.watchdog(); s.report_trust()
```

## How it works

| Archive concept | Implementation |
|---|---|
| RSOS glyph families, RSX (glyph, sound, plan) command | Hierarchical effect blocks: family → glyph → program, with context and plan interactions |
| RSIA Archetypes, RSSO MEMSTACK / CM1 | `ArchetypeBank.fit`: label-free EM compresses many people into K response modes |
| RSIA Watchdog | `CueSession.watchdog()`: one person's posterior over archetypes (soft switching) |
| RSX FutureProjection | `next_probe()`: the trial that most reduces uncertainty about current contenders |
| RSSO CONTAIN | Twins that ignore self-ratings and allow program-specific effects |
| RSIA Meta-Architect | The person's own archetype, including learned trust in their ratings (`report_trust()`) |
| LIA ancestry recovery | `discover_families()`: glyph families from population rating correlations |

All inference is exact linear-Gaussian algebra (numpy and scipy). `ProgramSpace(families=None)` gives the generic comparator with no family structure, which any claim about RSOS-specific value must beat.

## Data format and studies

- `rsos_cue/data.py` defines `trials.csv` and `reports.csv`.
- `study_kit/PROTOCOL.md` is an open replication protocol for a neutral memory task.
- `study_kit/power.py` does simulation-based sample-size planning; results are in `study_kit/power_table.txt`.

## Validation

See `VALIDATION.md` for all synthetic results, including the failures.
