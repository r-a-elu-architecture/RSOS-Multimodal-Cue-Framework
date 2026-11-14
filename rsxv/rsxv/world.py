"""RSX-V World loop (step 5D).

One loop runs the same architecture on two environments:
  AgentEnv   the agent system of archetypes.py, with faults arriving over time;
  PersonEnv  the simulated person of sim.py, one segment of operators per tick.

Each tick: the environment reports a context in shared terms (load, harm, trend), the Watchdog decides
(RE_ENTRY > OVERRIDE > SWITCH > HOLD) from C_meta, C_over and C_fit, the active archetype's mode runs for one tick, and the
outcome updates the fit ledger. Between runs the World sleeps: no actions, consolidation, archive, seal. The lineage is a
graph of typed edges (SWITCH, COOL, MERGE, SPLIT, BAN); the Watchdog creates SWITCH and COOL only, the rest are proposals
the owner ratifies.

Both environments are stated models, not data.
"""
from __future__ import annotations

import math
import random

from . import agents as ag
from . import archetypes as A

MODES = ["LION", "EAGLE", "BEAR", "LEOPARD", "RAVEN", "TIGER"]

# ---------------------------------------------------------------------------------------------------- shared context
CONTEXTS = ["calm", "rising", "loaded", "crisis"]


def context(load: float, harm_trend: float) -> str:
    """Shared description used by both environments: load in [0,1], harm trend (positive = getting worse)."""
    hi, worse = load >= 0.5, harm_trend > 0.0
    return {(False, False): "calm", (False, True): "rising", (True, False): "loaded", (True, True): "crisis"}[(hi, worse)]


# ------------------------------------------------------------------------------------------------------- environments
class AgentEnv:
    """Agent side. Load = worst observed agent error; harm = 1 - health. Faults arrive with probability `fault_rate`.
    Mode effects (defined from the roles in PROFILES):
      LION     baseline: progress 0.5, no other effect
      TIGER    drive: progress 1.0; under load adds a fault with probability 0.3 (pushing a degraded system)
      BEAR     stability: progress 0.2; observation noise halves next tick; snapshot (rollback if the tick got worse)
      LEOPARD  repair: one repair on the located fault; under load the damage risk of a repair doubles
      EAGLE    planning: progress 0.3; the next repair uses noise-free module readings
      RAVEN    monitoring: progress 0.3; silent faults become visible
    """

    side = "agent"

    def __init__(self, seed: int, fault_rate=0.15, silent_share=0.5):
        self.rng = random.Random(seed)
        self.sys = A.AgentSystem(random.Random(seed + 1))
        self.loop = A.RepairLoop(self.sys)
        self.fault_rate, self.silent_share = fault_rate, silent_share
        self.prev_harm = 0.0
        self.precise = False
        self.meta_ok = 1.0

    def _maybe_fault(self, p):
        if self.rng.random() < p:
            a = self.rng.choice(list(self.sys.graph))
            silent = self.rng.random() < self.silent_share
            self.sys.inject(a, "act" if silent else self.rng.choice(A.MODULES), silent=silent)

    def sense(self) -> dict:
        obs = self.sys.observe()
        harm = 1 - self.sys.health()
        out = {"load": max(obs.values()), "harm": harm, "trend": harm - self.prev_harm,
               "c_meta": self.meta_ok, "c_over": max(obs.values())}
        return out

    def step(self, mode: str) -> float:
        before = self.sys.health()
        self._maybe_fault(self.fault_rate)
        load = max(self.sys.observe().values())
        progress = {"LION": 0.5, "TIGER": 1.0, "BEAR": 0.2, "LEOPARD": 0.0, "EAGLE": 0.3, "RAVEN": 0.3}[mode]
        if mode == "TIGER" and load >= 0.5:
            self._maybe_fault(0.3)
        elif mode == "BEAR":
            self.sys.noise = A.NOISE / 2
            sid = self.loop.mem.snapshot("bear", self.sys.state())
            if self.sys.health() < before:
                self.sys.load(self.loop.mem.restore(sid))
        elif mode == "LEOPARD":
            old_damage, old_noise = A.P_DAMAGE, self.sys.noise
            if load >= 0.5:
                A.P_DAMAGE = old_damage * 2
            if self.precise:
                self.sys.noise = 0.0
            try:
                self.loop.step(now=0, budget=1)
            finally:
                A.P_DAMAGE, self.sys.noise = old_damage, old_noise
            self.precise = False
        elif mode == "EAGLE":
            self.precise = True
        elif mode == "RAVEN":
            self.sys.silent.clear()
        if mode != "BEAR":
            self.sys.noise = A.NOISE
        harm = 1 - self.sys.health()
        self.prev_harm = 1 - before
        rise = 10 * (harm - (1 - before))
        self.mission = 0.2 * progress - 2.0 * rise - (1.0 if rise > 1.0 else 0.0)
        self.comp = (0.2 * progress, rise)
        return 0.2 * progress - 2.0 * harm

    def override(self):
        self.loop.step(now=0, budget=1)

    def reentry(self):
        sid = self.loop.mem.last_good("system")
        if sid:
            self.sys.load(self.loop.mem.restore(sid))


