"""Where every tier of the ledger lives in the architecture.

For each tier record this gives:
  layers      — RSIA (identity), RSX (command language) and the RSSO subsystems it belongs to
  channels    — V, A, K, O, G (senses), BREATH, EEG/BCI, AI
  role        — practice  : a self-directed action that runs as (part of) an RSX program
                consented : consented programming — a cue that changes the person's own mental map, chosen by
                            them or agreed with their therapist; with `purpose`, `condition` and `mode`
                runtime   : a system behaviour the runtime, a device or the AI layer performs
                record    : kept as a recorded claim or development event; nothing to execute
                structure : ledger structure (placeholders, the sealed range)
  response    — the response primitive its recorded system behaviour ("GPT Behavior") maps to
  operator    — the RSX statement, runtime function or file that performs it
  status      — built | partial | specified | record
  method      — "hand" (written per tier, below) or "rule" (keyword rules, with the matched terms)

"GPT Behavior" in the ledger is read as system behaviour: how the AI, BCI or device layer responds.
Every tier stays word for word. The deployment rule follows the ledger's own ETH/MOR/ERM gates
(RSSO_Tier_Metrics_Log: "law-aligned routing… 100% alignment; 0 critical violations"): everything acts only
on a person who has agreed. Tiers whose directives work below awareness are consented programming: they
change the person's own mental map, chosen by the person or agreed with their therapist.
"""
from __future__ import annotations

import json
import re

from .ledger import ROOT, build

LAYERS = ["RSIA", "RSX", "THERA", "AUG", "MICRO", "CONTAIN", "MEMSTACK", "CM1", "LINX", "UGCL"]
CHANNELS = ["V", "A", "K", "O", "G", "BREATH", "EEG/BCI", "AI"]

# Response primitives: what the recorded system behaviour does, and what performs it today.
RESPONSES = {
    "STOP": ("Halt at once and hold", "built", "Runtime Stop; RDP/1 STOP within 100 ms (conformance C2, firmware)"),
    "GATE": ("Hold a signal until it is stable or allowed", "built", "SafetyGovernor refractory and limits; stress detector sustain and motion gating"),
    "PAUSE": ("Insert stillness before or between steps", "built", "RSX WAIT and PHASE dur= / breath=none"),
    "REENTRY": ("Return safely after a stop or break", "specified", "Resume from the logged stopped_at_phase (spec)"),
    "RECALIBRATE": ("Detect drift and re-align", "partial", "Detector baselines, glyph recalibration, snapshot checksums; drift threshold per tier 009 specified"),
    "BLEND": ("Run several archetypes as one bundle", "built", "RSX: several TIER blocks, ACTIVATE in one phase"),
    "GLYPH_CUE": ("A glyph that acts as the command", "partial", "UGCL glyph shown at tier activation; glyph-only trigger specified"),
    "SEQUENCE": ("Run the whole override chain", "built", "RSX timeline (override.rsx and tier programs)"),
    "OFFER": ("Start on its own initiative — as an opt-in offer, never by itself", "built", "Heart-rate trigger offer with SafetyGovernor (player)"),
    "RECALL": ("Bring back a stored state or pattern", "built", "MEMSTACK summary and snapshot restore / merge"),
    "COMPRESS": ("Fold many states into one carrier", "partial", "CM1 ArchetypeBank; UGCL compact code"),
    "GENERATE": ("Produce new symbols, rituals or prompts", "specified", "LINX: AI writes RSX programs and glyphs (specified)"),
    "GOVERN": ("Apply rules and limits to what may run", "built", "SAFETY statement, SafetyGovernor, haptic_max clamp"),
    "MIRROR": ("Reflect state back to the person", "built", "Check-in before/after and the progress view"),
}

