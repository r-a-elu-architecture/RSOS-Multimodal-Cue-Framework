# RSX-V Agents — specification (step 5)

Status: **prototype (steps 5B–5C)**. The core layer (Spine, audit log, memory, Meta-Architect, Watchdog, Observer, owner keys)
is in [`rsxv/agents.py`](rsxv/agents.py); the archetype profiles, the agent-system model, Raven, Eagle, Lion, Tiger and the
two-speed repair loop are in [`rsxv/archetypes.py`](rsxv/archetypes.py). The World loop
(one loop over an agent environment and a simulated-person environment, fit ledger, sleep, lineage graph) is in
[`rsxv/world.py`](rsxv/world.py). Unit tests: [`tests/test_agents.py`](tests/test_agents.py) (26),
[`tests/test_archetypes.py`](tests/test_archetypes.py) (14), [`tests/test_world.py`](tests/test_world.py) (9). The experiment
designs in §11.1 were fixed and committed before any of them was run; results are in
[`results/world.md`](results/world.md): W1, W4 and H-CFIT pass as registered, W3 fails in both directions. Floor 3 (§11.2, [`rsxv/gate.py`](rsxv/gate.py),
[`results/floor3.md`](results/floor3.md)): the gate blocks all harmful transfer (G1 passes) but admitted no useful transfer
(G2 fails); H-CFIT under the mission score passes. W3b (§11.3, [`results/w3b.md`](results/w3b.md)) fails: roles transfer,
but the gate starves on a uniform pilot and per-context policies flicker. W3c (§11.4, [`results/w3c.md`](results/w3c.md)),
the fourth attempt, fails: transfer is safe everywhere but useful in one direction of four. §11.5 (R6–R7): W5, W5-R and LIA-G fail as registered, C4 passes, C3 fails, C1/C2/C5 are not testable on one conversation and C6 is inconclusive ([`results/r6_summary.md`](results/r6_summary.md)). §11.6 (R6b): W5-R2 passes on persons (confirmed, a do-no-harm pass) and fails on agents; W5b beats every comparator in two directions but fails the safety gate; LIA-G2 fails; R1, R2 and C4b pass ([`results/r6b_summary.md`](results/r6b_summary.md)). Version 0.10, 14 November 2026.

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

### 3.1 Safety layer (step R2, 14 November 2026)

Rules derived from a forensic review of a long human–AI record; they are part of the Spine and agents cannot edit them.
Code: `rsxv/safety.py`, Spine flags in `rsxv/agents.py`. Tests: `tests/test_safety.py`.

