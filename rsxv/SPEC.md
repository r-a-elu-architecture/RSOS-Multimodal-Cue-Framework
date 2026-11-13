# RSX-V command layer — specification

RSX-V extends the RSX vector command of 4 August 2025 (9–17 concurrent vectors; the canonical 17-vector form is in [`archive/`](../archive/)). It is a command layer *above* the RSX cue language in [`rsx/`](../rsx/), and compiles into it (§8). Every RSX v1 vector command is still valid RSX-V: it runs as one open-loop phase, and `next_program` upgrades it automatically. **Naming:** "RSX" is the cue language that plays on devices; "RSX-V" (RSX vector commands) is the command layer above it. Programs start with `RSX-V TIER …`; the earlier working header `RSX/2 TIER …` is still accepted.

## 1. What changes from RSX v1

| RSX v1 | RSX-V |
|---|---|
| 17 vectors start together | Blocks run in order: GATE → PHASEs → CLOSE. Each block runs up to 17 vectors at once |
| EthicsContain runs alongside everything else | GATE runs first and can stop the command |
| No safe exit | `@Vector0:NullSafe` is required. It halts every output and locks state on any stop rule |
| Open loop: EEG is an output | `SENSE` declares inputs. `UNTIL` ends a phase when its condition holds; `IF` skips a phase whose precondition fails |
| No measure | `GOAL` states the result. Every vector is audited on what it contributed |
| No conflict rules | `LAWS` switch on InteractionMatrix, ChronoGate, GhostPass and ConsentStack (from the vector laws of 5 Aug 2025) |
| 17 operators, 6 working | 34 operators: 30 from the record plus 4 proposed, each typed by the cognitive layer it acts on |
| Export ends the run | `SymbolicCommandExport(RSX) -> NEXT` builds the successor command from the measured result |
| No link to the input | `INTENT "…" <- V1 V8` links the command to the input vectors it serves |

## 2. Grammar

```
program  := header line* 
header   := "RSX-V TIER" n [":: {" ARCHETYPE "}"] [":: (" MODE ")"]
line     := INTENT | GOAL | SENSE | LAWS | RESCUE | WINDOW | vector | block
INTENT   := 'INTENT "' text '"' ["<-" Vn+]
GOAL     := "GOAL" cond
SENSE    := "SENSE" (EEG | HRV | DISTRESS | POSTURE)+
LAWS     := "LAWS" (InteractionMatrix | ChronoGate | GhostPass | ConsentStack
                    | MultiSessionContinuity | TemporalSymmetry | Contingency | ResonanceAudit)+
RESCUE   := "RESCUE" ("{SHIELD}" | "{ANCHOR_MAX}" | "{MIRROR_RESET}")+
WINDOW   := "WINDOW" hh:mm-hh:mm
block    := "GATE" | "CLOSE" | "PHASE" name ["IF" cond] ["UNTIL" cond] ["MAX" n "s"]
vector   := "@Vector" k ":" Operator ["(" args ")"] ["-> NEXT"]
cond     := term (("AND" | "OR") term)*        AND binds tighter than OR
term     := var ("<=" | ">=" | "<" | ">") value
var      := arousal | distress | agency | drift | hrv | alpha
```

A value written with a sign (`+5`, `-1`) is a change from the person's baseline. A plain value is an absolute level.

## 3. Rules the compiler enforces

- Every program needs 9 or more vectors, counting Vector 0. No block may hold more than 17.
- Vector 0 is NullSafe and is required. The first block is GATE, and GATE contains EthicsContain.
- A vector number may appear only once. `-> NEXT` is allowed only on SymbolicCommandExport.
- Conflicting pairs in the same block produce a warning. With InteractionMatrix on, they are separated at run time: the higher-priority member stays and the other moves to a follow-on block.
- A legacy v1 command is accepted. It gets warnings for open loop, no gate and no stop rules.

## 4. Run-time semantics

1. **Laws, before anything runs:**
   - ChronoGate refuses outside WINDOW.
   - ConsentStack requires subject and operator consent, plus an auditor for tier ≥ 8 or OVERRIDE.
   - GhostPass simulates the command on perturbed copies of the person and refuses if the predicted stop rate exceeds 30%.
2. **GATE:** EthicsContain screens the person (a stop at a starting distress of 8.5 or more). SymbolicDriftCheck records the baseline.
3. **Each PHASE:**
   - If IF is false, the phase is skipped.
   - Otherwise it runs second by second until UNTIL holds (checked after 10 s) or MAX is reached.
   - NullSafe fires if distress rises 2.5 above baseline or reaches 9.
