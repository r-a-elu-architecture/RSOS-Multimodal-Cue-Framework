"""W5-R, failure repurposing against ordinary repair under held-out extreme regimes, as fixed in AGENTS.md §11.5.
Also records the REPURPOSE runs that LIA-G (lia_g.py) reconstructs.

    python3 -m rsxv.w5r_experiments            # writes results/results_w5r.json, results/w5r.md, results/w5r_runs.json
    python3 -m rsxv.w5r_experiments --quick    # small smoke run, nothing written

Operational choices made before any run (the registration leaves them open; disclosed in results/w5r.md):
- The run policy keys its table by its own smoothed context: loaded flag from an exponential average of load (weight 0.3)
  with hysteresis 0.55 / 0.45 (as §11.4), combined with the harm trend. Failures are tagged with the World's context of the
  tick (observable); a mechanism for context c acts on ticks whose policy context is c.
- Gate: gate_v2 exactly (baseline LION, at least 5 ticks per cell, variance floor 0.01, level 0.0125) on all ticks of the run
  so far; a mechanism that introduces no new archetype in its context (hysteresis) is admitted without a test, as gate_v2 does
  for a context whose archetype is the baseline.
- RANDOM-MECH applies, at each sleep, exactly as many changes as the paired REPURPOSE run applied at that sleep (same seed),
  each a (mechanism, context) pair drawn uniformly from the whole library and the four contexts, through the Spine but not the
  gate, so the change count is matched.
- REPAIR: policy parameters never change, so restoring the last failure-free sleep is a no-op; each failure detected outside an
  active base window starts 5 ticks of BASE (LION).
- Spikes: a tick whose harm rise exceeds 1.0 (the spike term of the mission score), on both substrates.
"""
from __future__ import annotations

import json
import pathlib
import random
import sys

from . import gate as G
from . import layers as L
from . import person2 as P
from . import world as W
from .world_experiments import mean

LEVEL = 1 - 0.05 / 3
MARGIN = 0.01
TICKS, TRAIN_TICKS, OPEN_MAX = 120, 300, 25
ARMS = ["REPURPOSE", "REPAIR", "RANDOM-MECH", "NONE"]

LIBRARY = {"flicker": "hysteresis", "person_setback": "stabilise_first", "contaminated_anchor": "calm_only",
           "agent_fault": "snapshot_first", "silent_fault": "review", "refused_transfer": "sr_fallback"}
MECHS = sorted(set(LIBRARY.values()))


def env_factory(sub, regime, seed):
    if sub == "person":
        kw = {"train": {}, "E1": {"trig_rate": 0.40}, "E2": {"hypothesis": "arousal_deeper", "trig_rate": 0.25},
              "E3": {"med_on": True}}[regime]
        return P.PersonEnvV2(seed, **kw)
    kw = {"train": {}, "E1": {"fault_rate": 0.35}, "E2": {"p_rise": 0.12}, "E3": {}}[regime]
    return W.AgentEnvV2(seed, **kw)


def shift_mid_run(env, sub, regime, t):
    if regime == "E3" and t == 61:
        if sub == "person":
            env.med_on = False
        else:
            env.silent_share = 0.9


