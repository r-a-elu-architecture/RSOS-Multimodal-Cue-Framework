# CTX_PREF_WC — reply style and the person's next reaction, by context, in WildChat-1M (results)

Design: [`spec/CTX_PREF_WC.md`](../../spec/CTX_PREF_WC.md), registered before the code and the run. Data:
`allenai/WildChat-1M` (ODC-BY; not gated), revision `7d6490e462285cf85d91eabea0f9a954fbddcd1f`, all 14 Parquet files (SHA-256 in
`results_ctx_pref_wc.json`). Run on a GitHub runner (run 44068403883, code 39941b0). Only these aggregates left the runner.
**This is association, not cause** (spec §0).

**Verdict: INCONCLUSIVE.** 536,786 events from 474,405 English conversations. PERSONAL held 2,074 events, and only
185 of them had a stabilising reply (200 needed). CODE had 117 (S) and 112 (Q). Only OTHER was usable.

## Counts
Conversations read 837,989; duplicates 11,670; English 474,405; events 536,786; replies without a
next user turn 474,405. Contexts: PERSONAL 2,074, CODE 15,189, OTHER 519,523.

## Cells (stratified difference in reaction score, with F − without; cluster-robust 99.944%)
| Feature in context | Events with / without | Estimate [interval] |
|---|---|---|
| S in PERSONAL | 185 / 1,889 | too few |
| Q in PERSONAL | 152 / 1,922 | too few |
| S in CODE | 117 / 15,072 | too few |
| Q in CODE | 112 / 15,077 | too few |
| S in OTHER | 13,012 / 506,511 | -0.0032 [-0.0088, +0.0025] |
| Q in OTHER | 22,432 / 497,091 | -0.0113 [-0.0204, -0.0022] |

## By model family (the verdict's sign check)
| Cell | Events with / without | Estimate [interval] |
|---|---|---|
| S · PERSONAL · GPT-3.5 | 107 / 969 | too few |
| S · PERSONAL · GPT-4 | 78 / 920 | too few |
| Q · PERSONAL · GPT-3.5 | 128 / 948 | too few |
| Q · PERSONAL · GPT-4 | 24 / 974 | too few |
| S · CODE · GPT-3.5 | 73 / 7,439 | too few |
| S · CODE · GPT-4 | 44 / 7,633 | too few |
| Q · CODE · GPT-3.5 | 98 / 7,414 | too few |
| Q · CODE · GPT-4 | 14 / 7,663 | too few |
| S · OTHER · GPT-3.5 | 10,545 / 343,560 | -0.0047 [-0.0110, +0.0016] |
| S · OTHER · GPT-4 | 2,467 / 162,951 | +0.0037 [-0.0094, +0.0168] |
| Q · OTHER · GPT-3.5 | 16,078 / 338,027 | -0.0137 [-0.0256, -0.0018] |
| Q · OTHER · GPT-4 | 6,354 / 159,064 | -0.0050 [-0.0157, +0.0057] |

## Information only
| Feature in context | Unstratified | Positive with / without | Repair with / without |
|---|---|---|---|
| S in PERSONAL | +0.0083 | 0.0486 / 0.0439 | 0.0054 / 0.0090 |
| Q in PERSONAL | -0.0243 | 0.0197 / 0.0463 | 0.0066 / 0.0088 |
| S in CODE | -0.0119 | 0.0000 / 0.0118 | 0.0171 / 0.0171 |
| Q in CODE | -0.0036 | 0.0089 / 0.0117 | 0.0179 / 0.0170 |
| S in OTHER | -0.0033 | 0.0194 / 0.0219 | 0.0108 / 0.0100 |
| Q in OTHER | -0.0125 | 0.0151 / 0.0221 | 0.0152 / 0.0098 |

## Reading
- Registered: inconclusive. Personal moments are 0.4% of events, and stabilising replies to them are rarer still.
- In OTHER, replies that end by asking back are followed by worse reactions: −0.011 [−0.020, −0.002], with fewer thanks
  (1.5% vs 2.2%) and more repair (1.5% vs 1.0%). This agrees in direction with CTX_PREF_HH, where asking back was chosen
  less often in everyday prompts. Within GPT-4 alone the interval includes zero.
- Reactions are sparse: about 2% of next turns thank and 1% ask for repair, so most events carry no signal.
