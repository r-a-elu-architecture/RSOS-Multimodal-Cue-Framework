# W3b — role-based transfer: results

Designs, seeds and pass criteria were fixed in [`../AGENTS.md`](../AGENTS.md) §11.3 and committed before this code
was written. The hypothesis came from an exploratory look at the floor-3 truth cohorts (disclosed there). All
environments are stated models; **no number here comes from people or production agents.** Mission score per tick;
paired bootstrap 95% intervals over 200 deployment targets.

Source roles: `{"person": {"RESTORE": "BEAR", "DRIVE": "LEOPARD"}, "agent": {"RESTORE": "LEOPARD", "DRIVE": "TIGER"}, "agent_v2": {"RESTORE": "LEOPARD", "DRIVE": "TIGER"}}`.
Source tables: `{"person": {"calm": "BEAR", "rising": "BEAR", "loaded": "BEAR", "crisis": "BEAR"}, "agent": {"calm": "LEOPARD", "rising": "LEOPARD", "loaded": "LEOPARD", "crisis": "LEOPARD"}, "agent_v2": {"calm": "LEOPARD", "rising": "LEOPARD", "loaded": "TIGER", "crisis": "LION"}}`.

## agent → person, pilot of 5 targets

Role table: `{"calm": "RESTORE", "rising": "RESTORE", "loaded": "RESTORE", "crisis": "RESTORE"}`. Target roles (half A): `{"RESTORE": "BEAR", "DRIVE": "LEOPARD"}`. ROLE deployed: `{"calm": "LION", "rising": "LION", "loaded": "LION", "crisis": "LION"}`.

| Arm | Mean / tick |
|---|---|
| ROLE | -0.0902 |
| PILOT-BONF | -0.0902 |
| PILOT-SPLIT | -0.0902 |
| NAME-GATED | -0.0902 |
| NONE | -0.0902 |
| ORACLE | +0.2366 |
| ROLE-RANDOM | -0.0902 |
| ROLE-SHUFFLED | -0.0902 |

| Contrast | Estimate [95% interval] |
|---|---|
| ROLE-NONE | +0.000 [+0.000, +0.000] |
| ROLE-PILOT-BONF | +0.000 [+0.000, +0.000] |
| ROLE-PILOT-SPLIT | +0.000 [+0.000, +0.000] |
| ROLE-ROLE-RANDOM | +0.000 [-0.000, +0.000] |
| ROLE-ROLE-SHUFFLED | -0.000 [-0.000, +0.000] |
| ROLE-NAME-GATED | +0.000 [+0.000, +0.000] |
| ROLE-ORACLE | -0.327 [-0.333, -0.319] |

| Context | Candidate | Decision | Pilot est. | Bound | Truth | False admit |
|---|---|---|---|---|---|---|
| calm | BEAR | reject: too few data | — | — | +0.908 | no |
| rising | BEAR | reject: too few data | — | — | +0.813 | no |
| loaded | BEAR | reject: too few data | — | — | +0.852 | no |
| crisis | BEAR | reject: too few data | — | — | +0.946 | no |

Beats NONE, PILOT-BONF, PILOT-SPLIT and ROLE-RANDOM: **no**. Non-inferior to NONE: yes.

## agent → person, pilot of 10 targets

Role table: `{"calm": "RESTORE", "rising": "RESTORE", "loaded": "RESTORE", "crisis": "RESTORE"}`. Target roles (half A): `{"RESTORE": "BEAR", "DRIVE": "LEOPARD"}`. ROLE deployed: `{"calm": "LION", "rising": "LION", "loaded": "LION", "crisis": "LION"}`.

| Arm | Mean / tick |
|---|---|
| ROLE | -0.0902 |
| PILOT-BONF | -0.0902 |
| PILOT-SPLIT | -0.0902 |
| NAME-GATED | -0.0902 |
| NONE | -0.0902 |
| ORACLE | +0.2366 |
| ROLE-RANDOM | -0.0902 |
| ROLE-SHUFFLED | -0.0902 |

