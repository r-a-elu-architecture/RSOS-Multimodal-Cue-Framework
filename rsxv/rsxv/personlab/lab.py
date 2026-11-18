"""PERSONLAB §7d C: the Person Lab session engine (architecture, not a test).

Agents work on a lab person toward its desired state. The person is step 4's ProfilePerson, unchanged, with its
random source replaced by mulberry32 so the browser (docs/js/personlab.js) gives identical runs.

    python -m rsxv.personlab.lab ../docs/data/personlab_persons.json ../docs/data/personlab_lab.json
"""
from __future__ import annotations

import copy
import json
import math
import sys

from . import person as PS
from . import schema as S
from .. import lang as L

M32 = 0xFFFFFFFF
TICKS = 20
SEED0 = 5000
POLICIES = ("agents", "always_bear", "no_support")
ARCH = {"STABILISE": "BEAR", "EXPLORE": "RAVEN", "SUGGEST": "TIGER", "SHARE": "LION", "NONE": None}

EFFECTS = {
    "placeholder": copy.deepcopy(PS.DEFAULTS["act"]),
    # Invented to show the architecture working; untested (spec §7d C).
    "illustrative": {
        "STABILISE": {"r": 0.35, "m": 0.08, "e": 0.02, "p": 0.01, "c": 0.0},
        "EXPLORE": {"r": 0.05, "m": 0.0, "e": 0.15, "p": 0.02, "c": 0.04},
        "SUGGEST": {"r": 0.10, "m": 0.01, "e": 0.03, "p": 0.08, "c": 0.05},
        "SHARE": {"r": 0.15, "m": 0.03, "e": 0.05, "p": 0.03, "c": 0.02},
        "NONE": {"r": 0.0, "m": 0.0, "e": 0.0, "p": 0.0, "c": 0.0},
    },
}

_HEAD = 'RSX-V TIER 0 :: {{{arch}}} :: ({mode})\nINTENT "{intent}"\nTARGET {{target}}\nSENSE HRV\nLAWS ConsentStack ChronoGate\nLEVEL self_guided\n@Vector0:NullSafe\nGATE\n  @Vector7:EthicsContain(CONTAIN)\n  @Vector13:SymbolicDriftCheck\n'
_TAIL = "CLOSE\n  @Vector15:MemoryUpdate(MEMSTACK)\n  @Vector17:EchoPropagationStop\n  @Vector16:SymbolicCommandExport(RSX) -> NEXT\n"
PROGRAMS = {
    "STABILISE": _HEAD.format(arch="BEAR", mode="STABILISE", intent="steady the person before any change")
    + "PHASE settle UNTIL arousal<=0.6 MAX 90s\n  @Vector3:BreathOverride(6/min)\n  @Vector4:PostureShift\n  @Vector6:EmotionalLock(Calm)\n" + _TAIL,
    "EXPLORE": _HEAD.format(arch="RAVEN", mode="EXPLORE", intent="see the target clearly")
    + "PHASE explore IF arousal<=0.6 MAX 60s\n  @Vector5:MemoryRecall(Archetype=RAVEN)\n  @Vector18:AssociativeExpand(RAVEN, 5)\n  @Vector19:MetaObserve\n" + _TAIL,
    "SUGGEST": _HEAD.format(arch="TIGER", mode="SUGGEST", intent="one step toward the desired state")
    + "PHASE step IF arousal<=0.6 MAX 60s\n  @Vector9:FutureProjection(1Week)\n  @Vector8:CompressionRun(CM1)\n  @Vector1:IdentityRebuild\n" + _TAIL,
    "SHARE": _HEAD.format(arch="LION", mode="SHARE", intent="share a steady example")
    + "PHASE share IF arousal<=0.6 MAX 60s\n  @Vector10:ArchetypeMerge(LION+BEAR)\n  @Vector9:FutureProjection(3Months)\n  @Vector19:MetaObserve\n" + _TAIL,
}


class Mulberry32:
    """Seeded uniforms and normals, identical to docs/js/personlab.js."""

    def __init__(self, seed: int):
        self.a = seed & M32

    def random(self) -> float:
        self.a = (self.a + 0x6D2B79F5) & M32
        t = self.a
        t = ((t ^ (t >> 15)) * (t | 1)) & M32
        t ^= (t + (((t ^ (t >> 7)) * (t | 61)) & M32)) & M32
        return ((t ^ (t >> 14)) & M32) / 4294967296

    def gauss(self, mu: float, sigma: float) -> float:
        u1 = 1.0 - self.random()
        u2 = self.random()
        return mu + sigma * math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)


