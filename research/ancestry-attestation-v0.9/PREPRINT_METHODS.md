# Proposed methods-paper contribution (draft)

## Title

**Independent-Audited Compact Ancestry Certificates for Privacy-Minimizing Human–AI Intervention Routing: A Reproducible Longitudinal Systems Benchmark**

## Abstract

Historical human–AI interactions can provide the provenance required to contextualize later user-authorized actions, but conveying complete ancestry paths discloses structural metadata and incurs verification and transmission costs. We present an experimental two-authority attestation protocol that encodes observed message ancestry using depth-first intervals, signed node assertions and an independently audited snapshot. On nine selected archives totaling 9,000 messages from 246 conversations involving one user, three separately sampled 900-query cohorts yielded a mean certificate payload of approximately 996 bytes versus 7.6–7.8 KB for the previous Merkle path implementation, with 19–25-fold faster certificate construction. All tested invalid source selections were rejected, along with the implemented replay, expiry, signature-tampering, revocation and consent tests. The gains require additional preprocessing and an independent auditor with access to pseudonymized graph metadata, and single-request signature verification was approximately 1.7 times slower. The protocol does not outperform an equivalently configured conventional signed-interval implementation and provides no evidence of psychological or clinical treatment effectiveness. We release a synthetic reproducibility fixture, threat model, baseline implementation and analysis code for external replication.

## Principal claim

For an **observed, single-parent event graph**, issuer-signed depth-first labeling plus independent topology audit can produce ancestry attestation payloads that are nearly constant in path length, enabling privacy-minimized, user-authorized cue-routing suggestions without disclosing private message bodies to the request verifier.

## Distinguishing architectural application

RSOS historical cue genealogy → RSIA validity/uncertainty gate → RSX scoped consented suggestion → RSSO replay-revocation-audit lifecycle. The integration is the proposed application, not a novel cryptographic primitive.

## Counterfactuals that could refute practical value

- A generic signed-interval system with the same witnesses matches or exceeds the code (expected).
- A modern authenticated DAG-proofs library achieves smaller/faster certificates under an equal trust model (possible).
- A malicious or compromised graph auditor falsifies ancestry or exposes sensitive metadata.
- Additional key management, real-world graph updates and remote verification overhead erase the savings.
- The user obtains no benefit from source-targeted cue history relative to ordinary context/consent handling.

## Strong next empirical paper

On independent individuals, test whether documented cue ancestry adds predictive value for **delayed behavioral recurrence** relative to strong equally-informed state-space and Bayesian learning models. Stratify by context renewal and missing history. The current study cannot estimate that effect and cannot justify therapeutic claims.