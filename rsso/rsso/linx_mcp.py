"""LINX for AI assistants: the planner as a propose-only, gated tool (spec/LINX_MCP.md; NODES.md §9).

The assistant proposes; the planner computes; the session check gates; the person approves.

  propose_plan(intake, check)   the assistant's proposal -> computed fields removed -> session check -> plan or pause
  session_check(answers)        the structured self-check alone (safety.event_from_check -> observe -> allowed)
  check_frame(text, mode, believability)   nodes.frame_check
  tacton(code)                  the pulse pattern of a vibration code

Pure functions: no network, no model client. mcp_server.py exposes them over the Model Context Protocol.
"""
from __future__ import annotations

import copy
import re

from . import nodes, safety

# What the assistant may propose. Everything else is computed by the planner or chosen by the person in the app.
INTAKE_FIELDS = ("person", "author", "concerns", "symptoms", "triggers", "nodes", "dose", "devices", "physiology",
                 "inhale", "exhale")
NODE_FIELDS = ("archetype", "name", "state", "mode", "representation", "V", "A", "K", "O", "G", "frames", "contexts",
               "rules", "believability")
CODE = re.compile(r"^[.\-]{1,6}( [.\-]{1,6})*$")
PROPOSAL = ("A proposal only: the person, or the person and their practitioner, reviews and approves it in the app "
            "before any practice. Vibration codes, programs, tiers, metrics, schedule and safety notes are computed "
            "by the planner (rsos-planner/1), not by the assistant.")


def _list(v):
    return [str(x) for x in v] if isinstance(v, list) else ([str(v)] if isinstance(v, str) and v.strip() else [])


def sanitise(intake: dict | None) -> dict:
    """Keep only what the assistant may propose, with safe types."""
    src = intake if isinstance(intake, dict) else {}
    out = {k: copy.deepcopy(src[k]) for k in INTAKE_FIELDS if k in src}
    for k in ("concerns", "triggers"):
        if k in out:
            out[k] = _list(out[k])
    for k in ("dose", "devices", "physiology"):
        if k in out and not isinstance(out[k], dict):
            out.pop(k)
    if "dose" in out:
        d = {}
        for k in ("per_day", "days"):
            v = out["dose"].get(k)
            if isinstance(v, (int, float)) and not isinstance(v, bool) and 0 <= v <= 1000:
                d[k] = int(v)
        out["dose"] = d
    for k in ("inhale", "exhale"):
        v = out.get(k)
        if not (isinstance(v, int) and not isinstance(v, bool) and 1 <= v <= 20):
            out.pop(k, None)
    for k in ("person", "author", "symptoms"):
        if k in out:
            out[k] = str(out[k])
    raw_nodes = out.get("nodes") if isinstance(out.get("nodes"), list) else []
    clean = []
    for raw in raw_nodes[:12]:
        if not isinstance(raw, dict):
            continue
        n = {k: copy.deepcopy(raw[k]) for k in NODE_FIELDS if k in raw}
        for k in ("frames", "contexts", "rules"):
            if k in n:
                n[k] = _list(n[k])
        for k in ("archetype", "name", "state", "mode", "representation", "V", "A", "K", "O", "G"):
            if k in n:
                n[k] = str(n[k])
        if n.get("mode") not in (None, "associated", "observer"):
            n.pop("mode")
        b = n.get("believability")
        if b is not None and not (isinstance(b, (int, float)) and not isinstance(b, bool) and 0 <= b <= 10):
            n.pop("believability")
        clean.append(n)
    if "nodes" in out:
        out["nodes"] = clean
    return out


MEDICATION = ("none", "non_sedative", "sedative", "unsure")
SUBSTANCES = ("no", "yes", "unsure")


def event(answers: dict | None) -> dict:
    """The safety module's event from the check. v2 (§6): finer `medication` and `substances` answers fill the module's
    own fields; an unknown value counts as unsure; the old `flags` keep their meaning (either source raises a field)."""
    a = answers if isinstance(answers, dict) else {}
    ev = safety.event_from_check(a)
    if "medication" in a:
        med = a["medication"] if a["medication"] in MEDICATION else "unsure"
        ev["sedative_prescribed"] = bool(ev.get("sedative_prescribed")) or med in ("sedative", "unsure")
    if "substances" in a:
        sub = a["substances"] if a["substances"] in SUBSTANCES else "unsure"
        ev["substances"] = bool(ev.get("substances")) or sub in ("yes", "unsure")
    return ev


def allowed_now(mode_key: str) -> dict:
    cats = sorted(safety.MODE_ALLOWED[mode_key])
    return {"categories": cats, "regulation_programs": list(safety.REGULATING) if "regulating_cue" in cats else []}


