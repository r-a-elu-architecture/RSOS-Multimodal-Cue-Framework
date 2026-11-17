# RAPPORT_ESCONV — do VAKOG matching and echo get better ratings from the person? (ESConv)

Status: registered 2026-11-17, before any code and before this text is read for these features. Results in §7, in a
separate record commit. Context: spec/PERSONLAB.md §7b–§7c. Reader-rated stress measured tone, not people's own state, so
this test uses **the people's own ratings**.

## 1. Data and outcome

- ESConv (thu-coai, commit f262d06, CC BY-NC 4.0). **All conversations except the 104 used by the Person Lab** (the 100
  and the 4 pilot ones), of every problem type. Aggregates only; nothing about any conversation is published.
- Before this registration only counts were looked at. 7,681 seeker turns carry the seeker's own rating (1–5) of the
  support just given: 1: 73, 2: 179, 3: 1,121, 4: 2,315, 5: 3,993. The ceiling (52% are 5) limits what any factor can show.
- **Event.** A seeker turn s_i, the block of supporter turns after it, and the next seeker turn s_{i+1}, which carries a
  rating. Outcome: that rating. Blocks with no rated next turn are not events.

## 2. Features (fixed now, in `rsxv/rsxv/personlab/rapport.py`)

- **VAKOG channel of a text.** Counts of sensory words from five fixed lists (`rapport.SENSES`): V (see, look, picture,
  …), A (hear, sound, listen, …), K (feel, touch, hold, …), O (smell, …) and G (taste, …). The channel is the sense with
  the highest count, and none when there are no hits or a tie. Disclosed: "feel" is common in support talk, so K will
  dominate.
- **MATCH:** the block's channel equals the channel of s_i, and both exist.
- **ECHO:** at least 25% of s_i's content words (`override.content`) appear in the block. Reported only: any shared run of
  3 words (phrase echo).
- **BOTH:** MATCH and ECHO together.

## 3. Placebos

- **MATCH-placebo:** the block's channel equals the channel of a seeker turn drawn from a **different** conversation
  (seeded, seed 2030).
- **ECHO-placebo:** the block contains at least 25% of the content words of that same drawn turn.

The placebos separate "fits this person" from "fits how people generally write".

## 4. Measure and verdict

- For each of MATCH, ECHO and BOTH: the stratified difference in mean rating between events with the feature and without
  it. For BOTH, the comparison is against events with neither. The strata are the action of the block's first supporter
  turn (5) × the conversation stage (first, middle or last third of the seeker turns), 15 strata in all, with weights
  n1·n0/(n1+n0).
- The same estimate is made with the placebo indicator. For BOTH, the placebo is "both placebos".
- Intervals come from a bootstrap over conversations (2000 resamples, seed 12345), at level 1 − 0.05/3 per feature.

Per feature:
- **HOLDS** when the estimate's interval lies above 0 **and** the interval of (estimate − placebo estimate) lies above 0;
- **NO EFFECT** when the estimate's interval contains 0;
- **NOT SPECIFIC** when the estimate is above 0 but not above the placebo;
- **NEGATIVE** when the estimate's interval lies below 0;
- **NOT TESTABLE** with fewer than 100 events in either group.

Reported beside the verdicts: the counts of each channel, the phrase echo, the share of ratings at 5 in each group, and
each feature's estimate within each stage.

**Sealed predictions:** P(MATCH holds) = 0.15 (earlier academic tests of predicate matching were mostly negative);
P(ECHO holds) = 0.40; P(BOTH holds) = 0.20.

## 5. Limits

- Association, not cause: supporters chose their words.
- Text patterns stand in for senses.
- Ratings are capped by the ceiling.
- The raters were crowdworkers playing seekers in a study, not clients.

## 6. What follows

- A feature that HOLDS becomes a rule the Person Lab agents may use, labelled as association.
- Features that do not hold stay out of the agents' defaults.
- The glyph-tier cue programs remain architecture until tested with people.

## 7. Results (recorded after code 3ce406c; aggregates `rsxv/results/rapport_esconv.json`)

- 1,196 conversations and 6,970 rated events.
- **MATCH: NO EFFECT.** +0.094 on the 1–5 rating, interval [-0.018, +0.197]
  (403 matched events). The placebo is +0.040.
- **ECHO: NO EFFECT.** -0.023, interval [-0.094, +0.048] (989 echo events). The placebo is
  +0.048.
- **BOTH: NOT TESTABLE.** 96 events with both, against the 100 needed.
- **Information.**
  - Most turns name no clear sense (5,188 of 6,970 seeker turns). Among those that do, K leads (751), then A (631)
    and V (394). O and G are almost absent (3 each).
  - Share of ratings at 5: matched 54.1% against 51.5%; echo 49.2% against 52.1%.
  - By stage, MATCH is largest in the middle third (+0.195), but no stage was tested.
- **The sealed predictions** (MATCH 0.15, ECHO 0.40, BOTH 0.20): MATCH and ECHO did not hold. BOTH cannot be scored.
- **What follows (§6).** Neither VAKOG matching nor word echo enters the Person Lab agents' defaults. In this data, how
  people rated the support does not depend on whether the supporter used their sensory words or repeated their words.
