# Round 5 (§11.9) — what the registered tests showed

All tests ran as registered in [`AGENTS.md`](../AGENTS.md) §11.9; choices are in each module's docstring. Smoke runs used
unregistered seeds only. All earlier results stand.

| Test | Registered result | Sealed prediction | Detail |
|---|---|---|---|
| T-AP-4, agents v1 → person at pilot 4 | **Fail** — the primary passes (beats every comparator, fewer spikes, 0 false certificates); the confirmation does not (−0.014 per tick against no transfer on person model v2) | 0.50 | [`tapr.md`](tapr.md) |
| T-AP-V2, agents v2 → person | **Fail** (below pilot-only) | 0.15 | [`tapr.md`](tapr.md) |
| J1, jam predictor | **Accepted**: accuracy 0.754 on fresh seeds vs 0.685 for "never jam" and 0.315 for "always jam" | 0.55 | [`j1.md`](j1.md) |
| W5e, transfer with J1 in the tube | **Fail** — two directions beat every comparator again; person → agents v1 still has +0.06 spikes per target against pilot-only | 0.25 | [`w5e.md`](w5e.md) |
| **W5-R5, snapshot forge, agents** | **Fail — but beats repair, random change and doing nothing in two of three held-out regimes**; in the mid-run shift regime (E3) it falls below doing nothing | 0.30 | [`w5r5.md`](w5r5.md) |
| W5-R5, persons | **Fail** (equal to doing nothing) | 0.10 | [`w5r5.md`](w5r5.md) |

Brier score of round-5 predictions: 0.106. Running record: 0.230, 0.195, 0.079, 0.132, 0.106.

## The strongest result so far on failure repurposing

For the first time in five attempts, turning failures into mechanisms **improved** outcomes beyond doing nothing in
held-out conditions, with no extra spikes, at the strictest level used so far (two-sided 99.67%):

| Agents v2 | Forge − repair | Forge − random change | Forge − doing nothing |
|---|---|---|---|
| E1, fault storm | +0.108 [+0.094, +0.122] | +0.033 [+0.023, +0.041] | **+0.025 [+0.017, +0.034]** |
| E2, capture-prone (fast pressure) | +0.065 [+0.056, +0.074] | +0.013 [+0.007, +0.020] | **+0.010 [+0.005, +0.016]** |
| E3, shift at tick 121 | +0.066 [+0.058, +0.077] | −0.007 [−0.014, −0.000] | −0.022 [−0.027, −0.016] |

What carried it: **the mechanisms the failures shaped themselves.** Of 574 committed mechanisms, 493 were data-generated
swaps (in the failing context, run the mode with the lowest observed failure rate), not library entries. Snapshots let the
ghost passes start inside the context, and the raised bar (shown improvement) rejected 16,600 candidates. The Lion's
forecasts again beat the base rate (Brier 0.231, 0.169, 0.173 vs 0.246, 0.221, 0.199).

Why it still fails: **E3 changes the world halfway through.** Mechanisms forged from snapshots taken before the shift stay
active after it, and they no longer fit; the spike guard does not catch a loss of score without spikes. The registered rule
needs non-inferiority in all three regimes, so W5-R5 fails. The diagnosis matches a rule already written in §6 of this file
and never implemented: a pre-approved reflex is *re-verified when conditions change*.

## Transfer

Agents v1 → person keeps replicating at pilot 8 (W5e: +0.049 per tick over pilot-only, 0.33 fewer spikes per target) — the
fourth independent run where this direction meets every comparator. At pilot 4 it holds on person model v1 but not on v2, so
the confirmed claim stays at pilot 8. Agents v2 → person does not transfer. Person → agents v1 beats every comparator in
every round but adds spikes against pilot-only every time (+0.06 here), so two-direction transfer is still blocked by the
same direction. The J1 predictor, accepted on calibration, scored only 151 of 280 inside W5e: its accuracy came mostly from
directions where little is adopted, and it does not separate good from harmful candidates in person → agents v1.

## Next (new registrations; thresholds unchanged)

1. **W5-R6 = W5-R5 + re-verification.** At every window, each committed mechanism is re-tested from fresh snapshots; it is
   decommissioned when its lower bound against "no change" falls below zero. A drop in the run's recent mission score per
   context also counts as a failure for the guard, not only spikes. This targets E3 exactly.
2. **Person → agents v1:** register the spike issue as its own failure kind on the target side — candidates whose pilot
   spike count exceeds pilot-only's in that context are not adopted.
3. **Confirm W5-R5's E1/E2 pattern** as part of W5-R6's registered confirmation.
