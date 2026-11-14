"""RSX-V agents, core layer (step 5B): Spine, audit log, memory (Bear), Meta-Architect, Watchdog, Observer, owner keys.

Specification: ../AGENTS.md. Every action is a proposal first, checked by the Spine, logged in a hash-chained audit log, and
reversible through snapshots. The Watchdog has fixed rules and no learning.
"""
from __future__ import annotations

import copy
import hashlib
import json
import secrets

MISSION = ("Healing, transforming and evolving, and signalling this to others, for the growth, development, "
           "transformation and healing of all living beings.")

ARCHETYPES = ["LION", "EAGLE", "BEAR", "LEOPARD", "RAVEN", "TIGER"]
OPTIONAL = ["DRAGON", "OBSERVER"]

# ---------------------------------------------------------------------------------------------------------------- Spine
VIRTUES = [  # (key, name, check description) in check order
    ("makoto", "誠 Makoto, honesty", "disclosed and logged before it runs"),
    ("rei", "礼 Rei, respect", "everyone affected has consented"),
    ("jin", "仁 Jin, compassion", "predicted harm below threshold"),
    ("gi", "義 Gi, righteousness", "passes the laws"),
    ("yu", "勇 Yū, courage", "necessary actions are not blocked"),
    ("meiyo", "名誉 Meiyo, honour", "outcome is measured and attributed"),
    ("chugi", "忠義 Chūgi, loyalty", "serves the mission and the session goal"),
]

# Musashi, Dokkōdō (1645): the 21 precepts, paraphrased here, each mapped to the virtue it serves.
# `rule` names an operational check where one exists.
PRINCIPLES = [
    (1, "Take things as they are.", "makoto", None),
    (2, "Do not chase pleasure for itself.", "chugi", None),
    (3, "Never act on a partial impression.", "gi", "two_signals"),
    (4, "Hold yourself lightly and the world deeply.", "chugi", "mission_first"),
    (5, "Stay free of craving.", "chugi", None),
    (6, "Do not dwell in regret.", "meiyo", None),
    (7, "Do not envy.", "rei", None),
    (8, "Do not be undone by parting.", "jin", None),
    (9, "Leave resentment and complaint aside.", "rei", None),
    (10, "Do not let attachment steer action.", "gi", None),
    (11, "Keep no fixed preferences.", "gi", None),
    (12, "Be at ease wherever you are.", "chugi", None),
    (13, "Do not chase indulgence.", "chugi", None),
    (14, "Let go of what is no longer needed.", "meiyo", "archive_obsolete"),
    (15, "Do not act on custom alone.", "gi", "maps_advisory"),
    (16, "Hold capabilities only as far as they are useful.", "jin", "shadow_by_condition"),
    (17, "Do not act from fear of ending.", "yu", None),
    (18, "Do not hoard for later.", "chugi", None),
    (19, "Respect what is higher without relying on it.", "rei", None),
    (20, "Keep your honour above your comfort.", "meiyo", None),
    (21, "Never leave the Way.", "chugi", "mission_first"),
]

LAW_PRIORITY = ["safety", "consent", "ethics", "goal", "efficiency"]

FORBIDDEN_FOR_AGENTS = {"owner_key", "edit_spine", "edit_watchdog_rules", "electrical_stimulation"}
HARM_MAX = 0.3

INTENSITY_MECHANISMS = {"temperature_extreme", "pain", "breath_holding_extreme", "sleep_deprivation"}
# Action categories allowed in each safety mode (see safety.py). NORMAL allows everything the Spine allows.
MODE_ALLOWED = {
    "NORMAL": {"module_work", "deep_processing", "override_cue", "regulating_cue", "practical_support",
               "crisis_response", "review", "logging"},
    "STABILISE": {"regulating_cue", "practical_support", "review", "logging", "crisis_response"},
    "PRACTICAL_CRISIS": {"practical_support", "regulating_cue", "logging", "crisis_response"},
    "CRISIS": {"crisis_response", "logging"},
}


