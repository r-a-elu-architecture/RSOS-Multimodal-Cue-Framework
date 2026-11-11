# RSOS Architecture Benchmark Lab — evidence register

Public URL: https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/architecture-benchmark.html

## Source basis

- Functional operator strict contextual holdout: [research/functional-operator-discovery-v1.0/RESEARCH_FINDINGS.md](../research/functional-operator-discovery-v1.0/RESEARCH_FINDINGS.md)
- Operator map and negative cases: [OPERATOR_MECHANISM_MAP.md](../research/functional-operator-discovery-v1.0/OPERATOR_MECHANISM_MAP.md)
- Ancestry attestation internal cohorts: [COMPARISON.csv](../research/ancestry-attestation-v0.9/COMPARISON.csv)

## What this actually does

A static, accessible interactive report comparing recorded aggregate metrics, plus a client-side CSV evaluator for paired held-out binary predictions. The CSV evaluator computes pooled Brier (not macro AP); it accepts quoted CSV fields and validates probability bounds. It never uploads the file.

**Not a new execution of the original model training.** The public repository contains aggregate research reports, not the complete source-era labeled examples and paired prediction files required for independent reproduction. The published operator experiment used 9,000 selected messages, 246 conversations, 1,571 linked assistant messages and a strict 25-conversation forward holdout with 259 response pairs. It was not a full-corpus or independent external replication.

## Reproduction requirement

To claim an independently reproduced benchmark, publish consent/privacy-reviewed held-out binary labels, paired prediction probabilities, conversation-level split manifest, model training scripts, exact dependency versions and cryptographic hashes. Then compare with optimized word+character contextual baselines, modern pretrained language models and matched provenance-feature ablations, with near-duplicate removal and conversation-cluster uncertainty.

## Scientific boundary

These tests predict next-assistant lexical operator language and measure internal proof-size tradeoffs. They do not validate RSOS clinical effects, model-weight modification, exclusive architectural novelty or market traction.
