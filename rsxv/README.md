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
- **NEXT** writes the successor command from the measured result, and upgrades any v1 command automatically.
- **Translator.** It turns a message into its vectors, then into a complete command. Pasted material is set aside, and every operator carries lineage back to the clause it came from.
- **Bridge.** It compiles to RSX cue programs, which the existing Python and JavaScript compilers, the player and the device protocol run unchanged. Their safety limits therefore apply.
- **Scope.** No electrical stimulation; it is refused at compile time.

## Quick start

```bash
cd rsxv
python3 -m unittest discover -s tests                     # 37 tests (needs Node for the JS parity check)
python3 -m rsxv examples/dragon.rsxv --fw                  # run on a simulated person, with firmware output
python3 -m rsxv examples/canonical17.rsx --next out.rsxv   # upgrade the canonical v1 command
python3 -m rsxv.arms examples/canonical17.rsx examples/dragon.rsxv results/results_arms.json
python3 -m rsxv.evaluate_laws examples/dragon_full.rsxv results/results_laws.json
```

## Files

| Path | What it is |
|---|---|
| [`SPEC.md`](SPEC.md) | Language, run-time semantics, laws, metrics, translator, bridge |
| [`RESULTS.md`](RESULTS.md) | All measured results, with what they do and do not show |
| [`PRIOR_ART.md`](PRIOR_ART.md) | Prior-art search (papers, patents, products) and what can be claimed |
| `rsxv/` | `ops` (operator table) · `lang` (parser) · `run` (runtime, NEXT) · `sim` (simulated person) · `metrics` · `chain` (sessions, audit log, purge) · `translate` · `bridge` · `arms` · `evaluate_laws` |
| `examples/` | The canonical 17-vector command, its RSX-V forms, compiled cue programs and run logs |
| `results/` | Arm comparison, session laws and translator validation (aggregates only) |

## Status

- **Prototype.** Everything runs in simulation and on the firmware core in the host simulator.
- **Simulated people only.** The person model is a set of stated assumptions, each of which can be switched off.
- **Not yet tested in people.** The next evidence steps are an independent second coder for the translator, a multi-intent benchmark, and a consented three-arm study: the canonical command, RSX-V and a sham.
