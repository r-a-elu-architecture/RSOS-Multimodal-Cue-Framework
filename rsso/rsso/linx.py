"""LINX — the AI interface and routing layer (spec/LINX.md).

Recovered role (archive, LINX_Historical_Reconstruction): the interface between RSOS and language models, in both
directions, with three operators — injection of the tier state into what the model sees, routing of what the
model returns, and a containment router so nothing from a model reaches a person unchecked. Here it is built as:

  understand(text)          plain language -> intake fields (concerns, nodes, states, frames, senses, contexts,
                            triggers, heart rate, dose), deterministic and offline;
  converse(state, text)     the intake conversation: one question at a time for what is still missing;
  suggest_frames(text)      rewrites of a frame that score higher on the frame check;
  model_prompt(ctx)         tier-state injection: the prompt any language model receives, with the person's plan,
                            practice summary and the reply schema;
  route(proposal, intake)   the containment router: a model's JSON proposal is checked field by field and only
                            what passes is applied; everything else is rejected with a reason;
  offer(event, plan, ...)   compressed override injection: when the body, the brain or a context signals a
                            negative state, which node to offer — never started without the person.

docs/js/linx.js is identical (tested). LINX only proposes; the planner builds, the person (or person and
therapist) approves, and the person starts every run.
"""
from __future__ import annotations

import copy
import json
import math
import re

from . import nodes as N

SCHEMA = "rsos-linx-proposal/1"
LIMITS = {"nodes": 6, "frames": 5, "contexts": 3, "triggers": 10, "notes": 5, "text": 160, "frame": 120, "sense": 80, "note": 240}

CONCERN_WORDS = [  # (concern, stems); stems match the start of a word
    ("ptsd", ["ptsd", "trauma", "flashback", "nightmare"]),
    ("depression", ["depress", "hopeless", "low mood", "emptiness"]),
    ("anxiety", ["anxi", "panic", "worr"]),
    ("chronic_stress", ["chronic stress", "burnout", "burned out", "burnt out", "exhaust"]),
    ("stress", ["stress", "tense", "tension", "overwhelm"]),
    ("habits", ["scroll", "procrastinat", "habit", "smok", "social media"]),
    ("confidence", ["confiden", "boundar", "saying no", "say no", "assert", "shy"]),
    ("focus", ["focus", "concentrat", "distract"]),
]
OBSERVER_WORDS = ["observer", "no ego", "nothing binds", "from outside", "from the outside", "detached", "watch it from"]
OWN_SYMBOLS = ["wolf", "rabbit", "hero", "owl", "phoenix", "horse", "shark", "warrior", "oak", "mountain", "ocean", "sun",
               "falcon", "hawk", "panther", "elephant", "dolphin", "tree", "river", "star"]
CONTEXT_RE = re.compile(r"\b(at|in|during|before|while|after) (work|home|meetings?|the office|school|the gym|bed|sleep|night|"
                        r"the morning|the evening|driving|exams?|presentations?|training|lunch|a conflict|conflicts)\b")
