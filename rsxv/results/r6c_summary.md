# Round 3 (§11.7) — what the registered tests showed

All tests ran as registered in [`AGENTS.md`](../AGENTS.md) §11.7; operational choices are in each module's docstring.
Smoke runs used only unregistered seeds. One fix before the registered W5c run: the `RANDOM-FUNC` comparator had picked up
the new spike guard by default; the registration says comparators are unchanged, so it was switched off for that arm before
the run that counts. All earlier results stand.

| Test | Registered result | Sealed prediction | Detail |
|---|---|---|---|
| W5c, transfer with a pilot spike guard (seventh attempt) | **Fail** — agents v1 → person meets every condition including safety; the second direction needed for a pass does not | 0.30 | [`w5c.md`](w5c.md) |
| W5-R3, agents | **Fail** (probing costs score; 5 commits from ~8,100 probes) | 0.25 | [`w5r3.md`](w5r3.md) |
| W5-R3, persons | **Fail** (equal to doing nothing; ties random change) | 0.20 | [`w5r3.md`](w5r3.md) |
| LIA-G3 | **Fail** (only 8 committed changes to recover; not a meaningful test) | 0.35 | [`lia_g3.md`](lia_g3.md) |

Brier score of the round-3 predictions: 0.079 (all four predicted below 0.5, all four failed). Running record: round 1 0.230,
round 2 0.195, round 3 0.079.

## What three rounds now show

**1. Agents → person transfer is real in these models, and only in that direction.** In both W5b and W5c, at a pilot of 8,
transfer from agents v1 to the simulated person beat pilot-only (+0.002, +0.007), no transfer (+0.20 both times) and random
functions, with no false certificates. In W5c it also cut spikes against every comparator (−0.07 per target vs pilot-only,
−1.16 vs no transfer) — the first time any transfer arm met every condition in a direction. The reverse directions are
unstable: person → agents v1 met every comparison in W5b and failed in W5c once the guard removed contexts; agents v2 → person
and person → agents v2 never did. The registered criterion needs two directions, so W5c fails.

**2. The repurposing library has nothing to give in these models.** With every change tested (W5-R3), the non-harm probe
rejected almost every mechanism — 1 commit per ~1,600 probes. The trained policies are already near the best these
environments allow, and the six hand-written mechanisms do not improve them; probing them costs score on agents. The safety
discipline works (bad changes are refused, rollbacks are rare), but the premise that a fixed library turns failures into
improvements is not supported. The failure node bookkeeping held throughout: no silent closes, no stale nodes.

**3. Genealogy recovery needs changes to recover.** With almost no commits, LIA-G3 had nothing to test. LIA-G2 (round 2) is
the informative result: the architecture's own parent rule beats temporal proximity and chance, but far below F1 0.70.

## Proposed next registrations (new hypotheses, disclosed origin, fresh seeds, thresholds unchanged)

1. **T-AP, directional transfer agents → person.** The pattern seen in W5b and W5c becomes its own hypothesis: W5c design,
   agents v1 → person only, all conditions as registered, confirmation on + 100000 seeds and the second person model. Origin
   disclosed as observed in two earlier runs; level corrected for all eight transfer attempts.
2. **W5-R4, generated mechanisms.** Replace the fixed library with candidates generated from the failure itself: the Eagle
   step proposes three variants (ghost passes on a copy of the recent state), the best non-harmful one is probed. Tests the
   repurposing principle as the corpus describes it — the failure shapes the new mechanism — rather than a lookup table.
3. **LSGPA R3 on public data** (Phase 9), as already registered.
