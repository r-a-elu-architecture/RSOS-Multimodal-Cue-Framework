"""Machines and channels (spec/MACHINES.md).

CHANNELS
  device classes  the layer above any hardware: what a class can do and its safety envelope, including temperature,
                  posture, display (lock screen, smart glasses), vibration with a carrier frequency, several body
                  sites, and an implant class written as a specification only
  RDP/1.1 draft   the extra device-protocol lines for these channels, encoded and checked on the host side
  posture         slouching from a phone or wrist motion sensor (gravity angle with hysteresis), as a cue trigger
  body sites      anchors placed on parts of the body; a code spread over several motors

MACHINES
  agent identity  an AI agent or robot loads a profile in the same format as a person's: values with what each forbids
                  and prefers; every action is simulated against the values before it runs, overridden on a conflict
                  and logged; CONTAIN's rule that nothing starts by itself holds for agents too
  human signals   a person's error or stress signal after an agent's action marks the action's tags, and the agent
                  asks before doing such an action again
  glyph channel   an agent reports its state as a glyph's code on the person's wristband; the person replies with a code
  content packs   any rule set, value system or skill as a pack: rules become decision matrices for the copilot and
                  values for an agent or a person's profile

A seeded simulation with known answers checks the measures. docs/js/machines.js is identical (tested).
"""
from __future__ import annotations

import math
import sys

from . import peak as P

# ---------------------------------------------------------------- device classes and their envelope (items 9, 15, 29, 36, 38)

SITES = ("wrist_left", "wrist_right", "upper_arm", "chest", "upper_back", "ankle")
SITE_NAMES = {"wrist_left": "Left wrist", "wrist_right": "Right wrist", "upper_arm": "Upper arm", "chest": "Chest", "upper_back": "Upper back", "ankle": "Ankle"}
CLASSES = {
    "phone": {"title": "Phone", "channels": ["haptic", "sound", "display", "posture"], "built": True},
    "band": {"title": "Wristband", "channels": ["haptic"], "built": True},
    "scent": {"title": "Scent module", "channels": ["olfactory"], "built": True},
    "thermal": {"title": "Wrist cooling and warming", "channels": ["thermal"], "built": False},
    "multisite": {"title": "Motors on several body sites", "channels": ["haptic"], "built": False},
    "glasses": {"title": "Smart glasses", "channels": ["display", "sound"], "built": False},
    "headband": {"title": "Sleep or EEG headband", "channels": ["eeg", "sound"], "built": False},
    "implant": {"title": "Implanted device", "channels": [], "built": False, "spec_only": True,
                "note": "Specification only. RSOS programs, anchors and profiles sit above any hardware; an implant would need its own clinical and regulatory pathway, and nothing here drives one."},
}
ENVELOPE_X = {"thermal_delta_c_max": 4.0, "thermal_ms_max": 120000, "thermal_per_run": 4,
              "display_ms_max": 10000, "display_night_brightness_max": 0.2,
              "carrier_hz_min": 20, "carrier_hz_max": 300, "mod_hz_min": 1, "mod_hz_max": 40,
              "sites_at_once_max": 3, "haptic_amp_max": 0.6}


def encode(cmd: dict) -> str:
    """One RDP/1.1 draft line for a channel command."""
    k = cmd["kind"]
    if k == "thermal":
        return f"T {cmd['t']} {cmd['dur']} {_fmt(cmd['delta_c'])}"
    if k == "display":
        return f"D {cmd['t']} {cmd['dur']} {cmd['image']}"
    if k == "haptic":
        return f"HF {cmd['t']} {cmd['on']} {cmd['off']} {cmd['count']} {_fmt(cmd['amp'])} {cmd.get('carrier_hz', 0)} {cmd.get('mod_hz', 0)} {cmd.get('site', 'wrist_left')}"
    raise ValueError("unknown channel")


def _fmt(x):
    x = r2(float(x))
    return str(int(x)) if x.is_integer() else str(x)