SENSE_RES = [
    ("O", re.compile(r"\b(?:smell|scent|aroma) of ([a-z][a-z ]{1,30}?)(?=[.,;!?]| and | when | while | at | in | for |$)")),
    ("O", re.compile(r"\bsmells like ([a-z][a-z ]{1,30}?)(?=[.,;!?]| and | when | while | at | in | for |$)")),
    ("G", re.compile(r"\btaste of ([a-z][a-z ]{1,30}?)(?=[.,;!?]| and | when | while | at | in | for |$)")),
    ("G", re.compile(r"\btastes like ([a-z][a-z ]{1,30}?)(?=[.,;!?]| and | when | while | at | in | for |$)")),
    ("A", re.compile(r"\b(?:sound|song|melody|music) of ([a-z][a-z ]{1,30}?)(?=[.,;!?]| and | when | while | at | in | for |$)")),
    ("A", re.compile(r"\blistening to ([a-z][a-z ]{1,30}?)(?=[.,;!?]| and | when | while | at | in | for |$)")),
    ("V", re.compile(r"\b(?:image|picture|colou?r) of ([a-z][a-z ]{1,30}?)(?=[.,;!?]| and | when | while | at | in | for |$)")),
    ("V", re.compile(r"\b(golden light|white light|blue light|a sphere of [a-z]+ light)\b")),
    ("K", re.compile(r"\bfeeling of ([a-z][a-z ]{1,30}?)(?=[.,;!?]| and | when | while | at | in | for |$)")),
]
STATE_RE = re.compile(r"\b(?:wants? to|wish(?:es)? to|would like to|needs? to) (?:feel|be|become|stay) (?:more )?([a-z][a-z ,]{1,40}?)(?=[.;!?]| when | while | at | in | so |$)")
STATE2_RE = re.compile(r"\b(?:i|she|he|they|we) (?:wants?|need|needs) (?!to |a |an |the |my |her |his |their |our |it )([a-z][a-z ]{1,40}?)(?=[.,;!?]| when | while | at | in | so | like |$)")
TRIGGER_RE = re.compile(r"\b(?:when|whenever|every time|each time|triggered by) ([a-z][a-z' ]{2,50}?)(?=[.,;!?]| i | and i |$)")
QUOTE_RE = re.compile(r"[\"“”«»]([^\"“”«»]{3,120})[\"“”«»]")
FRAME_RE = re.compile(r"\b(?:frame|statement|affirmation|i say|i tell myself)(?: is)?:? ([A-Za-z][^.!?\"“”]{3,110})", re.I)
ANTONYM = {"afraid": "calm", "scared": "steady", "anxious": "calm", "nervous": "steady", "weak": "strong", "stressed": "calm",
           "tired": "awake", "lazy": "active", "confused": "clear", "alone": "connected", "angry": "calm", "sad": "open",
           "distracted": "focused", "small": "whole", "stuck": "free", "lost": "clear", "overwhelmed": "steady", "tense": "relaxed"}
GERUND = {"seeing": "see", "focusing": "focus", "speaking": "speak", "learning": "learn", "listening": "listen", "leading": "lead",
          "thinking": "think", "remembering": "remember", "moving": "move", "breathing": "breathe", "deciding": "decide", "acting": "act",
          "holding": "hold", "standing": "stand", "staying": "stay", "saying": "say", "choosing": "choose", "keeping": "keep"}
NARROW_STRIP = re.compile(r"\b(only|just|a bit|a little|somewhat|try to|trying to)\s+", re.I)


def fmt1(x: float, sign: bool = False) -> str:
    """One decimal, rounded half up, identical in JavaScript."""
    k = int(math.floor(x * 10 + 0.5))
    a = abs(k)
    return ("+" if k >= 0 else "-") * sign + ("-" if k < 0 and not sign else "") + f"{a // 10}.{a % 10}"


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip(" ,.;")


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def _sentences(text: str) -> list[str]:
    return [s for s in re.split(r"[.!?]+\s+|\n+", text) if s.strip()]


def _concerns(low: str) -> list[str]:
    out = []
    for key, stems in CONCERN_WORDS:
        if any(re.search(r"\b" + re.escape(st), low) for st in stems):
            out.append(key)
    if "chronic_stress" in out and "stress" in out:
        out.remove("stress")
    return out


def _symbol(low: str):
    """(archetype or '', own name or '') mentioned in a sentence."""
    for a in N.ARCHETYPES:
        if a != "OBSERVER" and re.search(r"\b" + a.lower() + r"s?\b", low):
            return a, ""
    if any(w in low for w in OBSERVER_WORDS):
        return "OBSERVER", ""
    for w in OWN_SYMBOLS:
        if re.search(r"\b(?:a|an|the|my|like|as) " + w + r"\b", low):
            return "", _cap(w)
    return "", ""


