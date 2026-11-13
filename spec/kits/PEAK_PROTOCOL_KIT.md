# PEAK protocol kit: do anchors change the body?

A ready protocol for clinicians, labs, universities and companies to test PEAK anchors with real people and instruments. Everything here runs as written; adapt the measures to your instruments. Module specification: [PEAK.md](../PEAK.md).

## 1. Question

Does a cue that was paired with a peak state change heart rate variability when played alone, compared with a sham cue never paired with any state? Secondary: does strength grow with pairings, fade without practice, and turn negative after repeated use during stress (contamination)?

## 2. Design

- **Within-person, randomised, blinded probes.** Each participant has one anchor. After a pairing phase, each probe session plays either the anchor's code (cue) or a sham code, chosen at random (2 cue : 1 sham), with the participant not told which.
- **Pairing phase:** 8 pairings over 8 days, each at a measured peak (HRV at least 15% over the day's baseline, or a self-tap when no sensor is used).
- **Probe phase:** 12 probes over 12 days (8 cue, 4 sham).
- **Optional contamination arm:** after probe 4, half of the participants (randomised) also fire the anchor during mild lab stressors (for example a timed arithmetic task) three times before each later probe.
- **Sample size:** the simulation recognises a strong anchor (about 20% RMSSD change) in nearly every simulated person with 8 cue and 4 sham probes; for a group estimate of a smaller effect, plan from your own pilot.

## 3. Measures

| Measure | Instrument | When |
|---|---|---|
| RMSSD, heart rate | Chest strap (Bluetooth Heart Rate Service) or ECG; the phone camera as a secondary measure | 30 s before and 30 s after each probe |
| Calm rating, 0-10 | Asked on the page | Before and after each probe |
| Peak signature | Same instruments, plus EEG alpha and theta if available | At each pairing |
| Adverse events | Free text and severity | Any time (the Safety page) |
| Covariates | Time of day, posture, breathing rate, caffeine, sleep | Each session |

## 4. Consent wording (adapt to your ethics board)

> You are invited to take part in a study of whether a short vibration pattern, practised together with a calm or confident moment, can later change your heart's rhythm on its own. You will wear a heart-rate sensor and feel short vibration patterns on your wrist or phone. Some patterns are the one you practised and some are not; you will not be told which until the end. There are no known risks beyond mild discomfort from the vibration. You can stop at any moment, and your data is stored without your name. The method is experimental and is not a treatment.

## 5. Data format

One JSON file per participant, `{"schema": "rsos-peak-study/1", "participant": "random id", "anchors": [<rsos-anchor/1>, ...]}`. Anchors carry their captures, probes (with `kind` cue or sham) and uses, exactly as the page stores them. Dates become day numbers before sharing. The research contribution format (spec/DATA_CONTRIBUTION.md) can carry these files.

## 6. Analysis

```
python -m rsso.peak analyze participant.json
```

prints each anchor's strength against sham with its 95% interval, its status and its contamination risk. For a group analysis, pool the per-probe effects (cue minus the participant's sham mean) in a mixed model with participant as a random effect, probe number as a fixed effect (growth), and arm (contamination or not) by probe number as the test of contamination.

## 7. Report template

1. Participants: number, age range, recruitment, exclusions.
2. Instruments and their placement; how peaks were detected.
3. Pairings and probes completed; blinding check (could participants tell cue from sham?).
4. Per-participant strength with intervals (a forest plot).
5. Group effect of cue against sham, with interval.
6. Growth across pairings; fade between sessions.
7. Contamination arm: change in strength after use during stress.
8. Adverse events.
9. What this means for the claims in the claims register (C2, C10, C11, C12, C15, C24, C32).
