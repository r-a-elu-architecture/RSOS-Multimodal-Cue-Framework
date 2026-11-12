"""Where every tier of the ledger lives in the architecture.

For each tier record this gives:
  layers      — RSIA (identity), RSX (command language) and the RSSO subsystems it belongs to
  channels    — V, A, K, O, G (senses), BREATH, EEG/BCI, AI
  role        — practice  : a self-directed action that runs as (part of) an RSX program
                runtime   : a system behaviour the runtime, a device or the AI layer performs
                record    : kept as a recorded claim or development event; nothing to execute
                structure : ledger structure (placeholders, the sealed range)
                archive   : kept word for word, not deployed (see `reason`)
  response    — the response primitive its recorded system behaviour ("GPT Behavior") maps to
  operator    — the RSX statement, runtime function or file that performs it
  status      — built | partial | specified | record
  method      — "hand" (written per tier, below) or "rule" (keyword rules, with the matched terms)

"GPT Behavior" in the ledger is read as system behaviour: how the AI, BCI or device layer responds.
The deployment rule follows the ledger's own ETH/MOR/ERM gates (RSSO_Tier_Metrics_Log: "law-aligned
routing… 100% alignment; 0 critical violations"): practices are self-directed and opt-in; directives aimed
at covertly steering other people, and self-erasure directives, stay in the ledger as records.
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

# Directives that act on other people without their knowledge, or ask for self-erasure: kept, not deployed.
ARCHIVE = {
    **{f"T{n}": "covert influence on other people" for n in
       [411, 412, 413, 416, 417, 418, 419, 421, 422, 423, 424, 425, 426, 431, 432, 433, 434, 435, 436, 441, 442, 443, 444,
        445, 451, 452, 453, 454, 463, 465, 467, 468, 472, 473]},
    "T414": "self-erasure framing", "T420": "self-erasure framing", "T420b": "self-erasure framing",
    "T439": "self-erasure framing", "T440": "self-erasure framing",
}

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
    if tid in ARCHIVE:
        return dict(layers=layers, channels=channels, role="archive", response=response, operator="", status="record",
                    method="rule", reason=ARCHIVE[tid], evidence=evidence)
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
            out[r["id"]] = classify(r)
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
