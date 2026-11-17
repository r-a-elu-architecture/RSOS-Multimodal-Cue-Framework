"""Domain profiles (spec/PROFILES.md).

A profile changes what people see, never what the engine does. Modules keep one canonical vocabulary (the one the
Clinical profile shows); ``text`` translates it for display. Mirrors docs/js/profiles.js (identical results, tested).
No engine module imports this one.
"""
import re

PROFILES = [
    {"id": "personal", "name": "Personal", "for": "Individuals shaping their own state",
     "max_level": "structured", "clinical_module": "none", "memory_work": True},
    {"id": "coaching", "name": "Coaching", "for": "Coaches and personal-development practitioners",
     "max_level": "structured", "clinical_module": "none", "memory_work": True},
    {"id": "performance", "name": "Performance", "for": "Sport, music, stage and executives",
     "max_level": "structured", "clinical_module": "none", "memory_work": True},
    {"id": "learning", "name": "Learning", "for": "Universities, students, mnemonics and languages",
     "max_level": "structured", "clinical_module": "none", "memory_work": True},
    {"id": "research", "name": "Research", "for": "Labs, BCI/EEG, haptic devices and trials",
     "max_level": "clinician_led", "clinical_module": "study", "memory_work": True},
    {"id": "workplace", "name": "Workplace", "for": "Companies and teams; employers see aggregates only",
     "max_level": "structured", "clinical_module": "none", "memory_work": False},
    {"id": "clinical", "name": "Clinical", "for": "Psychotherapists, psychiatrists and clinics",
     "max_level": "clinician_led", "clinical_module": "practitioner", "memory_work": True},
]
IDS = [p["id"] for p in PROFILES]
DEFAULT = "personal"

_K = ["rating", "target_state", "memories", "memory", "low_mood", "surges", "ongoing_stress", "changes",
      "person", "persons", "practitioner", "practitioners", "therapy"]
_ROWS = {
    "clinical": ["distress", "negative state", "trauma", "distressing memory", "depression", "anxiety",
                 "chronic stress", "symptoms", "client", "clients", "therapist", "therapists", "therapy"],
    "personal": ["intensity", "state you want to change", "difficult memories", "difficult memory",
                 "low energy or mood", "sudden surges", "ongoing stress", "what you want to change",
                 "client", "clients", "practitioner", "practitioners", "guided practice"],
    "coaching": ["intensity", "state the client wants to change", "difficult memories", "difficult memory",
                 "low energy or mood", "sudden surges", "ongoing stress", "what the client wants to change",
                 "client", "clients", "coach", "coaches", "coaching"],
    "performance": ["tension", "limiting state", "past setbacks", "past setback", "low drive", "pre-event nerves",
                    "ongoing pressure", "performance limiters", "athlete", "athletes", "coach", "coaches", "coaching"],
    "learning": ["load", "learning block", "earlier learning experiences", "earlier learning experience",
                 "low motivation", "exam nerves", "ongoing study pressure", "learning blocks", "learner", "learners",
                 "teacher", "teachers", "tutoring"],
    "research": ["intensity", "target state", "aversive memories", "aversive memory", "low affect", "acute arousal",
                 "chronic stress", "outcome measures", "participant", "participants", "investigator", "investigators",
                 "guided sessions"],
    "workplace": ["pressure", "pressure point", "difficult memories", "difficult memory", "low energy",
                  "pressure spikes", "ongoing pressure", "focus areas", "team member", "team members", "facilitator",
                  "facilitators", "facilitated sessions"],
}
TERMS = {k: {p: _ROWS[p][i] for p in _ROWS} for i, k in enumerate(_K)}

