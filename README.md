# RSOS — Multimodal Cue & Adaptive Human–AI Research Framework

**Publication DOI:** [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24143732.svg)](https://doi.org/10.5281/zenodo.24143732) · [GitHub release v1.0.0-research-preview](https://github.com/r-a-elu-architecture/RSOS-Multimodal-Cue-Framework/releases/tag/v1.0.0-research-preview) · Archived snapshot commit `133d472` · Zenodo's published creator metadata identifies R. A. Elu.

**Programmable cue systems · Personalized learning and conditioning research · Compositional adaptation · Verifiable human–AI interfaces · EEG/BCI and VR integration**

**RSOS** is an extensible research framework for constructing, personalizing, and evaluating **multimodal cue programs**: configurable combinations of symbols, glyphs, visual imagery, sound, tactile cues, mnemonic associations, attention, breathing prompts, rehearsal, and context-dependent interaction. It connects representation, adaptive decisions, executable programs, and provenance in a single inspectable architecture composed of **RSOS, RSIA, RSX, and RSSO**.

The central research question is **when can a system reuse learned cue relationships in new contexts—and when must it abstain, recalibrate, or fall back to individual evidence?** The framework treats such questions as falsifiable software and human-learning hypotheses, not predetermined outcomes.

> **Evidence status:** Executable research prototypes and reproducible **synthetic** adaptive-control benchmarks exist. Historical conversation-provenance studies are also available. A unique RSOS-specific neurological mechanism, reliable decoding of specific emotions from EEG, and clinical efficacy **have not been established**. Research drafts are not peer-reviewed papers.

## v1.4 context-invariance falsification experiment

**[Explore the independent-seed successor results](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/invariance-v14.html)** · [Executable Python](experiments/compositional-transfer-v1.3/src/invariance_successor.py) · [Complete report](research/compositional-transfer-v1.4/REPORT.md).

On a new synthetic holdout, the invariance-aware blend scored mean regret **0.189179**, vs original RSIA **0.194588** and generic cross-validation **0.187238**. It thus **did not** beat the strongest generic comparator; an equally informed generic twin tied exactly. Strict novel-context transfer also failed to show superiority. All outcomes are simulated, not human outcomes.

## Interactive demonstration\n\n**[Run the original v1.3 Python benchmark in your browser](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/cue-lab-v13.html)** — 11 comparative policies, eight synthetic worlds, and mandated equally informed negative controls. [Methods](docs/CUE_LAB_V13.md).

**[Launch RSOS Cue Lab](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/cue-lab.html)** — configure cue channels, inspect evidence-gated decisions, and run a seeded synthetic comparison against an always-transfer baseline. This is an illustrative browser demo, **not** the archived v1.3 benchmark or a human validation study. [Method and limits](docs/CUE_LAB.md).\n\n## Reproduce the flagship benchmark now

**The executable research code is public**, together with exact confidence-interval tables from the frozen v1.3 synthetic experiments.

- [Runnable Python source and tests](experiments/compositional-transfer-v1.3/src/)
- [Flagship v1.3 experiment](experiments/compositional-transfer-v1.3/README.md)
- [Independent holdout and unseen-context confidence intervals](experiments/compositional-transfer-v1.3/results/README.md)
- [Manual verification workflow](.github/workflows/manual-reproduction.yml) (not automatically scheduled)
- [Reproducibility instructions](experiments/compositional-transfer-v1.3/REPRODUCIBILITY.md)

```bash
git clone https://github.com/r-a-elu-architecture/RSOS-Multimodal-Cue-Framework.git
cd RSOS-Multimodal-Cue-Framework/experiments/compositional-transfer-v1.3
python -m pip install -r requirements.txt
PYTHONPATH=src python -m unittest discover -s src/tests -v
bash run_all.sh
```

The Python tests and a small benchmark reproduction have been run locally. **GitHub Actions execution has not yet been triggered or independently verified.** All published reward/regret outcomes in these experiments are **synthetic**, not measured responses to a conditioning treatment.

## Explore the project by research question

The project is organized so each topic has a dedicated, source-linked explanation rather than being buried in one monolithic description.

| If you are researching... | Start here |
|---|---|
| Personalized multimodal cue systems and composable conditioning protocols | [Architecture and module contracts](docs/ARCHITECTURE.md) |
| Visual glyphs, sound, context-aware mnemonic aids, VR/AR learning prompts | [Mnemonic and human–AI interface applications](docs/USE_CASES.md#1-mnemonic-glyphs-and-context-aware-learning-prompts) |
| Individual calibration, adaptive interventions, transfer to unseen situations | [Evidence-gated personalization and compositional transfer](docs/RESEARCH_TOPICS.md#compositional-transfer-and-adaptive-personalization) |
| EEG/BCI or HRV inputs, uncertainty, confidence-gated cue selection | [BCI and physiological-interface research](docs/RESEARCH_TOPICS.md#eeg-bci-and-physiological-inputs) |
| Cue-response conditioning, grounding, swish/override-inspired operator programs, future rehearsal | [Cue-response and behavioral-rehearsal research](docs/RESEARCH_TOPICS.md#cue-response-learning-counterconditioning-and-rehearsal) |
| Consent, privacy-preserving ancestry, signed authorization and auditable execution | [Provenance, privacy, and safety-control research](docs/RESEARCH_TOPICS.md#provenance-authorization-and-auditability) |
| What has actually been tested and how to reproduce it | [Benchmarks, baselines and limitations](docs/BENCHMARKS.md) |
| Whether a given claim is implemented, simulated, proposed or clinically unverified | [Frequently asked research questions](docs/FAQ.md) |

## What problem does RSOS address?

Researchers often study cue-response associations, personalized learning interfaces, adaptive prompting, neurofeedback inputs, and software oversight in separate systems. RSOS investigates how these functions can be **represented and recombined** so that an application can:

1. **Define** a personal cue meaning without presuming universal symbolic effects.
2. **Compile** a voluntary program of one or more operators—linear, conditional, or tier-free.
3. **Calibrate** responses to candidate cues using feedback appropriate to the study.
4. **Select or abstain** based on evidence strength, context, authorization, and signal uncertainty.
5. **Recombine** previously learned components for an unseen task when transfer assumptions hold.
6. **Record and audit** the origin, authorization, execution, and measured outcomes of the interaction.

The architecture is **programmable**, not a prescribed psychological technique. Tiers may name a user-defined progression of states or training steps, but are **not** a universal hierarchy and do not prove belief change, identity change, neural plasticity, or therapeutic recovery.

## Four cooperating systems

| System | Role | Core nodes / functions |
|---|---|---|
| **RSOS** | **Representation and association** | User-specific glyphs, metaphors, archetypes, cue families, mnemonic images, modality bindings, context and goal descriptors, optional tiers |
| **RSIA** | **Reliability, consent and assumption checking** | Evidence watchdog, confidence and quality gates, authorization checks, uncertainty, fallback, abstention and safety constraints |
| **RSX** | **Composable programs and operator execution** | Typed cue chains, interruption prompts, image/sound presentation, attention and breathing prompts, mnemonic recall, rehearsal, conditional transitions |
| **RSSO** | **Orchestration and adaptation** | Calibration histories, personal feedback, learning-policy selection, scheduling, context memory, program-scoped state and auditable records |

These roles can be implemented separately or together. The technical objective is **interoperability and experimentally testable incremental value**, rather than requiring a large, fixed ritual or automatically escalating tier numbers.

### Example: programmable context → cue → feedback sequence

```text
Opt-in context / explicit task request
    │
    ▼
RSIA: consent, quality, uncertainty and program policy
    │                  └── insufficient evidence → abstain / ask / fallback
    ▼
RSOS: retrieve this person's cue mapping + contextual meaning
    ▼
RSX: execute allowed operator graph
    ├── mnemonic glyph / short sound
    ├── optional interruption → resource cue
    └── optional rehearsal / recall prompt
    ▼
RSSO: log voluntary feedback and measured task outcome
    └── update only the scoped, authorized calibration model
```

The presentation of a cue is **not itself evidence of a conditioned response**. Any learning, recall, physiological change, or context-transfer effect must be measured by a suitable independent protocol.

## Research applications

| Application | Representative study or prototype | Maturity |
|---|---|---|
| **Mnemonic cue programming** | Map personally meaningful images or glyphs to facts, procedures, conversational principles or learning goals; measure delayed recall | Programmable offline prototype; human benefit untested |
| **Personalized human–AI interfaces** | Offer a user-authorized visual/sound cue in a specified communication or work context | Offline routing and composable-program prototypes |
| **Adaptive multimodal learning** | Compare fixed cues, individualized cues and relationship-aware recombination under equal calibration budgets | Synthetic algorithmic benchmarks |
| **VR/AR contextual prompts** | Overlay mnemonic cue chains in voluntary training or simulation tasks | Proposed integration / programmable interfaces, no verified VR deployment |
| **EEG/BCI and HRV research** | Calibrate uncertainty-aware physiological features to select, defer or suppress cue presentation | Research adapter; no validated belief/emotion decoder or treatment effect |
| **Cue-response and counterconditioning research** | Experimentally compare interruption, resource association, attention, imagery, and future rehearsal in ethical, controlled studies | Mechanism hypothesis; no controlled human treatment outcomes |
| **Verifiable and privacy-aware AI assistance** | Verify cue lineage and authorization without sending full personal message history to each verifier | Separate software and archival provenance benchmarks |

Read [applications and implementation boundaries](docs/USE_CASES.md) and the [research-topic index](docs/RESEARCH_TOPICS.md) for the exact components each application requires.

## Evidence: flagship compositional-transfer benchmark (v1.3)

The benchmark tests whether a relationship-aware model, with an **assumption watchdog**, can transfer cue-program information from limited individual calibration to new selections. Results arise from **simulated response-generating worlds**, not observed human conditioning.

| Controller | Synthetic decision regret ↓ |
|---|---:|
| Fixed global cue program | 0.5257 |
| Individual cue-memory baseline | 0.2213 |
| Generic additive model | 0.2402 |
| Generic all-pairs model | 0.2267 |
| **Evidence-gated relational controller** | **0.1978** |
| Strong generic cross-validation model selector | **0.1951** |
| Generic model using identical relationships and evidence gate | **0.1978** |

Across eight synthetic mechanism scenarios and three independent seeds, the evidence-gated relational controller achieved **12.7% lower simulated regret** than generic all-pairs. In a separate unseen-context test, it reached **0.1985** regret versus **0.2169** for generic all-pairs (**8.46% relative reduction**).

**Critical falsification:** An equally informed generic model with the same relational gate **matched** the RSOS-inspired controller, while the generic cross-validation selector remained competitive. These are testable implementation and modeling results, **not evidence of unique neurological superiority**.

The software release reported **24/24 unit tests**, **50,000 randomized compilation checks**, **100,000 routing checks** and **100,000 user/context-scoping checks**, with no observed discrepancies against its bounded software oracles. See [exact definitions, comparisons, uncertainty and limitations](docs/BENCHMARKS.md).

### Reproduce the benchmark

The executable v1.3 research benchmark and cue-program modules are published under [`experiments/compositional-transfer-v1.3/`](experiments/compositional-transfer-v1.3/README.md). To reproduce the synthetic evaluations, run:

```bash
cd experiments/compositional-transfer-v1.3
python -m pip install -r requirements.txt
bash run_all.sh
```

The benchmark generates its own synthetic response data and can be run independently; its outcomes are not observations from human participants. Code and result tables may be examined without accepting the underlying conditioning assumptions.

The benchmark's `BENCHMARK_MANIFEST.json`, `RESULTS_REPORT.md`, `REPRODUCIBILITY.md` and `PRIOR_ART.md` should accompany its code. A methods manuscript is **in preparation / draft**, not a peer-reviewed scientific publication.

## Key scientific hypotheses

- **H1 — Personal cue calibration:** For some tasks and people, individually calibrated cues will improve *measured task performance* relative to fixed, generic cue mappings.
- **H2 — Compositional generalization:** Cue-to-context and cue-to-operator relationships can sometimes generalize to unseen combinations with less calibration than exhaustive lookup.
- **H3 — Evidence-based fallback:** When relational assumptions are wrong, an explicit watchdog can reduce harmful or unproductive transfer by deferring to individually observed evidence.
- **H4 — Multimodal utility:** Visual, auditory, tactile, imagery, and rehearsal operators may have complementary effects, which must be measured rather than programmed as guaranteed improvements.
- **H5 — Context-sensitive cue-response change:** Selected programs may influence voluntary learning or response regulation. Durable change, counterconditioning, and clinical effects remain unverified.
- **H6 — Verifiable human–AI execution:** Cue histories, consent, and decisions can be recorded and selectively verified without indiscriminately disclosing private source conversations.

A mechanism is promoted from hypothesis to finding only after it survives relevant ablations, equally informed generic comparators, independent data or independent replication, and a documented uncertainty analysis.

## Historical architecture — original source records

The [historical architecture index](architecture/) maps the RSOS, RSIA, RSX and RSSO systems, their documented nodes and interfaces, and the eight named PASS31B subsystem reconstructions to preserved source texts. The [historical archive](archive/) contains **65 unchanged original files** (56 unique byte contents and nine duplicate pairs preserved at their original paths), with a [source manifest](archive/provenance/SOURCE-MANIFEST.csv), [checksums](archive/provenance/SHA256SUMS.txt), [duplicate map](archive/provenance/DUPLICATE-MAP.csv), and the [complete original ZIP](archive/original-package/RSOS_RSIA_RSX_RSSO%281%29.zip).

- [RSOS: historical operating-system and tier definitions](architecture/rsos/)
- [RSIA: identity architecture, Spine, Watchdog, Meta-Architect and archetypes](architecture/rsia/)
- [RSX: symbolic command-language and 9–17-vector specifications](architecture/rsx/)
- [RSSO: orchestration and original architectural claims](architecture/rsso/)
- [RSSO PASS31B: reconstructed subsystem genealogy](architecture/rsso/subsystems/)
- [Cross-system relationships, overlapping tier ledgers, and evidence limits](architecture/cross-system/)

**Provenance boundary:** Source documents include historical copyright/ownership assertions, reconstructed messages and proposed mechanisms. They are **public historical records, not independent scientific confirmation** of those assertions. The original estates keep their notices and are **not automatically relicensed under the repository's Apache-2.0 software license**. The modern architecture index is an interpretation linked back to original file paths and hashes.

## Research architecture and topical reference

| Area | Detailed reference |
|---|---|
| Operator graph, tiers and module interfaces | [Architecture](docs/ARCHITECTURE.md) |
| Cue conditioning, future rehearsal and mnemonic learning | [Research topics](docs/RESEARCH_TOPICS.md) |
| VR/AR, communication, BCI, learning and accessibility use cases | [Applications](docs/USE_CASES.md) |
| Symbols, glyphs, cue genealogy, sensory modalities, typed program definitions | [Glossary](docs/GLOSSARY.md) |
| Exact experiments, baselines, confidence intervals and known negative results | [Benchmark index](docs/BENCHMARKS.md) |
| Answers to practical institutional and scientific questions | [FAQ](docs/FAQ.md) |
| Evidence provenance and historic RSOS/RSIA/RSX/RSSO specification boundaries | [Sources and release policy](docs/SOURCES_AND_RIGHTS.md) |
| Technical discoverability, citation and search measurement | [Discovery and publishing guide](docs/DISCOVERY_PLAN.md) |

## Research collaboration

We welcome independent work from groups in **human–computer interaction, cognitive science, learning science, adaptive machine learning, neurotechnology, computational psychiatry (methods only until clinically validated), accessible computing, privacy engineering, and trustworthy AI systems**.

Priority collaboration opportunities: reproduce the code; introduce stronger baselines; calibrate on real nonclinical EEG/HRV observations; evaluate neutral mnemonic learning; run delayed-context transfer experiments; formally analyze the state machine; or independently review provenance/security properties.

Please open a GitHub issue referencing the relevant benchmark or module. No clinical or product adoption claims are requested from collaborators.

## Publication, citation, and license status

**Historical estates and original records:** The underlying RSOS, RSIA, RSX and RSSO source archives document prior specifications. They may include historical proprietary notices. Preserve those records intact and publish intentionally, with clear current permissions and privacy review.

**Public software:** The newly released research implementation and corresponding project documentation are available under [Apache License 2.0](LICENSE) unless a file states otherwise. Historical estate texts remain separately governed records, not automatically relicensed.

**Citation:** See [CITATION.cff](CITATION.cff). The canonical public repository is https://github.com/r-a-elu-architecture/RSOS-Multimodal-Cue-Framework. The first tagged research preview has the version DOI [10.5281/zenodo.24143732](https://doi.org/10.5281/zenodo.24143732). The fixed archived tag references commit `133d472`; the author-citation update to `R. A. Elu` was added to the living repository afterward. Verify and correct the creator metadata on Zenodo directly if needed.

**Scientific boundaries:** No verified therapeutic efficacy, EEG-based identification of specific beliefs, automatic physiological transformation, or universal superiority over generic personalization models is claimed. No unreviewed private conversation exports should be placed in the repository.

---

**RSOS — Programmable cues. Evidence-gated adaptation. Reproducible research.**