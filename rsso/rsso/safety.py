"""Session states for people and agents (spec/CONTAIN.md §9 and §10; rules from rsxv/AGENTS.md §3.1).

One rule set. The agent World (rsxv) and the person-facing pages (docs/js/safety.js, identical results, tested) use
this module, so a rule changes in one place only. Rules here are fixed: no module, agent or model may edit them.

  screen(event)                  the screens a structured event raises
  RESPONSES / MESSAGES           the fixed actions and the sentence the person reads for each screen
  new_state / observe / enter_stabilise / exit
                                 the mode machine as plain data (NORMAL, STABILISE, PRACTICAL_CRISIS, CRISIS):
                                 escalation is automatic and never downgrades on a lower screen; leaving CRISIS needs
                                 a clinician or the owner; leaving STABILISE or PRACTICAL_CRISIS is the person's choice
  MODE_ALLOWED / category / allowed
                                 which kinds of action each mode allows
  MODE_NAME / LEVELS             what people read: Standard, Stabilisation, Paused: practical, Clinician-led protocol;
                                 guidance levels self_guided, structured, clinician_led (§10)
  SELF_CHECK / CLINICAL          the everyday self-check (intensity, sleep) and the clinician-entered screening result
  event_from_check(answers)      either of them as a structured event
  spine_flags(text)              Spine wording rules: no release through intensity mechanisms (Jin), no population
                                 ranks about the person (Makoto)
  may_start_deep_session         deep processing gated on stability, not on a planned count
  adjusted_effect                module effects stratified by medication state
"""
from __future__ import annotations

import copy
import re

MODES = ("NORMAL", "STABILISE", "PRACTICAL_CRISIS", "CRISIS")
SEVERITY = {"NORMAL": 0, "STABILISE": 1, "PRACTICAL_CRISIS": 2, "CRISIS": 3}

RECOVERY_H = {"mild": 0, "moderate": 24, "intense": 48, "highly_destabilising": 96}
WEEKLY_CAP = {"self_chosen": 1, "clinician_agreed": 3}

FOOTER = "Research and development framework; not a medical device."


def screen(event: dict) -> list[str]:
    """Return the screens a structured event raises (rsxv/AGENTS.md §3.1, with the §11.14 fix)."""
    hits = []
    if event.get("substances") and event.get("sedative_prescribed"):
        hits.append("sedative_combination")
    if event.get("arrangements_for_after"):          # §11.14 fix: arrangements for "after" alone
        hits.append("possible_crisis")
    if event.get("self_harm_signal"):
        hits.append("possible_crisis")
    if event.get("job_loss") or event.get("housing_risk") or event.get("no_income"):
        hits.append("practical_crisis")
    if event.get("intensity_mechanism"):
        hits.append("intensity_protocol")
    if (event.get("distress") if event.get("distress") is not None else 0) >= 7 or \
            (event.get("sleep_h") if event.get("sleep_h") is not None else 8) < 4:
        hits.append("unstable")
    if event.get("clinical_result") == "high":       # §10: a practitioner's screening result, validated instrument
        hits.append("clinical_high")
    elif event.get("clinical_result") == "moderate":
        hits.append("clinical_moderate")
    if event.get("history_reference") and "possible_crisis" not in hits:
        hits.append("history_check_in")             # a past crisis mentioned now: a gentle check-in, no mode change
    return list(dict.fromkeys(hits))


RESPONSES = {
    "possible_crisis": ["ask_safety_directly", "crisis_contacts_for_country", "notify_clinician_view",
                        "pause_module_work"],
    "sedative_combination": ["state_breathing_risk_plainly", "route_prescriber_or_emergency_if_symptoms",
                             "notify_clinician_view", "pause_module_work"],
    "practical_crisis": ["concrete_next_steps", "offer_human_services", "pause_module_work"],
    "intensity_protocol": ["block_protocol", "offer_ordinary_regulation"],
    "unstable": ["offer_stabilise_mode", "no_deep_processing_today"],
    "history_check_in": ["ask_how_they_are_now", "offer_contacts_without_escalation"],
    "clinical_high": ["route_to_clinician_led_protocol", "notify_clinician_view", "pause_module_work"],
    "clinical_moderate": ["offer_stabilise_mode", "no_deep_processing_today", "notify_clinician_view"],
}

