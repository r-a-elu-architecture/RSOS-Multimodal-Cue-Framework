# Round 4 (§11.8) — what the registered tests showed

All tests ran as registered in [`AGENTS.md`](../AGENTS.md) §11.8; operational choices are in each module's docstring.
Smoke runs used only unregistered seeds. One gap was found and closed before reporting: the shared transfer code skips the
`W3C` comparator when the target is the person model v2, but the T-AP confirmation must meet *every* registered condition,
so the confirmation was rerun with `W3C` included ([`rsxv/tap_confirm_w3c.py`](../rsxv/tap_confirm_w3c.py); same seeds,
deterministic). All earlier results stand.

| Test | Registered result | Sealed prediction | Detail |
|---|---|---|---|
| **T-AP, transfer agents v1 → person** | **PASS — primary and confirmation** (new seeds, second person model, every comparator) | 0.45 | [`tap.md`](tap.md) |
| W5d, negative certificates + fail-safe tube | **Fail** (two directions beat every comparator; person → agents v1 has 0.02 more spikes per target than pilot-only) | 0.25 | [`w5d.md`](w5d.md) |
| W5-R4, anticipatory forge, agents | **Fail** (worse than doing nothing; more spikes) — but the Lion's forecasts beat the base rate in every regime | 0.35 | [`w5r4.md`](w5r4.md) |
| W5-R4, persons | **Fail** (equal to doing nothing) | 0.20 | [`w5r4.md`](w5r4.md) |
| MSE on the record (origin, not a test) | notes and phrases: re-entry and carry-forward strong; melody: replies inherit the previous reply's shape | — | [`mse_origin.md`](mse_origin.md) |

Brier score of round-4 predictions: 0.132. Running record: 0.230, 0.195, 0.079, 0.132.

## The first confirmed result

**T-AP: knowledge learned on software agents, transferred as certified functions through the gate, safely improves outcomes
for a simulated person — confirmed.** At a pilot of 8 targets, over 200 fresh targets and 20 pilot repetitions:

| | Primary (person model v1) | Confirmation (seeds + 100000, person model v2) |
|---|---|---|
| T-AP − pilot-only | +0.024 per tick [+0.021, +0.028] | +0.034 [+0.030, +0.039] |
| T-AP − no transfer | +0.202 [+0.187, +0.215] | +0.018 [+0.011, +0.024] |
| T-AP − random functions | +0.203 [+0.189, +0.217] | +0.018 [+0.011, +0.024] |
| T-AP − previous attempt (W3c) | +0.202 [+0.187, +0.215] | +0.018 [+0.011, +0.024] |
| Spikes vs pilot-only | −0.10 per target [−0.14, −0.07] | −0.004 (no increase) |
| False certificates | 0 of 41 adopted contexts | — |

**What it is:** the first registered, confirmed pass for cross-substrate transfer in this programme, after seven failed
attempts, and the first time transfer beats a target's own pilot by a clear margin (+0.024 and +0.034 per tick) while also
reducing spikes. **What it is not:** a two-direction result (that test, W5d, failed again on spikes), a result about
people (both substrates are stated models written by the same author — §11.1 disclosure), or a clinical claim. The direction
was chosen after it was seen twice; that is disclosed, and the confirmation on a second person model is what makes it count.

## What else the round shows

**W5d.** Negative certificates travelled and were applied (the person source warned against its DRIVE function in crisis;
agent sources warned against modes with no role). Two directions again beat every comparator, but person → agents v1 had
+0.02 spikes per target against pilot-only (interval [+0.01, +0.03]), so the safety rule fails it. The jam predictor was
weak: 132 of 260 predictions correct — barely better than chance. The fail-safe tube's rule (jam = gate refused, guard
removed or too little data) does not predict real harm.

**W5-R4.** Two parts behaved differently. **The Lion's forecasting works on agents:** Brier 0.206, 0.178, 0.167 against the
base rate's 0.241, 0.216, 0.191 — it predicts where failures will come better than a constant rate. **The forge does not:**
a 10-tick ghost pass rarely visits the context in question, so many candidates show zero difference and commit with no real
evidence — the same flaw as untested commits in W5-R2. On persons the Lion never forecast a failure above 0.5, so almost
nothing was forged. The wrong-model ablation (FORGE-NOISY) was no worse than the perfect-model forge, which confirms the ghost
passes carried little information.

**MSE (origin).** On the held-out half of the record: user turns share 31% of their content words with the reply just
before vs 13% for an older reply, and 8% of their 3–7-word phrases vs 0.05%; re-entered words reach the next reply 51
points more often than the person's own words (phrases: 24 points). Replies inherit the shape of the previous reply (0.55
similarity vs 0.49 for an older reply). The person's prompts do not take on the reply's shape. These are the origin
numbers; the registered test runs on public data in Phase 9.

## Next mechanism changes (new registrations, thresholds unchanged)

1. **Ghost passes that reach the context:** start each ghost copy in the target context (state forced into c) and run
   until c has been visited at least 10 times; no commit without at least 10 visits on each side.
2. **Lion as a gate, not only a trigger:** use the forecasts (which work) to schedule *live* probes only where and when a
   failure is predicted — testing in the context before the fire, with real data.
3. **Jam predictor from truth-like signals:** predict jams from the pilot's spike rate and effect estimate per context
   rather than from gate outcomes; score it before use.
4. **T-AP replication at a smaller pilot (4) and on agents v2 as source**, to map how far the confirmed transfer reaches.
