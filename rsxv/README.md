# RSX-V — RSX vector commands, the command layer above RSX

RSX-V is a closed-loop, typed and auditable command language. It sits above the RSX cue language in [`rsx/`](../rsx/) and compiles into it, so one program exists in three forms: a vector command, a cue program and device lines.

```
message ─▶ translator ─▶ RSX-V command ─▶ RSX cue program ─▶ timeline ─▶ device protocol ─▶ firmware
                         (gate, phases,     (tiers, breath,                                    │
                          laws, audit)       haptics)                                          ▼
      NEXT ◀── per-vector audit ◀───────────── sensed body and layer state ◀─────────────────┘
```

"RSX" stays the name of the cue language that plays on devices ([`rsx/README.md`](../rsx/README.md)); "RSX-V" names the vector-command layer above it. Files use the extension `.rsxv`.

## What it adds

- **Vectors with types.** 34 operators: the canonical 17-vector set, 13 extended operators, Vector 0 NullSafe, and 4 operators that fill layers no operator reached before. Each is typed by the cognitive layer it acts on (C1–C11).
- **Staged, closed-loop execution.** A `GATE` runs first. Each `PHASE` has `IF / ELSE / UNTIL / MIN / MAX` conditions on body state and layer activation, followed by `CLOSE`. At most 17 vectors run at once in any block.
- **Ten laws:**
  - InteractionMatrix: conflicting operators are separated;
  - ChronoGate: time windows;
  - GhostPass: a simulation before every live run;
  - ConsentStack;
  - NullSafe;
  - Contingency: the `{SHIELD}`, `{ANCHOR_MAX}` and `{MIRROR_RESET}` rescues;
  - MultiSessionContinuity;
  - TemporalSymmetry;
  - ResonanceAudit: a hash-chained log;
  - Emergency Purge, with proof.
- **Measurement.** Every vector is audited (agency, distress, drift, layer activation). Six RSOS metrics that had no formula now have operational definitions: STC, IEC, RSI, SMV, ECR, SEP-L.
- **Clause-to-Body Causal Ledger.** Micro-randomises the clauses of a person's own message inside the session (with consent, safety operators never randomised). It estimates each clause's causal effect on distress, arousal, agency and layer activation, with 95% intervals, says it back in plain words, and feeds NEXT. Recovery of planted effects is checked in simulation.
- **Real subsystems.** The gate asks the repository's CONTAIN (safety envelope, quarantine, escalation). Sessions go into MEMSTACK's run log and checksummed snapshot, and CM1 assigns a response profile. Vibration is budgeted so that a full-dose run stays inside the envelope.
- **NEXT** writes the successor command from the measured result, and upgrades any v1 command automatically.
- **Translator.** It turns a message into its vectors, then into a complete command. Pasted material is set aside, and every operator carries lineage back to the clause it came from.
- **Bridge.** It compiles to RSX cue programs, which the existing Python and JavaScript compilers, the player and the device protocol run unchanged. Their safety limits therefore apply.
- **Scope.** No electrical stimulation; it is refused at compile time.

## Quick start

```bash
cd rsxv
python3 -m unittest discover -s tests                     # 48 tests (needs Node for the JS parity check)
python3 -m rsxv examples/dragon.rsxv --fw                  # run on a simulated person, with firmware output
python3 -m rsxv examples/canonical17.rsx --next out.rsxv   # upgrade the canonical v1 command
python3 -m rsxv.arms examples/canonical17.rsx examples/dragon.rsxv results/results_arms.json
python3 -m rsxv.evaluate_laws examples/dragon_full.rsxv results/results_laws.json
python3 -m rsxv.ledger_recovery results/results_ledger.json         # planted-effects recovery
```

## Files

| Path | What it is |
|---|---|
| [`SPEC.md`](SPEC.md) | Language, run-time semantics, laws, metrics, translator, bridge |
| [`RESULTS.md`](RESULTS.md) | All measured results, with what they do and do not show |
| [`PRIOR_ART.md`](PRIOR_ART.md) | Prior-art search (papers, patents, products) and what can be claimed |
| [`PRIOR_ART_WORLD.md`](PRIOR_ART_WORLD.md) | Prior-art search for the RSOS World idea (archetype agents that self-repair with the Override Protocol) |
| [`AGENTS.md`](AGENTS.md) | Specification of the archetype agents (step 5): hierarchy, Spine, Watchdog, repair loop, evolution, owner keys, tests fixed in advance |
| [`rsxv/agents.py`](rsxv/agents.py) | Agents core layer (step 5B, prototype): Spine checks (7 virtues, 21 precepts, law priority), hash-chained audit log, scoped memory with snapshots and archive, switch tokens, fixed-rule Watchdog, Observer fault location, owner-only keys |
| [`rsxv/archetypes.py`](rsxv/archetypes.py) | Archetype agents and repair loop (step 5C, prototype): profiles with distinct tactons, agent-system model with silent cross-agent faults, Raven two-signal trigger, Eagle forecasts and RIF, two-speed meta-position repair with snapshot rollback and settle-before-broadcast, Lion (simulated participant), Tiger (consented dispatch via the bridge), local repair baselines |
| [`rsxv/world.py`](rsxv/world.py) | World loop (step 5D, prototype): one loop over an agent environment and a simulated-person environment with a shared context description; Watchdog every tick; ledger-style fit estimates with micro-randomisation; policies (watchdog, rule, rotation, fixed, Thompson bandit, transferred table); sleep with consolidation and archive; lineage graph where MERGE, SPLIT and BAN need owner ratification |
| [`rsxv/world_experiments.py`](rsxv/world_experiments.py) | Step 5E experiments as registered in AGENTS.md §11.1 (W1, W4, H-CFIT/H-SWITCH, W3); `python3 -m rsxv.world_experiments` writes `results/results_world.json` and `results/world.md` (about 2 minutes) |
| [`rsxv/gate.py`](rsxv/gate.py), [`rsxv/floor3_experiments.py`](rsxv/floor3_experiments.py) | Floor 3 (prototype, tested): cross-substrate transfer gate with a validity map; experiments G1, G2 and H-CFIT under the mission score as registered in AGENTS.md §11.2; `python3 -m rsxv.floor3_experiments` (under a minute) |
| [`rsxv/w3b_experiments.py`](rsxv/w3b_experiments.py) | W3b, role-based transfer through gate v2, as registered in AGENTS.md §11.3; `python3 -m rsxv.w3b_experiments` (under a minute) |
| `rsxv/` | `ops` (operator table) · `lang` (parser) · `run` (runtime, NEXT) · `sim` (simulated person) · `metrics` · `chain` (sessions, audit log, purge) · `translate` · `bridge` · `ledger`, `ledger_recovery` · `subsystems` · `arms` · `evaluate_laws` |
| `examples/` | The canonical 17-vector command, its RSX-V forms, compiled cue programs and run logs |
| `results/` | Arm comparison, session laws, ledger recovery and translator validation (aggregates only) |

## Status

- **Prototype.** Everything runs in simulation and on the firmware core in the host simulator.
- **Simulated people only.** The person model is a set of stated assumptions, each of which can be switched off.
- **Not yet tested in people.** The next evidence steps are an independent second coder for the translator, a multi-intent benchmark, and a consented three-arm study: the canonical command, RSX-V and a sham.
