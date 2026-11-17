# ADOPT_WC — do the AI's words become the person's own words in later conversations? (WildChat-1M)

Status: registered 2026-11-17, before any code and before this run opens the data. Results in §8, in a separate record
commit.

## 0. Origin and question

- Phase 9 (AGENTS.md §11.11) replicated, on public data, that output becomes input *within* a conversation.
- This test asks whether it persists *across* a person's conversations. When the AI first uses a word with a person, does
  the person later write that word unprompted, at the start of a new conversation, more than topic persistence alone
  would explain?
- Disclosed: the idea comes from the owner's private record (LSGPA). Nothing about cross-conversation word adoption has
  been computed on WildChat before this registration.

## 1. Data and access

- `allenai/WildChat-1M` (ODC-BY), all Parquet files at the revision current at run time; revision and SHA-256 recorded.
- The job runs on a GitHub runner (`.github/workflows/adopt_wc.yml`) and prints aggregates only. No text, word, hash or
  user key is printed.
- Inclusion: English (top-level `language` "English"); each `conversation_hash` kept once.

## 2. Persons and order (fixed now)

- A person is the pair (top-level `hashed_ip`, `header` user-agent), as in Phase 9. Their conversations are ordered by
  `timestamp`.
- Kept: persons with 3 to 200 included conversations. Above 200 suggests a shared address or an automated client.
- Disclosed: one address can hide several people, and one person can use several addresses.

## 3. Words (fixed now)

- Lower-case alphabetic tokens of at least 6 letters, excluding the fixed stop list `adopt_wc.STOP`.
- For each conversation c, A(c) is the set of words in its assistant turns and U(c) the set of words in its user turns.
- F(c) is the set of words in the **first** user turn of c. It is written before the person sees any reply in c.

## 4. Events and the placebo (fixed now)

For a person's conversations c_0 … c_{n−1} and each k with 1 ≤ k ≤ n − 2:
- **X_prev** = A(c_{k−1}) minus every word in U(c_0 … c_{k−1}) and in A(c_0 … c_{k−2}). These are words the AI first used
  with this person in the conversation just before, and the person had never typed.
- **X_next** = A(c_{k+1}) minus every word in U(c_0 … c_{k−1}) and in A(c_0 … c_{k−1}). These are words the AI first uses
  in the conversation just after, which the person had neither typed nor been shown before c_k.
- p_prev = |F(c_k) ∩ X_prev| / |X_prev|; p_next = |F(c_k) ∩ X_next| / |X_next|.
- An event needs |X_prev| ≥ 5 and |X_next| ≥ 5.
- X_next cannot have influenced F(c_k). It measures how far a person's next conversation continues the same topic.
- Disclosed: X_next can include words the person writes first in c_k and the AI echoes in c_{k+1}. That raises p_next and
  makes the test conservative.

## 5. Measure and pass

- Per person: the mean over their events of (p_prev − p_next).
- Statistic: the mean over persons.
- Interval: percentile bootstrap over persons, 2000 resamples, seed 12345, 99%.
- **PASS** when the interval's lower bound is above 0 and at least 500 persons have an event.
- **FAIL** when the interval contains or lies below 0 with ≥ 500 persons.
- **NOT TESTABLE** with fewer than 500 persons.

Reported beside the verdict, not part of it:
- p_prev and p_next separately.
- By gap between c_{k−1} and c_k: under 1 day, 1–7 days, over 7 days.
- Dose: X_prev words the AI used 3 or more times in c_{k−1}, against words used once.
- Counts at each step.

**Sealed prediction:** P(PASS) = 0.55.

## 6. What a pass would and would not show

- It would show that words an AI introduced to a person appear in that person's own later writing more than topic
  persistence explains, in a large public sample.
- It would not show harm, and it would not show this generalises beyond 2023–2024 GPT-3.5 and GPT-4.
- It is observational, with a placebo built for the main alternative (topic persistence).

## 7. If it fails
A failure is recorded as such. No other word definition or window is tried on this data.

## 8. Results (recorded after code 84b660f; GitHub run 44084235343; `rsxv/results/adopt_wc.md`)

- Revision 7d6490e462285cf85d91eabea0f9a954fbddcd1f, 14 files. 120,611 persons; 28,366 kept; 26,783 with an event; 170,061
  events.
- **Verdict: FAIL.** Mean (p_prev − p_next) = -0.0046, 99% [-0.0059, -0.0032]; p_prev 0.0161,
  p_next 0.0206.
- The sealed prediction (P(PASS) = 0.55) was wrong.
- Information only: under 1 day +0.0022; 1–7 days -0.0200; over 7 days
  -0.0354; dose (3+ uses minus 1 use) +0.0131.
- The §4 bias (X_next can contain words the person writes first in c_k and the AI echoes later) probably inflates the
  placebo. The result reads "not shown by this design", not "no adoption". No other definition is tried on this data (§7).
