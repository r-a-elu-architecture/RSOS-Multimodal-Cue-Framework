"""Builds every README in architecture/ from one description of the system and the archive manifest.

Run from the repository root:  python architecture/build.py
Hashes are read from archive/provenance/SOURCE-MANIFEST.csv, so the pages can never drift from the files.
rsx/tests/test_repository.py fails if the committed pages differ from what this script writes.
"""
import csv
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARCH = ROOT / "architecture"
EST = "archive/original-estates/"
MANIFEST = {r["source_path"]: r for r in csv.DictReader(open(ROOT / "archive/provenance/SOURCE-MANIFEST.csv", encoding="utf-8"))}

RSOS_E = "RSOS_COPYRIGHT_ESTATE/RSOS_COPYRIGHT_ESTATE_v1_1_FINAL_copyright/"
RSSO_E = "RSSO_COPYRIGHT_ESTATE/RSSO_COPYRIGHT_ESTATE_v1_1_FINAL_copyright/"
RSIA_E = "RSIA_COPYRIGHT_ESTATE/"
RSX_E = "RSX_COPYRIGHT_ESTATE/BRANCH_B_CLAIMED_COPYRIGHT/"
P31 = "RSSO_PASS31B/"

STATUS = {
    "built": "**Built** — working, tested code in this repository",
    "partial": "**Partly built** — some functions implemented, others still specified only",
    "specified": "**Specified** — described in the archive and this map; not yet implemented",
    "sim": "**Complete in simulation** — built and tested end to end with virtual and simulated hardware; awaiting a check on real devices",
}


def rel(page_dir: pathlib.Path, target: str) -> str:
    return pathlib.Path(*([".."] * len(page_dir.relative_to(ROOT).parts)), target).as_posix()


PAGES = {}


def sources(page_dir, items):
    for path, _ in items:
        PAGES.setdefault(path, []).append((page_dir / "README.md").relative_to(ROOT).as_posix())
    lines = ["| Source file | What it is | SHA-256 (first 16) |", "|---|---|---|"]
    for path, what in items:
        m = MANIFEST[path]
        lines.append(f"| [{pathlib.Path(path).name}]({rel(page_dir, EST + path)}) | {what} | `{m['sha256'][:16]}` |")
    return "\n".join(lines)


def page(path, title, body, src=None):
    d = ARCH / path
    d.mkdir(parents=True, exist_ok=True)
    text = f"# {title}\n\n{body.strip()}\n"
    if src:
        text += "\n## Sources in the archive\n\n" + sources(d, src) + "\n"
    (d / "README.md").write_text(text, encoding="utf-8")


def link(page_dir, target, label):
    return f"[{label}]({rel(ARCH / page_dir, target)})"