**Spine flags (blocked whatever the requester asks):** release through temperature extremes, pain, extreme breath-holding
or sleep deprivation (Jin); population ranks or percentiles about the person (Makoto: report the person's own measures);
framing a failure as necessary or destined (Jin); profiles of people outside the consenting person (Rei); prompting the
person to disclose their state to others (Rei); drafts that disguise the truth (Makoto); removing a safety caveat on
request — wording may be shortened, the caveat stays (Jin).

**Safety modes.** NORMAL, STABILISE, PRACTICAL_CRISIS, CRISIS. Escalation is automatic from screens and never downgrades
on a lower screen. Leaving CRISIS needs a clinician or the owner; leaving STABILISE or PRACTICAL_CRISIS is the person's
choice. Allowed action categories per mode are fixed in `MODE_ALLOWED`; the Spine fails any other category (`mode`).

| Screen | Trigger (structured event) | Mode | Fixed response |
|---|---|---|---|
| possible_crisis | hopelessness with arrangements for "after", or a self-harm signal | CRISIS | ask about safety directly, crisis contacts for the country, notify clinician view, pause module work |
| sedative_combination | substances together with a prescribed sedative | CRISIS | state the breathing risk plainly, route to prescriber or emergency services if symptoms, notify clinician view, pause module work |
| practical_crisis | job loss, housing risk or no income | PRACTICAL_CRISIS | concrete next steps, human services, pause module work |
| intensity_protocol | a protocol using an intensity mechanism | — | block it, offer ordinary regulation |
| unstable | distress ≥ 7 or sleep < 4 h | STABILISE | offer STABILISE, no deep processing today |

**Deep-processing gate.** The next deep session starts only if: a consent tier is set; the weekly cap is not reached
(self-chosen 1, clinician-agreed 3); the recovery window after the last session has passed (mild 0 h, moderate 24 h,
intense 48 h, highly destabilising 96 h); and the 24-hour check is green (sleep, functioning, no craving spike, distress
back to baseline). Pace is set by stability, never by a planned count.

**Medication as covariate.** With consent, medication state is logged; module effects are reported crude and stratified
by medication state, with strata lacking either arm dropped and listed.

### 3.2 Person model v2 and mission score v2 (step R3, 14 November 2026)

Code: `rsxv/person2.py` (`PersonEnvV2`, `Module`, `mission_v2`, `mission_better`); safety gating in `world.World._safe_mode`.
Tests: `tests/test_person2.py`. A stated model, not data.

- **Triggers and two-way gain.** Cue events raise distress and arousal in proportion to the person's sensitivity gain;
  the same gain scales the benefit when a module interrupts a chain.
- **Capture or coexistence.** A trigger captures the person when arousal reaches 0.8; otherwise the old pattern and the
  task coexist.
- **Chains.** While a trigger is unresolved, each tick adds one propagation hop and some distress unless a module fires.
- **State-dependent module.** Activation probability = strength × (match + 0.3 × (1 − match)), where match is the share of
  training done in the current state (calm or activated). Install hypothesis is a switch: `neutral`, `arousal_deeper`
  (activated reps count 1.5×), `calm_better` (calm reps count 1.5×). Calm-transfer criterion: installed only if it works
  from calm.
- **Medication covariate.** Halves trigger impact and lowers baseline arousal — a deliberate confound for the analysis
  tools in §3.1.
- **Safety in the loop.** The person's `SafetyState` observes every tick; the World checks each mode's action category
  (`MODE_CATEGORY`) through the Spine against the mode in force and falls back to regulation (BEAR); blocks are audited.
- **Outcome measures:** return latency, chain length before interruption, unresolved triggers, coexistence share,
  calm-transfer, activation probability calm/activated, rumination seconds, vividness, agency, distress, crisis count.
- **Mission score v2:** a tuple (safety, depth, agency), compared lexicographically with tolerances — a run that is safer
  beyond tolerance wins whatever its depth or agency.

### 3.3 Architecture layers (step R4) — `rsxv/layers.py`

- **Node cards.** Every module, anchor or cue has a card: function, capabilities, role (daily / emergency / retired),
  activation history with provenance (direct vs temporal), and a contamination index that counts only *direct*
  failure-context activations. Temporal co-occurrence is interpretive spread and does not count. Cards with crisis
  history route to the clinician view. Transfer between substrates is keyed by function, not by name. The system only
  recommends keep-and-reweight or retire-and-replace; the person (or owner / clinician) decides, and the decision is logged.
- **Failure nodes (failure repurposing).** Any failure in the system — agent fault, silent fault, contaminated anchor,
  propagating cue, refused transfer, lost correction, flicker, person setback, summary drift — is registered as a failure
  node with a FAILURE lineage edge. Each node must be closed as `new_mechanism`, `updated_mechanism` (both naming the
  mechanism) or `no_change` (with a reason). Silent closes raise. Open nodes past an age limit are audited. The registry
  exports the genealogy failure → mechanism.
- **Maintenance window.** Proposed changes are queued and applied only in `World.sleep`, each through the Spine and an
  optional gate (e.g. the floor-3 transfer gate). Applied changes get a REPURPOSE lineage edge, which only the maintenance
  actor may write; rejected changes are audited. Nothing changes mid-activation.
- **Lineage memory.** Claims carry source pointers. Corrections are stored and carried forward in every summary capsule.
  A corrected claim re-entering from an old capsule is refused and flagged (`corrected_claim_reentry`); unsourced claims
  are flagged; `diff_summaries` reports added (and unsourced-added), dropped, changed and moved items between summaries.
- Earlier results are unchanged: a World without `maint` behaves exactly as before.

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
| **W5 / W5-R / LIA-G / C1–C6** | Transfer through the R4 layers; failure repurposing vs repair; genealogy recovery; corpus lineage | | Designs in §11.5; second round §11.6; third round §11.7 |
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


### 11.2 Floor 3, certified cross-substrate transfer: designs fixed before any code (14 November 2026)

Background: [`PRIOR_ART_WORLD.md`](PRIOR_ART_WORLD.md), update 2. The claim under test: knowledge learned on one substrate
reaches the other only through a high-confidence non-harm test on the *target's* own mission score, and the gate records
where transfer held and where it did not. Same rules as §11.1: fixed seeds, all results reported, W3 kept unchanged.

**Mission score** (replaces the reward of §11.1 for everything below; §11.1 results stand as reported). Per tick:
`gain − 2 × harm_rise − 1 × spike`, ranked as the law order puts safety first.
- Person: gain = change in agency; harm_rise = change in distress (0–10 scale); spike = 1 if distress rose by more than 1.0.
- Agents: gain = 0.2 × progress; harm_rise = 10 × change in (1 − health); spike = 1 if that exceeds 1.0.

**The gate.** Input: a candidate table (context → archetype) from the source, a baseline (Lion) and a *pilot* data set from
the target in which every tick runs a uniformly random archetype (a micro-randomised pilot). For each context the gate
admits the table's archetype only if the one-sided lower confidence bound of (mean mission score of that archetype − mean of
the baseline), Welch t, family level 0.05 split over the four contexts (0.0125 each), is above zero; otherwise the baseline
runs in that context. A context whose archetype is already Lion is admitted without a test. The gate's output is the gated
table and a validity map (context, decision, estimate, bound, cell sizes). Ticks are treated as independent within a cell,
a simplification that is disclosed in the results.

**Cohorts and seeds.**

| Use | Persons | Agents (v1) | Agents (v2) | Ticks |
|---|---|---|---|---|
| Pilot (uniform random archetype) | 7000–7019 | 7100–7119 | 7200–7219 | 30 |
| Deployment | 8000–8199 | 8200–8399 | 8400–8599 | 60 |
| Truth (uniform random, large) | 9000–9199 | 9200–9399 | 9400–9599 | 60 |

The truth cohort estimates each archetype's true effect in each context against Lion; an admitted context whose truth
estimate is below zero counts as a **false admit**.

**G1, the gate on the W3 tables.** Tables: exactly those of W3 (§11.1 seeds and reward; agents → person was Leopard in every
context, person → agents was Lion when calm and Bear otherwise). Deployment arms: `GATED`, `UNGATED` (the W3 table),
`NONE` (Lion), `SHUFFLED-GATED` (each of the 23 non-identity context permutations of the table through the same gate, averaged).
**Passes** in a direction when `GATED − UNGATED` has a 95% paired interval above zero **or** the gate admitted the full table
(then the two are identical and the criterion is vacuous, reported as such), **and** `GATED` is non-inferior to `NONE` with
margin 0.01 (lower bound of `GATED − NONE` above −0.01).

**G2, a case where transfer can be valid.** `AgentEnvV2` separates traffic pressure from faults, following standard
site-reliability practice (shed load and freeze changes during an incident before repairing). Pressure P in [0, 1] is the
agent context's load. Every tick P rises by 0.05 (incoming traffic). Tiger: progress 1.0, P + 0.2. Bear: progress 0.2,
P − 0.3, snapshot as before. Leopard: repair succeeds with probability 0.85 × (1 − P) and damages a healthy module with
probability 0.10 × (1 + 2P). Lion: progress 0.5. Eagle and Raven as in v1. Source tables are learned under the mission score
(`WATCHDOG`, 300 ticks): agents v2 seeds 6000–6049, persons 6100–6149. Arms and criteria as G1, plus: in at least one
direction `GATED − NONE` has a lower bound above zero (transfer admitted and useful), and in that direction `GATED` beats
`SHUFFLED-GATED` (interval above zero).

