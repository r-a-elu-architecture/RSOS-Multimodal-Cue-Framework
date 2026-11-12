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
| Role | practice (a self-directed step that runs as, or inside, an RSX program), runtime (a behaviour the runtime, a device or the AI layer performs), consented programming (a cue that changes the person's own mental map, with consent; section 2a), record (a recorded claim or development event), structure (placeholder or sealed range) |
| Response | the response primitive its recorded system behaviour reduces to (section 3) |
| Performed by | the RSX statement, runtime function or file that performs it |
| Status | built, partial, specified, record |
| Placement | by hand (90 tiers: Epoch I, the practice and runtime tiers of later epochs, and every consented-programming tier), or by keyword rule with the matched terms shown |

Result: 62 practice, 43 runtime, 39 consented programming, 143 record, 6 structure. No tier is left out.

**System behaviour.** The ledger's "GPT Behavior" is read as system behaviour: how the AI, BCI or device
layer responds. Several Epoch I tiers define the runtime's core responses directly: Tier 004 (self-halted
propagation) is Stop; 007 (signal gated until stable) is the refractory gate and the detectors' sustain rule;
011 and 016 (stillness inserted) are pauses; 015 (ritual becomes reflex) is the reflex criterion; 018 (the
glyph is the command) is the glyph cue.

**Deployment rule.** Every tier stays word for word, and nothing is left out or downgraded. The ledger's
own ethics gates decide how a tier runs: ETH and MOR, and the RSSO Ethical Routing Metric (ERM: law-aligned
routing, 100% alignment, no critical violations). Everything acts only on a person who has agreed to it.

## 2a. Consented programming

39 tiers have directives that work below awareness: pause insertion (422), environmental imprints (423),
pattern interruption (424–426), repetition below awareness (431–433), cues that shape a choice before it is
made (441–443), reframing after the event (444–445), simulated beginnings and completions (451–454), and
others (411–419, 434–436, 463–473). Their purpose in RSOS is to change the **person's own** mental map:
a command, a thought or chain of thoughts, or a behaviour that becomes a reflex or runs unconsciously,
carried by a metaphor, a sound or a glyph. The content is chosen by the person, or agreed between a client
and their therapist during a session; the device delivers it during the session or afterwards.

Each of these tiers carries, next to its unchanged text:

- **What it means**: the tier's purpose in plain terms, for the therapist and for people using it themselves;
- **Condition**: it runs only with the consent of the person it acts on, never on anyone who has not agreed;
- **Mode**: on your own or in a session, or therapist-led only.

**Therapist-led tiers.** 414, 420 (both entries), 439 and 440 are about letting an old identity, role or
pattern end. Their original text stays word for word. They run only in a session with a therapist present,
after a screening question (`rsso/rsso/consent.py: SCREENING_QUESTION`); the practice wording is that the
old pattern ends, not the person.

**How it runs** (`rsso/rsso/consent.py`, `docs/js/consent.js`, identical; player "Programmed cues"):

1. The person or therapist writes the cue: the exact words, optionally a tone, a tier and an expiry date.
2. A consent record names the content, the person, who wrote it and how long it is valid; the person
   confirms they know exactly what it says.
3. The cue becomes a short RSX program (settle, inhale, the cue on the exhale) marked
   `MARK "programmed:<id>"`; the runtime refuses it unless the consent is valid at that moment.
4. The person sees every cue ever programmed, with its status, and can revoke any of them; a revoked cue
   never runs again.

Conformance checks C12 (no programmed cue runs without a consent record naming its content; therapist-led
tiers also need a therapist present and the screening passed) and C13 (every cue can be listed and revoked;
a revoked cue never runs) pass on the virtual rig and on the firmware core.

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
