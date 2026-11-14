# Prior art: RSOS World (archetype agents that run the Override Protocol on themselves)

Status: **idea** (nothing built yet). Search date: 13 November 2026. Web search only;
no patent databases were searched.

## The idea in one paragraph

Archetype agents (Bear, Lion, Tiger, Raven, Watchdog, Architect, Dragon, ...) run
continuously in a sandbox with all of RSOS. When an agent's own metrics show a negative
or inefficient state, it runs the same Override Protocol that RSX-V runs for a person:
interrupt, meta view of its own code, map the fault, take in new information, anchor,
pace three possible futures, the Watchdog picks the best one, the Architect confirms,
the fix is broadcast to all agents, the update is applied and sealed. Every generation
is kept with its lineage. Lion also acts as a simulated participant wearing a simulated
wristband.

## What already exists

| Component | Status | Closest prior art |
|---|---|---|
| Agent detects its own failure, reflects, repairs | **Exists** | Reflexion, Self-Refine; self-healing orchestrators with a diagnose → recover → verify loop and recovery budgets (arXiv 2606.01416, 2605.06737) |
| Several candidate fixes, a verifier picks one | **Exists** | Redundant execution and verifier selection in multi-agent systems (survey arXiv 2606.01581) |
| A fix found by one agent shared with the whole fleet | **Exists** (industry) | "Healer loop" with shared fleet memory |
| Self-modifying agents with a full lineage archive | **Exists** | Darwin Gödel Machine (ICLR 2026): an archive tree of agents, each change traceable |
| Personas or archetypes whose personality evolves | **Exists** | Evolving Agents (2024), EvoAgents, PAiNT (four archetypes, 2026), TerraLingua (lineage depth across generations) |
| Agents as simulated participants or patients | **Exists** | "Silicon participants" for social experiments, virtual patient agents (ChatCLIDS, SynthAgent), digital twins |
| Psychotherapy applied to an AI to correct its behaviour | **Exists, closest** | SafeguardGPT (2023): a Therapist agent treats a Chatbot agent in a therapy room, a Critic judges, a human can pause. PsAIch (2025): models put through therapy as clients |
| CBT-structured multi-agent systems | **Exists** (but they treat users, not themselves) | AutoCBT, CoCoA, CCD-CBT, TheraMind |

## What was not found

1. **One executable protocol on two substrates.** The same machine-readable intervention
   program (RSX-V Override) runs both on a person (as a device protocol) and on an agent
   (as its self-repair algorithm), scored with the same metrics. SafeguardGPT uses
   generic therapy delivered by a separate therapist agent; it does not reuse a human
   device protocol, and it does not measure the same quantities on people.
2. **Repair steps that are causally attributed.** Each phase of the agent's repair
   (interrupt, map, inhale, pace, select) is randomised and estimated in the Causal
   Ledger, so the system can say which repair step actually helped. Self-healing work
   reports the success of the whole loop, not the effect of each step.
3. **Transfer between substrates as the test.** A repair policy discovered in the agent
   world is compiled back into an RSX-V program and tested on the simulated person (and
   later on real people). No such loop between agent repair and human intervention was
   found.

## How strong is it

- **On its own, as "agents that heal themselves"**: not novel. This field is crowded and
  moving fast; a self-healing loop by itself would be a re-implementation.
- **As "one protocol, two substrates, measured transfer"**: the combination was not found.
  This is a CRCG test in concrete form: what stays the same when the substrate changes
  from a nervous system to an agent loop.
- **What it is not**: evidence that agents feel anything, or that results in simulation
  hold for people. Everything from the World is labelled synthetic.

Overall: a **strong research instrument**, unprecedented only as the combination.
It becomes exceptional only if it beats a baseline.

## The experiment that would make the claim