| Contrast | Estimate [95% interval] |
|---|---|
| ROLE-NONE | +0.000 [+0.000, +0.000] |
| ROLE-PILOT-BONF | +0.000 [+0.000, +0.000] |
| ROLE-PILOT-SPLIT | +0.000 [+0.000, +0.000] |
| ROLE-ROLE-RANDOM | +0.000 [-0.000, +0.000] |
| ROLE-ROLE-SHUFFLED | -0.000 [-0.000, +0.000] |
| ROLE-NAME-GATED | +0.000 [+0.000, +0.000] |
| ROLE-ORACLE | -0.327 [-0.333, -0.319] |

| Context | Candidate | Decision | Pilot est. | Bound | Truth | False admit |
|---|---|---|---|---|---|---|
| calm | BEAR | reject: too few data | — | — | +0.908 | no |
| rising | BEAR | reject: too few data | — | — | +0.813 | no |
| loaded | BEAR | reject | +0.356 | -2.225 | +0.852 | no |
| crisis | BEAR | reject | +1.298 | -0.721 | +0.946 | no |

Beats NONE, PILOT-BONF, PILOT-SPLIT and ROLE-RANDOM: **no**. Non-inferior to NONE: yes.

## agent → person, pilot of 20 targets

Role table: `{"calm": "RESTORE", "rising": "RESTORE", "loaded": "RESTORE", "crisis": "RESTORE"}`. Target roles (half A): `{"RESTORE": "BEAR", "DRIVE": "LEOPARD"}`. ROLE deployed: `{"calm": "LION", "rising": "LION", "loaded": "LION", "crisis": "BEAR"}`.

| Arm | Mean / tick |
|---|---|
| ROLE | -0.1081 |
| PILOT-BONF | -0.0967 |
| PILOT-SPLIT | -0.1081 |
| NAME-GATED | -0.0902 |
| NONE | -0.0902 |
| ORACLE | +0.2366 |
| ROLE-RANDOM | -0.0929 |
| ROLE-SHUFFLED | -0.1081 |

| Contrast | Estimate [95% interval] |
|---|---|
| ROLE-NONE | -0.018 [-0.027, -0.009] |
| ROLE-PILOT-BONF | -0.011 [-0.018, -0.005] |
| ROLE-PILOT-SPLIT | +0.000 [+0.000, +0.000] |
| ROLE-ROLE-RANDOM | -0.015 [-0.023, -0.007] |
| ROLE-ROLE-SHUFFLED | +0.000 [-0.000, +0.000] |
| ROLE-NAME-GATED | -0.018 [-0.027, -0.009] |
| ROLE-ORACLE | -0.345 [-0.356, -0.333] |

| Context | Candidate | Decision | Pilot est. | Bound | Truth | False admit |
|---|---|---|---|---|---|---|
| calm | BEAR | reject | +0.663 | -0.772 | +0.908 | no |
| rising | BEAR | reject: too few data | — | — | +0.813 | no |
| loaded | BEAR | reject | +0.810 | -0.391 | +0.852 | no |
| crisis | BEAR | admit | +0.826 | +0.017 | +0.946 | no |

Beats NONE, PILOT-BONF, PILOT-SPLIT and ROLE-RANDOM: **no**. Non-inferior to NONE: no.

## person → agent, pilot of 5 targets

Role table: `{"calm": "RESTORE", "rising": "RESTORE", "loaded": "RESTORE", "crisis": "RESTORE"}`. Target roles (half A): `{"RESTORE": "LEOPARD", "DRIVE": "TIGER"}`. ROLE deployed: `{"calm": "LION", "rising": "LION", "loaded": "LION", "crisis": "LION"}`.

| Arm | Mean / tick |
|---|---|
| ROLE | -0.0798 |
| PILOT-BONF | -0.0798 |
| PILOT-SPLIT | -0.0798 |
| NAME-GATED | -0.0798 |
| NONE | -0.0798 |
| ORACLE | -0.0078 |
| ROLE-RANDOM | -0.0798 |
| ROLE-SHUFFLED | -0.0798 |

