# Evidence-Gated Compositional Cue Programs for Personalizable, Consent-First Human–Computer Feedback: An Executable Systems Benchmark

**Preprint draft — simulation methods and software engineering only. No clinical or biological efficacy claims.**

## Abstract

User-programmable cue interfaces may combine personalized symbols, visual/auditory reminders, mnemonic associations, optional tier labels, physiological context observations, and staged rehearsal commands. A key engineering risk is **negative transfer**: cue-family relationships inferred during calibration may be invalid for a particular user, task or context. We present an open research prototype derived from four historical source-system roles: RSOS (cue semantics), RSIA (assumption validity and consent), RSX (typed operator program), and RSSO (calibration, routing and memory). The proposed mechanism is *evidence-gated compositional transfer*: predict new program choices using declared cue relationships only when between-family variation is supported by available calibration; otherwise use individually observed cue responses.

We evaluate the idea in eight predeclared, deliberately heterogeneous **synthetic** mechanisms, including family transfer, pairwise synergy, reversal, idiosyncratic cue responses, independently sampled action preferences, noisy reports, context drift and null effects. With 24 artificial calibration observations per simulated person, 180 candidate cue programs and 16 held-out decisions each, independent three-seed confirmation yields 18,432 simulated decisions per model. The evidence-gated policy obtains 0.1978 regret versus 0.2267 for a generic all-pairs ridge controller: a 12.7% relative decrease (absolute paired reduction 0.02885, world/seed-cluster bootstrap 95% CI 0.0114–0.0504). A separately seeded experiment holding one context out of calibration shows an 8.46% relative difference (0.1985 versus 0.2169). A generic cross-validation model selector is statistically indistinguishable, and an identically specified generic evidence-gated policy matches exactly. Therefore, the result supports a *general, inspectable computational design principle*, not RSOS-exclusive superiority. Software checks validate 50,000 randomized compilations, 100,000 bounded routing decisions and 100,000 scoped cue-meaning lookups without oracle disagreements. No real EEG recording, psychotherapeutic intervention, delayed human mnemonic outcome, or neurological transformation was measured.

## 1. Motivation

Fixed symbolic-conditioning chains are poorly suited to context-specific goals, arbitrary tier subranges, individually preferred symbols, sensory aversion or conflicting cue meanings between people. A programmable system can instead permit a neutral mnemonic chain (context cue → private image → goal reminder), a voluntary imagery rehearsal, an interruption-to-resource suggestion, or a tier-free skill practice. The system's software architecture should not equate these program steps with actual changes in identity, emotion or brain physiology.

A scientifically important problem is to know **when a learned relationship should be reused**. Adding all imaginable modalities or pairwise operators is not automatically advantageous; a system needs a reason to trust each transfer. This is the precise contribution evaluated here.

## 2. Functional decomposition

RSOS supplies source-linked glyph and tier vocabularies, not empirically validated brain-state levels. RSIA supplies contextual safety checks and an assumption watchdog. RSX provides typed operator chains, such as optional mnemonic, interrupt, resource recall, breath, voluntary imagery and future-rehearsal prompts. RSSO supplies per-user program scope, history, cooldown and consent-first orchestration. A compiler accepts tiers as optional module annotations rather than mandatory milestones; a graph may branch, but requires the user to choose a branch.

A distinct identity-and-context namespace permits the same glyph (e.g. LION) to have different user-authorized meanings for separate users, goals, or contexts. Such namespacing is standard software engineering; it is not a claim of novel cryptography.

## 3. Methods

### 3.1 Artificial personalization environments

The evaluation contains 12 glyphs in four externally supplied families, five sound codes, three program-operator codes and four voluntary contexts. This creates 180 potential cue programs and 720 program/context combinations. Every simulated person supplies 24 randomized calibration trials with noisy numeric ratings, followed by 16 held-out evaluations. The assumed hidden utility generator consists of group, glyph, sound, plan, context, context-by-group and group-by-plan terms, plus action-specific variation. The relative strength of these terms changes dramatically by predeclared world. The simulator includes a null-effect world and an unstructured-action world which violates the relational hypothesis. All numeric utilities and preference reports are *invented* and must not be interpreted as psychological or physiological scores.

### 3.2 Comparators

Static global program; individually best observed arm; additive ridge; generic all-pairs ridge; source-inspired relational ridge; shuffled cue-family relations; evidence-gated relational/flat fallback; generic identical gate; generic 3-fold cross-validation selection of the same models; inaccessible oracle. All policies receive the identical action choices, artificial reports, and per-person calibration. The source-derived glyph-family labels represent an *assumed structured cue mapping*, not a measured cognitive relationship.

### 3.3 Assumption watchdog

The watchdog measures between-family variance in observed personal ratings relative to total variance (an ANOVA-style explained variance). The gating threshold was frozen at **0.23** before three independent confirmatory seeds. When the observed cue families explain insufficient variation, the policy uses the person's observed arm values rather than transferring relational predictions. This simple rule is a conventional statistical procedure. The name RSIA labels its placement in the user's proposed framework, not invention of the algorithm.

