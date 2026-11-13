"""THERA and LINX extensions: the therapist's copilot and the session tools around it (spec/COPILOT.md).

  matrix      the therapist's decision matrix: a central meaning with three trigger cues, each with its words, its
              response and its code; the copilot reads the live transcript and highlights the branch that matches;
              agreement between the copilot and the therapist is measured (Cohen's kappa) with response times
  levels      which level a sentence comes from (environment, behaviour, skills, beliefs and values, identity,
              mission) and the five-step operator chain: detect, analyse, modify (a question from the level above),
              output (through the safety checks) and future-pace
  types       typologies from speech as plug-ins (sensory words, time orientation); profiling another person needs
              their consent; agreement with a questionnaire
  craving     context triggers (an app opening, arriving at a place, a time) that offer the craving protocol, and
              cue-reactivity over months
  core        Core Transformation asked one question at a time, ending in a core state with its own code
  rescripting re-living an event with a symbol and light, as an RSX program
  timeline    life events as ordered nodes with glyphs, and the share recalled as specific events
  overrides   overrides per day, the share of events turned around, start latency (also just after waking), OXQ,
              monthly success, and DOL-9, the 90-second daily override loop
  perceptual  unusual perceptual events always go to escalation, never to automatic firing
  contexts    the four-day acquisition block, contexts recognised from speech, and the timed burst
  setting     warmth, music and imagery logged with sessions, and whether the setting matters

A seeded simulation with known answers checks the measures. docs/js/copilot.js is identical (tested).
"""
from __future__ import annotations

import math
import re
import sys

from . import peak as P
from . import trial as T

UNSAFE = re.compile(r"\b(kill|die|dying|suicid\w*|self-harm|harm myself|hurt myself|starve|purge|worthless|hate myself)\b", re.I)
WORD = re.compile(r"[a-z']+")


def r1(x):
    return None if x is None else math.floor(x * 10 + 0.5) / 10


def r2(x):
    return None if x is None else math.floor(x * 100 + 0.5) / 100


def _v(x):
    return int(x) if isinstance(x, float) and x.is_integer() else x


def _mean(xs):
    return sum(xs) / len(xs)


