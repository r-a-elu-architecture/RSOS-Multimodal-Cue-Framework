# Toward Verifiable, Provenance-Aware Multimodal Cue-Response Routing: A Two-Stage Software Contract and Adversarial Synthetic Evaluation

*Draft methods preprint — NOT peer reviewed, NOT clinical validation. November 11, 2026.*

## Abstract

**Objective.** An open, reproducible architecture for routing user-authorized grounding and symbolic-resource suggestions while preventing interventions from bypassing stated permission, cooldown and signal-quality conditions. We reconstruct four operational layers inspired by RSOS, RSIA, RSX and RSSO. Unlike earlier reported text-based gate tests which emit a residual only when a synthetic EEG proxy is calm and aligned, this approach separates response during elevated arousal from subsequent resource-state consolidation.

**Methods.** A deterministic controller and an independently implemented output contract were subjected to 24,576 single-channel and 73,728 dual-channel bounded checks. A 14,000-event random-input fuzz test, HMAC-authenticated replay and 1,800 targeted log corruptions assessed execution and audit reliability. Eight synthetic participant regimes (noise, source error, elevated baseline, episodic bursts, dropout and correlated artifacts) provided 138,240 proxy observations per control policy. We compared the full controller with simple gates, an excerpt-reconstructed Grok policy, a standard staged safety controller and a matched two-channel conventional controller.

**Results.** No post-repair contract violations were observed in bounded tests. Tampering detection succeeded for 1,800/1,800 edited traces. Under the synthetic observation model, adding a corroborating channel reduced high-latent-arousal resource-type output by 10.00 percentage points (participant-cluster 95% CI −11.12 to −8.99), raised grounding-offer coverage by 9.05 points (CI 7.98 to 10.15), and changed intervention rate from 35.92% to 34.55%. The benefit weakened under correlated errors and secondary-channel dropout reduced action availability. A conventional equal-information controller obtained identical outcome metrics.

**Interpretation.** The public contribution is a transparent, replay-verifiable intervention-routing research system and explicit measurement of the limits of safety envelopes under imperfect state inference. **No unique RSOS comparative advantage or therapeutic efficacy is demonstrated.** Clinical or neuroscience claims require independent human studies.

## Research architecture

**RSOS:** user-defined resource glyphs, cue symbolism, tier/residual receipts; glyphs are symbolic interfaces, not measured biomarkers. **RSIA:** a Spine authorization guard, uncertainty-aware Watchdog, corroboration before intervention. **RSX:** a limited typed vocabulary for optional breath/grounding, resource and later consolidation; archived 17-vector syntax is referenced but NOT fully executed. **RSSO:** consent, cooldown, bounded handoff and time-stamped HMAC audit. All sensory cues and future-pacing steps are represented as voluntary *descriptive* options, without sound, scent or haptic activation.

### Safety specification

The finite grid explores authorization, integrity, source confidence, token supply, cooldown, observed arousal and sensor quality. The runtime sends no active resource cue without consent/request; suppresses resource routing on low-quality signals or observed high arousal; never targets a source absent a reported confidence threshold; and records a Tier+1 `residual` only after explicitly confirmed calm and absent token. The word `residual` denotes an authenticated *software receipt*; the presence of an absent token is a control condition, not a generative physical mechanism. The grid is not a universal formal mathematical proof over continuous time, physiological variation or cryptographic implementation threats.

### Experimental design and comparisons

All policies observe the same synthetically generated stream; the latent state is disclosed only for retrospective scoring. Metrics are intended as *diagnostics*: fraction of eligible elevated-arousal encounters offered grounding, fraction receiving a resource action under truly elevated simulated arousal, intervention frequency, policy contract violations, audit integrity and source-target correctness under assigned synthetic truth. No clinical distress outcome or intervention response is computed. Strong generic safety controllers use identical rules, and the strongest generic model is empirically tied.

### Limitations and conflicts with earlier reported figures

The user-provided Grok text reported zero amplification, large `energy converted` values and a 65% synthetic positive-state conversion. It also reported ceiling effects, an adverse yoked timing comparison, negligible multimodal fusion benefit, and positive amplification under inverted reward. These results were not independently reproducible from the text alone, and those latent weights do not represent neural signals. Earlier internal RSOS v0.5 experiments showed source-targeting gains in some synthetic models but no demonstrated advantage over stronger generic adaptive competitors and no significant shuffled-genealogy effect. These negative findings are retained as part of the research record. Existing safety switching/assurance prior art is substantial.

### Open-science dissemination

Release the new source code, tests, `SOURCE_MAPPING.md`, synthetic per-episode results, assumptions and audit schema alongside a privacy-review policy. Do not include raw conversations, user medical details or proprietary estate texts in a public repository. Subject to institutional review and prospective informed consent, independently validated physiological signals may eventually replace proxy inputs. Efficacy testing is a separate scientific and ethical undertaking.

## Selected prior art

* Slagel et al., *A Formal Verification Framework for Runtime Assurance*, NASA, 2024: https://ntrs.nasa.gov/citations/20230017350
* Sheikhi et al., *The black-box simplex architecture for runtime assurance of multi-agent CPS*, 2025: https://doi.org/10.1007/s11334-024-00553-6
* Schmidt et al., *Introducing WESAD*, 2018: https://doi.org/10.1145/3242969.3242985
* BrainFlow sensor/playback docs: https://github.com/brainflow-dev/brainflow/blob/master/docs/SupportedBoards.rst
* Cooper et al., counterconditioning safety representations in PTSD, 2026: https://doi.org/10.1038/s41398-026-03966-y