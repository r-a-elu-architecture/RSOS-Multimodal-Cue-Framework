"""Simulated person and sensors for RSX/2 ghost passes and arm comparisons.

Everything here is a stated model, not data. The four assumptions can be
switched off one by one (MODEL flags) so a result can be traced to the
assumption that produces it:
  dilution   attention is shared: n concurrent content vectors each get 1/sqrt(n)
  readiness  deep layers (C3 C4 C5 C7 C10 C11) work only as arousal falls below ~0.7
  backfire   deep work under high arousal raises distress
  conflict   the listed conflicting pairs halve each other and add distress
"""
from __future__ import annotations
import math
import random
from . import ops as O

FULL = {"dilution": True, "readiness": True, "backfire": True, "conflict": True}
NEUTRAL = {"dilution": False, "readiness": False, "backfire": False, "conflict": False}


def person(rng: random.Random, pid: int) -> dict:
    a = rng.uniform(0.35, 0.80)
    return {"id": pid, "resp": math.exp(rng.gauss(0, 0.3)), "sham": rng.uniform(0.0, 0.3),
            "peak_hour": rng.choice([8, 11, 14, 17, 20]), "retain": rng.uniform(0.3, 0.8),
            "base": {"arousal": a, "distress": round(2 + 6 * a + rng.gauss(0, 0.8), 2),
                     "agency": rng.uniform(3, 6), "drift": rng.uniform(0.1, 0.3)}}


def perturb(p: dict, rng: random.Random) -> dict:
    q = {**p, "resp": p["resp"] * math.exp(rng.gauss(0, 0.25)), "base": dict(p["base"])}
    q["base"]["arousal"] = min(0.95, max(0.1, q["base"]["arousal"] + rng.gauss(0, 0.08)))
    return q


def hour_factor(p: dict, hour) -> float:
    """Assumption 5 (circadian): responsiveness peaks at the person's peak hour, down to 0.6 six hours away."""
    if hour is None or "peak_hour" not in p:
        return 1.0
    d = min(abs(hour - p["peak_hour"]), 24 - abs(hour - p["peak_hour"]))
    return max(0.6, 1.0 - 0.4 * min(d, 6) / 6)


def carry(p: dict, end: dict) -> dict:
    """Assumption 6 (carry-over): the next session starts from this one's end, decayed toward the original baseline."""
    q = {**p, "base": dict(p["base"])}
    r = p.get("retain", 0.5)
    orig = p.get("orig", p["base"])
    q["orig"] = orig
    for k in ("arousal", "distress", "agency", "drift"):
        q["base"][k] = orig[k] + r * (end[k] - orig[k])
    return q


class Body:
    def __init__(self, p, rng, model=None, sham=False):
        self.p, self.rng, self.m, self.sham = p, rng, dict(FULL if model is None else model), sham
        self.hf = 1.0
        self.s = dict(p["base"])
        self.s["distress"] = min(10, max(0, self.s["distress"]))
        self.layer = {c: 0.0 for c in O.LAYERS}
        self.t = 0

    def read(self):
        a = self.s["arousal"]; r = self.rng
        return {"arousal": a, "distress": self.s["distress"], "agency": self.s["agency"], "drift": self.s["drift"],
                "hrv": 75 - 50 * a + r.gauss(0, 2), "alpha": 0.25 + 0.4 * (1 - a) + r.gauss(0, 0.02)}

    def step(self, active: list[str]) -> dict:
        """One second with these operators active; returns each operator's contribution."""
        s, m = self.s, self.m
        content = [o for o in active if O.OPS[o][0] not in ("safety", "export")]
        att = 1 / math.sqrt(len(content)) if (m["dilution"] and content) else 1.0
        contrib = {}
        names = set(active)
        for o in active:
            fam, tgt, _, eff, _ = O.OPS[o]
            g = 0.0 if self.sham else self.p["resp"] * self.hf * (att if o in content else 1.0)
            d = {}
            if tgt in O.DEEP:
                if m["readiness"]:
                    g *= max(0.0, min(1.0, (0.75 - s["arousal"]) / 0.35))
                if m["backfire"] and s["arousal"] > 0.6 and not self.sham:
                    d["distress"] = d.get("distress", 0) + 0.02 * (s["arousal"] - 0.6) / 0.4
            if m["conflict"]:
                for pair in O.CONFLICTS:
                    if o in pair and pair <= names:
                        g *= 0.5
                        if not self.sham:
                            d["distress"] = d.get("distress", 0) + 0.004
            for k, v in eff.items():
                d[k] = d.get(k, 0) + v * g
            for k, v in d.items():
                if k == "layer":
                    if tgt in self.layer:
                        self.layer[tgt] = min(1.0, self.layer[tgt] + v)
                elif k.startswith("layer_"):
                    c = k[6:]; self.layer[c] = min(1.0, self.layer[c] + v)
                else:
                    s[k] += v
            contrib[o] = d
        # placebo, regression to baseline, noise
        b = self.p["base"]
        s["distress"] -= 0.006 * self.p["sham"] * (1 if active else 0)
        s["arousal"] -= 0.002 * self.p["sham"] * (1 if active else 0)
        s["arousal"] += 0.004 * (b["arousal"] - s["arousal"]) + self.rng.gauss(0, 0.003)
        s["distress"] += self.rng.gauss(0, 0.03)
        s["arousal"] = min(1, max(0, s["arousal"])); s["distress"] = min(10, max(0, s["distress"]))
        s["agency"] = min(10, max(0, s["agency"])); s["drift"] = min(1, max(0, s["drift"]))
        self.t += 1
        return contrib