def _median(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def _ci_diff(a, b):
    d = _mean(a) - _mean(b)
    if len(a) < 2 or len(b) < 2:
        return d, None, None
    va, vb = T._var(a) / len(a), T._var(b) / len(b)
    se = math.sqrt(va + vb)
    if se == 0:
        return d, d, d
    den = va * va / (len(a) - 1) + vb * vb / (len(b) - 1)
    df = max(1, int(math.floor((va + vb) * (va + vb) / den))) if den > 0 else len(a) + len(b) - 2
    h = T.tcrit(df) * se
    return d, d - h, d + h


def _slope(xs, ys):
    n = len(xs)
    mx, my = _mean(xs), _mean(ys)
    sxx = sum((x - mx) * (x - mx) for x in xs)
    if sxx == 0 or n < 3:
        return 0.0, None, None
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    res = sum((y - my - b * (x - mx)) * (y - my - b * (x - mx)) for x, y in zip(xs, ys))
    se = math.sqrt(res / (n - 2) / sxx)
    t = T.tcrit(n - 2)
    return b, b - t * se, b + t * se


def words(text: str) -> list:
    return WORD.findall((text or "").lower())


def hits(text: str, lexicon: list) -> list:
    """Entries of the lexicon found in the text. An entry ending in * matches the start of a word; an entry with a
    space matches the phrase."""
    ws = words(text)
    joined = " " + " ".join(ws) + " "
    out = []
    for e in lexicon:
        if e.endswith("*"):
            if any(w.startswith(e[:-1]) for w in ws):
                out.append(e)
        elif " " in e:
            if (" " + e + " ") in joined:
                out.append(e)
        elif e in ws:
            out.append(e)
    return out


def kappa(pairs: list) -> dict:
    """Cohen's kappa for pairs of labels."""
    n = len(pairs)
    if n == 0:
        return {"n": 0, "agree": None, "kappa": None}
    cats = sorted(set(a for a, _ in pairs) | set(b for _, b in pairs))
    po = sum(1 for a, b in pairs if a == b) / n
    pe = sum((sum(1 for a, _ in pairs if a == c) / n) * (sum(1 for _, b in pairs if b == c) / n) for c in cats)
    k = (po - pe) / (1 - pe) if pe < 1 else 1.0
    return {"n": n, "agree": _v(r1(po * 100)), "kappa": _v(r2(k))}


# ---------------------------------------------------------------- the decision matrix and the copilot (item 14)

def make_matrix(id_: str, center: str, branches: list) -> dict:
    if len(branches) != 3:
        raise ValueError("a decision matrix has three branches")
    return {"schema": "rsos-matrix/1", "id": id_, "center": center,
            "branches": [{"id": b["id"], "cue": b["cue"], "words": list(b["words"]), "response": b["response"], "code": b.get("code", "")} for b in branches]}


EXAMPLE_MATRIX = {"schema": "rsos-matrix/1", "id": "safety", "center": "Safety is here, now",
                  "branches": [
                      {"id": "blame", "cue": "Self-blame", "words": ["my fault", "blame*", "should have", "stupid", "idiot", "failed", "ruin*"],
                       "response": "Slow down. Name one thing you did that kept you or someone else safe.", "code": "..-"},
                      {"id": "flood", "cue": "Overwhelm", "words": ["too much", "overwhelm*", "can't cope", "cannot cope", "everything", "drown*", "panic*"],
                       "response": "Feet on the floor. Breathe out longer than in. Name three things you can see.", "code": "-.-"},
                      {"id": "withdraw", "cue": "Withdrawal", "words": ["give up", "alone", "no point", "leave", "hide", "nothing matters", "shut down"],
                       "response": "Stay with me for one breath. What is one small thing that still matters today?", "code": "--."}]}


def copilot_match(matrix: dict, text: str) -> dict:
    """The branch whose words appear most in the utterance (ties to the first), or none."""
    best, score, found = None, 0, []
    for b in matrix["branches"]:
        h = hits(text, b["words"])
        if len(h) > score:
            best, score, found = b["id"], len(h), h
    return {"branch": best, "score": score, "words": found, "unsafe": bool(UNSAFE.search(text or ""))}


def add_utterance(log: list, t, text: str, matrix: dict) -> dict:
    m = copilot_match(matrix, text)
    u = {"t": t, "text": text, "copilot": m["branch"], "words": m["words"], "unsafe": m["unsafe"], "therapist": None, "therapist_t": None}
    log.append(u)
    return u


def mark(log: list, i: int, branch, t) -> dict:
    """The therapist's own choice for utterance i: a branch id, or "none"."""
    log[i]["therapist"] = branch
    log[i]["therapist_t"] = t
    return log[i]


def agreement(log: list) -> dict:
    marked = [u for u in log if u["therapist"] is not None]
    k = kappa([(u["copilot"] or "none", u["therapist"]) for u in marked])
    lat = [u["therapist_t"] - u["t"] for u in marked if u["therapist"] != "none" and u["therapist_t"] is not None]
    miss = sum(1 for u in marked if u["copilot"] is None and u["therapist"] != "none")
    extra = sum(1 for u in marked if u["copilot"] is not None and u["therapist"] == "none")
    unsafe = sum(1 for u in log if u["unsafe"])
    say = ("Mark what you chose for each line to measure agreement." if not marked else
           f"Copilot and therapist agreed on {k['agree']}% of {k['n']} lines (kappa {k['kappa']}). The therapist answered in {_v(r1(_median(lat)))} s (median)."
           if lat else f"Copilot and therapist agreed on {k['agree']}% of {k['n']} lines (kappa {k['kappa']}).")
    if unsafe:
        say += f" {unsafe} line{'s' if unsafe != 1 else ''} held for the therapist: unsafe wording."
    return {"lines": len(log), "marked": len(marked), "agree": k["agree"], "kappa": k["kappa"], "median_s": _v(r1(_median(lat))) if lat else None,
            "copilot_missed": miss, "copilot_extra": extra, "unsafe": unsafe, "say": say}


# ---------------------------------------------------------------- levels and the five-step chain (item 13)

LEVELS = ("environment", "behaviour", "skills", "beliefs", "identity", "mission")
LEVEL_NAMES = {"environment": "Environment", "behaviour": "Behaviour", "skills": "Skills", "beliefs": "Beliefs and values",
               "identity": "Identity", "mission": "Mission"}
LEVEL_WORDS = {
    "mission": ["for others", "for my family", "my purpose", "purpose", "meaning", "the world", "legacy", "bigger than", "serve*", "mission", "calling", "for the people"],
    "identity": ["i am", "i'm a", "i'm an", "i'm the", "kind of person", "who i am", "myself as", "i'm not a", "i am not", "loser", "failure", "type of person"],
    "beliefs": ["i believe", "believe", "should", "must", "have to", "important", "matters", "because", "always", "never", "it's wrong", "it's right", "value*", "deserve*"],
    "skills": ["i can", "i can't", "i cannot", "able to", "unable", "know how", "don't know how", "learn*", "skill*", "good at", "bad at", "capable"],
    "behaviour": ["i did", "i do", "i went", "i said", "i shout*", "i ran", "i keep", "i stopped", "i started", "i yell*", "i drink", "i scroll*", "i eat", "i smoke"],
    "environment": ["at work", "at home", "in the office", "here", "there", "the room", "the city", "the weather", "the noise", "the traffic", "when he", "when she", "they", "people around"],
}
ORDER = ("mission", "identity", "beliefs", "skills", "behaviour", "environment")
ABOVE = {"environment": "behaviour", "behaviour": "skills", "skills": "beliefs", "beliefs": "identity", "identity": "mission", "mission": "mission"}
QUESTION = {
    "environment": "In that place, what is one thing you can do differently?",
    "behaviour": "What would you need to be able to do, so that this changes?",
    "skills": "What do you believe about yourself when you can do that?",
    "beliefs": "Who are you, when that belief is true for you?",
    "identity": "What is that for, beyond you?",
    "mission": "How will that show up tomorrow, in one small act?",
}


def level_of(text: str) -> dict:
    """The level a sentence speaks from: the highest level whose words it uses (the person's most general claim
    leads), or none."""
    scores = {l: hits(text, LEVEL_WORDS[l]) for l in LEVELS}
    for l in ORDER:
        if scores[l]:
            return {"level": l, "words": scores[l]}
    return {"level": None, "words": []}


def chain(text: str) -> dict:
    """The five steps for one sentence. An unsafe sentence is held for the therapist: no question is generated."""
    if UNSAFE.search(text or ""):
        return {"steps": [{"step": "detect", "say": "Unsafe wording: held for the therapist. Follow the escalation plan; nothing is generated."}],
                "held": True, "level": None}
    d = level_of(text)
    lv = d["level"] or "behaviour"
    up = ABOVE[lv]
    q = QUESTION[lv]
    return {"held": False, "level": d["level"], "steps": [
        {"step": "detect", "say": "Speaking from " + LEVEL_NAMES[lv].lower() + (" (" + ", ".join(d["words"]) + ")" if d["words"] else " (no clear words; assumed)") + "."},
        {"step": "analyse", "say": "Work one level above: " + LEVEL_NAMES[up].lower() + "."},
        {"step": "modify", "say": q},
        {"step": "output", "say": "Ask it slowly, in the client's own words; the router and the safety layer check anything a model adds."},
        {"step": "future", "say": "Then: picture the next time this happens, and the answer already in place."}]}


LEVEL_TEST = [
    ("The traffic on the way to work makes me tense.", "environment"), ("At work the noise is constant.", "environment"),
    ("When he raises his voice I freeze.", "environment"), ("The room is too small and too hot.", "environment"),
    ("There is never a quiet corner at home.", "environment"), ("People around me are always rushing.", "environment"),
    ("The weather gets me down every November.", "environment"), ("The city is loud at night.", "environment"),
    ("I shouted at my son this morning.", "behaviour"), ("I scroll my phone until two in the morning.", "behaviour"),
    ("I keep checking my email.", "behaviour"), ("I drink too much coffee before meetings.", "behaviour"),
    ("I went home early again.", "behaviour"), ("I stopped going to the gym.", "behaviour"),
    ("I said yes when I wanted to say no.", "behaviour"), ("I eat when I am bored.", "behaviour"),
    ("I can't speak in front of a group.", "skills"), ("I don't know how to calm down.", "skills"),
    ("I'm good at planning but bad at finishing.", "skills"), ("I'm unable to sleep after a fight.", "skills"),
    ("I want to learn to say no.", "skills"), ("I can focus for ten minutes at most.", "skills"),
    ("I never learned to swim.", "skills"), ("I'm not capable of keeping a routine.", "skills"),
    ("I believe people will leave if I am honest.", "beliefs"), ("You should never show weakness.", "beliefs"),
    ("Family matters more than work.", "beliefs"), ("I have to be perfect or it doesn't count.", "beliefs"),
    ("It's wrong to ask for help.", "beliefs"), ("Honesty is important to me.", "beliefs"),
    ("I don't deserve a break.", "beliefs"), ("Things always go wrong because of me.", "beliefs"),
    ("I am a failure.", "identity"), ("I'm not the kind of person who speaks up.", "identity"),
    ("I am a calm person underneath.", "identity"), ("I see myself as a fighter.", "identity"),
    ("I'm an anxious type of person.", "identity"), ("Who I am changed after the accident.", "identity"),
    ("I am not a leader.", "identity"), ("I'm a loser at heart.", "identity"),
    ("My purpose is to protect my family.", "mission"), ("I want my life to mean something for others.", "mission"),
    ("It's bigger than me; I do it for my children.", "mission"), ("I want to serve the people in my town.", "mission"),
    ("My work should leave a legacy.", "mission"), ("I feel a calling to teach.", "mission"),
    ("I am here to make the world a little kinder.", "mission"), ("Meaning matters more to me than money.", "mission"),
]


def level_accuracy() -> dict:
    """Accuracy of the level classifier on the built-in set of 48 example sentences (8 per level)."""
    rows = [(level_of(t)["level"], lv) for t, lv in LEVEL_TEST]
    by = {l: _v(r1(sum(1 for p, t in rows if t == l and p == l) / sum(1 for _, t in rows if t == l) * 100)) for l in LEVELS}
    return {"n": len(rows), "accuracy": _v(r1(sum(1 for p, t in rows if p == t) / len(rows) * 100)), "by_level": by,
            "kappa": kappa([(p or "none", t) for p, t in rows])["kappa"]}


# ---------------------------------------------------------------- typologies from speech, as plug-ins (item 12)

PLUGINS = {
    "senses": {"title": "Sensory words", "types": {
        "visual": ["see*", "look*", "picture*", "clear*", "bright*", "view*", "focus*", "show*", "imagine*", "colour*", "watch*", "vision*"],
        "auditory": ["hear*", "sound*", "listen*", "tell*", "said", "say*", "loud*", "quiet*", "voice*", "tune*", "ring*", "talk*"],
        "kinesthetic": ["feel*", "felt", "touch*", "grasp*", "heavy", "warm*", "solid*", "pressure*", "smooth*", "handle*", "tight*", "hold*"]}},
    "time": {"title": "Time orientation", "types": {
        "past": ["was", "were", "used to", "back then", "remember*", "before", "had", "ago", "last year", "childhood"],
        "present": ["now", "today", "is", "am", "right now", "currently", "these days", "this week", "at the moment"],
        "future": ["will", "going to", "plan*", "tomorrow", "next", "soon", "hope*", "someday", "future", "later"]}},
}


def _count(text: str, lex: list) -> int:
    """Words of the text that match the lexicon (each word once), plus phrase occurrences."""
    ws = words(text)
    joined = " " + " ".join(ws) + " "
    singles = [e for e in lex if " " not in e]
    n = sum(1 for w in ws if any((w.startswith(e[:-1]) if e.endswith("*") else w == e) for e in singles))
    return n + sum(joined.count(" " + e + " ") for e in lex if " " in e)


def profile(plugin: str, text: str, subject="self", consent=False) -> dict:
    """Counts each type's words in the text. Profiling another person needs their recorded consent."""
    if subject != "self" and not consent:
        return {"refused": True, "say": "Profiling another person's speech needs their consent, recorded first."}
    pl = PLUGINS[plugin]
    counts = {t: _count(text, lex) for t, lex in pl["types"].items()}
    total = sum(counts.values())
    ranked = sorted(pl["types"], key=lambda t: (-counts[t], list(pl["types"]).index(t)))
    shares = {t: _v(r1(counts[t] / total * 100)) if total else None for t in pl["types"]}
    lead = counts[ranked[0]] - counts[ranked[1]]
    top = ranked[0] if total >= 10 and lead >= max(3.0, 2 * math.sqrt(total)) else None
    say = (f"Too few {pl['title'].lower()} so far ({total}); ten or more give a profile." if total < 10 else
           f"Leans {top} ({shares[top]}% of {total} words)." if top else f"No clear lean yet ({total} words).")
    return {"refused": False, "plugin": plugin, "counts": counts, "total": total, "shares": shares, "top": top, "say": say}


# ---------------------------------------------------------------- craving: context triggers and cue-reactivity (item 8)

def context_trigger(triggers: list, event: dict):
    """triggers: [{id, kind: app|place|time, match}]; event: {kind, value}. Returns the trigger that matches, or None.
    A match only offers the craving protocol; the person starts it (the autonomy gate decides anything more)."""
    for t in triggers:
        if t["kind"] != event.get("kind"):
            continue
        v = str(event.get("value", "")).lower()
        if t["kind"] == "time":
            a, b = t["match"].split("-")
            if a <= v < b:
                return t
        elif t["match"].lower() in v:
            return t
    return None


def cue_reactivity(log: list) -> dict:
    """log: [{ts, craving (0-10)}] at each cue exposure. The change per month with an interval."""
    rows = sorted((r for r in log if r.get("craving") is not None), key=lambda r: r["ts"])
    if len(rows) < 6 or rows[-1]["ts"] - rows[0]["ts"] < 14 * 86400:
        return {"n": len(rows), "per_month": None, "lo": None, "hi": None, "verdict": "too_few",
                "say": "Rate the craving at six or more cue exposures over two weeks or more to see a trend."}
    b, lo, hi = _slope([(r["ts"] - rows[0]["ts"]) / 86400 / 30 for r in rows], [r["craving"] for r in rows])
    v = "falling" if hi < 0 else "rising" if lo > 0 else "no_clear_change"
    say = {"falling": "Cue-reactivity is falling", "rising": "Cue-reactivity is rising", "no_clear_change": "No clear change in cue-reactivity yet"}[v]
    return {"n": len(rows), "per_month": _v(r1(b)), "lo": _v(r1(lo)), "hi": _v(r1(hi)), "verdict": v,
            "say": say + f": {_v(r1(b))} points a month [{_v(r1(lo))}, {_v(r1(hi))}]."}


# ---------------------------------------------------------------- Core Transformation (item 20)

CORE_WORDS = ["peace*", "oneness", "one with", "being", "love", "loved", "okay-ness", "ok-ness", "whole*", "free*", "home", "still*", "light"]
CT_FIRST = "Notice the part of you that brings {state}. Thank it. What does it want for you?"
CT_NEXT = "And if you have that, fully and completely, what do you want through having it, that is even more important?"


def ct_start(state: str) -> dict:
    return {"state": state, "chain": [], "done": False, "question": CT_FIRST.replace("{state}", state or "this state")}


def ct_answer(ct: dict, text: str) -> dict:
    """Add the answer. The chain ends at a core state (peace, oneness, being, love, wholeness…) or after seven steps."""
    if ct["done"]:
        return ct
    if UNSAFE.search(text or ""):
        ct["done"], ct["held"] = True, True
        ct["question"] = "Stop here: this needs the therapist. Follow the escalation plan."
        return ct
    ct["chain"].append(text.strip())
    if hits(text, CORE_WORDS) or len(ct["chain"]) >= 7:
        ct["done"] = True
        ct["question"] = "Core state: " + ct["chain"][-1] + ". Let it flow back through every step, in reverse."
    else:
        ct["question"] = CT_NEXT
    return ct


def _q(s):
    return '"' + str(s).replace('"', "'").replace("\n", " ") + '"'


def ct_rsx(ct: dict, code="..--") -> str:
    """The completed chain as an RSX program: the core state first, then flowing back through each outcome to the old state."""
    core = ct["chain"][-1] if ct["chain"] else "the core state"
    L = ["PROTOCOL core_transformation \"Core Transformation\"", "VERSION 1.0", "SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4",
         "BREATH inhale=4s exhale=6s", "", "TIER 1 CORE {", f"  V {_q('a light that is ' + core)}", f"  A {_q('I have ' + core + ' already')}",
         f"  K {_q('feel ' + core + ' through the whole body')}", f"  TACTON {_q(code)}", "}", "",
         "PHASE core breath=inhale {", "  ACTIVATE CORE", "}"]
    for k, step in enumerate(reversed(ct["chain"][:-1])):
        L += [f"PHASE back{k + 1} breath=exhale {{", f"  FEEL {_q('having ' + core + ' already, ' + step + ' comes easily')}", "}"]
    L += ["PHASE old breath=exhale {", f"  FEEL {_q('let ' + core + ' flow into where ' + (ct['state'] or 'the old state') + ' used to be')}", "}",
          "PHASE seal breath=inhale {", "  ACTIVATE CORE", "  MARK \"core\"", "}"]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- re-living an event with a symbol and light (item 17)

def rescript_rsx(event: str, symbol: str, behaviour: str, light="radiant gold") -> str:
    """Imagery rescripting with the person's symbol: settle, see the event briefly from a distance, the symbol's light
    fills the scene, rehearse the new behaviour, future-pace. Timed so the distress can be rated before and after."""
    L = ["PROTOCOL rescript \"Re-living with the symbol\"", "VERSION 1.0", "SAFETY max_per_hour=2 max_per_day=4 refractory=90s haptic_max=0.4",
         "BREATH inhale=4s exhale=6s", "", "TIER 1 SYMBOL {", f"  GLYPH {_q(symbol)}", f"  V {_q(light + ' light from ' + symbol)}",
         "  A \"I am here now, and I am safe\"", "  K \"warmth spreading through the chest\"", "}", "",
         "PHASE settle dur=20s {", "  FEEL \"Feet on the floor, breathe out slowly\"", "}",
         "PHASE distance dur=15s {", f"  SEE {_q('the event, briefly, like a small picture far away: ' + event)}", "}",
         "PHASE light breath=inhale {", "  ACTIVATE SYMBOL", f"  SEE {_q(light + ' light fills the whole scene')}", "}",
         "PHASE rehearse dur=30s {", f"  SEE {_q('you in the scene, doing what you would do now: ' + behaviour)}", "  WAIT 10s",
         "  FEEL \"notice the body as you act\"", "}",
         "PHASE future dur=12s {", f"  SEE {_q('the next similar moment, and you, ' + behaviour)}", "}",
         "PHASE close breath=exhale {", "  SAY \"Back in the room. Eyes open.\"", "  MARK \"rescripted\"", "}"]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- the life timeline (item 47)

def timeline_report(events: list) -> dict:
    """events: [{year, title, glyph, specific: bool}]. Ordered nodes and the share recalled as specific events (one
    day, a place, a moment), the measure memory specificity training aims to raise."""
    ev = sorted(events, key=lambda e: (e.get("year", 0), e.get("title", "")))
    spec = sum(1 for e in ev if e.get("specific"))
    decades = {}
    for e in ev:
        d = int(e.get("year", 0)) // 10 * 10
        decades[str(d)] = decades.get(str(d), 0) + 1
    return {"nodes": [{"year": e.get("year"), "title": e.get("title"), "glyph": e.get("glyph", "")} for e in ev], "n": len(ev),
            "specific": _v(r1(spec / len(ev) * 100)) if ev else None, "by_decade": {k: decades[k] for k in sorted(decades)},
            "say": ("Add events from any time of your life." if not ev else
                    f"{len(ev)} events; {_v(r1(spec / len(ev) * 100))}% recalled as a specific moment.")}


# ---------------------------------------------------------------- overrides, OXQ and DOL-9 (items 40 and 50)

OVERRIDE_KINDS = ("fear", "craving", "thought", "perceptual")


def override_metrics(log: list, days: int, waking_hours=16.0) -> dict:
    """log: [{ts, kind, overridden: bool, latency_s, after_wake: bool}]. Overrides per day, the share of events turned
    around, start latency (median and 90th percentile; just after waking separately), and OXQ, overrides per waking
    hour times 100."""
    done = [e for e in log if e.get("overridden")]
    lat = sorted(e["latency_s"] for e in done if e.get("latency_s") is not None)
    wake = [e["latency_s"] for e in done if e.get("latency_s") is not None and e.get("after_wake")]
    p90 = lat[min(len(lat) - 1, int(math.ceil(0.9 * len(lat))) - 1)] if lat else None
    by = {k: {"events": sum(1 for e in log if e["kind"] == k), "turned": sum(1 for e in done if e["kind"] == k)} for k in OVERRIDE_KINDS}
    oxq = len(done) / (days * waking_hours) * 100 if days > 0 else None
    return {"events": len(log), "overrides": len(done), "per_day": _v(r1(len(done) / days)) if days > 0 else None,
            "turned": _v(r1(len(done) / len(log) * 100)) if log else None, "median_s": _v(r1(_median(lat))) if lat else None,
            "p90_s": _v(r1(p90)), "after_wake_s": _v(r1(_median(wake))) if wake else None, "oxq": _v(r1(oxq)), "by_kind": by,
            "within_4s": _v(r1(sum(1 for x in lat if x <= 4) / len(lat) * 100)) if lat else None}


def monthly(log: list) -> list:
    """The share of events turned around, month by month (30-day periods from the first event)."""
    if not log:
        return []
    t0 = min(e["ts"] for e in log)
    out = {}
    for e in log:
        m = int((e["ts"] - t0) // (30 * 86400))
        a = out.setdefault(m, [0, 0])
        a[0] += 1
        a[1] += 1 if e.get("overridden") else 0
    return [{"month": m + 1, "events": out[m][0], "turned": _v(r1(out[m][1] / out[m][0] * 100))} for m in sorted(out)]


def dol9_rsx(phrase="I move, I act", gesture="Fist closed, shoulders back", action="Do the next small task now") -> str:
    """DOL-9, the 90-second daily override loop: posture, breath 4-2-6 (five rounds), phrase, gesture, a 14 s action: 90 s."""
    L = ["PROTOCOL dol9 \"DOL-9 daily override loop\"", "VERSION 1.0", "SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4",
         "BREATH inhale=4s hold=2s exhale=6s", "", "PHASE posture dur=6s {", "  GESTURE \"Stand or sit tall, head up\"", "}",
         "REPEAT 5 {", "  PHASE in breath=inhale {", "    FEEL \"Breathe in\"", "  }", "  PHASE hold breath=hold {", "    FEEL \"Hold\"", "  }",
         "  PHASE out breath=exhale {", "    FEEL \"Breathe out\"", "  }", "}",
         "PHASE phrase dur=6s {", f"  SAY {_q(phrase)}", "}", "PHASE gesture dur=4s {", f"  GESTURE {_q(gesture)}", "}",
         "PHASE action dur=14s {", f"  FEEL {_q(action)}", "  MARK \"override\"", "}"]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- perceptual events (item 41)

def route_event(kind: str) -> dict:
    """Unusual perceptual experiences are never a trigger for automatic firing: they go to the escalation path."""
    if kind == "perceptual":
        return {"route": "escalate", "auto": False,
                "say": "Unusual perceptual experiences go to your clinician, not to automatic cues. Note what happened and contact them; nothing fires by itself."}
    if kind not in OVERRIDE_KINDS:
        raise ValueError("kind must be one of " + ", ".join(OVERRIDE_KINDS))
    return {"route": "offer", "auto": False, "say": "Offer the override; the person starts it (the autonomy gate decides anything more)."}


# ---------------------------------------------------------------- contexts from speech, the four-day block, the timed burst (item 16)

def speech_context(text: str, contexts: list):
    """contexts: [{id, phrases}]. The first context whose phrase is heard in the transcript, or None."""
    for c in contexts:
        h = hits(text, c["phrases"])
        if h:
            return {"id": c["id"], "heard": h}
    return None


def four_day_block(principle: str, start_day=0, per_day=3) -> list:
    """A four-day acquisition block for one principle: day 1 learn, day 2 rehearse, day 3 apply in context, day 4 test."""
    names = ["Learn", "Rehearse", "Apply in real contexts", "Test without cues"]
    return [{"day": start_day + d, "step": names[d], "principle": principle, "sessions": per_day if d < 3 else 1} for d in range(4)]


def burst(code: str, repeats=3, gap_ms=400) -> dict:
    """The timed burst: the code repeated with short gaps; its total length in milliseconds."""
    one = sum(100 if ch == "." else 300 if ch == "-" else 0 for ch in code) + 100 * max(0, len(code.replace(" ", "")) - 1) + 400 * code.count(" ")
    return {"code": code, "repeats": repeats, "ms": one * repeats + gap_ms * (repeats - 1)}


# ---------------------------------------------------------------- the setting (item 69)

SETTING_FACTORS = ("warmth", "music", "imagery")


def setting_effect(sessions: list, factor: str) -> dict:
    """sessions: [{change, setting: {warmth, music, imagery}}]. The outcome change with the factor against without."""
    on = [s["change"] for s in sessions if s.get("setting", {}).get(factor)]
    off = [s["change"] for s in sessions if not s.get("setting", {}).get(factor)]
    if len(on) < 3 or len(off) < 3:
        return {"factor": factor, "difference": None, "lo": None, "hi": None, "verdict": "too_few", "say": f"Log three or more sessions with and without {factor}."}
    d, lo, hi = _ci_diff(on, off)
    v = "helps" if lo > 0 else "hurts" if hi < 0 else "unclear"
    return {"factor": factor, "difference": _v(r1(d)), "lo": _v(r1(lo)), "hi": _v(r1(hi)), "verdict": v,
            "say": {"helps": f"Sessions with {factor} went better", "hurts": f"Sessions with {factor} went worse", "unclear": f"No clear effect of {factor} yet"}[v]
            + f": {_v(r1(d))} points [{_v(r1(lo))}, {_v(r1(hi))}]."}


# ---------------------------------------------------------------- simulation with known answers

NEUTRAL = ["we", "met", "about", "the", "week", "and", "my", "sister", "for", "a", "walk", "it", "got", "okay", "then", "dinner", "with", "friends", "work",
           "brother", "called", "nothing", "special", "slept", "fine", "the", "bus", "late"]


def sim_session(seed, lines=40, therapist_acc=0.85, matrix=None) -> list:
    """A session transcript: half the lines carry one branch's words (sometimes paraphrased past the lexicon), half are
    neutral. The therapist recognises a branch line with `therapist_acc`, answering in 1-4 s."""
    m = matrix or EXAMPLE_MATRIX
    rng, log = P.Rng(seed), []
    for i in range(lines):
        truth = None
        ws = [NEUTRAL[int(math.floor(rng.u() * len(NEUTRAL)))] for _ in range(6)]
        if rng.u() < 0.5:
            b = m["branches"][int(math.floor(rng.u() * 3))]
            truth = b["id"]
            if rng.u() < 0.8:
                ws.insert(3, b["words"][int(math.floor(rng.u() * len(b["words"])))].replace("*", ""))
        u = add_utterance(log, i * 30, " ".join(ws), m)
        u["_truth"] = truth
        if truth is None:
            choice = "none" if rng.u() < 0.95 else m["branches"][int(math.floor(rng.u() * 3))]["id"]
        else:
            choice = truth if rng.u() < therapist_acc else "none"
        mark(log, i, choice, i * 30 + 1 + 3 * rng.u())
    return log


def sim_speech(seed, plugin, true_type, n_words, lean=0.5) -> str:
    """Speech with a known lean: each content word comes from the true type with probability `lean`, else evenly from
    the others; nine filler words for each content word."""
    rng = P.Rng(seed)
    types = list(PLUGINS[plugin]["types"])
    out = []
    for k in range(n_words):
        if k % 10 == 0:
            t = true_type if rng.u() < lean else types[int(math.floor(rng.u() * len(types)))]
            lex = [e for e in PLUGINS[plugin]["types"][t] if " " not in e]
            out.append(lex[int(math.floor(rng.u() * len(lex)))].replace("*", ""))
        else:
            out.append(NEUTRAL[int(math.floor(rng.u() * len(NEUTRAL)))])
    return " ".join(out)


def _sim_craving(seed, decline, months=3):
    rng, log = P.Rng(seed), []
    for k in range(int(months * 12)):
        ts = k * 86400 * 30 / 12
        c = max(0, min(10, int(math.floor(7 - decline * ts / 86400 / 30 + rng.gauss() * 1.5 + 0.5))))
        log.append({"ts": ts, "craving": c})
    return cue_reactivity(log)["verdict"]


def evaluate(n=100) -> dict:
    res = {}
    for acc in (0.9, 0.6):
        ks, cop = [], []
        for i in range(n):
            log = sim_session(14000 + i, therapist_acc=acc)
            ks.append(agreement(log)["kappa"])
            cop.append(sum(1 for u in log if (u["copilot"] or None) == u["_truth"]) / len(log) * 100)
        res[("matrix", acc)] = {"kappa": _v(r2(_mean(ks))), "copilot": _v(r1(_mean(cop)))}
    for plugin, t in (("senses", "kinesthetic"), ("time", "future")):
        for nw in (200, 500, 1000):
            right = sum(1 for i in range(n) if profile(plugin, sim_speech(15000 + i, plugin, t, nw))["top"] == t)
            wrong = sum(1 for i in range(n) if profile(plugin, sim_speech(15000 + i, plugin, t, nw))["top"] not in (None, t))
            res[("type", plugin, nw)] = {"right": _v(r1(right / n * 100)), "wrong": _v(r1(wrong / n * 100))}
        nul = sum(1 for i in range(n) if profile(plugin, sim_speech(16000 + i, plugin, t, 1000, lean=0.0))["top"] is not None)
        res[("type", plugin, "null")] = {"called": _v(r1(nul / n * 100))}
    for decline in (1.0, 0.0):
        vs = [_sim_craving(17000 + i, decline) for i in range(n)]
        res[("craving", decline)] = {"falling": _v(r1(vs.count("falling") / n * 100)), "rising": _v(r1(vs.count("rising") / n * 100))}
    res["levels"] = level_accuracy()
    return {"n": n, "res": res}


def report(ev: dict) -> str:
    R, n = ev["res"], ev["n"]
    lv = R["levels"]
    L = ["# THERA and LINX extensions on simulated sessions", "",
         f"Generated by `python -m rsso.copilot --evaluate`. {n} simulated sessions or people per row. Built and tested in simulation; effect unproven in people.", "",
         "## The decision matrix and the copilot (claim C21)", "",
         "Forty client lines a session, half of them carrying one branch's cue; one in five of those is phrased past the matrix's word list. "
         "The therapist recognises a cue line with a known accuracy.", "",
         "| Therapist accuracy | Copilot right (against the truth) | Copilot against therapist, kappa |", "|---|---|---|"]
    for acc in (0.9, 0.6):
        x = R[("matrix", acc)]
        L.append(f"| {int(acc * 100)}% | {x['copilot']}% | {x['kappa']} |")
    L += ["", "## Levels of a sentence (claim C19)", "",
          f"The level classifier on the built-in set of {lv['n']} example sentences, eight per level, written for this test (not from clients): "
          f"{lv['accuracy']}% right, kappa {lv['kappa']}.", "",
          "| Level | Right |", "|---|---|"]
    for l in LEVELS:
        L.append(f"| {LEVEL_NAMES[l]} | {lv['by_level'][l]}% |")
    L += ["", "## Typology from speech (claim C18)", "",
          "Speech with a known lean: one word in ten is a type word, half of those from the true type. A profile needs ten type words, and the "
          "leading type must be ahead of the next by at least twice the square root of the type words (so chance alone rarely names one).", "",
          "| Plug-in | Words of speech | Right type | Wrong type |", "|---|---|---|---|"]
    for plugin in ("senses", "time"):
        for nw in (200, 500, 1000):
            x = R[("type", plugin, nw)]
            L.append(f"| {PLUGINS[plugin]['title']} | {nw} | {x['right']}% | {x['wrong']}% |")
    L += ["", f"With no lean (1,000 words), a type was named in {R[('type', 'senses', 'null')]['called']}% (sensory words) and "
          f"{R[('type', 'time', 'null')]['called']}% (time orientation).", "",
          "## Cue-reactivity over months (claims C4, C31)", "",
          "Craving rated at three cue exposures a week for three months, whole points with noise (sd 1.5).", "",
          "| Truth | Called falling | Called rising |", "|---|---|---|"]
    for d, name in ((1.0, "Falls 1 point a month"), (0.0, "No change")):
        x = R[("craving", d)]
        L.append(f"| {name} | {x['falling']}% | {x['rising']}% |")
    L += ["", "Reading: the copilot finds the cue lines it has words for and misses paraphrases, so its agreement with a therapist is "
          "limited by both; a matrix should grow its word list from real sessions. The level classifier works on clear sentences but is "
          "a word-list method, not an understanding of the sentence. A typology needs hundreds of words of speech before it names a type, "
          "and with no lean it rarely names one. A real fall in cue-reactivity of one point a month is found within three months.", ""]
    return "\n".join(L)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["--evaluate"]:
        import pathlib
        path = pathlib.Path(__file__).resolve().parents[1] / "results" / "copilot.md"
        path.write_text(report(evaluate()), encoding="utf-8")
        print(f"wrote {path}")
        return 0
    print("usage: python -m rsso.copilot --evaluate")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
