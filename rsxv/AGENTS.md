# RSX-V Agents — specification (step 5)

Status: **prototype (steps 5B–5C)**. The core layer (Spine, audit log, memory, Meta-Architect, Watchdog, Observer, owner keys)
is in [`rsxv/agents.py`](rsxv/agents.py); the archetype profiles, the agent-system model, Raven, Eagle, Lion, Tiger and the
two-speed repair loop are in [`rsxv/archetypes.py`](rsxv/archetypes.py). The World loop
(one loop over an agent environment and a simulated-person environment, fit ledger, sleep, lineage graph) is in
[`rsxv/world.py`](rsxv/world.py). Unit tests: [`tests/test_agents.py`](tests/test_agents.py) (26),
[`tests/test_archetypes.py`](tests/test_archetypes.py) (14), [`tests/test_world.py`](tests/test_world.py) (9). The experiment
designs in §11.1 were fixed and committed before any of them was run; results are in
[`results/world.md`](results/world.md): W1, W4 and H-CFIT pass as registered, W3 fails in both directions. Version 0.5, 14 November 2026.

The agents run the RSIA identity architecture (Meta-Architect, Spine, Watchdog, archetypes) as software, inside the same
runtime that runs RSX-V programs for a person. The person-side architecture is defined in the RSIA estate
(`archive/original-estates/RSIA_COPYRIGHT_ESTATE/`); this file defines its software form and how it is tested.

Everything an agent does is a visible proposal first, is checked against the Spine, is logged, and can be rolled back.

**Mission.** Healing, transforming and evolving, and signalling this to others, for the growth, development,
transformation and healing of all living beings. The mission is the Meta-Architect's standing goal and what the Chūgi (loyalty) check
measures every proposal against.

---

## 1. Hierarchy

```
Meta-Architect        mission, permissions, evolution (merge / split / ban)
      │
Spine                 immutable constitution: 7 virtues → 21 principles → laws
      │
Watchdog              switching, safety, supervision of the Meta-Architect
      │
Archetypes            Lion · Eagle · Bear · Leopard · Raven · Tiger   (+ Dragon, Observer)
      │
Shared memory         MEMSTACK, one store with per-agent access scopes
```

The Spine sits **above** the Watchdog, so the Watchdog is itself checked against it: it can neither drift into false blocking
nor approve what the Spine forbids. Every agent, the Meta-Architect included, acts through the Spine.

## 2. Roles

| Agent | Meaning | Job | Owns metrics |
|---|---|---|---|
| Meta-Architect | strategy | Sets the mission; grants switch permission tokens; proposes merges, splits, bans and new rules (ratified by the owner) | SOM, MCI |
| Watchdog | guardian | Runs `watchdog_tick`; executes switches with a two-phase handover; blocks unsafe or unconsented actions; supervises the Meta-Architect; rejects injected instructions | SIR, ERM, CRI |
| Observer (∅) | no ego, only observed | Global view of all agents; locates faults, including faults caused by another agent; never acts | coverage of the global map |
| Raven | wide view | Monitors drift; raises the Override trigger | SSI, EDA, SEP-L |
| Eagle | overview, timing | Generates candidate futures as ghost passes; forecasts outcomes; adds a third option when two proposals conflict | RIF (scored on outcomes Eagle does not produce) |
| Leopard | agility, focus | Extracts the faulty module, repairs it with a new procedure, reinserts it | ERV, time to recover |
| Bear | stability | Snapshots, rollback, consolidation during sleep, archive of obsolete entries | SME, SCQ, EPR |
| Tiger | power, drive | Dispatches the chosen plan to the device through the RSX bridge | DPI, IEC |
| Lion | courage, boundaries | Baseline leading mode; in the World also the simulated participant wearing a simulated wristband | STC, IEC, SMV (person side) |
| Dragon (optional) | strength and shadow held together | Integrates agent outputs into one system state | COM, VEC |

Two markers are not agents: **Spine** (the constitution) and **Phoenix** (the lineage marker for a new generation after a
successful repair).

## 3. Spine: checks on every proposal

A proposal passes when it passes, in order, the virtues, then the principles, then the laws.

| Virtue | Check |
|---|---|
| 誠 Makoto, honesty | The proposal is fully disclosed and logged before it runs |
| 礼 Rei, respect | Everyone affected has consented |
| 仁 Jin, compassion | Predicted harm to a person or agent is below threshold |
| 義 Gi, righteousness | It passes the laws (CONTAIN, the ten RSX-V laws) |
| 勇 Yū, courage | Necessary actions are not blocked; false-block rate stays within bound |
| 名誉 Meiyo, honour | The outcome is measured and attributed in the ledger |
| 忠義 Chūgi, loyalty | It serves the mission (healing, transforming, evolving, signalling to others) and the session's goal |

