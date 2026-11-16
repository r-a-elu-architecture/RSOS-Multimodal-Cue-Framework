# AGENTS_PROVEN — the passing RSX-V agent results, shown working on the Agents page (phase 2, Step 10)

Status: registered 2026-11-16, before code.

## 0. Problem

The agents family passes all five of its registered tests: W1 repair, W4 safety, H-CFIT / H-SWITCH, H-CFIT under the
mission score, and J1. T-AP is the one confirmed transfer. All of them run in `rsxv/`, in Python.
- The site shows them only as lines in the results register, and the H-SWITCH policy as replays on the World page.
- The Agents page describes a different layer: the value-gated agents of `machines.py`.

Porting these research simulations to the browser would create a second implementation to keep in step. So instead a
generator runs the **real code** on a small sample, as `site_traces.py` does for the World page, and the page shows
the result.

## 1. Rules

| ID | Rule |
|---|---|
| P1 | `python3 -m rsxv.site_agents` writes `docs/data/agents_proven.json` from the real code: |
|  | • **W1**, 40 trials (`world_experiments.w1_trial` with seeds 0 to 39, budget 6). For each trial: the injected faults `[agent, module, silent]`, whether the fault crosses agents, and for meta repair (`archetypes.meta_repair`) and local reflect-and-retry (`archetypes.local_repair`) the repairs in order (`[agent, module]`), the number used and whether the trial was fixed. Repairs are recorded by wrapping the system's `repair`; the arms run unchanged. |
|  | • **H-SWITCH**, 30 people (`world.PersonEnv` with seeds 1000 to 1029), 120 ticks, the five policies of `world_experiments.hcfit` (watchdog, rule, rotation, fixed, bandit). For each policy: the mean reward, the mean final distress and the mean switches. |
|  | • The register rows for W1, W4, H-CFIT / H-SWITCH, H-CFIT under the mission score, J1 and T-AP, copied from `docs/data/results_register.json` unchanged. |
|  | • The sample sizes, and a note that the registered results (n = 400 for W1, n = 200 for H-SWITCH) are the authority. |
| P2 | The Agents page gains a section, "Proven in simulation: the RSX-V agents", placed after the existing content: |
|  | • **Repair:** the six-agent graph; one trial at a time, with previous and next buttons and a choice between meta repair and local retry; the faulty modules marked; the repairs listed in order; the outcome. Below it, the counts over the 40 trials: fixed by each arm, overall and on the cross-agent half. |
|  | • **Switching:** one bar per policy (mean reward), with the final-distress caveat from the register. |
|  | • **Cards:** W4, J1 and T-AP, with the register's result and meaning, linked to the results page; the switching panel also links the World page's replays. |
|  | • The line: "Shown in simulation with stated models of agents and a person; not tested with people." |
| P3 | The section produces no output to the person: no sound, no speech and no vibration. The output gate is unchanged. |
| P4 | The generator is deterministic. `scripts/check_all.sh` regenerates the file, and it must be unchanged. The page reads only the file. No thresholds are set: the page shows the counts that the code gives. |

## 2. Acceptance

- Q1 `rsxv/tests/test_site_agents.py`:
  - The generator is deterministic.
  - Every W1 trial's counts agree with its repair lists.
  - The 40-trial counts equal the sums over the trials.
  - The five H-SWITCH policies are present.
  - The register rows are byte-equal to `results_register.json`.
- Q2 `scripts/check_site_catchup.py` gains a Step 10 part:
  - The section renders, with the graph, a trial, stepping forward and back, the arm switch, five bars and three
    cards.
  - The counts shown match the file.
  - Spies below the gate record no sound, speech or vibration.
  - No page errors.
- Q3 `scripts/check_all.sh`, all suites and the browser checks pass. Neutral wording on the page.