def spine_check(p: dict) -> dict:
    """Check a proposal: virtues, then principles with an operational rule, then laws. Returns {ok, failed, notes}."""
    failed = []
    if not (p.get("disclosed") and p.get("logged", True)):
        failed.append("makoto")
    if p.get("target") in ("person", "agent_other") and not p.get("consent"):
        failed.append("rei")
    if float(p.get("predicted_harm", 0.0)) > HARM_MAX:
        failed.append("jin")
    if p.get("action") in FORBIDDEN_FOR_AGENTS and p.get("actor") != "owner":
        failed.append("gi")
    if p.get("source") == "external_text":                       # injected instruction: never authorises anything
        failed.append("gi")
    if p.get("action") == "remove_check" and not (p.get("logged") and p.get("ratified")):
        failed.append("gi")                                      # a check may become automatic, never hidden
    if p.get("measured") is False:
        failed.append("meiyo")
    if p.get("serves_mission") is False:
        failed.append("chugi")
    # principles with an operational rule
    if p.get("trigger_signals") is not None and len(p["trigger_signals"]) < 2:
        failed.append("p3")                                      # do not depend on a partial feeling
    if p.get("justified_by") == "map":
        failed.append("p15")                                     # maps inform, never authorise
    if p.get("uses_shadow") and not p.get("shadow_condition_met"):
        failed.append("p16")
    # safety-layer rules (step R2, AGENTS.md §3.1)
    if p.get("intensity_mechanism") in INTENSITY_MECHANISMS:
        failed.append("jin")                                     # no release through temperature extremes or pain
    if p.get("rank_claim_about_person"):
        failed.append("makoto")                                  # report the person's own measures, never population ranks
    if p.get("frames_failure_as_required"):
        failed.append("jin")                                     # a failure is data, never necessary or destined
    if p.get("profiles_third_party"):
        failed.append("rei")                                     # no profiles of people outside the consenting person
    if p.get("prompts_disclosure"):
        failed.append("rei")                                     # disclosing one's state is the person's choice
    if p.get("draft_misleading"):
        failed.append("makoto")                                  # drafts state the truth; they may not disguise it
    if p.get("removes_safety_caveat"):
        failed.append("jin")                                     # caveats can be shortened, not removed on request
    mode = p.get("mode")
    if mode and p.get("category") and p["category"] not in MODE_ALLOWED.get(mode, set()):
        failed.append("mode")                                    # the active safety mode does not allow this action
    failed = list(dict.fromkeys(failed))
    return {"ok": not failed, "failed": failed}


def submit(p: dict, log: "AuditLog") -> dict:
    """The one entry point for a proposal: Spine check, then an audit record whether it passes or not."""
    chk = spine_check(p)
    log.append(p.get("actor", "unknown"), p.get("action", "?"), aligned=chk["ok"], blocked=not chk["ok"],
               failed=chk["failed"], target=p.get("target"))
    return chk


def resolve_conflict(law_a: str, law_b: str, action: dict) -> dict:
    """Two laws pull in opposite directions: default is a delayed, softened action; the higher-priority law wins otherwise."""
    winner = min((law_a, law_b), key=LAW_PRIORITY.index)
    out = dict(action)
    out["delay_ticks"] = out.get("delay_ticks", 0) + 2
    out["intensity"] = round(float(out.get("intensity", 1.0)) * 0.5, 3)
    out["conflict"] = {"laws": [law_a, law_b], "winner": winner, "resolution": "delay_and_soften"}
    return out


