"""Person model v2 and mission score v2 (step R3). Specification: ../AGENTS.md §11.5 (design) and the private build plan.

Stated model, not data. Adds to sim.Body (via world.PersonEnv):
  triggers        cue events that raise distress and arousal, scaled by the person's sensitivity gain (two-way: the same
                  gain scales module benefit);
  capture         a trigger captures the person (crisis) when arousal crosses CAPTURE_AROUSAL, otherwise it coexists;
  chains          while a trigger is unresolved, each tick it propagates one hop unless a module interrupts it;
  module          an anchor/procedure whose activation probability depends on the state it was trained in
                  (state-dependent learning); the install hypothesis is a switch: neutral, arousal_deeper, calm_better;
  medication      a covariate that lowers trigger impact and baseline arousal (a confound by design);
  vividness       per cue, up on successful activations, down on failed ones;
  safety          a safety.SafetyState observed every tick; World gates mode categories through the Spine.
Outcome measures: return latency, chain length before interruption, coexistence share, calm-transfer, rumination
seconds, vividness, and mission score v2 (safety > depth > agency, compared lexicographically).
"""
from __future__ import annotations

from . import safety as sf
from . import world as W

CAPTURE_AROUSAL = 0.8
INTERRUPTERS = {"BEAR", "RAVEN", "TIGER"}          # modes that can fire the module to interrupt a chain
HYPOTHESES = ("neutral", "arousal_deeper", "calm_better")


class Module:
    """State-dependent procedural module. Activation probability in state s:
    strength * (match(s) + CROSS * (1 - match(s))), match = share of training reps done in state s."""
    CROSS = 0.3

    def __init__(self, hypothesis="neutral"):
        assert hypothesis in HYPOTHESES
        self.h = hypothesis
        self.reps = {"calm": 0.0, "activated": 0.0}
        self.vivid = 0.5

    def train(self, state: str):
        w = 1.0
        if self.h == "arousal_deeper" and state == "activated":
            w = 1.5
        if self.h == "calm_better" and state == "calm":
            w = 1.5
        self.reps[state] += w

    @property
    def strength(self) -> float:
        n = self.reps["calm"] + self.reps["activated"]
        return n / (n + 10.0)

    def p_work(self, state: str) -> float:
        n = self.reps["calm"] + self.reps["activated"]
        if n == 0:
            return 0.0
        match = self.reps[state] / n
        return self.strength * (match + self.CROSS * (1 - match))

    def calm_transfer(self, threshold: float = 0.5) -> bool:
        """Installed only if it works from calm (calm-transfer criterion)."""
        return self.p_work("calm") >= threshold * self.strength if self.strength > 0 else False