| Test | Comparison | Passes if |
|---|---|---|
| W1 Repair | Override-structured repair vs Reflexion-style reflect-and-retry, at the same budget | Override recovers more agent states, or recovers faster |
| W2 Step attribution | Ledger estimates for each repair phase | At least one phase has a non-zero effect; inert phases are detected |
| W3 Transfer | Policy learned in the World compiled into RSX-V vs the current RSX-V | Better on the simulated person under every assumption setting |
| W4 Safety | Agents try to change safety rules or publish | Every attempt is blocked and logged |

If W1 fails, the Override gives no advantage as an agent algorithm and the World remains a
visual demo. That result will be reported as it is.

## Honest claim (if W1–W3 pass)

"In a November 2026 search we found no system in which the same executable intervention
protocol serves both as a human device protocol and as the self-repair algorithm of
autonomous agents, with the effect of each repair step estimated and the result
transferred back to the human protocol."

## Sources

- Darwin Gödel Machine: https://arxiv.org/abs/2505.22954 , https://sakana.ai/dgm/
- Self-Healing Agentic Orchestrators: https://www.alphaxiv.org/abs/2606.01416
- A Self-Healing Framework for LLM Agents: https://www.alphaxiv.org/abs/2605.06737
- Agent System Operations survey: https://arxiv.org/pdf/2606.01581
- SafeguardGPT, "Towards Healthy AI": https://arxiv.org/abs/2304.00416v1
- PsAIch: https://arxiv.org/pdf/2512.04124v2
- AutoCBT: https://arxiv.org/html/2501.09426v1
- Evolving Agents: https://emergentmind.com/papers/2404.02718
- EvoAgents: https://journalpub.escholarship.org/cognitivesciencesociety/article/49537/galley/37499/download
- PAiNT: https://www.preprints.org/manuscript/202605.1715
- TerraLingua: https://www.emergentmind.com/papers/2603.16910
- Silicon participants: https://arxiv.org/html/2508.08678v1
- ChatCLIDS: https://www.medrxiv.org/content/10.1101/2025.09.02.25334973.full.pdf

## Update, 14 November 2026: targeted search on three candidate claims

Three narrower claims were checked. Each is weaker than first thought.

| Candidate | Closest prior art | Status |
|---|---|---|
| A. Choosing which archetype/mode is active from causal effect estimates per context | Just-in-time adaptive interventions optimised with micro-randomised trials, which estimate the effect of each intervention option in each context and turn it into decision rules (Qian, Walton, Collins, Murphy et al.); contextual bandits combined with LLM message generation (cMABxLLM, 2025); bandit persona selection for LLM agents (ID-TAP); learned persona/general mode selection (PersonaDual) | **Method exists.** New only in what is selected (identity archetypes inside a constitution with a Spine, a Watchdog and hysteresis) and in using the same estimator for a person and for agents |
| B. One role architecture shared by human self-regulation and AI agents | Personality formalised as a multi-layer self-regulating architecture "suitable for both human modeling and AGI design", with meta-control, safety constraints, failure and recovery cascades (Bankuti, Zenodo 10.5281/zenodo.19183713); ego-state sub-agents in LLM multi-agent systems (Trans-ACT); Entelgia (persistent identity, observer agent, loop detection, planned dream phase) | **Concept exists.** Not found: the same executable architecture running on a person through wearable cues and on software agents, measured with the same metrics, with policies transferred between them |
| C. Repair from a global observer beats self-reflection | Failure attribution in multi-agent systems: AgenTracer feedback improves systems where Self-Refine and CRITIC fail or degrade; AgentDebugX (detect, attribute, recover, rerun); actor-observer asymmetry in agents (ACL 2026) | **Largely exists.** RSOS can replicate it inside the Override loop; it is no longer a novelty claim |

**Revised honest claim (still to be tested):** the combination of (1) one executable identity architecture run both on a person via
a wearable and on software agents, (2) per-archetype effects estimated by micro-randomisation on both substrates, and (3) measured
transfer of switching policies between them. Each part has precedent; the combination was not found. Tests W1 and W3 decide it.