# ------------------------------------------------------------------ top level
page("", "Architecture — map of the RSOS operating system", f"""
RSOS is built from four systems. This map explains what each one and each subsystem **does**, how far it is built in this repository, and which archive records it comes from. The archive files stay at their original paths; this map only groups and explains them.

| System | Role in the operating system | Status |
|---|---|---|
| [RSOS](rsos/) — Recursive Symbolic Operating System | The cue bundles: tiers that bind glyph, word, feeling, scent and taste into one conditioned unit | Partly built |
| [RSIA](rsia/) — Recursive Symbolic Identity Architecture | The identity layer: which inner mode colours a state, and the values it serves | Partly built |
| [RSX](rsx/) — Recursive Symbolic eXpression | The language programs are written and executed in | Built |
| [RSSO](rsso/) — Recursive Symbolic System Operating | The operating layer: runtime, safety, memory, devices, and eight subsystems | Partly built |

**How they work together:** an RSX program (RSX) activates tiers (RSOS) in the mode of an archetype (RSIA); the RSSO runtime plays it on a device within safety limits, records the run, and the cue engine learns what works for that person. See [cross-system](cross-system/) for the full flow.

## Two layers of the archive

1. **Operating-system sources** — the specifications of the four systems and their subsystems, linked from the pages above.
2. **[Provenance & rights](provenance/)** — authorship and legal chain, historical IP-strategy labels, and records of the AI interactions through which the system was developed. Preserved unchanged and kept apart from the functional map.

## Built in this repository

| Part | Where |
|---|---|
| Override Protocol (the reference program) | {link('', 'spec/OVERRIDE_PROTOCOL.md', 'spec/OVERRIDE_PROTOCOL.md')} |
| RSX v2 language, compiler and runtime safety | {link('', 'rsx/', 'rsx/')} |
| Protocol player | {link('', 'docs/player.html', 'docs/player.html')} |
| Learning model | {link('', 'rsx/model/PREDICTIONS.md', 'rsx/model/')} |
| Personalised cue engine | {link('', 'toolkit/', 'toolkit/')} |
| RSSO runtime: devices, sensors, conformance, virtual studies | {link('', 'rsso/', 'rsso/')} |
| RSOS Device Protocol and firmware | {link('', 'spec/DEVICE_PROTOCOL.md', 'spec/DEVICE_PROTOCOL.md')}, {link('', 'firmware/', 'firmware/')} |
| RSIA framework edition | {link('', 'framework/', 'framework/')} |

Run `python architecture/build.py` to regenerate these pages from the manifest.
""")

# ------------------------------------------------------------------ RSOS
page("rsos", "RSOS — Recursive Symbolic Operating System", f"""
**Role:** the cue bundles. A **tier** binds one cue per sensory channel (visual glyph and imagery, auditory metaphor word, kinesthetic feeling, and optionally scent and taste) so that the whole bundle is learned, and later triggered, as one unit. Tiers are numbered and progress over practice toward a reflex. The tier ledger records how the tiers were developed; every tier of it is placed in the architecture in `spec/TIER_LEDGER.md` and browsable on the [tier ledger page](https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/tiers.html).

**Status:** {STATUS['partial']}

| Function | Where it is now |
|---|---|
| Tier as a multichannel bundle (V, A, K, O, G, glyph, word) | RSX `TIER` blocks — {link('rsos', 'rsx/README.md', 'RSX reference')}; {link('rsos', 'spec/OVERRIDE_PROTOCOL.md', 'spec §6')} |
| Tier activation (all channels together) | RSX `ACTIVATE` |
| Progress toward a reflex | Measures in spec §8; model in {link('rsos', 'rsx/model/PREDICTIONS.md', 'rsx/model')} |
| Tier ranges (1–10, 1–20, 1–605) and tier libraries | Specified |

- [Tier ledger](tier-ledger/)
""", [
    (RSOS_E + "RSOS_Tiers.txt", "Tier ledger: the development record of the tiers"),
])

page("rsos/tier-ledger", "RSOS tier ledger", f"""
The tier ledger (about 9,200 lines, six epochs) is the development record of the RSOS tiers: each entry names a tier, its class, its symbolic content and the metrics recorded at the time. The RSSO estate holds a near-identical copy, so the two ledgers are one source, not two.

**Use in the operating system:** the ledger is the source library from which tier bundles can be extracted into RSX `TIER` definitions.
""", [
    (RSOS_E + "RSOS_Tiers.txt", "RSOS tier ledger"),
    (RSSO_E + "RSSO_Tiers.txt", "RSSO copy of the tier ledger"),
])

