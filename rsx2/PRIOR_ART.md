# Prior-art search: the RSX/2 combination

Date: 13 November 2026. Scope: web search of papers (arXiv, ACM, IEEE, Frontiers, JMIR, Wellcome Open Research), patents (USPTO full text, patent aggregators) and products. Fourteen searches, one per component and several on the combinations. This is a first pass, not a full freedom-to-operate or patentability search. That would need a patent attorney and the EPO, USPTO and WIPO databases.

## 1. The combination being checked

RSX/2, together with the existing RSX cue layer, does the following, in this order:

1. A person's message is decomposed into many separate directions (the 9–17-vector claim), with pasted material set aside.
2. Each direction is typed, then mapped to **operators that are typed by the cognitive layer they act on**, across 11 layers.
3. The operators are compiled into a **staged program**: a gate, then phases with IF, ELSE and UNTIL, then a close.
4. Each phase advances only when **body and layer targets are met**: closed loop on arousal, distress and HRV, with EEG as the intended sensor.
5. **Ten laws** govern execution: conflict separation, time windows, a simulation before every live run, consent, continuity across sessions, time-of-day scheduling, rescues, a hash-chained audit, and purge with proof.
6. The program runs as **multisensory cues on a wearable**: haptics, thermal, display, and the RSX cue tiers.
7. Every operator keeps **lineage back to the clause of the message** it came from. A **per-vector audit** feeds **NEXT**, which writes the successor program.
8. Planned: **archetype agents** run the phases.

## 2. Component by component

| # | Component | What exists | Verdict |
|---|---|---|---|
| A | Closed-loop adaptation to EEG or physiology | Research frameworks are long established: NFBLab, BCI2000, OpenViBE<sup>1</sup>. In products, Apollo's SmartVibes AI is described as a closed-loop system that responds automatically to sleep disturbances<sup>2</sup> | **Exists** |
| B | Language models generating physiology-adaptive sessions | EarStreAM monitors HR and HRV from an earable and starts an LLM-generated meditation when stress rises<sup>3</sup>. NieNie combines HRV with LLM guidance and rhythmic squeezing<sup>4</sup>. NeuroChat adapts an LLM tutor to EEG engagement<sup>5</sup>. MindMelody uses an EEG-driven loop for music<sup>6</sup>. NeuroSkill is an agentic system built on wearable brain-computer-interface signals<sup>7</sup> | **Exists** |
| C | A language for closed-loop protocols | NFBLab describes protocols in an internal XML language<sup>8</sup>. neuroConn's LoopIT runs RALGOL, a purpose-built on-device language for closed-loop control<sup>9</sup>. Turbo-Satori defines stimulation protocols<sup>10</sup> | **Exists as a category.** These describe signal processing and stimulus timing, not psychological operators |
| D | Interventions typed by their mechanism of action | Behaviour-change science has a 93-technique taxonomy (BCTTv1), a machine-readable Mechanism of Action ontology with 261 entities, and the Theory and Techniques Tool, which links techniques to mechanisms<sup>11, 12</sup> | **Exists conceptually.** This is the closest prior art to "operators typed by the layer they act on". It is a reporting and design vocabulary, not an executable language with run-time conditions |
| E | Decision rules over sensed variables | Just-in-time adaptive interventions (JITAI) are defined by decision points, tailoring variables, intervention options and decision rules<sup>13</sup>. JITAI-Twin (2026) uses a digital twin to test decision rules before deployment<sup>14</sup> | **Exists.** RSX/2's IF/UNTIL phases are decision rules. GhostPass is a per-person, per-run form of the twin idea |
| F | Text to haptics, scent or multisensory output | HapticGen (CHI 2025) and HapticLDM (2026) generate vibration from text<sup>15, 16</sup>. "Touched by ChatGPT" drives a 5×5 vibration sleeve from an LLM<sup>17</sup>. AromaGen generates scent mixtures from free-form text through a neck-worn dispenser<sup>18</sup> | **Exists** |
| G | Multisensory wearables that adapt to sensors (patents) | US 11,554,244 claims wearable multimodal stimulation with monitoring and adjustment; its claims require *charge-based* (electrical) stimulation plus a second modality<sup>19</sup>. US 10,912,915 describes multisensory sessions (sound, vibration, scent, VR) with breathing and heart-rate sensors feeding back<sup>20</sup>. US 11,422,626 covers outputting tactile, thermal, olfactory, visual and auditory stimulation to a user<sup>21</sup> | **Exists.** RSOS uses no electrical stimulation, which appears to put it outside US 11,554,244's independent claims. Only a patent attorney can confirm that |
| H | Provenance and lineage from prompt to action | PROV-AGENT (IEEE e-Science 2025) treats AI agent actions as first-class elements of a provenance graph<sup>22</sup>. Industry gateways record lineage from the user request to every tool call, with hash chains for tamper evidence<sup>23</sup> | **Exists for software actions.** Lineage that ends in a *body intervention and its measured effect* was not found |
| I | Several intents in one message | Multi-intent detection is an established NLP task. Its standard datasets (MixATIS, MixSNIPS) mostly hold one to three intents per utterance<sup>24</sup> | **Exists for 1–3 intents.** Not found: dense 9–17-direction messages used to drive an intervention program |
| J | Archetype and persona multi-agent systems | Jungian-type personality frameworks for LLM agents (JPAF)<sup>25</sup>. LLM "archetypes" in agent-based models<sup>26</sup>. Agent committees built from archetype families<sup>27</sup>. Internal Family Systems is widely used as a metaphor for multi-agent design<sup>28</sup> | **Exists as personas and metaphors.** Not found: archetype agents that each run a phase of a physiological intervention executed on a device |

