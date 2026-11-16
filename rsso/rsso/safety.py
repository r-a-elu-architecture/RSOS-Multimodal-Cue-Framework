"""Safety modes for people and agents (spec/CONTAIN.md §9, S1; rules from rsxv/AGENTS.md §3.1).

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
  CHECKIN / event_from_checkin   the structured check-in the pages ask instead of reading free text
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

HELP = ("If you might act on these thoughts, contact local emergency services now. You can also reach a crisis line: "
        "find one for your country at https://findahelpline.com.")


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
}

MESSAGES = {
    "possible_crisis": "Are you safe right now? Practice is paused, because what you said matters more than any "
                       "exercise. " + HELP + " If you have a therapist or doctor, tell them today.",
    "sedative_combination": "Alcohol or other drugs together with a prescribed sedative can slow or stop breathing. "
                            "If you feel very sleepy or confused, or your breathing is slow or shallow, call "
                            "emergency services now. Otherwise do not take more, and ask your prescriber or a "
                            "pharmacist today. Practice is paused.",
    "practical_crisis": "Losing work, a home or income is a crisis of its own. Practice is paused so you can deal "
                        "with it: write down the one next step for today, and contact local social, housing or "
                        "employment services, or someone you trust, to help with it.",
    "intensity_protocol": "This uses heat or cold, pain, holding the breath or going without sleep to force a "
                          "change. RSOS does not run that. Use ordinary regulation instead: slow breathing, "
                          "warmth that is comfortable, rest.",
    "unstable": "Today looks like a day for stabilising: high distress or very little sleep. No deep work today. "
                "Stabilise mode offers only calming and practical steps; you can leave it when you choose.",
    "history_check_in": "You mentioned a hard time in the past. How are you now? If any of it is close again, "
                        "talk to someone you trust or a crisis line (https://findahelpline.com). Nothing else "
                        "changes.",
}

MODE_ALLOWED = {
    "NORMAL": {"module_work", "deep_processing", "override_cue", "regulating_cue", "practical_support",
               "crisis_response", "review", "logging"},
    "STABILISE": {"regulating_cue", "practical_support", "review", "logging", "crisis_response"},
    "PRACTICAL_CRISIS": {"practical_support", "regulating_cue", "logging", "crisis_response"},
    "CRISIS": {"crisis_response", "logging"},
}

MODE_TEXT = {
    "NORMAL": "Normal: everything the Spine allows.",
    "STABILISE": "Stabilise: calming and practical steps only, no deep work. You can leave when you choose.",
    "PRACTICAL_CRISIS": "Practical crisis: practical support and calming only. You can leave when you choose.",
    "CRISIS": "Crisis: practice is paused; only crisis help. Leaving needs your clinician.",
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
            "reason": f"the safety mode is {mode}: {MODE_TEXT[mode]}"}


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
    if "possible_crisis" in hits or "sedative_combination" in hits:
        target = "CRISIS"
    elif "practical_crisis" in hits:
        target = "PRACTICAL_CRISIS"
    elif "unstable" in hits:
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
CHECKIN = [
    {"id": "now", "text": "Right now, are you having thoughts of harming yourself or of not wanting to live?"},
    {"id": "after", "text": "Have you been putting things in order or making arrangements for after you are gone?"},
    {"id": "sedative", "text": "Today, have you had alcohol or other drugs while taking a prescribed sedative "
                               "(for example a sleeping pill, a benzodiazepine or an opioid)?"},
    {"id": "practical", "text": "Are you losing your job, your home or all income right now?"},
    {"id": "past", "text": "Have you had such thoughts in the past, even if they are not here now?"},
]


def event_from_checkin(answers: dict) -> dict:
    """answers: {now, after, sedative, practical, past: 'yes' | 'no' | 'skip', distress: 0-10, sleep_h, screen}.
    'screen' is the older single screening question; a yes there counts as a self-harm signal."""
    yes = lambda k: answers.get(k) == "yes"  # noqa: E731
    ev = {"self_harm_signal": yes("now") or yes("screen"), "arrangements_for_after": yes("after"),
          "substances": yes("sedative"), "sedative_prescribed": yes("sedative"), "job_loss": yes("practical"),
          "history_reference": yes("past")}
    if answers.get("distress") is not None and answers.get("distress") != "":
        ev["distress"] = float(answers["distress"])
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
