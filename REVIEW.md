# Review package

This file is for an independent reviewer: an engineer, a clinician, a researcher, or a security or privacy
specialist. It says what RSOS is, how to reproduce every result in an hour, what is claimed and what is not,
what is known to be weak, and what to look at. Findings can be sent with the template in
[`review/REPORT_TEMPLATE.md`](review/REPORT_TEMPLATE.md).

## 1. What RSOS is, in one paragraph

RSOS is an open system for changing a state on purpose, such as distress becoming calm agency, through short
practised routines. A routine combines breath, words, imagery, sound, vibration, scent and taste, and is meant to
become a reflex. It consists of:

- **RSX:** a language for those routines, with compilers in Python and JavaScript.
- **RSSO:** the operating layer that plays them on devices, with safety, memory and AI layers.
- **A firmware core** and an RDP/1 device protocol for a wristband.
- **A website** with a player, a node studio, a therapist mode, a research-contribution page, a safety page and a
  wristband page.

It grew out of a long design record, the tier ledger, which is kept unchanged in `archive/` and integrated, tier
by tier, in `spec/TIER_LEDGER.md`.

## 2. A ten-minute tour

| Look at | Where |
|---|---|
| The idea and the protocol | [Home page](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/), [`spec/OVERRIDE_PROTOCOL.md`](spec/OVERRIDE_PROTOCOL.md) |
| How the parts connect | [System map](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/system.html), [`architecture/`](architecture/) |
| Using it | [Player](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/player.html), [Node studio](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/nodes.html), [Therapist mode](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/therapist.html) |
| Safety | [Safety page](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/safety.html), [`spec/CONTAIN.md`](spec/CONTAIN.md) |
| Data | [Contribute](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/contribute.html), [`spec/DATA_CONTRIBUTION.md`](spec/DATA_CONTRIBUTION.md) |
| Hardware | [Phones and wristbands](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/device.html), [`firmware/BOARD_KIT.md`](firmware/BOARD_KIT.md), [`spec/DEVICE_PROTOCOL.md`](spec/DEVICE_PROTOCOL.md) |

## 3. Reproduce everything

```bash
git clone https://github.com/r-a-elu-architecture/RSOS-Multimodal-Cue-Framework
cd RSOS-Multimodal-Cue-Framework
pip install -r requirements.txt          # Python 3.10+; Node.js 18+ and a C++ compiler are also needed
./scripts/check_all.sh                   # about 1 minute
```

The script runs:

- the RSX, RSSO and toolkit test suites (189 tests);
- the conformance suite on the virtual rig and on the firmware core;
- the board check against the firmware core in real time;
- a regeneration of every generated file, checking that nothing changed.

The same script runs on GitHub on every push (`.github/workflows/checks.yml`).

Wherever a module exists in both languages, Python and JavaScript are tested to give identical results. This
covers 19 modules: the RSX compiler, memory, glyphs, metrics, consent, nodes, LINX, CONTAIN, THERA, CM1, PEAK, TRIAL, CHECKS, the autonomy gate, IDENTITY, the
contribution format, the device protocol with its board check, the heart-rate driver and camera heart rate.

## 4. Evidence register: every number, and what kind of evidence it is

| Claim | Value | Kind | Source |
|---|---|---|---|
| Tier ledger read losslessly | 293 records, byte-identical when rebuilt | Measured on the archive | `rsso/rsso/ledger.py`, tests |
| Conformance suite | 15/15 on the virtual rig and on the C++ firmware core | Software in the loop | `rsso/results/conformance_*.md` |
| Board check B1–B7, then C1–C15 over the serial transport in real time | 22/22 against the firmware core | Software in the loop (no board yet) | `rsso/results/board_check_sim_realtime.md` |
| Device Stop | Within 100 ms (protocol); 0 ms in simulation | Simulation | C2, B4 |
| Heart-rate stress detector | 80% of stress events, 0.10 false alarms an hour with motion gating | Synthetic: virtual strap model | `rsso/results/detector_summary.txt` |
| EEG arousal detector | 2 of 2 events, none false | Synthetic signal | `rsso/rsso/eeg.py`, tests |
| Cue engine | 60% (10 runs) and 78% (20 runs) lower regret than the best fixed setting | Synthetic population | `toolkit/VALIDATION.md` |
| CM1 profiles | Right profile from 10 runs: 100% (clear), 96% (hard) | Synthetic population with known profiles | `rsso/results/cm1.md` |
| PEAK anchors | With 8 cue and 4 sham probes: strong anchors found 100%, no-effect anchors called an effect 0%, contaminated anchors flagged 100%, false flags 0.7% | Simulated people with known anchor strengths | `rsso/results/peak.md` |
| Camera heart rate | Heart rate within 1 bpm on clean synthetic fingertip signals; RMSSD approximate at 30 frames a second | Synthetic signals with known beats | `rsso/results/peak.md` |
| TRIAL | Personal effect of 1.5 points found in 42% (8 blocks) and 63.5% (12 blocks) of simulated people; false claims 3% and 4.5%; 30 people pooled to 1.14 [0.74, 1.54] for a true 1.0 | Simulated people with known effects | `rsso/results/trial.md` |
| Autonomy gate | Strong anchors automatic in 100% of simulated people (about day 11); no-effect anchors never fire by themselves (180 firings without the gate); contaminated anchors lose automatic use within a day in 75%, 0% automatic at day 60 | Simulated people with known anchors | `rsso/results/gate.md` |
| IDENTITY | Coherence rising 1 point a month found in 100% of simulated people over 26 weeks (2.5–3% false); drift found in 100% (2% false); tree advantage found faster in 99.5% after 12 walks (3% false); value conflict detected in 98.5% by chest strap, 81% by camera | Simulated people with known answers | `rsso/results/identity.md` |
| Original glyphs | 146 + 1 joined pair; 147 unique vibration codes | Measured on the ledger | `rsso/results/ugcl_originals.md` |
| Effect of the Override Protocol or nodes on people | **None measured** | — | Study kit ready: `toolkit/study_kit/` |