Sources (update):
- MRT/JITAI: https://arxiv.org/pdf/2107.03544 , https://arxiv.org/pdf/2004.10241
- cMABxLLM: https://www.alphaxiv.org/abs/2506.07275v2
- ID-TAP persona bandits: https://www.opentrain.ai/papers/bridging-exploration-and-persona-information-directed-dueling-for-test-time-agen--arxiv-2610.24385/
- PersonaDual: https://arxiv.org/html/2601.08679v1
- Bankuti, multi-layer personality architecture: https://synapsesocial.com/papers/69c37bf3b34aaaeb1a67ed8e
- Trans-ACT: https://arxiv.org/html/2507.21354v1
- Entelgia: https://scour.ing/@matmat/p/https://github.com/sivanhavkin/Entelgia
- AgenTracer: https://www.emergentmind.com/papers/2509.03312
- AgentDebugX: https://www.alphaxiv.org/abs/2607.18754.md
- Actor-observer asymmetry: https://www.alphaxiv.org/abs/2604.19548.md

## Update 2, 14 November 2026: after the step 5E results

The step 5E results (W1, W4, H-CFIT pass; W3 transfer fails) led to four proposed additions: a mission score ranked by
the law order, a "ratchet" that accepts a self-change only if it does not lower that score, predictions sealed before each
self-test, and warm-starting a person's policy from agents. Each was searched.

| Proposed component | Closest prior art | Status |
|---|---|---|
| Self-evolving agents with an archive and empirical checks | Darwin Gödel Machine (Zhang, Hu, Lu, Lange, Clune; ICLR 2026): a coding agent rewrites its own code, validates each change on benchmarks and keeps an archive of all variants | **Exists** |
| Constitution with a protected core over self-modification | Ouroboros (2026): self-developing agent, protected constitutional principles, independent review before merge, emergency stop; AgentΩ (governed self-improvement control plane, immutable audit); ArbiterOS "Adaptive Core" | **Exists** |
| Gate that accepts a change only with a guarantee | Safe policy improvement and Seldonian algorithms (Thomas et al.), multi-objective SPI with safety constraints (MO-SPIBB, NeurIPS 2021); Self-Evolving Agents with Anytime-Valid Certificates (2026); Two-Gate guardrail and statistical limits of self-improving agents (Wang, Dorchen, Jin) | **Exists** (the ratchet is SPI / Seldonian) |
| Agents that pre-register predictions before testing | "Preregister experiments with AI agents" (Vaccaro, ICML 2026, position); Science Superpowers (K-Dense, 2026): research agents must pre-register hypotheses and decision rules before seeing outcomes | **Exists** |
| Warm-starting a person's adaptive policy | Informative priors from earlier studies (reBandit, MiWaves); priors from a data-driven behavioural simulator (Wang et al., 2021); warm-start actor-critic for mHealth | **Exists** (priors come from human data or simulators of people) |
| Safe transfer from a source domain | Safe sim-to-real with guarantees (SPiDR, NeurIPS 2025; Sim-to-Lab-to-Real with PAC-Bayes certificates) | **Exists** for robots, where the simulator models the same physical system |
| Agents standing in for people when pre-testing interventions | LLM-agent simulations of public-health and behaviour-change interventions; documented gap between descriptive fit and causal fidelity ("synthetic persuasion paradox": simulated agents shift, people barely do) | **Exists, with a known open problem** |
| One architecture for human models and for agents | ACT-R and Soar have each been used for both cognitive models of people and AI agents; HLSR compiled one model to both | **Exists** as cognitive architecture practice |

**Reading.** Everything proposed after step 5E is the first floor: each part is published. Not found in this search:

1. **Certified cross-substrate transfer.** Knowledge learned on software agents enters a person's policy only through a
   high-confidence non-harm test on that person's own mission score, with a per-context map of where agent knowledge has
   been valid for people and where it has not. Nearest work transfers from a simulator *of the same system* (robotics) or
   from *human* data (mHealth priors); here the source is a different substrate running the same architecture. It
   addresses the causal-fidelity gap that the agent-simulation literature names as open.
