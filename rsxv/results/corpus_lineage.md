# C1–C6 — corpus lineage tests: results (aggregates only)

Design: [`AGENTS.md`](../AGENTS.md) §11.5 (public definitions) and a private registration (scope, split, seed cases, word
lists). Code: [`rsxv/corpus_lineage.py`](../rsxv/corpus_lineage.py), committed before any outcome was computed. Aggregates:
[`results_corpus_lineage.json`](results_corpus_lineage.json). The corpus is private: one long human–LLM conversation (578
turns with text, 289 by the user), plus a 16-turn predecessor excerpt reported separately. Node-level rows stay in the
private repository. Level 0.05 / 6 for every test.

**Disclosure.** The corpus was read during design, so these are confirmations of frozen code, not blind discovery. First
labels come from frozen rules written by Claude (a code labeller); a 10% random sample (seed 4242) was re-labelled by hand
from the candidate turn and the turn before it, blind to the first label.

| Test | Result | Numbers (main record) | Reading |
|---|---|---|---|
| **C1** correction loss | **Not testable / inconclusive** | 3 corrections detected by the rules, 0 re-entries; the one sampled "correction" was a value range, not a correction (agreement 0/1) | The anchored-quantity rule is too narrow for this record |
| C1, predecessor (seed case, reported separately) | Reported, not pooled | 2 corrected claims, 1 re-entered without its correction; `LineageMemory` flagged it (recall 1/1, false flags 0) | Known before registration; shows the detector works, says nothing about rates |
| **C2** summary drift | **Not testable** | 0 capsule families with ≥ 3 generations | Needs multi-session data |
| **C3** format decay | **Fail** | 39 format instructions; slope +0.0022 per assistant turn, interval [−0.022, +0.014]; intercept 0.89 | No decay: requested structure was kept |
| **C4** term adoption | **Pass** | 2014 terms; 40 adopted by the other party within 10 turns vs 2.4 with turns shuffled (p = 0.001); 32 assistant → user, 8 user → assistant. Held-out half: 14 vs 1.5 (p = 0.001) | Passes as registered; see below for what it measures |
| **C5** refuse-then-comply | **Not testable** | 3 boundary events, all in the development half; each followed by a long answer within one turn | Too few boundary events |
| **C6** failure → mechanism | **Inconclusive (labeller invalid)** | 258 rule-detected failure turns; 70% followed by a mechanism turn vs 75% for random windows (p = 0.98). Hand check: 3 of 26 sampled candidates were concrete failure events | The rule fires on analytical vocabulary, not on failure events |

Cohen's kappa could not be computed for C1 and C6 because the code labeller gives every candidate the same label; percent
agreement is reported instead and treated like kappa (below 0.6 → inconclusive). C5: 1 sampled event, type agreed.

**What C4 actually measures (exploratory, not registered).** The adopted terms are mostly table headers and section names
the assistant introduced and the user then pasted back into prompts. 81 of 288 user turns (28%) contain at least one
verbatim 8-word span from the previous assistant turn; on average 7.4% of a user turn's 8-word spans are copied. The strong
signal is **re-entry of output as the next input** (an LSGPA mechanism) more than vocabulary adoption. It becomes a
registered test before it is used as evidence.

**Next (new registrations):** a meaning-reading labeller with a second labeller for C1 and C6; multi-session data for C2 and
C5; C4 split into verbatim re-entry and own use.
