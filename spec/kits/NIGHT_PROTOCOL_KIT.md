# NIGHT protocol kit: cueing during sleep and reward codes

A ready protocol for testing closed-loop vibration cueing during sleep and reward codes with real people. Module specification: [NIGHT.md](../NIGHT.md).

## 1. Questions

1. Does replaying vibration codes in deep sleep improve next-day recall of cued items over uncued items (C7, C8)?
2. Does closed-loop cueing avoid the arousals and lost sleep that random cueing causes (C36)?
3. Does a safety code or gentle waking on a detected nightmare reduce nightmare frequency and distress (C5, C33)? Only with a clinician, in people with nightmares, never replaying trauma-related cues.
4. Do reward codes on success, and their night replay, improve skill (C9)?
5. Is a cue noticed sooner with light than with vibration alone (C28)?

## 2. Design

- **Memory (1, 2)**: within-person targeted memory reactivation. In the evening, learn 40 items (word pairs of a language being learned) each paired with a code; test; assign 20 to cueing at random. Sleep with a staging headband running the plan. Test in the morning. Seven nights per person, 20 or more people. A randomised sub-study compares closed-loop with random cueing.
- **Nightmares (3)**: alternating cueing and no-cueing weeks, four weeks, nightmare diary each morning, with a clinician.
- **Reward (4)**: 2 x 2 factorial over four weeks: reward codes on success or not, night replay or not; 80 or more athletes; a test of 50 attempts at the start and end.
- **Notice (5)**: ten trials a day for five days, vibration alone and with light alternating.

## 3. Measures

| Measure | When |
|---|---|
| Recall of cued and uncued items | Evening and morning |
| Night report from the device: stages, cues by stage, arousals | Each night |
| Sleep quality (a validated questionnaire) and next-day mood | Each morning |
| Nightmare count and distress (0-10) | Each morning |
| Reward log: successes, rewards, latencies | Each session |
| Skill test | Start and end |
| Adverse events, including disturbed sleep | Any time (the Safety page) |

## 4. Consent wording (adapt to your ethics board)

> On some nights a headband reads your sleep stages and, only in deep sleep, plays the vibration codes you practised during the day, very softly, stopping if you start to wake. Codes linked to painful memories are never played. You can turn cueing off at any time, and you will be asked each morning how you slept. The methods are experimental and are not a treatment.

## 5. Data format

The night plan (`rsos-night/1`), the device's night report, the recall counts per night, the diary and the reward log, as the page and the device export them. Dates become night numbers before sharing; the research contribution format (spec/DATA_CONTRIBUTION.md) can carry these files.

## 6. Analysis

- Question 1: `tmr_analyze` per person; pool retention advantages across people with a 95% interval (a mixed model with person as a random effect).
- Question 2: arousals, time awake and deep-sleep minutes per night by policy, against no-cue nights.
- Question 3: `diary_compare` per person; pooled difference.
- Question 4: main effects of reward and replay with intervals; their interaction.
- Question 5: `notice_report` per person; pooled difference in time to notice.

## 7. Report template

1. Participants, nights, devices and their staging accuracy where known.
2. Cues by stage, arousals, sleep measures, by policy.
3. Retention of cued against uncued items.
4. Nightmares (clinical arm only).
5. Reward and replay effects on skill.
6. Notice test.
7. Adverse events.
8. What this means for claims C5, C7, C8, C9, C28, C33 and C36.