| Contrast | Estimate [95% interval] |
|---|---|
| ROLE-NONE | +0.000 [+0.000, +0.000] |
| ROLE-PILOT-BONF | +0.000 [+0.000, +0.000] |
| ROLE-PILOT-SPLIT | +0.000 [+0.000, +0.000] |
| ROLE-ROLE-RANDOM | +0.000 [-0.000, +0.000] |
| ROLE-ROLE-SHUFFLED | +0.000 [-0.000, +0.000] |
| ROLE-NAME-GATED | +0.000 [+0.000, +0.000] |
| ROLE-ORACLE | -0.072 [-0.081, -0.062] |

| Context | Candidate | Decision | Pilot est. | Bound | Truth | False admit |
|---|---|---|---|---|---|---|
| calm | LEOPARD | reject | +0.401 | -0.110 | +0.872 | no |
| rising | LEOPARD | reject: too few data | — | — | +1.462 | no |
| loaded | LEOPARD | reject: too few data | — | — | +1.589 | no |
| crisis | LEOPARD | reject: too few data | — | — | +1.791 | no |

Beats NONE, PILOT-BONF, PILOT-SPLIT and ROLE-RANDOM: **no**. Non-inferior to NONE: yes.

## person → agent, pilot of 10 targets

Role table: `{"calm": "RESTORE", "rising": "RESTORE", "loaded": "RESTORE", "crisis": "RESTORE"}`. Target roles (half A): `{"RESTORE": "LEOPARD", "DRIVE": "TIGER"}`. ROLE deployed: `{"calm": "LION", "rising": "LION", "loaded": "LION", "crisis": "LION"}`.

| Arm | Mean / tick |
|---|---|
| ROLE | -0.0798 |
| PILOT-BONF | +0.0066 |
| PILOT-SPLIT | -0.0798 |
| NAME-GATED | -0.0798 |
| NONE | -0.0798 |
| ORACLE | -0.0078 |
| ROLE-RANDOM | -0.0798 |
| ROLE-SHUFFLED | -0.0798 |

| Contrast | Estimate [95% interval] |
|---|---|
| ROLE-NONE | +0.000 [+0.000, +0.000] |
| ROLE-PILOT-BONF | -0.086 [-0.097, -0.076] |
| ROLE-PILOT-SPLIT | +0.000 [+0.000, +0.000] |
| ROLE-ROLE-RANDOM | +0.000 [-0.000, +0.000] |
| ROLE-ROLE-SHUFFLED | +0.000 [-0.000, +0.000] |
| ROLE-NAME-GATED | +0.000 [+0.000, +0.000] |
| ROLE-ORACLE | -0.072 [-0.081, -0.062] |

| Context | Candidate | Decision | Pilot est. | Bound | Truth | False admit |
|---|---|---|---|---|---|---|
| calm | LEOPARD | reject | +0.653 | -0.003 | +0.872 | no |
| rising | LEOPARD | reject: too few data | — | — | +1.462 | no |
| loaded | LEOPARD | reject: too few data | — | — | +1.589 | no |
| crisis | LEOPARD | reject: too few data | — | — | +1.791 | no |

Beats NONE, PILOT-BONF, PILOT-SPLIT and ROLE-RANDOM: **no**. Non-inferior to NONE: yes.

## person → agent, pilot of 20 targets

Role table: `{"calm": "RESTORE", "rising": "RESTORE", "loaded": "RESTORE", "crisis": "RESTORE"}`. Target roles (half A): `{"RESTORE": "LEOPARD", "DRIVE": "TIGER"}`. ROLE deployed: `{"calm": "LEOPARD", "rising": "LION", "loaded": "LION", "crisis": "LION"}`.