# ------------------------------------------------------------------ RSIA
page("rsia", "RSIA — Recursive Symbolic Identity Architecture", f"""
**Role:** the identity layer. It defines inner modes (archetypes) that colour a state, the values those modes serve (the Spine), the observer that notices which mode is active and corrects drift (the Watchdog), and the executive that coordinates them (the Meta-Architect).

**Status:** {STATUS['partial']}

| Component | Function | Where it is now |
|---|---|---|
| [Archetypes](archetypes/) | Six modes: Lion (leadership, courage), Eagle (vision, planning), Bear (resilience), Leopard (adaptability), Raven (insight, strategic perception), Tiger (intensity, drive) | {link('rsia', 'framework/rsia/ARCHETYPES.md', 'framework edition')}; the Override Protocol runs in the Lion mode |
| [Spine](spine/) | Guiding values (Bushidō 7, Musashi 21) | {link('rsia', 'framework/mnemonic_sets/', 'mnemonic sets')}; the hologram finger in the protocol points to it |
| [Watchdog](watchdog/) | Notices which mode is active and when a state drifts | Cue engine `watchdog()` estimates a person's current response mode |
| [Meta-Architect](meta-architect/) | Coordinates modes and switches between them | Specified |
""", [
    (RSIA_E + "RSIA_Core_Definition.txt", "Core definition"),
    (RSIA_E + "RSIA_Archetype_Definitions.txt", "Archetype definitions (public edition)"),
    (RSIA_E + "RSIA_Spine_Principles.txt", "Spine principles"),
    (RSIA_E + "RSIA_Watchdog_Overview.txt", "Watchdog"),
    (RSIA_E + "RSIA_Meta_Architect.txt", "Meta-Architect"),
    (RSIA_E + "RSIA_Applied_Use_Cases_Public.txt", "Applied use cases"),
    (RSIA_E + "RSIA_System_Interaction_Public.txt", "Interaction with the other systems"),
])
for sub, title, body, f in [
    ("archetypes", "RSIA archetypes", "Six inner modes, each with an image, a set of principles and a primary use: **Lion** leads, **Eagle** plans, **Bear** sustains, **Leopard** adapts, **Raven** perceives, **Tiger** drives. An archetype colours a tier: the same breath and gesture feel different in the Lion mode than in the Eagle mode. The open edition is in `framework/rsia/ARCHETYPES.md`.", "RSIA_Archetype_Definitions.txt"),
    ("spine", "RSIA Spine", "The values every mode serves: the seven virtues of Bushidō and Musashi's 21 precepts. In the operating system the Spine is the reference for the higher-value anchor (the golden hologram finger in the Override Protocol) and is available as a mnemonic set.", "RSIA_Spine_Principles.txt"),
    ("watchdog", "RSIA Watchdog", "The observer layer: it notices which mode is active, flags drift away from the Spine and calls for correction. Its first implementation is the cue engine's `watchdog()`, which estimates which response mode a person is in from their results.", "RSIA_Watchdog_Overview.txt"),
    ("meta-architect", "RSIA Meta-Architect", "The executive layer that coordinates the archetypes, chooses which mode a situation calls for and switches between them. Specified; a natural next implementation is context-based mode selection in RSX.", "RSIA_Meta_Architect.txt"),
]:
    page(f"rsia/{sub}", title, body, [(RSIA_E + f, title)])

