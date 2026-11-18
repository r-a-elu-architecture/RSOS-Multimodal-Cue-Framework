# TURN_RATINGS — does what the supporter does predict the person's own next rating? (ESConv; WORLD_10X planet 8)

Status: registered 2026-11-18, before any code, before the pilot look and before any rating is read against any supporter
action. Results go in §9, in separate record commits. Context: spec/world10x/WORLD_10X.md row 8; spec/PERSONLAB.md §9
step 5 (final intensity carries no strategy signal); spec/RAPPORT_ESCONV.md (the same ratings, other features).

## 0. Why

Every agent and transfer result in this repository rests on stated person models in which one action wins (BASELINE_AUDIT,
STAB_DEFAULT). The Person Lab tried to replace them with data and failed at the grain it used: one final intensity per
conversation. ESConv also records the seeker's own 1–5 rating of the support just given, about 7,681 times: roughly 10×
more outcome events than conversations. This test asks, at that grain and with the person's own ratings:

- **Q1 (strategy).** Does the supporter's action predict the next rating beyond persistence, stage and the person's
  starting state?
- **Q2 (context).** Does the effect of the action depend on the stage of the conversation? A yes is the first measured case
  in this project where the best action depends on context, which every switching and transfer test needs (BASELINE_AUDIT
  §6).

No real person is involved. The data are recorded, public and de-identified.

## 1. Data

- ESConv, `thu-coai/Emotional-Support-Conversation`, commit f262d06, file `ESConv.json` (CC BY-NC 4.0). `FailedESConv.json`
  is not used.
- All conversations in the file. Aggregates only leave the workspace; nothing about any conversation is published.
- **Disclosed earlier contact.** Before this registration: the rating counts (RAPPORT_ESCONV §1); the 104 Person Lab
  conversations were read for profiles and reader stress (PERSONLAB steps 3–5c), not for ratings against actions;
  RAPPORT_ESCONV computed means within action × stage strata internally on all but those 104, as weights for its own
  features, and never printed them. No action → rating number has been seen by anyone in this project. Step 5b printed
  reader-stress change per action; that is a different outcome and is not used here.

## 2. Unit (as RAPPORT_ESCONV §1, extended)

- **Event:** a seeker turn s_i, the block of supporter turns after it, and the next seeker turn s_{i+1}, which carries a
  rating (`annotation.feedback`). Outcome y = that rating (1–5).
- **Previous rating** p: the most recent rating earlier in the same conversation. Events without one are counted and leave
  the primary analysis (they have no persistence baseline).
- **Stage:** first, middle or last third of the conversation's seeker turns (RAPPORT's rule).
- **Start:** the seeker's pre-chat `initial_emotion_intensity` (1–5); events from conversations without it are counted and
  dropped.
- **Action of the block:** five indicators, one per action of `person.STRATEGY_TO_ACTION` (STABILISE, EXPLORE, SUGGEST,
  SHARE, NONE), true when any supporter turn in the block carries a strategy mapped to that action. A block can have
  several.

## 3. Split

Conversations are permuted with seed 2101 and split in half: **development** (models are fitted here) and **test**
(contrasts are measured here). No model sees the test half before its fit is fixed.

## 4. Stage P: the pilot look at the unit (counts only)

Run first, on all conversations, printing only:
- conversations; rated seeker turns; events; events with a previous rating, overall and per half;
- events per conversation (median, quartiles);
- how often each action indicator is true, and how many indicators a block has;
- the overall rating distribution of events with a previous rating, and the share at 5 (the ceiling).

Stage P prints nothing that pairs an action with a rating. **Amendment rule:** stage P may change only the unit (§2), and
only if the test half holds fewer than 1,500 events with a previous rating or an action indicator is true in fewer than
100 test events. Any change is committed as an amendment, with its reason, before stage M runs. Thresholds (§6) never
change.

## 5. Stage M: models (least squares, fitted on the development half; predictions clipped to [1, 5])

| Model | Inputs |
|---|---|
| B0 persistence | ŷ = p |
| B1 baseline | intercept, p, stage (2 indicators), start |
| M1 strategy | B1 + the 5 action indicators |
| M2 context | M1 + action × stage interactions (5 × 2 indicators) |

Measure: squared error per test event. Contrast: mean of (error of the richer model − error of the simpler one), with an
interval from a bootstrap over test conversations (2000 resamples, seed 12345), at level 1 − 0.01/2 (two verdict
contrasts).

## 6. Verdicts (fixed now; δ = 0.01 rating² of mean squared error)

- **Q1, M1 − B1:** **SIGNAL** if the upper bound is below 0; **NULL** if the interval lies inside [−δ, +δ]; **WORSE** if the
  lower bound is above +δ; otherwise **INCONCLUSIVE**.
- **Q2, M2 − M1:** the same rule.

Reported beside the verdicts, not part of them:
- B1 − B0 with its interval (does the baseline beat persistence?);
- each M1 action coefficient with a bootstrap interval (association, per action);
- the test-half mean squared error of every model, and the share of predictions at the clip.

**Sealed predictions:** P(Q1 SIGNAL) = 0.40; P(Q2 SIGNAL) = 0.15; P(B1 beats B0, interval below 0) = 0.85. Expected size:
under a 2% relative reduction in mean squared error for M1, because 52% of ratings sit at 5.

## 7. What a result would and would not show

- It would show whether, in recorded support conversations, what a supporter did is associated with the seeker's own next
  rating, beyond persistence and starting state, and whether that association changes across the conversation.
- It would not show cause: supporters chose their actions. The raters were crowdworkers playing seekers, not clients.
  Strategy labels are the supporters' own annotations.

## 8. What follows (fixed now)