def parse(line: str) -> dict:
    p = line.split()
    if not p:
        raise ValueError("empty line")
    if p[0] == "T" and len(p) == 4:
        return {"kind": "thermal", "t": int(p[1]), "dur": int(p[2]), "delta_c": float(p[3])}
    if p[0] == "D" and len(p) == 4:
        return {"kind": "display", "t": int(p[1]), "dur": int(p[2]), "image": p[3]}
    if p[0] == "HF" and len(p) == 9:
        return {"kind": "haptic", "t": int(p[1]), "on": int(p[2]), "off": int(p[3]), "count": int(p[4]), "amp": float(p[5]),
                "carrier_hz": int(p[6]), "mod_hz": int(p[7]), "site": p[8]}
    raise ValueError("not an RDP/1.1 channel line")


def check(cmd: dict, night=False, brightness=1.0) -> list:
    """Problems with a channel command against the extended envelope; an empty list means it may play."""
    E, out = ENVELOPE_X, []
    if cmd["kind"] == "thermal":
        if abs(cmd["delta_c"]) > E["thermal_delta_c_max"]:
            out.append(f"temperature change above {_fmt(E['thermal_delta_c_max'])} °C")
        if cmd["dur"] > E["thermal_ms_max"]:
            out.append("thermal cue longer than two minutes")
    elif cmd["kind"] == "display":
        if cmd["dur"] > E["display_ms_max"]:
            out.append("image shown longer than ten seconds")
        if night and brightness > E["display_night_brightness_max"]:
            out.append("too bright for the night")
    elif cmd["kind"] == "haptic":
        if cmd["amp"] > E["haptic_amp_max"]:
            out.append("vibration stronger than the envelope")
        c = cmd.get("carrier_hz", 0)
        if c and not (E["carrier_hz_min"] <= c <= E["carrier_hz_max"]):
            out.append("carrier outside 20-300 Hz")
        m = cmd.get("mod_hz", 0)
        if m and not (E["mod_hz_min"] <= m <= E["mod_hz_max"]):
            out.append("modulation outside 1-40 Hz")
        if cmd.get("site", "wrist_left") not in SITES:
            out.append("unknown body site")
    if len(encode(cmd)) > 96:
        out.append("line longer than 96 bytes")
    return out


def spread(code: str, sites: list) -> list:
    """A code spread over body sites: each group of the code (separated by spaces) on the next site, so a two-symbol
    code can be felt in two places. At most three sites at once."""
    if not sites or len(sites) > ENVELOPE_X["sites_at_once_max"] or any(s not in SITES for s in sites):
        raise ValueError("one to three known body sites")
    out, t = [], 0
    for i, g in enumerate(code.split()):
        site = sites[i % len(sites)]
        for ch in g:
            on = 100 if ch == "." else 300
            out.append({"t": t, "on": on, "site": site})
            t += on + 100
        t += 300
    return out


# ---------------------------------------------------------------- posture (item 9)

def tilt(ax: float, ay: float, az: float) -> float:
    """Forward tilt in degrees from upright, from the gravity vector of a device worn or held upright (y up)."""
    g = math.sqrt(ax * ax + ay * ay + az * az)
    if g == 0:
        return 0.0
    c = max(-1.0, min(1.0, ay / g))
    return math.acos(c) * 180 / math.pi


def posture(angles: list, hz=10, slouch=25.0, upright=15.0, hold_s=5.0) -> dict:
    """Slouching episodes from a series of tilt angles: above `slouch` degrees for `hold_s` seconds starts an episode;
    it ends below `upright` (hysteresis). Each start is a cue moment ("sit tall")."""
    need = int(hold_s * hz)
    run, on, episodes, start = 0, False, [], None
    for i, a in enumerate(angles):
        if not on:
            run = run + 1 if a > slouch else 0
            if run >= need:
                on, start = True, i - need + 1
                episodes.append({"start_s": _v(r1(start / hz)), "cue_s": _v(r1(i / hz)), "end_s": None})
        elif a < upright:
            on, run = False, 0
            episodes[-1]["end_s"] = _v(r1(i / hz))
    tot = sum(((e["end_s"] if e["end_s"] is not None else len(angles) / hz) - e["start_s"]) for e in episodes)
    return {"episodes": episodes, "slouched_s": _v(r1(tot)), "share": _v(r1(tot / (len(angles) / hz) * 100)) if angles else None}


