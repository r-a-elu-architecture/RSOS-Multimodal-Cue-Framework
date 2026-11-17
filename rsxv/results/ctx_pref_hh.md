# CTX_PREF_HH — the context question on hh-rlhf helpfulness pairs (results)

Design: [`spec/CTX_PREF_HH.md`](../../spec/CTX_PREF_HH.md), registered before the code and before the data was opened.
Data: `Anthropic/hh-rlhf` (card licence MIT), revision `09be8c5bbc57cb3887f3a9732ad6aa7ec602a1fa`; file SHA-256 hashes are in
`results_ctx_pref_hh.json`. Run on a GitHub runner (run 44064375403, code 8668c32). Only these aggregates left the runner.

**Verdict: INCONCLUSIVE.** 123,415 of 124,503 pairs qualified. PERSONAL held 505 prompts. Of those,
11 (S) and 22 (Q) were discordant and length-matched, below the 50 needed, so PERSONAL was not
usable for either feature (spec §6).

## Length-matched cells (registered; Wilson 99.875%)
| Feature in context | Chosen / pairs | Rate | Interval |
|---|---|---|---|
| S in PERSONAL | 9 / 11 | 0.818 | [0.353, 0.974] |
| S in OTHER | 198 / 452 | 0.438 | [0.365, 0.514] |
| Q in PERSONAL | 11 / 22 | 0.500 | [0.217, 0.783] |
| Q in OTHER | 1476 / 3575 | 0.413 | [0.387, 0.440] |

## Without length matching (information only)
| Feature in context | Chosen / pairs | Rate | Interval |
|---|---|---|---|
| S in PERSONAL | 17 / 28 | 0.607 | [0.322, 0.834] |
| S in OTHER | 733 / 1705 | 0.430 | [0.392, 0.469] |
| Q in PERSONAL | 52 / 134 | 0.388 | [0.265, 0.527] |
| Q in OTHER | 9529 / 25980 | 0.367 | [0.357, 0.376] |

S in PERSONAL minus S in OTHER (information only, length-matched, 99%): +0.380 [+0.075, +0.686],
on 11 PERSONAL pairs.

## Reading
- Registered: inconclusive. The personal context is again too rare, and the stabilising feature too rare inside it.
- In OTHER, length-matched, replies that end by asking back are chosen less often: 0.413, with the interval below 0.5.
  Stabilising acknowledgment there: 0.438, interval reaching 0.514, not clear.
- Information only, not a registered result: in PERSONAL the stabilising reply was chosen in 9 of 11 matched pairs,
  against 0.438 in OTHER. The difference interval excludes zero at 99%, but it rests on 11 pairs. It is a lead, not a
  finding.
