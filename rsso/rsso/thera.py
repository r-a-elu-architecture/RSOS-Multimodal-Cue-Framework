"""THERA — therapist mode and session protocols (spec/THERA.md).

Recovered role (archive, THERA_Historical_Reconstruction): the therapeutic branch, "Therapy Protocol Deployment
Engine", with the operators IdentityRebuild, BreathOverride, EmotionalLock, VIB-ANCHOR and FP-ANCHOR, a human in
the loop and the safety envelope; protocol design survives, no validated clinical algorithm. Here it is built as
structured, measured sessions a therapist runs with a client, using the client's node plan:

  PROTOCOLS                 five session protocols as data (docs/data/thera.json): stress, boundaries, habits,
                            low mood and therapist-led observer work with a memory
  session_plan(id, plan)    the session's steps with the client's own nodes and programs filled in
  check(session)            the stop rules: screening, distress ceilings, return to breath, end and refer
  summary(session, runs)    minutes, fidelity, distress and agency from start to end, peak, anchors practised,
                            adverse events, and the session as a research contribution record
  homework(plan, session)   practice between sessions, from the plan and what worked in the session

docs/js/thera.js is identical (tested). RSOS supports the therapist's work; it does not diagnose or treat.
"""
from __future__ import annotations

import json
import math

FORMAT = "rsos-thera/1"
OPEN = [
    {"id": "open", "title": "Check in", "op": "EthicsContain", "minutes": 5, "required": True, "measure": ["sud", "agency"],
     "say": "How are you right now, from 0 (calm) to 10 (the most distress)? And how able do you feel to act, from 0 to 10?",
     "do": "Agree what today's session is for. Confirm consent for every node and cue you will use."},
]
SCREEN = {"id": "screen", "title": "Screening", "op": "EthicsContain", "minutes": 1, "required": True, "measure": ["screen"],
          "say": "Right now, are you in crisis, or having thoughts of harming yourself or not wanting to live?",
          "do": "If the answer is yes, stop the session work and follow your crisis procedure."}
BREATH = {"id": "breath", "title": "Paced breathing", "op": "BreathOverride", "minutes": 3, "required": True, "measure": ["sud"],
          "run": "program:paced_breathing",
          "say": "Breathe with the light: in for four, out for six. Let the exhale be longer.",
          "do": "Run paced breathing in the player; rate distress after it."}
INSTALL = {"id": "install", "title": "Build the node", "op": "IdentityRebuild", "minutes": 10, "required": True, "measure": ["believability"],
           "say": "Picture the {node}: what you see, hear, feel, smell and taste in that state. Say the frame aloud: “{frame}”.",
           "do": "Review the node with the client: senses, frame, glyph and vibration code. Rate how believable the frame is (0–10); reword it if it is below 6."}
ANCHOR = {"id": "anchor", "title": "Anchor the state", "op": "EmotionalLock", "minutes": 8, "required": True, "measure": ["sud", "agency"], "repeat": 3,
          "run": "node:0",
          "say": "Go fully into the state. At its peak, feel the code on your wrist: {code}.",
          "do": "Run the node three times in the player (VIB-ANCHOR at the peak). Rate distress and agency after each run."}
FUTURE = {"id": "future", "title": "Future pacing", "op": "FP-ANCHOR", "minutes": 5, "required": False, "measure": ["agency"],
          "run": "node:0",
          "say": "See yourself in {contexts}, with the {node} already in you, acting as you want to.",
          "do": "Run the node's futures (FP-ANCHOR, 150 ms × 8). Rate agency."}
HOMEWORK = {"id": "homework", "title": "Practice between sessions", "op": "VIB-ANCHOR", "minutes": 3, "required": True, "measure": [],
            "say": "Between now and next time, start the {node} when this happens: {trigger}. And practise it {dose}.",
            "do": "Agree the practice plan; the player records every run and the weekly automaticity check."}
