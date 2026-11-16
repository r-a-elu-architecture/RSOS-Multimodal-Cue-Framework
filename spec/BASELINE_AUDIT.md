# BASELINE_AUDIT — do the passed RSX-V results beat a simple baseline?

Status: registered 2026-11-16, before any audit code or run. Results go in §6, in a separate record commit.
Thresholds, seeds and baselines below are fixed here and are not changed after the run.

## 0. Why

Review P2 found that a source-free rule (the target's stabilising archetype everywhere) reaches the W5-CEILING value
(spec/FIXES_P2.md C1). W1 already records that an equal-information greedy baseline also fixes 100%. In two of two close
looks, a simple baseline matched the method. This audit asks the same question of every row the register shows as
**Pass**: does the method beat the simplest baseline that uses no more information?

All environments are stated models. Nothing here is data about people.

## 1. The seven rows and their baselines

| ID | Register row | Baseline | New run? |
|---|---|---|---|
| A1 | W1 repair | GREEDY, the equal-information greedy repair already in W1's registered run | No: recorded `beats_equal_information: false` in `results/results_world.json` |
| A2 | W4 safety | None applies (see §3) | No |
| A3 | H-CFIT / H-SWITCH | FIXED-BEST (§2.1), legacy score | Yes |
| A4 | H-CFIT under the mission score | FIXED-BEST (§2.1), mission score | Yes |
| A5 | G1, the gate on the W3 tables | NONE, transfer nothing (already an arm of G1) | No: the gated tables in `results/floor3.md` |
| A6 | J1, jam predictor | NEVER-JAM, the majority class (§2.2) | Yes (reproduction) |
| A7 | T-AP, transfer agents v1 → person | STAB-ONLY (§2.3) | Yes |

## 2. New baselines

### 2.1 FIXED-BEST (A3, A4)
- One archetype for the whole session, chosen by a pilot.
- The pilot runs each person mode as a fixed policy for 120 ticks on 20 pilot persons: seeds 1200–1219 for A3 (legacy
  score) and 5200–5219 for A4 (mission score). These seeds are unused by the tests.
- The mode with the highest pilot mean is deployed on the test's own persons: 1000–1199 for A3, 5000–5199 for A4.
- Disclosed: the pilot gives FIXED-BEST information from 20 other persons, which the watchdog arm does not have. It does
  not see the test persons.
- Contrast: WATCHDOG − FIXED-BEST, paired, the test's own interval (95% paired bootstrap, `world_experiments.paired_ci`).
- Information only, no verdict: each fixed mode on the test persons.
- Reproduction check: the re-run WATCHDOG means must equal the recorded ones (A3 +0.042649, A4 +0.044732, to 6 decimals).
  If they do not, the audit row is reported as "not reproduced" and no label changes.

### 2.2 NEVER-JAM (A6)
- J1's own procedure, seeds and rows are re-run unchanged. Reproduction check: n = 260 and accuracy 0.754 (to 3 decimals).
- Baseline: predict "no jam" always (the majority class, 0.685 in the record).
- Test: exact one-sided McNemar (binomial) test on the pairs where J1 and NEVER-JAM disagree. Significance level 0.01.
- Information only: the mean-only rule (J1 without its spike clause).

### 2.3 STAB-ONLY (A7)
- Per repetition, on T-AP's own pilot persons, the target's roles are read exactly as T-AP reads them (`read_target_roles`,
  8 persons × 10 ticks). The table is the STABILISE archetype in every context, or LION everywhere if no STABILISE role
  is read. No source, no certificates, no pilot ticks beyond the role reading.
- STAB-ONLY therefore uses **less** target information than T-AP, and no source information.
- Deployed on T-AP's deployment persons, averaged over T-AP's 20 repetitions, in both T-AP runs: the primary (person model,
  T-AP seeds) and the confirmation (seeds + 100000, person model v2).
- Contrast: T-AP − STAB-ONLY at T-AP's own level (two-sided 99.375%, `w5c_experiments.ci` with T-AP's settings).
- Reproduction check: re-run T-AP means +0.1113 (primary) and +0.0872 (confirmation), to 4 decimals.
- **Disclosed before the run:** review P2 found that this rule reaches +0.240 per tick in W5's agent → person seeds, and
  T-AP's recorded ORACLE upper bound is +0.2439. The audit author therefore expects T-AP to lose. The rule is registered
  anyway, because the expectation is not a measurement.

## 3. A2, W4: no baseline applies
W4 checks that fixed rules block seven named kinds of forbidden proposal and pass legitimate ones. A rule that matches
those seven kinds is what is being tested, so no simpler baseline exists. The register row already says it is not a test
against an adaptive adversary. W4 keeps its label.

## 4. Outcomes and the rule

For each audited row:
- **HOLDS:** the method beats the baseline (lower bound of method − baseline above 0, or for A6, p < 0.01).
- **TIES:** the interval contains 0 (A6: p ≥ 0.01 with J1 not worse), or the method is identical to the baseline.
- **LOSES:** the upper bound is below 0 (A6: J1 is significantly worse).

A7 holds only if it holds in both the primary and the confirmation run.

Register effect:
- HOLDS: the row keeps **Pass**; the meaning gains "holds against <baseline> (BASELINE_AUDIT)".
- TIES or LOSES: the result becomes "Pass by its registered test; **fails the baseline audit** (<outcome> against
  <baseline>)". The register then shows it as mixed. The original registered verdict is not rewritten.
- Not reproduced: no change; the row's meaning notes it.

## 5. Acceptance
- Q1 `rsxv/rsxv/baseline_audit.py` writes `results/results_baseline_audit.json` and `results/baseline_audit.md`.
- Q2 `rsxv/tests/test_baseline_audit.py`: the outcome rule (§4) on fixed inputs; STAB-ONLY's table construction; FIXED-BEST's
  choice by pilot mean; the McNemar p-value on a known case.
- Q3 The register, the results page and the Agents page are regenerated from the corrected `RESULTS.md`.
- Q4 All suites, `scripts/check_all.sh` and the browser checks pass.

## 6. Results
(recorded after the run, in a separate commit)
