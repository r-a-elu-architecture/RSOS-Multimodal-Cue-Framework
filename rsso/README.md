# RSSO runtime — devices, sensors, conformance and virtual studies

The operating layer of RSOS (RSSO subsystems **MICRO**, **AUG** and **CONTAIN**), built so that everything can be developed and verified **without hardware or participants**, then used unchanged with real devices and real people.

| Module | What it does |
|---|---|
| `rsso/devices.py` | One `Device` interface for every output (vibration, audio, display, scent). Virtual devices record exactly what they would have done, to the millisecond. A real device implements the same five methods. |
| `rsso/runtime.py` | Plays a compiled RSX timeline on a set of devices, with Stop at any moment, the safety governor and a defence-in-depth intensity clamp. Virtual clock for tests, real-time clock for hardware. |
| `rsso/sensors.py` | A virtual heart-rate strap (beat-to-beat RR intervals, stress responses, activity, slow-breathing effects) and a stress detector (heart rate up + RMSSD down, sustained, motion-gated). |
| `rsso/conformance.py` | The conformance suite: what any runtime and device set must do to be RSOS-compatible. |
| `rsso/protocol.py` | Host side of the [RSOS Device Protocol](../spec/DEVICE_PROTOCOL.md): drives any RDP/1 wristband or scent module; with `SimTransport` it runs the real firmware core ([`firmware/`](../firmware/)) in simulation. |
| `rsso/hrs.py` | Bluetooth Heart Rate Service driver (the standard every chest strap and most watches use): parses Heart Rate Measurement packets into beat-to-beat intervals. The player has the same driver in JavaScript (`docs/js/hrs.js`). |
| `rsso/memstack.py` | MEMSTACK: per-tier memory from the run log and weekly automaticity checks: runs, effect over time, bundle strength (model estimate), fitted habit curve, estimated triggers until a 3-second start, and the reflex criterion; checksummed snapshots with restore and merge. The player shows the same summary (`docs/js/memstack.js`), computed identically. |
| `rsso/ugcl.py`, `rsso/ugcl_originals.py`, `rsso/ugcl_library.py`, `rsso/calibration.py` | UGCL glyph layer ([format](../spec/GLYPH_FORMAT.md)): the 146 original glyphs of the tier ledger with image, rhythm, melody and ancestry (`python -m rsso.ugcl_originals`); stroke glyphs with image, rhythm, melody and compact code from one description, and an optional generated library of 48 (`python -m rsso.ugcl_library`); Bradley–Terry personal calibration from pairwise choices. Identical to `docs/js/ugcl.js`. |
| `rsso/ledger.py`, `rsso/ledger_map.py`, `rsso/metrics.py` | The tier ledger as lossless structured data; where every tier lives in the architecture; the metric registry and the operational metrics computed from the run log (identical to `docs/js/metrics.js`). See [the tier ledger in the architecture](../spec/TIER_LEDGER.md). |
| `rsso/consent.py` | Consented programming: cues a person or their therapist chooses to install, each with a consent record; programs with a cue are refused without valid consent; every cue can be listed and revoked. Identical to `docs/js/consent.js`. |
| `rsso/nodes.py` | Node planner ([spec](../spec/NODES.md)): from symptoms, triggers and desired states, nodes — a state held as one unit with cues on every sense, a vibration code, a glyph, a mode (associated or observer) and the mental frame — with a frame check, an RSX program per node, ledger tiers, metrics, dose and safety; per-sense opening from the run log. Identical to `docs/js/nodes.js`; the node studio is `docs/nodes.html`. |
| `rsso/contribution.py` | Research data contribution ([spec](../spec/DATA_CONTRIBUTION.md)): one de-identified, checksummed file per person, clinician or lab, filtered by consent scopes; `check` and `pool` from the command line; contributions back to run-log rows; BIDS events for any RSX program. Identical to `docs/js/contribution.js`; the page is `docs/contribute.html`. |
| `rsso/linx.py` | LINX, the AI layer ([spec](../spec/LINX.md)): plain language and conversation to the node intake, frame suggestions, the prompt for any language model, the containment router for model proposals, and node offers when the body, the brain or a context signals a negative state. Identical to `docs/js/linx.js`. |
| `rsso/contain.py` | CONTAIN, the safety layer ([spec](../spec/CONTAIN.md)): the device safety envelope, drift detection and quarantine, escalation, the decide() gate every module asks, restore and rollback; `play(..., contain=state)` refuses what it blocks. Identical to `docs/js/contain.js`; the page is `docs/safety.html`. |
| `rsso/thera.py` | THERA, therapist mode ([spec](../spec/THERA.md)): five measured session protocols as data (`python -m rsso.thera` writes `docs/data/thera.json`), sessions filled with the client's own nodes, stop rules, summary with fidelity and clinician ratings, the session as a research record, and practice between sessions. Identical to `docs/js/thera.js`; the page is `docs/therapist.html`. |
| `rsso/cm1.py` | CM1, the compression layer ([spec](../spec/CM1.md)): practice signatures, response profiles, assignment and where to start, patterns across everyone, and a compact device bundle; checked on a synthetic population with known profiles (`python -m rsso.cm1` writes `docs/data/cm1.json` and [results](results/cm1.md)). Identical to `docs/js/cm1.js`. |
| `rsso/peak.py` | PEAK, anchors as measured objects ([spec](../spec/PEAK.md)): capture at a peak, blind probe trials against sham, strength with a 95% interval, contamination and restoration, chains and their RSX program, and a seeded simulated body (`python -m rsso.peak --evaluate` writes [results](results/peak.md); `python -m rsso.peak analyze file.json` for real data). Identical to `docs/js/peak.js`. |
| `rsso/ppg.py` | Heart rate and RMSSD from a fingertip over the phone camera, with a quality score. Identical to `docs/js/ppg.js`. |
| `rsso/trial.py` | TRIAL, personal randomised trials ([spec](../spec/TRIAL.md)): designs, permuted-block schedules, analysis with intervals, permutation p-values and adjustment, pooling across people, consistency, simulated people (`python -m rsso.trial --evaluate` writes [results](results/trial.md); `python -m rsso.trial analyze file.json` for real data). Identical to `docs/js/trial.js`. |
| `rsso/checks.py` | CHECKS, built-in cognitive tests ([spec](../spec/CHECKS.md)): seeded task sequences and scoring for 2-back, digit span, reaction time, word recall, reading and dot-probe. Identical to `docs/js/checks.js`. |
| `rsso/gate.py` | The autonomy gate, part of CONTAIN ([spec](../spec/GATE.md)): stages per anchor (manual, suggest, automatic, under pressure) earned from PEAK evidence, offers and wear-out, closing again when evidence weakens; consent records, flags for anything below awareness, and the audit log of automatic decisions (`python -m rsso.gate --evaluate` writes [results](results/gate.md)). Identical to `docs/js/gate.js`. |
| `rsso/identity.py` | IDENTITY, identity profiles level by level ([spec](../spec/IDENTITY.md)): a symbol and login code over seven levels with images and codes, environment, language, versions, coherence and its trend, drift while mirroring others, generalisation, anchor-tree recall walks, value-conflict rehearsals, switching, programs (day, night, four steps, the prepared week, dose) and a library (`python -m rsso.identity --evaluate` writes [results](results/identity.md)). Identical to `docs/js/identity.js`. |
| `rsso/atlas.py` | ATLAS, the trigger atlas and the transfer engine ([spec](../spec/ATLAS.md)): weights for every node and combination by least squares over sampled moments, readiness, leave-one-out prediction, rerouting through the autonomy gate, transfer to untreated triggers against a repeat mapping, the level sweep and the glyph route (`python -m rsso.atlas --evaluate` writes [results](results/atlas.md)). Identical to `docs/js/atlas.js`. |
| `rsso/night.py` | SLEEP and REWARD ([spec](../spec/NIGHT.md)): the night plan (trauma-related codes held back), the closed-loop sleep-cue controller with a simulated sleeper and night report, next-day recall for cued against uncued items, the night diary, nightmare responses, reward codes and families, recognising a good move from an accelerometer, and the notice test (`python -m rsso.night --evaluate` writes [results](results/night.md)). Identical to `docs/js/night.js`. |
| `rsso/copilot.py` | THERA and LINX extensions ([spec](../spec/COPILOT.md)): the decision matrix and the copilot with agreement, levels and the five-step chain, typology plug-ins with consent, craving context triggers and cue-reactivity, Core Transformation, rescripting, the life timeline, overrides with OXQ and DOL-9, perceptual events routed to escalation, speech contexts, the four-day block, the timed burst and the setting (`python -m rsso.copilot --evaluate` writes [results](results/copilot.md)). Identical to `docs/js/copilot.js`. |
| `rsso/machines.py` | More channels and agents ([spec](../spec/MACHINES.md)): RDP/1.1 draft lines for temperature, images and vibration with carrier, rhythm and body site, with an extended envelope; posture with hysteresis; codes spread over body sites; an agent profile whose values gate every action (override, ask, allow), the person's error signal and answers, the alignment log; agent-state codes and replies with pulse coding; content packs as matrices and values (`python -m rsso.machines --evaluate` writes [results](results/machines.md); `--channels` runs checks X1-X11 on the firmware core: [results](results/channels_firmware.md)). Identical to `docs/js/machines.js`. |
| `rsso/pron.py` | Pronunciation feedback ([spec](../spec/MACHINES.md#10-pronunciation-item-10-claim-c14)): pitch, spectral envelope and syllables at 8 kHz; melody, vowels and rhythm compared syllable by syllable with the speaker's own voice, vocal tract and speed taken out; mouth shape per vowel from the camera; synthesised drills and simulated learners (`python -m rsso.pron --evaluate` writes [results](results/pron.md)). Identical to `docs/js/pron.js`. |
| `rsso/ssep.py` | The EEG test for claim C35 ([spec](../spec/MACHINES.md#11-the-eeg-test-for-claim-c35)): the response at a vibration rhythm, vibration against a sham with phase so the motor's electrical pickup cancels; permutation tests per person, pooled z per group (`python -m rsso.ssep --evaluate` writes [results](results/ssep.md)). |
| `rsso/board.py` | Board kit check ([kit](../firmware/BOARD_KIT.md)): B1–B7 on a real wristband over USB serial (`python -m rsso.board --port …`), the whole conformance suite in real time (`--full`), or the firmware core in real time without a board (`--sim`). The browser version is `docs/js/rdp.js` on the Wristband page (tested to match). |
| `rsso/eeg.py` | EEG input: one stream interface with replay, synthetic and Lab Streaming Layer sources (Muse, OpenBCI, Emotiv via LSL), band powers and an arousal detector. |
| `rsso/participants.py`, `rsso/study.py` | Virtual participants who live with RSOS for weeks, and synthetic studies that write files in the same format as real studies. |
| `rsso/analysis.py` | Pre-specified analyses for H1, H2 and H5. The same code runs on synthetic and on real data. |

```bash
cd rsso
python -m unittest discover -s tests                     # 182 tests
python -m rsso.conformance                               # conformance report for the virtual rig
python -m rsso.conformance --firmware                    # the same checks on the C++ firmware core
python -m rsso.study long --people 40 --out out/long     # a synthetic 4-week study
python -m rsso.analysis out/long/runs.csv --triggers out/long/triggers.csv --srbai out/long/srbai.csv
python -m rsso.study power --out out                     # H1 power by simulation
```

Requires Python 3.10+, NumPy, SciPy and pandas, and the `rsx` package in this repository.

## Conformance

**15/15 checks pass** on the virtual rig ([report](results/conformance_virtual_rig.md)) and on the C++ firmware core running in the host simulator ([report](results/conformance_firmware.md)).

| Check | Requirement |
|---|---|
| C1 | Every event dispatched within 10 ms of its time |
| C2 | Output ends within 100 ms of Stop, in every phase |
| C3 | No device output after Stop |
| C4 | Haptic intensity never exceeds the program's limit, even if the timeline was tampered with |
| C5 | No device-triggered run without opt-in |
| C6 | Refractory period and hourly limit enforced |
| C7 | No scent or taste released before the person confirms no allergy or aversion |
| C8 | Every output channel in the program has a device |
| C9 | A self-initiated run is always allowed |
| C10 | "I move, I act" spoken exactly once, then "I own" once |
| C11 | A run that is not stopped completes |
| C12 | No programmed cue runs without a consent record naming its content; therapist-led tiers also need a therapist present and the screening passed |
| C13 | The person can list every programmed cue and revoke any of them; a revoked cue never runs |
| C14 | A program outside the device safety envelope never starts; programs inside it run (CONTAIN) |
| C15 | A program that makes distress worse is paused and never starts until the person (or their therapist) restores it (CONTAIN) |

The suite is tested against deliberately faulty devices (one that keeps vibrating after Stop, one that over-drives the motor) to make sure the checks catch them. On the development machine, the real-time clock dispatched a full Override Protocol run with 0 ms maximum lateness and stopped in 0 ms.

**To certify your own hardware:** write a factory that returns your devices and run `conformance.run_suite(factory, clock_factory=RealTimeClock)`.

## Heart-rate trigger

The player connects to any Bluetooth heart-rate strap or watch that broadcasts the standard Heart Rate Service (Chrome or Edge; Android, Windows, macOS, Linux), runs the stress detector on the beat-to-beat intervals, and, if the person has opted in, offers the override within the run limits. A simulated strap is built in for trying it without hardware. The Python and JavaScript parsers give identical results on the same packets, and the two detectors give identical detection times on the same recording.

## Virtual heart-rate strap and detector

20 virtual people, 4 hours each, 6 stress events and 4 activity bouts per person ([data](results/detector_virtual_strap.csv)):

| Detector | Stress events detected | Median latency | False alarms per hour |
|---|---:|---:|---:|
| Heart rate + HRV | 85% | 39 s | 1.74 |
| Heart rate + HRV, ignoring periods with motion | 80% | 35 s | 0.10 |

Physical activity raises heart rate and lowers HRV just as stress does, so motion gating (from the watch or strap's accelerometer) is what keeps false alarms low. These figures depend on the strap model's assumptions; a real strap must be checked against real recordings.

## Synthetic studies

All effect sizes are **assumptions** set in `StudyConfig` (for example, one override run is assumed to lower distress by 2 points when the bundle is fully learned, and paced breathing by 1 point). The studies show that the design, the data flow and the analysis work, and what sample sizes are needed **if** effects are that size. They do not show that the protocol helps anyone.

- [H1 crossover](results/h1/report.md): 40 virtual participants, override vs paced breathing. The analysis recovers the assumed extra drop of 1.0 point (95% CI 0.80–1.21).
- [4-week study](results/long/report.md): practice makes the override faster (median latency 62 s in the first runs, 10 s in the last) and more automatic (SRBAI +1.65 points); device triggering raises the share of triggers followed by a run from 71% to 92%.
- **H1 power** ([table](results/h1_power.csv)), 12 runs per person:

| Assumed extra distress drop vs paced breathing | 10 people | 20 | 40 | 80 |
|---|---:|---:|---:|---:|
| 0.25 points | 13% | 28% | 46% | 79% |
| 0.5 points | 53% | 77% | 99% | 100% |
| 1.0 point | 95% | 100% | 100% | 100% |

## EEG

`SyntheticEEG` events suppress alpha and raise beta; the arousal detector, which compares the beta/alpha ratio with the person's own recent baseline, found both events in a 15-minute synthetic recording about 8 s after onset and none in a recording without events. Real EEG changes with arousal differ a lot between people and headsets, so the detector must be calibrated per person.

## Using it with real people and devices

1. Run the conformance suite on your hardware.
2. Collect run logs with the protocol player or `rsx.RunRecord`; for device-triggering studies, also log every detected or reported trigger in the `triggers.csv` format written by `rsso.study`.
3. Analyse with `python -m rsso.analysis`. For the final analysis of a real study, mixed-effects models are recommended in addition.