CLOSE = {"id": "close", "title": "Close", "op": "EthicsContain", "minutes": 5, "required": True, "measure": ["sud", "agency", "adverse", "cgi_s", "cgi_i", "engagement"],
         "say": "Notice your feet on the floor and your breath. How are you now, 0 to 10? Did anything feel unpleasant today?",
         "do": "Rate distress and agency. Record any unpleasant event. Therapist: rate severity (CGI-S), improvement (CGI-I) and engagement."}


def _s(base: dict, **kw) -> dict:
    d = dict(base)
    d.update(kw)
    return d


PROTOCOLS = {
    "stress": {"title": "Stress and chronic stress", "for": ["stress", "chronic_stress", "anxiety"], "therapist_led": False, "stop_sud": 9,
               "aim": "A calm, able state the client can start in seconds when stress begins.",
               "steps": [OPEN[0], BREATH, INSTALL, ANCHOR,
                         _s(ANCHOR, id="test", title="Rehearse a trigger", op="EmotionalLock", repeat=2, minutes=8,
                            say="Bring to mind a moment of this: {trigger}. Only up to a 5 of 10. Then start the {node}.",
                            do="Imagined trigger at moderate intensity, then the node. Rate distress before and after. Stop and return to breathing above the session's distress ceiling."),
                         FUTURE, HOMEWORK, CLOSE]},
    "boundaries": {"title": "Confidence and boundaries", "for": ["confidence"], "therapist_led": False, "stop_sud": 9,
                   "aim": "Saying no and holding ground with calm confidence.",
                   "steps": [OPEN[0], BREATH, INSTALL, ANCHOR,
                             _s(ANCHOR, id="test", title="Rehearse saying no", op="EmotionalLock", repeat=2, minutes=8,
                                say="Picture the moment you need to say no: {trigger}. Start the {node}, then say it aloud.",
                                do="Rehearse the boundary aloud with the node active. Rate distress and agency."),
                             FUTURE, HOMEWORK, CLOSE]},
    "habits": {"title": "Unwanted habits", "for": ["habits", "focus"], "therapist_led": False, "stop_sud": 9,
               "aim": "Replace the habit loop: trigger, then the node, then the chosen action.",
               "steps": [OPEN[0], INSTALL, ANCHOR,
                         _s(ANCHOR, id="test", title="Interrupt the loop", op="EmotionalLock", repeat=3, minutes=8,
                            say="The urge arrives: {trigger}. Start the {node}, and move straight into the action you choose.",
                            do="Rehearse trigger, node, new action three times. Rate the urge as distress (0–10)."),
                         FUTURE, HOMEWORK, CLOSE]},
    "low_mood": {"title": "Low mood", "for": ["depression"], "therapist_led": False, "stop_sud": 9, "screen": True,
                 "aim": "Small, planned actions started from an able state.",
                 "steps": [OPEN[0], SCREEN, BREATH, INSTALL, ANCHOR,
                           _s(FUTURE, id="action", title="Plan one small action", op="FP-ANCHOR", required=True, measure=["agency"],
                              say="Choose one small action for tomorrow. See yourself doing it with the {node} in you.",
                              do="Plan one concrete, small action with a time and place. Rate agency."),
                           HOMEWORK, CLOSE]},
    "trauma_observer": {"title": "A memory, observed (therapist-led)", "for": ["ptsd"], "therapist_led": True, "stop_sud": 8, "screen": True,
                        "aim": "A distressing memory observed from another position, where nothing binds, without reliving it.",
                        "steps": [OPEN[0], SCREEN, BREATH, _s(INSTALL, run="node:observer"),
                                  _s(ANCHOR, run="node:observer", title="Anchor the observer state"),
                                  _s(ANCHOR, id="observe", title="Observe the memory", op="IdentityRebuild", repeat=2, minutes=12, run="node:observer",
                                     say="From the observer position, let the memory play far away, small and still. Nothing binds; it is only observed.",
                                     do="Therapist-led. Rate distress during. At 8 or more: stop, return to breathing and grounding; do not continue the memory today."),
                                  _s(ANCHOR, id="return", title="Return to the able state", op="EmotionalLock", repeat=1, run="node:0",
                                     say="Come back fully into the room and into the {node}.", do="Run the client's associated node once."),
                                  HOMEWORK, CLOSE]},
}


