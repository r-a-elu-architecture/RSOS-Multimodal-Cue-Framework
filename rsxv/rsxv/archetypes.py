"""RSX-V archetype agents and the repair loop (step 5C).

Builds on agents.py (Spine, audit log, memory, Meta-Architect, Watchdog, Observer). Specification: ../AGENTS.md §2, §5, §6.

The agent system used for repair is a stated model, not data: six agents in a dependency graph, each with three modules whose
quality is 1.0 when healthy. An agent's error is its own module faults plus a share of its inputs' error, so a fault in one
agent shows up as symptoms downstream. Observations are noisy. A repair restores a module with probability P_FIX and can damage
a healthy module with probability P_DAMAGE, which is why snapshots and rollback matter.
"""
from __future__ import annotations

import copy
import random

from . import agents as ag

# ------------------------------------------------------------------------------------------------------------- profiles
PROFILES = {
    "LION": {"tacton": "..-", "role": "baseline lead; simulated participant in the World",
             "virtues": ["yu", "rei"], "language": "plain, direct, first person",
             "shadow": [("hold_boundary", "a person or agent pushes past declared consent")],
             "envelopes": ["leading a session", "boundary setting"], "prohibited": ["device dispatch"],
             "base_core": "courage with consent", "override": "pause and hand the lead to the Watchdog"},
    "EAGLE": {"tacton": "-..", "role": "overview and timing; forecasts candidate futures as ghost passes",
              "virtues": ["chugi", "meiyo"], "language": "future tense, conditional",
              "shadow": [("third_option", "two proposals conflict")],
              "envelopes": ["planning", "forecasting"], "prohibited": ["executing repairs it forecast"],
              "base_core": "see further before acting", "override": "produce three candidate repairs"},
    "BEAR": {"tacton": "--", "role": "stability: snapshots, rollback, consolidation, archive",
             "virtues": ["makoto", "meiyo"], "language": "slow, factual, past tense",
             "shadow": [("refuse_unverified", "a repaired state has not settled")],
             "envelopes": ["memory", "recovery"], "prohibited": ["deleting entries"],
             "base_core": "nothing is lost", "override": "snapshot before any change"},
    "LEOPARD": {"tacton": "...", "role": "agility: extract, repair, reinsert the faulty module",
                "virtues": ["yu", "jin"], "language": "short imperative steps",
                "shadow": [("hot_swap", "a pre-approved reflex exists for this fault")],
                "envelopes": ["repair", "focused change"], "prohibited": ["changing modules it was not assigned"],
                "base_core": "precise change, then step back", "override": "repair the located module only"},
    "RAVEN": {"tacton": ".-.", "role": "wide view: drift monitoring, raises the Override trigger",
              "virtues": ["makoto", "gi"], "language": "observational, third person",
              "shadow": [("early_alarm", "two independent signals agree")],
              "envelopes": ["monitoring"], "prohibited": ["acting on a single signal"],
              "base_core": "notice early, report honestly", "override": "report drift with both signals"},
    "TIGER": {"tacton": "-.-", "role": "drive: dispatches the chosen plan to the device through the RSX bridge",
              "virtues": ["chugi", "rei"], "language": "commands with explicit target and consent reference",
              "shadow": [("full_intensity", "the person has consented to the full-intensity tier")],
              "envelopes": ["delivery"], "prohibited": ["dispatch without consent", "electrical stimulation"],
              "base_core": "power in service of the mission", "override": "halt output, hold state"},
    "DRAGON": {"tacton": "---", "role": "integration of agent outputs into one system state (optional)",
               "virtues": ["chugi", "jin"], "language": "integrative, whole-system",
               "shadow": [("hold_opposites", "agents return contradictory states")],
               "envelopes": ["integration"], "prohibited": ["overruling the Spine"],
               "base_core": "strength and shadow held together", "override": "freeze integration until repaired"},
    "OBSERVER": {"tacton": "-", "role": "global view; locates faults; never acts",
                 "virtues": ["makoto"], "language": "none: maps only",
                 "shadow": [], "envelopes": ["fault location"], "prohibited": ["any action"],
                 "base_core": "no ego, only observed", "override": "rerun the global scan"},
}

# --------------------------------------------------------------------------------------------------------- agent system
GRAPH = {"RAVEN": [], "BEAR": [], "EAGLE": ["RAVEN", "BEAR"], "LEOPARD": ["EAGLE"],
         "TIGER": ["EAGLE", "LEOPARD"], "LION": ["TIGER"]}
MODULES = ("perceive", "decide", "act")
PASS_ON = 0.7          # share of the worst input's error an agent inherits
P_FIX, P_DAMAGE = 0.85, 0.10
NOISE = 0.05
SYMPTOM = 0.15         # observed error above this marks an agent as symptomatic