## 3. The combination

Across these searches, **no single system combines all of:**

1. decomposing one message into many typed directions;
2. compiling them into an executable intervention program whose operators are typed by the cognitive layer or mechanism they target;
3. phases that advance only when sensed body and layer targets are met, under explicit safety laws (gate, simulation before a live run, rescues, hash-chained audit, purge with proof);
4. multisensory cue output on a wearable;
5. lineage from every operator back to the clause of the message, with a measured per-vector audit that writes the successor program;
6. archetype agents running the phases (planned).

The closest neighbours each cover two or three of these:
- **EarStreAM / NieNie:** physiology, plus LLM-generated content, plus a device;
- **NeuroSkill:** wearable brain-computer-interface signals plus an agentic LLM harness;
- **BCIO / TaTT:** typed techniques and mechanisms, but not executable;
- **JITAI-Twin:** decision rules plus simulation, but without language input or typed operators;
- **PROV-AGENT:** lineage, but for software actions only.

## 4. What can honestly be said, and what can't

**Can be said (with the date and scope of the search):**
> "In a search of papers, patents and products in November 2026, we found no system that combines multi-direction message decomposition, operators typed by the cognitive layer they act on, closed-loop phases gated on sensed body and layer targets under explicit safety laws, multisensory wearable output, and per-operator lineage from the message to the measured effect."

**Should not be said:**
- "First closed-loop system", "first LLM-driven biofeedback", "first text-to-haptics", "first intervention typology". Each of these exists.
- "Unprecedented" without the scope and date. Absence in one search is not proof of absence.
- Any claim of human effectiveness. All RSX/2 results are simulated.

**Patent note:** each component exists, so a patent on the combination would turn on non-obviousness. That is a question for a patent attorney, ideally before any public description of the full combination. Publishing first (for example the Zenodo release) creates prior art against others, but it also starts grace-period clocks that differ by jurisdiction.

## 5. What this changes in the design

1. **Map the 11 RSX layers and 34 operators to the Mechanism of Action ontology** (BCIO MoA IDs) and to BCTTv1 techniques where they fit. This anchors RSX/2's typing in an existing, peer-reviewed vocabulary. It makes the typing checkable, and it makes the executable-language part clearly the new contribution.
2. **Describe RSX/2 phases in JITAI terms** (decision points, tailoring variables, decision rules), so researchers recognise it immediately. GhostPass should be presented as a per-run digital twin, citing JITAI-Twin.
3. **Make the audit chain PROV-compatible**: export the lineage as W3C PROV or OpenTelemetry spans, so it plugs into standard provenance tools.
4. **Lean the originality on the combination and its two strongest parts:**
   - lineage from message to body (no prior art found);
   - archetype agents running device phases (no prior art found).
