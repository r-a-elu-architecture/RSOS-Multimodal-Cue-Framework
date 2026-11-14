# Phase 9 (§11.11): what the public-data replication showed

Registered before the data was opened; one amendment, made before any outcome was computed, made the MSE level reachable
(2000 redraws) without changing any threshold. Data: WildChat-1M shards 0–2 (ODC-BY), 22,369 included English conversations
with at least 3 user turns (17,486 GPT-3.5, 4,883 GPT-4). Details: [`p9.md`](p9.md). Aggregates only.

**Result: 5 of 7 registered tests pass** (R1, R3, MSE notes, MSE phrases, C2); MSE melody passes 2 of its 3 measures and so
fails as a scale; C5 fails. Brier 0.173.

| Test | Result |
|---|---|
| P9-R1 verbatim re-entry | **PASS**: 4.9% of user turns vs 0.001% |
| P9-R3 re-entered words carry forward | **PASS**: +0.22, 99% CI [0.20, 0.24] |
| MSE notes | **PASS**: re-entry 0.26 vs 0.016; carry-forward +0.38 |
| MSE phrases | **PASS**: re-entry 0.034 vs 0.0001; carry-forward +0.52 |
| MSE melody | **FAIL** (2 of 3): inheritance 0.80 vs 0.54 and re-entry pass; carry-forward −0.004 (as in the origin) |
| P9-C2 drift of reused blocks across a user's conversations | **PASS**: ρ = 0.28, p = 0.001, 553 families |
| P9-C5 reframing predicts refuse-then-comply | **FAIL**: AUC 0.49 |

**Reading.** The lineage structure first measured in one long private record (one generation's output becomes the next
generation's input and carries forward) holds in a large public sample with two models. It is weaker in size (verbatim
re-entry about a quarter as common). Melody re-entry is small and reverses for GPT-4, so it is not robust. This is the first
LSGPA result replicated outside the record. It is observational: it shows the structure exists and its size, not that
re-entry causes the carry-forward.
