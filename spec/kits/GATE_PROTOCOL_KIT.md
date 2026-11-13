# GATE protocol kit: does earned automatic firing help?

A ready protocol for testing the autonomy gate with real people. Module specification: [GATE.md](../GATE.md).

## 1. Questions

1. When an anchor has earned automatic use, do automatic firings during detected stress lower stress more than suggested firings the person confirms (TRIAL design `auto_vs_manual`)?
2. Does the gate lower the number of firings that cannot help, compared with firing from day one?
3. How many uses outside training does a real anchor tolerate before its strength falls (wear-out, claims C13 and C63)?

## 2. Design

- **Run-in (2 to 4 weeks)**: PEAK pairing and probes until each participant's anchor reaches suggest.
- **Randomisation**: participants are randomised to the gate or to automatic firing from the start of the main phase (between-person), or, once the anchor is automatic, each detected episode is randomised to automatic or suggested firing (within-person, TRIAL `auto_vs_manual`).
- **Wear-out arm**: a pre-registered number of unpaired uses per week (for example 5, 15 or 30), with probe trials each week to track strength.
- **Duration**: 8 weeks of main phase.
- **Sample size**: plan from a pilot; the simulation's numbers are illustrations, not effect sizes.

## 3. Measures

| Measure | When |
|---|---|
| Stress before and 10 minutes after each firing (0-10), and heart rate or RMSSD where available | Each firing |
| Offer outcome: helped, not needed, didn't help | Each offer |
| Anchor strength (PEAK probes against sham) | Weekly |
| Stage over time, demotions and their reasons | Continuously (audit log) |
| Felt control: "The device acts when I would want it to" (1-7) | Weekly |
| Adverse events, including firings felt as intrusive | Any time |

## 4. Consent wording (adapt to your ethics board)

> The device may suggest your anchor when it detects stress. Later, if your anchor has proven itself, the device may play it by itself, but only if you agree; you can withdraw that agreement at any moment on the Safety page, and the device stops at once. Every automatic decision is logged and you can see the log. Some actions work without you noticing at the moment (for example playing during sleep); each is labelled. The methods are experimental and are not a treatment.

## 5. Data format

The Safety page stores and exports offers (`{"anchor", "ts", "outcome", "stage", "stress"}`), consent records (`{"scope", "by", "given", "withdrawn"}`) and the audit log (`{"ts", "actor", "action", "anchor", "decision", "reasons", "flag"}`). Dates become day numbers before sharing; the research contribution format (spec/DATA_CONTRIBUTION.md) can carry these files.

## 6. Analysis

- Question 1: TRIAL analysis of `auto_vs_manual` per participant, pooled with random effects.
- Question 2: firings that did not help, per participant per week, compared between arms (negative binomial or permutation test).
- Question 3: strength against cumulative unpaired uses, a mixed model with participant as a random effect; the use count where strength's interval first includes zero.

## 7. Report template

1. Participants, run-in, how many reached each stage and when.
2. Randomisation and arms.
3. Stress change by firing type, per participant and pooled.
4. Unhelpful firings by arm.
5. Strength over unpaired uses (the wear-out curve) and the tolerated dose.
6. Demotions: how often the gate closed, why, and whether the reasons were right.
7. Felt control, consent withdrawals and adverse events.
8. What this means for the thresholds in GATE.md and for claims C13, C40 and C63.
