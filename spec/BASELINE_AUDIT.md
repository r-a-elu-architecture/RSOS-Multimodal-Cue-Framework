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

## 6. Results (recorded after the code commits ee01c84 and 59539cf; `rsxv/results/baseline_audit.md`)

The full run took 90 s. Every reproduction check passed: H-SWITCH watchdog +0.042649, H-CFIT-M +0.044732, J1 n = 260 and
accuracy 0.754, T-AP +0.1113 and +0.0872.

| Row | Baseline | Method | Baseline value | Method − baseline | Outcome |
|---|---|---|---|---|---|
| A1 W1 | GREEDY | 100% fixed | 100% fixed | 0 (recorded) | **TIES** |
| A2 W4 | none | — | — | — | not applicable; label kept |
| A3 H-SWITCH | FIXED-BEST, Bear | +0.0426 | +0.0538 | −0.0111 [−0.0123, −0.0100] | **LOSES** |
| A4 H-CFIT-M | FIXED-BEST, Bear | +0.0447 | +0.1294 | −0.0847 [−0.0954, −0.0741] | **LOSES** |
| A5 G1 | NONE | gated table all Lion, both directions | the same | identical | **TIES** |
| A6 J1 | NEVER-JAM | 0.754 | 0.685 | discordant 65 vs 47; p = 0.054 | **TIES** |
| A7 T-AP primary | STAB-ONLY (Bear everywhere) | +0.1113 | +0.2439 | −0.1325 [−0.1449, −0.1190] | **LOSES** |
| A7 T-AP confirmation | STAB-ONLY (Bear everywhere) | +0.0872 | +0.2271 | −0.1399 [−0.1470, −0.1335] | **LOSES** |

**Verdict:** none of the six audited rows beats its simplest baseline. W4 keeps its label. By §4, W1, H-SWITCH, H-CFIT-M,
G1, T-AP and J1 now read "passed its registered test; fails the baseline audit"; their original verdicts are kept.

**What this means.**
- In these stated models, one fixed rule (Bear, the stabilising archetype, in every context) beats every adaptive method
  tested: ledger switching, transfer and pilot-gated tables. The models reward stabilising so strongly that choosing well
  between archetypes adds nothing on top.
- T-AP's STAB-ONLY table was Bear everywhere in all 40 repetitions. The rule needs 8 targets × 10 ticks of role reading and
  no source, so the T-AP pass is not evidence that anything transferred between substrates.
- This questions the models more than the methods. A model in which one archetype is best everywhere cannot show the value
  of switching or of transfer. Any future switching or transfer test needs a model where the best archetype depends on
  context. It also needs FIXED-BEST and STAB-ONLY as registered comparators.
- Information only: J1's mean-only rule scores 0.746. Each fixed mode on the test persons is listed in the results file.

**Disclosed deviation:** before the full run, a smoke run (`--quick`) used subsets of the registered seeds, not unregistered
ones as AGENTS.md §11.5 asks. Its outcome labels matched the full run's. Nothing was changed between the smoke run and the
full run.

**Checks:** listed in HANDOFF.

## 7. Amendment, 17 November 2026: the Agents page (registered before the code)

- T1: the section heading becomes "Tested in simulation: the RSX-V agents". The tags stay "passed its registered test",
  which is still true.
- T2: under the lede, one line built from `rsxv/results/results_baseline_audit.json` (via `rsxv.site_agents`), never typed
  into the page. It gives how many audited rows hold against their baseline, each row's outcome, and links to the results
  file. No new numbers.
- T3: `scripts/check_site_catchup.py` checks the heading, and checks that the line's counts equal the counts in the data.

**§7 results (code a775ffa).** The heading reads "Tested in simulation: the RSX-V agents". The line renders as "Baseline
audit: 0 of 6 audited results beat their simplest baseline (W1 ties …; T-AP loses against STAB-ONLY). The audit." The
first draft said "the simplest baseline that uses no more information", which is not true of FIXED-BEST (it uses a
20-person pilot), so that phrase was removed before the commit. Checks: `rsso` 291 passed, 2 skipped, 1 xfailed; RSX-V 156
passed; `check_all.sh` passed; `check_site_catchup.py`, `check_profiles.py` and `check_outlet.py` exit 0.

## 8. Note, 17 November 2026 (spec/STAB_DEFAULT.md §1a and §5)
Person model v2 has a loophole: under always-Bear the first cue is never interrupted, and it blocks every later cue. A3, A4
and T-AP's primary run used person model v1, which has no cues, so they are not affected. T-AP's confirmation run used
person model v2; its STAB-ONLY value there (+0.227) may be inflated by the loophole. The verdict for T-AP stands on the
primary run alone (−0.133 [−0.145, −0.119]).
