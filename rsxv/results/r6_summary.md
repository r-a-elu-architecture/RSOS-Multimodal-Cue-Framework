# Phase 7 (R6–R7) — what the registered tests showed

All four test sets ran exactly as registered in [`AGENTS.md`](../AGENTS.md) §11.5, with the operational choices listed in
each module's docstring fixed before the run. Smoke runs of the simulation code touched 20 of the held-out seeds for
debugging only; nothing in the design changed after them. Every failure stays on record.

| Test | Registered result | Sealed prediction | Detail |
|---|---|---|---|
| W5, transfer through the R4 layers (fifth attempt) | **Fail** | 0.30 | [`w5.md`](w5.md) |
| W5-R, agents | **Fail** (beats repair and random change in 2 of 3 regimes; raises spikes against repair in E1) | 0.45 | [`w5r.md`](w5r.md) |
| W5-R, persons | **Fail** (no mechanism was ever admitted, so repurposing equals doing nothing) | 0.35 | [`w5r.md`](w5r.md) |
| LIA-G, genealogy recovery | **Fail** (F1 0.12; beats temporal, not random) | 0.60 | [`lia_g.md`](lia_g.md) |
| C1 correction loss | Not testable / inconclusive | 0.85 | [`corpus_lineage.md`](corpus_lineage.md) |
| C2 summary drift | Not testable | 0.70 | |
| C3 format decay | **Fail** (no decay) | 0.75 | |
| C4 term adoption | **Pass** | 0.80 | mostly verbatim re-entry of output as input |
| C5 refuse-then-comply | Not testable | 0.40 | |
| C6 failure → mechanism | Inconclusive (labeller invalid) | 0.65 | |

**Calibration (floor 4 record).** Six tests resolved to pass or fail. Brier score of the sealed predictions: 0.230
(a constant 0.5 would score 0.25). Predictions were over-optimistic on every simulation test.

## What the results show

**W5.** Function certificates were accurate: 0 false certificates in 27 adopted contexts (the audit held). The bottleneck
was the pilot, not the certificate. The failure-driven pilot *starved* the gate further: it alternates with the baseline only
in contexts that just failed, so most contexts never get the 5 baseline ticks the gate needs. The ablation that alternates in
every certified context beat W5 by +0.12 per tick (agents v1 → person, pilot 8) and pilot-only beat W5 in three directions.
The random-certificate control was identical to W5 whenever a source certified the same function in every context (person
and agents v1 both did), so that comparator could not be beaten by construction — a design flaw in the registration.
W5's spikes were lower than no transfer (2.23 vs 2.45 per target) but higher than pilot-only, so the safety gate failed.

**W5-R.** On agents, turning failures into named mechanisms beat ordinary repair by +0.055 and +0.049 per tick (E2, E3) and
beat random changes of the same count by +0.013 and +0.007, but not in the trigger storm (E1), where it also produced more
spikes than repair. On persons the gate never admitted a mechanism: the trained table uses one archetype everywhere, so the
baseline cell the gate needs is empty. Every one of 34,000 failure nodes closed with a named outcome; no silent closes, no
stale open nodes, no audit failures — the bookkeeping layer works.

**LIA-G.** Two causes, both diagnosable (exploratory): the change detector found only 43% of the planted (time, context)
changes from behaviour, and the registry opens a node on the *first* failure of a kind in a maintenance cycle while the
reconstructor picks the *most recent* one (a median of 4 same-context failures per window). The parent failure itself was
always re-detected from the trace.

**Corpus.** One long conversation is too thin for C1, C2 and C5, and the word-rule labeller is invalid for C6 (3 of 26
sampled candidates were real failure events). C4 passes, and what it really shows is that 28% of user turns paste verbatim
spans of the previous assistant output back in as the next prompt.

## Mechanism changes for the next attempt (new registrations; thresholds unchanged)

1. W5 pilot: alternate with the baseline in every certified context, and give failed contexts *extra* alternation instead of
   *only* them; replace RANDOM-CERT with a control that also permutes functions when all contexts share one.
2. W5-R: gate repurposing proposals against the status-quo archetype in that context (not Lion), with a non-harm bound;
   add a spike guard so a mechanism that raises spikes is rolled back at the next window.
3. LIA-G: parent = first unresolved same-kind failure since the last maintenance window (the registry's rule, read as an
   architectural property); detect changes from per-context mode distributions with a likelihood test.
4. Corpus: hand or model labels with a second labeller for C1 and C6; multi-session data for C2 and C5; split C4 into
   verbatim re-entry and own use, and register re-entry as an LSGPA test.