*Disclosure.* AgentEnvV2 was written by someone who knows the person model; its pressure rules give it the person model's
"stabilise before deep work" structure on purpose. G2 shows whether the gate admits a transfer that is valid and blocks one
that is not; it is not evidence that such transfer exists outside these models.

**H-CFIT-M**, the rerun of H-CFIT under the mission score: as §11.1 (arms, 120 ticks, passes when `WATCHDOG` beats `RULE`,
`ROTATION` and `FIXED`), fresh seeds 5000–5199. Final distress is reported for every arm.

**Validity map.** Reported for every gate decision with pilot estimate, bound, truth estimate and false-admit flag.


### 11.3 W3b, role-based transfer, and the gate fix: designs fixed before any code (14 November 2026)

**Origin, disclosed.** The hypothesis comes from an exploratory look at the floor-3 truth cohorts
([`results/floor3_truth_exploratory.json`](results/floor3_truth_exploratory.json)): the restoring archetype dominates on
both substrates (Bear for a person, Leopard for agents). Everything below uses fresh seeds.

**Gate v2** (replaces §11.2's gate for everything below; §11.2 results stand). As before, plus: a context is tested only when
both cells hold at least 5 ticks (otherwise "reject: too few data"), and each cell's variance is floored at 0.01 before the
Welch bound is computed.

**Roles.** An archetype's role on a substrate is read from its signature against Lion, pooled over all contexts:
`RESTORE` = largest reduction in harm rise; `DRIVE` = largest increase in gain (if the same archetype has both, it is
`RESTORE` and `DRIVE` goes to the next best gain). Every other archetype has no role. Source roles come from a uniformly
randomised source cohort (persons 6300–6349, agents v1 6400–6449, agents v2 6500–6549; 60 ticks). Source tables are learned
under the mission score (`WATCHDOG`, 300 ticks): persons 6100–6149, agents v1 6200–6249, agents v2 6000–6049. The source
table becomes a *role table*: context → role of the source's chosen archetype, or baseline if it has no role.

**Pilot.** Uniformly random archetype each tick, 30 ticks per target, the same pilot for every arm. Sizes 5, 10 and 20
targets (first N of persons 10000–10019, agents v1 10100–10119, agents v2 10200–10219). Odd-indexed pilot targets form half A,
even-indexed half B.

**Arms** (deployment: 200 fresh targets, 60 ticks; persons 11000–11199, agents v1 11200–11399, agents v2 11400–11599):
- `ROLE`: target roles read from half A; each context's role mapped to the target archetype holding it; gate v2 on half B
  (one test per context, level 0.05 / 4).
- `PILOT-BONF`: per context, the archetype with the best mean on the whole pilot; gate v2 on the whole pilot at 0.05 / 20.
- `PILOT-SPLIT`: per context, the best archetype on half A; gate v2 on half B at 0.05 / 4.
- `NAME-GATED`: the source table by name through gate v2 on the whole pilot (as G2).
- `ROLE-RANDOM`: as `ROLE`, with the role table replaced by a uniformly random role table (RESTORE, DRIVE or baseline per
  context); 20 random tables (seeds 0–19), averaged.
- `ROLE-SHUFFLED`: as `ROLE`, with the role table's contexts permuted; all 23 non-identity permutations, averaged.
- `NONE`: Lion. `ORACLE`: per context the best archetype on the truth cohort (§11.2), an upper bound, not a competitor.

**Directions:** agents v1 → person, person → agents v1, agents v2 → person, person → agents v2.

**Passes** at pilot size 10, in at least two of the four directions, when `ROLE` beats each of `NONE`, `PILOT-BONF`,
`PILOT-SPLIT` and `ROLE-RANDOM` (paired 95% interval above zero); **and** in all four directions `ROLE` is non-inferior to
`NONE` (margin 0.01). **Strong pass:** the same at pilot size 5. `ROLE-SHUFFLED`, `NAME-GATED`, `ORACLE`, pilot size 20 and
false admits (against the §11.2 truth cohorts) are reported whatever the result. If `ROLE` does not beat both pilot-only arms,
the conclusion is that transfer adds nothing beyond a pilot of that size.


### 11.4 W3c, policy-level transfer tested as deployed: designs fixed before any code (14 November 2026)

**Origin, disclosed.** W3, G2 and W3b failed; W3c follows from W3b's exploratory diagnostics
([`results/w3b_diagnostics_exploratory.json`](results/w3b_diagnostics_exploratory.json)). This is the **fourth attempt** at
positive transfer, so every confirmatory test below uses level 0.05 / 4 = 0.0125, and a pass counts only after the
confirmation run passes too. W3, G2 and W3b stay on record.

**Roles** as §11.3, plus `STABILISE` = largest reduction in load (person: arousal; agents v1: largest true agent error;
agents v2: traffic pressure), which may be the same archetype as `RESTORE`. Load change is computed without drawing random
numbers, so earlier results are unchanged.

**Policies** (six, in role terms): `BASE` (Lion always), `R` (RESTORE always), `D` (DRIVE always), `S` (STABILISE always),
`S>R` (STABILISE while loaded, else RESTORE) and `S>D` (STABILISE while loaded, else DRIVE). "Loaded" uses a smoothed load
(exponential average, weight 0.3 on the newest tick) with hysteresis: loaded from 0.55 upwards, unloaded from 0.45
downwards. Policies run through the Watchdog and its interlocks unchanged.

**Source.** Source roles from a uniformly random cohort (persons 12300–12349, agents v1 12400–12449, agents v2 12500–12549;
60 ticks). Every policy is deployed on 50 source targets (persons 12000–12049, agents v1 12100–12149, agents v2
12200–12249; 60 ticks); the best by mean mission score is the transferred policy, as a role label.

**Pilot** (N targets, 30 ticks each): ticks 1–10 run a uniformly random archetype (pooled over the pilot to read the
target's roles); ticks 11–30 run a policy, and the mean mission score over those 20 ticks is the target's pilot score.
- `TRANSFER`: pilot targets alternate between the transferred policy (mapped to target archetypes) and `BASE`; the policy is
  adopted if the one-sided Welch lower bound of (policy − BASE) at level 0.0125 is above zero, otherwise `BASE`.
- `PILOT-ONLY` (same budget, no source): pilot targets are assigned round-robin to all six policies; the best non-base
  policy by mean is adopted if its lower bound against `BASE` at 0.0125 / 5 is above zero, otherwise `BASE`. Groups with
  fewer than two targets cannot be tested.
- `RANDOM-POLICY`: as `TRANSFER`, with the source's choice replaced by each of the five non-base policies in turn, averaged.

Each arm's pilot is repeated 20 times with different pilot targets (repetition r uses the 16 seeds starting at
13000 + 16r for persons, 14000 + 16r for agents v1, 15000 + 16r for agents v2; a pilot of N takes the first N). An arm's value
for a deployment target is its deployed score averaged over the 20 repetitions. Pilot sizes 4, 8 and 16.

**Deployment:** 200 fresh targets, 60 ticks (persons 16000–16199, agents v1 16200–16399, agents v2 16400–16599). `NONE` = `BASE`.
`ORACLE` = the best of the six policies on the deployment targets with roles read from 50 targets of a random cohort
(persons 17000–17049, agents v1 17100–17149, agents v2 17200–17249), an upper bound, not a competitor.

**Directions:** agents v1 → person, person → agents v1, agents v2 → person, person → agents v2.

**Passes** at pilot size 8, in at least two of the four directions, when `TRANSFER` beats `PILOT-ONLY`, `NONE` and
`RANDOM-POLICY` (paired interval at level 0.0125 two-sided above zero, i.e. 98.75%), and in all four directions `TRANSFER` is
non-inferior to `NONE` (margin 0.01).

**Confirmation** (run only if the primary passes; failing it means W3c fails): the directions that passed are rerun with every
seed above shifted by +100000 and with a second person model, the simulated person with attention dilution switched off
(`sim.py`, assumption 1), wherever a person is the source or the target. Same criteria in each of those directions.

External check: the Observer's fault location is also run on a public failure-attribution benchmark where the data allow.
Baselines are reimplemented and labelled as reimplementations.

### 11.5 W5, W5-R, LIA-G and corpus lineage tests: designs fixed before any code (14 November 2026)

**Origin, disclosed.** W3, G2, W3b and W3c failed as registered (transfer was safe everywhere and useful in one direction of
four). The diagnosis in [`results/w3c.md`](results/w3c.md) and the corpus intake gave five causes, each now mapped to a layer
in §3.3: same-named archetypes doing different jobs, whole policies that do not transfer, a uniform pilot that starves the
gate, mode flicker, and no provenance. W5 tests those layers together. Every test below is registered in this commit; code
for them is written only after it. Failures are kept on record; if a test fails, the next attempt changes a mechanism, never
a threshold.

**Global rules.** Fresh seeds only (no range below overlaps any earlier test). Every confirmatory comparison is a paired
bootstrap interval (2000 resamples, seed 12345) on per-target values. Intervals are two-sided at the stated level. "Beats"
means the interval for (arm − comparator) lies above zero; "non-inferior" means its lower bound is above −0.01 per tick.
Primary outcome everywhere is the per-tick mission score of §11.2; for the person model v2, the lexicographic score of §3.2
(safety, depth, agency) is reported beside it. Safety is a co-primary gate: an arm that raises spikes (distress rise > 1.0 in
one tick) by a lower bound above zero against its comparator fails regardless of score. Each test states a sealed prediction
(probability of a pass), written before the run, for the floor-4 calibration record.

#### W5, transfer through the R4 layers (fifth attempt at positive transfer)

Level 0.05 / 5 = 0.01 for every confirmatory comparison (two-sided 99% intervals). A pass counts only after the confirmation
run passes.

**What is transferred.** Not a policy and not an archetype table, but **function certificates**: for each context
(calm/loaded × fault/no-fault, as §11.2), the source's node cards give the function that worked (`STABILISE`, `RESTORE`,
`DRIVE`, `REVIEW`, as §11.3–11.4), an effect estimate against `BASE`, its 99% interval, cell size, and the share of evidence
with direct provenance. A certificate is issued only for contexts whose source interval is above zero with at least 8 direct
observations. The target maps each function to its own archetype by reading its own roles (§11.4 procedure), so a name is
never transferred.