def _nt(x: float) -> str:
    return str(int(x)) if float(x).is_integer() else str(x)


def _r1(x: float) -> float:
    return math.floor(x * 10 + 0.5) / 10


def _node_index(plan: dict, ref: str) -> int:
    nodes = (plan or {}).get("nodes") or []
    if ref == "node:observer":
        for i, n in enumerate(nodes):
            if n.get("mode") == "observer":
                return i
        return -1
    if ref.startswith("node:"):
        i = int(ref.split(":")[1])
        # node:0 means the first associated node when there is one
        assoc = [k for k, n in enumerate(nodes) if n.get("mode") != "observer"]
        return assoc[i] if i < len(assoc) else (i if i < len(nodes) else -1)
    return -1


def _fill(text: str, plan: dict, node: dict | None) -> str:
    it = (plan or {}).get("intake") or {}
    trig = it.get("triggers") or (plan or {}).get("triggers") or []
    sched = ((plan or {}).get("schedule") or [{}])[0]
    vals = {"node": (node or {}).get("name", "node").lower() if node else "node",
            "frame": ((node or {}).get("frames") or ["I breathe fully and completely"])[0],
            "code": (node or {}).get("tacton", "..-"),
            "contexts": ", ".join((node or {}).get("contexts") or []) or "the situations ahead",
            "trigger": (trig[0].lower() if trig else "the moment the old state begins"),
            "dose": f"{sched.get('per_day', 10)} times a day for {sched.get('days', 7)} days" if sched else "every day"}
    for k, v in vals.items():
        text = text.replace("{" + k + "}", v)
    return text


def session_plan(protocol_id: str, plan: dict | None = None) -> dict:
    """The steps of a session with the client's own nodes and programs filled in."""
    pr = PROTOCOLS[protocol_id]
    steps, problems = [], []
    for st in pr["steps"]:
        s = {k: v for k, v in st.items()}
        node = None
        run = st.get("run", "")
        if run.startswith("node:"):
            i = _node_index(plan, run)
            if i < 0:
                problems.append(f"{st['title']}: the plan has no " + ("observer node" if run == "node:observer" else "node") + "; add one in the node studio")
            else:
                node = plan["nodes"][i]
                s["program"] = f"plan:{i}"
                s["node"] = node.get("name")
        elif run.startswith("program:"):
            s["program"] = run.split(":")[1]
        if node is None and plan and plan.get("nodes"):
            j = _node_index(plan, "node:0")
            node = plan["nodes"][j] if j >= 0 else None
        s["say"] = _fill(st["say"], plan or {}, node)
        s["do"] = _fill(st["do"], plan or {}, node)
        s.pop("run", None)
        steps.append(s)
    return {"format": FORMAT, "protocol": protocol_id, "title": pr["title"], "aim": pr["aim"], "therapist_led": pr["therapist_led"],
            "stop_sud": pr["stop_sud"], "steps": steps, "problems": problems, "events": []}


def record(session: dict, step_id: str, values: dict, at: float) -> dict:
    """Add one measurement or completion to the session (returns a new session)."""
    s = json.loads(json.dumps(session))
    s["events"].append({"step": step_id, "at": at, **values})
    return s


def _sud_series(session: dict) -> list[tuple[str, float]]:
    return [(e["step"], float(e["sud"])) for e in session["events"] if e.get("sud") not in (None, "")]


def check(session: dict) -> list[dict]:
    """Stop rules, newest situation first: {level: stop | return | ok, text}."""
    out = []
    if any(e.get("screen") == "yes" for e in session["events"]):
        out.append({"level": "stop", "text": "The screening answer was yes: stop the session work, follow your crisis procedure, and do not start device practice."})
    series = _sud_series(session)
    if series and series[-1][1] >= session["stop_sud"]:
        out.append({"level": "return", "text": f"Distress is {_nt(series[-1][1])}, at or above this session's ceiling of {session['stop_sud']}: stop the current step, return to paced breathing and grounding, and continue only when it is below {session['stop_sud'] - 2}."})
    if any(e.get("adverse") in ("moderate", "serious") for e in session["events"]):
        out.append({"level": "stop", "text": "An adverse event was recorded: CONTAIN pauses the linked program until you restore it."})
    return out or [{"level": "ok", "text": "No stop rule applies."}]