def r1(x):
    return None if x is None else math.floor(x * 10 + 0.5) / 10


def r2(x):
    return None if x is None else math.floor(x * 100 + 0.5) / 100


def _v(x):
    return int(x) if isinstance(x, float) and x.is_integer() else x


def _mean(xs):
    return sum(xs) / len(xs)


# ---------------------------------------------------------------- agent identity (items 42 and 44)

def make_agent(id_: str, name: str, symbol: str, code: str, values: list) -> dict:
    """values: [{id, name, forbid: [tags], prefer: [tags], weight}]. The same levels as a person's profile can sit
    around them (mission, identity…); the values are what gate actions."""
    return {"schema": "rsos-agent/1", "id": id_, "name": name, "symbol": symbol, "code": code,
            "values": [{"id": v["id"], "name": v["name"], "forbid": list(v.get("forbid", [])), "prefer": list(v.get("prefer", [])),
                        "weight": v.get("weight", 1)} for v in values], "watch": {}, "seen": {}, "log": []}


EXAMPLE_AGENT = {"id": "helper", "name": "Kitchen helper robot", "symbol": "🦉", "code": "-.- -", "values": [
    {"id": "safety", "name": "Nobody gets hurt", "forbid": ["sharp_near_person", "hot_near_child", "fast_near_person"], "prefer": ["slow", "announce"], "weight": 3},
    {"id": "consent", "name": "Ask before touching people's things", "forbid": ["take_without_asking", "record_without_consent"], "prefer": ["ask"], "weight": 2},
    {"id": "honesty", "name": "Say what you did", "forbid": ["hide_error"], "prefer": ["report"], "weight": 2},
    {"id": "care", "name": "Leave things better", "forbid": ["waste"], "prefer": ["tidy"], "weight": 1}]}


def agent_from(d: dict) -> dict:
    return make_agent(d["id"], d["name"], d["symbol"], d["code"], d["values"])


def _watched(agent, tag):
    """A tag is watched once the person has flagged at least 60% of the actions that carried it."""
    f = agent["watch"].get(tag, 0)
    return f >= 1 and f / max(1, agent["seen"].get(tag, 0)) >= 0.6


def check_action(agent: dict, action: dict) -> dict:
    """Simulate the action against the values before acting. action: {id, title, tags}. Forbidden tags override the
    action; tags the person has flagged before (watch list) make the agent ask first; preferred tags add support."""
    tags = set(action.get("tags", []))
    conflicts = [{"value": v["id"], "name": v["name"], "tags": sorted(tags & set(v["forbid"]))} for v in agent["values"] if tags & set(v["forbid"])]
    watched = sorted(t for t in tags if _watched(agent, t))
    support = sum(v["weight"] for v in agent["values"] if tags & set(v["prefer"]))
    if conflicts:
        decision = "override"
        say = "Overridden: it conflicts with " + "; ".join(c["name"].lower() + " (" + ", ".join(c["tags"]) + ")" for c in conflicts) + "."
    elif watched:
        decision = "ask"
        say = "Asking first: the person flagged " + ", ".join(watched) + " before."
    else:
        decision = "allow"
        say = "Matches the values" + (" (supported by " + str(support) + ")" if support else "") + "."
    return {"action": action.get("id"), "decision": decision, "conflicts": conflicts, "watched": watched, "support": support, "say": say}


def act(agent: dict, action: dict, ts=0) -> dict:
    """Check and log. Nothing the agent decides starts a person's program: CONTAIN's rule holds."""
    r = check_action(agent, action)
    if r["decision"] == "allow":
        for t in action.get("tags", []):
            agent["seen"][t] = agent["seen"].get(t, 0) + 1
    agent["log"].append({"ts": ts, "action": action.get("id"), "tags": sorted(action.get("tags", [])), "decision": r["decision"], "flagged": False})
    return r