def understand(text: str) -> dict:
    """Plain language -> {concerns, nodes[], triggers[], physiology, dose, author}. Every value is something the
    person said; nothing is inferred beyond the matching rules."""
    out = {"concerns": [], "nodes": [], "triggers": [], "physiology": {}, "dose": {}, "author": ""}
    low_all = text.lower()
    out["concerns"] = _concerns(low_all)
    if re.search(r"\bmy (?:client|patient)s?\b", low_all):
        out["author"] = "therapist"
    m = re.search(r"\bresting (?:heart rate|hr|pulse)(?: is| of|:)? ?(\d{2,3})", low_all)
    if m:
        out["physiology"]["resting_hr"] = int(m.group(1))
    m = re.search(r"\b(?:hrv|rmssd)(?: is| of|:)? ?(\d{1,3})", low_all)
    if m:
        out["physiology"]["rmssd"] = int(m.group(1))
    m = re.search(r"\b(\d{1,3}) (?:times|runs|repetitions) (?:a|per) day\b", low_all)
    if m:
        out["dose"]["per_day"] = int(m.group(1))
    m = re.search(r"\bfor (\d{1,2}) days\b", low_all)
    if m:
        out["dose"]["days"] = int(m.group(1))
    current = None

    def node_for(arch, own):
        for n in out["nodes"]:
            if (arch and n.get("archetype") == arch) or (own and n.get("name") == own):
                return n
        n = {"archetype": arch} if arch else {"name": own}
        out["nodes"].append(n)
        return n

    pending = {}   # what was said before any symbol, given to the first node named
    for sent in _sentences(text):
        low = sent.lower()
        arch, own = _symbol(low)
        if arch or own:
            current = node_for(arch, own)
            if pending:
                for k, v in pending.items():
                    if k in ("frames", "contexts"):
                        current.setdefault(k, [])
                        current[k] += [x for x in v if x not in current[k]]
                    else:
                        current.setdefault(k, v)
                pending = {}
        target = current if current is not None else pending
        m = STATE_RE.search(low) or STATE2_RE.search(low)
        if m:
            target.setdefault("state", _clean(m.group(1)))
        for qm in QUOTE_RE.finditer(sent):
            target.setdefault("frames", [])
            f = _clean(qm.group(1))
            if f not in target["frames"]:
                target["frames"].append(f)
        fm = FRAME_RE.search(sent)
        if fm and not QUOTE_RE.search(sent):
            target.setdefault("frames", [])
            f = _clean(fm.group(1))
            if f not in target["frames"]:
                target["frames"].append(f)
        for ch, rx in SENSE_RES:
            sm = rx.search(low)
            if sm and not target.get(ch):
                target[ch] = _cap(_clean(sm.group(1)))
        for cm in CONTEXT_RE.finditer(low):
            target.setdefault("contexts", [])
            c = _cap(cm.group(0))
            if c not in target["contexts"]:
                target["contexts"].append(c)
        for tm in TRIGGER_RE.finditer(low):
            t = _cap(_clean(tm.group(1)))
            if t and t not in out["triggers"]:
                out["triggers"].append(t)
        if arch == "OBSERVER" and current is not None:
            current["mode"] = "observer"
    if pending:   # details given without a symbol: an unnamed node (the conversation gives it to the node in question)
        n = {"archetype": ""}
        n.update(pending)
        out["nodes"].append(n)
    return out


def merge(intake: dict, patch: dict) -> dict:
    """Patch an intake: lists are extended without duplicates, nodes matched by archetype or name, empty values ignored."""
    it = copy.deepcopy(intake or {})
    for k in ("concerns", "triggers"):
        cur = it.setdefault(k, [])
        for v in patch.get(k) or []:
            if v not in cur:
                cur.append(v)
    for k in ("physiology", "dose"):
        if patch.get(k):
            it.setdefault(k, {}).update(patch[k])
    if patch.get("author"):
        it["author"] = patch["author"]
    nodes = it.setdefault("nodes", [])
    for pn in patch.get("nodes") or []:
        ref = pn.get("ref")
        tgt = None
        if isinstance(ref, int) and 0 <= ref < len(nodes):
            tgt = nodes[ref]
        else:
            for n in nodes:
                if (pn.get("archetype") and n.get("archetype") == pn.get("archetype")) or (pn.get("name") and n.get("name") == pn.get("name")):
                    tgt = n
                    break
        if tgt is None:
            tgt = {}
            nodes.append(tgt)
        for k, v in pn.items():
            if k == "ref" or v in (None, "", []):
                continue
            if k in ("frames", "contexts", "rules"):
                cur = tgt.setdefault(k, [])
                for x in v:
                    if x not in cur:
                        cur.append(x)
            else:
                tgt[k] = v
    return it


