# PERSONLAB — a lab of simulated persons with identity profiles grounded in real stories

Status: registered 2026-11-17 (owner's decision). This file registers the lab's design and steps 1–2 in full. Later steps
are registered here, each before its code. Results are recorded in §9 in separate commits.

## 0. What the lab is

- An autonomous, intelligent agent–person system, extending the existing agent–person design (AGENTS.md). Agents work on
  **simulated persons** toward each simulated person's desired state, and researchers can see and build on the whole
  architecture.
- **No real person is treated.** The simulated persons' identity profiles are built from licensed, public, de-identified
  stories, instead of hand-written models. That replaces the weakness found in BASELINE_AUDIT and STAB_DEFAULT: hand-written
  person models that reward one answer and contain a loophole.
- **Module, not a new language** (owner's decision, 17 November): the lab is the package `rsxv/rsxv/personlab/`. Agents'
  actions stay RSX-V programs. A small RSX-V extension (a `TARGET` line naming the profile node an action serves) is
  registered separately, at step 6.

## 1. Steps

| Step | What | Registered |
|---|---|---|
| 1 | Identity-profile schema (§2) | here |
| 2 | Licence-checked data search (§3) | here |
| 3 | Profile builder: story → profile, two independent readers, agreement measured | before its code |
| 4 | Simulated persons driven by profiles (no open-cue blocking) | before its code |
| 5 | Validation: does each simulated person predict the held-out part of its source better than simple baselines? | before its code |
| 6 | Agents act from current → desired state; compared with "always stabilise" and other simple baselines; RSX-V `TARGET` | before its code |
| 7 | The Person Lab page on the site | before its code |

## 2. Step 1: the identity profile (`rsxv/rsxv/personlab/schema.py`)

- **Levels**, in order from bottom to top. The ids are the ones `copilot.js` already uses:

  | id | name | key question |
  |---|---|---|
  | `environment` | Environment | Where and when? |
  | `behaviour` | Behaviour | What do I do? |
  | `skills` | Capabilities and skills | How do I do it? |
  | `beliefs` | Beliefs and values | Why do I do it? What matters to me? |
  | `identity` | Identity | Who am I? |
  | `mission` | Purpose and mission | For what purpose? Who else? |

  Each level carries its fixed definition (from the owner's brief) and its key question.
- **Tree.** A profile holds one node per level. A level node holds statement sub-nodes ("I am a family member"), and each
  statement holds sub-sub-nodes for where, when and any detail. Every statement and sub-sub-node carries `source`: a
  pointer (document id, character span) to the text it came from. Nothing without a source is valid.
- **States.** `current` and `desired`: for each level, a list of statements, each pointing at the tree node it refers to
  or adding a new one. Also `signals`: what is happening now (stress, behaviour to change), each with its source.
- **Provenance.** Profile-level fields: `source_dataset`, `licence`, `document_id` (a dataset id, never a name), `builder`
  (the step-3 reader and version) and `created`.
- **Validation in code.** `validate(profile)` returns the list of problems: unknown level, missing source, empty statement,
  a desired-state node pointing at a missing node, missing licence. `to_tree(profile)` gives the nested view the site will
  draw.
- **Tests** (`rsxv/tests/test_personlab_schema.py`): a valid hand-made example passes; each problem above is caught; the
  levels and their order match `copilot.js`.

## 3. Step 2: the data search (no download in this step)

A source is **usable** only if it meets all of these:
- Public and downloadable by an official route, with a stated licence that allows research use and redistribution of
  derived aggregates.
- De-identified. No medical or patient records: those are private and cannot legally be downloaded.
- Holds first-person stories or conversations (counselling, support or life narratives) with enough text to fill several
  levels.
- **Has a later part** (later turns, a follow-up, an outcome) that step 5 can hold out for validation.

The search result is a table (`rsxv/rsxv/personlab/SOURCES.md`): name, owner, licence and its link, access route, size,
content, whether it has a later part, and a decision (usable, not usable, or unclear with the reason). It also notes, from
the dataset card, whether the content touches sensitive topics: those stay out of the public repo, by the
existing rules.

## 4. Privacy and publication
- Profiles built from any dataset stay in the workspace or the private repository.
- The public repo holds the schema, code, aggregate results and at most a few hand-written **illustrative** profiles,
  marked as invented.
- Public files keep neutral wording, by the existing rules.


## 5. Step 3: the profile builder (registered 17 November 2026, before any conversation text is read)

**Data.** ESConv, `ESConv.json` from `github.com/thu-coai/Emotional-Support-Conversation` (commit f262d06, 2024-06-19),
SHA-256 aa0556c5…f7efdd9af, licence CC BY-NC 4.0 (the repository's own LICENSE file). Before this registration only field
names and counts were looked at: 1,300 conversations, 1,150 with intensity before and after.

**Sample (fixed now).**
- Four everyday problem types: job, breakup with a partner, problems with friends, academic pressure.
- 25 conversations from each, drawn at random (seed 2026) from those with both intensity ratings.
- The very sensitive types (persistent low mood, alcohol and the small rare types) are left out of the lab.
- A drawn conversation is replaced by the next draw when the existing safety screen (`rsso.safety`, lexical) flags any of
  its seeker turns as `possible_crisis`. Replacements are counted.
- A separate **pilot** of 4 conversations (one per type, seed 2027, none of the 100) tests the instructions first. The
  instructions may be corrected once after the pilot, and are then frozen and committed before the 100 are read.

**What the builder sees.** The pre-chat `situation`, the initial intensity, and the first half of the conversation (all
turns up to and including the seeker's ⌈k/2⌉-th turn, for k seeker turns). **Held out for step 5:** the rest of the
conversation and the final intensity. No reader sees them.

**Two independent readers.** Separate model instances, each given only the frozen instructions
(`rsxv/rsxv/personlab/builder_instructions.md`) and the input text. They write a profile in the step-1 schema. Every item
quotes its span exactly, and the code turns the quote into character offsets. The two readers do not see each other's
output.

**Checks in code.**
- Each profile is validated (step 1). Items whose quote is not found in the input are dropped and counted.
- **Agreement:** for each of the 600 cells (100 profiles × 6 levels), whether each reader put at least one statement
  there. Cohen's kappa over the cells must be at least 0.6; below that, step 3 is "agreement too low" and step 5 waits.
  Also reported: span overlap per level.
- **The final profile** keeps reader A's statements. Each is flagged `agreed` when reader B has a statement at the same
  level whose span overlaps it by at least half of the shorter span. Current and desired states are merged the same way.

**Privacy.** The conversations and profiles stay in the private repository. The public repo gets the code, the
instructions, the counts, the agreement and the per-level coverage.

**Pilot, before the 100 were read.** 4 conversations (ESConv ids 559, 600, 781, 1222). Every quote was found, all 8
profiles are valid, the level-cell agreement is 21 / 24 (kappa 0.727), and 21 of 25 of reader A's statements are matched by
reader B. **The instructions are frozen unchanged** (`builder_instructions.md` as committed in c324fa1).

**Sealed prediction:** P(kappa ≥ 0.6) = 0.55. The environment and behaviour levels are expected to agree best, and mission
worst (people rarely state a purpose in a support chat).

## 6. Step 4: simulated persons driven by profiles (registered 17 November 2026, before its code)

Module `rsxv/rsxv/personlab/person.py`, class `ProfilePerson(profile, params, seed)`.

**Actions.** Five, mapped from ESConv's own supporter-strategy labels, so step 5 can fit them from real conversations.
Each carries the archetype that plays it in the architecture:

| Action | ESConv strategies | Archetype |
|---|---|---|
| `STABILISE` | Affirmation and Reassurance; Reflection of feelings | Bear |
| `EXPLORE` | Question; Restatement or Paraphrasing | Raven |
| `SUGGEST` | Providing Suggestions; Information | Tiger |
| `SHARE` | Self-disclosure | Lion |
| `NONE` | Others | — |

**State.** Intensity I on ESConv's 1–5 scale, starting at the profile's initial intensity. Arousal u in [0, 1], starting at
(I − 1) / 4. Clarity k in [0, 1], starting at 0. Progress g in [0, 1] towards the desired state.

**Targets.** The levels of the desired items that both readers agreed on. Otherwise all desired items. Otherwise the levels
with current items. Otherwise `behaviour`. These are recorded in the person, so the weak desired states (§5) are handled
openly.

**One tick (one supporter turn).**
- A cue arrives with probability ρ: I rises by δ and u by δ/4. **Cues never block one another**, which fixes the
  STAB_DEFAULT loophole.
- The action applies, with parameters per action:
  - relief r_a lowers I;
  - calming m_a lowers u;
  - clarity gain e_a raises k;
  - progress p_a raises g, scaled by (0.5 + k). It applies only when u < τ; at u ≥ τ the action instead raises u by c_a.
- I drifts back towards 1 at rate λ.
- Values are clipped to their ranges.

**Observation.** A feedback score in 1–5: 3 + f1 · (relief this tick) + f2 · (progress this tick) + noise, rounded and
clipped. This is what ESConv records after supporter turns.

**Profile → person, by count only.** No meaning is read beyond step 3. The cue rate is ρ · (1 + 0.25 · the number of
signals, capped at 4). The progress scale is × 1.25 when the profile has a `skills` statement.

**Parameters.** Defaults are neutral placeholders: every action has the same small effects, ρ = 0.1, δ = 0.5, τ = 0.6,
λ = 0.02, f1 = f2 = 1. **Step 5 fits them from ESConv** (development conversations) and tests them on held-out ones. The
structure ("progress only when calm enough") is a hypothesis that step 5's fit can weaken: a fitted τ near 1 removes it.

**Score for step 6.** Per tick: (relief) + (progress), minus 1 when I rises by more than 1 in one tick (a spike).

**Tests.** Same seed gives the same run. Cues keep arriving while earlier ones are unresolved. Each action moves its own
variable in the stated direction. The targets rule. Building all 100 private profiles gives 100 valid persons, and an
aggregate summary of targets is published.

## 8. Amendment, 17 November 2026
Wording only, before any data was downloaded: neutral terms replace three phrases that broke the public-repo wording
rule, and the SOURCES.md path is made exact. No design change.

## 9. Results
(recorded per step, in separate commits)

### Step 1 (code eb39498)
`rsxv/rsxv/personlab/schema.py`: six levels with fixed definitions and key questions (the ids match `copilot.js`), a
statement tree with where, when and detail sub-nodes, a source on every item, current and desired states, signals,
`validate`, `to_tree` and an invented example. 5 tests pass.

### Step 2 (search only; nothing downloaded)
`rsxv/rsxv/personlab/SOURCES.md`. Usable: **ESConv** (primary: multi-turn, with emotion intensity before and after),
**Hippocorpus** (the same writer's retelling 3–6 months later) and EmpatheticDialogues. Not usable: counsel-chat (single
message, unclear licence) and MentalChat16K (partly synthetic). Proposed for step 3: 100 profiles from ESConv, with each
conversation's second half and post-chat intensity held out for step 5.

### Step 3 (code c324fa1; instructions frozen 2d1f9c5; aggregates `rsxv/results/personlab_step3.json`)
- 100 conversations (25 per type; 1 replaced by the safety screen), two independent readers, 8 parallel runs.
- 0 parse errors, 0 invalid profiles, 0 quotes not found.
- **Agreement: kappa 0.728 over 600 level cells (519 agree). The bar of 0.6 is met.** Profiles are stored privately
  (private repository, `dev` branch, `personlab/esconv_v1`, commit bbb3faa).
- Per level (profiles where reader A / reader B placed at least one statement; agreement; kappa):

  | Level | A | B | Agree | Kappa |
  |---|---|---|---|---|
  | environment | 82 | 67 | 77/100 | 0.412 |
  | behaviour | 89 | 89 | 96/100 | 0.796 |
  | skills | 46 | 42 | 86/100 | 0.716 |
  | beliefs | 71 | 69 | 86/100 | 0.667 |
  | identity | 42 | 42 | 82/100 | 0.631 |
  | mission | 14 | 6 | 92/100 | 0.563 |
- 497 statements from reader A, of which 332 (67%) are matched by reader B. Median 5 statements per profile.
- Desired states are the weak part: 64 profiles have one, and 37 of 80 desired items (46%) are matched by reader B.
- The sealed prediction (P = 0.55) was met. Its detail was half right: behaviour agreed best (0.796) and mission was sparse
  (0.563), but **environment agreed worst (0.412)**, not mission. The readers differ on whether a situation line ("my
  school closed") counts as the person's environment.
- For step 4, statements flagged `agreed: false` and the weak desired states are known limits, recorded before step 4 is
  designed.

### Step 4 (code 06fa583; aggregates `rsxv/results/personlab_step4.json`)
- `ProfilePerson` is built from all 100 private profiles. Each person starts at its conversation's own initial intensity.
- Targets: 33 persons from agreed desired items, 31 from any desired item, 36 from current items, 0 from the default.
  Target levels: behaviour 44, environment 30, skills 18, identity 14, beliefs 13, mission 4.
- 46 persons have a skills statement (progress × 1.25). The median number of signals is 2.
- Deviation fixed before the commit: a first draft scaled relief by 4 and progress by 10 inside the code, which the
  registered formula does not say. The code now matches §6 literally (default relief 0.2 per tick).
- 5 tests pass: same seed, same run; cues never block; action directions; the targets rule; the 8 strategies map to the
  5 actions.
- The parameters are still the neutral placeholders. **Nothing about real behaviour is claimed until step 5 fits and tests
  them.**
