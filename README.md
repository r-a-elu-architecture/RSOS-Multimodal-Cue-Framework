# RSOS — Recursive Symbolic Operating System

**An open operating system for changing state on purpose.** RSOS turns a negative state (a sound, a smell, something seen, a body sensation, a memory) into the signal that starts a scripted override: movement, words, a fist, breath and golden-light imagery that redirect it into agency, rehearse it in three future situations and seal it with "I own". Practised often enough, the override is meant to become a reflex.

**[Run the Override Protocol in your browser →](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/player.html)**

> **Status.** Open specification and tested software. No human outcome data exists yet; RSOS is published so that researchers, clinics and individuals can test it and share results. It is not a medical device or a treatment. If you are in crisis, contact local emergency services or a crisis line.

## What is here

| Part | What it is | Where |
|---|---|---|
| **Override Protocol** | The core routine: interrupt, then five breaths: lion light in, through the body, three futures, out to the world, back in, sealed with "I own". Phases, channels, practice schedule, measures, safety, testable hypotheses. | [`spec/OVERRIDE_PROTOCOL.md`](spec/OVERRIDE_PROTOCOL.md) |
| **RSX** | The executable language RSOS programs are written in. Compiles a program to a timeline of breath, word, image, gesture, haptic, tone, scent and taste events. Python and JavaScript implementations, checked against each other. | [`rsx/`](rsx/) |
| **Protocol player** | Runs any RSX program with breath pacing, spoken words, tones and phone vibration; check-in before and after; a heart-rate trigger; progress toward a reflex for each tier, with weekly automaticity checks; your own glyph and colour, found by pairwise choices; run log and memory export; live RSX editor. Installable as an offline app. | [`docs/player.html`](docs/player.html) |
| **Learning model** | A formal model (Rescorla–Wagner + habit curve) of how a cue bundle becomes a reflex, with predictions swept across parameters. | [`rsx/model/PREDICTIONS.md`](rsx/model/PREDICTIONS.md) |
| **RSSO runtime** | One interface for all devices; a Bluetooth heart-rate driver and stress detector; EEG input; a conformance suite every device must pass; virtual participants, synthetic studies and the analysis kit for real ones. | [`rsso/`](rsso/) |
| **Device protocol and firmware** | The RSOS Device Protocol for wristbands and scent modules, a tested C++ device core and an ESP32 wristband sketch. | [`spec/DEVICE_PROTOCOL.md`](spec/DEVICE_PROTOCOL.md), [`firmware/`](firmware/) |
| **Glyph layer (UGCL)** | 48 glyphs, each an image, a vibration rhythm and a melody from one description, evolved with full genealogy and selected to be as distinct as possible; compact code for devices. [See, feel and hear them](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/glyphs.html). | [`spec/GLYPH_FORMAT.md`](spec/GLYPH_FORMAT.md), [`docs/glyphs.html`](docs/glyphs.html) |
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
  GLYPH "◈"
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