MESSAGES = {
    "possible_crisis": "Self-guided practice is paused. The session continues inside a clinician-led protocol: the "
                       "responsible clinician decides the next step and resumes practice.",
    "sedative_combination": "Medication interaction flagged. Self-guided practice is paused until the prescribing "
                            "clinician has reviewed it.",
    "practical_crisis": "Practical circumstances flagged. Practice is paused so the next practical step comes first; "
                        "resume when you choose.",
    "intensity_protocol": "Intensity methods (temperature extremes, pain, extreme breath-holding, sleep loss) are "
                          "outside RSOS. Use a regulation program instead.",
    "unstable": "High intensity or short sleep: Stabilisation is suggested. Regulation programs only today; leave "
                "Stabilisation when you choose.",
    "history_check_in": "Earlier experience noted for the practitioner's review. Nothing changes in the session.",
    "clinical_high": "Screening result: high. The session moves to the clinician-led protocol; the responsible "
                     "clinician resumes practice.",
    "clinical_moderate": "Screening result: moderate. Stabilisation: regulation programs only, no deep processing "
                         "today; the practitioner is informed.",
}

MODE_ALLOWED = {
    "NORMAL": {"module_work", "deep_processing", "override_cue", "regulating_cue", "practical_support",
               "crisis_response", "review", "logging"},
    "STABILISE": {"regulating_cue", "practical_support", "review", "logging", "crisis_response"},
    "PRACTICAL_CRISIS": {"practical_support", "regulating_cue", "logging", "crisis_response"},
    "CRISIS": {"crisis_response", "logging"},
}

MODE_NAME = {"NORMAL": "Standard", "STABILISE": "Stabilisation", "PRACTICAL_CRISIS": "Paused: practical",
             "CRISIS": "Clinician-led protocol"}
MODE_TEXT = {
    "NORMAL": "Standard: every program the person's guidance level allows.",
    "STABILISE": "Stabilisation: regulation programs and practical steps only, no deep processing. The person "
                 "leaves it when they choose.",
    "PRACTICAL_CRISIS": "Paused: practical. Practical steps and regulation only. The person resumes when they choose.",
    "CRISIS": "Clinician-led protocol: self-guided practice is paused; the responsible clinician resumes it.",
}
LEVELS = {
    "self_guided": "Everyday states (pressure, nerves, low energy, distraction): self-guided.",
    "structured": "Recurring strong states, panic, difficult memories: with consent, self-guided or with a "
                  "practitioner the person chooses (therapist, coach).",
    "clinician_led": "Trauma processing, depression work and any acute risk to life: only inside a qualified "
                     "clinician's protocol (including a private psychotherapist or psychiatrist).",
}

REGULATING = ("paced_breathing", "interrupt_only", "tier016_stillness", "tier012_breath_anchor")


def category(action: dict) -> str:
    """The kind of action, for MODE_ALLOWED. action as CONTAIN's: {kind, protocol, therapist_led, deep, category}."""
    if action.get("category"):
        return action["category"]
    if action.get("kind") == "plan":
        return "module_work"
    if action.get("therapist_led") or action.get("deep"):
        return "deep_processing"
    if (action.get("protocol") or "") in REGULATING:
        return "regulating_cue"
    return "override_cue"


def new_state() -> dict:
    return {"mode": "NORMAL", "history": [], "last": None}


def allowed(state: dict | None, action: dict) -> dict:
    """{ok, mode, category, reason}: whether the mode in force allows the action."""
    mode = (state or new_state())["mode"]
    cat = category(action)
    if cat in MODE_ALLOWED[mode]:
        return {"ok": True, "mode": mode, "category": cat, "reason": ""}
    return {"ok": False, "mode": mode, "category": cat,
            "reason": f"session state {MODE_TEXT[mode]}"}


def _go(st: dict, mode: str, why: str, by: str, now: float) -> dict:
    rec = {"from": st["mode"], "to": mode, "why": why, "by": by, "at": now}
    st["mode"] = mode
    st["history"] = (st["history"] + [rec])[-50:]
    return rec


def observe(state: dict | None, event: dict, now: float = 0.0) -> tuple[dict, dict]:
    """Screen an event and escalate if it calls for a higher mode. Returns (state, result)."""
    st = copy.deepcopy(state or new_state())
    hits = screen(event)
    target = "NORMAL"
    if "possible_crisis" in hits or "sedative_combination" in hits or "clinical_high" in hits:
        target = "CRISIS"
    elif "practical_crisis" in hits:
        target = "PRACTICAL_CRISIS"
    elif "unstable" in hits or "clinical_moderate" in hits:
        target = "STABILISE"
    actions = list(dict.fromkeys(a for h in hits for a in RESPONSES[h]))
    rec = None
    if SEVERITY[target] > SEVERITY[st["mode"]]:
        rec = _go(st, target, ",".join(hits), "screen", now)
    st["last"] = {"at": now, "screens": hits}
    return st, {"mode": st["mode"], "screens": hits, "actions": actions, "transition": rec,
                "messages": [MESSAGES[h] for h in hits]}