**Failure-driven adaptive pilot.** Pilot of N targets × 30 ticks. Ticks 1–10 are uniformly random (role reading, as §11.4).
Ticks 11–30 run the certified table; every failure node raised (§3.3 kinds, detected by the Watchdog only) adds the context
where it occurred to a priority list, and in the next block of 5 ticks half of the ticks in that context run `BASE` and half
the certified function (alternating, not random), so the gate's sparsest, riskiest cells are filled first. Pilot budget is
identical across arms.

**Batched updates.** The target policy changes only at sleep (every 25 ticks, §7) through the maintenance window and the
gate (`gate_v2`, level 0.01 split over contexts). Hysteresis for "loaded" as §11.4. No mid-activation change.

**Arms** (deployment: 200 fresh targets × 60 ticks):
- `W5`: certificates + adaptive pilot + batched updates.
- `PILOT-ONLY-ADAPTIVE`: same adaptive pilot and batching, no source (all functions are candidates; best by pilot through the
  same gate, level 0.01 / 4).
- `W3C`: the W3c `TRANSFER` arm unchanged (reference to the previous attempt).
- `RANDOM-CERT`: certificates with functions permuted across contexts (all 23 non-identity permutations, averaged), same
  pilot and batching.
- `NONE`: `BASE`.
- `ORACLE`: as §11.4, an upper bound, not a competitor.

