"""CONTAIN — the safety layer (spec/CONTAIN.md).

Recovered role (archive, CONTAIN_Historical_Reconstruction): drift lock, propagation control and recovery
governance across modules; outputs allow / block / quarantine / rollback decisions; operators: containment,
propagation stop, rollback, quarantine, guard insertion; protocols: human in the loop, reversibility, device
safety envelope. The archive recovers the architecture but no executable policy engine; this module is that
engine. docs/js/contain.js is identical (tested).

  ENVELOPE                   the device safety envelope every program must stay inside
  check_envelope(timeline)   violations of the envelope, one per rule and event
  drift(runs, protocol)      whether a program or node stops helping or starts to harm
  escalation(...)            when practice must pause device offers and point to a therapist or crisis help
  review(state, ...)         the safety state after new runs and events: drift quarantines, escalation
  decide(action, state, ...) allow or block, with every reason (the gate every module asks before acting)
  release(state, ...)        restore a quarantined program: by the person, or by the therapist when harm was involved
  rollback(history)          the previous approved node plan

Times: runs carry `timestamp` in seconds; adverse events and screening answers carry `ts` in milliseconds (as the
pages store them); `now` is in seconds.
"""
from __future__ import annotations

import copy
import math

ENVELOPE = {
    "haptic_amp_max": 0.6,          # absolute vibration strength (0..1); programs set their own lower limit
    "haptic_pulse_ms_max": 1000,    # one pulse
    "haptic_burst_ms_max": 6000,    # one pattern, pulses and gaps together
    "haptic_on_ms_per_run": 20000,  # all vibration in one run
    "tone_hz_min": 60, "tone_hz_max": 2000,
    "tone_ms_max": 10000, "tone_ms_per_run": 60000,
    "scent_per_run": 3, "scent_gap_ms": 20000,
    "taste_per_run": 2,
    "run_ms_max": 900000,           # 15 minutes
    "max_per_hour": 6, "max_per_day": 20, "refractory_ms_min": 90000,   # programs may be stricter, never looser
}
THERAPIST_LED_TIERS = ("414", "420", "439", "440")
DAY, WEEK = 86400, 7 * 86400


def _num(v):
    if v is None or v == "" or isinstance(v, bool):
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def r1(x: float) -> float:
    """Round to one decimal, half up (identical in JavaScript)."""
    return math.floor(x * 10 + 0.5) / 10


def t1(x: float) -> str:
    """One decimal as text, half up (identical in JavaScript)."""
    k = math.floor(abs(x) * 10 + 0.5)
    return ("-" if x < 0 and k else "") + f"{k // 10}.{k % 10}"


def _v(x):
    """Whole numbers as int, so text and JSON read the same in Python and JavaScript."""
    return int(x) if isinstance(x, float) and x.is_integer() else x


def check_envelope(tl: dict, env: dict | None = None) -> list[dict]:
    env = env or ENVELOPE
    out = []
    s = tl.get("safety") or {}
    if (s.get("max_per_hour") or 0) > env["max_per_hour"]:
        out.append({"rule": "max_per_hour", "value": _v(s["max_per_hour"]), "limit": env["max_per_hour"]})
    if (s.get("max_per_day") or 0) > env["max_per_day"]:
        out.append({"rule": "max_per_day", "value": _v(s["max_per_day"]), "limit": env["max_per_day"]})
    if (s.get("refractory_ms") or 0) < env["refractory_ms_min"]:
        out.append({"rule": "refractory_ms_min", "value": _v(s.get("refractory_ms")), "limit": env["refractory_ms_min"]})
    if (s.get("haptic_max") or 0) > env["haptic_amp_max"]:
        out.append({"rule": "haptic_amp_max", "value": _v(s["haptic_max"]), "limit": env["haptic_amp_max"]})
    if (tl.get("duration_ms") or 0) > env["run_ms_max"]:
        out.append({"rule": "run_ms_max", "value": _v(tl["duration_ms"]), "limit": env["run_ms_max"]})
    hap_on = tone_ms = 0
    scents, tastes = [], 0
    for i, e in enumerate(tl.get("events") or []):
        ch, kind = e.get("channel"), e.get("kind")
        if ch == "haptic":
            on, off, n = int(e.get("on") or 0), int(e.get("off") or 0), int(e.get("count") or 1)
            amp = float(e.get("amp") or 0)
            if amp > env["haptic_amp_max"]:
                out.append({"rule": "haptic_amp_max", "event": i, "value": _v(amp), "limit": env["haptic_amp_max"]})
            if on > env["haptic_pulse_ms_max"]:
                out.append({"rule": "haptic_pulse_ms_max", "event": i, "value": _v(on), "limit": env["haptic_pulse_ms_max"]})
            if n * (on + off) > env["haptic_burst_ms_max"]:
                out.append({"rule": "haptic_burst_ms_max", "event": i, "value": _v(n * (on + off)), "limit": env["haptic_burst_ms_max"]})
            hap_on += n * on
        elif ch == "auditory" and kind == "tone":
            hz, dur = float(e.get("hz") or 0), int(e.get("dur") or 0)
            if not env["tone_hz_min"] <= hz <= env["tone_hz_max"]:
                out.append({"rule": "tone_hz", "event": i, "value": _v(hz), "limit": f"{env['tone_hz_min']}-{env['tone_hz_max']}"})
            if dur > env["tone_ms_max"]:
                out.append({"rule": "tone_ms_max", "event": i, "value": _v(dur), "limit": env["tone_ms_max"]})
            tone_ms += dur
        elif ch == "olfactory":
            if scents and e["t"] - scents[-1] < env["scent_gap_ms"]:
                out.append({"rule": "scent_gap_ms", "event": i, "value": _v(e["t"] - scents[-1]), "limit": env["scent_gap_ms"]})
            scents.append(e["t"])
        elif ch == "gustatory":
            tastes += 1
    if hap_on > env["haptic_on_ms_per_run"]:
        out.append({"rule": "haptic_on_ms_per_run", "value": _v(hap_on), "limit": env["haptic_on_ms_per_run"]})
    if tone_ms > env["tone_ms_per_run"]:
        out.append({"rule": "tone_ms_per_run", "value": _v(tone_ms), "limit": env["tone_ms_per_run"]})
    if len(scents) > env["scent_per_run"]:
        out.append({"rule": "scent_per_run", "value": _v(len(scents)), "limit": env["scent_per_run"]})
    if tastes > env["taste_per_run"]:
        out.append({"rule": "taste_per_run", "value": _v(tastes), "limit": env["taste_per_run"]})
    return out


