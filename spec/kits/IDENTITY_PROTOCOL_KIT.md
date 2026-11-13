# IDENTITY protocol kit: do identity profiles change people?

A ready protocol for testing identity profiles with real people. Module specification: [IDENTITY.md](../IDENTITY.md).

## 1. Questions

1. Over six months, does practising an identity profile raise its coherence more than a control practice (claim C41)?
2. Does the behaviour start in places that were never trained, and how quickly (C17)?
3. Is a context recalled better or faster from an anchor tree than from a single image (C16)?
4. Does mirroring other people pull a person away from their profile, and does practice reduce that pull (C89)?
5. Is a rehearsed value conflict visible in the body, and does the profile's symbol bring it back (C62)?
6. Does practising the profile in its own language help more than the first language (C82, TRIAL design `identity_language`)?

## 2. Design

- **Randomised, parallel groups**: identity profile practice (the day symbol, the night chain, the prepared week, then the month's dose) against a control practice of equal time (for example general relaxation with the same scheduling).
- **Duration**: one prepared week, then 26 weeks; ratings weekly.
- **Within-person parts**: anchor tree against single image (both for every participant, order alternated); value-conflict rehearsals against ordinary situations; the language trial as a series of N-of-1 trials (TRIAL).
- **Sample size**: plan from a pilot. In the simulation, a rise of one point a month was found in two thirds of single people after 8 weeks; a group comparison needs far fewer weeks.

## 3. Measures

| Measure | When |
|---|---|
| Level ratings, 0-10, all seven levels | Weekly, and after time with other people when it happens |
| Generalisation log | Whenever the person meant to act from the profile |
| Anchor tree and single-image walks | Weekly |
| RMSSD before, during and after value-conflict and ordinary rehearsals (chest strap preferred) | Fortnightly |
| Switch log and settle time | Whenever a switch happens |
| A validated self-concept clarity scale and wellbeing scale | Baseline, week 8, week 26 |
| Adverse events | Any time (the Safety page) |

## 4. Consent wording (adapt to your ethics board)

> You will design a profile of who you want to be in one area of your life and practise it with short cues by day and, if you agree, a longer one as you fall asleep. Each week you will rate how true each part feels. Some exercises measure your heart while you imagine situations that go against your values; you can skip any of them. Your results are stored without your name. You can stop at any time. The methods are experimental and are not a treatment.

## 5. Data format

The page exports each profile as `rsos-identity/1` JSON (the profile with its ratings, contexts, walks, rehearsals and versions) and the switch log. Dates become day numbers before sharing; the research contribution format (spec/DATA_CONTRIBUTION.md) can carry these files.

## 6. Analysis

- Question 1: coherence over time, a mixed model with participant as a random effect and group by time as the fixed effect of interest.
- Question 2: share of new contexts where the behaviour started, by group; time to start.
- Question 3: paired differences in accuracy and time, tree minus single image, pooled across participants.
- Question 4: `drift` per participant, then the difference in drift between groups.
- Question 5: reaction and recovery per participant against ordinary situations; sensitivity and false flags across participants.
- Question 6: TRIAL analysis of `identity_language`, pooled with random effects.

## 7. Report template

1. Participants, groups, completion of the prepared week and the dose.
2. Coherence over 26 weeks by group, with intervals.
3. Generalisation and time to start.
4. Anchor tree against single image.
5. Drift while mirroring others, by group.
6. Value-conflict reactions and recovery.
7. The language trial.
8. Self-concept clarity, wellbeing and adverse events.
9. What this means for claims C16, C17, C41, C61, C62, C82 and C89.
