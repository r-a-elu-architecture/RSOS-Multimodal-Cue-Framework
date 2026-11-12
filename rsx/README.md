# RSX — the executable language of RSOS

RSX (Recursive Symbolic eXpression) is the language RSOS programs are written in. Version 2 turns the archive's RSX v1 vector syntax into a real, tested language: a program compiles to a **timeline** of breath, word, image, gesture, haptic, tone, scent and taste events that a runtime (the [protocol player](../docs/player.html), a phone, a wearable, a VR scene) can play.

- **Two matching implementations:** Python (`rsx/`) and JavaScript ([`docs/js/rsx.js`](../docs/js/rsx.js), used in the browser). A conformance test checks that both give byte-identical output.
- **Safety in the language:** haptic intensity above the program's `SAFETY haptic_max` is a compile error; run limits and refractory periods are enforced by the runtime.
- **Backwards compatible:** RSX v1 vector commands from the archive (`TIER 8 :: {DRAGON} :: (OVERRIDE) :: @Vector1:… `) still run.

```bash
cd rsx
python -m unittest discover -s tests          # 35 tests, incl. Python/JS conformance (needs Node)
python -m rsx check protocols/*.rsx
python -m rsx compile protocols/override.rsx -o override.json
python model/predictions.py                   # regenerates model/PREDICTIONS.md
```

## Example

```rsx
PROTOCOL override "RSOS Override Protocol"
SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4
BREATH inhale=4s exhale=6s

TIER 1 LION {
  V "Golden lion light"
  A "I move, I act"
  K "Warmth and strength in the belly"
  GLYPH "🦁"
  WORD "Courage"
}

FUTURES "Driving the car" | "At work" | "Achieving your goal"

PHASE interrupt {
  SAY "I move, I act"
  GESTURE "Clench your fist"
  HAPTIC on=300ms off=300ms x=6 amp=0.4
}
PHASE ignite breath=inhale {
  ACTIVATE LION
}
PHASE futures breath=exhale {             # one exhale through all three futures
  HAPTIC on=150ms off=150ms x=8 amp=0.3
  FOR FUTURE {
    SEE "$future"
    WAIT 2s
  }
}
```

The full reference program is [`protocols/override.rsx`](protocols/override.rsx); the protocol itself is specified in [`spec/OVERRIDE_PROTOCOL.md`](../spec/OVERRIDE_PROTOCOL.md).

## Language reference

One statement per line; `;` separates statements on one line; `#` starts a comment outside quotes. Durations: `300ms`, `4s`, `1.5s`, `2m`.

### Top level

| Statement | Meaning |
|---|---|
| `PROTOCOL <id> ["title"]` | Required. Names the program. |
| `VERSION <v>` | Program version. |
| `SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4` | Limits (defaults shown). |
| `BREATH inhale=4s exhale=6s hold=0s` | Breath lengths used by `breath=` phases. |
| `TIER <n> <NAME> { … }` | A multichannel bundle. Fields `V`, `A`, `K` (required), `O`, `G`, `GLYPH`, `WORD`, each with one quoted value. Node fields ([spec/NODES.md](../spec/NODES.md)): `FRAME` (up to 5, the sentences said in the state), `MODE "associated"` or `"observer"`, `TACTON "..-"` (the node's vibration code, `.` 100 ms and `-` 300 ms pulses, played when the tier is activated; a space joins up to three codes with a 400 ms pause, `"..- ---"`). |
| `FUTURES "a" \| "b" \| "c"` | Future contexts for `FOR FUTURE`. |
| `PHASE <name> [breath=inhale\|exhale\|hold\|none] [dur=…] { … }` | A time slot. All steps start together at the phase start, except after `WAIT`. The phase lasts as long as its breath, its `dur` or its longest step, whichever is longest. |
| `FOR FUTURE { PHASE … }` | Repeats the enclosed phases once per future; `$future` is replaced by the context text. Also allowed *inside* a phase to repeat steps (e.g. all futures within one exhale). |
| `REPEAT <n> { PHASE … }` | Repeats the enclosed phases `n` times (1–100). |
| `TIER <n> :: {ARCH} :: (MODE) :: @VectorK:Op(args) :: …` | RSX v1 vector command (up to 17 vectors). |

### Steps inside a phase

| Step | Channel | Notes |
|---|---|---|
| `SAY "…"` | auditory | Spoken or inner words, shown for 1.5 s |
| `SEE "…"` | visual | Imagery instruction, 2 s |
| `FEEL "…"` | kinesthetic | Body sensation, 2 s |
| `GESTURE "…"` | kinesthetic | Physical anchor, 2 s |
| `SMELL "…"` / `TASTE "…"` | olfactory / gustatory | Real or imagined |
| `HAPTIC on=300ms off=300ms x=6 amp=0.4` | haptic | `amp` ≤ `haptic_max` or compile error |
| `TONE 220Hz 4s` | auditory | 20–4000 Hz |
| `ACTIVATE <tier name or number>` | all of the tier's channels | Fires every channel of the bundle at once |
| `WAIT 600ms` | — | Delays the steps that follow |
| `MARK "…"` | marker | A labelled point in the timeline, for logging |

### RSX v1 vector operators

| Operator | v2 runtime effect |
|---|---|
| `BreathOverride` | One inhale and one exhale |
| `MemoryRecall(Archetype=X)` | Activates tier `X` if defined, otherwise a recall instruction |
| `EmotionalLock(S)` | State marker `S` |
| `FutureProjection(T)` | "See your future self T" |
| `DeviceOutput(D)` | Device event `D` for the runtime |
| `PostureShift` | Posture instruction |
| any other | Recorded in the timeline with a warning; no effect |

## Timeline format

`compile_rsx(source)` returns a dict (the same JSON from both implementations):

- `phases`: `[{name, t, dur, breath, index, future_index?}]`, contiguous, in ms.
- `events`: `[{t, dur, channel, kind, phase, …}]` sorted by time. Channels: `breath`, `visual`, `auditory`, `kinesthetic`, `olfactory`, `gustatory`, `haptic`, `marker`, `device`, `annotation`.
- `tiers`, `futures`, `safety`, `breath`, `duration_ms`, `warnings`.

## Session log

`RunRecord` / `write_log` produce one CSV row per run, the shared format for pooling data between studies:

`timestamp, participant, protocol, trigger (self|device), trigger_channel (V|A|K|O|G|thought|memory), trigger_note, sud_before, sud_after, agency_before, agency_after (0–10), latency_s, completed, stopped_at_phase, tier, voice (own|computer|none)`

The personalised cue engine reads this log directly (`toolkit/rsos_cue/runlog.py`) to learn which program, tier and voice work best for each person and trigger type.

The protocol player exports the same columns.

## Learning model

[`rsx/conditioning.py`](rsx/conditioning.py) is a formal model of what the protocol is supposed to do (Rescorla–Wagner for the cue bundles and the trigger; an asymptotic habit curve for the reflex). [`model/PREDICTIONS.md`](model/PREDICTIONS.md) lists its predictions, including two that cut against the simplest version of the protocol: rich bundles *overshadow* their single cues, and a well-practised bundle *blocks* the trigger from changing its own value.
