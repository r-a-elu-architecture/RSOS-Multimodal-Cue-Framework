# CTX_PREF — is the preferred reply style context-dependent in real arena votes? (results)

Design: [`spec/CTX_PREF.md`](../../spec/CTX_PREF.md), registered before the code and before the data was opened. Data:
`lmarena-ai/arena-human-preference-140k` (CC BY 4.0), revision `6322995ab34d7c2693e3f47dd13fa5caa0789a74`, 135,634 rows. Run on a GitHub runner (job 44061366439,
code 6869870). Only the aggregates below left the runner.

**Verdict: INCONCLUSIVE.** Only 128 of 35,858 included prompts were PERSONAL, so S had one usable
context (OTHER) and Q two (CODE, OTHER). No cell's interval lies above or below 0.5.

## Inclusion
| Step | Votes |
|---|---|
| All rows | 135,634 |
| Winner is model_a or model_b | 98,348 |
| English | 51,664 |
| First vote of a session | 42,053 |
| Single exchange, same prompt | 35,896 |
| Both replies non-empty | 35,858 |

Contexts: PERSONAL 128, CODE 11,045, OTHER 24,685.

## Length-matched cells (the registered measure; Wilson 99.83%; usable from n = 50)
| Feature in context | Wins / votes | Win rate | Interval |
|---|---|---|---|
| S in PERSONAL | 1 / 2 | 0.500 | [0.044, 0.956] |
| S in CODE | 5 / 11 | 0.455 | [0.133, 0.819] |
| S in OTHER | 41 / 76 | 0.539 | [0.366, 0.704] |
| Q in PERSONAL | 1 / 7 | 0.143 | [0.012, 0.692] |
| Q in CODE | 175 / 339 | 0.516 | [0.432, 0.600] |
| Q in OTHER | 456 / 836 | 0.545 | [0.491, 0.599] |

## Without length matching (information only)
| Feature in context | Wins / votes | Win rate |
|---|---|---|
| S in PERSONAL | 15 / 26 | 0.577 | [0.296, 0.816] |
| S in CODE | 41 / 89 | 0.461 | [0.307, 0.622] |
| S in OTHER | 230 / 458 | 0.502 | [0.429, 0.575] |
| Q in PERSONAL | 23 / 49 | 0.469 | [0.270, 0.679] |
| Q in CODE | 907 / 2233 | 0.406 | [0.374, 0.439] |
| Q in OTHER | 2200 / 5043 | 0.436 | [0.414, 0.458] |

S in PERSONAL minus S in CODE (information only): +0.045, 99% interval
[-0.94, +1.03].

## Reading
- The arena is not where people bring personal difficulty: 0.4% of prompts match the pattern. The question cannot be
  answered here, for lack of data in the context that matters most.
- Length-matched, neither style wins or loses clearly anywhere. Information only: without length matching, replies that
  end by asking back win 41–44% in CODE and OTHER. Because the length-matched rates are near 0.5, that gap probably comes
  from length (asking-back replies tend to be shorter), not from the question itself. This was not a registered test.
- S (stabilising acknowledgment) is rare in replies to everyday prompts (76 length-matched discordant votes in OTHER) and
  neither wins nor loses there.
