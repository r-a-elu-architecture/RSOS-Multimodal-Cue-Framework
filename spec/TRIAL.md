# TRIAL: personal randomised experiments

Status: built and tested in simulation; effect unproven in people. Implementation: `rsso/rsso/trial.py` and `docs/js/trial.js` (identical, tested), page `docs/trials.html`. Simulation results: [`rsso/results/trial.md`](../rsso/results/trial.md). Protocol kit: [`kits/TRIAL_PROTOCOL_KIT.md`](kits/TRIAL_PROTOCOL_KIT.md). Cognitive tests: [CHECKS.md](CHECKS.md). Roadmap items 33, 45, 49, 52, 53 and 64.

## 1. Why

The claims register holds 101 claims. Most can be tested by one person comparing two ways of practising, provided the person does not choose which way to use when (that choice would carry their mood and expectations into the result). TRIAL makes these comparisons the default way to use RSOS: the system chooses at random, the person practises and rates, and the answer is that person's own effect with an interval. Many people's trials pool into group evidence.

## 2. Designs

| Design | Arms (reference last) | Outcome | Claims it tests |
|---|---|---|---|
| `anchor_vs_sham` | the anchor's code, a sham code never paired | Calm, 0-10 | C2, C10, C12 |
| `cue_vs_none` | play the anchor when stress starts, play nothing | Calm, 0-10 | C1, C12 |
| `auto_vs_manual` | the device fires the anchor, the person fires it | Calm, 0-10 | C40 |
| `order_ct_identity` | Core Transformation first, identity peak first, hybrid, identity fully first | Calm, 0-10 | C85, C88 |
| `ssit` | higher-level imagery, imagery of the activity itself, general calming imagery | Ease of an untrained activity, 0-10 | C97, C101 |

## 3. Schedule

Permuted blocks: each block holds every arm once, in a random order from a seeded generator (the same order in Python and the browser). The person learns each session's arm only when the session starts.

## 4. A session

The outcome is rated before and after; the change is the session's result. Background factors are recorded with each session: hours slept, caffeine, exercise, and the hour of day (roadmap item 49).

## 5. Analysis

For each arm against the reference arm:

- **Difference** in mean change, with a 95% Welch interval (unequal variances).
- **Permutation p-value**: the share of 1,000 random relabellings of the sessions with a difference at least as large (seeded).
- **Adjusted difference**: an ordinary least-squares model with session order (drift over time) and sleep, pre-specified so a short trial is not over-fitted. The other background factors are reported as a balance table only.
- **Verdict**: too few sessions (under three per arm), one arm better (interval above or below zero), or no clear difference yet.

## 6. Pooling across people

Each person's difference and standard error pool by random effects (DerSimonian and Laird): the average effect with its interval, and the spread between people (`tau`).

## 7. Consistency

`consistency(decisions)` gives the share of repeated decisions in the same situation that match the most common choice. It is the measure for the behaviour-consistency test of agents (roadmap item 45, claim C70), and works for people too.

## 8. Simulated people

`SimPerson` has known arm effects, noise, drift over sessions and a sleep effect. `evaluate()` reports how often a true difference is found and a false one claimed, how well pooling recovers an average effect and the spread between people, and how adjustment changes the error. Results in `rsso/results/trial.md`.

## 9. What is not claimed

One person's trial answers large effects for that person. Moderate effects need pooling across people. The simulation shows the machinery works; it does not show that any arm works in people.
