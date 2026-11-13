# SLEEP and REWARD: cueing during sleep and reward codes

Status: built and tested in simulation; effect unproven in people. Implementation: `rsso/rsso/night.py` and `docs/js/night.js` (identical, tested), page `docs/night.html`. Simulation results: [`rsso/results/night.md`](../rsso/results/night.md). Protocol kit: [`kits/NIGHT_PROTOCOL_KIT.md`](kits/NIGHT_PROTOCOL_KIT.md). Roadmap items 2, 3, 6, 18 (merged into 2) and 28; claims C5, C7, C8, C9, C28, C33 and C36. Combination X2: one conditioning loop around the clock.

## 1. Why

What is practised by day can be strengthened at night: sounds or smells linked to learning and replayed in slow-wave sleep improve later memory (targeted memory reactivation). RSOS replays the day's vibration codes, with dim light and an earbud voice if chosen. The same code can also mark a success at the moment it happens, by day, and return at night. Both are powerful and both can backfire: a cue that wakes the sleeper costs sleep, and a trauma-related cue replayed in sleep could do harm. The module is built around those risks.

## 2. The night plan

```
{schema: "rsos-night/1", codes: [{code, label, area}], held: [...], channels: ["vibration", "light", "voice"],
 trauma: "safety" | "wake", safety_code, limit, max_intensity, say}
```

Codes the person marks as linked to a painful memory go to `held` and are **never played during sleep**. A detected nightmare gets the separate safety code or a gentle waking (the person chooses). The plan needs consent to night cueing on the Safety page and is flagged "Plays while you sleep".

## 3. The closed-loop controller (item 2)

The controller sees only what a device sees: the estimated stage of each 30-second epoch and whether an arousal was detected. It cues when:

- the device has read deep sleep (N3) for three epochs in a row (90 seconds);
- no arousal or waking was seen in the last five minutes;
- the nightly limit (300 cues) is not reached.

Intensity starts at 0.3 of the waking level, falls by 30% after every arousal, rises by 0.02 after every 20 quiet cues, and never exceeds the plan's maximum (0.6 by default, at most 0.9). Codes rotate through the plan. Random cueing (a cue in a quarter of all epochs at the maximum) is built in as the comparison.

## 4. Measures

| Measure | What | Claims |
|---|---|---|
| Night report | Cues by stage, share in deep sleep, cues that woke the sleeper, deep sleep, time awake after sleep onset | C36 |
| Next-day recall | Items learned in the evening are split; half are cued. Retention of cued minus uncued items, over nights, with a 95% interval | C7, C8 |
| Night diary | Bad dreams and their distress on cueing nights against nights without | C5, C33 |
| Notice test | Vibration alone against vibration with a flash of light: share noticed and time to notice | C28 |
| Reward log | Successes, rewards, those held back by the limits, time from success to code | C9 |

## 5. Reward codes (items 3, 6 and 28)

- **Families**: each learning area has a prefix (for example `-.`); its codes are the prefix and a distinct suffix (`-. .`, `-. -`, …). Prefixes must differ and none may start another, so the body knows the area from the first pulses.
- **Events**: an outside sensor (a rim sensor, a quiz, a motion sensor) or the person reports a success; the area's code plays at once, unless a reward played in the last 1.5 seconds or 20 in the last minute. The aim is under 300 ms from the success to the code.
- **Recognising a good move**: from accelerometer magnitude, a peak that stays the largest for 150 ms; the 600 ms ending 150 ms after it is compared with the shape of a good move (wind-up, release, follow-through); a correlation of 0.85 or more is a success. The decision comes 150 ms after the release.
- **Night replay**: the area's reward code can join the night plan.

## 6. Simulation

`python -m rsso.night --evaluate`, 60 simulated people per row ([night.md](../rsso/results/night.md)):

- closed loop: 99% of cues in deep sleep, under one cue-caused arousal a night, almost no lost sleep; random times at the allowed strength: 16% in deep sleep, about 15 arousals a night (claim C36);
- in the memory model, a benefit is found in 15% of single people over seven nights but in all groups of 20; with random cueing the same benefit turns into a loss;
- nightmares: the safety code shortened nightmare time from 2.8 to 0.6 minutes, waking to 0.1;
- a good move was recognised in 90% of good moves and 0% of poor ones, the code starting about 190 ms after the release;
- reward codes (4 points) and night replay (2 points) in a 2 x 2 study: with 80 athletes the reward effect is found in 63% of studies and the replay effect in 25%.

The simulation's memory and training effects are assumptions chosen to test the analysis, not findings.

## 7. Limits

- Finding deep sleep needs a device that reads sleep stages (an EEG headband or similar); a phone on the mattress cannot. The page plans and simulates; the device runs the plan.
- Published targeted memory reactivation used sounds and smells; whether vibration works the same way is open (C8). Reactivation was not effective in REM in the meta-analysis, which bears on C23.
- Night cueing in people with trauma belongs with a therapist; RSOS never replays trauma-related codes.
- In the page, the time from success to code is measured from the tap to the start of the code, plus an assumed 40 ms for the device.