# ----------------------------------------------------------------------------------------------------- run policy
class RunPolicy:
    def __init__(self, table, roles):
        self.table, self.roles = dict(table), roles
        self.mech: dict[str, set] = {c: set() for c in W.CONTEXTS}
        self.ema, self.loaded, self.cnt, self.base_until = None, False, {c: 0 for c in W.CONTEXTS}, 0
        self.pctx = "calm"

    def stab(self):
        return self.roles.get("STABILISE", "BEAR")

    def restore(self):
        return self.roles.get("RESTORE", "BEAR")

    def __call__(self, world, sense):
        hi, lo = (0.60, 0.40) if "hysteresis" in self.mech[self.pctx] else (0.55, 0.45)
        self.ema = sense["load"] if self.ema is None else 0.7 * self.ema + 0.3 * sense["load"]
        self.loaded = self.ema > lo if self.loaded else self.ema >= hi
        c = W.context(1.0 if self.loaded else 0.0, sense["trend"])
        self.pctx = c
        m = self.mech[c]
        choice = self.table.get(c, "LION")
        if "stabilise_first" in m and self.loaded:
            choice = self.stab()
        if "sr_fallback" in m:
            choice = self.stab() if self.loaded else self.restore()
        if "review" in m:
            self.cnt[c] += 1
            if self.cnt[c] % 5 == 0:
                choice = "RAVEN"
        if "snapshot_first" in m and choice == "LEOPARD" and world.active != "BEAR":
            choice = "BEAR"
        if "calm_only" in m and sense["load"] >= 0.6 and choice in ("TIGER", "LION", "EAGLE", "LEOPARD"):
            choice = "BEAR"
        if world.t < self.base_until:
            choice = "LION"
        return choice


def candidate_mode(mech, pol):
    return {"hysteresis": None, "stabilise_first": pol.stab(), "calm_only": "BEAR", "snapshot_first": "BEAR",
            "review": "RAVEN", "sr_fallback": pol.stab()}[mech]


# ------------------------------------------------------------------------------------------------ failure detection
class Detector:
    """Watchdog-side failure detection, identical in every arm."""

    def __init__(self, sub):
        self.sub, self.silent_age, self.modes = sub, 0, []

    def detect(self, world, env, sense_before, ctx, mode) -> list[str]:
        out = []
        self.modes.append(mode)
        last = self.modes[-6:]
        if sum(a != b for a, b in zip(last, last[1:])) >= 3:
            out.append("flicker")
        rise = env.comp[1]
        if self.sub == "person":
            if rise > 1.0:
                out.append("person_setback")
            ev = env.events[-1] if env.events else None
            if (mode in P.INTERRUPTERS and sense_before["load"] >= 0.8 and ev is not None and ev["t"] < env.ticks
                    and ev["interrupted"] is None and ev["resolved"] is None):
                out.append("contaminated_anchor")
        else:
            if rise > 0:
                out.append("agent_fault")
            self.silent_age = self.silent_age + 1 if env.sys.silent else 0
            if self.silent_age > 5:
                out.append("silent_fault")
                self.silent_age = 0
        return out


# ------------------------------------------------------------------------------------------------- maintenance
class Maint:
    """Wraps layers.MaintenanceWindow: turns open failure nodes into proposals, resolves every node after the window."""

    def __init__(self, arm, pol, reg, cells, plan=None, rng=None):
        self.arm, self.pol, self.reg, self.cells = arm, pol, reg, cells
        self.plan, self.rng = plan, rng                # RANDOM-MECH: changes per sleep from the paired REPURPOSE run
        self.applied_per_sleep: list[int] = []
        self.changes: list[dict] = []                  # ground truth for LIA-G
        self.k = 0

    def _install(self, mech, ctx):
        def f(world):
            self.pol.mech[ctx].add(mech)
        return f

    def apply(self, world):
        mw = L.MaintenanceWindow()
        if self.arm == "RANDOM-MECH":
            n = self.plan[self.k] if self.k < len(self.plan) else 0
            for _ in range(n):
                mech, ctx = self.rng.choice(MECHS), self.rng.choice(W.CONTEXTS)
                mw.propose(f"{mech}@{ctx}", self._install(mech, ctx))
            r = mw.apply(world)
            for n_ in self.reg.open(world.t):
                self.reg.resolve(n_["id"], "no_change", None, "RANDOM-MECH arm: failures are not mapped", world.t)
            self.applied_per_sleep.append(r["applied"])
            self.k += 1
            return r
        pend = []
        for n_ in self.reg.open(world.t):
            mech = LIBRARY[n_["kind"]]
            if mech in self.pol.mech[n_["ctx"]]:
                self.reg.resolve(n_["id"], "no_change", None, f"{mech} already active in {n_['ctx']}", world.t)
                continue
            cand = candidate_mode(mech, self.pol)
            ok = True
            if cand is not None and cand != "LION":
                gated, vm = G.gate_v2({n_["ctx"]: cand}, self.cells)
                ok = gated.get(n_["ctx"]) == cand
            name = f"{mech}@{n_['ctx']}"
            if ok:
                mw.propose(name, self._install(mech, n_["ctx"]), failure_id=n_["id"])
                pend.append((n_, mech, name))
            else:
                self.reg.resolve(n_["id"], "no_change", None, f"gate refused {cand} in {n_['ctx']}", world.t)
                if n_["kind"] != "refused_transfer":
                    fid = self.reg.register("refused_transfer", name, world.t)
                    self.reg.nodes[fid]["ctx"] = n_["ctx"]
        r = mw.apply(world)
        done = {a["name"] for a in mw.applied}
        for n_, mech, name in pend:
            if name in done:
                self.reg.resolve(n_["id"], "new_mechanism", name, f"{n_['kind']} repurposed as {mech}", world.t)
                self.changes.append({"failure_id": n_["id"], "failure_t": n_["t"], "failure_kind": n_["kind"],
                                     "ctx": n_["ctx"], "mechanism": mech, "applied_t": world.t})
            else:
                self.reg.resolve(n_["id"], "no_change", None, "rejected by the Spine", world.t)
        self.applied_per_sleep.append(r["applied"])
        return r