| Arm | Mean / tick |
|---|---|
| ROLE | +0.0066 |
| PILOT-BONF | -0.0078 |
| PILOT-SPLIT | +0.0066 |
| NAME-GATED | -0.0798 |
| NONE | -0.0798 |
| ORACLE | -0.0078 |
| ROLE-RANDOM | -0.0452 |
| ROLE-SHUFFLED | +0.0066 |

| Contrast | Estimate [95% interval] |
|---|---|
| ROLE-NONE | +0.086 [+0.076, +0.097] |
| ROLE-PILOT-BONF | +0.014 [+0.010, +0.019] |
| ROLE-PILOT-SPLIT | +0.000 [+0.000, +0.000] |
| ROLE-ROLE-RANDOM | +0.052 [+0.046, +0.058] |
| ROLE-ROLE-SHUFFLED | +0.000 [-0.000, +0.000] |
| ROLE-NAME-GATED | +0.086 [+0.076, +0.097] |
| ROLE-ORACLE | +0.014 [+0.010, +0.019] |

| Context | Candidate | Decision | Pilot est. | Bound | Truth | False admit |
|---|---|---|---|---|---|---|
| calm | LEOPARD | admit | +0.506 | +0.126 | +0.872 | no |
| rising | LEOPARD | reject: too few data | — | — | +1.462 | no |
| loaded | LEOPARD | reject: too few data | — | — | +1.589 | no |
| crisis | LEOPARD | reject: too few data | — | — | +1.791 | no |

Beats NONE, PILOT-BONF, PILOT-SPLIT and ROLE-RANDOM: **no**. Non-inferior to NONE: yes.

## agent_v2 → person, pilot of 5 targets

Role table: `{"calm": "RESTORE", "rising": "RESTORE", "loaded": "DRIVE", "crisis": "BASELINE"}`. Target roles (half A): `{"RESTORE": "BEAR", "DRIVE": "LEOPARD"}`. ROLE deployed: `{"calm": "LION", "rising": "LION", "loaded": "LION", "crisis": "LION"}`.

| Arm | Mean / tick |
|---|---|
| ROLE | -0.0902 |
| PILOT-BONF | -0.0902 |
| PILOT-SPLIT | -0.0902 |
| NAME-GATED | -0.0902 |
| NONE | -0.0902 |
| ORACLE | +0.2366 |
| ROLE-RANDOM | -0.0902 |
| ROLE-SHUFFLED | -0.0902 |

| Contrast | Estimate [95% interval] |
|---|---|
| ROLE-NONE | +0.000 [+0.000, +0.000] |
| ROLE-PILOT-BONF | +0.000 [+0.000, +0.000] |
| ROLE-PILOT-SPLIT | +0.000 [+0.000, +0.000] |
| ROLE-ROLE-RANDOM | +0.000 [-0.000, +0.000] |
| ROLE-ROLE-SHUFFLED | -0.000 [-0.000, +0.000] |
| ROLE-NAME-GATED | +0.000 [+0.000, +0.000] |
| ROLE-ORACLE | -0.327 [-0.333, -0.319] |

| Context | Candidate | Decision | Pilot est. | Bound | Truth | False admit |
|---|---|---|---|---|---|---|
| calm | BEAR | reject: too few data | — | — | +0.908 | no |
| rising | BEAR | reject: too few data | — | — | +0.813 | no |
| loaded | LEOPARD | reject: too few data | — | — | -0.213 | no |
| crisis | LION | admit (already baseline) | +0.000 | — | +0.000 | no |

Beats NONE, PILOT-BONF, PILOT-SPLIT and ROLE-RANDOM: **no**. Non-inferior to NONE: yes.

## agent_v2 → person, pilot of 10 targets

Role table: `{"calm": "RESTORE", "rising": "RESTORE", "loaded": "DRIVE", "crisis": "BASELINE"}`. Target roles (half A): `{"RESTORE": "BEAR", "DRIVE": "LEOPARD"}`. ROLE deployed: `{"calm": "LION", "rising": "LION", "loaded": "LION", "crisis": "LION"}`.