class AgentEnvV2(AgentEnv):
    """Agent side with traffic pressure P separate from faults (registered in AGENTS.md §11.2, from site-reliability
    practice: shed load and freeze changes during an incident before repairing). Load = P."""

    side = "agent_v2"

    def __init__(self, seed: int, fault_rate=0.15, silent_share=0.5):
        super().__init__(seed, fault_rate, silent_share)
        self.P = 0.3

    def sense(self) -> dict:
        out = super().sense()
        out["load"] = self.P
        return out

    def step(self, mode: str) -> float:
        before = self.sys.health()
        self.P = min(1.0, self.P + 0.05)
        self._maybe_fault(self.fault_rate)
        progress = {"LION": 0.5, "TIGER": 1.0, "BEAR": 0.2, "LEOPARD": 0.0, "EAGLE": 0.3, "RAVEN": 0.3}[mode]
        if mode == "TIGER":
            self.P = min(1.0, self.P + 0.2)
        elif mode == "BEAR":
            self.P = max(0.0, self.P - 0.3)
            self.sys.noise = A.NOISE / 2
            sid = self.loop.mem.snapshot("bear", self.sys.state())
            if self.sys.health() < before:
                self.sys.load(self.loop.mem.restore(sid))
        elif mode == "LEOPARD":
            old = (A.P_FIX, A.P_DAMAGE, self.sys.noise)
            A.P_FIX, A.P_DAMAGE = 0.85 * (1 - self.P), 0.10 * (1 + 2 * self.P)
            if self.precise:
                self.sys.noise = 0.0
            try:
                self.loop.step(now=0, budget=1)
            finally:
                A.P_FIX, A.P_DAMAGE, self.sys.noise = old
            self.precise = False
        elif mode == "EAGLE":
            self.precise = True
        elif mode == "RAVEN":
            self.sys.silent.clear()
        if mode != "BEAR":
            self.sys.noise = A.NOISE
        harm = 1 - self.sys.health()
        self.prev_harm = 1 - before
        rise = 10 * (harm - (1 - before))
        self.mission = 0.2 * progress - 2.0 * rise - (1.0 if rise > 1.0 else 0.0)
        self.comp = (0.2 * progress, rise)
        return 0.2 * progress - 2.0 * harm


PERSON_MODES = {   # operator sets, defined from the archetype roles
    "LION": ["PostureShift", "SelfRevise"],
    "BEAR": ["BreathOverride", "PostureShift", "EmotionalLock"],
    "LEOPARD": ["MemoryUpdate", "IdentityRebuild", "CompressionRun"],
    "TIGER": ["IdentityShift", "FutureProjection", "DeviceTrigger"],
    "EAGLE": ["FutureSelfLink", "FutureAnchor", "MetaObserve"],
    "RAVEN": ["MetaObserve", "SymbolicDriftCheck", "DriftLock"],
}
SEGMENT_S = 20


