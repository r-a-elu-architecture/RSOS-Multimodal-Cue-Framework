# CTX_PREF_HH — the same question on human preference pairs where personal requests are common

Status: registered 2026-11-17, before any code and before the data is opened in this project. Results go in §7, in a
separate record commit. Second attempt at the question of spec/CTX_PREF.md, which was inconclusive (128 PERSONAL prompts).

## 1. Data

- `Anthropic/hh-rlhf` on Hugging Face, the card's licence: MIT. Only the helpfulness files: `helpful-base`,
  `helpful-online` and `helpful-rejection-sampled`, train and test. The harmless (red-team) files are excluded.
- Each line holds two transcripts, `chosen` and `rejected`. They share the conversation up to the last assistant reply,
  and a crowdworker preferred the chosen reply.
- Same access and privacy as CTX_PREF: a GitHub Actions job (`.github/workflows/ctx_pref_hh.yml`) prints only aggregates,
  file hashes (SHA-256) and the dataset revision. No text leaves the runner.
- Disclosed: the replies come from 2022 research models, and the raters were told to prefer the more helpful reply.

## 2. Pairs (fixed now)

- Split each transcript at its last "\n\nAssistant:". Keep the pair only if the two prefixes are identical, both replies
  are non-empty and the replies differ.
- The prompt is the text of the last "Human:" turn in the shared prefix.

## 3. Context, features and measure: unchanged from CTX_PREF

- The same code and the same fixed patterns: `ctx_pref.PERSONAL_RX` and `ctx_pref.STAB_RX`, plus the Q rule, the 1.25
  length match and n ≥ 50. Nothing is retuned.
- Contexts: **PERSONAL** (the prompt matches `PERSONAL_RX`) and **OTHER**. The data has no code flag, so there is no CODE
  context.
- The winner is the chosen reply. k = pairs where the reply with the feature was chosen.
- Level: four cells and the second attempt at this question, so the Wilson intervals are at 1 − 0.01 / 4 / 2 (two-sided
  99.875%).

## 4. Verdict (as CTX_PREF §6)

- **CONTEXT-DEPENDENT:** for a feature, one context's interval lies above 0.5 and the other's below.
- **SAME DIRECTION:** no crossover, with both contexts usable for both features.
- **INCONCLUSIVE:** otherwise.

Reported beside the verdict, not part of it:
- Unmatched cells.
- S in PERSONAL minus S in OTHER, with a 99% interval. A clear difference without a crossover means "the size of the
  preference depends on context".
- Counts per file.

**Sealed prediction:** P(CONTEXT-DEPENDENT) = 0.30. Most likely: S favoured in PERSONAL and neutral in OTHER (a difference
in size, without a crossover).

## 5. Limits

- One rater group, 2022 models, an instruction to judge helpfulness, and text-pattern features.
- A crossover would support context-dependent switching in what people prefer to read, not in what helps them over time.
- SAME DIRECTION would add real-data weight to the BASELINE_AUDIT finding.

## 6. If PERSONAL is again too small
If PERSONAL has fewer than 50 discordant length-matched pairs for both features, the verdict is INCONCLUSIVE and that is
the result. No new pattern is tried on this data.

## 7. Results
(recorded after the run, in a separate commit)