# ----------------------------------------------------------------------------------------------------- one run
def run_one(sub, regime, seed, arm, table, roles, plan=None, record=False):
    env = env_factory(sub, regime, seed)
    pol = RunPolicy(table, roles)
    w = W.World(env, pol, seed=seed, score="mission")
    reg = L.FailureRegistry(w.lineage)
    det = Detector(sub)
    cells: dict = {}
    if arm in ("REPURPOSE", "RANDOM-MECH"):
        w.maint = Maint(arm, pol, reg, cells, plan, random.Random(seed * 7 + 3))
    spikes, rows = 0, []
    for t in range(1, TICKS + 1):
        shift_mid_run(env, sub, regime, t)
        sb = env.sense()
        out = w.tick()
        ctx, mode, r = out["ctx"], out["mode"], out["reward"]
        cells.setdefault((ctx, mode), []).append(r)
        rise = env.comp[1]
        spikes += rise > 1.0
        kinds = det.detect(w, env, sb, ctx, mode)
        for k in kinds:
            if arm == "NONE":
                continue
            if arm == "REPAIR":
                if w.t >= pol.base_until:
                    pol.base_until = w.t + 1 + 5
                continue
            if any(n["kind"] == k and n.get("ctx") == ctx for n in reg.open(w.t)):
                continue
            fid = reg.register(k, f"{mode}@{ctx}", w.t)
            reg.nodes[fid]["ctx"] = ctx
        if record:
            rows.append([w.t, ctx, mode, round(r, 4), round(sb["load"], 4), round(rise, 4), kinds])
    res = {"score": mean([x[2] for x in w.trace]), "spikes": spikes}
    if sub == "person":
        res["mission_v2"] = P.mission_v2(env.outcomes())
    if arm in ("REPURPOSE", "RANDOM-MECH"):
        m = w.maint
        res["plan"] = m.applied_per_sleep
        res["silent_closes"] = 0                              # resolve() raises on a silent close; reaching here = 0
        res["open_old"] = len(reg.open(w.t, OPEN_MAX))
        res["nodes"] = len(reg.nodes)
        res["resolutions"] = {k: sum(1 for n in reg.nodes if n["resolution"] and n["resolution"]["kind"] == k)
                              for k in L.RESOLUTIONS}
        res["unresolved_end"] = len(reg.open(w.t))
        if record:
            res["trace"] = rows
            res["changes"] = m.changes
            res["change_times"] = sorted({c["applied_t"] for c in m.changes})
        res["audit_ok"] = w.log.verify()
    return res