def summary(session: dict, runs: list[dict] | None = None, started: float | None = None, ended: float | None = None) -> dict:
    """Minutes, fidelity, distress and agency, anchors practised, and the research-contribution session record."""
    ev = session["events"]
    done = {e["step"] for e in ev if e.get("done")}
    required = [s["id"] for s in session["steps"] if s.get("required")]
    fidelity = _r1(10 * sum(1 for r in required if r in done) / len(required)) if required else 0
    suds = [v for _, v in _sud_series(session)]
    ags = [float(e["agency"]) for e in ev if e.get("agency") not in (None, "")]
    t0 = started if started is not None else (ev[0]["at"] if ev else 0)
    t1 = ended if ended is not None else (ev[-1]["at"] if ev else t0)
    in_session = [r for r in runs or [] if t0 <= float(r.get("timestamp") or 0) <= t1 + 60]
    last = {}
    for e in ev:
        for k in ("cgi_s", "cgi_i", "engagement", "adverse"):
            if e.get(k) not in (None, ""):
                last[k] = e[k]
    out = {"protocol": session["protocol"], "minutes": max(1, math.floor((t1 - t0) / 60 + 0.5)) if ev else 0, "steps_done": len(done), "steps": len(session["steps"]),
           "fidelity": fidelity, "sud_start": suds[0] if suds else None, "sud_end": suds[-1] if suds else None,
           "sud_peak": max(suds) if suds else None, "sud_change": _r1(suds[-1] - suds[0]) if len(suds) >= 2 else None,
           "agency_change": _r1(ags[-1] - ags[0]) if len(ags) >= 2 else None, "runs": len(in_session),
           "nodes_used": len({r.get("protocol") for r in in_session if str(r.get("protocol") or "").startswith("node_")}),
           "adverse": last.get("adverse") or "none", "stops": [c["text"] for c in check(session) if c["level"] != "ok"]}
    out["record"] = {"ts": int(t0 * 1000), "minutes": out["minutes"], "nodes_used": out["nodes_used"], "fidelity": fidelity,
                     "engagement": last.get("engagement"), "cgi_s": last.get("cgi_s"), "cgi_i": last.get("cgi_i"),
                     "therapist_led": bool(session.get("therapist_led"))}
    return out


def homework(plan: dict | None, session: dict | None = None) -> list[str]:
    """Practice between sessions, in plain sentences."""
    plan = plan or {}
    nodes = plan.get("nodes") or []
    sched = (plan.get("schedule") or [{}])[0]
    it = plan.get("intake") or {}
    trig = it.get("triggers") or []
    out = []
    for n in nodes:
        if n.get("mode") == "observer":
            out.append(f"Use the {n.get('name', 'observer').lower()} node only as agreed in sessions" + (" (therapist-led work stays in sessions)." if (session or {}).get("therapist_led") else "."))
        else:
            out.append(f"Practise the {n.get('name', 'node').lower()} node {sched.get('per_day', 10)} times a day for {sched.get('days', 7)} days, spread over the day; its vibration code is {n.get('tacton', '')}.")
    if trig:
        out.append("Start the node when this happens: " + trig[0].lower() + ". Rate distress before and after in the player.")
    out.append("Fill in the weekly automaticity check in the player once a week.")
    out.append("If anything feels wrong, press “Something felt wrong” in the player; practice pauses until you have talked it through.")
    return out


def export() -> dict:
    return {"format": FORMAT, "protocols": PROTOCOLS}


def main():
    from .ledger import ROOT
    (ROOT / "docs" / "data" / "thera.json").write_text(json.dumps(export(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("docs/data/thera.json:", ", ".join(PROTOCOLS))


if __name__ == "__main__":
    main()