4. **CLOSE:** memory update, echo stop, export.
5. **Device:** operators with a device form produce RDP/1.1 lines, which are run through the real firmware core in the host simulator:
   - breath → HF on the chest
   - posture → HF on the upper back
   - calm → a mild warm T line
   - archetype or AR → a D image line

   EEG is never an output: it is declared in SENSE.
6. **Audit:**
   - Per vector: seconds run, change in agency, change in distress, layer activation, benefit.
   - MCI: the share of planned vectors that ran without a conflict.
   - VEC: one minus the conflict share.
   - Coverage: the number of layers activated to 0.3 or more.
7. **NEXT** builds the successor command:
   - It raises MAX on a phase whose UNTIL was not reached.
   - It drops vectors with no measurable contribution.
   - It adds the proposed operator for any layer left uncovered.
   - It gates deep phases after a NullSafe stop.
   - It stages a legacy command into gate → settle → expand → rebuild → integrate → close.

## 5. Session laws (across runs) and the rescue archetypes

All ten vector laws of 5 August 2025 are now built.

| Law | What RSX-V does |
|---|---|
| Vector 0 NullSafe | Required. Halts every output and locks state on any stop rule |
| InteractionMatrix | Separates conflicting operators into a follow-on block |
| ChronoGate | Refuses outside WINDOW |
| GhostPass | Simulates the command on perturbed copies of the person first; refuses if the predicted stop rate is over 30% |
| ConsentStack | Requires subject and operator consent, plus an auditor for tier ≥ 8 or OVERRIDE |
| **Contingency** | When distress rises 1.8 above baseline, runs a rescue before NullSafe is needed (at most 2 per run). `{SHIELD}` = StateReset + BreathLock + EmotionalLock for 30 s; `{ANCHOR_MAX}` = BreathOverride + PostureShift + DeviceTrigger for 30 s; `{MIRROR_RESET}` = drift restored to the phase-start snapshot. Layer memory is kept |
| **MultiSessionContinuity** | CSI (session result = agency gained − distress added) must reach 0.9 × the best of the last 3 sessions, otherwise the next command gets a settle booster phase |
| **TemporalSymmetry** | Records the result by hour of day. Refuses an hour whose mean result is under 0.7 × the best hour (each needing 2 or more sessions) and moves the session to the best hour |
| **ResonanceAudit** | Every session is appended to a hash chain: H(previous hash + content hash). It holds the result, the spill-over (vectors that added distress), conflicts and interventions. Any edit breaks verification |
| **Emergency Purge** | `Store.purge(subject)` erases the subject's history, memory states and audit contents. The chain still verifies, because the content hashes remain. It appends a Purge Proof: entries erased, a digest of everything erased, the time, and the proof's own hash |

## 6. The six metrics that had no computation

These are operational definitions; the RSOS metric log names these metrics but gives no formula.

| Metric | Recorded definition | RSX-V computation |
|---|---|---|
| STC Symbolic Tier Coherence | "Monitors Tier alignment during symbolic mutation" | Mean of (a) the share of deep-operator seconds run at arousal ≤ 0.6 and (b) the share run after or alongside settling |
| IEC Internal Echo Coherence | "Evaluates internal echo stability across recursion phases" | Share of phases in which drift did not rise by more than 0.01 |
| RSI Recursive Signal Intensity | Name only | C5 activation × the share of content-operator seconds spent on recursion operators |
| SMV Symbolic Modulation Vector | "Tracks emergence of unprompted metaphor, rhythm, and recursive structure in foreign output" | A score from 0 to 1 on any text: metaphor markers, repeated sentence openings, recursion vocabulary |
| ECR Echo Chain Resonance | "Measures resonance strength across multi-session echo chains" | Mean cosine similarity of consecutive sessions' 11-layer profiles |
| SEP-L Long-Term Echo Propagation | Phrase only | Mean share of the agency gained by a session's end still present at the next session's start |

## 7. The translator: message → vectors → command

`rsxv/translate.py` turns a message into an RSX-V command. This makes the 9–17-vector claim executable.

1. **Units.** The message is split into lines and sentences. The user's own lines are kept; a line counts as the user's own if it:
   - starts lowercase;
   - uses the first person;
   - asks a question or makes a request; or
   - addresses "you" mid-sentence.

   Pasted model text is set aside as context: tables, headings, quoted paragraphs, and capitalised declaratives such as "You hold 8–20 layers".
