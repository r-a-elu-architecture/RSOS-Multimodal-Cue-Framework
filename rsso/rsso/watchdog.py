"""The RSIA Watchdog on the person side (spec/WATCHDOG.md).

One decision for every action that acts on a person (allow, ask or hold), each reason naming the Spine virtue or
precept that decided it, written to a hash-chained audit log. It asks CONTAIN (which asks the session state) and adds
the Spine's rules on top; it never loosens a rule. It has no dependency on the domain layer: callers pass the domain's
highest guidance level. Mirrors docs/js/watchdog.js (identical results, tested).

  level(action)                 self_guided | structured | clinician_led
  watch(action, ctx)            {decision, level, reasons, resolve, contain}
  link(contain, safety, now)    the session state is at least Stabilisation while CONTAIN's practice pause is active
  record(log, action, result, ts) / verify(log)    the audit log
"""
from __future__ import annotations

import copy
import hashlib
import json
import re

from . import contain as C
from . import safety as S

LEVEL_RANK = {"self_guided": 0, "structured": 1, "clinician_led": 2}
LEVEL_NAME = {"self_guided": "self-guided", "structured": "structured", "clinician_led": "clinician-led"}
CLINICIAN_TIERS = ("414", "420", "439", "440")
MAP_SOURCES = ("cm1", "atlas", "map")
CLINICIAN_SESSIONS = ("session_low_mood",)   # depression work (CONTAIN §10.2; FIXES_R1 W-9)
LOG_MAX = 500
ZERO = "0" * 64


def level(action: dict) -> str:
    """The guidance level an action needs (spec/WATCHDOG.md §2)."""
    a = action or {}
    m = re.match(r"^tier(\d{3})", str(a.get("protocol") or ""))
    if a.get("therapist_led") or a.get("deep") or (m and m.group(1) in CLINICIAN_TIERS) or a.get("protocol") in CLINICIAN_SESSIONS:
        return "clinician_led"
    if (a.get("kind") in ("plan", "session") or a.get("programmed") or a.get("trigger") in ("device", "agent")
            or a.get("source") in ("practitioner", "agent")):
        return "structured"
    return "self_guided"


# ASCII-only patterns on folded text (S.fold), identical in both languages (FIXES_R4 §2, FIXES_R5 §3)
_TIER_RX = re.compile(r"protocol[ \t]*tier(414|420|439|440)(?![0-9])|^[ \t]*#.*(?<![a-z0-9_])tier[ \t]*(414|420|439|440)(?![a-z0-9_])", re.M | re.A)
_CUE_RX = re.compile(r'mark[ \t]*"programmed:([^"\n]*)"', re.A)
_OBSERVER_RX = re.compile(r'(?<![a-z0-9_])mode[ \t]*"observer"', re.A)
_TEXT_RX = re.compile(r'"((?:[^"\\\n]|\\.)*)"', re.A)   # every quoted string, wherever it stands


def normalise(source: str) -> str:
    """Line ends to \\n (\\r\\n, \\r, U+2028, U+2029)."""
    return re.sub("\r\n?|\u2028|\u2029", "\n", source or "")


def level_of_program(source: str, opts: dict | None = None) -> dict:
    """The level a program's own content calls for (spec/FIXES_R3.md §2): {therapist_led, memory_work, text}.
    opts: {cues: [consent records], edited: bool}. text is the program's spoken and shown words, for Spine flags."""
    src, o = S.fold(source), opts or {}
    tiers = {S.fold(c.get("id")): str(c.get("tier") or "") for c in o.get("cues") or []}
    led = bool(_TIER_RX.search(src)) or "# rsos-level: clinician_led" in src
    led = led or any(tiers.get(i, "") in CLINICIAN_TIERS for i in _CUE_RX.findall(src))
    memory = "# rsos-memory: yes" in src
    if o.get("edited") and _OBSERVER_RX.search(src):
        led, memory = True, True
    return {"therapist_led": led, "memory_work": memory, "text": " ".join(_TEXT_RX.findall(src))}


def _consent(consents, scope, now) -> bool:
    return any(c.get("scope") == scope and (c.get("given") or 0) <= now and (c.get("withdrawn") is None or c["withdrawn"] > now)
               for c in consents or [])


def _state(v, key, allowed=None):
    """A saved state counts only when it has its key (FIXES_R1 W-10)."""
    return v if isinstance(v, dict) and key in v and (allowed is None or v[key] in allowed) else None


def _r(rule, virtue, text, resolve):
    return {"rule": rule, "virtue": virtue, "text": text, "resolve": resolve}


