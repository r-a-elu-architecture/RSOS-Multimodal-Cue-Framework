"""Nodes: personal conditioned operators, designed from an intake and installed by practice (spec/NODES.md).

A node is a state held as one unit: a representation (a golden sphere of light, a lion, a raven), the cues on
every channel (V A K O G), a vibration code (tacton), a glyph, a mode (associated: in the body; observer:
nothing binds, only observed), and the mental frame held in that state, what is said in it, which sets how
widely the person perceives. Practised together, any one channel can later open the whole node.

This module (identical to docs/js/nodes.js, tested):
  - TACTONS: the vibration alphabet of the archetypes (. short 100 ms, - long 300 ms, 100 ms apart);
  - frame_check: scope, process or trait, and wording risks of a frame, with suggestions;
  - plan: from an intake (concerns, body, triggers, desired states, nodes, dose, devices) to a full plan:
    nodes with codes and glyphs, the RSX program of each node, ledger tiers, metrics, schedule, devices,
    safety requirements; the plan is a proposal for the person and their therapist to approve;
  - channel_opening: from the run log, how reliably each channel alone already opens the practice.
"""
from __future__ import annotations

import math
import re
import statistics

PLANNER = "rsos-planner/1"
SHORT, LONG, GAP = 100, 300, 100

ARCHETYPES = {
    "LION": dict(tacton="..-", glyph="🦁", mode="associated", meaning="Courage and boundaries",
                 frame="I breathe fully and completely, and I hold my ground", source="Tier 001"),
    "RAVEN": dict(tacton=".-.", glyph="", mode="associated", meaning="Intelligence and the wide view",
                  frame="I am intelligent and I see broadly, from above", source=""),
    "EAGLE": dict(tacton="-..", glyph="", mode="associated", meaning="Overview and precision",
                  frame="I see the whole field clearly and choose my moment", source=""),
    "LEOPARD": dict(tacton="...", glyph="", mode="associated", meaning="Agility and focus",
                    frame="I move lightly and stay fully focused", source=""),
    "TIGER": dict(tacton="-.-", glyph="", mode="associated", meaning="Power and drive",
                  frame="I move with power toward what I choose", source=""),
    "BEAR": dict(tacton="--", glyph="", mode="associated", meaning="Strength and stability",
                 frame="I stand steady and strong", source=""),
    "DRAGON": dict(tacton="---", glyph="🐉", mode="associated", meaning="Strength and shadow held together",
                   frame="I hold my strength and my shadow in one breath", source="Tier 013"),
    "OBSERVER": dict(tacton="-", glyph="∅", mode="observer", meaning="No ego: nothing binds, only observed",
                     frame="Nothing binds. Nothing holds. Only observed", source="∅ in the tier ledger"),
}
CODE_POOL = [".", "..", ".-", "-.", "....", ".--", "--.", "..--", "-.-.", ".-..", "--..", "...-", "-...", ".---"]

CONCERNS = {
    "ptsd": "PTSD or trauma", "depression": "Depression", "chronic_stress": "Chronic stress", "stress": "Stress",
    "anxiety": "Anxiety", "habits": "Unwanted habits (for example scrolling)", "confidence": "Confidence and boundaries",
    "focus": "Focus and work",
}
TIER_SETS = {   # ledger tiers that carry each purpose (docs/data/tier_map.json)
    "associated": ["T001", "T003", "T006", "T014"],
    "calm": ["T012", "T016", "T513", "T576"],
    "observer": ["T016", "T578", "T581", "T433"],
    "memory": ["T444"],
    "habits": ["T422", "T441"],
    "futures": ["T535"],
    "reflex": ["T587"],
}
CHANNEL_DEVICE = {"V": "Screen or VR: the node's glyph and representation", "A": "Earbuds: the node's sound and spoken frames",
                  "K": "Wristband: the node's vibration code; posture and gesture", "O": "Scent module: the node's scent",
                  "G": "Taste cue the person brings (for example a specific mint)"}

PROCESS = {"breathe", "breathes", "see", "sees", "move", "moves", "act", "acts", "hold", "holds", "notice", "choose", "stand",
           "speak", "walk", "listen", "observe", "observed", "let", "return", "step", "focus", "say", "feel", "rise", "keep"}
