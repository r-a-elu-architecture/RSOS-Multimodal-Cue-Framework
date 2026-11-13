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