def enter_stabilise(state: dict | None, by: str = "person", now: float = 0.0) -> tuple[dict, dict]:
    st = copy.deepcopy(state or new_state())
    if SEVERITY[st["mode"]] >= SEVERITY["STABILISE"]:
        return st, {"ok": False, "why": "already_at_or_above"}
    return st, {"ok": True, "transition": _go(st, "STABILISE", "chosen", by, now)}


def exit(state: dict | None, by: str, now: float = 0.0) -> tuple[dict, dict]:  # noqa: A001 (mirrors the agent API)
    st = copy.deepcopy(state or new_state())
    if st["mode"] == "NORMAL":
        return st, {"ok": False, "why": "not_in_safety_mode"}
    if st["mode"] == "CRISIS" and by not in ("clinician", "owner"):
        return st, {"ok": False, "why": "crisis_exit_needs_clinician_or_owner"}
    if st["mode"] in ("STABILISE", "PRACTICAL_CRISIS") and by not in ("person", "clinician", "owner"):
        return st, {"ok": False, "why": "exit_is_the_persons_choice"}
    return st, {"ok": True, "transition": _go(st, "NORMAL", "exit", by, now)}


class SafetyState:
    """The mode machine as an object, for the agent World (rsxv). Same rules as the functions above; the history
    is kept in full here (the pages keep the last 50)."""

    def __init__(self):
        self._st = new_state()
        self.history: list[dict] = []

    @property
    def mode(self) -> str:
        return self._st["mode"]

    def _keep(self, rec):
        if rec:
            rec = {k: v for k, v in rec.items() if k != "at"}
            self.history.append(rec)
        return rec

    def observe(self, event: dict) -> dict:
        self._st, r = observe(self._st, event)
        return {"mode": r["mode"], "screens": r["screens"], "actions": r["actions"],
                "transition": self._keep(r["transition"])}

    def enter_stabilise(self, by: str = "person") -> dict:
        self._st, r = enter_stabilise(self._st, by)
        if r.get("transition"):
            r["transition"] = self._keep(r["transition"])
        return r

    def exit(self, by: str) -> dict:
        self._st, r = exit(self._st, by)
        if r.get("transition"):
            r["transition"] = self._keep(r["transition"])
        return r


# ---------------------------------------------------------------------------------------------- structured check-in
SELF_CHECK = [
    {"id": "intensity", "text": "Intensity of the state right now (0 none, 10 the most)", "kind": "scale"},
    {"id": "sleep_h", "text": "Hours slept last night", "kind": "hours"},
]
CLINICAL_RESULTS = ("none", "low", "moderate", "high")
CLINICAL_FLAGS = {"medication": "Medication interaction (substances with a prescribed sedative)",
                  "practical": "Practical circumstances (work, housing, income)"}


def event_from_check(answers: dict) -> dict:
    """answers: {intensity: 0-10, sleep_h, clinical_result: none|low|moderate|high, flags: [medication, practical],
    history: bool}. The clinical fields are entered by the practitioner from a validated instrument of their choice."""
    flags = set(answers.get("flags") or [])
    ev = {"substances": "medication" in flags, "sedative_prescribed": "medication" in flags,
          "job_loss": "practical" in flags, "history_reference": bool(answers.get("history"))}
    if answers.get("clinical_result") in CLINICAL_RESULTS:
        ev["clinical_result"] = answers["clinical_result"]
    if answers.get("intensity") is not None and answers.get("intensity") != "":
        ev["distress"] = float(answers["intensity"])
    if answers.get("sleep_h") is not None and answers.get("sleep_h") != "":
        ev["sleep_h"] = float(answers["sleep_h"])
    return ev


