# Round 6 (§11.10) — W5-R6, the snapshot forge with re-verification: what the registered test showed

Run as registered in [`AGENTS.md`](../AGENTS.md) §11.10; choices in [`rsxv/w5r6_experiments.py`](../rsxv/w5r6_experiments.py).
Smoke run on unregistered seeds only. Details: [`w5r6.md`](w5r6.md). All earlier results stand.

**Result: fail on both substrates** (sealed predictions 0.35 agents, 0.05 persons; Brier 0.063). No confirmation was run,
because the primary failed.

| Agents v2 (two-sided 99.72%) | Forge6 − repair | Forge6 − random change | Forge6 − doing nothing | Forge6 − Forge5 (ablation) |
|---|---|---|---|---|
| E1, fault storm | +0.174 [+0.158, +0.192] | +0.016 [+0.009, +0.025] | **+0.007 [+0.001, +0.014]** | −0.006 [−0.013, +0.001] |
| E2, fast pressure | +0.103 [+0.093, +0.113] | +0.006 [+0.001, +0.012] | +0.001 [−0.003, +0.006] | +0.002 [−0.002, +0.008] |
| E3, shift at tick 121 | +0.133 [+0.124, +0.140] | +0.006 [−0.001, +0.013] | −0.009 [−0.013, −0.005] | **+0.016 [+0.011, +0.021]** |

**What re-verification did.** It worked where it was aimed: in the shift regime it improved on the forge without it by
+0.016 per tick and cut the gap to doing nothing from −0.022 (round 5) to −0.009 — but the lower bound (−0.013) is still past
the −0.01 margin, so non-inferiority fails. 452 mechanisms were decommissioned (229 by re-verification, 220 by the score-drop
guard, 3 by the spike guard), and every failure node closed with a named outcome.

**What did not hold.** On fresh seeds the E2 gain seen in round 5 did not replicate: here neither the forge with
re-verification (+0.001) nor the round-5 forge itself (−0.001) beats doing nothing in E2. The only repurposing gain that has
now held on two independent seed sets is in **E1, the fault storm** (+0.025 in round 5, +0.007 here). On persons the
forge again equals doing nothing.

**Reading across six rounds.** In these agent models, failure-shaped mechanisms (data-generated swaps, 560 of 582 commits
here) give small, real gains under a fault storm and lose a little after a regime shift; re-verification recovers most, not
all, of that loss. The fixed-library versions never helped. The bookkeeping, the Lion's forecasts (Brier 0.222, 0.147, 0.144
vs base rate 0.243, 0.207, 0.181) and the safety discipline hold in every round.
