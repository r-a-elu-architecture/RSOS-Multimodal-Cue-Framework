# RSOS — Recursive Symbolic Operating System

**An open operating system for changing state on purpose.** RSOS turns a negative state (a sound, a smell, something seen, a body sensation, a memory) into the signal that starts a scripted override: movement, words, a fist, breath and golden-light imagery that redirect it into agency, rehearse it in three future situations and seal it with "I own". Practised often enough, the override is meant to become a reflex.

**[Run the Override Protocol in your browser →](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/player.html)**

> **Status.** Open specification and tested software. No human outcome data exists yet; RSOS is published so that researchers, clinics and individuals can test it and share results. It is not a medical device or a treatment. If you are in crisis, contact local emergency services or a crisis line.

## What is here

| Part | What it is | Where |
|---|---|---|
| **Override Protocol** | The core routine: interrupt, then five breaths: lion light in, through the body, three futures, out to the world, back in, sealed with "I own". Phases, channels, practice schedule, measures, safety, testable hypotheses. | [`spec/OVERRIDE_PROTOCOL.md`](spec/OVERRIDE_PROTOCOL.md) |
| **RSX** | The executable language RSOS programs are written in. Compiles a program to a timeline of breath, word, image, gesture, haptic, tone, scent and taste events. Python and JavaScript implementations, checked against each other. | [`rsx/`](rsx/) |
| **Protocol player** | Runs any RSX program with breath pacing, spoken words, tones and phone vibration; check-in before and after; a heart-rate trigger; progress toward a reflex for each tier, with weekly automaticity checks; your own glyph among the original glyphs and your colour, found by pairwise choices; run log and memory export; live RSX editor. Installable as an offline app. | [`docs/player.html`](docs/player.html) |
| **Learning model** | A formal model (Rescorla–Wagner + habit curve) of how a cue bundle becomes a reflex, with predictions swept across parameters. | [`rsx/model/PREDICTIONS.md`](rsx/model/PREDICTIONS.md) |
| **RSSO runtime** | One interface for all devices; a Bluetooth heart-rate driver and stress detector; EEG input; a conformance suite every device must pass; virtual participants, synthetic studies and the analysis kit for real ones. | [`rsso/`](rsso/) |
| **Device protocol and firmware** | The RSOS Device Protocol for wristbands and scent modules, a tested C++ device core and an ESP32 wristband sketch. | [`spec/DEVICE_PROTOCOL.md`](spec/DEVICE_PROTOCOL.md), [`firmware/`](firmware/) |
| **Glyph layer (UGCL)** | The 146 original glyphs of the tier ledger, exactly as recorded (the Lion is 🦁), each also a vibration rhythm and a melody derived from its shape, with its ancestry from the ledger's mutation chain; a stroke format with a compact code for devices, and an optional generated library of 48. [See, feel and hear them](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/glyphs.html). | [`spec/GLYPH_FORMAT.md`](spec/GLYPH_FORMAT.md), [`docs/glyphs.html`](docs/glyphs.html) |
| **Nodes and LINX** | Describe it in your own words and LINX, the AI layer, builds the plan with you, one question at a time; any AI model can propose improvements through its containment router. Design the states you want to live in: from symptoms, triggers and desired states, a plan of nodes — each a state held as one unit, with cues on every sense, an original glyph, a vibration code on the wrist, a mode (associated, or observer: nothing binds) and the mental frame said in that state — with programs, ledger tiers, metrics, dose and safety, run in the player after consent. [Node studio](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/nodes.html). | [`spec/NODES.md`](spec/NODES.md), [`spec/LINX.md`](spec/LINX.md), [`docs/nodes.html`](docs/nodes.html) |
| **Anchors you can measure (PEAK)** | A cue paired with a state becomes a measured object: pair it at a peak (marked by you, or measured as a rise in heart rate variability or EEG), test it with blind probes (the cue alone or a sham cue, the heart measured before and after), and see its strength with a 95% interval. The page warns when an anchor is taking on stress and gives the restoration plan; anchors play as chains in role order. Heart rate from a fingertip over the phone camera. Checked on simulated people with known answers; a protocol kit for real studies. [Anchors](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/anchors.html). | [`spec/PEAK.md`](spec/PEAK.md) |
| **Personal trials and short tasks (TRIAL, CHECKS)** | Find out what works for you: compare two or more ways of practising (your anchor or a sham code, a cue or none, automatic or by hand, the order of Core Transformation and identity, higher-level imagery), with the order of sessions chosen at random in permuted blocks. Your own effect with an interval, a permutation p-value, an estimate adjusted for drift and sleep, and a plain verdict; results from many people pool into one estimate. Short tasks with dated scores: working memory (2-back), digit span, reaction time (calm and under pressure), word recall, reading, and attention to threat. [Trials](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/trials.html). | [`spec/TRIAL.md`](spec/TRIAL.md), [`spec/CHECKS.md`](spec/CHECKS.md) |
| **Autonomy gate** | A device may act on its own only when an anchor has earned it: manual first, then suggesting when it detects stress, then firing by itself, then during pressure practice by opt-in. Each step needs training at a peak, proven strength against sham, confirmed offers with few false alarms, and no wear-out or stress contamination; the gate closes again by itself when the evidence weakens. Consent records, a visible flag on anything that works below awareness, and a log of every automatic decision. [Safety](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/safety.html#autonomy). | [`spec/GATE.md`](spec/GATE.md) |
| **Identity profiles (IDENTITY)** | A symbol heads a tree of seven levels (mission, identity, values, beliefs, skills, behaviour, environment), each with a statement, an image and its own vibration code; the symbol by day, the whole chain at night, four steps when an old state starts, a prepared week and a month's dose, all playable in the player. Rate how true each level feels and see coherence over months, drift after time with other people, whether the behaviour starts in untrained places, anchor-tree recall walks, value conflicts measured in the heart, switching between profiles and versions. Six ready profiles. [Identity](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/identity.html). | [`spec/IDENTITY.md`](spec/IDENTITY.md) |
| **Trigger atlas (ATLAS)** | Map which sights, sounds, smells, tastes, places, thoughts, symbols and people shift your state: a few moments a day for two weeks, and every path gets a weight with an interval, combinations that only work together are found, and the map is tested on moments it has not seen. A strong trigger can be rerouted to your best anchor through the autonomy gate. A live 3D guided descent through your own network; then a repeat mapping shows whether the change spread to triggers you never worked on. Higher nodes by abstraction and by scope, and the original glyphs as a memory route. [Atlas](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/atlas.html). | [`spec/ATLAS.md`](spec/ATLAS.md) |
| **Night and reward (SLEEP, REWARD)** | The day's codes replayed only in deep sleep, below waking level, stopping at the first sign of waking, with a nightly limit; codes linked to painful memories are never played, and a nightmare gets a safety code or a gentle waking. A simulated night shows closed-loop cueing against random cueing. Next-day recall of cued against uncued items, a night diary, reward codes per learning area that answer a success within a fraction of a second, a motion sensor that recognises a good move, and a test of whether light makes a cue noticed sooner. [Night](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/night.html). | [`spec/NIGHT.md`](spec/NIGHT.md) |
| **Therapist mode (THERA)** | Structured, measured sessions with the client's own nodes: stress, boundaries, habits, low mood and therapist-led observer work with a memory. What to say, do and measure at each step; stop rules; fidelity, distress and agency from start to end; clinician ratings; the practice plan between sessions; a session record for research. [Therapist sessions](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/therapist.html). | [`spec/THERA.md`](spec/THERA.md) |
| **The copilot and session tools** | A decision matrix the therapist learns by heart (a central meaning, three trigger cues, their responses and codes), drawn as an anchor tree; the copilot reads the transcript and lights up the branch it hears, and agreement with the therapist is measured. The level of a sentence and a question from the level above; Core Transformation one question at a time; re-living an event with the symbol and light; overrides with OXQ and DOL-9, the 90-second loop; craving context triggers; typologies from speech with consent; the life timeline; the setting of each session. [Therapist page](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/therapist.html#copilot). | [`spec/COPILOT.md`](spec/COPILOT.md) |
| **Patterns (CM1)** | Each person's practice compressed into a signature, many people into a few response profiles, and the patterns that repeat across everyone; a new person learns where to start from a few runs. A person's plan fits in about 40 bytes for a device. Checked on a synthetic population with known answers. [Patterns](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/metrics.html#cmTitle). | [`spec/CM1.md`](spec/CM1.md) |
| **Safety (CONTAIN)** | One gate every part asks before it acts: a device safety envelope no program can exceed, programs and nodes paused when they stop helping or an adverse event is linked to them, practice paused and the person pointed to a therapist or crisis help when needed, every decision logged with its reason. Conformance C14 and C15. [Safety page](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/safety.html). | [`spec/CONTAIN.md`](spec/CONTAIN.md) |
| **On your phone** | RSOS runs in the phone's browser and installs like an app. Android (Chrome) is a complete RSOS device: player, vibration codes on the phone, a Bluetooth heart-rate strap as the trigger, and an RSOS wristband. iPhone: light, words, voice and tones; no vibration or Bluetooth from the browser. [What works on each phone, and Android set-up](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/device.html#android). | [`docs/device.html`](docs/device.html) |
| **Wristband and board kit** | Works on bands whose software you can replace (a self-built ESP32 band, ESP32 wearables such as LilyGO T-Watch or M5StickC, any RDP/1 device) and on the vibration of Android phones; not on closed brand watches (Apple Watch, Fitbit, Garmin, Mi Band) or Wear OS watches until RSOS watch apps exist ([which wristbands work](firmware/BOARD_KIT.md#which-wristbands-work)). Build an ESP32 wristband from common parts, flash it (Arduino IDE, arduino-cli or PlatformIO) and check it: seven device checks plus the whole conformance suite in real time, from a computer (`python -m rsso.board`) or in the browser over USB or Bluetooth; feel the vibration codes of your nodes and play programs on it. [Phones and wristbands](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/device.html), including Android set-up. | [`firmware/BOARD_KIT.md`](firmware/BOARD_KIT.md) |
| **For reviewers** | What RSOS is, how to reproduce every result in an hour (`./scripts/check_all.sh`, also run on every push), an evidence register that marks every number as measured, simulated or synthetic, known open findings, and a review checklist. | [`REVIEW.md`](REVIEW.md) |
| **Research data contribution** | One de-identified, checksummed file per person, clinician or lab: practice runs with their full context, heart rate, node plans, glyph choices, a vibration-code check, questionnaires (PHQ-9, GAD-7, PCL-5, PSS-10, WEMWBS), safety events, clinician sessions and CGI ratings, EEG/BCI recordings with BIDS events. Twelve consent scopes; nothing leaves the browser until the contributor sends the file; pooled with one command for the analysis kit. [Contribute](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/contribute.html). | [`spec/DATA_CONTRIBUTION.md`](spec/DATA_CONTRIBUTION.md) |
| **Tier ledger, metrics and system map** | Every tier of the ledger as recorded, with where it lives in the architecture and the system behaviour it defines; every metric code with its recorded values and what it measures today, including your own numbers; one map of how the parts connect. [Ledger](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/tiers.html), [metrics](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/metrics.html), [system](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/system.html). | [`spec/TIER_LEDGER.md`](spec/TIER_LEDGER.md) |
| **Roadmap and claims register** | What comes next: 69 items from the RSOS design records, built in nine steps (anchors you can measure, personal trials, an autonomy gate, identity profiles, a trigger atlas, sleep and reward, therapist extensions, machines and channels), and 101 claims from the records, each recorded with the test it becomes. Prior art, glossary, foundations and who coined each name. [Roadmap](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/roadmap.html). | [`spec/ROADMAP.md`](spec/ROADMAP.md), [`spec/CLAIMS.md`](spec/CLAIMS.md) |
| **Personalised cue engine** | `rsos_cue`: reads the run log and learns which program, tier and voice work best for each person and trigger type, borrowing strength from earlier participants. | [`toolkit/`](toolkit/) |
| **RSIA framework** | The identity layer: six archetypes (Lion, Eagle, Bear, Leopard, Raven, Tiger), the Spine, Watchdog and Meta-Architect; mnemonic sets. | [`framework/`](framework/) |
| **Archive** | The dated source records of RSOS, RSIA, RSX and RSSO (public edition), with hashes. | [`archive/`](archive/), [`architecture/`](architecture/) |

## The four systems

- **RSOS** (Recursive Symbolic Operating System): the cue bundles. Each **tier** binds a visual glyph, a spoken metaphor word, a body feeling and optionally a scent and a taste, activated together.
- **RSIA** (Recursive Symbolic Identity Architecture): which inner mode colours the state (the Lion by default) and the values it serves.
- **RSX** (Recursive Symbolic eXpression): the language that writes and runs programs.
- **RSSO** (Recursive Symbolic System Operating): orchestration: triggers, scheduling, safety limits and logging.

## Quick start

```bash
git clone https://github.com/r-a-elu-architecture/RSOS-Multimodal-Cue-Framework
cd RSOS-Multimodal-Cue-Framework/rsx
python -m unittest discover -s tests           # 35 tests (Python/JS conformance needs Node)
python -m rsx compile protocols/override.rsx   # the protocol as a JSON timeline
python model/predictions.py                    # regenerate the model predictions

cd ../rsso
python -m unittest discover -s tests           # 30 tests (firmware tests need a C++ compiler)
python -m rsso.conformance --firmware          # device conformance on the C++ firmware core

cd ../toolkit
python -m unittest discover -s tests           # 10 tests
python examples/quickstart.py
```

Requirements: Python 3.10+ with NumPy, SciPy and pandas (the cue engine only). RSX itself needs nothing beyond the standard library.

## A program in RSX

```rsx
TIER 1 LION {
  V "Golden lion light"
  A "I move, I act"
  K "Warmth and strength in the belly"
  GLYPH "🦁"
}
FUTURES "Driving the car" | "At work" | "Achieving your goal"

PHASE interrupt {
  SAY "I move, I act"
  GESTURE "Clench your fist"
  HAPTIC on=300ms off=300ms x=6 amp=0.4
}
PHASE ignite breath=inhale { ACTIVATE LION }
PHASE futures breath=exhale {
  HAPTIC on=150ms off=150ms x=8 amp=0.3
  FOR FUTURE { SEE "$future"; WAIT 2s }      # all three futures in one exhale
}
```

Haptic intensity above the program's safety limit does not compile. Archive RSX v1 commands (`TIER 8 :: {DRAGON} :: (OVERRIDE) :: @Vector1:…`) still run.

## What the model predicts

The learning model makes the protocol's claims precise enough to fail. Across every parameter setting tested it predicts that multichannel tiers reach the agency state in fewer runs than single cues, **and** two costs: each cue alone ends weaker inside a rich bundle (overshadowing), and a well-practised bundle limits how much the trigger itself changes (blocking). The protocol therefore has two outcomes to measure separately: the reflex (latency, automaticity) and how the trigger feels. See [`rsx/model/PREDICTIONS.md`](rsx/model/PREDICTIONS.md).

## Test it

The specification lists six hypotheses with minimal study designs (§10) and a shared run-log format, so results from different groups can be pooled. [`rsso/`](rsso/) runs complete synthetic studies with virtual participants and devices, and its analysis kit runs unchanged on real data. [`toolkit/study_kit/`](toolkit/study_kit/) has a study procedure and sample sizes for the first hypotheses. If you run a study, please open an issue so it can be listed here.

## Related work

RSOS combines parts that exist separately (scent conditioning, wearable cue delivery, closed-loop multisensory systems, adaptive-intervention frameworks, BCI operating systems). [`RELATED_WORK.md`](RELATED_WORK.md) lists the closest systems and what each lacks.

## Licence and citation

- Software: Apache 2.0. Specifications and framework texts: CC BY 4.0. Archive records keep their original notices. Details in [LICENSING.md](LICENSING.md).
- Cite: [CITATION.cff](CITATION.cff). DOI for all versions (always the latest): [doi:10.5281/zenodo.24143731](https://doi.org/10.5281/zenodo.24143731). v2.0.0 is archived at [doi:10.5281/zenodo.24151788](https://doi.org/10.5281/zenodo.24151788). The earlier v1.0.0 research preview (superseded) is at [doi:10.5281/zenodo.24143732](https://doi.org/10.5281/zenodo.24143732).

Author: R. A. Elu.
