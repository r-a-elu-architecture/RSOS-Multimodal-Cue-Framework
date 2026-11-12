# LINX — the AI interface and routing layer

Status: built and tested. `rsso/rsso/linx.py` and `docs/js/linx.js` give identical results (tested). The node
studio (`docs/nodes.html`) and the player (`docs/player.html`) use it.

## 1. Role, as recovered from the archive

The archive (`LINX_Historical_Reconstruction.txt`) names LINX as the layer between RSOS and language models,
"symbolic layer injection", "GPT interface for compressed override injection", "GPT routing system" and, later,
"GPT interface + containment router". It has three operators:

- injection of the tier state;
- routing of what the model returns;
- containment, so that nothing from a model reaches a person unchecked.

The archive recovers no executable algorithm for any of them (its "negative space"). This specification is that
algorithm. Each operator is built so that it works with no model at all, and with any model.

| Operator (archive) | Built as |
|---|---|
| Human intent to structured instruction | `understand(text)` and `converse(state, text)`: plain language to the intake of the node planner |
| Tier-recursion and state injection | `model_prompt(ctx)`: everything a model needs about the person's system, plus the reply schema |
| Containment router | `route(proposal, intake)`: a model's proposal is checked field by field; only what passes is applied |
| Compressed override injection | `offer(event, plan, runs, gov, now)`: which node to offer when the body, the brain or a context signals a negative state |
| (new) Frame improvement | `suggest_frames(text, mode)`: rewrites that score higher on the frame check |

**Principle.** LINX only proposes. The planner builds the plan, the person (or the person with their therapist)
approves it, and the person starts every run. The router enforces this: any field that would start, run, play or
fire something is rejected.

## 2. Understanding plain language

`understand(text)` returns `{concerns, nodes[], triggers[], physiology, dose, author}`. It uses deterministic
matching rules and makes no guesses beyond them.

| What | Matched by |
|---|---|
| Concerns | Word stems: trauma or flashback → `ptsd`; burnout → `chronic_stress`; scroll or social media → `habits`; boundaries or saying no → `confidence`; and so on |
| Symbols | The archetypes (lion, raven, eagle, leopard, tiger, bear, dragon); the observer ("no ego", "nothing binds", "detached"); 20 symbols of your own ("like a phoenix", "my wolf") |
| Desired state | "I want to feel X", "she wants to be X", "I want X" |
| Frames | Quoted sentences; "my frame is …", "I tell myself …" |
| Senses | "the smell of …" → O; "the taste of …" → G; "the sound of …" or "listening to …" → A; "golden light" or "the colour of …" → V; "a feeling of …" → K |
| Contexts | "at work", "in meetings", "before sleep", "while driving", and similar |
| Triggers | "when …", "whenever …", "every time …" |
| Body and dose | "resting heart rate 72", "HRV 35", "50 times a day", "for 4 days" |
| Author | "my client" or "my patient" → therapist |

Details are attached to the symbol named in the same sentence. Details said before any symbol go to the first
symbol named.

## 3. The conversation

`converse(state, text)` asks one question at a time for whatever is still missing, in this order:

1. what is happening;
2. the symbol;
3. the state (skipped for archetypes, which carry one);
4. the frame;
5. the senses;
6. where the node will be used;
7. the triggers.

An answer that the rules cannot place fills the slot that was asked about. For example, an answer to the frame
question becomes the frame. Answers to the senses question are split item by item ("golden light, the sound of
waves, cedar" → V, A, O). "Skip" or "no" moves to the next question. In the node studio the conversation works
on the form itself, so typing and talking can be mixed.

## 4. Frame suggestions

`suggest_frames(text, mode)` returns up to three rewrites that score higher on the frame check (spec/NODES.md §2):

- negation becomes the opposite state ("I will not be afraid" → "I am calm and I breathe fully");
- narrowing words go ("only", "just", "try to");
- the future becomes the present;
- "I am good at seeing things" becomes "I see broadly and clearly";
- trait-only frames gain a process ("…, and I breathe fully and completely");
- neutral frames gain breadth.

A rewrite that still contains a negation or the future is never offered. In the node studio each suggestion is
a button that replaces the frame.

## 5. Any language model: injection and routing

`model_prompt(ctx)` writes the prompt for any language model. It contains:

- what RSOS is and the rules (propose only, no diagnosis, frames that are present-tense, process-based, broad and believable);
- the person's concerns, triggers and nodes (state, frames, cues, contexts);
- the ledger tiers in use;
- the practice summary (mean change in distress per program);
- the reply schema.

The model replies with JSON in the format `rsos-linx-proposal/1`:

```json
{"schema": "rsos-linx-proposal/1",
 "nodes": [{"ref": 0, "frames": ["…"], "O": "…", "contexts": ["…"]}, {"archetype": "RAVEN", "state": "…"}],
 "concerns": ["stress"], "triggers": ["…"], "notes_for_therapist": ["…"]}
```

`route(proposal, intake)` applies only what passes. The following are rejected, each with a reason:

- an unknown field;
- any field that would act (`start`, `run`, `play`, `fire`, `*_now`);
- an unknown archetype, mode or concern;
- a reference to a node that does not exist;
- text over its length limit (frames 120 characters, cues 80, other text 160, notes 240);
- unsafe wording (self-harm, violence, self-hatred), which is held back for the person and their therapist;
- any frame scoring below 70 on the frame check, or containing a negation.

What passes is merged into the intake. The planner then rebuilds the plan, and the person reads and approves it.
In the node studio: "Copy the prompt for an AI model", then "Paste the AI's reply", then "Check and apply". The
page shows what was applied, what was held back and why, and the notes for the therapist.

No API key and no model provider is built in. The prompt works with any model the person or clinic chooses, and
everything the model returns passes through the router.

## 6. Offering a node at the right moment

`offer(event, plan, runs, gov, now)` receives an event `{source: hr | eeg | context | memory, text}`.

- It requires an approved plan.
- It applies the safety limits (90 s between runs, 6 device offers an hour, 20 a day).
- It scores each node:
  - +2 per word of the event that matches the node's contexts;
  - +1 for an associated node when the event matches a known trigger;
  - +3 for the observer when the event is a memory;
  - +1 for associated nodes when the heart rate or EEG signals stress;
  - up to ±2 from the node's own history (mean change in distress, from 3 or more rated runs).
- It returns the node and the reasons.

In the player, when the heart-rate detector signals stress and the person has opted in, the offer names that
node and why ("Start your Lion node? (the body signals stress; it lowered your distress by 4.2 on average)"). The
person starts it or dismisses it.

## 7. Next

- A live connection to a model chosen by the person or clinic, through the same prompt and router.
- Offers from EEG (AUG) and from context sources such as calendar or location, with consent.
- Learning which phrasings of frames work best from pooled contributions (spec/DATA_CONTRIBUTION.md, `texts` scope).