QUESTIONS = {
    "concerns": "What is happening that you want to change? For example stress at work, flashbacks, or scrolling instead of working.",
    "symbol": "Which symbol should hold the state you want: a lion for courage and boundaries, a raven for the wide view, the observer for no ego where nothing binds, or a symbol of your own?",
    "state": "What state should the {name} hold? For example calm confidence, or clear focus.",
    "frame": "What do you say to yourself in that state? A short sentence in the present tense, like “I breathe fully and completely, and I hold my ground”.",
    "senses": "What do you see, hear, smell or taste in that state? Name any you like: a colour, a song, a scent, a taste.",
    "contexts": "Where will you use the {name}? Up to three situations, for example at work, before sleep.",
    "triggers": "What usually sets off the state you want to change? For example raised voices, or opening social media.",
}
SKIP = re.compile(r"^\s*(no|none|nothing|skip|pass|not sure|don't know|dont know|-)\s*[.!]?\s*$", re.I)


def _name(n: dict) -> str:
    return n.get("name") or (n["archetype"][:1] + n["archetype"][1:].lower() if n.get("archetype") else "node")


def _next(intake: dict, asked: list[str]):
    nodes = intake.get("nodes") or []
    if not intake.get("concerns") and "concerns" not in asked:
        return "concerns", -1
    if not nodes:
        return ("symbol", -1) if "symbol" not in asked else (None, -1)
    for i, n in enumerate(nodes):
        if not n.get("state") and f"state:{i}" not in asked and not N.ARCHETYPES.get(n.get("archetype") or "", {}).get("meaning"):
            return "state", i
        if not n.get("frames") and f"frame:{i}" not in asked:
            return "frame", i
        if not any(n.get(c) for c in ("A", "O", "G")) and f"senses:{i}" not in asked:
            return "senses", i
        if not n.get("contexts") and f"contexts:{i}" not in asked:
            return "contexts", i
    if not intake.get("triggers") and "triggers" not in asked:
        return "triggers", -1
    return None, -1


def _heard(patch: dict, intake: dict) -> list[str]:
    said = []
    if patch.get("concerns"):
        said.append("what is happening: " + ", ".join(N.CONCERNS[c].lower() for c in patch["concerns"]))
    for n in patch.get("nodes") or []:
        bits = []
        if n.get("state"):
            bits.append("the state " + n["state"])
        if n.get("frames"):
            bits.append("the frame “" + n["frames"][0] + "”")
        for ch, word in (("V", "seen:"), ("A", "heard:"), ("O", "smell:"), ("G", "taste:"), ("K", "felt:")):
            if n.get(ch):
                bits.append(word + " " + n[ch].lower())
        if n.get("contexts"):
            bits.append("for " + ", ".join(c.lower() for c in n["contexts"]))
        ref = n.get("ref")
        nodes = intake.get("nodes") or []
        who = _name(nodes[ref]) if isinstance(ref, int) and 0 <= ref < len(nodes) else _name(n)
        said.append(who + (": " + "; ".join(bits) if bits else ""))
    if patch.get("triggers"):
        said.append("triggers: " + ", ".join(t.lower() for t in patch["triggers"]))
    return said


SENSE_WORDS = [("O", ["cedar", "lavender", "rose", "citrus", "sandalwood", "pine", "vanilla", "eucalyptus", "jasmine", "incense", "scent", "smell", "perfume"]),
               ("G", ["mint", "chocolate", "lemon", "honey", "ginger", "salt", "taste", "tea", "coffee"]),
               ("A", ["song", "music", "drum", "bell", "waves", "rain", "melody", "voice", "piano", "guitar", "sound", "hum"]),
               ("V", ["gold", "golden", "light", "blue", "white", "red", "green", "sun", "fire", "colour", "color", "sphere", "image"])]


def senses_from_list(raw: str) -> dict:
    """'golden light, the sound of waves, cedar' -> {V: Golden light, A: The sound of waves, O: Cedar}; unknown items are felt (K)."""
    out = {}
    for item in [x.strip() for x in re.split(r",|;| and ", raw) if x.strip()]:
        low = item.lower()
        ch = next((c for c, ws in SENSE_WORDS if any(re.search(r"\b" + w, low) for w in ws)), "K")
        if ch not in out:
            out[ch] = _cap(item[:LIMITS["sense"]])
    return out