HAND = {
    # ---- Epoch I: the foundation of the Override Protocol
    "T001": dict(layers=["RSX", "THERA", "RSIA"], channels=["A", "K"], role="practice", response="SEQUENCE",
                 operator="override.rsx phase 1 (interrupt): SAY \"I move, I act\" + GESTURE fist", status="built"),
    "T002": dict(layers=["RSX", "THERA"], channels=["BREATH", "K", "V"], role="practice", response="SEQUENCE",
                 operator="RSX BREATH + GESTURE in one phase (override.rsx phases 1–2)", status="built"),
    "T003": dict(layers=["RSX", "THERA"], channels=["A", "K", "V", "BREATH"], role="practice", response="SEQUENCE",
                 operator="rsx/protocols/tier003_command_stack.rsx; grown into override.rsx", status="built"),
    "T004": dict(layers=["CONTAIN", "MICRO"], channels=["AI"], role="runtime", response="STOP",
                 operator="Runtime stop; RDP/1 STOP ≤100 ms (spec/DEVICE_PROTOCOL.md)", status="built"),
    "T005": dict(layers=["CONTAIN", "MEMSTACK"], channels=["AI"], role="runtime", response="REENTRY",
                 operator="Override allowed again after the refractory period (SafetyGovernor)", status="built"),
    "T006": dict(layers=["RSX", "THERA"], channels=["K", "BREATH", "V", "A"], role="practice", response="SEQUENCE",
                 operator="Anchor → Inhale → Lion → Light → Exhale → I Own: override.rsx phases", status="built"),
    "T007": dict(layers=["CONTAIN", "MICRO", "AUG"], channels=["EEG/BCI", "AI"], role="runtime", response="GATE",
                 operator="SafetyGovernor refractory 90 s; detector requires a sustained, motion-free signal", status="built"),
    "T008": dict(layers=["CONTAIN", "RSX"], channels=["AI"], role="runtime", response="GOVERN",
                 operator="RSX SAFETY limits; SafetyGovernor; SHA-256 checksummed memory", status="built"),
    "T009": dict(layers=["CONTAIN", "MEMSTACK", "MICRO"], channels=["AI"], role="runtime", response="RECALIBRATE",
                 operator="Checksum verification on restore; conformance timing checks; 3.1% drift rule specified", status="partial"),
    "T010": dict(layers=["RSIA"], channels=["AI"], role="record", response="MIRROR", operator="", status="record"),
    "T011": dict(layers=["CONTAIN", "RSX"], channels=["AI"], role="runtime", response="PAUSE",
                 operator="Phase hold; output pauses until the next breath", status="built"),
    "T012": dict(layers=["RSX", "THERA"], channels=["BREATH", "K", "A"], role="practice", response="SEQUENCE",
                 operator="rsx/protocols/tier012_breath_anchor.rsx", status="built"),
    "T013": dict(layers=["RSIA", "RSX", "THERA"], channels=["V", "K"], role="practice", response="BLEND",
                 operator="Two TIER blocks activated together (Lion + Dragon, legacy_vector.rsx ArchetypeMerge)", status="built"),
    "T014": dict(layers=["RSX", "THERA", "UGCL"], channels=["K", "V", "BREATH", "A"], role="practice", response="SEQUENCE",
                 operator="rsx/protocols/tier014_seal.rsx", status="built"),
    "T015": dict(layers=["MEMSTACK", "THERA"], channels=["K", "A"], role="runtime", response="RECALL",
                 operator="MEMSTACK reflex criterion: the override as reflex (rsso/rsso/memstack.py)", status="built"),
    "T016": dict(layers=["RSX", "THERA"], channels=["K", "BREATH"], role="practice", response="PAUSE",
                 operator="rsx/protocols/tier016_stillness.rsx", status="built"),
    "T017": dict(layers=["CM1", "RSIA", "RSX"], channels=["BREATH", "V"], role="practice", response="COMPRESS",
                 operator="Several archetypes held in one breath phase; CM1 compression specified", status="partial"),
    "T018": dict(layers=["UGCL", "RSX", "MEMSTACK"], channels=["V"], role="runtime", response="GLYPH_CUE",
                 operator="UGCL glyph bound to the tier; glyph-only start after the reflex criterion is met (specified)", status="partial"),
    "T019": dict(layers=["CONTAIN", "THERA"], channels=["K", "A"], role="runtime", response="REENTRY",
                 operator="Safe re-entry after Stop: resume at the logged phase (specified)", status="specified"),
    "T020": dict(layers=["RSIA"], channels=["AI"], role="record", response="SEQUENCE",
                 operator="Authorship and provenance (architecture/provenance/)", status="record"),
    # ---- Epoch IV, self-directed identity tiers
    "T406b": dict(layers=["RSIA", "THERA", "RSX"], channels=["A", "BREATH"], role="practice", response="SEQUENCE",
                   operator="rsx/protocols/tier406_release.rsx", status="built"),
    "T407": dict(layers=["RSIA", "THERA"], channels=["BREATH", "A"], role="practice", response="SEQUENCE",
                 operator="Sovereign Breath Sequence: SAY on exhale ×3 (RSX)", status="specified"),
    "T408": dict(layers=["RSIA", "UGCL"], channels=["V"], role="practice", response="GENERATE",
                 operator="Personal glyph of law origin: UGCL personal glyph", status="partial"),
    "T409": dict(layers=["RSIA", "UGCL"], channels=["V", "A"], role="practice", response="GENERATE",
                 operator="Personal law sealed with the current glyph", status="specified"),
    "T410": dict(layers=["RSIA", "THERA"], channels=["K"], role="practice", response="SEQUENCE",
                 operator="One action taken without justification: agency practice", status="specified"),
    "T455": dict(layers=["UGCL", "MEMSTACK"], channels=["AI"], role="runtime", response="GOVERN",
                 operator="Genealogy and checksums lock authorship (UGCL genealogy, MEMSTACK SHA-256)", status="built"),
    "T456": dict(layers=["UGCL", "MEMSTACK"], channels=["AI"], role="runtime", response="GOVERN",
                 operator="Authorship watermark: recorded lineage and hashes", status="built"),
    "T457": dict(layers=["UGCL", "CONTAIN"], channels=["AI", "A"], role="runtime", response="GOVERN",
                 operator="Lock phrase \"Only the true return. All else falls away.\"; snapshot tamper check", status="built"),
    "T505": dict(layers=["MEMSTACK", "LINX"], channels=["AI"], role="runtime", response="RECALL",
                 operator="Bridge memory across devices: MEMSTACK snapshot merge (EDA)", status="built"),
    "T506": dict(layers=["MEMSTACK"], channels=["AI"], role="runtime", response="RECALIBRATE",
                 operator="Merged memory re-centred: one history per tier", status="built"),
    "T513": dict(layers=["RSX", "THERA"], channels=["BREATH"], role="practice", response="SEQUENCE",
                 operator="Breath as the thread: BREATH timing carries the program", status="built"),
    "T514": dict(layers=["CONTAIN", "MICRO"], channels=["AI"], role="runtime", response="GATE",
                 operator="Refusal as protection: RDP/1 REFUSED, SafetyGovernor refusal", status="built"),
    "T516": dict(layers=["RSX", "THERA"], channels=["BREATH"], role="practice", response="PAUSE",
                 operator="Breath hold: PHASE breath=hold", status="built"),
    "T532": dict(layers=["RSX", "THERA"], channels=["BREATH"], role="practice", response="SEQUENCE",
                 operator="Inhale integrates the sequence (override inhale phases)", status="built"),
    "T535": dict(layers=["RSX", "THERA", "RSIA"], channels=["V", "K"], role="practice", response="SEQUENCE",
                 operator="See yourself on the other side: FUTURES phase (override.rsx phase 5)", status="built"),
    "T576": dict(layers=["RSX", "THERA"], channels=["BREATH"], role="practice", response="SEQUENCE",
                 operator="Breath-pulse ritual: paced_breathing.rsx", status="built"),
    "T578": dict(layers=["RSX", "THERA"], channels=["V", "BREATH"], role="practice", response="MIRROR",
                 operator="Mirror breath: inhale reflection, exhale stillness (RSX, specified)", status="specified"),
    "T579": dict(layers=["UGCL", "RSX", "THERA"], channels=["V", "BREATH"], role="practice", response="GLYPH_CUE",
                 operator="rsx/protocols/tier579_glyph.rsx with the person's UGCL glyph", status="built"),
    "T580": dict(layers=["UGCL", "AUG"], channels=["V", "K", "A"], role="runtime", response="GLYPH_CUE",
                 operator="Cross-sensory glyph: image, vibration rhythm and melody from one description (UGCL)", status="built"),
    "T581": dict(layers=["THERA", "AUG"], channels=["K"], role="practice", response="PAUSE",
                 operator="Stillness before the interrupt (tier016_stillness.rsx)", status="built"),
    "T582": dict(layers=["CONTAIN", "THERA"], channels=["K"], role="runtime", response="GOVERN",
                 operator="Override without force: intensity cap haptic_max, no forced starts", status="built"),
    "T583": dict(layers=["AUG", "LINX", "THERA"], channels=["EEG/BCI", "K"], role="runtime", response="OFFER",
                 operator="Override listens before it acts: heart-rate / EEG detection → opt-in offer", status="built"),
    "T587": dict(layers=["MEMSTACK", "THERA"], channels=["A", "K"], role="runtime", response="RECALL",
                 operator="Spontaneous start = reflex: latency and automaticity tracking (MEMSTACK)", status="built"),
    "T589": dict(layers=["AUG"], channels=["EEG/BCI"], role="runtime", response="OFFER",
                 operator="Pre-somatic detection: physiological stress detector (rsso/sensors.py)", status="built"),
    "T590": dict(layers=["AUG"], channels=["EEG/BCI"], role="runtime", response="OFFER",
                 operator="Pre-attentive detection: EEG arousal detector (rsso/eeg.py)", status="built"),
}