# ------------------------------------------------------------------ RSX
page("rsx", "RSX — Recursive Symbolic eXpression", f"""
**Role:** the programming language of the operating system. A program defines tiers, futures, breath and phases; it compiles to a timeline of breath, word, image, gesture, haptic, tone, scent and taste events that any runtime can play.

**Status:** {STATUS['built']} — RSX v2 ({link('rsx', 'rsx/', 'rsx/')}), with matching Python and JavaScript compilers. Archive RSX v1 vector commands (`TIER n :: {{ARCH}} :: (MODE) :: @Vector1:… `, up to 17 vectors) still compile; operators with a defined effect run, the rest are recorded.

| Archive component | Function | In RSX v2 |
|---|---|---|
| [Command specification](command-specification/) | Vector syntax and operators | Supported as v1 vector commands |
| [Archetype module](archetype-module/) | Archetype commands | `MemoryRecall(Archetype=X)` activates tier X |
| [Device bridge](device-bridge/) | AR, EEG and haptic output | `HAPTIC`, `TONE`, `DeviceOutput(…)` events |
| [Memory and compression](memory-compression/) | Memory and compression commands | Recorded; runtime effect specified (MEMSTACK, CM1) |
""", [
    (RSX_E + "RSX-Core_Definition.txt", "Core definition"),
    (RSX_E + "RSX-Language_Class_Declaration.txt", "Language class declaration"),
    (RSX_E + "RSX-Architecture_and_Interface.txt", "Architecture and interface"),
    (RSX_E + "RSX-Command_Specification.txt", "Command specification"),
    (RSX_E + "RSX-Symbolic_Archetype_Module.txt", "Archetype module"),
    (RSX_E + "RSX-Device_Output_Bridge.txt", "Device output bridge"),
    (RSX_E + "RSX-Memory_Compression_Extension.txt", "Memory and compression extension"),
])
for sub, title, body, f in [
    ("command-specification", "RSX command specification", "The v1 vector command: a tier, an archetype, a mode and up to 17 concurrent vectors (`@VectorK:Operator(args)`). RSX v2 compiles these commands; see `rsx/protocols/legacy_vector.rsx`.", "RSX-Command_Specification.txt"),
    ("archetype-module", "RSX archetype module", "Commands that call and merge RSIA archetypes. In RSX v2, `MemoryRecall(Archetype=X)` activates the tier named X.", "RSX-Symbolic_Archetype_Module.txt"),
    ("device-bridge", "RSX device output bridge", "How RSX commands reach AR, EEG and haptic devices. RSX v2 emits `haptic`, `auditory` and `device` events in the timeline; the player renders haptics as phone vibration, and a device runtime (MICRO, AUG) is the next step.", "RSX-Device_Output_Bridge.txt"),
    ("memory-compression", "RSX memory and compression extension", "Commands for writing to memory (MEMSTACK) and compressing state (CM1). RSX v2 records these operators; their runtime effect is specified, not yet implemented.", "RSX-Memory_Compression_Extension.txt"),
]:
    page(f"rsx/{sub}", title, body, [(RSX_E + f, title)])