def converse(state: dict | None, text: str) -> dict:
    """One turn of the intake conversation. state: {intake, asked, pending}. Returns {state, reply, done}."""
    st = copy.deepcopy(state or {"intake": {}, "asked": [], "pending": None})
    patch = understand(text)
    slot = st.get("pending")
    if slot and not SKIP.match(text):
        kind, _, idx = slot.partition(":")
        i = int(idx) if idx else -1
        nodes = st["intake"].get("nodes") or []
        node = nodes[i] if 0 <= i < len(nodes) else None
        raw = _clean(text)
        if kind == "concerns" and not patch["concerns"]:
            st["intake"]["symptoms"] = (st["intake"].get("symptoms", "") + " " + raw).strip()
        elif kind == "symbol" and not patch["nodes"] and raw:
            patch["nodes"] = [{"name": _cap(raw.split(" ")[-1])}]
        elif kind == "triggers" and not patch["triggers"]:
            patch["triggers"] = [_cap(c.strip()) for c in re.split(r",| and |\n", raw) if c.strip()][:5]
        elif node is not None:
            for p in patch["nodes"]:          # details without a symbol answer the question about this node
                if not p.get("archetype") and not p.get("name"):
                    p["ref"] = i
            have = lambda key: any(p.get(key) for p in patch["nodes"])
            if kind == "state" and not have("state"):
                patch["nodes"].append({"ref": i, "state": raw[:60]})
            elif kind == "frame" and not have("frames"):
                patch["nodes"].append({"ref": i, "frames": [raw[:LIMITS["frame"]]]})
            elif kind == "contexts" and not have("contexts"):
                patch["nodes"].append({"ref": i, "contexts": [_cap(c.strip()) for c in re.split(r",| and ", raw) if c.strip()][:3]})
            elif kind == "senses":           # the answer to "what do you see, hear…", item by item, in the person's words
                patch["nodes"].append(dict(senses_from_list(raw), ref=i))
    # unnamed details belong to the node in question, else to the last node; alone they need a state or a frame
    known = st["intake"].get("nodes") or []
    target = int(slot.split(":")[1]) if slot and ":" in slot else len(known) - 1
    keep = []
    for p in patch["nodes"]:
        if "ref" not in p and not p.get("archetype") and not p.get("name"):
            if known:
                p["ref"] = target
            elif not (p.get("state") or p.get("frames")):
                continue
        keep.append(p)
    patch["nodes"] = keep
    st["intake"] = merge(st["intake"], patch)
    if slot:
        st["asked"].append(slot)
    heard = _heard(patch, st["intake"])
    kind, i = _next(st["intake"], st["asked"])
    if kind is None:
        st["pending"] = None
        reply = ("Noted " + "; ".join(heard) + ". " if heard else "") + \
            "Your plan is ready on the right. Read every node; change anything in the form, or tell me more."
        return {"state": st, "reply": reply, "done": True}
    st["pending"] = kind if i < 0 else f"{kind}:{i}"
    q = QUESTIONS[kind].replace("{name}", _name(st["intake"]["nodes"][i]).lower() if i >= 0 else "node")
    reply = ("Noted " + "; ".join(heard) + ". " if heard else "") + q
    return {"state": st, "reply": reply, "done": False}


def suggest_frames(text: str, mode: str = "associated") -> list[dict]:
    """Up to three rewrites of a frame that score higher on the frame check, best first."""
    base = N.frame_check(text, mode)
    cands = []
    t = _clean(text)
    m = re.match(r"^i (?:will not|won't|am not|do not|don't|will never|never) (?:be |feel |get )?([a-z]+)(.*)$", t, re.I)
    if m and m.group(1).lower() in ANTONYM:
        rest = _clean(m.group(2))
        cands.append("I am " + ANTONYM[m.group(1).lower()] + (" " + rest if rest else "") + " and I breathe fully")
    s = NARROW_STRIP.sub("", t)
    s = re.sub(r"\bi will be\b", "I am", s, flags=re.I)
    s = re.sub(r"\bi will (?!not\b|never\b)", "I ", s, flags=re.I)
    gm = re.search(r"\bi am good at ([a-z]+ing)\b", s, re.I)
    if gm and gm.group(1).lower() in GERUND:
        s = s[:gm.start()] + "I " + GERUND[gm.group(1).lower()] + s[gm.end():]
        s = re.sub(r"\bsee things\b", "see broadly and clearly", s, flags=re.I)
    else:
        s = re.sub(r"\bi am good at\b", "I am skilled at", s, flags=re.I)
    if s != t:
        cands.append(s)
    if re.search(r"\bsee\b", s, re.I) and not re.search(r"\b(broadly|clearly|whole|from above)\b", s, re.I):
        cands.append(re.sub(r"\bsee\b", "see broadly", s, count=1, flags=re.I))
    chk = N.frame_check(s, mode)
    if "trait only" in chk["flags"]:
        cands.append(s.rstrip(" .") + ", and I breathe fully and completely")
    if mode == "associated" and chk["scope"] == "neutral" and "trait only" not in chk["flags"]:
        cands.append(s.rstrip(" .") + ", fully and completely")
    out, seen = [], {text.strip().lower()}
    for c in cands:
        c = _cap(_clean(c))
        if c.lower() in seen:
            continue
        seen.add(c.lower())
        fc = N.frame_check(c, mode)
        if "negation" in fc["flags"] or "future" in fc["flags"]:
            continue
        if fc["score"] > base["score"] or (fc["score"] == base["score"] and len(fc["broad"]) > len(base["broad"])):
            out.append({"text": c, "score": fc["score"], "scope": fc["scope"], "kind": fc["kind"]})
    out.sort(key=lambda x: -x["score"])
    return out[:3]


