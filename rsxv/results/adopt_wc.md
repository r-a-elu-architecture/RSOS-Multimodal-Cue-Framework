# ADOPT_WC — do the AI's words become the person's own across conversations? (results)

Design: [`spec/ADOPT_WC.md`](../../spec/ADOPT_WC.md), registered before the code and the run. Data: `allenai/WildChat-1M`,
revision `7d6490e462285cf85d91eabea0f9a954fbddcd1f`, all 14 files (SHA-256 in `results_adopt_wc.json`). GitHub run 44084235343, code 84b660f.
Only these aggregates left the runner.

**Verdict: FAIL.** Mean over 26,783 persons (170,061 events) of p_prev − p_next = -0.0046,
99% bootstrap interval [-0.0059, -0.0032]. Words the AI first used in the conversation before appeared in the
person's next opening message less often than the placebo words from the conversation after.

## Counts
Conversations read 837,989; duplicates 11,670; English 474,405; persons 120,611; kept (3–200
conversations) 28,366; over 200 158; conversations of kept persons 267,547.

## Information only (not part of the verdict)
| Measure | Value |
|---|---|
| p_prev (AI words from the conversation before, in the next opening message) | 0.0161 |
| p_next (placebo: AI words from the conversation after) | 0.0206 |
| p_prev − p_next, gap under 1 day (148,929 events) | +0.0022 |
| … gap 1–7 days (16,546 events) | -0.0200 |
| … gap over 7 days (4,586 events) | -0.0354 |
| Dose: words the AI used 3+ times minus words used once, adoption rate (103,343 events) | +0.0131 |

## Reading
- Registered: FAIL. Across conversations, this design finds no adoption beyond what the placebo measures.
- The placebo is likely inflated by the bias disclosed in spec §4. X_next can include words the person wrote first in the
  target conversation, which the AI then repeats in the next one. Because the AI echoes the person's words, p_next rises.
  The size of that bias is not measured here, so the failure cannot be read as "no adoption". It can only be read as "not
  shown by this design".
- Information only, not registered results: the difference is slightly positive when conversations are under a day apart,
  and turns negative as the gap grows. Words the AI used 3 or more times were later written by the person more often than
  words it used once (+0.013). Both point the way adoption would, but they are not tests, and the gap pattern fits topic
  drift too.
- Per spec §7, no other word definition or window is tried on this data. A corrected design (X_next excluding every word in
  the target conversation) would be a new registered test on new data, such as WildChat-4.8M beyond these files.