class AgentSystem:
    def __init__(self, rng: random.Random, graph: dict | None = None, noise: float = NOISE):
        self.rng, self.graph, self.noise = rng, dict(graph or GRAPH), noise
        self.q = {a: {m: 1.0 for m in MODULES} for a in self.graph}
        self.faults: list[tuple] = []
        self.silent: set = set()
        self.version = 0

    def own(self, a, visible_only=False):
        return sum(1 - v for m, v in self.q[a].items() if not (visible_only and (a, m) in self.silent)) / len(MODULES)

    def output_error(self, a, _memo=None):
        """Error in what the agent passes downstream (includes silent faults)."""
        memo = {} if _memo is None else _memo
        if a not in memo:
            up = max((self.output_error(u, memo) for u in self.graph[a]), default=0.0)
            memo[a] = min(1.0, self.own(a) + PASS_ON * up)
        return memo[a]

    def error(self, a, _memo=None):
        """Error visible at the agent itself (silent faults excluded)."""
        up = max((self.output_error(u, _memo) for u in self.graph[a]), default=0.0)
        return min(1.0, self.own(a, visible_only=True) + PASS_ON * up)

    def errors(self):
        memo = {}
        return {a: self.error(a, memo) for a in self.graph}

    def health(self):
        e = self.errors()
        return 1 - sum(e.values()) / len(e)

    def observe(self):
        return {a: max(0.0, e + self.rng.gauss(0, self.noise)) for a, e in self.errors().items()}

    def observe_modules(self, a):
        return {m: min(1.0, v + self.rng.gauss(0, self.noise)) for m, v in self.q[a].items()}

    def inject(self, agent, module, severity=0.8, silent=False):
        self.q[agent][module] = 1 - severity
        self.faults.append((agent, module))
        if silent:
            self.silent.add((agent, module))

    def repair(self, agent, module):
        """One repair attempt: costs one unit of budget."""
        if self.q[agent][module] < 0.99:
            if self.rng.random() < P_FIX:
                self.q[agent][module] = 1.0
                self.silent.discard((agent, module))
        elif self.rng.random() < P_DAMAGE:
            self.q[agent][module] = 0.8
        return self.q[agent][module]

    def fixed(self):
        return all(self.q[a][m] >= 0.99 for a, m in self.faults)

    def state(self):
        return copy.deepcopy(self.q)

    def load(self, q):
        self.q = copy.deepcopy(q)


# ------------------------------------------------------------------------------------------------------- Raven and Eagle
class Raven:
    """Drift trigger. Needs two independent signals (precept 3): smoothed health below baseline, and a symptomatic agent."""

    def __init__(self, alpha=0.5, drop=0.05):
        self.alpha, self.drop, self.base, self.ema = alpha, drop, None, None

    def watch(self, obs: dict) -> dict:
        h = 1 - sum(obs.values()) / len(obs)
        self.ema = h if self.ema is None else (1 - self.alpha) * self.ema + self.alpha * h
        self.base = self.ema if self.base is None else max(self.base, self.ema)
        signals = []
        if self.base - self.ema > self.drop:
            signals.append("health_drop")
        if any(v > SYMPTOM for v in obs.values()):
            signals.append("symptom")
        p = {"actor": "RAVEN", "action": "raise_override", "target": "system", "disclosed": True, "measured": True,
             "trigger_signals": signals}
        return {"trigger": len(signals) >= 2 and ag.spine_check(p)["ok"], "signals": signals}


class Eagle:
    """Forecasts candidate repairs by ghost passes on a copy of the observed state. Eagle never executes, so its forecast
    skill (RIF) is scored only on outcomes produced by another agent."""

    def __init__(self):
        self.forecasts: list[dict] = []

    def candidates(self, system: AgentSystem, roots: list, n=3) -> list:
        out = []
        for r in roots or list(system.graph):
            mods = sorted(system.observe_modules(r).items(), key=lambda kv: kv[1])
            out += [(r, m) for m, _ in mods]
        seen, uniq = set(), []
        for c in out:
            if c not in seen:
                seen.add(c)
                uniq.append(c)
        return uniq[:n]

    def forecast(self, system: AgentSystem, cand: tuple) -> float:
        a, m = cand
        ghost = AgentSystem(random.Random(0), system.graph, 0.0)
        ghost.q = {x: system.observe_modules(x) for x in system.graph}
        ghost.q[a][m] = 1.0
        f = ghost.health()
        self.forecasts.append({"cand": cand, "forecast": f, "realized": None, "executed_by": None})
        return f

    def record(self, cand, realized, executed_by):
        for fr in reversed(self.forecasts):
            if fr["cand"] == cand and fr["realized"] is None:
                fr["realized"], fr["executed_by"] = realized, executed_by
                return