5. **Keep electrical stimulation out of scope**, which keeps clear of US 11,554,244's independent claims (to be confirmed by an attorney).
6. **Benchmark the translator against multi-intent detection.** Report how often real messages exceed the 1–3 intents of the standard datasets. That is the measurable side of the 9–17 claim.

## Sources

1. A framework for closed-loop neurofeedback for real-time EEG decoding — https://www.biorxiv.org/content/10.1101/834713.full.pdf
2. Apollo Neuroscience profile (SmartVibes AI) — https://cbinsights.com/company/apollo-neuroscience
3. EarStreAM: A Closed-Loop Earable System for Personalized Stress-Adaptive Meditation — https://arxiv.org/pdf/2609.19127
4. NieNie: Adaptive Rhythmic System for Stress Relief with LLM-Based Guidance — https://arxiv.org/pdf/2510.17534
5. NeuroChat (Baradari, Kosmyna et al.) — https://arxiv.org/pdf/2503.07599v2
6. MindMelody: A Closed-Loop EEG-Driven System for Personalized Music Intervention (review) — https://www.themoonlight.io/es/review/mindmelody-a-closed-loop-eeg-driven-system-for-personalized-music-intervention
7. NeuroSkill (review) — https://www.themoonlight.io/review/neuroskilltm-proactive-real-time-agentic-system-capable-of-modeling-human-state-of-mind
8. NFBLab (Frontiers in Neuroinformatics, 2018) — https://www.frontiersin.org/journals/neuroinformatics/articles/10.3389/fninf.2018.00100/epub
9. LoopIT RALGOL guide (neuroConn) — https://loopit.neurocaregroup.com/html/ralgol-guide.html
10. Turbo-Satori stimulation protocol — https://download.brainvoyager.com/Satori/TSI/TSIUsersGuide/10_StimProt.html
11. Linking behaviour change techniques to mechanisms of action (Wellcome Open Research, 2025) — https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12596556/
12. An ontology of mechanisms of action in behaviour change interventions — https://www.aminer.org/pub/65f124c513fb2c6cf6001081/an-ontology-of-mechanisms-of-action-in-behaviour-change-interventions-version-peer
13. Towards a Holistic Approach to Designing Theory-based Mobile Health Interventions (JITAI framework) — https://arxiv.org/pdf/1712.02548
14. Digital Twins for Just-in-Time Adaptive Interventions (JMIR 2026) — https://www.jmir.org/2026/1/e72830/PDF
15. HapticGen (CHI 2025) — https://camps.aptaracorp.com/ACM_PMS/PMS/ACM/CHI25/524/6262bdae-d6c0-11ef-ada9-16bb50361d1f/OUT/chi25-524.html
16. HapticLDM — https://arxiv.org/abs/2605.09971
17. Touched by ChatGPT — https://web3.arxiv.org/pdf/2501.07224
18. AromaGen — https://arxiv.org/html/2604.01650
19. US 11,554,244 — https://mtec-sc.org/patents/US-11554244-B2
20. US 10,912,915 — https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10912915
21. US 11,422,626 — https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11422626
22. PROV-AGENT — https://arxiv.org/pdf/2508.02866v3
23. Data lineage and provenance tracking for AI agent tool calls — https://gravitee.io/corpus/gen-1159/computational-informatics/data-lineage-and-provenance-tracking-for-ai-agent-tool-calls-and-llm-traffic.html
24. Multi-Intent Spoken Language Understanding: Methods, Trends, and Challenges — https://arxiv.org/pdf/2512.11258
25. Structured Personality Control and Adaptation for LLM Agents (JPAF) — https://arxiv.org/pdf/2601.10025
26. On the limits of agency in agent-based models (LLM archetypes) — https://arxiv.org/pdf/2409.10568
27. Process-Aware Fairness Diagnosis for LLM-based Multi-Agent Decision Systems (archetype families) — https://arxiv.org/pdf/2609.02092
28. Therapy and AI architecture (IFS and multi-agent systems) — https://poqpoq-adobe.pages.dev/adobe/therapy-and-ai-architecture/