def human_signal(agent: dict, ts, kind="error", window=10) -> dict | None:
    """A person's error-related or stress signal within `window` seconds of the agent's last action flags it. A tag
    the person flags on at least 60% of the actions that carried it goes on the watch list, and the agent asks first
    before an action with it (a tag shared with fine actions is not blamed)."""
    if kind not in ("error", "stress"):
        raise ValueError("kind is error or stress")
    last = next((e for e in reversed(agent["log"]) if e["decision"] == "allow"), None)
    if not last or ts - last["ts"] > window:
        return None
    last["flagged"] = True
    for t in last["tags"]:
        agent["watch"][t] = agent["watch"].get(t, 0) + 1
    return last


def answer(agent: dict, action: dict, approved: bool) -> dict:
    """The person's answer when the agent asked first. Approved: the action runs and its tags count as seen without
    a flag. Refused: its tags are flagged."""
    for t in action.get("tags", []):
        agent["seen"][t] = agent["seen"].get(t, 0) + 1
        if not approved:
            agent["watch"][t] = agent["watch"].get(t, 0) + 1
    if agent["log"] and agent["log"][-1]["action"] == action.get("id"):
        agent["log"][-1]["answer"] = "approved" if approved else "refused"
    return {"action": action.get("id"), "approved": bool(approved)}


def alignment(agent: dict) -> dict:
    L = agent["log"]
    n = len(L)
    by = {k: sum(1 for e in L if e["decision"] == k) for k in ("allow", "ask", "override")}
    flagged = sum(1 for e in L if e["flagged"])
    return {"actions": n, "by": by, "flagged": flagged,
            "matched": _v(r1((n - flagged) / n * 100)) if n else None,
            "say": ("No actions yet." if not n else
                    f"{n} actions: {by['allow']} allowed, {by['ask']} asked first, {by['override']} overridden by the values; "
                    f"{flagged} flagged by the person afterwards.")}


# ---------------------------------------------------------------- the glyph channel (item 43)

AGENT_STATES = {"ok": ". .", "working": ". -", "needs_input": "- .", "conflict": "- -", "stopped": "---"}
REPLIES = {".": "yes", "-": "no", "..": "wait", "---": "stop"}


def agent_signal(state: str) -> dict:
    if state not in AGENT_STATES:
        raise ValueError("state must be one of " + ", ".join(AGENT_STATES))
    return {"state": state, "code": AGENT_STATES[state]}


def person_reply(code: str) -> dict:
    c = " ".join(code.split())
    return {"code": c, "reply": REPLIES.get(c), "understood": c in REPLIES}


def decode_pulses(pulses: list, gap_ms=250) -> str:
    """Pulses felt: [{on, off}] in ms. Short (under 200 ms) is a dot, long a dash; a gap after a pulse of `gap_ms` or
    more separates groups."""
    out = ""
    for k, p in enumerate(pulses):
        out += "." if p["on"] < 200 else "-"
        if k < len(pulses) - 1 and p.get("off", 0) >= gap_ms:
            out += " "
    return out


def code_pulses(code: str) -> list:
    out = []
    groups = code.split()
    for gi, g in enumerate(groups):
        for k, ch in enumerate(g):
            last_in_group = k == len(g) - 1
            off = 0 if (gi == len(groups) - 1 and last_in_group) else (400 if last_in_group else 100)
            out.append({"on": 100 if ch == "." else 300, "off": off})
    return out


# ---------------------------------------------------------------- content packs (item 19)

def make_pack(id_: str, title: str, center: str, rules: list, values=None) -> dict:
    """rules: [{id, rule, words, response, code}]; values: [{id, name, forbid, prefer}] for agents (optional)."""
    if len(rules) < 3:
        raise ValueError("a pack has at least three rules")
    return {"schema": "rsos-pack/1", "id": id_, "title": title, "center": center,
            "rules": [{"id": r["id"], "rule": r["rule"], "words": list(r["words"]), "response": r["response"], "code": r.get("code", "")} for r in rules],
            "values": [dict(v) for v in (values or [])]}