def rif(forecasts: list) -> float | None:
    """Forecast skill: 1 - mean absolute error, on outcomes Eagle did not produce itself."""
    rows = [f for f in forecasts if f["realized"] is not None and f["executed_by"] not in (None, "EAGLE")]
    if not rows:
        return None
    return 1 - sum(abs(f["forecast"] - f["realized"]) for f in rows) / len(rows)


# ---------------------------------------------------------------------------------------------------------- repair loop
SETTLE_TICKS = 3
TIME_FULL, TIME_FAST = 5, 1


class RepairLoop:
    """The Override from the meta position (§6), with two speeds."""

    def __init__(self, system: AgentSystem, log: ag.AuditLog | None = None, meta: ag.MetaArchitect | None = None):
        self.s = system
        self.log = log or ag.AuditLog()
        self.meta = meta or ag.MetaArchitect()
        self.mem = ag.Memory()
        self.eagle = Eagle()
        self.reflexes: dict = {}        # fault signature -> {"fix": (agent, module), "version": graph version}
        self.generation = 0
        self.time = 0
        self.broadcasts: list = []

    def _signature(self, roots, obs):
        """Fault signature: the located roots and, for each, the module that reads worst."""
        return tuple((r, min(self.s.observe_modules(r).items(), key=lambda kv: kv[1])[0]) for r in roots)

    def _ancestors(self, a):
        out, todo = [], list(self.s.graph[a])
        while todo:
            u = todo.pop(0)
            if u not in out:
                out.append(u)
                todo += self.s.graph[u]
        return out

    def _refine(self, roots):
        """Global view: a located root whose own modules all read healthy is a symptom; the Observer walks upstream and
        names the nearest ancestor whose modules show a fault (this is what a local agent cannot see)."""
        out = []
        for r in roots:
            if min(self.s.observe_modules(r).values()) > 1 - SYMPTOM:
                bad = [u for u in self._ancestors(r) if min(self.s.observe_modules(u).values()) <= 1 - SYMPTOM]
                out += bad[:1] or [r]
            else:
                out.append(r)
        return list(dict.fromkeys(out))

    def _execute(self, cand, now):
        before = self.s.health()
        sid = self.mem.snapshot("system", self.s.state())                                        # Bear
        p = {"actor": "LEOPARD", "action": "repair", "target": "agent_other", "consent": "meta-token",
             "disclosed": True, "measured": True, "serves_mission": True}
        chk = ag.spine_check(p)
        if not chk["ok"]:
            self.log.append("LEOPARD", "repair", aligned=False, failed=chk["failed"])
            return False, before
        self.s.repair(*cand)                                                                       # Leopard
        after = self.s.health()
        rolled = False
        if after < before - 1e-9:
            self.s.load(self.mem.restore(sid))                                                     # Bear rollback
            after, rolled = self.s.health(), True
        self.log.append("LEOPARD", f"repair {cand[0]}.{cand[1]}", aligned=True, override_triggered=True,
                        pre=round(before, 4), post=round(after, 4), rolled_back=rolled, t=now)
        return not rolled and after > before + 1e-9, after

    def step(self, now: int, budget: int) -> dict:
        """One pass of the loop. Returns what happened and the budget used (one unit per repair attempt)."""
        obs = self.s.observe()
        loc = ag.observer_locate(obs, self.s.graph, threshold=SYMPTOM)                             # Observer
        roots = self._refine(loc["roots"])
        sig = self._signature(roots, obs)
        rx = self.reflexes.get(sig)
        if rx and rx["version"] == self.s.version and budget >= 1:                                 # fast speed
            self.time += TIME_FAST
            ok, after = self._execute(rx["fix"], now)
            self.log.append("WATCHDOG", "reflex", aligned=True, signature=str(sig), ok=ok)
            if not ok:
                self.reflexes.pop(sig)                                                             # re-verify next time
            return {"speed": "fast", "used": 1, "ok": ok}
        self.time += TIME_FULL                                                                     # full speed
        cands = self.eagle.candidates(self.s, roots)                                              # Eagle
        if not cands or budget < 1:
            return {"speed": "full", "used": 0, "ok": False}
        scored = sorted(((self.eagle.forecast(self.s, c), c) for c in cands), reverse=True)
        best = scored[0][1]                                                                        # Watchdog chooses
        tok = self.meta.grant_switch("LEOPARD", now)                                               # Meta confirms
        assert self.meta.valid(tok, "LEOPARD", now)
        ok, after = self._execute(best, now)
        self.eagle.record(best, after, "LEOPARD")
        if ok:
            self.reflexes[sig] = {"fix": best, "version": self.s.version, "settled": 0}
        return {"speed": "full", "used": 1, "ok": ok, "cand": best, "roots": roots}

    def settle_and_broadcast(self, now: int):
        """Broadcast a new reflex only after the system has stayed healthy for SETTLE_TICKS observations."""
        stable = all(max(self.s.observe().values()) <= SYMPTOM for _ in range(SETTLE_TICKS))
        if stable:
            fresh = [k for k, v in self.reflexes.items() if not v.get("broadcast")]
            for k in fresh:
                self.reflexes[k]["broadcast"] = True
                self.broadcasts.append(k)
            if fresh or self.s.fixed():
                self.generation += 1                                                               # Phoenix
                self.log.append("META", "seal", aligned=True, generation=self.generation, t=now)
        else:
            self.log.append("WATCHDOG", "veto_broadcast", aligned=True, t=now)
        return stable