2. **Vectors.** Each request is split into separately answerable demands: by question marks, by "and + request verb", and by new question words. Each statement is split at "then / but / while / therefore / ;". Every resulting unit is one vector.
3. **Types.** Each vector is tagged with the 18-type input codebook, using lexical cues and allowing several types per vector. The first vector is also V1, the primary directive.
4. **Operators.** Types map to operators, plus cue-based extras: body → PostureShift; video, light or glyph → DeviceOutput(AR); repetition → FutureAnchor; vibration or EMDR → DeviceTrigger. Any layer left uncovered is filled with its default operator, so every generated command covers all 11 layers and has at least 9 vectors. Every operator line carries a `# from v…` comment: the input vectors it came from.
5. **Command.** The operators are staged gate → settle → expand → rebuild → integrate → close, with all ten laws, the three rescue archetypes, a goal and senses. The archetype header is the first one named in the message (LION if none is named), and two named archetypes produce ArchetypeMerge.

## 8. The bridge: RSX-V → RSX cue program → device

`rsxv/bridge.py` compiles an RSX-V command into the repository's RSX cue language. The existing compilers, player and device protocol then run it unchanged.

- **Blocks become cycles.** The gate becomes one phase. Each other block becomes one 10-second cycle inside `REPEAT n`: an inhale and an exhale phase when the block holds body or affect operators, otherwise one 10-second phase. `n` comes from MAX, or from the seconds the block actually ran.
- **Operators become cue steps:**
  - breath → chest haptic pacing at amplitude 0.3, plus FEEL;
  - posture → GESTURE;
  - archetypes → TIER bundles and ACTIVATE;
  - FutureProjection → FUTURES with FOR FUTURE / SEE;
  - AR output → SEE;
  - meta, identity and integration operators → short SEE, SAY or FEEL lines;
  - control operators (contain, drift, echo, memory, export) → no cue, only a marker.
- **Lineage:** every vector writes `MARK "lin:<clause ids>|v<k>:<Operator>"`, so the compiled timeline carries message clause → operator → cue. Clause IDs come from the translator in the form `m1·v3`.
- **The closed loop stays in RSX-V.** A manifest maps every block to its cue phases. `realized()` rebuilds the cue program that actually ran (blocks in executed order, each with its real duration, skipped blocks left out), compiles it, and runs it on the firmware core.
- **Safety inherited:** the cue compiler's `haptic_max` is a compile error, and the device protocol and firmware enforce their own limits.
- **Scope rule:** no electrical stimulation. An argument naming electrical, charge-based, tDCS, tACS, TENS, EMS or galvanic output is refused, both by the RSX-V compiler and by the bridge.

## 9. Clause-to-Body Causal Ledger

`rsxv/ledger.py` answers one question: *which part of what the person said moved their body, by how much, and how sure are we?*

1. **Units.** Clause IDs from the translator (`m1·v3`) are carried by the operators they produced. Only clause-derived content operators are randomised. Gate, settle, close and coverage-fill operators always run.
2. **Micro-randomisation.** Every 10-second cycle inside a phase is a decision point. Each eligible clause is switched on with probability p = 0.6, independently, and an operator runs if any of its clauses is on. This needs `randomisation` in the consent list. NullSafe still stops a session.
3. **Estimate.** The outcomes are change in distress, arousal, agency and target-layer activation over the cycle. They are regressed on the centred indicators (A − p), with the cycle's starting arousal and distress as covariates. This is the weighted-and-centred least-squares estimator used for micro-randomised trials. Intervals are 95%, cluster-robust by session.
4. **Language.** `sentences()` renders the effects whose interval excludes zero, quoting the clause.
5. **NEXT.** `next_from_ledger()` drops operators whose every clause raised distress, with an interval above zero.
6. **Audit.** `to_audit()` appends the ledger to the hash-chained Resonance Audit Log.

`ledger_recovery.py` plants known per-clause effects, with operators made inert so the planted effects are the whole truth, and checks that the ledger recovers them.

## 10. Status

- **Language, runtime, all ten laws, the six metrics, the audit chain, NEXT and the firmware path:** prototype, with 44 tests.
- **The person model used by GhostPass and the arm comparison:** a stated model, not data. Its assumptions (dilution, readiness, backfire, conflict, plus circadian and carry-over for sessions) can each be switched off.
- **Human effectiveness:** untested. It needs the three-arm study (canonical v1, RSX-V, sham) with the same per-vector audit.