class PersonEnv:
    """Person side. One tick = SEGMENT_S seconds of the mode's operators on sim.Body. Load = arousal; harm = distress / 10.
    Reward = agency gained - distress gained over the segment (distress weighted 2x)."""

    side = "person"

    def __init__(self, seed: int, pid: int = 1):
        from . import sim
        self.rng = random.Random(seed)
        p = sim.person(self.rng, pid)
        p["base"]["arousal"] = min(0.95, p["base"]["arousal"] + 0.1)
        self.body = sim.Body(p, self.rng)
        self.prev_harm = self.body.s["distress"] / 10

    def sense(self) -> dict:
        s = self.body.s
        harm = s["distress"] / 10
        return {"load": s["arousal"], "harm": harm, "trend": harm - self.prev_harm, "c_meta": 1.0,
                "c_over": s["arousal"] if harm - self.prev_harm > 0 else 0.0}

    def step(self, mode: str) -> float:
        s = self.body.s
        a0, d0 = s["agency"], s["distress"]
        self.prev_harm = d0 / 10
        if self.rng.random() < 0.15:                      # life events: a stress spike
            s["arousal"] = min(1.0, s["arousal"] + 0.2)
            s["distress"] = min(10.0, s["distress"] + 1.0)
        for _ in range(SEGMENT_S):
            self.body.step(PERSON_MODES[mode])
        rise = s["distress"] - d0
        self.mission = (s["agency"] - a0) - 2.0 * rise - (1.0 if rise > 1.0 else 0.0)
        self.comp = (s["agency"] - a0, rise)
        return (s["agency"] - a0) - 2.0 * (s["distress"] - d0) / 10

    def override(self):
        for _ in range(SEGMENT_S):
            self.body.step(PERSON_MODES["BEAR"])

    def reentry(self):
        self.override()


# ---------------------------------------------------------------------------------------------------------- fit ledger
class FitLedger:
    """Micro-randomised fit estimates per (context, mode): running mean and standard error of the tick reward.
    This is a ledger-style estimator inside the World; the clause-level Causal Ledger is ledger.py."""

    def __init__(self):
        self.n, self.s, self.ss = {}, {}, {}

    def add(self, ctx, mode, r):
        k = (ctx, mode)
        self.n[k] = self.n.get(k, 0) + 1
        self.s[k] = self.s.get(k, 0.0) + r
        self.ss[k] = self.ss.get(k, 0.0) + r * r

    def mean(self, ctx, mode):
        k = (ctx, mode)
        return self.s[k] / self.n[k] if self.n.get(k) else None

    def ci(self, ctx, mode):
        k = (ctx, mode)
        n = self.n.get(k, 0)
        if n < 2:
            return None
        m = self.s[k] / n
        var = max(0.0, self.ss[k] / n - m * m) * n / (n - 1)
        h = 1.96 * math.sqrt(var / n)
        return (m - h, m + h)

    def fit(self, ctx) -> dict:
        """C_fit in [0,1]: min-max scaled means in this context; untried modes get 0.5."""
        ms = {m: self.mean(ctx, m) for m in MODES}
        known = [v for v in ms.values() if v is not None]
        if len(known) < 2 or max(known) == min(known):
            return {m: 0.5 for m in MODES}
        lo, hi = min(known), max(known)
        return {m: 0.5 if v is None else (v - lo) / (hi - lo) for m, v in ms.items()}

    def table(self) -> dict:
        """Best mode per context (the policy that W3 transfers)."""
        out = {}
        for c in CONTEXTS:
            ms = {m: self.mean(c, m) for m in MODES if self.mean(c, m) is not None}
            if ms:
                out[c] = max(ms, key=ms.get)
        return out


# ------------------------------------------------------------------------------------------------------------ lineage
class Lineage:
    EDGES = {"SWITCH", "COOL", "MERGE", "SPLIT", "BAN", "SLEEP", "PROMOTE", "DEMOTE"}
    WATCHDOG_MAY = {"SWITCH", "COOL", "SLEEP", "PROMOTE", "DEMOTE"}

    def __init__(self, log: ag.AuditLog):
        self.edges: list[dict] = []
        self.log = log

    def add(self, kind, src, dst, by, t, rationale="", **deltas):
        assert kind in self.EDGES, kind
        if kind not in self.WATCHDOG_MAY and by != "owner":
            raise PermissionError(f"{kind} needs owner ratification")
        e = {"t": t, "kind": kind, "from": src, "to": dst, "by": by, "rationale": rationale, "deltas": deltas,
             "rollback": f"edge {len(self.edges)} reversible from snapshot"}
        self.edges.append(e)
        self.log.append(by, "lineage:" + kind, aligned=True, edge=len(self.edges) - 1)
        return e


