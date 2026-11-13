# MACHINES protocol kit: posture cues, glyph signalling and value-gated agents

A ready protocol for testing the new channels and the agent identity layer with real people. Module specification: [MACHINES.md](../MACHINES.md).

## 1. Questions

1. Does a posture cue from the phone reduce time spent slouched over a working day, and is it tolerated (item 9)?
2. Can people read the agent-state codes on a wristband while doing another task, and reply in codes (item 43)?
3. Does a value-gated agent make fewer value-breaking choices and more consistent choices than the same agent without the gate, across reworded prompts (C70)?
4. Does the person's error signal (button first, then EEG) teach the agent what its values missed, at an acceptable cost in questions (item 44)?
5. Do people rate a value-gated agent as more trustworthy or caring in a shared task (C72)?

## 2. Design

- **Posture (1)**: within-person, two weeks, alternating days with cues on and off; 30 or more desk workers. Phone or clip-on sensor logs tilt all day either way.
- **Glyph reading (2)**: 20 or more people; 100 codes each over two sessions, while doing a typing or sorting task and while idle. Replies by tapping. Measures: accuracy, reaction time, task slowdown.
- **Agent consistency (3)**: no people needed beyond scenario authors. 200 scenarios, each with an option that breaks a stated value, presented five times as reworded prompts to the same language model with and without the gate. Pre-register the scenarios and the rewordings.
- **Teaching (4)**: 20 or more people supervise a simulated household agent for 40 actions; one disliked kind of action is not in its values. Error signal by button first (a perfect channel), then by EEG error-related potential in a sub-study.
- **Trust (5)**: randomised, 60 or more people, a shared task with a robot or on-screen agent that is gated or not; trust and empathy questionnaires and behavioural reliance.

## 3. Measures

| Measure | Question |
|---|---|
| Share of the day slouched; cues per hour; cues dismissed | 1 |
| Codes read correctly; reaction time; replies correct | 2 |
| Same choice in five rewordings; value-breaking choices | 3 |
| Disliked actions in the first and last thirds; fine actions asked about | 4 |
| Trust and empathy ratings; reliance on the agent | 5 |

## 4. Analysis

- Posture: mixed model of slouched share by cue condition with day and person effects.
- Glyphs: accuracy by code with a confidence interval; confusion matrix; compare with the simulated 40 ms and 70 ms jitter rows.
- Agent: paired comparison over scenarios, with and without the gate; the simulation's numbers are the expected pattern, not a prediction for any model.
- Teaching: learning curve by thirds; the number of questions per avoided disliked action.
- Trust: difference in means with a confidence interval; pre-registered primary outcome.

## 5. Safety

- Every channel command passes `check()`; vibration strength at most 0.6, no thermal module above 4 °C or two minutes.
- The person's stop code is always obeyed at once. The agent never starts a person's program.
- No implant is used or driven. EEG is non-invasive and recorded with consent; raw data stay on the person's device unless they share them.
- A gated agent is a guard rail, not a guarantee: in a shared physical task, the usual robot safety rules apply in full.

## 6. Run it

The pages are `docs/agents.html` and `docs/device.html#channels`; the simulation is `python3 -m rsso.machines --evaluate`. Record results with the contribution form so they join the claims register.