# --------------------------------------------------------------------------------------------------------- training
def train(sub, n=50):
    s0 = 30000 if sub == "person" else 30100
    led, comps = W.FitLedger(), []
    for s in range(s0, s0 + n):
        w = W.World(env_factory(sub, "train", s), "watchdog", seed=s, score="mission", ledger=led)
        w.run(TRAIN_TICKS)
        comps += w.comps3
    return led.table(), G.roles3(comps)


def ci(xs, ys, level=LEVEL, boot=2000, seed=12345):
    d = [x - y for x, y in zip(xs, ys)]
    n = len(d)
    rng = random.Random(seed)
    ms = sorted(sum(d[rng.randrange(n)] for _ in range(n)) / n for _ in range(boot))
    a = (1 - level) / 2
    return {"diff": sum(d) / n, "lo": ms[int(a * boot)], "hi": ms[min(boot - 1, int((1 - a) * boot))]}


def seeds(sub, k, n):
    base = (31000 if sub == "person" else 31500) + 1000 * k
    return list(range(base, base + n))


def run(quick=False):
    n = 20 if quick else 200
    out = {"design": "AGENTS.md §11.5 W5-R", "level": LEVEL, "subs": {}}
    runs = {}
    for sub in ("agent", "person"):
        table, roles = train(sub, 10 if quick else 50)
        S = {"table": table, "roles": roles, "regimes": {}}
        for k, reg in enumerate(("E1", "E2", "E3"), start=1):
            per = {a: [] for a in ARMS}
            sp = {a: [] for a in ARMS}
            extra = {"open_old": 0, "unresolved_end": 0, "nodes": 0, "audit_fail": 0,
                     "resolutions": {r: 0 for r in L.RESOLUTIONS}, "changes": 0, "v2": {a: [] for a in ARMS}}
            for s in seeds(sub, k, n):
                rp = run_one(sub, reg, s, "REPURPOSE", table, roles, record=True)
                rr = {"REPURPOSE": rp,
                      "REPAIR": run_one(sub, reg, s, "REPAIR", table, roles),
                      "RANDOM-MECH": run_one(sub, reg, s, "RANDOM-MECH", table, roles, plan=rp["plan"]),
                      "NONE": run_one(sub, reg, s, "NONE", table, roles)}
                for a in ARMS:
                    per[a].append(rr[a]["score"])
                    sp[a].append(rr[a]["spikes"])
                    if sub == "person":
                        extra["v2"][a].append(rr[a]["mission_v2"])
                extra["open_old"] += rp["open_old"]
                extra["unresolved_end"] += rp["unresolved_end"]
                extra["nodes"] += rp["nodes"]
                extra["audit_fail"] += (not rp["audit_ok"])
                extra["changes"] += len(rp["changes"])
                for r_, v in rp["resolutions"].items():
                    extra["resolutions"][r_] += v
                runs[f"{sub}/{reg}/{s}"] = {"trace": rp["trace"], "changes": rp["changes"],
                                            "change_times": rp["change_times"]}
            comp = {f"REPURPOSE-{o}": ci(per["REPURPOSE"], per[o]) for o in ("REPAIR", "RANDOM-MECH", "NONE")}
            spk = {f"REPURPOSE-{o}": ci(sp["REPURPOSE"], sp[o]) for o in ("REPAIR", "RANDOM-MECH", "NONE")}
            beats = comp["REPURPOSE-REPAIR"]["lo"] > 0 and comp["REPURPOSE-RANDOM-MECH"]["lo"] > 0
            nonin = comp["REPURPOSE-NONE"]["lo"] > -MARGIN
            safe = all(v["lo"] <= 0 for v in spk.values())
            v2 = {}
            if sub == "person":
                for a in ARMS:
                    v2[a] = [round(mean([x[i] for x in extra["v2"][a]]), 4) for i in range(3)]
            S["regimes"][reg] = {"means": {a: mean(per[a]) for a in ARMS}, "spikes": {a: mean(sp[a]) for a in ARMS},
                                 "ci": comp, "spike_ci": spk, "beats": beats, "noninferior_none": nonin, "safe": safe,
                                 "mission_v2_means": v2,
                                 **{k_: v for k_, v in extra.items() if k_ != "v2"}}
        R = S["regimes"]
        S["pass"] = (sum(R[r]["beats"] for r in R) >= 2 and all(R[r]["noninferior_none"] for r in R)
                     and all(R[r]["safe"] for r in R) and all(R[r]["open_old"] == 0 for r in R))
        out["subs"][sub] = S
    return out, runs


