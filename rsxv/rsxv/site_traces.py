"""Recorded runs for the website's live world (docs/world.html). Real runs of the tested code: an agent system
(AgentEnvV2) and a simulated person (PersonEnvV2), each driven by its own World under the Watchdog (mission score),
recorded tick by tick. Interventions: a storm (agent fault rate 0.35; a cue reaches the person at its start and the
person's trigger rate is 0.40, for 20 ticks) or a
shift (silent agent faults 0.9 and person medication off) at a chosen tick.

    python3 -m rsxv.site_traces ../docs/data/world_runs.json
"""
from __future__ import annotations

import json
import sys

from . import archetypes as A
from .person2 import PersonEnvV2
from .world import AgentEnvV2, World

TICKS = 160
SEEDS = (11, 12, 13)
EVENTS = (None, "storm", "shift")
TIMES = (40, 90)


def run(seed, event, t0):
    ae = AgentEnvV2(seed, fault_rate=0.15, silent_share=0.5)
    pe = PersonEnvV2(seed + 500, med_on=(event == "shift"), trig_rate=0.15)
    wa = World(ae, policy="watchdog", seed=seed, score="mission")
    wp = World(pe, policy="watchdog", seed=seed + 500, score="mission")
    ticks = []
    seen_a = seen_p = 0
    for t in range(1, TICKS + 1):
        if event == "storm":
            on = t0 <= t < t0 + 20
            ae.fault_rate = 0.35 if on else 0.15
            pe.trig_rate = 0.40 if on else 0.15
            if t == t0 and pe.open is None:
                pe._trigger()                                   # a cue arrives at the storm's start
        elif event == "shift" and t == t0:
            ae.silent_share = 0.9
            pe.med_on = False
        b0 = getattr(wp, "safety_blocks", 0)
        ra = wa.tick(); rp = wp.tick()
        errs = ae.sys.errors()
        la = wa.lineage.edges[seen_a:]
        lp = wp.lineage.edges[seen_p:]
        seen_a += len(la); seen_p += len(lp)
        s = pe.body.s
        ticks.append({
            "a": {"ctx": ra["ctx"], "act": ra["action"], "mode": ra["mode"], "r": round(ra["reward"], 3),
                  "err": {k: round(v, 3) for k, v in errs.items()}, "health": round(ae.sys.health(), 3),
                  "p": round(getattr(ae, "P", 0.0), 3),
                  "lin": [[e["kind"], e["from"], e["to"], e["rationale"]] for e in la]},
            "p": {"ctx": rp["ctx"], "act": rp["action"], "mode": rp["mode"], "r": round(rp["reward"], 3),
                  "d": round(s["distress"], 2), "u": round(s["arousal"], 3), "g": round(s["agency"], 2),
                  "safe": pe.safety.mode if pe.safety else "NORMAL",
                  "trig": bool(pe.events and pe.events[-1]["t"] == pe.ticks),
                  "lin": [[e["kind"], e["from"], e["to"], e["rationale"]] for e in lp],
                  "blk": getattr(wp, "safety_blocks", 0) - b0}})
    blocks = getattr(wp, "safety_blocks", 0)
    return {"seed": seed, "event": event, "t0": t0, "ticks": ticks,
            "summary": {"agent_mean": sum(wa.rewards) / TICKS, "person_mean": sum(wp.rewards) / TICKS,
                        "agent_switches": wa.switches, "person_switches": wp.switches, "safety_blocks": blocks}}


def main(out):
    runs = []
    for seed in SEEDS:
        for ev in EVENTS:
            for t0 in (TIMES if ev else (0,)):
                runs.append(run(seed, ev, t0))
    data = {"graph": A.GRAPH, "ticks": TICKS, "runs": runs,
            "note": "Recorded runs of the tested rsxv code (AgentEnvV2, PersonEnvV2, World with the Watchdog). Stated models, not data about people."}
    open(out, "w").write(json.dumps(data, separators=(",", ":")))
    print(len(runs), "runs")


if __name__ == "__main__":
    main(sys.argv[1])
