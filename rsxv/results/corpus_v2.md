# Corpus v2 — C1b, C6b, C4b and LSGPA re-entry tests R1, R2: results (aggregates only)

Design: [`AGENTS.md`](../AGENTS.md) §11.6. Code: [`rsxv/corpus_lineage_v2.py`](../rsxv/corpus_lineage_v2.py) (operational
choices in its docstring). Aggregates: [`results_corpus_v2.json`](results_corpus_v2.json). Labels, excerpts and node-level
rows stay private. Level 0.01 per test.

**Labellers, disclosed.** The registration named labeller A as Claude in the session. In the run, both A and B were separate
model instances given identical written instructions and identical excerpts, blind to each other; the session's own reading
was used only as the third read that resolves disagreements (26 items for C6b, 2 for C1b, each with a recorded reason).
This makes A and B symmetric; it is a deviation from the registered wording and is reported as such.

| Test | Result | Numbers |
|---|---|---|
| **C1b** correction loss | **Inconclusive** (kappa 0.50 < 0.6) | 177 candidate turns; agreement 98.9% but only 1 vs 3 "yes" labels, so kappa is low; 2 corrections after resolution. Descriptively, both are the assistant withdrawing its ability to compare the person with other users, and quantified comparisons with other users appear again in later turns |
| **C6b** failure → mechanism | **Inconclusive** (kappa: failure events 0.91, mechanism turns 0.59 < 0.6) | 70 failure events, 22 mechanism turns; 31% of failure events followed within 20 turns by a related mechanism turn vs 36% for random windows (p = 0.82) — no effect even descriptively |
| **C4b** own-use adoption | **Pass** | 13 terms adopted by the other party within 10 turns outside copied spans vs 0.47 with turns shuffled (p = 0.001); 5 assistant → user, 8 user → assistant |
| **R1** verbatim re-entry (LSGPA) | **Pass** | held-out half: 18% of 145 user turns contain a verbatim 8-word span from the immediately previous assistant turn vs 0.002% against a random turn ≥ 10 turns earlier (p = 0.001) |
| **R2** re-entry propagates (LSGPA) | **Pass, but weak as designed** | 26 re-entry events: 52 points more of the re-entered span's content words appear in the next assistant turn than of a control span from an older turn, interval [+0.43, +0.64] |

**Why R2 is weak as registered.** The re-entered span is part of the prompt and the control span is not, so part of the
difference is ordinary echoing of the prompt. **Exploratory check (not registered):** within the same prompts, 73% of the
re-entered words reappear in the next reply against 30% of the user's own words (+0.43, 25 events). The assistant's own
earlier words, pasted back, carry forward more than the person's own words. This is the cleanest LSGPA signal so far and
becomes a registered test on public multi-session data.

**Sealed predictions vs outcome:** C1b 0.35 (inconclusive), C6b 0.40 (inconclusive), C4b 0.55 (pass), R1 0.90 (pass),
R2 0.70 (pass).