def target_nodes(p: dict) -> list:
    """The desired nodes the agents work on, in order: step 4's targets rule, then the nodes of those items."""
    lvls, _ = PS.targets(p)
    out = []
    for lv in lvls:
        for part in ("desired", "current"):
            for it in (p.get(part) or {}).get(lv, []):
                if it.get("node") and (lv, it["node"]) not in out:
                    out.append((lv, it["node"]))
        if not any(x[0] == lv for x in out):
            sts = (p.get("levels") or {}).get(lv, {}).get("statements", [])
            out.append((lv, sts[0]["id"] if sts else "all"))
    return out


def node_text(p: dict, lv: str, node: str) -> str:
    for st in (p.get("levels") or {}).get(lv, {}).get("statements", []):
        if st["id"] == node:
            return st["text"]
    return ""


def session(p: dict, number: int, policy: str = "agents", effects: str = "placeholder", ticks: int = TICKS) -> dict:
    params = copy.deepcopy(PS.DEFAULTS)
    params["act"] = copy.deepcopy(EFFECTS[effects])
    person = PS.ProfilePerson(p, params, seed=0, initial_intensity=p["initial_intensity"])
    person.rng = Mulberry32(SEED0 + number)
    tg = target_nodes(p)
    ti, calm = 0, 0
    rows = []
    for _ in range(ticks):
        if policy == "no_support":
            action = "NONE"
        elif policy == "always_bear":
            action = "STABILISE"
        else:
            if person.u >= params["tau"]:
                action = "STABILISE"
            else:
                calm += 1
                action = "SHARE" if calm % 6 == 0 else ("EXPLORE" if person.k < 0.5 else "SUGGEST")
        lv, node = tg[ti % len(tg)] if policy == "agents" else tg[0]
        I_before = person.I
        o = person.step(action)
        rows.append({"t": o["t"], "action": action, "archetype": ARCH[action],
                     "target": None if action == "NONE" else f"{lv}:{node}", "cue": o["cue"],
                     "I": round(o["I"], 6), "u": round(o["u"], 6), "k": round(o["k"], 6), "g": round(o["g"], 6),
                     "feedback": o["feedback"], "score": round(o["score"], 6), "spike": (o["I"] - I_before) > 1})
        if policy == "agents" and action == "SUGGEST":
            ti += 1
    return {"id": p["id"], "policy": policy, "effects": effects, "ticks": rows,
            "final_I": rows[-1]["I"], "final_g": rows[-1]["g"], "spikes": sum(r["spike"] for r in rows),
            "mean_score": round(sum(r["score"] for r in rows) / len(rows), 6)}


def program(action: str, target: str) -> str:
    return PROGRAMS[action].replace("{target}", target)


def population(persons: list) -> dict:
    out = {}
    for eff in EFFECTS:
        runs = {pol: [session(p, n + 1, pol, eff) for n, p in enumerate(persons)] for pol in POLICIES}
        summ = {}
        for pol, rs in runs.items():
            n = len(rs)
            summ[pol] = {"mean_final_I": round(sum(r["final_I"] for r in rs) / n, 4),
                         "mean_final_g": round(sum(r["final_g"] for r in rs) / n, 4),
                         "mean_spikes": round(sum(r["spikes"] for r in rs) / n, 4),
                         "mean_score": round(sum(r["mean_score"] for r in rs) / n, 4)}
        a, b = runs["agents"], runs["always_bear"]
        summ["agents_vs_bear"] = {"more_progress": sum(x["final_g"] > y["final_g"] + 1e-9 for x, y in zip(a, b)),
                                  "same": sum(abs(x["final_g"] - y["final_g"]) <= 1e-9 for x, y in zip(a, b)),
                                  "less_progress": sum(x["final_g"] < y["final_g"] - 1e-9 for x, y in zip(a, b))}
        out[eff] = summ
    return out


def build(lab_persons: dict) -> dict:
    persons = lab_persons["persons"]
    return {"spec": "spec/PERSONLAB.md §7d C", "ticks": TICKS, "seed0": SEED0, "policies": list(POLICIES),
            "tau": PS.DEFAULTS["tau"], "defaults": {k: v for k, v in PS.DEFAULTS.items() if k != "act"},
            "effects": EFFECTS, "archetypes": ARCH, "programs": PROGRAMS, "levels": S.LEVELS,
            "population": population(persons),
            "note": "Architecture, not evidence. The person model failed validation (PERSONLAB step 5). 'placeholder' are "
                    "step 4's registered equal effects; 'illustrative' effects are invented and untested."}


def main(src: str, out: str):
    data = build(json.load(open(src, encoding="utf-8")))
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(json.dumps(data["population"]))


if __name__ == "__main__":
    main(*sys.argv[1:3])
