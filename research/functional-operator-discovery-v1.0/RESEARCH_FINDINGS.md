# Empirical Report: Functional Operator Assembly v1.0

## Strongest NEW source finding

The user-provided RSOS and RSSO tier bodies are not distinct independently developed libraries. Once their respective introductions and line endings are normalized, the RSOS tier body of **365,484 characters** is an exact prefix of the RSSO body. Both contain **317 matching tier headings** and **292 unique tier identifiers**; RSSO then appends 2,083 more characters. Different legal/system wrappers do not multiply the tier mechanisms.

## Most impactful measured assembly on actual historical data

This study uses 9,000 recovered source messages in 246 conversations (7,205 assistant; 1,795 user), a selected export, not the entire claimed longitudinal corpus. Of those, 1,571 assistant messages have a directly observed user-message parent in the same conversation, across 100 conversations.

Retrospective task: given the user message and optionally its known immediately preceding assistant message, predict the presence of 13 documented *lexical operator categories* in the next recorded assistant message. The response text is used **only to generate ground-truth lexical labels**; model inputs use earlier or current messages. Each sample's assistant response is an observed record, not an intervention outcome. Targeted categories are selected for nonextreme prevalence. The corpus is heavily nonrandomly enriched for RSOS terms.

### Five group-held-out tests (source-aware direct-user-only vs word TF-IDF)

Mean across five splits:

| Representation | Mean macro AP | Mean Brier |
|---|---:|---:|
| Word TF-IDF | 0.459525 | 0.174884 |
| Word + source additive indicators | **0.500559** | **0.164860** |
| Word + all 105 pairwise interactions | 0.483903 | 0.167700 |

Source-additive indicators reduce average Brier by **0.010024** (5.73%) versus word TF-IDF. Adding all pairwise interactions **hurts** versus additive. Across the five group splits, train/test conversation sets are disjoint; splits overlap one another and are *not* independent population replicates.

### Stronger lexical baselines (forward holdout)

In a 25-conversation forward split, word+character TF-IDF macro AP **0.455209**, Brier **0.169838**; with user-operator flags, macro AP **0.535399**, Brier **0.159368**. Comparison against shuffled / decoy flags favors specific source-derived inputs rather than arbitrary extra dimensions.

### Strongest strict contextual holdout

The strict follow-up uses the *same current and prior text* for baseline and enriched models, removes **one** exact duplicate user input from training, limits the lexical input window equally, and holds out 25 later-starting conversations (259 response pairs):

| Model | AP | Brier |
|---|---:|---:|
| Current + immediate preceding assistant text, word+char TF-IDF | 0.480377 | 0.163686 |
| Above + current user operator flags | 0.552751 | 0.153775 |
| Above + current user and preceding assistant operator flags | **0.554699** | **0.149174** |

Full vs lexical-only: Brier delta **-0.014512**, participant analog = conversation-cluster bootstrap 95% CI **[-0.022584, -0.007192]**, 4,000 group resamples (25 clusters). Full vs current-only flags: Brier delta **-0.004600**, CI **[-0.007958,-0.001402]**. These are *exploratory post-hoc uncertainty estimates*, not preregistered hypothesis-test probabilities.

The same direction was observed on two other non-overlapping conversation-held-out samples (fresh seeded group splits), though all samples come from the same historical archive. The ancestry-link feature helps predict *assistant text* even though the previous assistant text is available to the lexical baseline; it does not prove the parent link's biological or psychological significance.

### Post-hoc operator importance

Permuting one operator at a time at test time (while retaining the trained model) caused the biggest Brier increase for `visual_glyph` (+0.00602), `metaphor` (+0.00601), and `watchdog_contain` (+0.00597), then `memory_recall` (+0.00274) and `identity_archetype` (+0.00268). These are **model feature diagnostics**, affected by feature correlations and language repetition, not estimates of effects on humans. All figures are in `results/posthoc_operator_importance.csv`.

### Critical limitations

- Source-era assistants repeat user vocabulary: operator labels are extracted by regex from their outputs. This is a next-text-operator forecasting task, not proof of an autonomous cognitive architecture or any internal model changes.
- The archive selected only 9,000 messages from a larger claimed dataset, and 100 conversations have linked samples. It may overrepresent assistant generated formulas and repeated templates.
- Cross-conversation paraphrases and near duplicates may remain; only exact user text duplicates were removed in the strict split. Other splits did not remove duplicates.
- The model family/hyperparameters and feature registry were developed using this corpus: no untouched external replication, no independent third-party annotation.
- Macro AP differences can be sensitive to rare family prevalence and held-out conversation composition. Brier intervals are clustered, but not independently prospective.
- Stronger transformer models, modern event extraction models, and optimized contextual retrieval were not run. **'Outcompetes everything' is not supported.**
- Real WESAD-style human physiological data does not contain RSOS interventions or psychological cue ancestry; such a dataset cannot validate therapeutic efficacy from these results.

### Actual execution evidence

The typed assembler is a pure Python, voluntary suggestion router. Its 12 software tests, including an exhaustive 384-combination control grid, pass. An equally implemented generic typed controller can satisfy the same contract: these tests verify an executable source-inspired composition, not proprietary superiority. No actual smell, taste, EEG, haptic or other stimulus was delivered by this code.