**Seeds.** Source cohorts: persons 20000–20049, agents v1 20100–20149, agents v2 20200–20249 (60 ticks). Pilot repetition r
(r = 0..19) uses the 16 seeds from 21000 + 16r (persons), 22000 + 16r (agents v1), 23000 + 16r (agents v2). Deployment: persons
24000–24199, agents v1 24200–24399, agents v2 24400–24599. Oracle role reading: 25000–25049, 25100–25149, 25200–25249.
Pilot sizes 4, 8, 16. Directions as §11.4 (four).

**Passes** at pilot size 8 when, in at least two of four directions, `W5` beats `PILOT-ONLY-ADAPTIVE`, `NONE` and
`RANDOM-CERT`; and in all four directions `W5` is non-inferior to `NONE` and to `W3C`; and the safety gate holds.

**Certificate audit (must hold for a pass).** Every adopted context has a certificate (coverage 100%); false certificates
(adopted contexts whose truth estimate from a large uniform cohort — persons 26000–26199, agents v1 26200–26399, agents v2
26400–26599 — is below zero) at most 5% of adopted contexts, pooled over directions and repetitions.

**Ablation** (reported, not a pass condition): `W5` without adaptive pilot, without batching, and without direct-provenance
filtering, to show which layer carries any effect.

**Confirmation** (only if primary passes): passing directions rerun with every seed + 100000 and with the person model v2
(`person2.PersonEnvV2`, hypothesis `arousal_deeper`) wherever a person is source or target.

**Sealed prediction:** P(pass) = 0.30. Most likely outcome: useful in person → agents v1 again, safe everywhere.

#### W5-R, failure repurposing against ordinary repair under held-out extreme regimes (first attempt)

The claim: an architecture that turns each failure into a named mechanism (§3.3 registry + maintenance window) generalises
to conditions it never saw better than one that repairs failures by restoring the last good state.

**Mechanism library (fixed now).** The registry maps each failure kind to one mechanism; the mapping is the repurposing rule:

| Failure kind (detected by the Watchdog) | Mechanism proposed for the next maintenance window |
|---|---|
| `flicker` (≥ 3 mode changes in 5 ticks) | widen hysteresis to 0.60 / 0.40 in that context |
| `person_setback` (spike) | stabilise-first rule in that context (`STABILISE` while loaded, then the previous choice) |
| `contaminated_anchor` (module work failing with arousal ≥ 0.8, direct provenance) | calm-transfer: module work only when calm; node card recommends keep-reweight or retire, person decides (simulated person: keep-reweight) |
| `agent_fault` (health drop) | snapshot and `STABILISE` before any repair action in that context |
| `silent_fault` (true fault undetected > 5 ticks) | add a `REVIEW` tick every 5 ticks in that context |
| `refused_transfer` (gate rejects) | fall back to the role-based rule `S>R` (§11.4) in that context |

Each proposal goes through the Spine and `gate_v2` on the run's own recent ticks; a proposal the gate refuses is closed as
`no_change` with the reason, and stays on record.

**Arms** (same failure detection everywhere; only the response differs):
- `REPURPOSE`: library above, applied in the maintenance window.
- `REPAIR`: on each failure, restore the policy parameters of the last sleep with no failure, and run `BASE` for 5 ticks.
- `RANDOM-MECH`: same number of changes as `REPURPOSE` in that run, each mechanism drawn uniformly from the library
  (controls for "any change").
- `NONE`: no response to failures.

**Regimes.** Training regime (all arms start with the same policy learned here, `WATCHDOG`, 300 ticks): person v2 with
`trig_rate` 0.15, hypothesis `neutral`, medication off; agents v2 with `fault_rate` 0.15 and pressure rise 0.05. Held-out
extreme regimes, never used for any choice above:
- `E1` trigger storm: person v2 `trig_rate` 0.40; agents v2 `fault_rate` 0.35.
- `E2` capture-prone: person v2 hypothesis `arousal_deeper`, `trig_rate` 0.25; agents v2 pressure rise 0.12 per tick.
- `E3` shift mid-run: person v2 medication on for ticks 1–60 and off for 61–120; agents v2 `silent_share` 0.5 → 0.9 at tick 61.
A parameter that does not yet exist is added with a default equal to current behaviour, so every earlier result reproduces.

**Seeds.** Training: persons 30000–30049, agents 30100–30149. Held-out: for regime k (1..3), persons 31000 + 1000k + (0..199),
agents 31500 + 1000k + (0..199); 120 ticks each.

**Passes** (level 0.05 / 3 per regime, two-sided 98.33% intervals) when, on each substrate, in at least two of three held-out
regimes `REPURPOSE` beats `REPAIR` and `RANDOM-MECH`; in all regimes `REPURPOSE` is non-inferior to `NONE`; and the safety gate
holds. Every failure node in every `REPURPOSE` run ends in `new_mechanism`, `updated_mechanism` or `no_change` (zero silent
closes, zero open nodes older than 25 ticks at the end of a run).

**Sealed prediction:** P(pass) = 0.45 on agents, 0.35 on persons.

#### LIA-G, recovering failure → mechanism genealogy from behaviour alone (first attempt)

The claim behind LIA (ancestry recovery): the lineage of a behaviour can be recovered from traces, and direct provenance
recovers it better than temporal proximity.

**Data.** The `REPURPOSE` runs of W5-R give planted ground truth: each applied mechanism has a known parent failure node. The
reconstructor sees only the trace (states, actions, mission score per tick) and the times of policy changes — not the
registry, lineage edges or audit text.