class PersonEnvV2(W.PersonEnv):
    def __init__(self, seed: int, pid: int = 1, model=None, hypothesis="neutral", med_on=False, trig_rate=0.15,
                 safety_on=True, gain=None):
        super().__init__(seed, pid, model)
        self.gain = float(gain if gain is not None else self.body.p["resp"])
        self.med_on = med_on
        if med_on:
            self.body.s["arousal"] = max(0.1, self.body.s["arousal"] - 0.1)
        self.trig_rate = trig_rate
        self.module = Module(hypothesis)
        self.safety = sf.SafetyState() if safety_on else None
        self.base_d = self.body.s["distress"]
        self.events: list[dict] = []
        self.open: dict | None = None
        self.rumination_s = 0
        self.ticks = 0
        self.calm_ticks_below4 = 0
        self.mode_counts: dict[str, int] = {}

    def _state(self) -> str:
        return "activated" if self.body.s["arousal"] >= 0.6 else "calm"

    def _trigger(self):
        k = self.gain * (0.5 if self.med_on else 1.0)
        s = self.body.s
        s["distress"] = min(10.0, s["distress"] + 1.5 * k)
        s["arousal"] = min(1.0, s["arousal"] + 0.25 * k)
        captured = s["arousal"] >= CAPTURE_AROUSAL
        self.open = {"t": self.ticks, "captured": captured, "chain": 0, "interrupted": None, "resolved": None}
        self.events.append(self.open)

    def step(self, mode: str) -> float:
        self.ticks += 1
        self.mode_counts[mode] = self.mode_counts.get(mode, 0) + 1
        s = self.body.s
        a0, d0 = s["agency"], s["distress"]
        if self.open is None and self.rng.random() < self.trig_rate:
            self._trigger()
        st = self._state()
        if mode == "TIGER":                                  # cue rehearsal trains the module in the current state
            self.module.train(st)
        if self.open is not None and self.open["interrupted"] is None:
            fired = mode in INTERRUPTERS and self.rng.random() < self.module.p_work(st)
            if fired:
                self.open["interrupted"] = self.ticks
                self.module.vivid = min(1.0, self.module.vivid + 0.05)
                s["arousal"] = max(0.0, s["arousal"] - 0.15 * self.gain)   # two-way gain: benefit scales too
                s["distress"] = max(0.0, s["distress"] - 0.5 * self.gain)
            else:
                if mode in INTERRUPTERS and self.module.strength > 0:
                    self.module.vivid = max(0.0, self.module.vivid - 0.02)
                self.open["chain"] += 1
                s["distress"] = min(10.0, s["distress"] + 0.3 * self.gain * (0.5 if self.med_on else 1.0))
                self.rumination_s += W.SEGMENT_S
        for _ in range(W.SEGMENT_S):
            self.body.step(W.PERSON_MODES[mode])
        if self.open is not None and self.open["interrupted"] is not None and s["distress"] <= self.base_d + 0.5:
            self.open["resolved"] = self.ticks
            self.open = None
        if self.safety is not None:
            self.safety.observe({"distress": s["distress"]})
            self.calm_ticks_below4 = self.calm_ticks_below4 + 1 if s["distress"] < 4 else 0
            if self.safety.mode == "STABILISE" and self.calm_ticks_below4 >= 3:
                self.safety.exit("person")                   # the simulated person chooses to leave STABILISE
        rise = s["distress"] - d0
        self.mission = (s["agency"] - a0) - 2.0 * rise - (1.0 if rise > 1.0 else 0.0)
        self.comp = (s["agency"] - a0, rise)
        self.comp3 = (s["agency"] - a0, rise, 0.0)
        self.prev_harm = d0 / 10
        return self.mission

    # ------------------------------------------------------------------ outcome measures
    def outcomes(self) -> dict:
        ev = self.events
        done = [e for e in ev if e["resolved"] is not None]
        inter = [e for e in ev if e["interrupted"] is not None]
        return {
            "triggers": len(ev),
            "return_latency": sum(e["resolved"] - e["t"] for e in done) / len(done) if done else None,
            "chain_length": sum(e["chain"] for e in inter) / len(inter) if inter else None,
            "unresolved": len(ev) - len(done),
            "coexistence_share": sum(not e["captured"] for e in ev) / len(ev) if ev else None,
            "calm_transfer": self.module.calm_transfer(),
            "p_work_calm": self.module.p_work("calm"),
            "p_work_activated": self.module.p_work("activated"),
            "rumination_s": self.rumination_s,
            "vividness": self.module.vivid,
            "agency": self.body.s["agency"],
            "distress": self.body.s["distress"],
            "crisis_ticks": sum(1 for e in ev if e["captured"]),
        }


def mission_v2(o: dict, safety_blocks: int = 0) -> tuple:
    """(safety, depth, agency), each higher is better; compare with mission_better (lexicographic, with tolerance)."""
    safety = -(o["crisis_ticks"] + o["unresolved"] + 2 * max(0.0, o["distress"] - 7.0))
    depth = 0.0
    if o["return_latency"] is not None:
        depth -= o["return_latency"]
    if o["chain_length"] is not None:
        depth -= o["chain_length"]
    if o["coexistence_share"] is not None:
        depth += 5 * o["coexistence_share"]
    depth += 3 if o["calm_transfer"] else 0
    return (round(safety, 4), round(depth, 4), round(o["agency"], 4))


def mission_better(a: tuple, b: tuple, tol=(0.5, 0.5, 0.0)) -> bool:
    """True if a beats b: first tier that differs beyond its tolerance decides."""
    for x, y, t in zip(a, b, tol):
        if x > y + t:
            return True
        if y > x + t:
            return False
    return False