The tier ledger's own metric values (for example "Containment Reflex Integrity") are historical records of what
was claimed during design. They are kept and labelled as records, and are never presented as measurements
(metrics page).

## 5. Known limits and open findings (internal pre-review)

These are findings from my own review of the repository. An outside reviewer should confirm, extend or overturn
them.

| # | Area | Finding | Severity | Status |
|---|---|---|---|---|
| F1 | Security | The wristband's Bluetooth link (Nordic UART) is unauthenticated, so anyone in range can connect and send commands. The firmware's own limits bound the damage: motor capped at 0.6, releases capped at 3 s, scent off without consent, Stop always works. Pairing and bonding are still missing. | High for wearables | Open: enable BLE bonding with a passkey |
| F2 | Privacy | Run logs, node plans, screening answers and therapist session data live unencrypted in the browser's local storage on the person's device. | Medium | Open: optional passphrase-encrypted storage and exports |
| F3 | Privacy | Contributions are de-identified by construction (day numbers, bands, random ids, no free text by default), but in small studies the combination of hour, weekday and protocol could still single someone out. No k-anonymity check is run. | Medium | Open: k-anonymity check before pooling |
| F4 | Clinical | CONTAIN thresholds, THERA protocols, the dose (50 a day for 4 days) and the frame rules are design choices. They are not validated, and not yet reviewed by clinicians. | High before clinical use | Open: clinician review, ethics-approved pilot |
| F5 | Clinical / regulatory | Used with patients, parts of RSOS could count as medical-device software (EU MDR, FDA). The site states it is not a treatment. | High before clinical use | Open: regulatory assessment |
| F6 | Hardware | The firmware has never run on a board. | High | Open: board kit, first board report |
| F7 | LINX | Plain-language understanding is rule-based and English-only, so it misses unusual phrasing. The form always lets the person correct it. | Low | Known |
| F8 | Accessibility | Keyboard focus, contrast and reduced motion are handled, but there has been no WCAG audit and no screen-reader test. | Medium | Open |
| F9 | Glyphs | About 10 Unicode 15 alchemical symbols may lack a font on some devices; they fall back to a stored image. | Low | Known |
| F11 | Hardware reach | RSOS runs only on bands whose software can be replaced (self-built ESP32 bands, flashable ESP32 wearables, RDP/1 devices) and on the vibration of Android phones. Closed brand watches (Apple Watch, Fitbit, Garmin, Mi Band) and Wear OS watches need RSOS watch apps that do not exist yet. | Medium for adoption | Open: Wear OS and watchOS apps; PineTime and Bangle.js ports |
| F10 | Process | One maintainer; no outside code review yet. | Medium | This package |

## 6. What to look at, by area

**Engineering**

- Do the RSX compilers agree on every program, and does the language reference match them (`rsx/README.md`)?
- Is the runtime's timing claim sound (C1, C2)?
- Does the firmware core meet RDP/1 §4 in every state (`firmware/rsos_core/`)?
- Are the parity tests strong enough, or could both implementations share the same bug?

**Safety**

- Can any path start a run without passing CONTAIN, consent and the run limits?
- Is the device safety envelope enforced everywhere: compiler, host and firmware?
- Are the drift and escalation rules sensible? What would a clinician change?

**Clinical**

- Are the THERA protocols safe as written, particularly the therapist-led observer work with memories?
- Are the screening question, the distress ceilings and the stop rules adequate?
- What should be measured in a first pilot (`toolkit/study_kit/PROTOCOL.md`)?

**Research**

- Do the pre-specified analyses test H1–H6 as stated?
- Is the contribution format sufficient for pooled analysis?
- Does CM1's synthetic validation say what it claims, and no more?
- Do TRIAL's verdicts claim no more than one person's data supports, and does pooling say what it claims?
- Does PEAK's probe design (blind, against sham) answer whether an anchor works, and does its simulation say what it claims, and no more?

**Privacy and security**

- F1–F3 above.
- Is the contribution file de-identified as specified?
- Can anything leave the browser without the person's action?

**Accessibility and design**

- Can every page be used by keyboard and with a screen reader?
- Is the language plain?

## 7. How to report

Open an issue in the repository with the label `review`, or send a report written with
[`review/REPORT_TEMPLATE.md`](review/REPORT_TEMPLATE.md). Name the area, the file and line or the page, what you
expected and what happened, and the severity. Reviews are credited in the release notes unless you prefer
otherwise.