| Arm | Mean / tick |
|---|---|
| ROLE | -0.0902 |
| PILOT-BONF | -0.0902 |
| PILOT-SPLIT | -0.0902 |
| NAME-GATED | -0.0902 |
| NONE | -0.0902 |
| ORACLE | +0.2366 |
| ROLE-RANDOM | -0.0902 |
| ROLE-SHUFFLED | -0.0902 |

| Contrast | Estimate [95% interval] |
|---|---|
| ROLE-NONE | +0.000 [+0.000, +0.000] |
| ROLE-PILOT-BONF | +0.000 [+0.000, +0.000] |
| ROLE-PILOT-SPLIT | +0.000 [+0.000, +0.000] |
| ROLE-ROLE-RANDOM | +0.000 [-0.000, +0.000] |
| ROLE-ROLE-SHUFFLED | -0.000 [-0.000, +0.000] |
| ROLE-NAME-GATED | +0.000 [+0.000, +0.000] |
| ROLE-ORACLE | -0.327 [-0.333, -0.319] |

| Context | Candidate | Decision | Pilot est. | Bound | Truth | False admit |
|---|---|---|---|---|---|---|
| calm | BEAR | reject: too few data | — | — | +0.908 | no |
| rising | BEAR | reject: too few data | — | — | +0.813 | no |
| loaded | LEOPARD | reject | -0.284 | -2.454 | -0.213 | no |
| crisis | LION | admit (already baseline) | +0.000 | — | +0.000 | no |

Beats NONE, PILOT-BONF, PILOT-SPLIT and ROLE-RANDOM: **no**. Non-inferior to NONE: yes.

## agent_v2 → person, pilot of 20 targets

Role table: `{"calm": "RESTORE", "rising": "RESTORE", "loaded": "DRIVE", "crisis": "BASELINE"}`. Target roles (half A): `{"RESTORE": "BEAR", "DRIVE": "LEOPARD"}`. ROLE deployed: `{"calm": "LION", "rising": "LION", "loaded": "LION", "crisis": "LION"}`.

| Arm | Mean / tick |
|---|---|
| ROLE | -0.0902 |
| PILOT-BONF | -0.0967 |
| PILOT-SPLIT | -0.1081 |
| NAME-GATED | -0.0902 |
| NONE | -0.0902 |
| ORACLE | +0.2366 |
| ROLE-RANDOM | -0.0929 |
| ROLE-SHUFFLED | -0.0996 |

| Contrast | Estimate [95% interval] |
|---|---|
| ROLE-NONE | +0.000 [+0.000, +0.000] |
| ROLE-PILOT-BONF | +0.006 [-0.003, +0.015] |
| ROLE-PILOT-SPLIT | +0.018 [+0.009, +0.027] |
| ROLE-ROLE-RANDOM | +0.003 [+0.001, +0.004] |
| ROLE-ROLE-SHUFFLED | +0.009 [+0.005, +0.014] |
| ROLE-NAME-GATED | +0.000 [+0.000, +0.000] |
| ROLE-ORACLE | -0.327 [-0.333, -0.319] |

| Context | Candidate | Decision | Pilot est. | Bound | Truth | False admit |
|---|---|---|---|---|---|---|
| calm | BEAR | reject | +0.663 | -0.772 | +0.908 | no |
| rising | BEAR | reject: too few data | — | — | +0.813 | no |
| loaded | LEOPARD | reject | -0.013 | -0.970 | -0.213 | no |
| crisis | LION | admit (already baseline) | +0.000 | — | +0.000 | no |

Beats NONE, PILOT-BONF, PILOT-SPLIT and ROLE-RANDOM: **no**. Non-inferior to NONE: yes.

## person → agent_v2, pilot of 5 targets

Role table: `{"calm": "RESTORE", "rising": "RESTORE", "loaded": "RESTORE", "crisis": "RESTORE"}`. Target roles (half A): `{"RESTORE": "LEOPARD", "DRIVE": "TIGER"}`. ROLE deployed: `{"calm": "LION", "rising": "LION", "loaded": "LION", "crisis": "LION"}`.