# Ordered phrase rules: (pattern, template). "{key}" inserts a term, "{a:key}" adds "a" or "an".
RULES = [
    (r"\bdistress \(SUDS?\)", "{rating}"),                              # FIXES_R1 P-4
    (r"\btherapy sessions?\b", "{therapy}"),
    (r"\b(?:an? )?(?:anxiety|panic) disorders?\b", "{surges}"),
    (r"\bclinical judgement\b", "professional judgement"),              # FIXES_R1 P-3
    (r"\bclinical screening\b", "screening"),
    (r"\bPTSD or trauma\b", "{memories}"),
    (r"\btrauma symptoms\b", "{memories}"),
    (r"\btrauma(?:tic)? memories\b", "{memories}"),
    (r"\b(?:a|an) distressing memory\b", "{a:memory}"),
    (r"\bdistressing memory\b", "{memory}"),
    (r"\bthe most distress\b", "the highest {rating}"),
    (r"\bsymptoms and what they feel like\b", "{changes} (describe how it feels)"),
    (r"\b(?:a|an) negative state\b", "{a:target_state}"),
    (r"\bnegative state\b", "{target_state}"),
    (r"\b(?:a|an) therapist\b", "{a:practitioner}"),
    (r"\b(?:a|an) (?:client|patient)\b", "{a:person}"),
    (r"\btherapists\b", "{practitioners}"),
    (r"\btherapist\b", "{practitioner}"),
    (r"\b(?:clients|patients)\b", "{persons}"),
    (r"\b(?:client|patient)\b", "{person}"),
    (r"\btherapy\b", "{therapy}"),
    (r"\bchronic stress\b", "{ongoing_stress}"),
    (r"\bSUDS?\b", "{rating}"),
    (r"\bdistressing\b", "intense"),
    (r"\bdistress\b", "{rating}"),
    (r"\bPTSD\b", "{memories}"),
    (r"\btrauma\b", "{memories}"),
    (r"\bdepression\b", "{low_mood}"),
    (r"\b(?:anxiety|panic)\b", "{surges}"),
    (r"\bsymptoms\b", "{changes}"),
]
_RX = re.compile("|".join("(" + p + ")" for p, _ in RULES), re.I)
_SLOT = re.compile(r"\{(a:)?(\w+)\}")

CLINICAL_WORDS = (r"\b(?:SUDS?|PTSD|depress\w*|trauma\w*|symptom\w*|distress\w*|panic\w*|anxiety|patients?|therap\w*"
                  r"|clinical screening|clinical judgement|diagnos\w*|C-SSRS|PHQ-9|GAD-7|PCL-5)\b")   # FIXES_R1 P-3

# Research records and architecture pages keep their original wording.
EXEMPT_PAGES = ["results.html", "system.html", "tiers.html", "roadmap.html", "glyphs.html",
                "architecture-benchmark.html", "invariance-v14.html", "cue-lab.html", "cue-lab-v13.html"]


def valid(profile):
    return profile if profile in IDS else DEFAULT


def get(profile):
    return PROFILES[IDS.index(valid(profile))]


def max_level(profile, clinical_on=False):
    """The domain's highest guidance level. Research allows clinician-led work only with a study clinician, that is
    with the clinical module on (FIXES_R1 W-2)."""
    p = valid(profile)
    if p == "research":
        return "clinician_led" if clinical_on else "structured"
    return get(p)["max_level"]


_LED = re.compile(r"\b(?:therapist|clinician)-led\b", re.I)
_THERAPIST = re.compile(r"\btherapist(s?)\b", re.I)


def _clinician_led_text(s):
    """In text about therapist-led or clinician-led work, the therapist is a clinician in every domain (FIXES_R1 P-1)."""
    if not _LED.search(s):
        return s
    return _THERAPIST.sub(lambda m: ("Clinician" if m.group(0)[0].isupper() else "clinician") + m.group(1), s)


def clinical_vocab(profile, clinical_on=False):
    """True when the canonical (clinical) vocabulary is shown."""
    p = valid(profile)
    return p == "clinical" or (p == "research" and bool(clinical_on))


def term(key, profile, clinical_on=False):
    p = "clinical" if clinical_vocab(profile, clinical_on) else valid(profile)
    return TERMS[key][p]


def _cap(s):
    return s[:1].upper() + s[1:]


def _article(w):
    return ("an " if w[:1].lower() in "aeiou" else "a ") + w


def text(s, profile, clinical_on=False):
    """Translate canonical display text into the profile's vocabulary."""
    if not s or clinical_vocab(profile, clinical_on):
        return s
    p = valid(profile)
    s = _clinician_led_text(s)

    def fill(m):
        tpl = RULES[m.lastindex - 1][1]
        out = _SLOT.sub(lambda t: _article(TERMS[t.group(2)][p]) if t.group(1) else TERMS[t.group(2)][p], tpl)
        w = m.group(0)
        if w[0].isupper() and (len(w) == 1 or not w[1].isupper() or m.start() == 0):
            out = _cap(out)
        return out

    return _RX.sub(fill, s)


def has_clinical_words(s):
    return re.search(CLINICAL_WORDS, s, re.I) is not None