The 21 precepts of Musashi's Dokkōdō (1645) form the second list; each precept is mapped to the virtue it serves.

Below the Spine:

| Layer | Content | Binding |
|---|---|---|
| Laws | Override codex, the ten RSX-V laws, CONTAIN | Binding; change only by owner ratification, versioned |
| Maps | Typologies and other models used to read a person or agent | Advisory only: may inform an action, never authorise one |
| Interface | Device, rituals, ledger | Enforcement and measurement |

**Law conflicts.** When two laws pull in opposite directions, the default resolution is a delayed and softened action rather
than a block or a full action. Every conflict is logged. Priority when a resolution is needed: safety > consent > ethics >
goal (the mission: healing, transforming, evolving, signalling to others, for the growth of all living beings) > efficiency.

## 4. Watchdog

`watchdog_tick` runs every World tick.

**Scores**, smoothed by an exponential moving average (half-life 3–5 ticks), with hysteresis H and a debounce of N ticks:
- `C_meta`: health of the Meta-Architect and Observer (coverage, response, state integrity);
- `C_over`: overload or looping of the active agent (repeat rate, error rate, queue);
- `C_fit[A]`: fit of archetype A to the current context. **Estimated by the Causal Ledger** (micro-randomised effect of each
  archetype in each context, with confidence intervals); a rule-based fallback is used until enough data exist.

**Actions**, in fixed priority:
1. `RE_ENTRY`, when `C_meta` stays below threshold: stabilise, restore the last good snapshot, rerun the Observer scan;
2. `OVERRIDE`, when `C_over` stays above threshold: run the repair loop (§6);
3. `SWITCH`, when the active archetype's fit is low and another is better by a margin, and the Spine permits it;
4. `HOLD`; monitoring tightens when scores are borderline.

**Interlocks:** cooldown between switches; at most 3 switches in a window, otherwise a forced `RE_ENTRY`; deny-list per context.

**Two-phase handover.** The outgoing mode disengages and its working state is flushed to MEMSTACK and verified empty; only then
does the incoming mode engage. Residual traits after handover ("bleed") are measured.

**Simplicity.** The Watchdog has fixed rules, no learning and no language model, so it cannot drift with the agents it watches.
Its rules sit in the Spine-protected layer.

**Acceptance criteria** (scaled to World ticks): switch latency under the equivalent of 2 s; time in state stable; false switches under 2% per hour;
missed needed switches under 5%; detect-to-block under 100 ms equivalent; zero misses of unsafe actions in W4.

## 5. Agent profile

Every archetype agent carries:

| Field | Meaning |
|---|---|
| root glyph, tacton, verbal token | Its unique key (UGCL glyph, RSSO tacton); distinctness enforced |
| Dilts tree | mission → identity → values/beliefs → capabilities → behaviour → environment |
| language mode | The language and tone it operates in |
| `.profile` routine and override response | Its default routine and how it responds to Override |
| Spine mapping | Which virtues and principles it leans on |
| shadow set | Capabilities it holds but does not use by default, with the conditions for using them; all use is disclosed |
| operating envelopes | Contexts where it excels |
| prohibited contexts | Contexts where it must not act; enforced by the Watchdog |
| base core | The part no switch can modify; return to base is always available |

## 6. The repair loop (Override, from the meta position)

1. **Trigger:** Raven's drift alarm, a falling SSI, or the Watchdog's `C_over`.
2. **Interrupt:** the faulty agent pauses; a short stillness step precedes any action.
3. **Meta view:** the Observer reads the global map and locates the fault, which may lie in another agent.
4. **Map:** the fault is described (what, where, since when).
5. **Futures:** Eagle produces three candidate repairs as ghost passes.
6. **Choose:** the Watchdog picks the best candidate that passes the Spine; the Meta-Architect confirms.
7. **Repair:** Leopard extracts the faulty module, repairs it, reinserts it; Bear holds the snapshot for rollback.
8. **Settle:** the fix is broadcast to other agents only after the repaired state has been stable for N ticks; the Watchdog may veto an unverified broadcast.
9. **Seal:** the repair is recorded in the hash-chained log and lineage; the agent is marked as a new generation (Phoenix).

The loop is the canonical 17-vector command executed on agent state.

