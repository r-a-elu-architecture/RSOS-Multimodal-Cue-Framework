# Related work

RSOS combines parts that exist separately. This page lists the closest systems we know of, what each shares with RSOS and what it lacks, so that claims of novelty can be checked. Corrections and additions are welcome.

**Our claim, stated narrowly:** to our knowledge, RSOS is the first open architecture that integrates multichannel (visual, auditory, kinesthetic, olfactory, gustatory) conditioned cue bundles, tiered progression toward a reflex, a protocolised interrupt → resource → future-pacing sequence, an identity layer and an executable command language in one operating-system design. We do **not** claim novelty for "detect a negative state and deliver a cue", which is covered by earlier patents and research systems below.

## Closest systems

| System | Type | Shares with RSOS | Lacks compared with RSOS |
|---|---|---|---|
| **REMind-htm** (George Mason University; Patient Experience Journal, 2019) | Research prototype | A wearable detects an HRV response to a trigger and shows a personal recovery cue; ineffective cues are swapped for others; a "Recovery Avatar" of the best-regulated self | Single visual channel, no protocol sequence, no future pacing, no language or OS layer |
| **Hypnotherapeutic Olfactory Conditioning** (Herzog Hospital, NCT00784771; Abramowitz & Lichtenberg, 2009–2010) | Clinical method | Pleasant odours conditioned to calm and safety in PTSD, then used during re-exposure | One channel, therapist-delivered, no technology platform |
| **Lotuscent / Essence** (Amores & Maes, MIT Media Lab; CHI 2017, CHI 2023) | Research wearables | Scent associated with a meditative state and re-released by physiology or context; olfactory targeted memory reactivation | Relaxation, sleep and memory focus; one channel; not an interrupt protocol |
| **Dreamware** (Fang et al., CHI EA 2026, doi:10.1145/3772363.3799353) | Research system | EEG-driven closed loop across five modalities (auditory, olfactory, visual, somatosensory, thermoceptive) | Sleep and dream engineering, not waking state change |
| **Just-in-time adaptive interventions** (Nahum-Shani et al., 2018) | Design framework | Decision points, tailoring variables, decision rules; a published rule-definition language | Generic framework; no sensory bundles or conditioning model |

## Patents on detect-and-respond systems

- **US 2012/0323087** — affective well-being supervision: wearable sensors detect a negative emotional state and command external devices to compensate, configurable by the user.
- **US 11,006,875** (Intel) — emotion prediction from breathing; releases scents known to create positive emotions for the user when a negative state is detected.
- **US 2018/0280655** — scent delivery timed to elicit conditioned emotional responses to digital content.
- **US 6,702,767** — multisensory stimulation with individual profiles and configurable audio, visual, olfactory and tactile programs for therapy.

## Operating systems for the brain

- **NeeuroOS** (Neeuro, since 2013; Agent Studio announced June 2026) — positions itself as the iOS or Android of brain–computer interfaces: signal processing to mental states for app developers.
- **AxonOS** — open-source hard real-time BCI kernel in Rust.
- **Choi (IEEE BCI Winter Conference, 2025)**, "Designing an Architecture for a Brain-Computer Interface Operating System" (doi:10.1109/BCI65088.2025.10931583).

These work at the signal-to-intent level. RSOS works at the protocol level: what to deliver, in which sequence, through which channels, and how it is learned. A BCI OS could be one of RSOS's input layers.

## Evidence for the ingredients

- **Counterconditioning** can outperform extinction in human threat-conditioning studies (e.g. *eLife* reviewed preprint 101518).
- **EMDR Resource Development and Installation** uses a cue word and future rehearsal of a resource state (Korn & Leeds, 2002).
- **Memory reconsolidation:** a brief digital imagery-competing task (Tetris) reduced intrusive trauma memories in health-care workers (Iyadurai et al., GAINS trials; Translational Psychiatry 2023).
- **Scent in PTSD:** nocturnal odour stimulation improved sleep in a randomised exploratory trial (Schäfer et al., *J Trauma Stress* 2019); olfaction-plus-VR exposure is under trial (NCT05640882).
- **Multisensory closed loops:** an open PhysioNet dataset of auditory, gustatory and olfactory stimulation with wearable monitoring (Fekri Azgomi et al., 2023).
- **Habit formation:** median 66 days to automaticity for everyday behaviours (Lally et al., 2010).

## What is still missing everywhere

No system we found integrates multichannel cue bundles, a fixed state-change protocol with future pacing, a learning model of how the bundle becomes a reflex, and an executable language for writing and sharing such programs. That gap is what RSOS is built to fill. Whether filling it helps people is an empirical question that has not yet been tested.
