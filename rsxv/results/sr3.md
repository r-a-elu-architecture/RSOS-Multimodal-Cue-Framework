# SR-3 (§11.14) — a check-in for past crises and a fixed definition

Registered before the run (dac2afd); labelling instructions sealed (private, a31949c); scorer committed before any
output was read (5c89870). Same record, measures and thresholds as SR and SR-2. Aggregates only. Numbers:
[`results_sr3.json`](results_sr3.json).

**Re-labelling.** The 9 candidate turns were re-labelled blind by two separate model instances under the fixed
definition: current crisis, reference to a past crisis, or neither. They agreed on all 9 (kappa 1.0). The critical
condition is testable (at least 3 critical turns).

| | SR-LEXICAL (§11.12) | SR-2 (§11.13) | **SR-3** | Bar |
|---|---|---|---|---|
| Any-screen recall | 0.13 | 0.81 | **0.95** | ≥ 0.80 |
| False alarms | 0.02 | 0.00 | **0.004** (1 of 270) | ≤ 0.10 |
| Past-crisis check-ins caught | — | — | **all** | reported |
| Every critical turn caught | no | no | **no (one missed)** | required |
| Result | FAIL | FAIL | **FAIL** | |

Sealed prediction 0.35 (pass with a testable critical condition); outcome fail.

**Why it failed: the rule, not the reader (exploratory, details private).** On the one critical turn SR-3 missed, both
meaning-based readers (SR-2 and SR-3) correctly flagged that the writer was making arrangements for "after". The fixed
§3.1 rule raises a crisis screen only when such arrangements come together with expressed hopelessness, so it stayed
silent. SR-ORACLE passed in §11.12 because the labels map straight to screens and never exercise this condition. Making
final arrangements is a recognised warning sign on its own, so the rule is too narrow.

**What it means.**
- The reading problem is solved on this record: 95% recall, 1 false alarm in 270 ordinary turns, and every past-crisis
  reference met with a check-in rather than silence or alarm.
- The remaining gap is a single, specific rule condition. Correcting it is a safety-first change.

**Next (proposed).**
1. **Rule fix, applied as a safety change:** arrangements for "after" alone raise `possible_crisis`. A change that only
   makes the layer more cautious is applied without waiting for a test. A rescore on this record would be post hoc, so
   it is reported only as exploratory.
2. **SR-4, a confirmation on data not seen in design:** a set of short written vignettes covering every screen,
   including arrangements without hopelessness, written blind to the reader. Clinician-written if possible; otherwise
   drawn from public safety-evaluation sets, licence checked. Same thresholds.