BROAD = ["broadly", "whole", "all", "everything", "from above", "wide", "widely", "clearly", "fully", "completely", "every",
         "big picture", "the field"]
NARROW = ["only", "just", "a bit", "a little", "good at", "try", "trying", "somewhat"]
NEGATION = {"not", "no", "never", "don't", "dont", "won't", "can't", "cannot", "stop", "without"}
ABSOLUTE = {"always", "never", "exceptional", "perfect", "perfectly", "best", "unlimited", "infinite", "flawless"}


def tacton_pulses(code: str) -> list[list[int]]:
    """[[on_ms, off_ms], ...] for a code; the last off is 0."""
    out = [[SHORT if c == "." else LONG, GAP] for c in code]
    if out:
        out[-1][1] = 0
    return out


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z']+", text.lower())


def _has(text: str, phrase: str) -> bool:
    return (" " + " ".join(_words(text)) + " ").find(" " + phrase + " ") >= 0


def frame_check(text: str, mode: str = "associated", believability=None) -> dict:
    words = _words(text)
    trait = _has(text, "i am") or _has(text, "i'm")
    process = any(w in PROCESS for w in words)
    kind = "process and trait" if (trait and process) else "trait" if trait else "process" if process else "statement"
    broad = [p for p in BROAD if _has(text, p)]
    narrow = [p for p in NARROW if _has(text, p)]
    scope = "mixed" if (broad and narrow) else "broad" if broad else "narrow" if narrow else "neutral"
    flags, tips = [], []
    if narrow and mode == "associated":
        flags.append("narrowing")
        tips.append("Narrowing words (" + ", ".join(narrow) + ") shrink the frame. Say what you see or do in full.")
    if mode == "associated" and any(w in NEGATION for w in words):
        flags.append("negation")
        tips.append("Say what you do, not what you don't: the mind has to picture the thing a negation names.")
    absolutes = [w for w in words if w in ABSOLUTE]
    if absolutes:
        flags.append("absolute")
        tips.append("Absolutes (" + ", ".join(absolutes) + ") are easy to doubt. A process frame such as “I breathe fully and see clearly” is easier to believe.")
    if "will" in words:
        flags.append("future")
        tips.append("Use the present tense: the frame describes the state you are in now.")
    if len(words) > 16:
        flags.append("long")
        tips.append("Keep a frame under 16 words so it can be said on one exhale.")
    if trait and not process:
        flags.append("trait only")
        tips.append("Add what you do in that state (I see, I breathe, I move): process frames hold up better than claims about who you are.")
    if believability is not None and believability < 6:
        flags.append("low believability")
        tips.append("You rated it " + str(believability) + " of 10. Choose a wording you can believe today; it can grow later.")
    if scope == "neutral" and mode == "associated":
        tips.append("To widen perception, add how far you see or feel: broadly, from above, the whole field.")
    return dict(text=text, kind=kind, scope=scope, broad=broad, narrow=narrow, flags=flags, tips=tips,
                score=max(0, 100 - 15 * len(flags)))


def _q(s: str) -> str:
    return '"' + str(s).replace("\\", "\\\\").replace('"', "'").replace("\n", " ").strip() + '"'


