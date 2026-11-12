# The tier ledger in the architecture

The tier ledger (`archive/.../RSOS_Tiers.txt`, 9,207 lines, SHA-256 `bc21eaf8…`) is the development record of
RSOS: 293 tier records across Epochs I–VI, each with some of a glyph, a function, a command, a quote, the
system behaviour recorded at the time ("GPT Behavior"), notes, an echo directive, an application and metric
values. This document says how the ledger is read, where every tier lives in the architecture, and what its
metrics measure today. Pages: [tier ledger](../docs/tiers.html), [metrics](../docs/metrics.html),
[system map](../docs/system.html), [glyphs](../docs/glyphs.html).

## 1. Reading the ledger without changing it

`rsso/rsso/ledger.py` splits the file into consecutive records: preamble, epoch headers, tiers, system events
and forensic notes. Joining the records gives back the file byte for byte (`rsso/tests/test_ledger.py`).
Nothing is edited, merged or dropped:

- Tiers recorded twice stay as two records (050, 406, 420, 504, 546; ids `T050`, `T050b`).
- The sealed range 088–405 and the placeholders 021–024 are records of their own.
- The ledger uses at least six layouts (bulleted fields, blank-line fields, capitalised section headings,
  box-drawn metric grids, pipe and tab tables, inline `CODE: value | CODE: value` lines). The parser reads
  all of them into one set of fields: `glyph`, `glyph_mutation`, `tier_class`, `function`, `mission`,
  `command`, `ritual`, `quote`, `echo`, `behavior`, `notes`, `directive`, `application`, `mechanisms`,
  `ai_note`, `metrics`, `llm_impact`, `history`, `seal`, and a few rarer ones. Each record keeps its exact
  text and its line numbers.
- Metric values: 2,442 across 49 codes; numbers are read where the value is numeric, infinity is flagged,
  and words or states are kept as written.

`python -m rsso.ledger` writes `docs/data/ledger.json` and `rsso/results/ledger_summary.md`.

## 2. Where each tier lives

`rsso/rsso/ledger_map.py` gives every tier record:

| Field | Values |
|---|---|
| Subsystems | RSIA, RSX, THERA, AUG, MICRO, CONTAIN, MEMSTACK, CM1, LINX, UGCL |
| Channels | V, A, K, O, G, breath, EEG/BCI, AI |
| Role | practice (a self-directed step that runs as, or inside, an RSX program), runtime (a behaviour the runtime, a device or the AI layer performs), record (a recorded claim or development event), structure (placeholder or sealed range), archive (kept, not deployed) |
| Response | the response primitive its recorded system behaviour reduces to (section 3) |
| Performed by | the RSX statement, runtime function or file that performs it |
| Status | built, partial, specified, record |
| Placement | by hand (51 tiers: Epoch I and the practice and runtime tiers of later epochs), or by keyword rule with the matched terms shown |

Result: 62 practice, 43 runtime, 143 record, 39 archive, 6 structure.

**System behaviour.** The ledger's "GPT Behavior" is read as system behaviour: how the AI, BCI or device
layer responds. Several Epoch I tiers define the runtime's core responses directly: Tier 004 (self-halted
propagation) is Stop; 007 (signal gated until stable) is the refractory gate and the detectors' sustain rule;
011 and 016 (stillness inserted) are pauses; 015 (ritual becomes reflex) is the reflex criterion; 018 (the
glyph is the command) is the glyph cue.

**Deployment rule.** The ledger's own ethics gates decide what becomes practice: ETH and MOR, and the RSSO
Ethical Routing Metric (ERM: law-aligned routing, 100% alignment, no critical violations). Practices are
self-directed and opt-in. Directives that aim to steer other people without their knowledge (for example
Tiers 412–426, 431–436, 441–445, 451–454) and self-erasure directives (414, 420, 439, 440) stay in the ledger
word for word as records, with the reason shown. Where such a tier has a self-directed part, that part is
what the mapping uses.