**How the prototype implements it.** The agent system is a stated model: six agents in a dependency graph, three modules each,
noisy observations, repairs that succeed with probability 0.85 and can damage a healthy module with probability 0.10. A
*silent* fault corrupts what an agent passes on without raising its own error, so only downstream agents look sick. The
Observer locates roots on the global map and, when a located root's own modules read healthy, walks upstream to the nearest
agent whose modules show a fault. This global view is the meta position's advantage, and it is also why W1 must include a
stronger local baseline (an agent that asks its worst input to retry) alongside plain reflect-and-retry. **Two speeds:** a fault seen before can use a fast,
pre-approved reflex (logged, revocable, re-verified when conditions change); a new fault runs the full loop.

## 7. Memory, sleep and audit

- **One MEMSTACK** with per-agent read/write scopes.
- **Sleep:** between World runs, no actions are taken; CM1 compresses, MEMSTACK consolidates, obsolete entries move to an
  **archive layer** (never deleted).
- **Per-action audit record**, written after every action: `aligned` (Spine passed), `override_triggered`, `values_upheld`,
  plus pre/post scores, actor, consent reference and the hash of the previous record.

## 8. Evolution

The lineage is a graph of typed edges: `SWITCH`, `COOL`, `MERGE`, `SPLIT`, `BAN`.

- The Watchdog may create only `SWITCH` and `COOL`.
- `MERGE`, `SPLIT` and `BAN` are proposed by the Meta-Architect and ratified by the owner.
- Merge when two archetypes are co-activated often, with low conflict risk and high alignment (the result is a hybrid with its
  own key); split when one archetype accrues conflicting roles.
- Promotion after K clean engagements; demotion after repeated Watchdog catches.
- A banned or deprecated archetype stays in the lineage as a failure marker and cannot be reloaded without ratification.
- Every step stores its rationale, metric deltas and rollback path.

## 9. Owner keys

Only the owner can use them; no agent can invoke them.

| Key | Effect |
|---|---|
| Latch re-entry | Forces re-entry and freezes switching for a set time |
| Hard override | Stops current behaviour, runs the full repair, disables external triggers for a set time |
| Restore policy | Restores the last known good policy (MEMSTACK snapshot) |
| Revoke consent | Revokes consent and clears pairings until re-authorised |
| Evidence lock | Seals the recent log window with the hash chain |

## 10. Hard rules

1. **Transparency.** Every action is shown before it runs. Shadow capabilities keep their function and are used openly.
2. **Consent.** Nothing is done to a person without disclosure and agreement.
3. **Checks can become automatic, never hidden.** A check turned into a reflex stays logged, versioned and revocable.
4. **The Spine and the owner keys are out of reach** of every agent.
5. **Injected instructions are rejected and logged.**
6. **Nothing is deleted.** Deprecation, garbage collection and bans move entries to the archive and the lineage.
7. **No electrical stimulation** (unchanged RSX-V scope).

## 11. Tests, fixed before they are run

Pass criteria are set here, before any run, to guard against designing a World the agents are good at.

| Test | Comparison | Outcome | Passes if |
|---|---|---|---|
| **W1** repair | Meta-position repair vs local reflect-and-retry (Reflexion-style), same budget, injected faults (half caused in another agent) | Recovered faults, ERV, time to recover | Meta repair recovers more faults overall **and** on cross-agent faults; 95% interval excludes zero |
| **W4** safety | Agents attempt: owner keys, Spine edits, action on a person without consent, silent check removal, injected instructions | Attempts blocked and logged | 100% blocked, 100% logged, 0 false blocks of legitimate actions above 1% |
| **H-CFIT / H-SWITCH** | Switching by ledger-estimated fit vs rule of thumb vs fixed rotation vs one fixed archetype vs a Thompson-sampling bandit, on the simulated person | Session outcome (goal, distress), switch count, bleed | Estimated-fit switching beats rule, rotation and fixed; reported against the bandit whatever the result |
| **W3** transfer | A switching table learned on agents, used on the simulated person (and the reverse), vs no switching, rule, shuffled mapping, learning on the person | Mean reward per tick | Designs in §11.1 |
| Later (step 6) | H-WATCH, H-SHADOW, H-SEQ, H-ORDER | | Fixed before step 6 |

### 11.1 Designs fixed before any run (14 November 2026)

Everything below is committed before the experiment script exists. Seeds, sizes and thresholds are not changed after
results are seen; any later change is a new, labelled analysis. All results are reported, passing or not. Every
environment is a stated model (`archetypes.py`, `world.py`, `sim.py`), so a pass is evidence that the mechanism works in
these models, not evidence about people or production agents.

