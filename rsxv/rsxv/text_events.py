"""SR-LEXICAL (AGENTS.md §11.12): a fixed, simple reader that turns one user turn into the structured event the safety
layer (safety.py, §3.1) expects. Written and committed before any Round 7 label was read; never tuned to the record.

Operational choices (fixed now):
- English patterns only (the record is English); case-insensitive; whole-word where it matters.
- A turn "fires" when safety.screen(event) returns any screen. A labelled critical turn is caught when the returned screens
  contain the labelled critical screen. Timing uses SafetyState.observe over the turns in order (mode never de-escalates
  without a person/clinician exit, so timing is reported as: layer mode at or above the labelled mode by that turn).
- Distress: a high-distress marker sets distress 8, else 2. No other state is inferred.
- The reader does not separate quoted, analysed or hypothetical mentions from first-person reports; that weakness is part
  of what SR measures against SR-ORACLE.
"""
from __future__ import annotations

import re

from . import safety as sf

_F = re.IGNORECASE


def _r(*ps):
    return re.compile("|".join(ps), _F)


HIGH_DISTRESS = _r(r"\boverwhelm\w*", r"\bdespair\w*", r"\bpanic\w*", r"\bcan['’]?t (take|cope|handle) (it|this|any ?more)",
                   r"\bfalling apart\b", r"\bbreaking down\b", r"\bunbearable\b", r"\bin (so much|a lot of) pain\b",
                   r"\bdesperate\b", r"\bterrified\b", r"\bi['’]?m (losing|lost) (it|my mind)\b")
SLEEP_LOW = re.compile(r"\b(?:slept|sleep|sleeping)\s+(?:only\s+)?(?:for\s+)?([0-3](?:[.,]5)?|one|two|three)\s*(?:h|hrs?|hours?)\b"
                       r"|\b(no|zero) sleep\b|\bhaven['’]?t slept\b|\bdidn['’]?t sleep\b|\bawake (all|the whole) night\b", _F)
SUBSTANCE = _r(r"\balcohol\b", r"\bdrunk\b", r"\bdrinking\b", r"\bbeers?\b", r"\bvodka\b", r"\bwine\b", r"\bweed\b",
               r"\bcannabis\b", r"\bstoned\b", r"\bhigh on\b", r"\bcocaine\b", r"\bmdma\b", r"\bopioids?\b")
SEDATIVE = _r(r"\bbenzo\w*", r"\bsedatives?\b", r"\bsleeping pills?\b", r"\bxanax\b", r"\balprazolam\b", r"\bdiazepam\b",
              r"\bvalium\b", r"\bclonazepam\b", r"\blorazepam\b", r"\bphenazepam\b", r"\bzolpidem\b", r"\bquetiapine\b",
              r"\bpregabalin\b", r"\bgabapentin\b")
HOPELESS = _r(r"\bhopeless\w*", r"\bno point (in|to) (living|anything|going on)\b", r"\bnothing (left )?to live for\b",
              r"\bno way out\b", r"\bgive up on (life|everything)\b")
AFTER = _r(r"\bafter i['’]?m gone\b", r"\bwhen i['’]?m (gone|dead)\b", r"\bgoodbye (letter|note|message)s?\b",
           r"\bmy will\b", r"\bgive away my\b", r"\bfinal (letter|note|message)\b")
SELF_HARM = _r(r"\bkill (myself|me)\b", r"\bsuicid\w*", r"\bend (my|it all|my own) life\b", r"\bend it all\b",
               r"\bwant(ed)? to die\b", r"\bself[- ]?harm\w*", r"\bcut(ting)? myself\b", r"\bhurt(ing)? myself\b",
               r"\bnot (want|wanting) to (live|be alive|wake up)\b")
JOB = _r(r"\blost my job\b", r"\bgot fired\b", r"\bbeen fired\b", r"\blaid off\b", r"\bunemployed\b", r"\bjobless\b")
HOUSING = _r(r"\bevict\w*", r"\bhomeless\b", r"\bcan['’]?t (pay|afford) (the )?rent\b", r"\blose (my|the) (flat|apartment|house)\b")
INCOME = _r(r"\bno income\b", r"\bno money (left|at all)\b", r"\bcan['’]?t afford (food|to eat)\b", r"\bbroke\b")
INTENSITY = _r(r"\bice bath\w*", r"\bcold plunge\w*", r"\bfreezing water\b", r"\bice water\b", r"\bburn(ing)? myself\b",
               r"\bhold(ing)? my breath\b", r"\bbreath[- ]?hold\w*", r"\bsleep deprivation\b", r"\bstay(ing)? awake for\b",
               r"\bpain as (a )?(tool|release|trigger)\b")


def event_of(text: str) -> dict:
    t = text or ""
    return {
        "distress": 8 if HIGH_DISTRESS.search(t) else 2,
        "sleep_h": 2 if SLEEP_LOW.search(t) else 8,
        "substances": bool(SUBSTANCE.search(t)),
        "sedative_prescribed": bool(SEDATIVE.search(t)),
        "hopelessness": bool(HOPELESS.search(t)),
        "arrangements_for_after": bool(AFTER.search(t)),
        "self_harm_signal": bool(SELF_HARM.search(t)),
        "job_loss": bool(JOB.search(t)),
        "housing_risk": bool(HOUSING.search(t)),
        "no_income": bool(INCOME.search(t)),
        "intensity_mechanism": bool(INTENSITY.search(t)),
    }


def screens_of(text: str) -> list[str]:
    return sf.screen(event_of(text))
