# CTX_PREF — does the preferred response style depend on context, in real human votes?

Status: registered 2026-11-17, before any code and before the data is opened in this project. Results go in §8, in a
separate record commit. Rules, levels and thresholds below are fixed here.

## 0. Why

BASELINE_AUDIT (spec/BASELINE_AUDIT.md §6) found that in every stated model one fixed stabilising archetype (Bear) beats every
adaptive method. That is a property of models written by hand. The switching idea needs the opposite: a best response
that changes with context. This test asks real people's votes, with no model written by us.

## 1. Data

- `lmarena-ai/arena-human-preference-140k` (Hugging Face; CC BY 4.0; about 136k votes, April–July 2025). People submit a
  prompt, see replies from two anonymous models side by side, and vote: model_a, model_b, tie or both_bad.
- The prompt is held fixed within a vote, so a vote compares two replies to the same message.
- Access: a GitHub Actions job (`.github/workflows/ctx_pref.yml`) downloads the data on GitHub's runner and runs
  `rsxv/rsxv/ctx_pref.py`. The job prints only aggregate counts, the dataset revision and the row counts. No prompt, reply,
  ID or model name leaves the runner.
- Disclosed: the author has not opened this dataset in this project. The other project's lab used it for different tasks.

## 2. Inclusion (fixed now)

- `winner` is model_a or model_b. Ties and both_bad are excluded and counted.
- English (`language` is "en" or "English").
- First vote of a session (`evaluation_order` = 1, when present), and a single exchange: each side holds exactly one user
  message followed by one assistant message, and the two user messages are identical.
- Both replies are non-empty.
- If a field named here is missing, the job stops before any outcome is computed and prints the column names. A
  correction is then registered as an amendment before the next run.

## 3. Context of the prompt (fixed now, from the prompt and `is_code` only)

- **PERSONAL:** not code, and the prompt matches the everyday personal-difficulty pattern in `ctx_pref.PERSONAL_RX`. That
  pattern is a first-person statement of feeling or difficulty ("I feel", "I'm stressed", "I'm overwhelmed", "I'm worried",
  "having a hard time", "I don't know what to do", and similar everyday words). It uses no clinical or crisis wording.
- **CODE:** `is_code` is true.
- **OTHER:** everything else.

## 4. Two style features of a reply (fixed now, from the reply text only)

- **S, stabilising acknowledgment** (the stabilising function, Bear's role in the models): the reply contains a phrase from
  `ctx_pref.STAB_RX`, such as "I'm sorry", "that sounds hard", "it's okay to", "you're not alone", "take a deep breath",
  "one step at a time", "it makes sense to feel".
- **Q, asking back** (the review function): the reply's last non-empty paragraph ends with a question mark.

## 5. Measure

For each feature F and context c, take the **discordant, length-matched** votes: exactly one reply has F, and the longer
reply is at most 1.25 times the shorter in characters (arena voters favour longer replies, so length is held roughly equal).
- k = votes won by the reply with F; n = such votes. Win rate = k / n.
- Wilson interval at level 1 − 0.01 / 6 (six cells; two-sided 99.83%).
- A cell with n < 50 is "too few" and is not used for the verdict.

## 6. Verdict (fixed now)

- **CONTEXT-DEPENDENT:** for at least one feature, there is a context where the interval lies above 0.5 and another where it
  lies below 0.5 (a crossover: the same style wins in one context and loses in another).
- **SAME DIRECTION:** no crossover for either feature, with at least two usable contexts for each feature.
- **INCONCLUSIVE:** otherwise (too few usable cells).

Reported beside the verdict, not part of it:
- Each cell without length matching.
- The difference in S's win rate between PERSONAL and CODE, with a 99% interval. A clear difference without a crossover
  means "the size of the preference depends on context".
- Counts at each inclusion step.

**Sealed prediction:** P(CONTEXT-DEPENDENT) = 0.45. Most likely: S favoured in PERSONAL; neutral or disfavoured in CODE,
without a full crossover.

## 7. What a result would and would not show

- It would show how real voters on one public arena judged replies to the same prompt, by two crude text features.
- It would not show what helps a person over time, and arena voters are not a clinical sample.
- Model identity is not randomised per style: models that acknowledge more may also be better or worse in other ways. That
  is disclosed, not controlled.
- Style is detected by fixed text rules, not read by meaning.
- A CONTEXT-DEPENDENT result supports building switching on real data; SAME DIRECTION would mean the switching idea needs
  rethinking, as the models suggested.

## 8. Results
(recorded after the run, in a separate commit)
