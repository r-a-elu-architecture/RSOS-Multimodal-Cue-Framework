# Study kit — testing the Override Protocol

For research groups and clinics that want to test the RSOS Override Protocol with consenting adults and share data in one format. Each group needs its own ethics approval. This is not a crisis intervention; follow the exclusions in `spec/OVERRIDE_PROTOCOL.md` §9.

## What to test

The specification lists six hypotheses (§10). The three easiest to start with:

| Hypothesis | Design | Primary outcome |
|---|---|---|
| **H1** — one run lowers distress and raises agency more than a control | Within-person, randomised order: Override Protocol vs paced breathing of the same length | Change in distress (SUD 0–10) and agency (0–10), before → after |
| **H2** — with practice the override becomes faster and more automatic | Single-case multiple-baseline across participants, 4–6 weeks | Latency (s) from noticing a trigger to "I move, I act"; SRBAI weekly |
| **H6** — people, objects and places rehearsed in the futures later bring more agency | Within-person: list rehearsed and comparable unrehearsed elements in advance | Agency (0–10) at each real encounter, by ecological momentary assessment |

## Procedure

1. **Consent and screening.** Exclude acute crisis, active psychosis or mania, severe dissociation. Explain that stopping is always allowed.
2. **Personalisation.** The participant sets their three futures and, optionally, records "I move, I act" and "I own" in their own voice in the [protocol player](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/player.html).
3. **Learning.** A guided first run, then stage A practice (3–5 calm runs a day for one week; spec §5).
4. **Measurement.** Every run is logged by the player (check-in before and after). Weekly SRBAI. For H6, a short in-the-moment rating at each listed encounter.
5. **Export.** The participant exports the run log (CSV) from the player; the study collects it.

## Sample size

`python power.py` writes `power_table.txt`. For a paired effect of d_z = 0.5 (H1, H6), about 34 people give 80% power; for d_z = 0.3, about 90. Effect sizes are unknown, so run a 10–20 person pilot first and re-plan.

## Data to share (de-identified)

- The run log CSV, with columns `timestamp, participant, protocol, trigger, trigger_channel, trigger_note, sud_before, sud_after, agency_before, agency_after, latency_s, completed, stopped_at_phase, tier, voice` (`rsx/README.md`). Replace participant names with codes and remove free text from `trigger_note`.
- The RSX program files used (`.rsx`).
- The pre-registration link.

Never share names, voice recordings, raw EEG/HRV streams or anything that allows re-identification.

## Analysis

- **H1:** mixed model of change score ~ condition + (1 | participant).
- **H2:** latency ~ run number + (run number | participant); visual analysis per case.
- **H6:** agency ~ rehearsed + (1 | participant) + (1 | element).
- **Personalisation (exploratory):** fit `rsos_cue` on the pooled logs (`rsos_cue.runlog`) to see which program, tier and voice work best for which trigger types.