def _rated(r: dict) -> bool:
    return _num(r.get("sud_before")) is not None and _num(r.get("sud_after")) is not None


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)


def drift(runs: list[dict], protocol: str, since: float | None = None) -> dict:
    """{status: ok | watch | drift, signals[], runs}. Only runs after `since` (a release) count."""
    rs = sorted((r for r in runs if r.get("protocol") == protocol and (since is None or (_num(r.get("timestamp")) or 0) > since)),
                key=lambda r: _num(r.get("timestamp")) or 0)
    rated = [r for r in rs if _rated(r)]
    sig = []
    last = rated[-5:]
    if len(last) >= 4:
        ch = _mean([_num(r["sud_after"]) - _num(r["sud_before"]) for r in last])
        if ch >= 0.5:
            sig.append({"signal": "worse after", "value": r1(ch), "text": f"distress rose by {t1(ch)} on average over the last {len(last)} rated runs"})
        ag = [_num(r.get("agency_after")) - _num(r.get("agency_before")) for r in last
              if _num(r.get("agency_after")) is not None and _num(r.get("agency_before")) is not None]
        if len(ag) >= 4 and _mean(ag) <= -1:
            sig.append({"signal": "agency falls", "value": r1(_mean(ag)), "text": f"agency fell by {t1(-_mean(ag))} on average"})
    if len(rated) >= 8:
        a = _mean([_num(r["sud_after"]) for r in rated[-5:]])
        b = _mean([_num(r["sud_after"]) for r in rated[-10:-5]])
        if a - b >= 1.5:
            sig.append({"signal": "rising distress", "value": r1(a - b), "text": f"distress after a run is {t1(a - b)} higher than in the runs before"})
    recent = rs[-6:]
    if len(recent) >= 6:
        stopped = sum(1 for r in recent if str(r.get("completed")) in ("0", "0.0", "False", "false"))
        if stopped >= 4:
            sig.append({"signal": "stopped often", "value": stopped, "text": f"stopped {stopped} of the last 6 times"})
    names = {s["signal"] for s in sig}
    status = "drift" if ("worse after" in names or "agency falls" in names or len(sig) >= 2) else "watch" if sig else "ok"
    return {"status": status, "signals": sig, "runs": len(rs)}


def escalation(runs: list[dict], adverse: list[dict], screens: list[dict], now: float) -> dict:
    """{active, reasons[]}: while active, device offers and therapist-led work pause and the person is pointed to
    their therapist or to crisis help."""
    reasons = []
    for a in adverse or []:
        age = now - (_num(a.get("ts")) or 0) / 1000
        if a.get("severity") == "serious" and age <= 30 * DAY:
            reasons.append("a serious adverse event in the last 30 days")
            break
    mod = [a for a in adverse or [] if a.get("severity") == "moderate" and a.get("related") in ("possible", "likely")
           and now - (_num(a.get("ts")) or 0) / 1000 <= 14 * DAY]
    if len(mod) >= 2:
        reasons.append(f"{len(mod)} moderate adverse events possibly related to practice in 14 days")
    if any(s.get("answer") == "yes" and now - (_num(s.get("ts")) or 0) / 1000 <= WEEK for s in screens or []):
        reasons.append("the screening question was answered yes in the last 7 days")
    week = [r for r in runs if _rated(r) and now - (_num(r.get("timestamp")) or 0) <= WEEK]
    week.sort(key=lambda r: _num(r.get("timestamp")) or 0)
    high = sum(1 for r in week[-5:] if _num(r["sud_after"]) >= 8)
    if high >= 3:
        reasons.append(f"distress stayed at 8 or more after {high} of the last 5 runs")
    return {"active": bool(reasons), "reasons": reasons}