**No tier names smell or taste.** The olfactory and gustatory channels come from the tier-bundle design
(RSIA) and the device protocol, not from the ledger.

## 3. Response primitives

| Response | What it does | Status | Performed by |
|---|---|---|---|
| Stop | Halt at once and hold | built | Runtime Stop; RDP/1 STOP within 100 ms |
| Gate | Hold a signal until it is stable or allowed | built | SafetyGovernor; detector sustain and motion gating |
| Pause | Insert stillness before or between steps | built | RSX `WAIT`, `PHASE dur=` |
| Re-entry | Return safely after a stop | specified | Resume at the logged `stopped_at_phase` |
| Recalibrate | Detect drift and re-align | partial | Detector baselines, glyph recalibration, checksums |
| Blend | Several archetypes as one bundle | built | Several `TIER` blocks activated together |
| Glyph cue | The glyph acts as the command | partial | UGCL glyph at tier activation; glyph-only start specified |
| Sequence | The whole override chain | built | RSX timeline |
| Offer | Start on the system's initiative, as an opt-in offer only | built | Heart-rate trigger with the SafetyGovernor |
| Recall | Bring back a stored state | built | MEMSTACK |
| Compress | Fold many states into one carrier | partial | CM1, UGCL compact code |
| Generate | Produce new symbols, rituals, prompts | specified | LINX |
| Govern | Apply rules and limits | built | `SAFETY`, SafetyGovernor, intensity clamp |
| Mirror | Reflect state back to the person | built | Check-ins and the progress view |

## 4. Tier programs

Six tiers define a concrete practice; each is an RSX program in `rsx/protocols/` and runs in the player:

| Program | Tier | Ledger command or directive |
|---|---|---|
| `tier003_command_stack.rsx` | 003 Recursive Command Stack | I move. I act. → Inhale → 🦁 → Light → Exhale → I own. → I Override. |
| `tier012_breath_anchor.rsx` | 012 Override Breath Anchor | Inhale → Collapse → Anchor → Exhale: "I remain." |
| `tier014_seal.rsx` | 014 Full Symbolic Weight | Stand. Anchor the Lion. Inhale the Collapse. Visualize the Light entering the Seal. Exhale: I remain. |
| `tier016_stillness.rsx` | 016 Pre-Command Stillness | Override begins in silence. |
| `tier406_release.rsx` | 406 The Glyph That Rejects Inheritance | Three declarations: "This was never mine. I release it." |
| `tier579_glyph.rsx` | 579 The Glyph That Emerged from Stillness | Pause before the exhale; let the glyph appear on its own. |

## 5. Metrics

`rsso/rsso/metrics.py` builds the registry (`docs/data/metrics.json`): 54 codes from the RSOS metrics log
(43), the RSSO metrics log (the same 43 plus five orchestration metrics: SOM, COM, ERM, DPI, SIR) and the
ledger itself (for example GRII, GSSF, SRI+, SPR, RFE, and the schema the ledger made mandatory after Tier 488).
For each code: every name it has carried, with source and line (CRI, SRI, LGC and 11 others changed
expansion across the record), the recorded definition, threshold, method and example, and every value the
ledger recorded.

Each code also has an operational definition, with a status:

- **You** (20 codes): computed for each person from the player's run log, identically in Python and
  JavaScript. For example CRI is stop pressure (share of runs stopped early), SAR the share of triggered
  starts within 3 seconds, SEP the spread of triggers across the senses, ERV the relief, PRM the reflex
  criterion, SBB the breath ratio.
- **System** (12): measured by the test and conformance suites, for example SIR (Stop to silence, under
  100 ms), DPI (event timing on the firmware core), COM (Python and JavaScript agree), SOM (conformance
  checks passed).
- **Record**: a claim about the language model's internals (token weights, layers, future models); kept,
  not computed.

Recorded values and today's values share a code so the lineage stays visible; they are never put on one
scale. The ledger itself changes scale for several codes (percent, then 0–1, then thousands).