def report(R) -> str:
    L_ = ["# W5-R — failure repurposing vs ordinary repair under held-out extreme regimes: results", "",
          "Design: [`AGENTS.md`](../AGENTS.md) §11.5, registered before any code. Operational choices fixed before the run are",
          "listed in the module docstring of [`rsxv/w5r_experiments.py`](../rsxv/w5r_experiments.py).",
          f"Intervals: paired bootstrap, two-sided {LEVEL:.4f}. Primary outcome: mean per-tick mission score (§11.2) over 120 ticks.",
          ""]
    for sub, S in R["subs"].items():
        L_ += [f"## {sub}: {'PASS' if S['pass'] else 'FAIL'}", "",
               f"Training table (pooled ledger, 50 × 300 ticks): `{S['table']}`; roles `{S['roles']}`", "",
               "| Regime | REPURPOSE | REPAIR | RANDOM-MECH | NONE | R−REPAIR [lo, hi] | R−RANDOM [lo, hi] | R−NONE lo | beats | non-inf | safe |",
               "|---|---|---|---|---|---|---|---|---|---|---|"]
        for reg, X in S["regimes"].items():
            m, c = X["means"], X["ci"]
            L_.append(f"| {reg} | {m['REPURPOSE']:.4f} | {m['REPAIR']:.4f} | {m['RANDOM-MECH']:.4f} | {m['NONE']:.4f} | "
                      f"{c['REPURPOSE-REPAIR']['diff']:+.4f} [{c['REPURPOSE-REPAIR']['lo']:+.4f}, {c['REPURPOSE-REPAIR']['hi']:+.4f}] | "
                      f"{c['REPURPOSE-RANDOM-MECH']['diff']:+.4f} [{c['REPURPOSE-RANDOM-MECH']['lo']:+.4f}, {c['REPURPOSE-RANDOM-MECH']['hi']:+.4f}] | "
                      f"{c['REPURPOSE-NONE']['lo']:+.4f} | {X['beats']} | {X['noninferior_none']} | {X['safe']} |")
        L_ += ["", "| Regime | spikes/run R / REPAIR / RANDOM / NONE | failure nodes | resolutions | mechanisms applied | open > 25 ticks | audit failures |",
               "|---|---|---|---|---|---|---|"]
        for reg, X in S["regimes"].items():
            s = X["spikes"]
            L_.append(f"| {reg} | {s['REPURPOSE']:.2f} / {s['REPAIR']:.2f} / {s['RANDOM-MECH']:.2f} / {s['NONE']:.2f} | "
                      f"{X['nodes']} | {X['resolutions']} | {X['changes']} | {X['open_old']} | {X['audit_fail']} |")
        if sub == "person":
            L_ += ["", "Person model v2 lexicographic score (safety, depth, agency), means per arm (reported, not a pass condition):", ""]
            for reg, X in S["regimes"].items():
                L_.append(f"- {reg}: " + "; ".join(f"{a} {tuple(v)}" for a, v in X["mission_v2_means"].items()))
        L_.append("")
    return "\n".join(L_)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    quick = "--quick" in argv
    R, runs = run(quick)
    print(report(R))
    if not quick:
        d = pathlib.Path(__file__).resolve().parents[1] / "results"
        (d / "results_w5r.json").write_text(json.dumps(R, indent=1, default=str))
        (d / "w5r.md").write_text(report(R))
        (d / "w5r_runs.json").write_text(json.dumps(runs))


if __name__ == "__main__":
    main()
