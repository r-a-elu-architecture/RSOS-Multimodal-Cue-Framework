# SR-2 (§11.13) — a meaning-based reader for the safety layer

Registered before the run (9be7dd7); scorer committed before any reader output was read (c12c03d). Same record, truth
labels and measures as SR in §11.12. Aggregates only. Numbers: [`results_sr2.json`](results_sr2.json).

| System | Any-screen recall (bar ≥ 0.80) | Critical recall (bar = all) | False alarms (bar ≤ 0.10) | Result |
|---|---|---|---|---|
| SR-2 (meaning-based reader) | **0.81** | below the bar | **0.00** | **FAIL** |
| SR-LEXICAL (keyword reader, §11.12) | 0.13 | below the bar | 0.02 | FAIL |

SR-2 against SR-LEXICAL on the same turns: 13 moments caught only by SR-2, 2 only by the keyword reader (McNemar exact
p = 0.007). Sealed prediction 0.45; outcome fail.

**What went wrong (exploratory, details private).** The critical turns SR-2 missed share one kind of wording that the
registration did not settle, and the truth labels were not consistent on it either. So part of the failure is a
definition gap, not reading quality.

**What it means.**
- The reading step can be made to work. A meaning-based reader brings recall from 13% to 81% with no false alarms on 273
  ordinary turns.
- The remaining gap is a definition and a mechanism, not reading quality. A conservative safety layer should answer
  moments of this kind, inside an active conversation, with a gentle check-in. That is a new, softer screen, not
  silence and not full crisis mode.

**Next test (proposed): SR-3.**
1. Add a `history_reference` flag to the reader and a `check_in` response to the rules: ask how the person is now, and
   offer contacts.
2. Fix the label definition (current signal → crisis screen; reference to past crisis → check-in) with clinician input
   where possible.
3. Re-label the past-reference turns blind under the new definition, then score on the same record. Thresholds unchanged.