| Arm | Mean / tick |
|---|---|
| ROLE | -0.0792 |
| PILOT-BONF | -0.0792 |
| PILOT-SPLIT | -0.0792 |
| NAME-GATED | -0.0792 |
| NONE | -0.0792 |
| ORACLE | +0.0004 |
| ROLE-RANDOM | -0.0792 |
| ROLE-SHUFFLED | -0.0792 |

| Contrast | Estimate [95% interval] |
|---|---|
| ROLE-NONE | +0.000 [+0.000, +0.000] |
| ROLE-PILOT-BONF | +0.000 [+0.000, +0.000] |
| ROLE-PILOT-SPLIT | +0.000 [+0.000, +0.000] |
| ROLE-ROLE-RANDOM | -0.000 [-0.000, +0.000] |
| ROLE-ROLE-SHUFFLED | +0.000 [-0.000, +0.000] |
| ROLE-NAME-GATED | +0.000 [+0.000, +0.000] |
| ROLE-ORACLE | -0.080 [-0.085, -0.075] |

| Context | Candidate | Decision | Pilot est. | Bound | Truth | False admit |
|---|---|---|---|---|---|---|
| calm | LEOPARD | reject: too few data | — | — | +0.562 | no |
| rising | LEOPARD | reject: too few data | — | — | +0.870 | no |
| loaded | LEOPARD | reject: too few data | — | — | +0.023 | no |
| crisis | LEOPARD | reject: too few data | — | — | +0.109 | no |

Beats NONE, PILOT-BONF, PILOT-SPLIT and ROLE-RANDOM: **no**. Non-inferior to NONE: yes.

## person → agent_v2, pilot of 10 targets

Role table: `{"calm": "RESTORE", "rising": "RESTORE", "loaded": "RESTORE", "crisis": "RESTORE"}`. Target roles (half A): `{"RESTORE": "LEOPARD", "DRIVE": "TIGER"}`. ROLE deployed: `{"calm": "LION", "rising": "LION", "loaded": "LION", "crisis": "LION"}`.

| Arm | Mean / tick |
|---|---|
| ROLE | -0.0792 |
| PILOT-BONF | -0.0792 |
| PILOT-SPLIT | -0.0792 |
| NAME-GATED | -0.0792 |
| NONE | -0.0792 |
| ORACLE | +0.0004 |
| ROLE-RANDOM | -0.0792 |
| ROLE-SHUFFLED | -0.0792 |

| Contrast | Estimate [95% interval] |
|---|---|
| ROLE-NONE | +0.000 [+0.000, +0.000] |
| ROLE-PILOT-BONF | +0.000 [+0.000, +0.000] |
| ROLE-PILOT-SPLIT | +0.000 [+0.000, +0.000] |
| ROLE-ROLE-RANDOM | -0.000 [-0.000, +0.000] |
| ROLE-ROLE-SHUFFLED | +0.000 [-0.000, +0.000] |
| ROLE-NAME-GATED | +0.000 [+0.000, +0.000] |
| ROLE-ORACLE | -0.080 [-0.085, -0.075] |

| Context | Candidate | Decision | Pilot est. | Bound | Truth | False admit |
|---|---|---|---|---|---|---|
| calm | LEOPARD | reject | +0.379 | -0.792 | +0.562 | no |
| rising | LEOPARD | reject: too few data | — | — | +0.870 | no |
| loaded | LEOPARD | reject | +0.776 | -0.976 | +0.023 | no |
| crisis | LEOPARD | reject: too few data | — | — | +0.109 | no |

Beats NONE, PILOT-BONF, PILOT-SPLIT and ROLE-RANDOM: **no**. Non-inferior to NONE: yes.

## person → agent_v2, pilot of 20 targets

