# CTX_PREF_WC — the context question in real conversations, by the person's next reaction (WildChat-1M)

Status: registered 2026-11-17, before any code and before this run opens the data. Results go in §8, in a separate record
commit. This is the third attempt at the question of spec/CTX_PREF.md. The first two (arena votes; hh-rlhf pairs) were
inconclusive because personal prompts were too rare.

## 0. What kind of evidence this is

Each message in a conversation has one reply, so two styles are never compared on the same message. This test measures
**association**: in a context, is a reply style followed by better reactions from the person than other replies? A
crossover between contexts would show that what goes well depends on context. It would not show that the style caused the
reaction.

## 1. Data

- `allenai/WildChat-1M` (Hugging Face; ODC-BY), every Parquet file of the revision current at run time (revision and file
  SHA-256 hashes recorded). Phase 9 used shards 0–2 for other questions; nothing about reply style or reactions was looked
  at then.
- Access as CTX_PREF: a GitHub Actions job (`.github/workflows/ctx_pref_wc.yml`) prints aggregates only. If the dataset
  refuses download (gated), the job stops and that is reported. No other credentials are used.
- Inclusion: top-level `language` is "English"; each `conversation_hash` is kept once.

## 2. Events (fixed now)

- An event is a user turn u, the assistant reply a that follows it, and the next user turn u' in the same conversation.
- Turns without a next user turn are not events. They are counted and reported.
- Model family: GPT-4 when the `model` field starts with "gpt-4", otherwise GPT-3.5.

## 3. Context of u, features of a (fixed now)

- **PERSONAL:** u matches `ctx_pref.PERSONAL_RX` and is not CODE.
- **CODE:** u contains "```" or matches `ctx_pref_wc.CODE_RX`: a line starting with `def `, `class `, `import `, `#include`,
  `function `, `public `, `SELECT `, `const ` or `let `, or the text `console.log(`.
- **OTHER:** everything else.
- **S** and **Q** exactly as CTX_PREF (`feat_s`, `feat_q`).

## 4. Outcome from u' (fixed now; first 300 characters, lower case)

- **Positive:** `ctx_pref_wc.POS_RX` ("thank", "thanks", "thx", "great", "perfect", "that helps", "helpful", "awesome",
  "it works", "it worked", "exactly what").
- **Repair:** `ctx_pref_wc.REP_RX` (starts with "no" or "nope"; "not what i", "that's wrong", "that is wrong", "incorrect",
  "doesn't work", "does not work", "didn't work", "you didn't", "you misunderstood", "try again", "still wrong",
  "still not", "still doesn't").
- Score = 1 if positive and not repair, −1 if repair and not positive, otherwise 0.

## 5. Measure

For a feature F and context c:
- Events are split into ten reply-length strata (deciles of the reply's length within c).
- The estimate is the stratified difference in mean score between replies with and without F. The weights are
  w_s = n1·n0 / (n1 + n0) per stratum, normalised.
- The interval is normal, with a cluster-robust standard error by conversation (influence functions summed per
  conversation), at level 1 − 0.01 / 6 / 3 (six cells, third attempt: two-sided 99.944%).
- A cell is usable when it holds at least 200 events with F and 200 without.

## 6. Verdict (fixed now)

- **CONTEXT-DEPENDENT:** for a feature, one context's interval lies above 0 and another's below 0, **and** in each model
  family separately the point estimates in those two contexts have the same signs as the pooled ones.
- **SAME DIRECTION:** no such crossover, and all three contexts are usable for both features.
- **INCONCLUSIVE:** otherwise.

Reported beside the verdict, not part of it:
- Unstratified differences.
- Positive and repair rates separately.
- Each family's estimates.
- Counts at each step.

**Sealed prediction:** P(CONTEXT-DEPENDENT) = 0.30. Most likely: Q associated with worse reactions in CODE and OTHER, as in
hh-rlhf, and S near zero outside PERSONAL.

## 7. Limits

- Association, not cause.
- Text-pattern contexts, styles and reactions, in English only.
- 2023–2024 models (GPT-3.5 and GPT-4).
- Leaving a conversation is not counted as a reaction.
- Only aggregates leave the runner. No text, hash or model output is published.

## 8. Results
(recorded after the run, in a separate commit)