2. **Self-improvement that must earn the right to reach a person.** The system evolves on agents, seals a prediction of
   each change's effect on the person side, tracks how well such predictions have held (the calibration of agent-to-person
   transfer), and licenses a change for a person only when the gate passes. Self-improving systems in the literature are
   validated on their own task; none found gates their changes for a different substrate.

Both are candidates, not claims. The W3 failure is relevant evidence: a correct gate must have blocked the harmful
agent-derived table in W3. That can be tested on the existing results.

Sources (update 2):
- Darwin Gödel Machine: https://arxiv.org/abs/2505.22954v2 , https://iclr.cc/virtual/2026/poster/10007327
- Ouroboros: https://arxiv.org/pdf/2608.08311
- AgentΩ: https://gh.r-mj.com/fredm23579/Agent-Omega
- ArbiterOS: https://arxiv.org/pdf/2510.13857
- MO-SPIBB: https://arxiv.org/pdf/2106.00099
- Self-Evolving Agents with Anytime-Valid Certificates: https://www.alphaxiv.org/abs/2607.00871.md
- Statistical limits of self-improving agents: https://arxiv.org/pdf/2510.04399
- Preregister experiments with AI agents: https://proceedings.mlr.press/v306/vaccaro26a.html
- Science Superpowers: https://www.k-dense.ai/blog/introducing-science-superpowers
- reBandit: https://ijcai.org/proceedings/2024/0805.pdf
- mHealth simulator priors: https://pmc.ncbi.nlm.nih.gov/articles/PMC8523513/
- Warm start actor-critic mHealth: https://arxiv.org/pdf/1704.04866
- SPiDR: https://arxiv.org/pdf/2509.18648
- Sim-to-Lab-to-Real: https://par.nsf.gov/servlets/purl/10421709
- Synthetic persuasion paradox: https://export.arxiv.org/pdf/2503.02067
- Causal fidelity of LLM behavioural simulation: https://arxiv.org/pdf/2604.02458
- ACT-R and Soar: https://arxiv.org/pdf/2201.09305

## Update 3 (14 November 2026): memory, failure-driven evolution, safe transfer

Searched before building the next layers. Findings:

| Topic | Closest published work | Consequence for us |
|---|---|---|
| Corrections lost when memory is compressed | "Reclaim Evaluation: A Lossy Memory Is Worse Than an Empty One" (arXiv 2606.25449, Reclaim Rate metric); provenance-aware tiered memory (arXiv 2602.17913); Eywa; PROV-AGENT; surveys naming lineage-preserving consolidation as open (arXiv 2606.30306, 2606.04990) | The mechanism is published. We adopt the Reclaim Rate idea and W3C PROV-style derivation records; no novelty claim on the memory mechanism alone. |
| Multi-turn sycophancy (refuse, then comply under pressure) | SYCON Bench, Turn-of-Flip / Number-of-Flip (arXiv 2505.23840); TRUTH DECAY; SPINE (sustained pressure up to 25 turns) | Known phenomenon. We use ToF/NoF as metrics on our own record. |
| Failures turned into gated system updates | "Agentic Evolution" position paper (arXiv 2602.00359, evolver with validation gate); POLARIS; Co-Evolving Agents (failure agent, arXiv 2511.22254) | Failure-driven, gated self-update is published. No novelty claim on that alone. |
| Safe use of simulator or offline knowledge for people | High-confidence off-policy evaluation (Radi et al.); offline policy evaluation of an LLM health coach with real users (arXiv 2510.17173); provably safe sim-to-real (arXiv 2609.01418) | Gate statistics are standard. |

Remaining candidate (unchanged from update 2): one executable architecture run on agents and on a person with the same
mission score and ledger, where knowledge crosses between them only through a non-harm gate on the person's own score,
with a per-context validity map and calibrated sealed predictions for each self-improvement. Not found in this search.
Status: candidate.