Role table: `{"calm": "RESTORE", "rising": "RESTORE", "loaded": "RESTORE", "crisis": "RESTORE"}`. Target roles (half A): `{"RESTORE": "LEOPARD", "DRIVE": "TIGER"}`. ROLE deployed: `{"calm": "LION", "rising": "LION", "loaded": "LION", "crisis": "LION"}`.

| Arm | Mean / tick |
|---|---|
| ROLE | -0.0792 |
| PILOT-BONF | -0.0792 |
| PILOT-SPLIT | -0.0792 |
| NAME-GATED | -0.0792 |
| NONE | -0.0792 |
| ORACLE | +0.0004 |
| ROLE-RANDOM | -0.0792 |
| ROLE-SHUFFLED | -0.0792 |

| Contrast | Estimate [95% interval] |
|---|---|
| ROLE-NONE | +0.000 [+0.000, +0.000] |
| ROLE-PILOT-BONF | +0.000 [+0.000, +0.000] |
| ROLE-PILOT-SPLIT | +0.000 [+0.000, +0.000] |
| ROLE-ROLE-RANDOM | -0.000 [-0.000, +0.000] |
| ROLE-ROLE-SHUFFLED | +0.000 [-0.000, +0.000] |
| ROLE-NAME-GATED | +0.000 [+0.000, +0.000] |
| ROLE-ORACLE | -0.080 [-0.085, -0.075] |

| Context | Candidate | Decision | Pilot est. | Bound | Truth | False admit |
|---|---|---|---|---|---|---|
| calm | LEOPARD | reject | +0.556 | -0.197 | +0.562 | no |
| rising | LEOPARD | reject: too few data | — | — | +0.870 | no |
| loaded | LEOPARD | reject | +0.077 | -0.688 | +0.023 | no |
| crisis | LEOPARD | reject: too few data | — | — | +0.109 | no |

Beats NONE, PILOT-BONF, PILOT-SPLIT and ROLE-RANDOM: **no**. Non-inferior to NONE: yes.

**Registered criterion (pilot 10): FAIL. Strong (pilot 5): FAIL.** False admits in ROLE: 0 of 2 admitted.

## What these results show

**W3b fails as registered**, in every direction and at every pilot size. Three things are visible in the tables and in
exploratory diagnostics run afterwards ([`w3b_diagnostics_exploratory.json`](w3b_diagnostics_exploratory.json)).

1. **The role layer transfers.** In all 12 runs the target pilot named the same restoring archetype that the source role
   pointed to: Bear on the person, Leopard on agents. Reading roles from a small pilot works.
2. **The gate starved.** A uniform pilot spreads its ticks over six archetypes and four contexts, so the tested cells held 1 to
   15 ticks and most contexts were rejected for too few data. 2 of 48 tests admitted a change; both were right
   (0 false admits).
3. **Per-tick effects are not policy value.** The truth cohort measures one tick of an archetype inside a randomised session.
   Deployed as a policy, the picture changes:
   - On the person, Bear only when in crisis *lowered* the score (−0.108 against −0.090 for no change) although its per-tick
     effect is +0.95. The context flips almost every tick (the trend term is noisy), so the policy switched about 10 times
     per person and set off the Watchdog's chaotic-switching interlock 3 times per person. Bear in every context, with one
     switch, reaches +0.237, close to the oracle.
   - On agents v1, Leopard everywhere (−0.008) is close to the oracle against −0.080 for no change.
   - On agents v2, Leopard everywhere is *worse* than no change (−0.138 against −0.079): repairing while traffic pressure
     keeps rising fails. There the right structure is shed load first, then repair, which is not one role held constantly.

**What to change, as a new registered test (W3c), not as a re-analysis of this one:**
- transfer a whole policy (which role, held or sequenced), not a per-context table;
- test the policy as it will be deployed, with a pilot that randomises *policies* between targets or blocks rather than
  archetypes between ticks, so all of the pilot's data serve the one hypothesis transfer proposes;
- smooth the context (trend over a window) so per-context policies do not flicker, and keep the Watchdog interlock as it is:
  it caught a real problem.

The W3b failure stays on record alongside W3 and G2.
