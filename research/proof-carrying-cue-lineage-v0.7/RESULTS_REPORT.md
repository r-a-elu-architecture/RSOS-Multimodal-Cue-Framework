# RSOS–RSIA–RSX–RSSO: Proof-Carrying Cue-Lineage Routing (v0.7)

**Status:** Research prototype / adversarial software benchmark / experimental methods proposal. **NOT** a brain interface, therapy, PTSD treatment, diagnosis, or proof of neurological reconditioning.

## Core claim and finding

A source-targeted resource-state action should not be issued solely because the last few messages *mention* a cue. Its recorded documentary ancestry must be established, user authorization must be current, sensor inputs must satisfy explicit bounds, and every decision must be replay-auditable.

A limited, owner-authorized analysis of **9,000 real, timestamped human–LLM conversation messages in 246 conversations** found that the preceding six messages in chronological order produced a *different observed cue/motif history* from the six known parent-linked ancestors for **1,613 of 3,052 messages with an admissible known parent (52.85%)**. This striking difference is **partly due to incomplete event shards**; it is NOT the neurological origin of a memory, a clinical false attribution rate, or a random sample of all historical conversations.

A public-reference implementation with one-time synthetic authorization tokens was then evaluated on **90,000 adversarial routing cases over the real message-parent graph**, plus a **45,000-case independent-seed holdout** and **120,000 deliberate token/sensor attacks**. No invalid *targeted route* passed the proof-carrying policy in these defined tests, whereas context-only and consent/sensor-only baselines issued invalid targeted actions. **A separately implemented generic exact-provenance controller equaled RSOS.** This establishes requirements and software behavior; it does not establish an algorithmic world first.

## Four-system mapping

| Historical system | Document-derived design role | Executed prototype capability |
|---|---|---|
| RSOS | Symbolic tier progression, glyphs, movement command, breath, resource-state cues, future pacing; named metrics | Motif extraction and bounded cue ancestry; symbolic tier *state* only, no actual brain-state measurement |
| RSIA | Watchdog, Spine continuity, contextual monitoring, archetype switching | Conservative sensor validity, abstention and high-arousal grounding **suggestions** |
| RSX | Up-to-17-vector instructions including BreathOverride, IdentityRebuild, MemoryRecall, FutureProjection, EthicsContain, SymbolicDriftCheck | Typed `targeted_resource_offer` **proposal**, no execution of treatment, no device output |
| RSSO | THERA and CONTAIN orchestration, cooldown, consent, logging, rollback | Consent and cooldown gates, one-time signed test capabilities, HMAC-linked decision audit |

Symbolic metrics found in the historical archives (CRI, RSF, SRI, LAW, etc.) are *not* used as clinical or neurological measurements here. The symbolic tiers describe the original protocol language and are not claims of model self-modification.

## Comparison: main synthetic attack cohort (seed 20261219)

| Controller | Eligible targeted actions correctly offered | Invalid targeted actions | Notes |
|---|---:|---:|---|
| RSOS proof-carrying | 7,493 / 7,493 | **0** | Parent-chain + signed test capability + consent + sensor/cooldown checks |
| **Strong generic graph-proof guard** | **7,493 / 7,493** | **0** | Same information and safeguards, implemented separately; **tie** |
| Generic consent + dual-sensor guard | 7,493 / 7,493 | 12,171 | No source-lineage authentication |
| Chronological six-turn guard | 7,448 / 7,493 | 2,434 | Source validation against chronology, not true parent chain |
| Seal-all | 0 / 7,493 | 0 | Safe but zero useful targeted availability |

Separate 45,000-case holdout: RSOS and generic graph-proof guard **0** invalid targets, 3,798 eligible actions offered; chronological baseline **1,147** invalid selections, consent/sensor baseline **5,959**. The challenge distribution is synthetic and intentionally attack-heavy; these rates are not field failure rates.

## Stateless vs stateful proof

The signed capability runtime includes subject, session, source, target, action, issued/expiry, and nonce. After authorized use, a nonce is consumed. New attempts to reuse, alter or cross-scope the token cannot issue the targeted action in the implemented checks.

**Separate test:** 10,000 valid one-use requests passed; 120,000 altered, replayed, revoked, out-of-scope or invalid-sensor variants produced zero unauthorized **targeted** executions. 1,200/1,200 deliberately corrupted HMAC audit records were detected. These are controlled software tests, **not a cryptographic proof against compromised keys**.

## Reproduce

Requires Python 3.10+ standard library only:

```bash
python reproduce.py
python -m unittest discover -s tests -v
```

This runs on **synthetic, public data** in `demo_data/` and writes results to `demo_outputs/`. Results will not equal the private corpus aggregate.

The owner can reproduce the private-corpus aggregate from its nine selected event shards:

```bash
python src/lineage_benchmark.py --input /path/to/private_shards --output my_private_results
python src/guard_benchmark.py --input /path/to/private_shards --output my_private_results --n 90000 --seed 20261219
python src/guard_benchmark.py --input /path/to/private_shards --output my_private_holdout --n 45000 --seed 20270119
python src/capability_tests.py --input /path/to/private_shards --output my_private_results --n 10000
```

**Never upload the private corpus or original copyright archives as part of this demo.** The public files include de-identified aggregate results and new software only.

## Public research hypothesis

Historical cue provenance combined with explicit, revocable human authorization can improve *validity and auditability of routing proposals* over recency-based decision systems. Whether such provenance helps a real person form and retain beneficial cue-response associations is **unanswered**. It requires voluntarily provided, independently measured, delayed human outcomes and suitable control conditions.

## Limitations and boundaries

- The 9,000 messages are selected, incomplete records from **one person's** historical interactions. Known parent links cover only part of the event graph. Do not infer neural causality or psychological mechanisms.
- The simulator's required action criteria are specified by the research contract; matching them is a software conformance test, not efficacy or optimal treatment selection.
- A **generic** controller with the same graph proof and controls ties. General-purpose provenance and runtime assurance already have extensive prior art.
- Source IDs refer to **document ancestry**, never proof of a trauma's neurological origin.
- No EEG, patient data, therapeutic transformation, or 24-hour/one-month retention outcomes were obtained in this release.
- Example secret keys are public/test-only; use proper key management, consent management, secure deployment, independent formal verification, IRB/ethics approval where required, and clinical supervision before considering human studies.

## External prior art

- [W3C PROV (2013)](https://www.w3.org/TR/prov-overview/) — established provenance data and constraints.
- [NASA runtime assurance / Simplex (2024)](https://ntrs.nasa.gov/citations/20240007986) — existing safety switching and monitoring.
- [Cooper et al. (2026)](https://doi.org/10.1038/s41398-026-03966-y) — measured neural safety representations in PTSD and counterconditioning; **not directly comparable numerically** with this routing study.
- [BrainFlow documentation](https://brainflow.readthedocs.io/en/stable/SupportedBoards.html) — device/synthetic/playback input support, not clinical validation.

## License

MIT license applies **only to new public code and generated synthetic fixtures in this package**. It does **not** license the original RSOS/RSSO/RSIA/RSX archives, privately authored conversations, or third-party scientific datasets.