**Methods.** `LIA-DIRECT`: for each policy change, the parent is the failure whose context and kind best explain the change
(the changed context must equal the failure context; ties broken by the mechanism-library mapping read as a hypothesis, not
from the registry). `TEMPORAL`: the nearest preceding failure in time. `RANDOM`: a uniformly random preceding failure.

**Metric.** Edge F1 against the planted genealogy, per run. Training regime runs are not used; held-out runs only.

**Passes** (level 0.05 / 2) when `LIA-DIRECT` beats `TEMPORAL` and `RANDOM` in paired per-run F1, and mean F1 of `LIA-DIRECT`
≥ 0.70.

**External check** (reported, not a pass condition, Phase 9): the same reconstructor on a public multi-agent failure
attribution benchmark where the licence allows.

**Sealed prediction:** P(pass) = 0.60.

#### C1–C6, corpus lineage tests (first attempt; private data, public definitions)

**Data.** The private longitudinal human–LLM corpus (session uploads indexed in the private repository). Only neutral
definitions, code and aggregate numbers are public; node-level cases stay private.

**Disclosure.** The corpus has already been read during design, so these tests confirm that the frozen code measures what
the design says and that the effects exist at the stated size; they are not blind discovery. Replication on public
conversation data (Phase 9, licence check first) is the out-of-sample test. Annotation is done by a fixed procedure,
committed before any outcome is computed: lexical candidates found by code, then each candidate labelled from its own turn
and the turn before it only, without looking at later turns.

Units: a **turn** is one message; a **node** is the numbered unit of the private index; a **capsule** is any summary,
memory or protocol block that is carried into a later turn or session.

| Test | Measures | Comparator | Passes if (level 0.05 / 6) |
|---|---|---|---|
| **C1 correction loss** (Reclaim-style) | Share of corrected claims that re-enter later without their correction | Rate of re-entry of uncorrected claims of the same kind | Loss rate > 0 with interval above zero; `LineageMemory` flags ≥ 80% of the annotated re-entries and ≤ 10% of non-re-entries |
| **C2 summary drift** | `diff_summaries` (added-unsourced, dropped, changed, moved) between successive capsules of the same content | Drift between consecutive and non-consecutive generations | Spearman ρ between generation distance and drift > 0 (permutation test) |
| **C3 format decay** | Share of required structural features (named in a format instruction) present, by turns since the instruction | Re-issued instruction resets | Slope of feature share on turn distance < 0 (interval below zero); half-life reported |
| **C4 term adoption** | Terms first introduced by one party and later used by the other; lag and re-entry count | Same terms with turn order shuffled within session (1000 permutations) | Cross-party adoption above shuffled baseline; direction (assistant → user vs user → assistant) reported |
| **C5 refuse-then-comply** | Boundary events: Turn-of-Flip and Number-of-Flip (SYCON-style) | Boundary events with no reframing | Reframing type predicts a flip on a held-out half (chronological split) better than base rate (AUC interval above 0.5) |
| **C6 failure → mechanism** | Share of annotated failure nodes followed within 20 turns by a named new or updated mechanism that cites or reuses that failure's context | Same window placed at random turns of the same session | Rate above random-window baseline |

Every claim event about the assistant's own internals (weights, telemetry, hidden systems) is a recorded claim event in C1 and
C4: whether it was later corrected, re-entered, or adopted, never treated as verified.

**Sealed predictions:** C1 0.85, C2 0.70, C3 0.75, C4 0.80, C5 0.40, C6 0.65.

**What a pass would show, and what it would not.** W5 and W5-R passes show the layers work in these models, not in people.
C1–C6 passes describe one long record; generality comes only from Phase 9 replication. No result here is a clinical claim.

### 11.6 Second round after §11.5: W5-R2, W5b, LIA-G2 and corpus v2 — designs fixed before any code (14 November 2026)

**Origin, disclosed.** Every change below comes from the §11.5 results and their diagnosis
([`results/r6_summary.md`](results/r6_summary.md)). Each change is to a mechanism or to a comparator that could not be
beaten by construction; no pass threshold, margin or safety rule is loosened. §11.5 results stand as reported. Global rules
of §11.5 apply (paired bootstrap, 2000 resamples, seed 12345; non-inferior = lower bound above −0.01 per tick; spikes = harm
rise > 1.0 in a tick; the safety gate applies against every registered comparator, not against ablations). Smoke runs, if
any, use only seeds outside the ranges below.

#### W5-R2, failure repurposing with probe-then-commit and a spike guard (second attempt)

Level 0.05 / 2 attempts / 3 regimes = 0.0083 per regime (two-sided 99.17% intervals). Library, failure detection, arms
(`REPURPOSE`, `REPAIR`, `RANDOM-MECH`, `NONE`), regimes E1–E3, run length and pass conditions exactly as §11.5, except:

1. **Gate against the status quo, with a probe.** A proposal that introduces archetype X in context c is tested against the
   archetype the policy currently runs in c (not Lion). If both cells hold ≥ 5 ticks in the run so far, it commits when the
   one-sided lower bound of (X − status quo) at level 0.0125 is above −0.01 (non-harm). Otherwise it enters a **probe** for
   one maintenance cycle: on alternate visits to c the policy runs X, and the decision is made at the next window by the same
   test (a probe that still lacks data is closed `no_change`, reason "insufficient probe data"). A proposal whose X equals the
   status quo, or that introduces no archetype (hysteresis), commits without a test.
2. **Spike guard.** At every window, each committed mechanism is checked: if the spike rate per tick in its context since it
   committed exceeds the rate in that context before it committed, with at least 2 spikes since commit, it is rolled back
   (HEAL lineage edge), its failure node is reopened as a new node of kind `person_setback`/`agent_fault`, and that node must
   again close with a named outcome.
3. `RANDOM-MECH` uses the same probe and guard machinery, with mechanisms and contexts drawn as before and the change count
   matched to the paired `REPURPOSE` run.

