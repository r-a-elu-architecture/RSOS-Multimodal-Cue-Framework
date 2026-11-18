"""PERSONLAB step 4 (spec/PERSONLAB.md §6): a simulated person driven by an identity profile.

Action effects are parameters; the defaults are neutral placeholders that step 5 fits from ESConv."""
from __future__ import annotations

import copy
import random

from . import schema as S

ACTIONS = {
    "STABILISE": {"strategies": ("Affirmation and Reassurance", "Reflection of feelings"), "archetype": "BEAR"},
    "EXPLORE": {"strategies": ("Question", "Restatement or Paraphrasing"), "archetype": "RAVEN"},
    "SUGGEST": {"strategies": ("Providing Suggestions", "Information"), "archetype": "TIGER"},
    "SHARE": {"strategies": ("Self-disclosure",), "archetype": "LION"},
    "NONE": {"strategies": ("Others",), "archetype": None},
}
STRATEGY_TO_ACTION = {s: a for a, v in ACTIONS.items() for s in v["strategies"]}

_EFF = {"r": 0.2, "m": 0.02, "e": 0.05, "p": 0.03, "c": 0.02}
DEFAULTS = {"rho": 0.1, "delta": 0.5, "tau": 0.6, "lam": 0.02, "f1": 1.0, "f2": 1.0, "noise": 0.5,
            "act": {a: dict(_EFF) for a in ACTIONS}}
DEFAULTS["act"]["NONE"] = {k: 0.0 for k in _EFF}


def targets(profile: dict) -> tuple[list, str]:
    """§6 targets rule. Returns (levels, which rule applied)."""
    des = profile.get("desired") or {}
    agreed = [lv for lv in S.LEVEL_IDS if any(it.get("agreed") for it in des.get(lv, []))]
    if agreed:
        return agreed, "desired_agreed"
    anyd = [lv for lv in S.LEVEL_IDS if des.get(lv)]
    if anyd:
        return anyd, "desired_any"
    cur = [lv for lv in S.LEVEL_IDS if (profile.get("current") or {}).get(lv)]
    if cur:
        return cur, "current"
    return ["behaviour"], "default"


def _clip(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


class ProfilePerson:
    def __init__(self, profile: dict, params: dict | None = None, seed: int = 0, initial_intensity: float | None = None):
        self.profile = profile
        self.P = copy.deepcopy(params or DEFAULTS)
        self.rng = random.Random(seed)
        self.targets, self.target_rule = targets(profile)
        n_sig = min(4, len(profile.get("signals") or []))
        self.rho = self.P["rho"] * (1 + 0.25 * n_sig)
        self.skill = 1.25 if (profile.get("levels") or {}).get("skills", {}).get("statements") else 1.0
        I0 = initial_intensity if initial_intensity is not None else float(profile.get("initial_intensity", 3))
        self.I = _clip(float(I0), 1.0, 5.0)
        self.u = (self.I - 1) / 4
        self.k = 0.0
        self.g = 0.0
        self.t = 0
        self.cues = 0
        self.history: list[dict] = []

    def step(self, action: str) -> dict:
        assert action in ACTIONS, action
        P, a = self.P, self.P["act"][action]
        I0, g0 = self.I, self.g
        cue = self.rng.random() < self.rho
        if cue:
            self.cues += 1
            self.I = _clip(self.I + P["delta"], 1, 5)
            self.u = _clip(self.u + P["delta"] / 4, 0, 1)
        I_after_cue = self.I
        self.I = _clip(self.I - a["r"], 1, 5)
        self.u = _clip(self.u - a["m"], 0, 1)
        self.k = _clip(self.k + a["e"], 0, 1)
        if self.u < P["tau"]:
            self.g = _clip(self.g + a["p"] * (0.5 + self.k) * self.skill, 0, 1)
        else:
            self.u = _clip(self.u + a["c"], 0, 1)
        self.I = _clip(self.I - P["lam"] * (self.I - 1), 1, 5)
        relief = I_after_cue - self.I
        progress = self.g - g0
        fb = round(_clip(3 + P["f1"] * relief + P["f2"] * progress + self.rng.gauss(0, P["noise"]), 1, 5))
        spike = (self.I - I0) > 1
        out = {"t": self.t, "action": action, "cue": cue, "I": self.I, "u": self.u, "k": self.k, "g": self.g,
               "relief": relief, "progress": progress, "feedback": fb, "score": relief + progress - (1.0 if spike else 0.0)}
        self.t += 1
        self.history.append(out)
        return out