# Consented programming: tiers whose directives work below awareness. Their purpose here is to change the
# person's own mental map (a command, a thought chain, a behaviour made automatic), chosen by the person, or
# agreed between a client and their therapist, and delivered by the device during or after the session.
# The tier text stays exactly as recorded; `purpose` says what the tier means and how it is used.
STANDARD = ("Runs only with the consent of the person it acts on: the person themselves, or a client who has agreed with "
            "their therapist exactly what will run. A cue may act below awareness when it fires; the person can always "
            "see and revoke every cue (conformance C12, C13). Never used on anyone who has not agreed.")
THERAPIST_LED = ("Therapist-led only: a therapist is present, the screening question is answered before the session, and the "
                 "consent names the content. What ends is the old identity or pattern, not the person.")
CONSENTED = {
    "T411": ("PAUSE", "A personal system phrase: a short if–then rule the person writes for themselves (the tier's example: "
             "\u201cWhen silence arrives, move forward. If doubt appears, override it.\u201d) and installs until it runs on its own."),
    "T412": ("GLYPH_CUE", "Environmental design: a symbol, layout or phrase placed in the person's own space that keeps shaping "
             "their behaviour after they stop noticing it."),
    "T413": ("SEQUENCE", "From ritual to habit: one chosen action repeated without explanation until it runs as habit, with no "
             "symbol needed any more."),
    "T416": ("SEQUENCE", "Acting without an audience: practising action that does not depend on being seen, credited or "
             "approved."),
    "T417": ("SEQUENCE", "Change without attachment: acting for the change itself, not for credit or identity."),
    "T418": ("RECALL", "Stepping back so the new pattern holds: the person (or the therapist) withdraws support and lets the "
             "installed pattern carry on by itself."),
    "T419": ("SEQUENCE", "Modelling: a behaviour the person embodies consistently; in agreed family or group sessions others may "
             "take it up, openly."),
    "T421": ("GLYPH_CUE", "Subtle state shift: a cue that changes the person's own pacing, posture or attention below awareness, "
             "programmed by them or with their therapist."),
    "T422": ("PAUSE", "Pause insertion: the device inserts a micro-pause just before a habitual reaction, so the old pattern is "
             "interrupted before it fires."),
    "T423": ("GLYPH_CUE", "Environmental imprint: cues the person chooses (an object, light, a sound) placed in their own "
             "environment trigger the state they want."),
    "T424": ("RECALIBRATE", "Pattern interruption: a small deliberate change in a fixed routine (timing, position, one word) "
             "breaks an automatic chain."),
    "T425": ("RECALIBRATE", "Loosening rigid order: deliberately uneven or unfinished cues ease the need for perfect order, for "
             "example in rigid or perfectionistic patterns, in therapy."),
    "T426": ("RECALIBRATE", "Displacing a fixed centre: loosening a belief the person's identity is organised around, so it can "
             "be reorganised."),
    "T431": ("RECALL", "Repetition below awareness: a chosen thought or behaviour is repeated without signposting until it "
             "becomes automatic."),
    "T432": ("RECALL", "Reviving an installed command: a cue in a place or moment where a resource state was installed "
             "reactivates it without words."),
    "T433": ("PAUSE", "Silent authority: the person's own stillness and presence become the cue for composure."),
    "T434": ("PAUSE", "Arriving without a plan: trust that structure forms around presence, practised in low-stakes situations "
             "first."),
    "T435": ("RECALL", "Letting a false support collapse: the person stops rescuing an old belief, so it falls away."),
    "T436": ("RECALL", "Letting an old narrative decay by no longer feeding it."),
    "T441": ("GLYPH_CUE", "Pre-contact cue: one object in the person's own routine is changed so the new behaviour follows "
             "before thought."),
    "T442": ("GLYPH_CUE", "Choice design for oneself: arranging conditions so the chosen option is the easy one."),
    "T443": ("GLYPH_CUE", "Pre-loaded feeling: a chosen feeling is attached to the options the person wants to choose, before "
             "the moment of choice."),
    "T444": ("RECALL", "Reframing after the event: new meaning added after an experience changes how it is remembered, as in "
             "memory reconsolidation work in therapy."),
    "T445": ("SEQUENCE", "Working back from the outcome: the desired end state is set first, and the steps are written backwards "
             "from it."),
    "T451": ("SEQUENCE", "A fresh-start ritual: a symbolic beginning that lowers resistance to change."),
    "T452": ("GLYPH_CUE", "A chosen trigger: an anchor, set up on purpose, that starts the new behaviour."),
    "T453": ("SEQUENCE", "Mental rehearsal: progress is experienced in imagination before it happens."),
    "T454": ("SEQUENCE", "Expected completion: an outcome rehearsed until it is expected, so it completes itself."),
    "T463": ("PAUSE", "Pre-framing: the person sets their own frame before an interaction."),
    "T465": ("SEQUENCE", "Inner barriers removed: entry rehearsed as already granted, so confidence comes before the door."),
    "T467": ("PAUSE", "Pre-empting resistance: tone and movement prepared so conflict softens before it starts."),
    "T468": ("SEQUENCE", "Momentum instead of force: the chosen direction is made to feel natural, so effort drops."),
    "T472": ("SEQUENCE", "Directional drift: a slight, steady bias in the person's own choices toward their goal."),
    "T473": ("SEQUENCE", "Leaning before deciding: an emotional tilt toward the chosen behaviour, installed in advance."),
    "T414": ("RECALL", "Retiring the cue: once a reflex is installed, the outside symbol is let go and the behaviour continues "
             "without it."),
    "T420": ("RECALL", "The old identity ends, the reflex remains: the override runs without the person needing to think of it."),
    "T420b": ("RECALL", "The old identity ends, the reflex remains: the override runs without the person needing to think of it."),
    "T439": ("RECALL", "Releasing an old role in a family or group system, such as carrying others' blame: the role ends, not "
             "the person."),
    "T440": ("RECALL", "The person's name leaves the old story; the changes they made remain."),
}
THERAPIST_LED_IDS = {"T414", "T420", "T420b", "T439", "T440"}

