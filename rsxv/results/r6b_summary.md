# Phase 7b (R6b) — second round: what the registered tests showed

All tests ran as registered in [`AGENTS.md`](../AGENTS.md) §11.6, with operational choices fixed in each module's docstring
before the run. Smoke runs used only seeds outside the registered ranges. One implementation fix was made after a smoke run
(W5-R2 gate data keyed by the policy's own context, where probes act); it is disclosed in the module docstring. Every result
stays on record; §11.5 results are unchanged.

| Test | Registered result | Sealed prediction | Detail |
|---|---|---|---|
| W5-R2, persons | **Pass, confirmed** (new seeds + second install hypothesis) — but see below: it passes by doing no harm, not by helping | 0.10 | [`w5r2.md`](w5r2.md), [`w5r2_confirmation.md`](w5r2_confirmation.md) |
| W5-R2, agents | **Fail** (worse than doing nothing in all three regimes, more spikes) | 0.35 | [`w5r2.md`](w5r2.md) |
| W5b, transfer (sixth attempt) | **Fail** on the safety gate only: two directions beat pilot-only, no transfer and random functions — a first — but in agents v1 → person W5b had 0.06 more spikes per target than pilot-only | 0.20 | [`w5b.md`](w5b.md) |
| LIA-G2 | **Fail** (F1 0.12; now beats temporal and random) | 0.30 | [`lia_g2.md`](lia_g2.md) |
| C1b | Inconclusive (kappa 0.50) | 0.35 | [`corpus_v2.md`](corpus_v2.md) |
| C6b | Inconclusive (mechanism-turn kappa 0.59) | 0.40 | |
| C4b own-use adoption | **Pass** | 0.55 | |
| R1 verbatim re-entry (LSGPA) | **Pass** | 0.90 | |
| R2 re-entry propagates (LSGPA) | **Pass** (weak comparator; exploratory within-prompt check +0.43) | 0.70 | |

**Calibration.** Seven tests resolved to pass or fail; Brier score 0.195 (round 1: 0.230; constant 0.5: 0.25). The large
miss is W5-R2 on persons (predicted 0.10, passed).

## What the results show

**W5b — transfer works, the safety rule stops it.** With the pilot comparing against the baseline on every visit, transfer
beat pilot-only, no transfer and random functions in agents v1 → person (+0.002 over pilot-only, +0.20 over no transfer)
and person → agents v1 (+0.001, +0.10). Certificates were accurate (0 false of 96 adopted contexts). The registered safety
gate applies against every comparator, and W5b produced 0.06 more spikes per target than pilot-only in agents v1 → person
(while cutting spikes by 1.09 per target against no transfer). The margins over pilot-only are small: transfer adds a
little beyond a pilot of 8; most of the gain is the pilot itself.

**W5-R2 on persons — a do-no-harm pass.** Repurposing scored exactly the same as doing nothing (difference 0.0000) and beat
ordinary repair and random changes because those two *cost* something (repair runs the baseline for 5 ticks; random
mechanisms disturb a policy that was already right). The committed person mechanisms added no new archetype, because the
trained person policy already stabilises everywhere. So the pass shows the architecture's discipline — it only commits what
is shown not to harm, and every one of ~350 committed changes held — not that repurposing improves a person's outcome.

**W5-R2 on agents — the shortcut was the flaw.** Mechanisms that add no *new* archetype (hysteresis, snapshot-first,
stabilise-first when the status quo already stabilises) committed without a test, yet they change behaviour on other ticks.
They lowered scores in every regime and raised spikes; the spike guard rolled back about 300 of them, too late. Probes
almost never gathered enough data in one 25-tick cycle (1 commit from ~3,900 probes).

**LIA-G2.** The first-failure parent rule now beats temporal proximity and random choice clearly (+0.11 and +0.09 F1), but
change detection finds only 40% of planted changes and the parent is right 38% of the time when the slot is found; person
changes (mostly hysteresis) leave almost no behavioural trace.

**Corpus.** The strongest finding of the whole programme on real data: output re-enters as input (R1: 18% of held-out user
turns contain a verbatim span of the reply just before, against 0.002% for older replies), and re-entered words carry into
the next reply far more than the person's own words in the same prompt (73% vs 30%, exploratory). Meaning-based labels
agreed well for failure events (kappa 0.91) but not for mechanism turns or corrections, which are too rare in one
conversation.

## Next mechanism changes (new registrations; thresholds and the safety rule unchanged)

1. W5c: keep the W5b pilot; add the spike guard to the transfer pilot (a context whose adopted archetype raises spikes in the
   pilot is not adopted). This targets exactly the failure that blocked W5b.
2. W5-R3: no untested commits — every mechanism that changes behaviour gets a probe, probes last until both cells hold ≥ 5
   ticks (up to three cycles); runs of 240 ticks so probes can finish.
3. LIA-G3: give the reconstructor the mechanism signature of hysteresis (switch-rate change per context) as a first-class
   signal; longer runs.
4. LSGPA: register the within-prompt comparison (re-entered words vs the person's own words) on public multi-session data.