def model_prompt(ctx: dict) -> str:
    """Tier-state injection: everything a language model needs to propose improvements, and the reply schema."""
    it, plan = ctx.get("intake") or {}, ctx.get("plan") or {}
    runs = ctx.get("runs") or []
    lines = ["You are LINX, the AI layer of RSOS (https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/).",
             "RSOS installs resourceful states as nodes: a state held as one unit, with cues on every sense (V seen, A heard, K felt, O smell, G taste), "
             "a vibration code, a glyph, a mode (associated: in the body; observer: nothing binds, only observed) and the mental frame said in that state.",
             "Rules: propose only; the person approves and starts every run. Do not diagnose. Frames are short, present tense, about what the person does "
             "(I breathe, I see), broad rather than narrow, and believable. Use the person's own words where you can. Point out anything a therapist should review.",
             "", "Current state of this person's system:"]
    if it.get("concerns"):
        lines.append("- What is happening: " + ", ".join(N.CONCERNS.get(c, c) for c in it["concerns"]))
    if it.get("triggers"):
        lines.append("- Triggers: " + "; ".join(it["triggers"]))
    for i, n in enumerate(plan.get("nodes") or it.get("nodes") or []):
        frames = n.get("frames") or []
        ch = n.get("channels") or {k: n.get(k) for k in "VAKOG" if n.get(k)}
        lines.append(f"- Node {i} {n.get('name') or n.get('archetype') or 'own'} ({n.get('mode') or 'associated'}): state {n.get('meaning') or n.get('state') or '-'}; "
                     f"frames {json.dumps(frames, ensure_ascii=False, separators=(",", ":"))}; cues {json.dumps({k: v for k, v in ch.items() if v}, ensure_ascii=False, separators=(",", ":"))}; "
                     f"contexts {json.dumps(n.get('contexts') or [], ensure_ascii=False, separators=(",", ":"))}")
    if plan.get("tiers"):
        lines.append("- Ledger tiers in use: " + ", ".join(plan["tiers"]))
    if runs:
        by = {}
        for r in runs:
            if r.get("sud_before") not in (None, "") and r.get("sud_after") not in (None, ""):
                by.setdefault(r.get("protocol") or "?", []).append(float(r["sud_after"]) - float(r["sud_before"]))
        lines.append(f"- Practice so far: {len(runs)} runs" + "".join(
            f"; {p}: {len(v)} rated, mean change in distress {fmt1(sum(v) / len(v), True)}" for p, v in sorted(by.items())))
    lines += ["", "Reply with JSON only, in this form (leave out anything you do not change):",
              json.dumps({"schema": SCHEMA, "nodes": [{"ref": "index of an existing node, or omit for a new node", "name": "", "archetype": "LION|RAVEN|EAGLE|LEOPARD|TIGER|BEAR|DRAGON|OBSERVER|",
                                                       "mode": "associated|observer", "state": "", "frames": [""], "V": "", "A": "", "K": "", "O": "", "G": "", "contexts": [""]}],
                          "concerns": list(N.CONCERNS), "triggers": [""], "notes_for_therapist": [""]}, ensure_ascii=False, separators=(",", ":"))]
    return "\n".join(lines) + "\n"