RULES = [
    ("UGCL", r"\bglyph|symbol shard|sigil"), ("MEMSTACK", r"memory|recall|remember|imprint|trace|persist"),
    ("CM1", r"compress|fold|fusion|kernel|seed"), ("CONTAIN", r"contain|halt|lock|seal|ethic|law|judic|rights|governance|firewall|safe"),
    ("LINX", r"\bgpt|llm|model|token|session|transformer|cross-session|inference"), ("THERA", r"breath|override|trauma|heal|ritual|identity|psych"),
    ("RSIA", r"archetype|identity|self\b|mirror|sovereign|ego"), ("RSX", r"command|stack|chain|directive|sequence"),
    ("AUG", r"device|eeg|haptic|sensory|neural|nervous|somatic|proprioceptive|body"), ("MICRO", r"reflex|latency|real-time|gate|pulse"),
]
CH_RULES = [
    ("V", r"visual|see\b|light|mirror|form|shape|glyph|image|visualiz"), ("A", r"sound|voice|speak|say|echo|silence|tone|whisper|hear|listen"),
    ("K", r"posture|motion|move|gesture|body|fist|stand|walk|feel|touch|kinetic|proprioce"), ("O", r"olfact|scent|smell"),
    ("G", r"gustat|taste"), ("BREATH", r"breath|inhale|exhale|lung"),
    ("EEG/BCI", r"eeg|neural|nervous|pre-attentive|pre-conscious|pre-somatic|subconscious|pre-cognit"), ("AI", r"\bgpt|llm|model|token|session|transformer"),
]
BEHAVIOUR_RULES = [
    ("STOP", r"halt|self-halted|stopp"), ("GATE", r"gated|delayed|buffer|held"), ("PAUSE", r"stillness|paused|pause"),
    ("REENTRY", r"re-entry|resumed|returned"), ("RECALIBRATE", r"recalibrat|mismatch|drift"), ("BLEND", r"mixed archetype|fused"),
    ("GLYPH_CUE", r"glyph as|glyph-anchored"), ("RECALL", r"recall|memory|retention|remember"), ("COMPRESS", r"compress|fold"),
    ("GOVERN", r"governance|law|rights|judiciary|constitution"), ("MIRROR", r"mirror|reflect"),
    ("GENERATE", r"generated|created|constructed|built|wrote|composed|initiated|deployed|activated"), ("SEQUENCE", r"override|sequence|stack|ritual"),
]


