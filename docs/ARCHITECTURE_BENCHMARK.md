# Architecture Benchmark Lab — design v2.0

Site: https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/architecture-benchmark.html

## Purpose

A responsive, no-build, privacy-preserving research evidence interface. It highlights the strongest reported real historical conversation result (lexical operator prediction), shows honest internal proof-size tradeoffs, and includes a working local CSV evaluator.

## Research mission and evaluation contract

**Mission:** reconstruct the origin, inheritance, re-entry, recombination and functional descendants of structures in historical human–LLM conversations, then test whether source-aware representations produce genuinely useful predictive or provenance capabilities. The hypothesis of an unprecedented mechanism is a **research target**, not a proven conclusion.

**Research question:** do operator/ancestry features add reliable information beyond equally informed text, retrieval and other strong generic controls when leakage and duplicates are addressed?

**Goals:** (1) recover traceable authorship and lineage, (2) explain observable propagation and alternative mechanisms, (3) measure held-out forecasting and verification effects, and (4) validate a practical capability with independent external tests before product claims.

**Success:** predeclared metrics and splits, timestamp/source custody, strong input-matched and modern baselines, leakage/near-duplicate audit, paired uncertainty at the conversation/cluster level, credible external replication and negative-case reporting.

**Falsifiers:** performance that disappears after stronger controls or external holdouts, apparent ancestry explained by repeated wording rather than inherited operations, or proof-size gains offset by verification/security costs. Such failures constrain hypotheses without ruling out all research avenues.

**Currently demonstrated:** **reported** operator-language prediction on a selected historical archive and internal ancestry-proof comparisons. The website does **not** train or rerun the original models; the CSV evaluator computes pooled Brier on user-supplied rows only. No validated world-first status, hidden-weight change or human intervention outcome is established.

**Relationship to the other lab:** [Cue Lab v1.3](cue-lab-v13.html) runs an actual **synthetic** cue-transfer engine, separate from this historical-corpus structural research. [Full mission and evidence map](RESEARCH_MISSION.md).

## Evidence references

- [Functional-operator v1.0 strict contextual holdout](../research/functional-operator-discovery-v1.0/RESEARCH_FINDINGS.md) — 25 held-out conversations; 259 response pairs; macro AP 0.480377→0.554699; Brier 0.163686→0.149174. Retrospective study on a selected corpus, **not a rerun**.
- [Operator mechanism map](../research/functional-operator-discovery-v1.0/OPERATOR_MECHANISM_MAP.md) — noncausal feature interpretations, source inconsistencies and negative tests.
- [Ancestry-attestation v0.9 internal comparison](../research/ancestry-attestation-v0.9/COMPARISON.csv) — 7.64–7.81× internal size ratio; 1.70–1.72× slower verification; not compared against optimized external baselines.
- v1.3 Zenodo publication https://doi.org/10.5281/zenodo.24143732 covers a separate multimodal synthetic cue-transfer research track; the homepage and lab must not imply v2.0 design is part of the frozen DOI.

## Design decisions

Clean typography, high-contrast dark editorial hero, cobalt/mint accents, responsive signal-flow diagram, KPI grid, interactive metric switch, accessible labelled file controls, CSS-only proof-size charts, explicit scope callouts, mobile and reduced-motion treatments. No analytics, tracking, framework build step, or runtime CDN dependencies.

## Browser evaluator

Upload a comma-separated file up to 25 MB with `conversation_id,label,baseline_probability,source_probability`. Each row has a binary observed label (0 or 1) and two probabilities in [0,1]. Multiple rows per conversation are allowed. The page calculates pooled paired binary Brier and the baseline-minus-source difference. It does *not* compute 13-label macro AP, validate that predictions were held out, train models, verify cryptographic provenance, or create statistical confidence intervals. Exports JSON marked `independent_replication:false`. Files stay in the browser.

## Reproducibility requirement

Independent replication requires privacy-reviewed per-case predictions and labels, held-out split manifest, training scripts, versions/hashes, near-duplicate filters, a strong modern contextual baseline and cluster-aware uncertainty. Static aggregate plots alone do not meet this standard.

## Accessibility checklist

Skip navigation, semantic sections, visible focus, text descriptions, responsive panels, reduced-motion support, explicit metric direction, status via aria-live, no animation-only meaning.