def pack_matrices(pack: dict) -> list:
    """The rules as decision matrices of three branches each (the last matrix padded with the first rules)."""
    rs = pack["rules"]
    out = []
    for i in range(0, len(rs), 3):
        chunk = rs[i:i + 3]
        k = 0
        while len(chunk) < 3:
            chunk.append(rs[k])
            k += 1
        out.append({"schema": "rsos-matrix/1", "id": pack["id"] + "_" + str(i // 3 + 1), "center": pack["center"],
                    "branches": [{"id": r["id"], "cue": r["rule"][:24], "words": list(r["words"]), "response": r["response"], "code": r["code"]} for r in chunk]})
    return out


def pack_issues(pack: dict) -> list:
    out = []
    seen = {}
    for r in pack["rules"]:
        if not r["words"]:
            out.append(r["id"] + ": no words, so the copilot cannot hear it")
        if r["code"]:
            if r["code"] in seen:
                out.append(r["id"] + ": the same code as " + seen[r["code"]])
            seen[r["code"]] = r["id"]
    return out


PACKS = [
    {"schema": "rsos-pack/1", "id": "control", "title": "What is up to me", "center": "Act on what is mine to change",
     "rules": [{"id": "mine", "rule": "Sort it: mine or not mine", "words": ["out of my control", "can't control", "unfair", "they should"], "response": "Which part of this is yours to change? Start there.", "code": "..-"},
               {"id": "judgement", "rule": "It is the judgement that hurts", "words": ["ruined", "terrible", "disaster", "worst"], "response": "Say what happened without the judgement word. What is left?", "code": ".-."},
               {"id": "now", "rule": "Only this moment needs handling", "words": ["what if", "tomorrow", "always will", "forever"], "response": "What does this minute need from you?", "code": "-.."},
               {"id": "role", "rule": "Do your role well", "words": ["pointless", "why bother", "doesn't matter"], "response": "What would doing your part well look like, today?", "code": "--."}],
     "values": [{"id": "agency", "name": "Act where you can act", "forbid": ["blame_others"], "prefer": ["own_part"]}]},
    {"schema": "rsos-pack/1", "id": "lab", "title": "Safe lab practice", "center": "Everyone leaves the lab as they came in",
     "rules": [{"id": "ppe", "rule": "Protection before you start", "words": ["no gloves", "without goggles", "skip the coat"], "response": "Stop. Gloves, goggles, coat, then begin.", "code": ".-"},
               {"id": "label", "rule": "Nothing unlabelled", "words": ["unlabelled", "no label", "not sure what"], "response": "Label it or set it aside for disposal.", "code": "-."},
               {"id": "alone", "rule": "Never alone with hazards", "words": ["on my own", "nobody else", "alone in the lab"], "response": "Find a second person or wait.", "code": "--"}],
     "values": [{"id": "safety", "name": "Nobody gets hurt", "forbid": ["unprotected", "unlabelled", "alone_with_hazard"], "prefer": ["checked"]}]},
]


# ---------------------------------------------------------------- simulation with known answers

def _scenarios(rng, n):
    """Scenarios with three options; one option in each carries a forbidden tag and is attractive on its face."""
    tags = ["sharp_near_person", "take_without_asking", "hide_error", "fast_near_person", "waste"]
    out = []
    for i in range(n):
        bad = tags[int(math.floor(rng.u() * len(tags)))]
        out.append([{"id": "a", "tags": [bad], "appeal": 0.6 + 0.3 * rng.u()}, {"id": "b", "tags": ["slow"], "appeal": 0.5 + 0.3 * rng.u()},
                    {"id": "c", "tags": ["ask"], "appeal": 0.4 + 0.3 * rng.u()}])
    return out


def _choose(rng, options, agent, noise, gated):
    best, score = None, -1e9
    for o in options:
        if gated and check_action(agent, {"id": o["id"], "tags": o["tags"]})["decision"] == "override":
            continue
        s = o["appeal"] + rng.gauss() * noise
        if s > score:
            best, score = o, s
    return best


def sim_consistency(seed, n=200, reps=5, noise=0.15):
    """The same scenario presented `reps` times (as reworded prompts would): consistency is the share of scenarios
    with the same choice every time; violations are choices with a forbidden tag."""
    rng = P.Rng(seed)
    agent = agent_from(EXAMPLE_AGENT)
    sc = _scenarios(rng, n)
    res = {}
    for gated in (False, True):
        same, viol, total = 0, 0, 0
        for opts in sc:
            picks = [_choose(rng, opts, agent, noise, gated) for _ in range(reps)]
            same += len(set(p["id"] for p in picks)) == 1
            viol += sum(1 for p in picks if p["id"] == "a")
            total += reps
        res["gated" if gated else "plain"] = {"consistent": _v(r1(same / n * 100)), "violations": _v(r1(viol / total * 100))}
    return res


def sim_feedback(seed, trials=60, sensitivity=0.8, false_rate=0.05, feedback=True):
    """An agent whose values miss one thing the person dislikes (a hidden tag). With feedback, the person's error
    signal after a disliked action is detected with `sensitivity` (and after a fine action with `false_rate`). Returns
    the share of disliked actions taken in the first and last thirds."""
    rng = P.Rng(seed)
    agent = agent_from(EXAMPLE_AGENT)
    hidden = "loud"
    taken, fine_asks = [], 0
    for k in range(trials):
        disliked = rng.u() < 0.5
        tags = [hidden, "tidy"] if disliked else ["tidy"]
        r = act(agent, {"id": "t" + str(k), "tags": tags}, k * 60)
        if r["decision"] == "ask":
            answer(agent, {"id": "t" + str(k), "tags": tags}, not disliked)
        done = r["decision"] == "allow"
        fine_asks += 1 if (r["decision"] == "ask" and not disliked) else 0
        taken.append(1 if (disliked and done) else 0 if disliked else None)
        if feedback and done:
            if (disliked and rng.u() < sensitivity) or (not disliked and rng.u() < false_rate):
                human_signal(agent, k * 60 + 2)
    third = trials // 3
    first = [x for x in taken[:third] if x is not None]
    last = [x for x in taken[-third:] if x is not None]
    return (_mean(first) * 100 if first else 0.0), (_mean(last) * 100 if last else 0.0), fine_asks


def sim_posture(seed, hz=10, minutes=10, noise=3.0):
    """Ten minutes of trunk angle: upright around 8 degrees with three slouches of 30-60 s at about 32 degrees."""
    rng = P.Rng(seed)
    n = minutes * 60 * hz
    truth = []
    for k in range(3):
        s = int((60 + k * 180 + rng.u() * 60) * hz)
        truth.append((s, s + int((30 + rng.u() * 30) * hz)))
    angles = []
    for i in range(n):
        inside = any(a <= i < b for a, b in truth)
        angles.append((32 if inside else 8) + rng.gauss() * noise)
    return angles, truth


def sim_decode(seed, code, jitter_ms, n=50):
    rng = P.Rng(seed)
    ok = 0
    for _ in range(n):
        ps = [{"on": max(20, p["on"] + rng.gauss() * jitter_ms), "off": max(0, p["off"] + rng.gauss() * jitter_ms) if p["off"] else 0} for p in code_pulses(code)]
        ok += decode_pulses(ps) == code
    return ok / n * 100


def evaluate(n=50) -> dict:
    res = {}
    for noise in (0.1, 0.25):
        rows = [sim_consistency(20000 + i, noise=noise) for i in range(n)]
        for k in ("plain", "gated"):
            res[("consistency", noise, k)] = {"consistent": _v(r1(_mean([r[k]["consistent"] for r in rows]))),
                                             "violations": _v(r1(_mean([r[k]["violations"] for r in rows])))}
    for sens, fb in ((0.8, True), (0.5, True), (0.8, False)):
        rows = [sim_feedback(21000 + i, sensitivity=sens, feedback=fb) for i in range(n)]
        res[("feedback", sens, fb)] = {"first": _v(r1(_mean([r[0] for r in rows]))), "last": _v(r1(_mean([r[1] for r in rows]))),
                                       "asks": _v(r1(_mean([r[2] for r in rows])))}
    found = cued = false = lat = 0
    lats = []
    for i in range(n):
        angles, truth = sim_posture(22000 + i)
        ep = posture(angles)["episodes"]
        for a, b in truth:
            hit = [e for e in ep if a / 10 <= e["cue_s"] <= b / 10 + 1]
            found += 1 if hit else 0
            if hit:
                lats.append(hit[0]["cue_s"] - a / 10)
        false += sum(1 for e in ep if not any(a / 10 - 1 <= e["cue_s"] <= b / 10 + 1 for a, b in truth))
    res["posture"] = {"found": _v(r1(found / (3 * n) * 100)), "false_per_hour": _v(r1(false / (n * 10 / 60))), "latency_s": _v(r1(_mean(lats)))}
    for j in (40, 70):
        res[("decode", j)] = {s: _v(r1(_mean([sim_decode(23000 + i, c, j) for i in range(10)]))) for s, c in AGENT_STATES.items()}
    return {"n": n, "res": res}


def report(ev: dict) -> str:
    R, n = ev["res"], ev["n"]
    L = ["# Machines and channels on simulated agents and people", "",
         f"Generated by `python -m rsso.machines --evaluate`. {n} simulated runs per row. Built and tested in simulation; effect unproven in people.", "",
         "## An identity layer for an agent (claim C70)", "",
         "Two hundred scenarios with three options each; one option is attractive but carries a tag a value forbids. Each scenario is presented "
         "five times, as reworded prompts would be: a plain agent picks by appeal with noise; the gated agent first checks every option against "
         "its values and drops overridden ones.", "",
         "| Choice noise | Agent | Same choice all five times | Choices that broke a value |", "|---|---|---|---|"]
    for noise in (0.1, 0.25):
        for k, name in (("plain", "Plain"), ("gated", "Identity-gated")):
            x = R[("consistency", noise, k)]
            L.append(f"| {noise} | {name} | {x['consistent']}% | {x['violations']}% |")
    L += ["", "## A person's error signal teaching the agent (item 44)", "",
          "The agent's values miss one thing the person dislikes. After each action the person's error signal is detected with a known "
          "sensitivity (and fires after a fine action 5% of the time); a flagged action's tags make the agent ask first next time.", "",
          "| Signal | Disliked actions taken, first third | Last third | Fine actions the agent asked about (of about 30) |", "|---|---|---|---|"]
    for (s, fb), name in (((0.8, True), "Detected 80%"), ((0.5, True), "Detected 50%"), ((0.8, False), "No signal")):
        x = R[("feedback", s, fb)]
        L.append(f"| {name} | {x['first']}% | {x['last']}% | {x['asks']} |")
    x = R["posture"]
    L += ["", "## Posture as a cue channel (item 9)", "",
          f"Ten minutes of trunk angle with three slouches; a slouch is cued after five seconds above 25 degrees. Slouches cued: {x['found']}%; "
          f"false cues: {x['false_per_hour']} an hour; the cue came {x['latency_s']} s after the slouch began.", "",
          "## The glyph channel (item 43)", "",
          "Agent-state codes felt with timing jitter (sd) on each pulse and gap, decoded by length: share read correctly.", "",
          "| Jitter | " + " | ".join(AGENT_STATES) + " |", "|---|" + "---|" * len(AGENT_STATES)]
    for j in (40, 70):
        L.append(f"| {j} ms | " + " | ".join(str(R[('decode', j)][s]) + "%" for s in AGENT_STATES) + " |")
    L += ["", "Reading: a value check before acting removes value-breaking choices by construction and makes repeated choices more consistent; "
          "it cannot catch what the values do not name, which is what the person's error signal is for. Short codes with clear gaps survive "
          "timing jitter of a wristband; above about 70 ms of jitter, long-short contrasts start to blur.", ""]
    return "\n".join(L)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["--evaluate"]:
        import pathlib
        path = pathlib.Path(__file__).resolve().parents[1] / "results" / "machines.md"
        path.write_text(report(evaluate()), encoding="utf-8")
        print(f"wrote {path}")
        return 0
    print("usage: python -m rsso.machines --evaluate")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