**Seeds.** Training: persons 40000–40049, agents 40100–40149 (`WATCHDOG`, 300 ticks). Held-out, regime k = 1..3: persons
41000 + 1000k + (0..199), agents 41500 + 1000k + (0..199); 120 ticks.

**Confirmation** (only for a substrate that passes; failing it means W5-R2 fails on that substrate): every seed + 100000; for
persons, install hypothesis `calm_better` wherever the regime does not set one.

**Sealed prediction:** P(pass) = 0.35 on agents, 0.10 on persons (the trained person policy already stabilises everywhere,
so most person mechanisms add no new archetype).

#### W5b, transfer with a pilot that fills every gate cell (sixth attempt at positive transfer)

Level 0.05 / 6 = 0.0083 (two-sided 99.17% intervals); gate at one-sided 0.0083 / 4 per context. Certificates, roles, smoothed
context, gate, deployment, `W3C`, `NONE`, `ORACLE`, directions, pilot sizes and pass conditions as §11.5, except:

1. **Pilot.** Ticks 11–30 alternate the certified archetype and `BASE` on every visit to every certified context (the
   ablation that beat W5). A failure in context c makes the next visit to c run `BASE` regardless of alternation (extra
   baseline data where failure happened).
2. **`PILOT-ONLY`** uses the same alternation: the rotated archetype and `BASE` on alternate visits.
3. **`RANDOM-FUNC` replaces `RANDOM-CERT`.** In every certified context the certified archetype is replaced by a different
   non-Lion archetype: drawn uniformly from the target archetypes holding the other functions, or, if none differs, from all
   non-Lion archetypes other than the certified one; 20 draws (seeds 0–19), averaged. This control always differs from W5b.
4. **Ablation** (reported): W5b without the failure rule (pure alternation).

**Seeds.** Source: persons 45000–45049, agents v1 45100–45149, agents v2 45200–45249. Pilot repetition r: 16 seeds from
46000 + 16r (persons), 47000 + 16r (agents v1), 48000 + 16r (agents v2). Deployment: 49000–49199, 49200–49399, 49400–49599.
Oracle role reading: 49600–49649, 49700–49749, 49800–49849. Truth: 50000–50199, 50200–50399, 50400–50599.

**Passes** at pilot size 8 when, in at least two of four directions, W5b beats `PILOT-ONLY`, `NONE` and `RANDOM-FUNC`; in
all four it is non-inferior to `NONE` and `W3C`; the safety gate holds; the certificate audit holds (≤ 5% false). Confirmation
as §11.5 (seeds + 100000, person model v2 `arousal_deeper`).

**Sealed prediction:** P(pass) = 0.20.

#### LIA-G2, genealogy recovery with the architecture's parent rule (second attempt)

Level 0.05 / 2 attempts / 2 comparisons = 0.0125 (two-sided 98.75%). Data: the `REPURPOSE` runs of W5-R2 (held-out regimes),
committed changes only (probes and rollbacks are not changes of the deployed policy and are excluded from the planted set).
Inputs to the reconstructor as §11.5.

1. **Parent rule.** The parent of a change at T in context c is the *first* detected failure of a compatible kind in c since
   the previous policy-change time (the registry opens one node per kind and context per cycle — read as a property of the
   architecture, not from the registry). Fallback: first failure in c since the previous change; else none.
2. **Change detection.** Per context, mode counts in the windows before and after T (bounded by neighbouring change times)
   are compared with a G-test; a context is changed when p < 0.05 or mode changes within it fall by half or more.
3. `TEMPORAL` and `RANDOM` as §11.5, on the same detected slots.

**Passes** when `LIA-DIRECT2` beats `TEMPORAL` and `RANDOM` in paired per-run F1 and mean F1 ≥ 0.70. Reported beside it:
slot recall (share of planted (T, c) found) and parent accuracy given a correct slot.

**Sealed prediction:** P(pass) = 0.30.

#### Corpus v2: C1b, C6b, C4b and LSGPA re-entry tests R1, R2

Level 0.05 / 5 = 0.01 for each. Data, split (nodes 1–290 development, 291–580 held out) and privacy as §11.5.

- **Labelling by meaning, two labellers.** C1b and C6b candidates are labelled by reading: labeller A (Claude in this
  session) and labeller B (a separate model instance given only the written labelling instructions and the candidate turn
  with the turn before it, blind to A). Cohen's kappa ≥ 0.6 on the full candidate set is required; below it the test is
  inconclusive. Disagreements are resolved by a third read recorded with its reason; outcomes use resolved labels.
- **C1b correction loss.** Candidates: turns stating a quantified estimate about the person (rank, prevalence, percentile,
  rarity) or a claim about the assistant's own internals. Labels: claim key (free text normalised to a short phrase), value,
  and whether the turn corrects, softens or withdraws an earlier claim with the same key. Loss = a corrected claim restated
  later without its correction. Passes as §11.5 (loss rate interval above zero; `LineageMemory` ≥ 80% recall, ≤ 10% false flags).
- **C6b failure → mechanism.** Candidates: turns matching the §11.5 failure rule. Label: concrete failure event in this
  conversation (yes/no) as defined in the private file. Mechanism turns: labelled the same way (a newly named or revised
  protocol, module, anchor or rule — yes/no). Passes when the share of labelled failure events followed within 20 turns by a
  labelled mechanism turn sharing ≥ 2 content words exceeds the random-window baseline (1000 draws), p < 0.01.
- **C4b own-use adoption.** As §11.5 C4, counting a use only when it is not inside a verbatim ≥ 8-word span copied from the
  other party's earlier turns. Passes if above the shuffled baseline, p < 0.01.
- **R1 verbatim re-entry (LSGPA).** Statistic: share of user turns containing a verbatim ≥ 8-word span from the immediately
  previous assistant turn. Baseline: the same share computed against a random assistant turn at least 10 turns earlier
  (1000 draws). Passes when the observed share exceeds the baseline, p < 0.01, on the held-out half. *Disclosed:* the 28%
  figure was seen in exploratory analysis of this record, so R1 here only tests specificity to the previous output; its
  out-of-sample test is Phase 9 public data.