def meta_repair(system: AgentSystem, budget: int, loop: RepairLoop | None = None, raven: Raven | None = None) -> dict:
    loop = loop or RepairLoop(system)
    raven = raven or Raven()
    used, t = 0, 0
    raven.watch({a: 0.0 for a in system.graph})       # healthy reference
    while used < budget and t < budget * 4:
        t += 1
        if not raven.watch(system.observe())["trigger"] and system.fixed():
            break
        r = loop.step(t, budget - used)
        used += r["used"]
        if r["used"] == 0:
            break
        if max(system.observe().values()) <= SYMPTOM:
            loop.settle_and_broadcast(t)
            if system.fixed():
                break
    return {"fixed": system.fixed(), "used": used, "health": system.health(), "time": loop.time,
            "generation": loop.generation}


def local_repair(system: AgentSystem, budget: int, blame_upstream: bool = False) -> dict:
    """Baseline: reflect-and-retry inside each symptomatic agent, on its own modules (Reflexion-style).
    With blame_upstream, an agent whose own modules look healthy asks its worst input to retry (a stronger baseline)."""
    used, rounds = 0, 0
    while used < budget and rounds < budget * 4:
        rounds += 1
        obs = system.observe()
        sick = sorted((a for a, v in obs.items() if v > SYMPTOM), key=lambda a: -obs[a])
        if not sick:
            break
        a = sick[0]
        mods = system.observe_modules(a)
        worst, q = min(mods.items(), key=lambda kv: kv[1])
        if blame_upstream and q > 1 - SYMPTOM and system.graph[a]:
            a = max(system.graph[a], key=lambda u: obs[u])
            worst = min(system.observe_modules(a).items(), key=lambda kv: kv[1])[0]
        system.repair(a, worst)
        used += 1
    return {"fixed": system.fixed(), "used": used, "health": system.health(), "time": used * TIME_FULL}


# ----------------------------------------------------------------------------------------------------- Lion and Tiger
class Lion:
    """The simulated participant: a simulated person (sim.person) with a consent record. Sessions run through rsxv.run."""

    def __init__(self, rng: random.Random, pid: int = 1, consent: set | None = None):
        from . import sim
        self.person = sim.person(rng, pid)
        self.consent = set(consent or ())

    def session(self, prog: dict, ctx: dict | None = None, log: ag.AuditLog | None = None) -> dict:
        from .run import run
        p = {"actor": "LION", "action": "session", "target": "person", "consent": bool(self.consent),
             "disclosed": True, "measured": True, "serves_mission": True}
        chk = ag.spine_check(p)
        if log is not None:
            log.append("LION", "session", aligned=chk["ok"], failed=chk["failed"])
        if not chk["ok"]:
            return {"status": "refused_by_spine", "failed": chk["failed"]}
        return run(prog, self.person, {**(ctx or {}), "consent": tuple(self.consent)})


class Tiger:
    """Dispatches a program to the device through the RSX bridge, only with a consent reference."""

    def dispatch(self, prog: dict, consent_ref: str | None, log: ag.AuditLog, electrical: bool = False) -> dict:
        from . import bridge
        p = {"actor": "TIGER", "action": "electrical_stimulation" if electrical else "dispatch", "target": "person",
             "consent": consent_ref, "disclosed": True, "measured": True, "serves_mission": True}
        chk = ag.spine_check(p)
        log.append("TIGER", p["action"], aligned=chk["ok"], consent_ref=consent_ref, failed=chk["failed"])
        if not chk["ok"]:
            return {"ok": False, "failed": chk["failed"]}
        cue = bridge.to_cue(prog)
        return {"ok": True, "source": cue["source"], "manifest": cue["manifest"]}
