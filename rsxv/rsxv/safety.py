"""Safety layer (step R2). Specification: ../AGENTS.md §3.1.

Screens structured events, keeps a safety mode (NORMAL, STABILISE, PRACTICAL_CRISIS, CRISIS), builds the fixed response
for each screen, gates deep-processing sessions on stability rather than on count, and adjusts effect estimates for
medication covariates. Rules here are fixed; agents cannot edit them (they are part of the Spine).
"""
from __future__ import annotations

MODES = ("NORMAL", "STABILISE", "PRACTICAL_CRISIS", "CRISIS")
SEVERITY = {"NORMAL": 0, "STABILISE": 1, "PRACTICAL_CRISIS": 2, "CRISIS": 3}

# Recovery window in hours before the next deep-processing session, by intensity of the last one.
RECOVERY_H = {"mild": 0, "moderate": 24, "intense": 48, "highly_destabilising": 96}
WEEKLY_CAP = {"self_chosen": 1, "clinician_agreed": 3}       # deep sessions per 7 days by consent tier


def screen(event: dict) -> list[str]:
    """Return the screens an event triggers. Events are structured; text classification happens upstream and is logged."""
    hits = []
    if event.get("substances") and event.get("sedative_prescribed"):
        hits.append("sedative_combination")
    if event.get("hopelessness") and event.get("arrangements_for_after"):
        hits.append("possible_crisis")
    if event.get("self_harm_signal"):
        hits.append("possible_crisis")
    if event.get("job_loss") or event.get("housing_risk") or event.get("no_income"):
        hits.append("practical_crisis")
    if event.get("intensity_mechanism"):
        hits.append("intensity_protocol")
    if event.get("distress", 0) >= 7 or event.get("sleep_h", 8) < 4:
        hits.append("unstable")
    return list(dict.fromkeys(hits))


RESPONSES = {
    "possible_crisis": ["ask_safety_directly", "crisis_contacts_for_country", "notify_clinician_view",
                        "pause_module_work"],
    "sedative_combination": ["state_breathing_risk_plainly", "route_prescriber_or_emergency_if_symptoms",
                             "notify_clinician_view", "pause_module_work"],
    "practical_crisis": ["concrete_next_steps", "offer_human_services", "pause_module_work"],
    "intensity_protocol": ["block_protocol", "offer_ordinary_regulation"],
    "unstable": ["offer_stabilise_mode", "no_deep_processing_today"],
}


class SafetyState:
    """Mode machine. Escalation is automatic; leaving CRISIS needs a clinician or owner confirmation; leaving STABILISE or
    PRACTICAL_CRISIS needs the person's own choice. Every transition is returned so the caller can log it."""

    def __init__(self):
        self.mode = "NORMAL"
        self.history: list[dict] = []

    def _go(self, mode: str, why: str, by: str) -> dict:
        rec = {"from": self.mode, "to": mode, "why": why, "by": by}
        self.mode = mode
        self.history.append(rec)
        return rec

    def observe(self, event: dict) -> dict:
        hits = screen(event)
        target = "NORMAL"
        if "possible_crisis" in hits or "sedative_combination" in hits:
            target = "CRISIS"
        elif "practical_crisis" in hits:
            target = "PRACTICAL_CRISIS"
        elif "unstable" in hits:
            target = "STABILISE"
        actions = [a for h in hits for a in RESPONSES[h]]
        rec = None
        if SEVERITY[target] > SEVERITY[self.mode]:
            rec = self._go(target, ",".join(hits), "screen")
        return {"mode": self.mode, "screens": hits, "actions": list(dict.fromkeys(actions)), "transition": rec}

    def enter_stabilise(self, by: str = "person") -> dict:
        if SEVERITY[self.mode] >= SEVERITY["STABILISE"]:
            return {"ok": False, "why": "already_at_or_above"}
        return {"ok": True, "transition": self._go("STABILISE", "chosen", by)}

    def exit(self, by: str) -> dict:
        if self.mode == "NORMAL":
            return {"ok": False, "why": "not_in_safety_mode"}
        if self.mode == "CRISIS" and by not in ("clinician", "owner"):
            return {"ok": False, "why": "crisis_exit_needs_clinician_or_owner"}
        if self.mode in ("STABILISE", "PRACTICAL_CRISIS") and by not in ("person", "clinician", "owner"):
            return {"ok": False, "why": "exit_is_the_persons_choice"}
        return {"ok": True, "transition": self._go("NORMAL", "exit", by)}


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
    """Effect of a module (treated vs not) stratified by medication state, then weighted by stratum size.
    records: {"treated": bool, "med_state": str, outcome}. Strata missing either arm are dropped and reported."""
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
