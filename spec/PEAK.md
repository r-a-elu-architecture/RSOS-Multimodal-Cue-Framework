# PEAK: anchors as measured objects

Status: built and tested in simulation; effect unproven in people. Implementation: `rsso/rsso/peak.py` and `docs/js/peak.js` (identical, tested), camera heart rate in `rsso/rsso/ppg.py` and `docs/js/ppg.js` (identical, tested), page `docs/anchors.html`. Simulation results: [`rsso/results/peak.md`](../rsso/results/peak.md). Protocol kit for real studies: [`kits/PEAK_PROTOCOL_KIT.md`](kits/PEAK_PROTOCOL_KIT.md). Roadmap items 1, 7, 21, 22, 66 and 68.

## 1. Why

An anchor in RSOS (a vibration code, a scent, a light, a phrase, a glyph) is meant to call back a state. Until now the system stored the cue but not whether it works. PEAK makes the anchor a measured object: it is captured at a measured peak, it records the body's response each time it is tested, and it shows whether it is strong, fading or turning against its purpose.

## 2. The anchor object (`rsos-anchor/1`)

| Field | Meaning |
|---|---|
| `id`, `name` | Identity |
| `glyph`, `code` | The glyph and its vibration code (spec/GLYPH_FORMAT.md §7), e.g. 🦁 `..-` |
| `role` | `healing`, `stability`, `redirection` or `lockin`: its place in a chain |
| `channels` | `vibration`, `scent`, `light`, `phrase`, `glyph`; one scent per state |
| `parts` | For a composite, the two anchors it joins |
| `captures` | Moments it was paired with a peak: time, source, body signature |
| `probes` | Probe trials: cue or sham, with heart rate, RMSSD or calm rating before and after |
| `uses` | Times it was fired outside practice, and whether that was during stress |

**Composite anchors.** Two anchors held as one: glyphs joined with `+`, codes joined with a pause (the form of Tier 013, 🦁 + 🐉, code `..- ---`).

## 3. Capture at a peak

| Source | Counts as a peak when |
|---|---|
| Self-tap | Always: the person marks the moment |
| Heart rate variability | RMSSD at least 15% above the person's baseline, and heart rate not more than 10 bpm above baseline (so movement or effort is not mistaken for a peak) |
| EEG | Alpha plus theta power at least 20% above baseline |

The body signature at the moment is stored with the capture.

## 4. Heart rate from the phone camera

A fingertip covers the rear camera with the flash on. Each frame's mean red value dips with every heartbeat. The analysis removes the slow baseline (±0.75 s), smooths over ±2 frames, finds beats (40-180 per minute) with sub-frame timing, rejects intervals more than 25% from the median, and reports heart rate, RMSSD and a quality score. A reading is usable at 70% quality and 8 or more clean beats; RMSSD is used only at 95% quality, because at 30 frames a second it is approximate (see the results). Chrome on Android can turn the flash on from the page; iPhone browsers cannot, so a bright light behind the finger is needed there.

## 5. Probe trials and strength

A **probe** plays the cue alone, with nothing else, and measures the body before and after (30 seconds each with the camera or a strap, or a calm rating from 0 to 10). A **sham probe** plays a code that was never paired with any state. The page decides at random, one probe in three, which kind is played, and does not say which until afterwards.

Each probe's effect is one of: RMSSD change in % (preferred), heart-rate fall in bpm, or calm change; the measure with three or more probes is used. **Strength** is the mean effect of the recent cue probes (up to 8) minus the mean effect of the sham probes (once there are three or more; before that, against zero), with a 95% Welch interval (t distribution). The smallest effect that counts: 5% RMSSD, 2 bpm, or 1 calm point.

| Status | When |
|---|---|
| Building | Fewer than three probes |
| Strong | Interval above zero and effect at or above the smallest that counts |
| Present | Interval above zero, effect below that |
| Weakening | Effect falling probe by probe, and the last three below the earlier ones |
| Contaminated | Interval entirely below zero: the cue now makes things worse than no cue |
| Unclear | None of these |

## 6. Contamination and restoration

An anchor fired while a stressor is present can take on the stressor's meaning (counterconditioning). PEAK flags it when the strength interval is below zero, or the last three probes are clearly negative (high risk), and warns when half or more of its recent uses were during stress while its effect is falling (medium risk). The restoration plan: keep it manual (the autonomy gate, step 3), stop using it during stress, re-pair it in calm at a measured peak together with a resource anchor (optionally as one composite), and count it restored after three positive probes in a row with the interval above zero.

## 7. Chains

Anchors play in role order (healing, stability, redirection, lock-in). `chain_rsx` writes the chain as an RSX program: each anchor a tier with its glyph, channels and code (`TACTON`), each role a phase that activates it, with a check marker. After a played chain, `chain_report` takes a calm rating around each phase and shows which phases worked and which is weakest.

## 8. Simulated body

`SimBody` is a simulated person with known anchor strengths: pairings at peaks raise strength toward a ceiling (Rescorla-Wagner), days without practice let it fade, uses during stress pull it negative. Probes measure RMSSD and heart rate with noise; sham probes measure noise plus a small placebo effect. The random generator is a seeded linear congruential generator with integer arithmetic, so Python and JavaScript produce the same simulated people. `evaluate()` checks how well strength and contamination are recovered; results in `rsso/results/peak.md`.

## 9. What is not claimed

The simulation shows that the machinery recovers known effects. It does not show that anchors work in people: that is what the protocol kit is for. Camera RMSSD is approximate. Claims C2, C10, C11, C12, C15, C24 and C32 of the claims register now have a working test.