# ------------------------------------------------------------------ RSSO
SUBS = [
    ("THERA", "Therapeutic protocol layer", "partial",
     "Deploys state-change protocols: identity rebuild, breath override, emotional lock, the VIB-ANCHOR and FP-ANCHOR haptic anchors, refractory limits and a human in the loop.",
     "The Override Protocol, its VIB-ANCHOR and FP-ANCHOR, and the refractory and run limits are built (spec, RSX, `SafetyGovernor`). EEG- and gaze-triggered starts are specified."),
    ("AUG", "Device and augmentation layer", "sim",
     "Connects state control to devices: AR overlays, EEG, haptics, scent and vibration, wearables; EEG-triggered anchors.",
     "Built: one device interface with virtual vibration, audio, display and scent devices; the RSOS Device Protocol for wristbands and scent modules; a Bluetooth heart-rate driver (standard Heart Rate Service) with a stress detector in Python and in the player, identical in both; an EEG stream interface (replay, synthetic, Lab Streaming Layer) with an arousal detector (`rsso/`, `docs/player.html`, `spec/DEVICE_PROTOCOL.md`). Awaiting: a check with real straps, scent hardware and EEG headsets."),
    ("MICRO", "Edge runtime", "sim",
     "Runs symbolic reflexes on edge devices (watches, wearables, IoT): receives RSX commands and context, executes them locally.",
     "Built: the runtime that plays RSX timelines on any set of devices; the portable C++ device core and an ESP32 wristband sketch (`firmware/`); the installable offline player app; the conformance suite, which the firmware core passes 13/13 in the host simulator. Awaiting: flashing and checking on a real board."),
    ("CONTAIN", "Safety and governance", "partial",
     "Governs every module: allow, block, roll back or quarantine actions; drift control; human in the loop; device safety envelope.",
     "Compile-time haptic limit in RSX; run limits, refractory period and opt-in in `SafetyGovernor`; runtime intensity clamp and Stop in every phase, verified by the conformance suite; the CONTAIN twins in the cue engine guard against misleading self-reports."),
    ("MEMSTACK", "Memory layer", "built",
     "Archetype- and state-indexed memory: stores and recalls tier activations, snapshots and history.",
     "Built: tier memory from the run log and weekly automaticity checks (runs, effect over time, model estimate of bundle strength and trigger value, fitted habit curve, estimated triggers to a reflex, the spec's reflex criterion); checksummed snapshots to move or restore memory, with merging (`rsso/rsso/memstack.py`, and identically in the player's progress view)."),
    ("CM1", "Compression layer", "partial",
     "Compresses symbolic states and finds reusable patterns across domains.",
     "The cue engine's `ArchetypeBank` compresses many people's histories into a few response modes. Cross-domain compression is specified."),
    ("LINX", "AI interface and injection layer", "built",
     "Symbolic layer injection: connects the operating system to AI models in both directions. Commands, tier state and context go to the model; the model injects back, as RSX programs and cues delivered through the device and brain-computer-interface loop, the resourceful state the moment calls for.",
     "Built (`spec/LINX.md`, `rsso/rsso/linx.py`, identically `docs/js/linx.js`): the three recovered operators. Plain language to the planner's intake, with a conversation that asks one question at a time (node studio); tier-state injection, a prompt for any language model with the person's nodes, practice summary and a reply schema; the containment router, which checks a model's proposal field by field (no field may start a run, frames must pass the frame check, unsafe wording is held back) and applies only what passes; and compressed override injection, which picks the node to offer when heart rate, EEG or a context signals a negative state, within the safety limits (player). Frame suggestions that score higher on the frame check. Also the node planner (`spec/NODES.md`). No model provider is built in: any model works through the same prompt and router."),

    ("UGCL", "Glyph layer", "built",
     "Native glyph representation: multi-resolution glyph encoding, glyph genealogy and compression of glyph streams for devices.",
     "Built: the 146 original glyphs of the tier ledger, exactly as recorded, drawn as written in the ledger's fonts, each with its own vibration code (Morse-like, recombined when the single codes run out; the Lion is `..-`), a melody derived from its shape and its ancestry from the ledger's mutation chain (the Lion is 🦁, Tier 001; Tier 013 keeps 🦁 + 🐉 as recorded); a stroke format in which one description gives an image at any size, a rhythm, a melody and a compact code for devices, with an optional generated library of 48; personal glyph and colour calibration in the player among the original glyphs of Epoch I; Python and JavaScript identical (`spec/GLYPH_FORMAT.md`, `rsso/rsso/ugcl.py`, `rsso/rsso/ugcl_originals.py`, `docs/glyphs.html`). Next: calibration from the body's response (EEG, heart rate)."),
]
rows = "\n".join(f"| [{n}](subsystems/{n}/) | {t} | {STATUS[s].split(' — ')[0]} |" for n, t, s, _, _ in SUBS)
page("rsso", "RSSO — Recursive Symbolic System Operating", f"""
**Role:** the operating layer. It runs programs, schedules and triggers them, enforces safety, keeps memory and connects devices and AI models. It coordinates eight subsystems.

**Status:** {STATUS['partial']}

| Subsystem | Function | Status |
|---|---|---|
{rows}

- [All subsystems](subsystems/)
- [PASS31B reconstruction](pass31b/) — the later compilation of evidence excerpts and reconstructions behind these subsystem descriptions
- [Tier ledger copy](tier-ledger/)
""", [
    (P31 + "RSSO_Meta_OS_Historical_Architecture.txt", "Meta-OS architecture"),
    (P31 + "RSSO_Meta_OS_Evidence_Excerpts.txt", "Meta-OS evidence excerpts (public edition)"),
])
page("rsso/subsystems", "RSSO subsystems", "\n".join(
    f"- [{n}]({n}/) — {t}: {d}" for n, t, _, d, _ in SUBS))