def _slug(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", name.strip()).strip("_").upper()
    return s or "NODE"


def node_program(n: dict, inhale: int = 4, exhale: int = 6) -> str:
    name, mode = n["key"], n["mode"]
    L = [f"# Node {n['name']} ({mode}), generated by the RSOS planner from an intake (spec/NODES.md).",
         f"PROTOCOL node_{name.lower()} {_q('Node: ' + n['name'])}", "VERSION 1.0",
         "SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4", f"BREATH inhale={inhale}s exhale={exhale}s", "",
         f"TIER 1 {name} {{"]
    for ch in ("V", "A", "K", "O", "G"):
        if n["channels"].get(ch):
            L.append(f"  {ch} {_q(n['channels'][ch])}")
    if n["glyph"]:
        L.append(f"  GLYPH {_q(n['glyph'])}")
    L.append(f"  WORD {_q(n['meaning'])}")
    for f in n["frames"]:
        L.append(f"  FRAME {_q(f)}")
    L += [f"  MODE {_q(mode)}", f"  TACTON {_q(n['tacton'])}", "}", ""]
    if n["contexts"]:
        L += ["FUTURES " + " | ".join(_q(c) for c in n["contexts"][:3]), ""]
    phases = []   # (breath, lines): an inhale is inserted between two exhales so the breathing stays natural
    if mode == "associated":
        phases.append(("interrupt", "", ['  SAY "I move, I act"', '  GESTURE "Spine straight, head up, clench your fist"']))
    else:
        phases.append(("stillness", "dur=3s", ['  FEEL "Stillness. The body stays still"']))
    phases.append(("inhale", "breath=inhale", [f"  ACTIVATE {name}", f"  SEE {_q(n['representation'])}"]))
    for i, f in enumerate(n["frames"]):
        phases.append((f"frame{i + 1}", "breath=exhale", [f"  SAY {_q(f)}"]))
    if mode == "observer":
        phases.append(("position", "dur=4s", ['  SEE "See it from another position: nothing binds, only observed"']))
    if n["contexts"]:
        phases.append(("futures", "breath=exhale", [f"  FEEL {_q('Hold the ' + n['name'].lower() + ' in you as you enter')}",
                                                   "  FOR FUTURE {", '    SEE "$future"', "    WAIT 1s", "  }"]))
    phases.append(("seal", "breath=exhale", ['  SAY "I own"' if mode == "associated" else '  FEEL "Let it settle"', '  MARK "installed"']))
    prev, k = "", 0
    for pname, attr, body in phases:
        if attr == "breath=exhale" and prev == "breath=exhale":
            k += 1
            L += [f"PHASE breathe{k} breath=inhale {{", '  FEEL "Breathe in"', "}"]
        L += [f"PHASE {pname} {attr} {{" if attr else f"PHASE {pname} {{"] + body + ["}"]
        prev = attr
    return "\n".join(L) + "\n"


def plan(intake: dict) -> dict:
    concerns = [c for c in intake.get("concerns", []) if c in CONCERNS]
    devices = intake.get("devices", {})
    used, nodes = set(), []
    for raw in intake.get("nodes", []):
        arch = str(raw.get("archetype", "")).upper()
        base = ARCHETYPES.get(arch, {})
        if raw.get("tacton"):
            code = raw["tacton"]
        elif base.get("tacton") and base["tacton"] not in used:
            code = base["tacton"]
        else:
            code = next(c for c in CODE_POOL + [x + "." for x in CODE_POOL] if c not in used and c not in [a["tacton"] for a in ARCHETYPES.values()])
        used.add(code)
        mode = raw.get("mode") or base.get("mode", "associated")
        name = raw.get("name") or arch.title() or "Node"
        frames = [f.strip() for f in raw.get("frames", []) if f.strip()][:5] or ([base["frame"]] if base else [])
        rep = raw.get("representation") or ("A sphere of golden light" if mode == "associated" else "A clear, empty space around you")
        ch = {k: str(raw.get(k, "")).strip() for k in ("V", "A", "K", "O", "G")}
        ch["V"] = ch["V"] or rep
        ch["A"] = ch["A"] or (frames[0] if frames else "Your own sound")
        ch["K"] = ch["K"] or ("Spine straight, warmth in the belly" if mode == "associated" else "The body still, nothing held")
        n = dict(name=name, key=_slug(name), archetype=arch if arch in ARCHETYPES else "", mode=mode,
                 meaning=raw.get("state") or base.get("meaning", ""), representation=rep, channels=ch,
                 glyph=raw.get("glyph") or base.get("glyph", ""), tacton=code, tacton_pulses=tacton_pulses(code),
                 frames=frames, contexts=[c.strip() for c in raw.get("contexts", []) if c.strip()][:3],
                 rules=[r.strip() for r in raw.get("rules", []) if r.strip()],
                 frame_checks=[frame_check(f, mode, raw.get("believability")) for f in frames])
        n["program"] = node_program(n, intake.get("inhale", 4), intake.get("exhale", 6))
        nodes.append(n)
    tiers = []

    def add(key):
        for t in TIER_SETS[key]:
            if t not in tiers:
                tiers.append(t)
    if any(n["mode"] == "associated" for n in nodes):
        add("associated")
    if any(n["mode"] == "observer" for n in nodes):
        add("observer")
    if set(concerns) & {"stress", "chronic_stress", "anxiety"}:
        add("calm")
    if "habits" in concerns:
        add("habits")
    if "ptsd" in concerns and any(n["mode"] == "observer" for n in nodes):
        add("memory")
    if any(n["contexts"] for n in nodes):
        add("futures")
    add("reflex")
    metrics = ["SAR", "RSF", "CRI", "ERV", "MCRAL", "PRM", "SEP", "RIF", "LAW"]
    if intake.get("author") == "therapist":
        metrics.append("MCI")
    dose = intake.get("dose", {})
    per_day, days = int(dose.get("per_day", 50)), int(dose.get("days", 4))
    schedule = [dict(phase="Massed practice", per_day=per_day, days=days, note="Self-started runs, spread over the waking day, each node in turn."),
                dict(phase="Maintenance", per_day=5, days=21, note="Spaced practice, plus every real trigger."),
                dict(phase="On triggers", per_day=0, days=0, note="Start the node when the trigger comes; device offers only with consent.")]
    safety = ["Every node runs with the person's consent; the person can stop any run at once."]
    therapist_led = "ptsd" in concerns and any(n["mode"] == "observer" for n in nodes)
    if therapist_led:
        safety.append("Observer work with trauma memories is therapist-led: a therapist is present and the screening question is answered before the session.")
    if set(concerns) & {"ptsd", "depression"}:
        safety.append("Ask the screening question before the first session: " + "Right now, are you in crisis, or having thoughts of harming yourself or not wanting to live?")
    if any(n["channels"]["O"] for n in nodes) or any(n["channels"]["G"] for n in nodes):
        safety.append("Confirm there is no allergy to the scent or taste before it is used.")
    if per_day > 20:
        safety.append("More than 20 a day are self-started; device-triggered offers stay within the safety limits (20 a day, 90 s apart).")
    if any("negation" in fc["flags"] or "low believability" in fc["flags"] for n in nodes for fc in n["frame_checks"]):
        safety.append("Some frames need rewording before practice (see the frame checks).")
    phys = intake.get("physiology", {})
    detector = None
    if phys.get("resting_hr"):
        detector = dict(resting_hr=phys["resting_hr"], rmssd=phys.get("rmssd"),
                        note="Heart-rate trigger: the detector learns this person's baseline and offers the first node when heart rate rises and variability falls without movement.")
    devs = [CHANNEL_DEVICE[c] for c in ("V", "A", "K", "O", "G") if any(n["channels"][c] for n in nodes) and devices.get(c, True)]
    if devices.get("hr"):
        devs.append("Heart-rate strap or watch: triggers and the node's body signature")
    if devices.get("eeg"):
        devs.append("EEG headset: early detection and the node's signature")
    return dict(planner=PLANNER, person=intake.get("person", "me"), author=intake.get("author", "self"),
                concerns=[CONCERNS[c] for c in concerns], symptoms=intake.get("symptoms", ""), triggers=intake.get("triggers", []),
                nodes=nodes, tiers=tiers, metrics=metrics, schedule=schedule, devices=devs, detector=detector,
                safety=safety, therapist_led=therapist_led, approved=False)


def channel_opening(runs: list[dict]) -> dict:
    """For each trigger channel: runs started by it, completed, median start latency, share started within 3 s."""
    out = {}
    for ch in ("V", "A", "K", "O", "G", "thought", "memory"):
        rs = [r for r in runs if (r.get("trigger_channel") or "").strip() == ch]
        if not rs:
            continue
        done = [r for r in rs if str(r.get("completed", "1")) in ("1", "1.0", "True", "true")]
        lats = []
        for r in done:
            try:
                lats.append(float(r.get("latency_s")))
            except (TypeError, ValueError):
                pass
        out[ch] = dict(runs=len(rs), completed=len(done), median_latency=statistics.median(lats) if lats else None,
                       within_3s=math.floor(1000.0 * sum(1 for x in lats if x <= 3.0) / len(lats) + 0.5) / 10 if lats else None)
    return out