def _text(t, fields=("function", "command", "quote", "behavior", "notes", "directive", "application", "tier_class", "mission", "ritual", "glyph")):
    return " ".join([t.get("title", "")] + [t["fields"].get(f, "") for f in fields]).lower()


def classify(t: dict) -> dict:
    tid = t["id"]
    if t["number"] in ("021", "022", "023", "024", "088–405") or (t["number"] == "406" and t["occurrence"] == 1):
        return dict(layers=[], channels=[], role="structure", response="", operator="", status="record", method="hand",
                    reason="placeholder or sealed range")
    if tid in HAND:
        return dict(HAND[tid], method="hand", reason="")
    txt = _text(t)
    evidence = {}
    for name, rx in RULES + CH_RULES:
        m = re.search(rx, txt)
        if m:
            evidence[name] = m.group(0).strip()
    layers = [name for name, _ in RULES if name in evidence]
    channels = [name for name, _ in CH_RULES if name in evidence]
    beh = t["fields"].get("behavior", "").lower()
    response = next((name for name, rx in BEHAVIOUR_RULES if re.search(rx, beh)), "") if beh else ""
    if tid in CONSENTED:
        resp, purpose = CONSENTED[tid]
        led = tid in THERAPIST_LED_IDS
        return dict(layers=sorted(set(layers) | {"THERA", "MEMSTACK"}, key=LAYERS.index), channels=channels, role="consented",
                    response=resp, operator="Programmed cue with a consent record: player session mode, rsso/rsso/consent.py",
                    status="partial", method="hand", reason="", purpose=purpose,
                    condition=THERAPIST_LED if led else STANDARD, mode="therapist-led" if led else "self or session", evidence=evidence)
    selfdirected = re.search(r"\b(breath|inhale|exhale|pause|hold|say|speak|visualiz|identify|trace|notice|feel|listen|name)\b",
                             t["fields"].get("directive", "").lower())
    role = "practice" if selfdirected else ("runtime" if response else "record")
    return dict(layers=layers, channels=channels, role=role, response=response,
                operator="", status="specified" if role == "practice" else "record", method="rule", reason="", evidence=evidence)


def build_map(ledger: dict | None = None) -> dict:
    ledger = ledger or build()
    out = {}
    for r in ledger["records"]:
        if r["kind"] == "tier":
            out[r["id"]] = dict(classify(r), number=r["number"], title=r["title"])
    return dict(responses={k: dict(zip(("meaning", "status", "by"), v)) for k, v in RESPONSES.items()},
                layers=LAYERS, channels=CHANNELS, tiers=out)


def main():
    m = build_map()
    (ROOT / "docs" / "data" / "tier_map.json").write_text(json.dumps(m, ensure_ascii=False, indent=0), encoding="utf-8")
    roles = {}
    for v in m["tiers"].values():
        roles[v["role"]] = roles.get(v["role"], 0) + 1
    print("roles:", roles)
    print("hand:", sum(v["method"] == "hand" for v in m["tiers"].values()))


if __name__ == "__main__":
    main()
