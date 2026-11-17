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

## 8. Amendment, 17 November 2026
Wording only, before any data was downloaded: neutral terms replace three phrases that broke the public-repo wording
rule, and the SOURCES.md path is made exact. No design change.

## 9. Results
(recorded per step, in separate commits)