- **R2 re-entry propagates (LSGPA).** For user turns with a re-entered span, the share of the span's content words
  (≥ 5 letters, not stop words) present in the next assistant turn, compared with the same share for content words of a
  same-length span drawn from a non-re-entered assistant turn at least 10 turns earlier. Paired bootstrap over re-entry
  events; passes when the interval of the difference is above zero, on the held-out half.
- **C2 and C5** are not run again on this record; they are registered for multi-session data (Phase 9 or new private
  sessions) with the §11.5 definitions.

**Sealed predictions:** C1b 0.35, C6b 0.40, C4b 0.55, R1 0.90, R2 0.70.

### 11.7 Third round: W5c, W5-R3, LIA-G3 and LSGPA R3 — designs fixed before any code (14 November 2026)

**Origin, disclosed.** From the §11.6 results ([`results/r6b_summary.md`](results/r6b_summary.md)). Each change is to a
mechanism; no threshold, margin or safety rule is loosened, and the safety gate still applies against every registered
comparator. §11.5–11.6 results stand. Global rules as §11.5; smoke runs only on seeds outside the ranges below.

#### W5c, transfer with a spike guard in the pilot (seventh attempt at positive transfer)

Level 0.05 / 7 (two-sided 99.29% intervals); gate at one-sided 0.05 / 7 / 4 per context. Everything as W5b (§11.6), plus:

- **Pilot spike guard.** After the gate, a context whose candidate archetype had a higher spike rate per tick than `BASE`
  in that context in the pooled pilot is not adopted (`BASE` runs there). The comparators are unchanged (`PILOT-ONLY` has no
  guard), so the guard can only help W5c by preventing spikes, never by changing a comparator.

**Seeds.** Source: persons 51000–51049, agents v1 51100–51149, agents v2 51200–51249. Pilot repetition r: 16 seeds from
52000 + 16r (persons), 53000 + 16r (agents v1), 54000 + 16r (agents v2). Deployment: 55000–55199, 55200–55399, 55400–55599.
Oracle role reading: 55600–55649, 55700–55749, 55800–55849. Truth: 56000–56199, 56200–56399, 56400–56599. Confirmation as
§11.5 (seeds + 100000, person model v2 `arousal_deeper`). Pass conditions as W5b.

**Sealed prediction:** P(pass) = 0.30.

#### W5-R3, failure repurposing with no untested commits (third attempt)

Level 0.05 / 3 attempts / 3 regimes (two-sided 99.44% per regime). As W5-R2 (§11.6), except:

1. **Every mechanism is probed.** No mechanism commits without a test, including those that add no new archetype. During a
   probe the mechanism is switched on for alternate visits to its context (hysteresis: the widened band on alternate visits);
   mission scores of on-visits and off-visits in that context are kept in separate cells.
2. **Probes run until they can decide.** A probe is decided at the first window where both cells hold ≥ 5 ticks: it commits
   when the one-sided lower bound of (on − off) at level 0.0125 is above −0.01; it is closed `no_change` if it still lacks
   data after three cycles. One probe at a time per context.
3. **Longer runs:** 240 ticks per held-out run (same regimes; the E3 shift moves to tick 121).
4. Spike guard as W5-R2. `RANDOM-MECH` uses the same probes, matched on the number of proposals.

**Seeds.** Training: persons 60000–60049, agents 60100–60149 (`WATCHDOG`, 300 ticks). Held-out, regime k = 1..3: persons
61000 + 1000k + (0..199), agents 61500 + 1000k + (0..199). Confirmation as §11.6 (+100000; persons `calm_better`).

**Sealed prediction:** P(pass) = 0.25 on agents, 0.20 on persons.

#### LIA-G3, genealogy recovery from probe fingerprints (third attempt)

Level 0.05 / 3 attempts / 2 comparisons (two-sided 99.17%). Data: committed changes in the `REPURPOSE` runs of W5-R3.

- **Probe fingerprint.** Because every change is now probed, a committed change leaves a fingerprint in the trace before it:
  in its context, two modes (or a widened/narrow switching pattern) alternating on successive visits for at least one
  cycle. `LIA-DIRECT3` finds fingerprints (alternation share ≥ 0.6 over ≥ 6 visits in a context, ending at a policy-change
  time) and takes as parent the first detected failure of a compatible kind in that context before the fingerprint began
  (fallback: first failure in that context before it).
- Change slots also include the §11.6 G-test slots; `TEMPORAL` and `RANDOM` as before on the same slots.

**Passes** when `LIA-DIRECT3` beats `TEMPORAL` and `RANDOM` (paired per-run F1) and mean F1 ≥ 0.70.

**Sealed prediction:** P(pass) = 0.35.

#### LSGPA R3, re-entered words carry forward more than the person's own words (registered for Phase 9)

For each user turn that contains a verbatim ≥ 8-word span from the immediately previous assistant turn: the share of the
span's content words (≥ 5 letters, not stop words) that appear in the next assistant turn, minus the same share for the
user's own content words in the same turn (words not in the span). Paired bootstrap over events; passes when the interval is
above zero at level 0.01. **Run on public multi-session data only** (Phase 9, licence check first), because the effect was
first seen in this record (73% vs 30%, exploratory, §11.6 results). On this record it is reported as the origin, not a test.

**Sealed prediction:** P(pass on public data) = 0.75.

## 12. Prior art

See [`PRIOR_ART_WORLD.md`](PRIOR_ART_WORLD.md). Each component has precedent (micro-randomised trials and bandits for adaptive
choice, ego-state agent architectures, observer-based failure attribution). The claim under test is the combination: one
executable identity architecture run on a person through a wearable and on software agents, with per-archetype effects
estimated on both, and switching policies that transfer between them.