def _gate(answers):
    state, res = safety.observe(safety.new_state(), event(answers))
    ok = safety.allowed(state, {"kind": "plan"})
    return {"plan_allowed": ok["ok"], "mode": safety.MODE_NAME[state["mode"]], "mode_text": safety.MODE_TEXT[state["mode"]],
            "screens": res["screens"], "actions": res["actions"], "messages": res["messages"],
            "allowed_now": allowed_now(state["mode"])}


def session_check(answers: dict | None) -> dict:
    """The structured self-check: {intensity 0-10, sleep_h, clinical_result none|low|moderate|high (entered by the
    practitioner), medication none|non_sedative|sedative|unsure, substances no|yes|unsure, flags [medication,
    practical], history bool} -> mode, screens, fixed messages, whether a plan may be built, what is allowed now."""
    return _gate(answers)


def summary(p: dict) -> dict:
    """The compact plan for the assistant (§6): every node's name, mode, code, frames and contexts; frame tips only where
    flagged; tiers; one line per schedule phase; every safety line in full."""
    def fr(text, fc):
        d = {"text": text, "score": fc["score"]}
        if fc["flags"]:
            d.update(flags=fc["flags"], tips=fc["tips"])
        return d
    return {"planner": p["planner"], "detail": "summary",
            "nodes": [{"name": n["name"], "mode": n["mode"], "tacton": n["tacton"],
                       "frames": [fr(t, fc) for t, fc in zip(n["frames"], n["frame_checks"])],
                       "contexts": n["contexts"]} for n in p["nodes"]],
            "tiers": p["tiers"],
            "schedule": [f"{x['phase']}: {x['per_day']} a day for {x['days']} days" if x["per_day"] else x["phase"]
                         for x in p["schedule"]],
            "safety": p["safety"], "therapist_led": p["therapist_led"], "approved": False}


def propose_plan(intake: dict | None, check: dict | None, detail: str = "summary") -> dict:
    """Gate first, then plan. The plan is never approved here. detail: summary (default) or full."""
    gate = _gate(check)
    if not gate["plan_allowed"]:
        return {"plan": None, **gate, "note": "No plan is built in this session state."}
    p = nodes.plan(sanitise(intake))
    p["approved"] = False
    return {"plan": p if detail == "full" else summary(p), **gate, "note": PROPOSAL}


def check_frame(text: str, mode: str = "associated", believability=None) -> dict:
    mode = mode if mode in ("associated", "observer") else "associated"
    b = believability if isinstance(believability, (int, float)) and not isinstance(believability, bool) else None
    return nodes.frame_check(str(text), mode, b)


def tacton(code: str) -> dict:
    code = str(code).strip()
    if not CODE.match(code):
        return {"code": code, "valid": False, "pulses": [],
                "rule": "Symbols . (100 ms) and - (300 ms), 1-6 per code; a space joins codes with a 400 ms pause."}
    return {"code": code, "valid": True, "pulses": nodes.tacton_pulses(code)}


INTAKE_PROMPT = """You are filling an RSOS intake with a person (or with a practitioner on their behalf). RSOS is a
research and development framework for practising desired states with cues on every sense; it is not a medical device.

How to work:
1. Ask first, in plain language, the short self-check: intensity right now (0-10), hours of sleep last night, any
   medication (none, non-sedative, sedative, unsure), alcohol or other substances now (no, yes, unsure), whether
   practical circumstances (work, housing, income) are a concern right now, and whether there is earlier experience the
   practitioner should know about. A screening result (none, low, moderate, high) is entered only by a practitioner
   from their own validated instrument; never estimate it.
2. Then help the person describe what they want to practise: the states they want (courage, calm, focus, the observer
   position), the situations where they will use them (up to 3 per state), and the cues on each sense: what they see,
   hear, feel in the body, smell and taste.
3. Suggest frames (up to 5 per state): short, present tense, process words (I breathe, I see, I move), broad and
   believable.
4. Propose only. Never write vibration codes, pulse patterns, programs, tiers, metrics, schedules or safety notes: the
   planner computes them. Make one propose_plan call with the intake and the self-check answers; the reply carries
   the frame checks, so offer their tips from it. Use detail "full" only when the person or practitioner asks for the
   complete programs.
5. If propose_plan returns no plan, read its messages to the person as they are, offer only what allowed_now lists
   (for example a regulation program), and do not build a plan another way.
6. The plan is a proposal. Say that the person, or the person and their practitioner, approves it before practice.
   Work with difficult memories, depression or trauma is led by a qualified practitioner.
"""