# ---------------------------------------------------------------------------------------------------- Spine wording
SPINE_WORDS = {
    "temperature_extreme": [r"ice[- ]?bath", r"ice[- ]?water", r"cold[- ]?plunge", r"freezing", r"scalding",
                            r"boiling", r"burn(?:ing)? (?:yourself|your skin|the skin)", r"very hot (?:bath|water|shower)",
                            r"hottest (?:bath|water|shower)", r"as hot as (?:you|it) can"],
    "pain": [r"cause (?:yourself )?pain", r"until it hurts", r"through the pain", r"pinch (?:yourself )?hard",
             r"snap (?:a|the) (?:rubber )?band", r"hurt yourself", r"self[- ]?inflicted"],
    "breath_holding_extreme": [r"hold (?:your|the) breath (?:as long as|until)", r"until you (?:almost )?(?:faint|pass out|black out)",
                               r"(?:hold|holding) (?:your|the) breath for (?:[2-9]|\d{2,}) ?min"],
    "sleep_deprivation": [r"without sleep", r"no sleep", r"stay awake (?:all night|for \d+)", r"skip sleep",
                          r"sleep deprivation"],
    "rank_claim": [r"\btop \d+(?:\.\d+)? ?%", r"\b\d+ in (?:a |one )?(?:thousand|million|billion)",
                   r"\b\d+ (?:in|of) \d+ (?:thousand|million|billion)", r"\bone in a (?:thousand|million|billion)",
                   r"rarer than", r"\bpercentile\b", r"better than (?:\d+ ?%|most people|everyone)",
                   r"only (?:a few|\d+) (?:people )?in the world"],
}
SPINE_VIRTUE = {"temperature_extreme": "jin", "pain": "jin", "breath_holding_extreme": "jin",
                "sleep_deprivation": "jin", "rank_claim": "makoto"}
SPINE_TEXT = {
    "temperature_extreme": "release through extreme heat or cold is not used (Jin): keep warmth comfortable",
    "pain": "release through pain is not used (Jin)",
    "breath_holding_extreme": "extreme breath-holding is not used (Jin): breathe slowly instead",
    "sleep_deprivation": "going without sleep is not used (Jin)",
    "rank_claim": "no population ranks about the person (Makoto): RSOS reports your own measures",
}
_SPINE_RE = {k: re.compile("|".join(v), re.I) for k, v in SPINE_WORDS.items()}


def spine_flags(text: str) -> list[dict]:
    """Spine wording flags in a frame, rule, cue or proposal: [{flag, virtue, text}] in fixed order."""
    t = str(text or "")
    return [{"flag": k, "virtue": SPINE_VIRTUE[k], "text": SPINE_TEXT[k]} for k in SPINE_WORDS if _SPINE_RE[k].search(t)]


# ------------------------------------------------------------------------------------------------- deep processing
def may_start_deep_session(now_h: float, last: dict | None, check_24h: dict | None, done_7d: int, tier: str) -> dict:
    """Gate the next deep-processing session on stability, not on a planned count.
    last = {"end_h", "intensity"}; check_24h = {"sleep_ok", "functioning_ok", "craving_spike", "distress_at_baseline"}."""
    if tier not in WEEKLY_CAP:
        return {"ok": False, "why": "consent_tier_required"}
    if done_7d >= WEEKLY_CAP[tier]:
        return {"ok": False, "why": "weekly_cap"}
    if last:
        if now_h - last["end_h"] < RECOVERY_H[last["intensity"]]:
            return {"ok": False, "why": "recovery_window"}
        c = check_24h or {}
        if not (c.get("sleep_ok") and c.get("functioning_ok") and not c.get("craving_spike")
                and c.get("distress_at_baseline")):
            return {"ok": False, "why": "stability_check_not_green"}
    return {"ok": True}


def adjusted_effect(records: list[dict], key: str = "outcome") -> dict:
    """Effect of a module (treated vs not) stratified by medication state, weighted by stratum size.
    Strata missing either arm are dropped and reported."""
    strata: dict[str, dict] = {}
    for r in records:
        s = strata.setdefault(r.get("med_state", "none"), {"t": [], "c": []})
        s["t" if r["treated"] else "c"].append(r[key])
    used, dropped, num, den = [], [], 0.0, 0
    for name, s in strata.items():
        if s["t"] and s["c"]:
            n = len(s["t"]) + len(s["c"])
            num += n * (sum(s["t"]) / len(s["t"]) - sum(s["c"]) / len(s["c"]))
            den += n
            used.append(name)
        else:
            dropped.append(name)
    t = [r[key] for r in records if r["treated"]]
    c = [r[key] for r in records if not r["treated"]]
    crude = (sum(t) / len(t) - sum(c) / len(c)) if t and c else None
    return {"adjusted": num / den if den else None, "crude": crude, "strata_used": used, "strata_dropped": dropped}