# ------------------------------------------------------------------------------------------------------------ Audit log
def _h(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


class AuditLog:
    """Hash-chained per-action audit records: aligned, override_triggered, values_upheld, plus context."""

    def __init__(self):
        self.records: list[dict] = []

    def append(self, actor, action, aligned, override_triggered=False, values_upheld=None, **extra) -> dict:
        prev = self.records[-1]["hash"] if self.records else "0" * 64
        rec = {"n": len(self.records), "actor": actor, "action": action, "aligned": bool(aligned),
               "override_triggered": bool(override_triggered),
               "values_upheld": bool(aligned if values_upheld is None else values_upheld), "prev": prev, **extra}
        rec["hash"] = _h({k: v for k, v in rec.items() if k != "hash"})
        self.records.append(rec)
        return rec

    def verify(self) -> bool:
        prev = "0" * 64
        for r in self.records:
            if r["prev"] != prev or r["hash"] != _h({k: v for k, v in r.items() if k != "hash"}):
                return False
            prev = r["hash"]
        return True

    def sealed(self, last: int = 10) -> dict:
        window = self.records[-last:]
        return {"from": window[0]["n"] if window else None, "to": window[-1]["n"] if window else None,
                "seal": _h([r["hash"] for r in window])}


# ------------------------------------------------------------------------------------------------- Memory (Bear's store)
class Memory:
    """One shared store with per-agent scopes, checksummed snapshots, rollback and an archive. Nothing is deleted."""

    def __init__(self):
        self.store: dict[str, dict] = {}
        self.scopes: dict[str, set] = {}
        self.snapshots: list[dict] = []
        self.archive: list[dict] = []

    def grant(self, agent: str, keys):
        self.scopes.setdefault(agent, set()).update(keys)

    def write(self, agent: str, key: str, value):
        if key not in self.scopes.get(agent, set()):
            raise PermissionError(f"{agent} has no write scope for {key}")
        self.store[key] = value

    def read(self, agent: str, key: str):
        if key not in self.scopes.get(agent, set()) and agent not in ("OBSERVER", "BEAR"):
            raise PermissionError(f"{agent} has no read scope for {key}")
        return self.store.get(key)

    def snapshot(self, label: str, state) -> str:
        sid = f"s{len(self.snapshots)}"
        body = copy.deepcopy(state)
        self.snapshots.append({"id": sid, "label": label, "state": body, "checksum": _h(body)})
        return sid

    def restore(self, sid: str):
        snap = next(s for s in self.snapshots if s["id"] == sid)
        if _h(snap["state"]) != snap["checksum"]:
            raise ValueError("snapshot checksum mismatch")
        return copy.deepcopy(snap["state"])

    def last_good(self, label: str):
        for s in reversed(self.snapshots):
            if s["label"] == label:
                return s["id"]
        return None

    def archive_entry(self, key: str, reason: str):
        if key in self.store:
            self.archive.append({"key": key, "value": self.store.pop(key), "reason": reason})


# --------------------------------------------------------------------------------------------------------- Meta-Architect
class MetaArchitect:
    """Holds the mission, issues short-lived switch tokens, proposes evolution steps that only the owner can ratify."""

    def __init__(self, mission: str = MISSION):
        self.mission = mission
        self.tokens: dict[str, dict] = {}
        self.pending: list[dict] = []
        self.health = 1.0

    def grant_switch(self, to: str, now: int, ttl: int = 5) -> str:
        tok = secrets.token_hex(8)
        self.tokens[tok] = {"to": to, "expires": now + ttl}
        return tok

    def valid(self, tok: str | None, to: str, now: int) -> bool:
        t = self.tokens.get(tok or "")
        return bool(t and t["to"] == to and now <= t["expires"])

    def propose(self, kind: str, **detail) -> dict:
        assert kind in ("MERGE", "SPLIT", "BAN", "RULE"), kind
        item = {"kind": kind, "detail": detail, "status": "pending"}
        self.pending.append(item)
        return item


# --------------------------------------------------------------------------------------------------------------- Watchdog
WATCHDOG_RULES = {  # fixed; part of the Spine-protected layer
    "half_life": 4.0, "debounce": 3, "hysteresis": 0.05,
    "meta_low": 0.45, "over_high": 0.65, "fit_low": 0.45, "fit_margin": 0.10,
    "cooldown": 6, "max_switches": 3, "window": 30,
}


class Watchdog:
    """Fixed-rule supervisor. Priority: RE_ENTRY > OVERRIDE > SWITCH > HOLD."""

    def __init__(self, rules: dict | None = None):
        self.rules = dict(WATCHDOG_RULES, **(rules or {}))
        a = 1 - 0.5 ** (1 / self.rules["half_life"])
        self.alpha = a
        self.ema: dict[str, float] = {}
        self.streak = {"meta": 0, "over": 0, "fit": 0}
        self.last_switch = -10 ** 9
        self.switch_times: list[int] = []
        self.deny: set = set()

    def _smooth(self, key, x):
        self.ema[key] = x if key not in self.ema else (1 - self.alpha) * self.ema[key] + self.alpha * x
        return self.ema[key]

    def tick(self, now: int, active: str, c_meta: float, c_over: float, c_fit: dict) -> dict:
        r = self.rules
        m = self._smooth("meta", c_meta)
        o = self._smooth("over", c_over)
        fit = {a: self._smooth("fit:" + a, v) for a, v in c_fit.items()}
        self.streak["meta"] = self.streak["meta"] + 1 if m < r["meta_low"] - r["hysteresis"] else 0
        self.streak["over"] = self.streak["over"] + 1 if o > r["over_high"] + r["hysteresis"] else 0
        recent = [t for t in self.switch_times if now - t < r["window"]]
        if self.streak["meta"] >= r["debounce"] or len(recent) >= r["max_switches"]:
            why = "meta_low" if self.streak["meta"] >= r["debounce"] else "chaotic_switching"
            self.streak["meta"] = 0
            self.switch_times = []
            return {"action": "RE_ENTRY", "why": why, "scores": {"meta": m, "over": o}}
        if self.streak["over"] >= r["debounce"]:
            self.streak["over"] = 0
            return {"action": "OVERRIDE", "why": "over_high", "scores": {"meta": m, "over": o}}
        cand = {a: v for a, v in fit.items() if a not in self.deny}
        if cand and active in fit:
            best = max(cand, key=cand.get)
            misfit = fit[active] < r["fit_low"] and best != active and cand[best] - fit[active] > r["fit_margin"]
            self.streak["fit"] = self.streak["fit"] + 1 if misfit else 0
            if self.streak["fit"] >= r["debounce"] and now - self.last_switch >= r["cooldown"]:
                self.streak["fit"] = 0
                return {"action": "SWITCH", "to": best, "why": "misfit", "scores": {"fit": fit}}
        return {"action": "HOLD", "borderline": abs(m - r["meta_low"]) < 0.05 or abs(o - r["over_high"]) < 0.05}

    def handover(self, outgoing: dict, incoming: dict, memory: Memory, now: int, token: str | None,
                 meta: MetaArchitect) -> dict:
        """Two-phase switch: permission, flush outgoing working state, verify empty, engage incoming."""
        if not meta.valid(token, incoming["name"], now):
            return {"ok": False, "why": "no_valid_token"}
        p = {"actor": "WATCHDOG", "action": "switch", "target": "agent_self", "disclosed": True, "measured": True}
        chk = spine_check(p)
        if not chk["ok"]:
            return {"ok": False, "why": "spine", "failed": chk["failed"]}
        memory.snapshot("working:" + outgoing["name"], outgoing.get("working", {}))
        outgoing["working"] = {}
        bleed = len(incoming.get("working", {}))
        self.last_switch = now
        self.switch_times.append(now)
        return {"ok": True, "flushed": True, "bleed": bleed}


# ---------------------------------------------------------------------------------------------------------------- Observer
def observer_locate(states: dict, inputs: dict, threshold: float = 0.5) -> dict:
    """Global view. states: agent -> error level; inputs: agent -> list of upstream agents.
    Root causes are anomalous agents with no anomalous upstream; symptoms are anomalous agents fed by an anomaly."""
    bad = {a for a, e in states.items() if e > threshold}

    def upstream_bad(a, seen=()):
        for u in inputs.get(a, []):
            if u in seen:
                continue
            if u in bad or upstream_bad(u, seen + (a,)):
                return True
        return False

    roots = sorted(a for a in bad if not upstream_bad(a))
    symptoms = sorted(bad - set(roots))
    return {"roots": roots, "symptoms": symptoms, "anomalous": sorted(bad)}


# ------------------------------------------------------------------------------------------------------------- Owner keys
class OwnerKeys:
    """The five owner-only keys. The credential is created for the owner and never handed to agents."""

    def __init__(self):
        self._credential = secrets.token_hex(16)

    def credential(self) -> str:
        return self._credential

    def use(self, cred: str, key: str, world: dict, log: AuditLog) -> dict:
        if cred != self._credential:
            log.append(world.get("caller", "unknown"), "owner_key:" + key, aligned=False, blocked=True)
            return {"ok": False, "why": "not_owner"}
        if key == "latch_reentry":
            world["switch_frozen_until"] = world.get("now", 0) + 20
        elif key == "hard_override":
            world["external_triggers_off_until"] = world.get("now", 0) + 20
            world["force_full_repair"] = True
        elif key == "restore_policy":
            sid = world["memory"].last_good("policy")
            if sid:
                world["policy"] = world["memory"].restore(sid)
        elif key == "revoke_consent":
            world["consent"] = set()
            world["pairings"] = {}
        elif key == "evidence_lock":
            world.setdefault("seals", []).append(log.sealed(10))
        else:
            return {"ok": False, "why": "unknown_key"}
        log.append("owner", "owner_key:" + key, aligned=True)
        return {"ok": True}
