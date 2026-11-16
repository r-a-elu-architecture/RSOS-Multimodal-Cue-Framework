# PROFILES — domain profiles

Status: registered 2026-11-16, before code. Code: `rsso/rsso/profiles.py` and `docs/js/profiles.js` (identical
results, tested).

## 1. Purpose

RSOS is used in sport, learning, research (BCI/EEG, haptics, N-of-1 trials), companies, coaching, personal
development and psychotherapy. Each domain has its own professional vocabulary. A profile changes what people
**see**; it never changes what the engine **does**.

## 2. Invariants (what a profile never changes)

1. Thresholds, session states, guidance levels, consent, CONTAIN, the safety engine and every limit.
2. Stored data: keys and values (`sud_before`, `concerns: ["ptsd"]`, …) are the same in every profile. A 0–10
   rating labelled "Tension" is stored exactly as one labelled "Distress".
3. Module outputs (`nodes`, `thera`, `linx`, `contain`, `safety`). Modules keep one internal vocabulary, the
   canonical one, which is what the Clinical profile shows. Profiles translate it at display time only.
4. The clinician-led protocol keeps its name in every profile: acute risk is led by a qualified clinician in any
   domain (spec/CONTAIN.md §10).

## 3. Profiles

| id | Name | For | Highest guidance level | Clinical module | Difficult-memory work |
|---|---|---|---|---|---|
| personal | Personal | Individuals shaping their own state (default) | structured | hidden | offered |
| coaching | Coaching | Coaches, personal-development practitioners | structured | hidden | offered |
| performance | Performance | Sport, music, stage, executives | structured | hidden | offered |
| learning | Learning | Universities, students, mnemonics, languages | structured | hidden | offered |
| research | Research | Labs, BCI/EEG, haptic devices, trials | clinician_led with a study clinician | study enables | offered |
| workplace | Workplace | Companies and teams | structured | hidden | not offered |
| clinical | Clinical | Psychotherapists, psychiatrists, clinics | clinician_led | practitioner enables | offered |

The highest guidance level is shown on the chooser; enforcing it per program is part of Step 2 (Watchdog).
Workplace: employers see aggregates only; no individual data view exists or is added.

Research uses the clinical vocabulary when the clinical module is on (a clinical study), and neutral lab terms
otherwise.

## 4. Vocabulary

Canonical (= Clinical) word → label per profile. Personal / Coaching / Performance / Learning / Research / Workplace.

| Key | Canonical | Personal | Coaching | Performance | Learning | Research | Workplace |
|---|---|---|---|---|---|---|---|
| rating | distress | intensity | intensity | tension | load | intensity | pressure |
| target_state | negative state | state you want to change | state the client wants to change | limiting state | learning block | target state | pressure point |
| memories | trauma (PTSD) | difficult memories | difficult memories | past setbacks | earlier learning experiences | aversive memories | difficult memories |
| low_mood | depression | low energy or mood | low energy or mood | low drive | low motivation | low affect | low energy |
| surges | anxiety, panic | sudden surges | sudden surges | pre-event nerves | exam nerves | acute arousal | pressure spikes |
| ongoing_stress | chronic stress | ongoing stress | ongoing stress | ongoing pressure | ongoing study pressure | chronic stress | ongoing pressure |
| changes | symptoms | what you want to change | what the client wants to change | performance limiters | learning blocks | outcome measures | focus areas |
| person | client, patient | client | client | athlete | learner | participant | team member |
| practitioner | therapist | practitioner | coach | coach | teacher | investigator | facilitator |
| therapy | therapy | guided practice | coaching | coaching | tutoring | guided sessions | facilitated sessions |

Translation is an ordered list of phrase rules (longest first), case-preserving, with article and plural forms.
Validated clinical instruments (PHQ-9, GAD-7, PCL-5) and the conditions list on the contribution page are shown
only with the clinical vocabulary. Research records and architecture pages (results, system, tiers, roadmap,
glyphs, architecture-benchmark, invariance-v14, cue-lab pages) keep their original wording.

## 5. Choosing

A domain selector in every page header; a chooser on the home page; `?profile=<id>` in a link sets and saves it.
Stored as `rsos.profile` (the only key profiles write). Default: personal. The home headline becomes one line for
every profile: "turning the state you have into the state you want".

## 6. Acceptance

- P1 Parity: profiles, terms and translation identical in Python and JS over a fixed corpus (all THERA strings,
  planner and contribution labels, and the visible text of the in-scope pages).
- P2 Vocabulary: for every profile without clinical vocabulary, no translated corpus string contains a clinical
  word (SUD, PTSD, depress*, trauma*, symptom*, distress, panic, anxiety, patient*, therap*).
- P3 Clinical identity: the Clinical profile (and Research with the clinical module on) shows the canonical text
  unchanged.
- P4 Engine untouched: no engine module imports profiles; profiles.js writes only `rsos.profile`.
- P5 Idempotent: translating translated text changes nothing.
- P6 Browser: for each non-clinical profile, the visible text (navigation excluded) of index, player, nodes,
  therapist, contribute, night, safety, world, metrics, anchors, identity, atlas, trials, device and agents has no
  clinical word, after load and after the planner and therapist interactions.
- P7 Safety page: clinical module controls appear only in Clinical and Research; the clinician's resume control
  appears in any profile while the clinician-led protocol is active.