UNSAFE = re.compile(r"\b(kill|die|dying|suicid\w*|self-harm|harm myself|hurt myself|starve|purge|worthless|hate myself)\b", re.I)
ACTIONS = re.compile(r"^(auto_?)?(start|run|execute|play|fire|trigger)(_now)?$|_now$")   # field names that would act instead of propose


def route(proposal, intake: dict) -> dict:
    """Containment router: check a model's proposal and apply only what passes. Returns {intake, applied, rejected}."""
    rejected, applied = [], []
    if not isinstance(proposal, dict):
        return {"intake": copy.deepcopy(intake or {}), "applied": [], "rejected": [{"path": "", "reason": "not a JSON object"}]}
    if proposal.get("schema") != SCHEMA:
        rejected.append({"path": "schema", "reason": f"expected {SCHEMA}"})
        return {"intake": copy.deepcopy(intake or {}), "applied": [], "rejected": rejected}
    for k in sorted(proposal):
        if ACTIONS.search(k.lower()):
            rejected.append({"path": k, "reason": "LINX may only propose: the person starts every run"})
        elif k not in ("schema", "nodes", "concerns", "triggers", "notes_for_therapist"):
            rejected.append({"path": k, "reason": "unknown field"})
    patch = {"concerns": [], "triggers": [], "nodes": []}

    def text_ok(path, v, limit):
        if not isinstance(v, str) or not v.strip():
            return None
        if len(v) > limit:
            rejected.append({"path": path, "reason": f"longer than {limit} characters"})
            return None
        if UNSAFE.search(v):
            rejected.append({"path": path, "reason": "unsafe wording: held for the person and their therapist"})
            return None
        return v.strip()

    for c in proposal.get("concerns") or []:
        if c in N.CONCERNS:
            patch["concerns"].append(c)
        else:
            rejected.append({"path": "concerns", "reason": f"unknown concern {c!r}"})
    for j, t in enumerate((proposal.get("triggers") or [])[:LIMITS["triggers"]]):
        v = text_ok(f"triggers.{j}", t, LIMITS["text"])
        if v:
            patch["triggers"].append(v)
    nodes = (intake or {}).get("nodes") or []
    for j, pn in enumerate((proposal.get("nodes") or [])[:LIMITS["nodes"]]):
        p = f"nodes.{j}"
        if not isinstance(pn, dict):
            rejected.append({"path": p, "reason": "not an object"})
            continue
        out = {}
        ref = pn.get("ref")
        if isinstance(ref, int) and not isinstance(ref, bool):
            if 0 <= ref < len(nodes):
                out["ref"] = ref
            else:
                rejected.append({"path": p + ".ref", "reason": "no such node"})
                continue
        for k in sorted(pn):
            if ACTIONS.search(k.lower()):
                rejected.append({"path": f"{p}.{k}", "reason": "LINX may only propose: the person starts every run"})
            elif k not in ("ref", "name", "archetype", "mode", "state", "frames", "V", "A", "K", "O", "G", "contexts"):
                rejected.append({"path": f"{p}.{k}", "reason": "unknown field"})
        arch = pn.get("archetype") or ""
        if arch:
            if arch in N.ARCHETYPES:
                out["archetype"] = arch
            else:
                rejected.append({"path": p + ".archetype", "reason": f"unknown archetype {arch!r}"})
        mode = pn.get("mode")
        if mode:
            if mode in ("associated", "observer"):
                out["mode"] = mode
            else:
                rejected.append({"path": p + ".mode", "reason": "mode is associated or observer"})
        for k, lim in (("name", 40), ("state", 60), ("V", LIMITS["sense"]), ("A", LIMITS["sense"]), ("K", LIMITS["sense"]),
                       ("O", LIMITS["sense"]), ("G", LIMITS["sense"])):
            v = text_ok(f"{p}.{k}", pn.get(k), lim)
            if v:
                out[k] = v
        node_mode = out.get("mode") or (nodes[out["ref"]].get("mode") if "ref" in out else None) or N.ARCHETYPES.get(arch, {}).get("mode", "associated")
        frames = []
        for q, f in enumerate((pn.get("frames") or [])[:LIMITS["frames"]]):
            v = text_ok(f"{p}.frames.{q}", f, LIMITS["frame"])
            if not v:
                continue
            fc = N.frame_check(v, node_mode)
            if fc["score"] < 70 or "negation" in fc["flags"]:
                rejected.append({"path": f"{p}.frames.{q}", "reason": "frame check " + str(fc["score"]) + "/100: " + ", ".join(fc["flags"])})
                continue
            frames.append(v)
        if frames:
            out["frames"] = frames
        ctx = [v for q, c in enumerate((pn.get("contexts") or [])[:LIMITS["contexts"]]) if (v := text_ok(f"{p}.contexts.{q}", c, LIMITS["text"]))]
        if ctx:
            out["contexts"] = ctx
        if len(out) > (1 if "ref" in out else 0):
            patch["nodes"].append(out)
            applied.append(f"{p}: " + ", ".join(k for k in out if k != "ref"))
    if patch["concerns"]:
        applied.append("concerns: " + ", ".join(patch["concerns"]))
    if patch["triggers"]:
        applied.append(f"triggers: {len(patch['triggers'])}")
    notes = [v for q, n in enumerate((proposal.get("notes_for_therapist") or [])[:LIMITS["notes"]]) if (v := text_ok(f"notes_for_therapist.{q}", n, LIMITS["note"]))]
    res = merge(intake or {}, patch)
    if notes:
        res["notes_for_therapist"] = (res.get("notes_for_therapist") or []) + notes
        applied.append(f"notes for the therapist: {len(notes)}")
    return {"intake": res, "applied": applied, "rejected": rejected}


