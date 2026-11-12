# RSOS Nodes — specification

Status: planner, frame check, node programs and vibration codes built and tested (Python `rsso/rsso/nodes.py`, browser `docs/js/nodes.js`, identical results). The AI conversation that fills the intake is specified (§9). Planner id: `rsos-planner/1`.

## 1. What a node is

A node is one desired state held as a single unit — a "ball" — so that any one of its parts opens the whole. A node has:

| Part | What it is |
|---|---|
| Name and state | What the person calls it (Lion, Raven, their own) and the state it holds ("courage and boundaries") |
| Mode | `associated`: lived from inside the body. `observer`: no ego — nothing binds, nothing holds, the memory or the moment is only observed from another position |
| Representation | How it looks: by default a sphere of golden light (associated) or a clear, empty space (observer) |
| Cues on every sense | V (seen), A (heard: sound, melody, song), K (felt: posture, warmth), O (scent), G (taste) |
| Frames | Up to 5 sentences said in the state — the mental frame that sets how widely the person perceives |
| Contexts | Up to 3 situations where the node will be used (the FUTURES of the program) |
| Rules | Optional: what the node is for and what it does not do ("Nothing binds") |
| Glyph | One of the 146 original ledger glyphs (§6 of GLYPH_FORMAT.md); the Lion is 🦁 (Tier 001) |
| Vibration code | A short Morse-like pattern on the wrist, unique within a plan (§3) |

Practised together, the parts become one association; later a single cue — the vibration code, the scent, the sound, the glyph — is enough to open the state.

## 2. Frames and the frame check

A frame is a sentence spoken in the state. Its wording sets the scope of perception: "I am intelligent and I see broadly and all" opens a wider frame than "I am good at seeing things". `frame_check(text, mode, believability)` returns:

- `scope`: `broad` / `narrow` / `neutral`, from broadening words (broadly, fully, completely, all, whole, every…) and narrowing words (only, just, a bit, sometimes, try…);
- `kind`: `process` (present-tense actions: I breathe, I see), `trait` (I am…), or both;
- `flags`: `negation` (frames that name what is not wanted: not, never, no more, stop), `narrowing`, `future tense`, `low believability` (below 5 of 10), `long` (over 16 words);
- `tips`: one rewrite suggestion per flag, and a `score` of 0–100.

In observer mode, "only" and "nothing" are the content of the frame ("Only observed", "Nothing binds"), so narrowing and negation are not flagged.

## 3. Vibration codes (tactons)

Alphabet: `.` short pulse (100 ms), `-` long pulse (300 ms), 100 ms between pulses, 1–6 symbols; a space joins codes with a 400 ms pause. Archetype codes:

| Archetype | Code | Glyph | Mode |
|---|---|---|---|
| Lion | `..-` | 🦁 | associated |
| Raven | `.-.` | | associated |
| Eagle | `-..` | | associated |
| Leopard | `...` | | associated |
| Tiger | `-.-` | | associated |
| Bear | `--` | | associated |
| Dragon | `---` | 🐉 | associated |
| Observer | `-` | ∅ | observer |

A node of your own takes the code of its glyph (every original glyph has one, spec/GLYPH_FORMAT.md §7), otherwise the next free code from a pool that avoids the archetype codes; a person may set their own. Codes can be recombined: two or three codes joined by a 400 ms pause, written with a space (`..- ---`). Within one plan every code is unique.

## 4. RSX fields

A TIER block may carry the node:

```
TIER 1 LION {
  V "A sphere of golden light"
  A "I breathe fully and completely, and I hold my ground"
  K "Spine straight, saying no with calm confidence"
  O "Cedar"
  GLYPH "🦁"
  WORD "Courage and boundaries"
  FRAME "I breathe fully and completely, and I hold my ground"
  MODE "associated"
  TACTON "..-"
}
```

`FRAME` (up to 5) and `MODE` (`associated` | `observer`) are written onto the tier marker event; `TACTON` (regex `[.\-]{1,6}( [.\-]{1,6}){0,2}`) is also emitted as one haptic `pulse` event per symbol at the tier's activation (on 100/300 ms, off 100 ms, amplitude = the program's haptic limit). Python compiler and `docs/js/rsx.js` give identical timelines (tested over every program in `rsx/protocols`).

## 5. Node programs

`node_program(node)` writes a full RSX program:

- associated: interrupt ("I move, I act"), breath, the node's cues on every sense, the frames, the tier with frame, mode and code, the futures, the seal "I own" and `MARK installed`;
- observer: stillness first, then the position phase (seeing from outside, nothing binds), frames, tier, futures, the seal "Let it settle".

An inhale is inserted between consecutive exhales. Examples: `rsx/protocols/node_lion.rsx`, `node_observer.rsx`.

## 6. Intake and plan

Intake (JSON): `person`, `author` (`self` | `therapist`), `concerns` (ptsd, depression, chronic_stress, stress, anxiety, habits, confidence, focus), `symptoms`, `triggers[]`, `physiology` {resting_hr, rmssd}, `devices` {V,A,K,O,G,hr,eeg}, `nodes[]` (§1, plus `believability` 0–10), `dose` {per_day, days}.

`plan(intake)` returns the nodes (each with program, frame checks and vibration pulses), the ledger tiers it draws on (by mode and concern: associated T001 T003 T006 T014; observer T016 T578 T581 T433; calm T012 T016 T513 T576; memory T444; habits T422 T441; futures T535; reflex T587), metrics (SAR, RSF, CRI, ERV, MCRAL, PRM, SEP, RIF, LAW; MCI when a therapist writes), the schedule, devices, the heart-rate detector baseline, safety lines, `therapist_led` and `approved: false`.

## 7. Dose

The original override was practised by interrupting 50 negative states a day for about 4 days until it ran by itself. Default schedule: massed practice 50 a day × 4 days (self-started), then maintenance 5 a day × 21 days, plus every real trigger. Device-triggered offers stay inside the safety governor's limits (90 s apart, 6 an hour, 20 a day). MEMSTACK's habit curve and reflex criterion show when a node has become a reflex.

## 8. Safety and consent

- A plan runs only after the person's consent (the node studio's approval; the player loads only an approved plan).
- Observer work with trauma memories (PTSD with an observer node) is therapist-led: a therapist is present and the screening question is answered first; a "yes" stops the session and points to crisis help.
- Scent and taste cues require confirming there is no allergy.
- Frames flagged for negation or low believability are reworded before practice.
- Consented programming rules (spec/TIER_LEDGER.md §2a, conformance C12–C13) apply to any cue that works below awareness.

## 9. AI layer (LINX) — specified

An AI conversation fills the intake in plain language, suggests broad, process-based, believable frames and cues for empty senses, and marks what a therapist should review. It may only propose: the planner builds the plan deterministically, and the person (or person and therapist) approves it. The node studio's "Copy for an AI assistant" button produces this prompt today with the intake and the plan.

## 10. Measuring a node

- Per-sense opening: from the run log's `trigger_channel` and `latency_s`, `channel_opening(runs)` gives runs, completions, median start time and the share started within 3 s, per sense (V A K O G, thought, memory) — which cue already opens the state fastest.
- Specified: a body signature per node (heart rate, HRV, EEG band powers during the tier) so a node's state can be recognised and compared across sessions.