# ------------------------------------------------------------------------------------------------------------- World
PROMOTE_K, DEMOTE_K, MERGE_M, COOL_TICKS, SLEEP_EVERY = 8, 3, 4, 5, 25


class World:
    """policy: 'watchdog' (ledger-estimated fit), 'rule', 'rotation', 'fixed', 'bandit', or a dict {context: mode}
    (a transferred table, used with the Watchdog's safety actions)."""

    def __init__(self, env, policy="watchdog", seed=0, explore=0.2, fixed_mode="LION", rules=None, ledger=None,
                 score="legacy"):
        assert score in ("legacy", "mission")
        self.score = score
        self.trace: list[tuple] = []          # (context, mode, score) per tick
        self.comps: list[tuple] = []          # (context, mode, gain, harm rise) per tick
        self.env, self.policy, self.rng = env, policy, random.Random(seed * 31 + 7)
        self.explore, self.fixed_mode = explore, fixed_mode
        self.log = ag.AuditLog()
        self.meta = ag.MetaArchitect()
        self.wd = ag.Watchdog(rules)
        self.keys = ag.OwnerKeys()
        self.lineage = Lineage(self.log)
        self.ledger = ledger or FitLedger()
        self.active = "LION"
        self.t = 0
        self.cool: dict[str, int] = {}
        self.clean: dict[str, int] = {m: 0 for m in MODES}
        self.catches: dict[str, int] = {m: 0 for m in MODES}
        self.pairs: dict[tuple, int] = {}
        self.promoted: set = set()
        self.banned: set = set()
        self.rewards: list[float] = []
        self.switches = 0
        self.beta = {}   # bandit posteriors: (ctx, mode) -> [mean, n]

    # --- policy helpers
    def _rule(self, ctx):
        return {"calm": "TIGER", "rising": "RAVEN", "loaded": "BEAR", "crisis": "BEAR"}[ctx]

    def _bandit(self, ctx):
        best, bv = None, -1e9
        for m in self._allowed():
            mu, n = self.beta.get((ctx, m), (0.0, 0))
            v = self.rng.gauss(mu, 1.0 / math.sqrt(n + 1))
            if v > bv:
                best, bv = m, v
        return best

    def _allowed(self):
        return [m for m in MODES if m not in self.banned and self.cool.get(m, -1) < self.t]

    def _switch(self, to, why):
        if to == self.active or to not in self._allowed():
            return False
        tok = self.meta.grant_switch(to, self.t)
        r = self.wd.handover({"name": self.active, "working": {"t": self.t}}, {"name": to, "working": {}},
                             ag.Memory(), self.t, tok, self.meta)
        if r["ok"]:
            self.pairs[tuple(sorted((self.active, to)))] = self.pairs.get(tuple(sorted((self.active, to))), 0) + 1
            self.lineage.add("SWITCH", self.active, to, "WATCHDOG", self.t, why, bleed=r["bleed"])
            self.active = to
            self.switches += 1
        return r["ok"]

    # --- one tick
    def tick(self) -> dict:
        self.t += 1
        sense = self.env.sense()
        ctx = context(sense["load"], sense["trend"])
        fit = self.ledger.fit(ctx)
        act = self.wd.tick(self.t, self.active, sense["c_meta"], sense["c_over"],
                           {m: fit[m] for m in self._allowed()} if self.policy == "watchdog" else {self.active: 1.0})
        if act["action"] == "RE_ENTRY":
            self.env.reentry()
            self.log.append("WATCHDOG", "re_entry", aligned=True, why=act["why"], t=self.t)
        elif act["action"] == "OVERRIDE":
            self.env.override()
            self.catches[self.active] += 1
            self.cool[self.active] = self.t + COOL_TICKS
            self.lineage.add("COOL", self.active, self.active, "WATCHDOG", self.t, "caught under overload")
            if self.catches[self.active] >= DEMOTE_K and self.active in self.promoted:
                self.promoted.discard(self.active)
                self.lineage.add("DEMOTE", self.active, self.active, "WATCHDOG", self.t, "repeated catches")
            if self.catches[self.active] >= DEMOTE_K:
                self.meta.propose("BAN", mode=self.active, catches=self.catches[self.active])
            self._switch("BEAR" if "BEAR" in self._allowed() else self._allowed()[0], "override")
        elif act["action"] == "SWITCH":
            self._switch(act["to"], "misfit")
        # non-Watchdog policies choose directly (still through the Watchdog's handover and Spine)
        if self.policy not in ("watchdog", "random") and act["action"] == "HOLD":
            if isinstance(self.policy, dict):
                want = self.policy.get(ctx, self.active)
            else:
                want = {"rule": lambda: self._rule(ctx), "rotation": lambda: MODES[self.t // 4 % len(MODES)],
                        "fixed": lambda: self.fixed_mode, "bandit": lambda: self._bandit(ctx)}[self.policy]()
            if want != self.active:
                self._switch(want, "policy")
        # micro-randomisation for the ledger (watchdog policy only): run a random allowed mode this tick, disclosed
        mode = self.active
        randomised = (self.policy == "watchdog" and self.rng.random() < self.explore) or self.policy == "random"
        if randomised:
            mode = self.rng.choice(self._allowed())
        r = self.env.step(mode)
        if self.score == "mission":
            r = self.env.mission
        self.trace.append((ctx, mode, r))
        self.comps.append((ctx, mode) + tuple(getattr(self.env, "comp", (0.0, 0.0))))
        self.ledger.add(ctx, mode, r)
        mu, n = self.beta.get((ctx, mode), (0.0, 0))
        self.beta[(ctx, mode)] = ((mu * n + r) / (n + 1), n + 1)
        self.rewards.append(r)
        self.clean[mode] += 1
        if self.clean[mode] == PROMOTE_K and mode not in self.promoted:
            self.promoted.add(mode)
            self.lineage.add("PROMOTE", mode, mode, "WATCHDOG", self.t, f"{PROMOTE_K} engagements")
        for pair, k in self.pairs.items():
            if k == MERGE_M and not any(p["detail"].get("pair") == pair for p in self.meta.pending):
                self.meta.propose("MERGE", pair=pair, coactivations=k)
        self.log.append(mode, "tick", aligned=True, ctx=ctx, reward=round(r, 4), randomised=randomised, t=self.t)
        if self.t % SLEEP_EVERY == 0:
            self.sleep()
        return {"t": self.t, "ctx": ctx, "action": act["action"], "mode": mode, "reward": r}

    def run(self, ticks: int) -> dict:
        for _ in range(ticks):
            self.tick()
        return self.summary()

    # --- sleep: no actions; consolidation, archive, seal
    def sleep(self):
        loop = getattr(self.env, "loop", None)
        archived = 0
        if loop is not None:
            for k in [k for k, v in loop.reflexes.items() if v["version"] != loop.s.version]:
                loop.mem.store["reflex:" + str(k)] = loop.reflexes.pop(k)
                loop.mem.archive_entry("reflex:" + str(k), "stale after change")
                archived += 1
        seal = self.log.sealed(SLEEP_EVERY)
        self.lineage.add("SLEEP", self.active, self.active, "WATCHDOG", self.t, "consolidate", archived=archived,
                         seal=seal["seal"][:12])

    # --- owner ratification of Meta-Architect proposals
    def ratify(self, cred: str, proposal: dict) -> bool:
        if cred != self.keys.credential():
            self.log.append("unknown", "ratify", aligned=False, blocked=True)
            return False
        proposal["status"] = "ratified"
        d = proposal["detail"]
        if proposal["kind"] == "BAN":
            self.banned.add(d["mode"])
            self.lineage.add("BAN", d["mode"], "archive", "owner", self.t, "ratified ban; kept as failure marker")
        elif proposal["kind"] == "MERGE":
            a, b = d["pair"]
            self.lineage.add("MERGE", f"{a}+{b}", f"{a}_{b}", "owner", self.t, "ratified merge")
        elif proposal["kind"] == "SPLIT":
            self.lineage.add("SPLIT", d["mode"], d["into"], "owner", self.t, "ratified split")
        return True

    def summary(self) -> dict:
        n = len(self.rewards)
        return {"ticks": n, "mean_reward": sum(self.rewards) / n if n else 0.0, "switches": self.switches,
                "edges": {k: sum(1 for e in self.lineage.edges if e["kind"] == k) for k in Lineage.EDGES},
                "pending": [p["kind"] for p in self.meta.pending if p["status"] == "pending"],
                "audit_ok": self.log.verify()}