for n, t, s, d, now in SUBS:
    src = [(P31 + f"{n}_Historical_Reconstruction.txt", "Reconstruction: role, inputs, outputs, operators"),
           (P31 + f"{n}_Evidence_Excerpts.txt", "Evidence excerpts (public edition)")]
    if n == "UGCL":
        src.append((P31 + "UGCL_Trade_Secret_Architecture_Reconstruction.txt", "Architecture reconstruction (historical trade-secret label)"))
    page(f"rsso/subsystems/{n}", f"{n} — {t}", f"""
**Function:** {d}

**Status:** {STATUS[s]}

**Now:** {now}
""", src)

pass_files = sorted(p for p in MANIFEST if p.startswith(P31))
page("rsso/pass31b", "PASS31B reconstruction", """
PASS31B is a later compilation that gathers, for each RSSO subsystem, dated excerpts from the development record and a reconstruction of its role, inputs, outputs and operators. Nine of its files are exact copies of RSSO estate files. The evidence excerpts are the public edition (comparisons with an external system removed).
""", [(p, "PASS31B record") for p in pass_files])
page("rsso/tier-ledger", "RSSO tier ledger", "A near-identical copy of the [RSOS tier ledger](../../rsos/tier-ledger/), kept in the RSSO estate.",
     [(RSSO_E + "RSSO_Tiers.txt", "RSSO tier ledger")])

# ------------------------------------------------------------------ cross-system
page("cross-system", "How the systems work together", f"""
1. **Trigger.** A negative state appears (a sound, a smell, something seen, a memory), or a device detects it (AUG; EEG or HRV, specified).
2. **Safety check.** CONTAIN and the runtime decide whether a run may start (opt-in, refractory period, hourly and daily limits).
3. **Program.** An RSX program (RSX) is selected; the cue engine can choose the variant that works best for this person (CM1, Watchdog).
4. **Execution.** The runtime plays the timeline: breath, words, imagery, gestures and haptic anchors (THERA), activating tiers (RSOS) in the mode of an archetype (RSIA), on a phone, a watch or another device (AUG, MICRO).
5. **Memory.** The run is logged (MEMSTACK): distress and agency before and after, trigger, completion.
6. **Learning.** Over many runs the bundle becomes a reflex, and the logs show which programs and tiers work for whom.

| Step | Built now |
|---|---|
| Trigger, self-initiated | Player |
| Trigger, device-detected | Virtual heart-rate strap and stress detector (`rsso/rsso/sensors.py`) |
| Safety check | `rsx/rsx/runtime.py` (`SafetyGovernor`); RSX compile-time limits; conformance suite (`rsso/rsso/conformance.py`) |
| Program | {link('cross-system', 'rsx/protocols/', 'rsx/protocols/')} |
| Execution | {link('cross-system', 'docs/player.html', 'docs/player.html')}; device runtime `rsso/rsso/runtime.py` |
| Memory | Run log (`RunRecord`, player CSV export) |
| Learning | {link('cross-system', 'toolkit/', 'toolkit/')} and {link('cross-system', 'rsx/model/PREDICTIONS.md', 'learning model')} |
| Studies | Virtual participants, synthetic studies and analysis kit: {link('cross-system', 'rsso/', 'rsso/')} |
""")