### 3.4 Outcomes and uncertainty

Primary outcome is synthetic decision regret relative to the best hidden synthetic action for the given simulated person/context. World-seed clusters (8 worlds × 3 seeds = 24) are resampled with nested simulated-person draws. Dependence between 16 trials of a person is preserved. Bootstrap intervals represent variability across **invented environments**, not sampling uncertainty about biological effects. Multiple contrasts are exploratory; no correction for multiple comparisons is claimed.

### 3.5 Additional experiment

On fresh seeds, context 3 is excluded from calibration in the drift world, creating a genuine held-out-context software challenge. Separate equal-budget balanced coverage explores whether more diverse calibration observations improve performance; the gate's gain over random calibration was not statistically established.

### 3.6 Safety contracts

A suggestion-only compiler validates typed operator graphs, optional tier ranges, user-defined goal maps, permitted sensory channels and DAG acyclicity. The runtime abstains without user consent, when context/quality thresholds fail, or when cooldown is active, and routes high self-reported distress to optional manual grounding rather than an untested memory protocol. The scoped registry blocks stale, revoked, or wrong-person cue meanings. Signal-adapter unit tests demonstrate spectral extraction on a **synthetic sine wave only**; EEG cannot be assumed to indicate conditioned emotions from its alpha/beta bands.

## 4. Results

On confirmation seeds 63011/63012/63013 (1,152 fictional persons, 18,432 held-out choices per policy), evidence gating yields regret **0.197825**, compared with static **0.525743**, flat personal arm **0.221336**, generic additive **0.240188**, generic all-pairs **0.226675**, ungated relational **0.220643**, and generic 3-fold selector **0.195136**. Gate-minus-all-pairs improvement is **0.028850** (95% world/seed cluster CI **0.011383–0.050399**), or **12.73% relative**. The exact-match generic gate scores **0.197825**. Thus no architecture-exclusive advantage is established.

In a strict new-context holdout across fresh seeds 64011/64012/64013, evidence-gate regret is **0.198525**, versus generic all-pairs **0.216869** (8.46% relative, improvement CI **0.003944–0.035346**). On the novel-context world alone, gate regret is **0.281141** versus all-pairs **0.309829**, with no observed performance on real human recollection or physiology.

A prespecified balanced calibration design improves evidence-gate regret by **0.010586** on matched seeds, but a world/seed-cluster interval of **−0.000847 to 0.021778** does not exclude zero. Compiler checks passed 50,000 randomized programs; routing checks 100,000; scoped registry 100,000. Twenty-four unit tests passed.

## 5. Interpretation

The strongest qualitative result is **selective reuse of symbolic associations**. The same descriptive relation can help transfer to untested cue combinations when group effects exist and harm performance when actions are independent. A simple evidence watchdog reduces negative transfer by changing which hypothesis class is allowed to drive decisions. This improvement is functional in the mathematical simulation. It does **not** imply that glyphs act as a brain-writing interface, that tier numbers encode neurological maturity, or that metaphor, scent, sound, EMDR-like dual attention, or future pacing have been proven to cause new mental states.

The same result can be built by a generic relational model with the same gate. Hence the novelty claim is **a concrete integration and reproducible negative-transfer evaluation**, not an exclusive or world-first algorithm. The paper is a methods/prototype contribution until actual target-response data exists.

## 6. Limitations and falsifiers

1. The environment's cue effects, group families, ratings, and goal utilities are *synthetic* and partially aligned with one tested representation; family-specific effects are generator parameters, not discovered brain laws.
2. No human EEG/HRV, true voluntary conditioning, mnemonic retrieval, controlled cue exposure or clinical outcome is included.
3. The strongest generic CV selector is a credible comparator and is slightly better on one aggregate.
4. Semantic glyph families might be arbitrary to a real person. Reversing or shuffling personal cue mappings may eliminate any advantage.
5. The flat personal baseline beats the gate in the unstructured-action world, revealing residual failure.
6. Safety-contract compliance does not prove clinical safety or successful emotional regulation.
7. Scope-isolation tests compare against an intentionally inadequate global symbol table, not modern access-control systems.
8. Generalization to public neural-interface datasets and external laboratories is completely untested.

## 7. Next study

A neutral, consented learning task should randomize matched-dose fixed, generic adaptive, single-cue personalized and compositional cue-chain interventions. Measure objective delayed recall and response latency across contexts, pre-register the smallest meaningful effect, and test the exact matched generic policy. Physiological recordings require independent calibration and should not be treated as mental-state labels absent direct validation. See `NEXT_HUMAN_STUDY.md`.

## References

Li et al. (2010), contextual bandit personalization: https://doi.org/10.1145/1772690.1772758

Decoded neurofeedback methods: https://doi.org/10.1093/SCAN/NSAA063

VR neurofeedback review: https://doi.org/10.1007/s10484-024-09677-8

Co-adaptive real-time fMRI evidence (2026): https://pubmed.ncbi.nlm.nih.gov/41644844/

EEG Motor Movement/Imagery dataset: https://physionet.org/content/eegmmidb/1.0.0/