- **Q1 SIGNAL:** the M1 coefficients become the Person Lab's measured action effects, replacing the equal placeholders and
  labelled "association, ESConv ratings". They are the input for WORLD_10X row 1 (an environment fitted from data).
- **Q2 SIGNAL:** the first measured case where the best action depends on context; switching becomes testable on a fitted
  environment (WORLD_10X rows 1 and 3).
- **Q1 and Q2 NULL:** ESConv ratings do not separate supporter actions at this grain. The Person Lab agents cannot be
  validated on this data, and WORLD_10X row 1 needs other data. The switching idea is not supported here.
- **INCONCLUSIVE:** more rated events are needed (WORLD_10X row 11, pooling).

## 9. Results

(recorded per stage, in separate commits)

### Stage P (code fca11ec; `rsxv/results/turn_ratings_pilot.json`; ESConv.json SHA-256 aa0556c5…f7efdd9af)

- 1,300 conversations; 7,681 rated seeker turns; 7,605 events; 1,253 without a previous rating; 0 without a start.
- **Usable events 6,352: development 3,119, test 3,233.** Events per conversation: median 4 (quartiles 4–6).
- Action indicators true in test events: STABILISE 1,102, SUGGEST 1,102, EXPLORE 792, NONE 637, SHARE 484. Indicators per
  block: one 4,723, two 1,557, three 68, four 4.
- Rating distribution of usable events: 1: 47, 2: 128, 3: 817, 4: 1,890, 5: 3,470; **54.6% at 5**.
- **No amendment** (§4): the test half holds ≥ 1,500 usable events and every indicator is true in ≥ 100 test events. Stage M
  runs as registered.

### Stage M (code fca11ec, run once after stage P was recorded in e0da9ed; `rsxv/results/turn_ratings.json`)

- Fitted on 3,119 development events; measured on 3,233 test events in 650 conversations. Run time 9 s.
- Test mean squared error: B0 persistence 0.677; **B1 0.4926; M1 0.4918; M2 0.4950**.
- **Q1, M1 − B1: −0.0008 [−0.0036, +0.0019] → NULL.** The interval lies inside ±0.01: the supporter's action adds nothing
  measurable to the next rating beyond the previous rating, stage and starting intensity.
- **Q2, M2 − M1: +0.0032 [+0.0005, +0.0063] → NULL.** Letting the action's effect depend on the stage adds nothing; the
  richer model is slightly worse on the test half (overfitting), within the band.
- Reported beside them: **B1 − B0: −0.185 [−0.232, −0.141]**: the previous rating and starting intensity, used together,
  predict better than persistence (27% lower error). M1 action coefficients (rating points, 99.5% intervals): EXPLORE
  −0.08 [−0.19, +0.02]; SHARE +0.05 [−0.05, +0.15]; NONE −0.01 [−0.13, +0.09]; STABILISE −0.005 [−0.09, +0.08];
  SUGGEST +0.004 [−0.10, +0.09]. Every interval contains 0. Share of predictions at the clip: B0 0.50 (persistence at 5),
  B1 0, M1 0, M2 0.001.
- **Independent recomputation.** A separately written script (different parser, normal equations; workspace only)
  reproduced the event counts (6,352; 3,119 / 3,233) and all four errors to six decimals.
- **Sealed predictions:** P(Q1 SIGNAL) = 0.40, not met; P(Q2 SIGNAL) = 0.15, not met; P(B1 beats B0) = 0.85, met.

**Reading (§8).** Q1 and Q2 are NULL, so by the rule fixed before the run: ESConv ratings do not separate supporter actions at
this grain; the Person Lab agents cannot be validated on this data; WORLD_10X row 1 needs other data; the switching idea is
not supported here. This is now the third ESConv outcome with no action signal (conversation-level intensity, PERSONLAB
step 5; VAKOG matching and echo, RAPPORT_ESCONV; turn-level action, here), and the first measured as equivalence rather
than as an interval that merely contains zero. What does predict the next rating is the person: their previous rating and
their starting state. Limits as §7: association only; crowdworkers playing seekers; strategy labels by supporters; a
ceiling of 54.6% at 5. The EXPLORE coefficient points the same way as the asking-back findings (CTX_PREF_HH, CTX_PREF_WC) but
its interval contains 0 and it is not a finding.

## 10. Corrections, 18 November 2026 (FIXES_NIGHT, after the night review, pull request #11)

- **TR-1, wording.** The outcome is the seeker's 1–5 rating of the support just given, not the seeker's own state; the
  seekers were crowdworkers; the result is an association. Every sentence about this test now says "did not measurably
  improve the prediction of the seeker's next rating of the support (within ±0.01 squared error)". The review's
  sensitivity check (not registered) found that a per-action effect of about +0.1 rating points (STABILISE) would have
  given SIGNAL, while +0.1 on SHARE and about +0.12 net on EXPLORE stay NULL: the NULL rules out per-action effects larger
  than about 0.1–0.2 points, not every effect.
- **TR-2.** The NULL is consistent with the Person Lab's equal effects but does not show them: equal ratings do not imply
  equal effects on intensity, arousal, openness or progress. The effect option now reads "Equal (placeholder; consistent
  with ESConv ratings)".
- **TR-3.** §0's "roughly 10× more outcome events than conversations" is wrong: 7,681 ratings over 1,300 conversations is
  5.9×. The ≈10× of WORLD_10X row 8 compares with the 756 conversation outcomes of step 5; against step 5's 100 test
  conversations, 6,352 usable events is 63×.
- **TR-4.** The registration was pushed 90 s before 309 lines of code and 7 tests, so the code was written before the
  registration was pushed. The order rule holds; git cannot show the code was not run earlier (it was not). Future steps
  register before writing code, or put the code's tree hash in the registration.
