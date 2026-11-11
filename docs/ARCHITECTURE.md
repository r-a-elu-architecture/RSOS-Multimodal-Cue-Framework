# RSOS system architecture

RSOS is a **research framework** for user-programmed multimodal cues, not a universal therapeutic protocol.

| Layer | Responsibility | Interface |
|---|---|---|
| RSOS | Cue semantics | `user_id`, `context`, glyph/meaning mapping, optional tier label, goal |
| RSIA | Evidence & authorization | Consent, signal quality, context confidence, assumption watchdog, abstention |
| RSX | Typed program graph | Linear or branching operator sequence, no automatic choice at ambiguous branches |
| RSSO | Longitudinal control | Calibration evidence, feedback, scheduling, cooldown, provenance, audit |

## Program semantics

A cue program can span tiers 1–10, tiers 1–20, a different interval, or no tier range. **Tiers are optional program annotations, not measured brain levels.** Glyph names and sensory associations belong to the individual and context in which they were defined.

Representative operators: mnemonic reminder, user-authorized interruption, visual imagery, resource recall, breath prompt, posture suggestion, voluntary swish visualization, grounding, dual-attention prompt and future-situation rehearsal. Optional visual, auditory, tactile, olfactory and gustatory channels are interfaces; smell and taste devices are not implemented as treatment devices.

## Execution and safety

```text
User/context observation -> RSIA permissions + uncertainty checks
  -> RSOS scoped cue lookup
  -> RSX validates a bounded operator DAG
  -> RSSO cooldown + audit
  -> suggest / abstain / manual grounding
  -> collect optional feedback for future calibration
```

No involuntary stimulus dispatch, automatic diagnosis, inference of beliefs from EEG, or clinical claims. See [research topics](RESEARCH_TOPICS.md), [evidence](BENCHMARKS.md), and [source policy](SOURCES_AND_RIGHTS.md).

## Historical architectural source records

The [source-linked architecture directory](../architecture/) provides a navigable technical map of the original [copyright/source estates](../archive/), including original SHA-256 registers, exact file paths, source-layer distinctions, and eight later PASS31B subsystem reconstructions. These are historical design/claim artifacts, not validated neural or therapeutic outcomes. The modern v1.3 software is a separate executable interpretation.
