# THERA and LINX extensions: the copilot and the session tools

Status: built and tested in simulation; effect unproven in people. Implementation: `rsso/rsso/copilot.py` and `docs/js/copilot.js` (identical, tested), on the Therapist page (`docs/therapist.html`, from "The decision matrix and the copilot" down). Simulation results: [`rsso/results/copilot.md`](../rsso/results/copilot.md). Protocol kit: [`kits/COPILOT_PROTOCOL_KIT.md`](kits/COPILOT_PROTOCOL_KIT.md). Roadmap items 8, 12, 13, 14, 16, 17, 20, 40, 41, 47, 50 and 69; claims C4, C18, C19, C21, C31, C44, C45, C57, C64 and C81. Combination X5: one program, two executors.

## 1. Why

THERA gave therapists structured, measured sessions. This step adds the tools around a session: a decision matrix the therapist learns by heart and a copilot that runs the same matrix on the transcript, so that the two can be compared; questions from the level above the problem; Core Transformation and rescripting as guided programs; and the measures between sessions that the design records talk about (overrides, cue-reactivity, OXQ). Every tool reports what it measured and how sure it is, and everything that touches risk goes to the therapist.

## 2. The decision matrix and the copilot (item 14, claim C21)

```
{schema: "rsos-matrix/1", id, center, branches: [{id, cue, words, response, code}] x 3}
```

A central meaning with three trigger cues. Each cue has a word list (an entry ending in `*` matches the start of a word; an entry with a space is a phrase), a response and a vibration code. For each client line the copilot names the branch whose words it hears most, or none; lines with unsafe wording are held for the therapist. The therapist marks what they actually chose. Measured: agreement and Cohen's kappa between copilot and therapist, lines the copilot missed or added, and the therapist's response time.

## 3. Levels and the five-step chain (item 13, claim C19)

A sentence's level (environment, behaviour, skills, beliefs and values, identity, mission) is the highest level whose words it uses. The chain: **detect** the level, **analyse** (work one level above), **modify** (the question for that level), **output** (asked in the client's words; anything a model adds passes the LINX router and CONTAIN), **future-pace**. Unsafe sentences are held. On the built-in set of 48 example sentences, written for the test, the classifier is 85.4% right (kappa 0.83); it is a word-list method, not understanding.

## 4. Typologies as plug-ins (item 12, claim C18)

A plug-in is a set of types with word lists: sensory words (visual, auditory, kinesthetic) and time orientation (past, present, future) are built in. A profile counts each type's words; a type is named only with ten or more type words and a lead over the next type of at least twice the square root of the total. **Profiling another person's speech needs their recorded consent.** Agreement with a questionnaire is Cohen's kappa. The sensory-predicate idea (a "preferred representational system") was not supported in reviews of the research (see [PRIOR_ART.md](PRIOR_ART.md)); the plug-in is here to be tested, not assumed.

## 5. Craving and context triggers (item 8, claims C4 and C31)

Triggers are contexts: an app opening, arriving at a place, a time window. A match offers the craving protocol; the person starts it (the autonomy gate decides anything more). Cue-reactivity is the craving rating at each exposure; its change per month has a 95% interval.

## 6. Core Transformation, rescripting and the life timeline (items 20, 17 and 47; claim C77 from step 2)

- **Core Transformation**: one question at a time from the unwanted state; the chain ends at a core state (peace, wholeness, being, love…) or after seven steps; the chain becomes an RSX program where the core state flows back through each step. Unsafe answers stop the chain for the therapist.
- **Rescripting**: an RSX program that shows the event briefly and from a distance, fills it with the symbol's light, rehearses the new behaviour and future-paces it.
- **The life timeline**: events with year, title, glyph and whether they are recalled as one specific moment; the share recalled specifically is the measure memory specificity training aims to raise.

## 7. Overrides, OXQ and DOL-9 (items 40 and 50; claims C44, C45, C57, C64 and C81)

Each fear, craving or intrusive thought is logged with whether it was turned around and the seconds until the override started (and whether it was just after waking). Measures: overrides a day, the share turned around (overall and month by month), start latency (median, 90th percentile, after waking, share within 4 seconds) and **OXQ**, overrides per waking hour times 100. **DOL-9** is the daily override loop as an RSX program of exactly 90 seconds: posture, five rounds of breath 4-2-6, the phrase, the gesture and a 14-second action.

## 8. Perceptual events (item 41)

An unusual perceptual experience is never a trigger for a cue: it goes to the escalation path, with the advice to note it and contact the clinician. Nothing fires by itself.

## 9. Contexts, the four-day block, the timed burst and the setting (items 16 and 69)

A principle is learned in a four-day block: learn, rehearse, apply in real contexts, test without cues. A context can be recognised from speech ("the meeting starts") and fire a timed burst of the code (three repeats with 400 ms gaps), through the autonomy gate. Each session's setting (warmth, music, imagery) is logged, and the outcome with each factor is compared with the outcome without it.

## 10. Simulation

`python -m rsso.copilot --evaluate` ([copilot.md](../rsso/results/copilot.md)):

- copilot right on 90% of simulated lines; kappa with a therapist of 90% accuracy 0.74, with 60% accuracy 0.55;
- typologies: the right type in 61% of people at 200 words of speech and 98% at 500, no wrong types; with no lean, a type named in 3%;
- cue-reactivity falling one point a month found in 96% within three months (6% false with no change).

## 11. Limits

- Word lists find what they contain and miss paraphrases; a matrix should grow from real sessions.
- The level test set was written for the test; it is not a validation on client speech.
- Real speech is full of everyday words that match type lists ("see you later"); the simulation used clean fillers.
- Delivering Core Transformation and rescripting belongs to trained therapists; the page provides structure and records.
