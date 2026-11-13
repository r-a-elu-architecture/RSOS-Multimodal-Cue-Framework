# ATLAS protocol kit: does a change on one trigger spread to others?

A ready protocol for testing the trigger atlas and the transfer engine with real people. Module specification: [ATLAS.md](../ATLAS.md).

## 1. Questions

1. Does a two-week map predict a person's state at moments it has not seen (C93)?
2. After work on the strongest trigger, do untreated triggers change beyond the change between two untreated mappings (C94)?
3. Is the network trance better or worse than a timeline session at changing untreated triggers (C95)?
4. Does working from a higher node help more than working on the trigger, and does the benefit rise, peak or fall with the level (C99, C100)?
5. Does rerouting a strong trigger to a proven anchor lower the state in the minutes after (C92)?

## 2. Design

- **Mapping**: ecological momentary assessment, 8 to 10 prompts a day at random times within waking hours, for two weeks; one in five prompts asks about an ordinary moment.
- **Repeat mapping** of two weeks with no treatment.
- **Randomisation** to network trance (three sessions in a week, on the strongest trigger) or a timeline session (same number and length), then a third two-week mapping.
- **Level sweep** (optional arm): eight sessions at each of five levels in one dimension, in random order.
- **Rerouting** (optional): with an anchor at suggest or automatic on the Safety page, offers are logged and the state is rated 10 minutes later; compare with randomly withheld offers.
- **Sample size**: the simulation finds spread in two thirds of single people with two-week mappings; a two-arm comparison should be planned from a pilot.

## 3. Measures

| Measure | When |
|---|---|
| Nodes present and state before and after (0-10) | Each prompt |
| Untreated trigger rating, before and after each session | Each session |
| Weights, readiness and prediction | End of each mapping |
| A validated anxiety or stress scale | Baseline, end of each mapping |
| Adverse events | Any time (the Safety page) |

## 4. Consent wording (adapt to your ethics board)

> For six weeks your phone will ask you, a few times a day, what is around you and how you feel. In between, you will do three short guided sessions, either imagining a journey through your own map of triggers or a timeline exercise. You can skip any prompt and stop at any time. Your answers are stored without your name. The methods are experimental and are not a treatment.

## 5. Data format

The page exports the atlas as `rsos-atlas/1` JSON (nodes, exposures with phase, treatments, sweep and routes). Dates become day numbers before sharing; the research contribution format (spec/DATA_CONTRIBUTION.md) can carry these files.

## 6. Analysis

- Question 1: `predict` per participant; pooled share of participants whose map predicts, and the mean error reduction.
- Question 2: `transfer` per participant; pool the mean untreated change with random effects.
- Question 3: compare the pooled transfer between arms; and the TRIAL design `network_vs_timeline` for within-person comparisons.
- Question 4: `sweep_report` per participant; the share with each shape, and abstraction against scope pooled.
- Question 5: state change after offers against withheld offers, mixed model with participant as a random effect.

## 7. Report template

1. Participants, prompts answered, nodes per atlas.
2. Map readiness and prediction.
3. Drift between the two untreated mappings.
4. Transfer by arm, per participant and pooled.
5. Level sweep shapes.
6. Rerouting.
7. Adverse events.
8. What this means for claims C92 to C95, C99 and C100.