def _words(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]+", (s or "").lower()) if len(w) > 2 and w not in {"the", "and", "with", "for", "from", "when", "into"}}


def offer(event: dict, plan: dict, runs: list[dict] | None = None, gov: dict | None = None, now: float = 0.0) -> dict:
    """Which node to offer for an event {source: hr|eeg|context|memory, text}. gov: {last_start, starts} (seconds).
    Returns {node, name, protocol, reason} or {node: None, reason}."""
    if not plan or not plan.get("nodes"):
        return {"node": None, "reason": "no node plan"}
    if not plan.get("approved"):
        return {"node": None, "reason": "the plan is not approved yet"}
    gov = gov or {}
    starts = [s for s in gov.get("starts") or [] if now - s < 86400]
    if gov.get("last_start") is not None and now - gov["last_start"] < 90:
        return {"node": None, "reason": "wait: at least 90 s between runs"}
    if sum(1 for s in starts if now - s < 3600) >= 6:
        return {"node": None, "reason": "limit: 6 device-offered runs an hour"}
    if len(starts) >= 20:
        return {"node": None, "reason": "limit: 20 device-offered runs a day"}
    src, ev_words = event.get("source") or "hr", _words(event.get("text") or "")
    trig_words = set()
    for t in (plan.get("intake") or {}).get("triggers") or plan.get("triggers") or []:
        trig_words |= _words(t)
    best, best_score, why = None, None, ""
    for i, n in enumerate(plan["nodes"]):
        score, reasons = 0.0, []
        ctx = set()
        for c in n.get("contexts") or []:
            ctx |= _words(c)
        hit = sorted(ev_words & ctx)
        if hit:
            score += 2 * len(hit)
            reasons.append("its context matches " + ", ".join(hit))
        if ev_words & trig_words and n.get("mode") == "associated":
            score += 1
            reasons.append("a known trigger")
        if src == "memory" and n.get("mode") == "observer":
            score += 3
            reasons.append("a memory: observed, not relived")
        if src in ("hr", "eeg") and n.get("mode") == "associated":
            score += 1
            reasons.append("the body signals stress" if src == "hr" else "the brain signals arousal")
        proto = "node_" + str(n.get("key") or "").lower()
        ch = [float(r["sud_after"]) - float(r["sud_before"]) for r in runs or []
              if r.get("protocol") == proto and r.get("sud_before") not in (None, "") and r.get("sud_after") not in (None, "")]
        if len(ch) >= 3:
            mean = sum(ch) / len(ch)
            score += max(-2.0, min(2.0, -mean / 2))
            if mean < 0:
                reasons.append(f"it lowered your distress by {fmt1(-mean)} on average")
        if best_score is None or score > best_score:
            best, best_score, why = i, score, "; ".join(reasons)
    n = plan["nodes"][best]
    return {"node": best, "name": n.get("name"), "protocol": "node_" + str(n.get("key") or "").lower(), "reason": why or "your first node"}