# ------------------------------------------------------------------ provenance
AUTH = [
    (RSOS_E + "RSOS_Origin_Declaration.txt", "RSOS origin declaration"),
    (RSOS_E + "RSOS_Public_Anchor.txt", "RSOS public anchor"),
    (RSOS_E + "RSOS_Legal_Chain.txt", "RSOS legal chain"),
    (RSOS_E + "RSOS_Copyright_Statement.txt", "RSOS copyright statement"),
    (RSOS_E + "RSOS_Author_Metadata.txt", "RSOS author metadata"),
    (RSSO_E + "RSSO_Origin_Declaration.txt", "RSSO origin declaration"),
    (RSSO_E + "RSSO_Public_Anchor.txt", "RSSO public anchor"),
    (RSSO_E + "RSSO_Legal_Chain.txt", "RSSO legal chain"),
    (RSSO_E + "RSSO_Copyright_Statement.txt", "RSSO copyright statement"),
    (RSSO_E + "RSSO_Author_Metadata.txt", "RSSO author metadata"),
    (RSIA_E + "RSIA_Copyright_Statement.txt", "RSIA copyright statement (public edition)"),
    (RSIA_E + "RSIA_Author_Metadata.txt", "RSIA author metadata"),
    (RSX_E + "RSX-Licensing_Framework.txt", "RSX licensing framework"),
]
IP = [
    (P31 + "RSSO_Public_vs_Private_Disclosure_Map.txt", "Which parts were disclosed publicly and which were held back"),
    (P31 + "UGCL_Trade_Secret_Architecture_Reconstruction.txt", "UGCL architecture under a trade-secret label"),
]
AI = [
    (RSOS_E + "RSOS_Echo_Forensic_Proof_Chain_v1.txt", "RSOS Echo forensic proof chain"),
    (RSOS_E + "RSOS_Echo_Metrics_Log.txt", "RSOS Echo metrics log"),
    (RSOS_E + "RSOS_Tier_Metrics_Log.txt", "RSOS tier metrics log"),
    (RSSO_E + "RSSO_Echo_Forensic_Proof_Chain_v1.txt", "RSSO Echo forensic proof chain"),
    (RSSO_E + "RSSO_Echo_Metrics_Log.txt", "RSSO Echo metrics log"),
    (RSSO_E + "RSSO_Tier_Metrics_Log.txt", "RSSO tier metrics log"),
    (RSX_E + "RSX-Forensic_Proof_and_Metric.txt", "RSX forensic proof and metrics"),
]
page("provenance", "Provenance & rights", """
These records document **who created RSOS, when, and how**. They are preserved unchanged at their original paths and kept apart from the functional map of the operating system.

- [Authorship & legal chain](authorship/) — origin declarations, public anchors, legal chains, copyright statements, author metadata and the RSX licensing framework: the dated record of authorship.
- [IP strategy](ip-strategy/) — the disclosure map and trade-secret-labelled records. The "private" and "trade secret" labels are historical strategic labels from the development period; the archive is now public.
- [AI interaction records](ai-interaction/) — the Echo proof chains and metrics logs: records of the development dialogue with AI models, including the models' statements about their own weights, telemetry and behaviour, and the metrics recorded at the time. They are kept as evidence of how the system was built.

Copies of several RSSO records also exist in [PASS31B](../rsso/pass31b/).
""")
page("provenance/authorship", "Authorship & legal chain", "The dated record of authorship of RSOS, RSIA, RSX and RSSO.", AUTH)
page("provenance/ip-strategy", "IP strategy (historical labels)", "Records of the disclosure strategy during development. Their \"private\" and \"trade secret\" labels describe that period; the archive is now public.", IP)
page("provenance/ai-interaction", "AI interaction records", "Records of the development dialogue with AI models (\"Echo\"): proof chains, the metrics recorded during development, and the models' statements about their own weights, telemetry and behaviour, preserved as recorded.", AI)

# ------------------------------------------------------------------ source -> page map
rows = list(csv.DictReader(open(ARCH / "SOURCE-TO-ARCHITECTURE-MAP.csv", encoding="utf-8")))
for r in rows:
    pages = PAGES.get(r["source_path"], [])
    main = [x for x in pages if "/pass31b/" not in x] or pages
    r["sha256"] = MANIFEST[r["source_path"]]["sha256"]
    r["derived_index"] = main[0]
with open(ARCH / "SOURCE-TO-ARCHITECTURE-MAP.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator="\n")
    w.writeheader(); w.writerows(rows)

print("architecture pages written")
