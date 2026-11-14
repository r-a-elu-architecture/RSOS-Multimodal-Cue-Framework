# LIA-WW (§11.15) — root-cause attribution on real multi-agent failure logs (Who&When)

Registered before the data was read (ae04ef2); prep and scorer committed before any judge output (480e502). Data:
Who&When (Zhang et al., ICML 2025), 184 failure logs from 127 LLM multi-agent systems, with the responsible agent and
decisive step annotated. Annotations were never shown to a judge. Aggregates only. Numbers:
[`results_lia_ww.json`](results_lia_ww.json).

| Method (same model) | Agent accuracy | Step accuracy |
|---|---|---|
| LIA-UPSTREAM (first-failure lineage rule) | 69.6% | 41.8% |
| ALL-AT-ONCE (the benchmark's best agent-level method, reimplemented) | 67.4% | **45.1%** |
| Random | 34.3% | 9.4% |

**Result: FAIL.** The lineage rule did not beat judging the whole log at once on step accuracy: 10 tasks were found only
by LIA, 16 only by all-at-once (McNemar one-sided p = 0.92). On agent accuracy it was not worse: +2.2 points, 95% CI
[−4.3, +8.7]. Sealed prediction 0.35.

**By subset (exploratory).** Algorithm-generated systems (126): LIA 65% / 46%, all-at-once 67% / 52% (agent / step).
Hand-crafted systems (58; long logs from Magentic-One): LIA 79% / 33%, all-at-once 69% / 31%. The lineage rule helps on
the long hand-crafted logs and hurts on the shorter generated ones.

**Context: the model, not the method.** Both arms score far above the published GPT-4o numbers (best published step
accuracy 25.5% on algorithm-generated and 8.8% on hand-crafted logs; here 46–52% and 31–33%). That gain comes from the
model used, which is the same in both arms, so it is not a result of this architecture. Methods published since 2025 may
score higher still; no claim of a new state of the art is made.

**Other notes.** All 184 tasks were answered by both arms. Three annotated steps lie beyond the end of their logs and
count as misses for both. Steps were capped at 1,000 characters for both arms.

**What it means.** On real agent failures, the architecture's first-failure lineage rule, given to a model as
instructions, finds the responsible agent as well as judging the whole log at once. It does not locate the decisive step
better. The upstream walk may help most where logs are long, which is worth a registered test of its own.

**Next (proposed).** Register the upstream walk as a test on long logs only, with fresh data (Who&When Pro or a new
split), rather than re-testing on these logs.