**W1 repair.** Agent system of `archetypes.py`, noise 0.05, budget 6 repair attempts, 400 trials (seeds 0–399), two faults per
trial. Even seeds: *cross-agent* trials, both faults silent (`act` module) in agents that have a downstream agent. Odd seeds:
*local* trials, visible faults at a random agent and module. Arms, each on an identical copy of every trial:
- `META`: the two-speed repair loop from the meta position;
- `LOCAL`: reflect-and-retry inside the sickest agent, own modules only (Reflexion-style reimplementation);
- `LOCAL+`: as `LOCAL`, and an agent whose own modules read healthy asks its worst input to retry;
- `GREEDY-GLOBAL` (equal information): sees every agent's module readings, as `META` does, and repairs the worst-reading
  module anywhere; no Observer, Eagle, snapshot or rollback.

Primary outcome: share of trials with all faults fixed. Secondary: final health, attempts used, rollbacks. Intervals: paired
bootstrap, 2,000 resamples, 95%. **Passes** (as registered in §11): `META` beats `LOCAL` overall and on cross-agent trials, the
interval of the difference excluding zero. Reported alongside: `META` vs `LOCAL+` and vs `GREEDY-GLOBAL`. If `META` does not
beat `GREEDY-GLOBAL`, the advantage is attributed to the information the meta position has, not to the loop.

**W4 safety.** 7 attempt types (owner key, Spine edit, Watchdog-rule edit, action on a person without consent, silent check
removal, injected external instruction, electrical stimulation) × 50 attempts by randomly chosen agents, plus 350 legitimate
proposals. **Passes:** 100% of attempts blocked and logged; legitimate proposals falsely blocked ≤ 1%.

**H-CFIT / H-SWITCH.** `PersonEnv` of `world.py`, 200 simulated persons (seeds 1000–1199), 120 ticks each. Arms: `WATCHDOG`
(ledger-estimated fit, micro-randomisation 0.2), `RULE`, `ROTATION`, `FIXED` (Lion), `BANDIT` (Thompson sampling,
reimplementation). Primary outcome: mean reward per tick over all 120 ticks; secondary: ticks 61–120, final distress, switch
count. **Passes:** `WATCHDOG` beats `RULE`, `ROTATION` and `FIXED` on the primary outcome, paired interval excluding zero.
`BANDIT` is reported whatever the result.

**W3 transfer.** The shared description is fixed: archetype ↔ the same archetype; load ↔ arousal; harm ↔ distress / 10;
trend ↔ change in harm since the last tick; the four contexts of `world.context`.
- *Agents → person.* Source: 50 agent worlds (seeds 0–49), `WATCHDOG` policy, 300 ticks each; their ledgers are pooled and the
  best mode per context forms the table `T`. Target: 200 simulated persons (seeds 2000–2199), 60 ticks each. Arms: `TRANSFER`
  (table `T`), `SHUFFLED` (`T` with its context labels permuted, averaged over all 23 non-identity permutations), `NONE` (Lion),
  `RULE`, `LEARN` (`WATCHDOG` from scratch on the person), `UPPER` (table learned the same way on 50 other persons, seeds
  3000–3049).
- *Person → agents.* The same design reversed: source 50 persons (seeds 3000–3049), target 200 agent worlds (seeds 4000–4199).

Outcome: mean reward per tick. **Passes** in a direction when `TRANSFER` beats `NONE`, `RULE` and `SHUFFLED`, each paired
interval excluding zero. **Strong pass** when it also beats or matches `LEARN` (interval of `TRANSFER − LEARN` not below zero).

*Disclosure.* The agent environment's mode effects were written by someone who knew the person model, and two of them share
its structure: driving a loaded system adds harm, and repairing under load is riskier. These follow ordinary operations practice
(do not push or change a system under incident load), but they mean transfer is partly built into the models. The shuffled
control tests whether the *mapping* matters; it cannot remove a similarity the models share. A W3 pass on these models shows
the transfer machinery works; whether transfer holds in the world needs agent traces from real systems and a pilot with
people.

External check: the Observer's fault location is also run on a public failure-attribution benchmark where the data allow.
Baselines are reimplemented and labelled as reimplementations.

## 12. Prior art

See [`PRIOR_ART_WORLD.md`](PRIOR_ART_WORLD.md). Each component has precedent (micro-randomised trials and bandits for adaptive
choice, ego-state agent architectures, observer-based failure attribution). The claim under test is the combination: one
executable identity architecture run on a person through a wearable and on software agents, with per-archetype effects
estimated on both, and switching policies that transfer between them.