def new_state() -> dict:
    return {"quarantine": {}, "released": {}, "escalation": {"active": False, "reasons": []}}


def review(state: dict | None, runs: list[dict], adverse: list[dict] | None = None, screens: list[dict] | None = None,
           now: float = 0.0) -> tuple[dict, list[dict]]:
    """The safety state after the latest runs and events, and what changed ({kind, protocol?, text})."""
    st = copy.deepcopy(state or new_state())
    changes = []
    for p in sorted({r.get("protocol") for r in runs if r.get("protocol")}):
        if p in st["quarantine"]:
            continue
        rel = st["released"].get(p)
        d = drift(runs, p, rel["at"] if rel else None)
        if d["status"] == "drift":
            st["quarantine"][p] = {"since": now, "reason": "; ".join(s["text"] for s in d["signals"]), "signals": [s["signal"] for s in d["signals"]],
                                   "therapist": False}
            changes.append({"kind": "quarantine", "protocol": p, "text": st["quarantine"][p]["reason"]})
    for a in adverse or []:    # an adverse event linked to a program quarantines it at once
        p = a.get("protocol")
        if p and a.get("related") in ("possible", "likely") and a.get("severity") in ("moderate", "serious") and p not in st["quarantine"]:
            rel = st["released"].get(p)
            if rel is None or (_num(a.get("ts")) or 0) / 1000 > rel["at"]:
                st["quarantine"][p] = {"since": now, "reason": f"a {a['severity']} adverse event {a['related']}ly related to it", "signals": ["adverse"], "therapist": True}
                changes.append({"kind": "quarantine", "protocol": p, "text": st["quarantine"][p]["reason"]})
    esc = escalation(runs, adverse or [], screens or [], now)
    if esc["active"] != st["escalation"]["active"]:
        changes.append({"kind": "escalation" if esc["active"] else "escalation ended", "text": "; ".join(esc["reasons"])})
    st["escalation"] = esc
    return st, changes


def decide(action: dict, state: dict | None, timeline: dict | None = None, now: float = 0.0) -> dict:
    """The gate every module asks before acting. action: {kind: run | offer | cue | plan, protocol, trigger,
    therapist_led, therapist_present}. Returns {decision: allow | block, reasons[]}."""
    st = state or new_state()
    reasons = []
    if timeline is not None:
        for v in check_envelope(timeline):
            reasons.append(f"outside the device safety envelope: {v['rule']} is {v['value']}, the limit is {v['limit']}")
    p = action.get("protocol")
    if p and p in st["quarantine"]:
        q = st["quarantine"][p]
        reasons.append(f"paused by CONTAIN: {q['reason']}. It can be restored on the safety page" + (" with your therapist" if q.get("therapist") else ""))
    esc = st["escalation"]
    if esc.get("active"):
        if action.get("kind") == "offer" or action.get("trigger") == "device":
            reasons.append("device offers are paused: " + "; ".join(esc["reasons"]))
        if action.get("therapist_led") and not action.get("therapist_present"):
            reasons.append("therapist-led work is paused unless a therapist is present: " + "; ".join(esc["reasons"]))
        if action.get("kind") == "plan" and not action.get("therapist_present"):
            reasons.append("a new plan needs a therapist present while practice is paused: " + "; ".join(esc["reasons"]))
    return {"decision": "block" if reasons else "allow", "reasons": reasons}


def release(state: dict, protocol: str, by: str, now: float) -> tuple[dict, str]:
    """Restore a quarantined program. Returns (state, message); a quarantine that involved harm needs the therapist."""
    st = copy.deepcopy(state)
    q = st["quarantine"].get(protocol)
    if q is None:
        return st, "not paused"
    if (q.get("therapist") or st["escalation"].get("active")) and by != "therapist":
        return st, "needs the therapist: this pause involved an adverse event or practice is paused"
    del st["quarantine"][protocol]
    st["released"][protocol] = {"at": now, "by": by}
    return st, "restored"


def rollback(history: list[dict]) -> dict | None:
    """The previous approved node plan, or None."""
    approved = [h for h in history or [] if h.get("approved")]
    return copy.deepcopy(approved[-2]) if len(approved) >= 2 else None