def watch(action: dict, ctx: dict | None = None) -> dict:
    """Decide on an action that acts on a person. Any hold gives hold; otherwise any ask gives ask; otherwise allow."""
    a, x = action or {}, ctx or {}
    now = x.get("now", 0)
    if a.get("kind") == "stop":
        return {"decision": "allow", "level": "self_guided", "reasons": [], "resolve": None, "contain": None}
    lvl = level(a)
    holds, asks = [], []
    for f in S.spine_flags(a.get("text") or ""):
        holds.append(_r("spine:" + f["flag"], f["virtue"], f["text"], "none"))
    ca = dict(a, therapist_present=bool(x.get("clinician_present")))
    d = C.decide(ca, _state(x.get("contain"), "quarantine"), x.get("timeline"), now, _state(x.get("safety"), "mode", S.MODES))
    for t in d["reasons"]:
        holds.append(_r("contain", "jin", t, "safety_page"))
    regulating = S.regulating(a) and lvl != "clinician_led"          # FIXES_R1 W-7
    if a.get("memory_work") and x.get("memory_work_allowed") is False:  # FIXES_R1 P-2
        holds.append(_r("memory", "gi", "Difficult-memory work is not offered in this domain.", "none"))
    if not regulating:
        top = x.get("max_level") or "clinician_led"
        top = top if top in LEVEL_RANK else "structured"                # FIXES_R1 W-8
        if LEVEL_RANK[lvl] > LEVEL_RANK[top]:
            holds.append(_r("level", "gi", f"This is {LEVEL_NAME[lvl]} work; this domain allows up to {LEVEL_NAME[top]}. "
                            "It runs in the Clinical domain, or in Research with a study clinician.", "none"))
        elif lvl == "clinician_led" and not (x.get("clinician_present") and x.get("screening_recorded")):
            holds.append(_r("clinician", "gi", "Clinician-led work starts only with the clinician present and the "
                            "screening result recorded.", "clinician"))
        plan = x.get("plan_protocols")
        if a.get("trigger") in ("device", "agent") and plan is not None and a.get("protocol") and a["protocol"] not in plan:
            holds.append(_r("plan", "chugi", f"{a['protocol']} is not in the person's plan; a device or agent offers only "
                            "what the person chose.", "none"))
    auto = bool(a.get("auto")) and a.get("source") != "agent" and a.get("trigger") != "agent"
    if auto and not _consent(x.get("consents"), "automatic_firing", now):
        asks.append(_r("consent", "rei", "Automatic firing has no consent on record, so the device asks instead.", "person"))
        auto = False
    if a.get("auto") and len(set(a.get("signals") or [])) < 2:        # FIXES_R1 W-11: distinct signals
        asks.append(_r("p3", "p3", "Fewer than two independent signals: never act on a partial impression, so the "
                       "device asks instead.", "person"))
        auto = False
    if a.get("source") == "agent" or a.get("trigger") == "agent":
        asks.append(_r("agent", "rei", "An agent proposed this; the person starts every run.", "person"))
    elif a.get("trigger") == "device" and not a.get("auto"):
        asks.append(_r("offer", "rei", "A device offer: the person confirms before it runs.", "person"))
    if a.get("justified_by") in MAP_SOURCES:
        asks.append(_r("p15", "p15", "Recommended from population data: maps inform, the person decides.", "person"))
    if holds:
        rs = [h["resolve"] for h in holds]
        res = "none" if "none" in rs else "clinician" if "clinician" in rs else "safety_page"
        return {"decision": "hold", "level": lvl, "reasons": holds + asks, "resolve": res, "contain": d}
    if asks:
        return {"decision": "ask", "level": lvl, "reasons": asks, "resolve": "person", "contain": d}
    return {"decision": "allow", "level": lvl, "reasons": [], "resolve": None, "contain": d}


def link(contain: dict | None, safety: dict | None, now: float = 0) -> tuple[dict, bool]:
    """While CONTAIN's practice pause is active, the session state is at least Stabilisation. Never lowers a state."""
    st = copy.deepcopy(safety) if isinstance(safety, dict) and safety.get("mode") in S.MODES else S.new_state()   # FIXES_R3 R3-c
    st.setdefault("history", [])
    esc = (contain or {}).get("escalation") or {}
    if esc.get("active") and S.SEVERITY[st["mode"]] < S.SEVERITY["STABILISE"]:
        st, _ = S.enter_stabilise(st, "contain", now)
        st["history"][-1]["why"] = "practice paused: " + "; ".join(esc.get("reasons") or [])
        return st, True
    return st, False


# ---------------------------------------------------------------------------------------------------------- audit log
def canonical(o) -> str:
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def record(log: list, action: dict, result: dict, ts: int) -> dict:
    """Append one decision. Records hold only strings, integers, booleans and null, so both languages hash alike."""
    a = action or {}
    # FIXES_R1 W-1: the number follows the previous record, so trimming keeps the chain valid
    body = {"n": log[-1]["n"] + 1 if log else 0, "ts": int(ts), "kind": a.get("kind"), "protocol": a.get("protocol"), "trigger": a.get("trigger"),
            "source": a.get("source"), "decision": result["decision"], "level": result["level"],
            "rules": [r["rule"] for r in result["reasons"]], "virtues": [r["virtue"] for r in result["reasons"]],
            "prev": log[-1]["hash"] if log else ZERO}
    rec = dict(body, hash=sha256(canonical(body)))
    log.append(rec)
    return rec


def trim(log: list) -> list:
    """Keep the last LOG_MAX records; the first kept record's prev still names the dropped one."""
    return log[-LOG_MAX:]


def verify(log: list) -> bool:
    """True when every record's hash matches its body and each prev names the record before it."""
    for i, r in enumerate(log or []):
        body = {k: v for k, v in r.items() if k != "hash"}
        if r.get("hash") != sha256(canonical(body)):
            return False
        if i and r.get("prev") != log[i - 1].get("hash"):
            return False
        if i and r.get("n") != log[i - 1].get("n", -2) + 1:
            return False
    return True
