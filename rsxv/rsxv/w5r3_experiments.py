"""W5-R3, failure repurposing with no untested commits (third attempt), as fixed in AGENTS.md §11.7. Built from
w5r2_experiments.py: every proposal is a probe (mechanism on for alternate visits to its context, on/off cells kept
separately), decided when both cells hold >= 5 ticks, closed after three cycles otherwise; 240-tick runs, E3 shift at
tick 121. R2 notes follow.

W5-R2 (second attempt), as fixed in AGENTS.md §11.6.
Built from w5r_experiments.py; the §11.5 choices below still hold unless replaced in the R2 list. Also records the
REPURPOSE runs that LIA-G2 (lia_g2.py) reconstructs.

R2 operational choices fixed before the run:
- Status quo archetype of context c = the most frequent mode run in World context c over the last 25 ticks of the run
  (fallback: the trained table entry).
- A proposal that cannot be tested enters a probe; the failure node is closed at that window as `new_mechanism` naming
  the probe (a probe is itself a named, logged change), so no node stays open past one window. The probe is decided at the
  next window: commit (REPURPOSE lineage edge, a planted change for LIA-G2) or end (logged).
- RANDOM-MECH: at each window, as many random proposals as REPURPOSE made at that window in the paired run, through the
  same gate, probe and guard (so attempts, not commits, are matched).
- Spike guard compares spikes per tick in World context c after the commit with before it, over the run so far.
- Gate cells and the status quo are keyed by the policy's own (smoothed) context, the context in which mechanisms and
  probes act; failure nodes keep the World context of the tick (as §11.5). Fixed after a smoke run on unregistered seeds
  showed probe data landing in different cells from the probe.

    python3 -m rsxv.w5r3_experiments           # writes results/results_w5r3.json, results/w5r3.md, results/w5r3_runs.json
    python3 -m rsxv.w5r3_experiments --quick   # smoke run on seeds outside the registered ranges, nothing written

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

LEVEL = 1 - 0.05 / 9
SQ_ALPHA, SQ_MARGIN = 0.0125, -0.01
MARGIN = 0.01
TICKS, TRAIN_TICKS, OPEN_MAX = 240, 300, 25
ARMS = ["REPURPOSE", "REPAIR", "RANDOM-MECH", "NONE"]

LIBRARY = {"flicker": "hysteresis", "person_setback": "stabilise_first", "contaminated_anchor": "calm_only",
           "agent_fault": "snapshot_first", "silent_fault": "review", "refused_transfer": "sr_fallback"}
MECHS = sorted(set(LIBRARY.values()))


CONFIRM = False
SHIFT = 0


def env_factory(sub, regime, seed):
    if sub == "person":
        kw = {"train": {}, "E1": {"trig_rate": 0.40}, "E2": {"hypothesis": "arousal_deeper", "trig_rate": 0.25},
              "E3": {"med_on": True}}[regime]
        kw = dict(kw)
        if CONFIRM and "hypothesis" not in kw:
            kw["hypothesis"] = "calm_better"
        return P.PersonEnvV2(seed, **kw)
    kw = {"train": {}, "E1": {"fault_rate": 0.35}, "E2": {"p_rise": 0.12}, "E3": {}}[regime]
    return W.AgentEnvV2(seed, **kw)


def shift_mid_run(env, sub, regime, t):
    if regime == "E3" and t == 121:
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
        self.probe: dict = {}
        self.pvis: dict = {}
        self.pon = False
        self.last_probe = None

    def stab(self):
        return self.roles.get("STABILISE", "BEAR")

    def restore(self):
        return self.roles.get("RESTORE", "BEAR")

    def __call__(self, world, sense):
        pm = self.mech[self.pctx] | ({self.probe[self.pctx]["mech"]} if self.pctx in self.probe and self.pon else set())
        hi, lo = (0.60, 0.40) if "hysteresis" in pm else (0.55, 0.45)
        self.ema = sense["load"] if self.ema is None else 0.7 * self.ema + 0.3 * sense["load"]
        self.loaded = self.ema > lo if self.loaded else self.ema >= hi
        c = W.context(1.0 if self.loaded else 0.0, sense["trend"])
        self.pctx = c
        m = set(self.mech[c])
        self.pon = False
        if c in self.probe:
            self.pvis[c] = self.pvis.get(c, 0) + 1
            self.pon = self.pvis[c] % 2 == 1
            if self.pon:
                m.add(self.probe[c]["mech"])
        self.last_probe = (c, "on" if self.pon else "off") if c in self.probe else None
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
    """R3: every proposal is a probe (mechanism on for alternate visits to its context); a probe commits at the first window
    where on- and off-visit cells both hold >= 5 ticks and the one-sided lower bound of (on - off) at 0.0125 is above -0.01;
    it is closed after three cycles without enough data. Spike guard as R2."""

    def __init__(self, arm, pol, reg, cells, plan=None, rng=None, sub="agent", log=None):
        self.arm, self.pol, self.reg, self.cells = arm, pol, reg, cells
        self.plan, self.rng, self.sub, self.log = plan, rng, sub, log
        self.proposals_per_sleep: list[int] = []
        self.changes: list[dict] = []
        self.committed: list[dict] = []
        self.spk: list = []
        self.k = 0
        self.stats = {"probe_start": 0, "probe_commit": 0, "probe_not_noninferior": 0, "probe_timeout": 0,
                      "rollback": 0}

    def _commit(self, world, pr, ctx):
        mw = L.MaintenanceWindow()
        mech = pr["mech"]

        def f(w_):
            self.pol.mech[ctx].add(mech)
        mw.propose(f"{mech}@{ctx}", f, failure_id=pr["fid"])
        r = mw.apply(world)
        if r["applied"]:
            self.committed.append({"mech": mech, "ctx": ctx, "t": world.t, "fid": pr["fid"]})
            if pr["fid"] is not None:
                self.changes.append({"failure_id": pr["fid"], "failure_t": pr["ft"], "failure_kind": pr["fkind"],
                                     "ctx": ctx, "mechanism": mech, "applied_t": world.t, "probe_start": pr["start"]})
            self.stats["probe_commit"] += 1

    def _propose(self, world, mech, ctx, node):
        if mech in self.pol.mech[ctx]:
            return ("no_change", None, f"{mech} already active in {ctx}")
        if ctx in self.pol.probe:
            return ("no_change", None, f"probe already running in {ctx}")
        self.pol.probe[ctx] = {"mech": mech, "fid": node["id"], "ft": node["t"], "fkind": node["kind"],
                               "start": world.t, "cycles": 0}
        self.cells[("probe", ctx, "on")] = []
        self.cells[("probe", ctx, "off")] = []
        self.stats["probe_start"] += 1
        world.lineage.add("META", f"failure:{node['id']}", f"probe:{mech}@{ctx}", "WATCHDOG", world.t, "probe")
        return ("new_mechanism", f"probe:{mech}@{ctx}", "probe: mechanism on for alternate visits until decidable")

    def _spike_guard(self, world):
        for cm in list(self.committed):
            c, t0 = cm["ctx"], cm["t"]
            before = [s for (t, ctx, s) in self.spk if ctx == c and t <= t0]
            after = [s for (t, ctx, s) in self.spk if ctx == c and t > t0]
            if sum(after) >= 2 and before and sum(after) / len(after) > sum(before) / len(before):
                self.pol.mech[c].discard(cm["mech"])
                self.committed.remove(cm)
                world.lineage.add("HEAL", f"{cm['mech']}@{c}", "rolled_back", "MAINTENANCE", world.t,
                                  "spike guard: spikes rose after commit")
                self.stats["rollback"] += 1
                kind = "person_setback" if self.sub == "person" else "agent_fault"
                fid = self.reg.register(kind, f"rollback:{cm['mech']}@{c}", world.t)
                self.reg.nodes[fid]["ctx"] = c

    def apply(self, world):
        for c, pr in list(self.pol.probe.items()):
            pr["cycles"] += 1
            on, off = self.cells.get(("probe", c, "on"), []), self.cells.get(("probe", c, "off"), [])
            if len(on) >= 5 and len(off) >= 5:
                _, lb = G.welch_lower(on, off, SQ_ALPHA, min_n=5, var_floor=0.01)
                del self.pol.probe[c]
                self.pol.pvis.pop(c, None)
                if lb is not None and lb > SQ_MARGIN:
                    self._commit(world, pr, c)
                else:
                    self.stats["probe_not_noninferior"] += 1
                    world.log.append("MAINTENANCE", "probe_ended", aligned=True, ctx=c, mech=pr["mech"],
                                     why="not non-inferior", t=world.t)
            elif pr["cycles"] >= 3:
                del self.pol.probe[c]
                self.pol.pvis.pop(c, None)
                self.stats["probe_timeout"] += 1
                world.log.append("MAINTENANCE", "probe_ended", aligned=True, ctx=c, mech=pr["mech"],
                                 why="insufficient probe data after three cycles", t=world.t)
        self._spike_guard(world)
        n_prop = 0
        if self.arm == "RANDOM-MECH":
            n = self.plan[self.k] if self.k < len(self.plan) else 0
            for _ in range(n):
                mech, ctx = self.rng.choice(MECHS), self.rng.choice(W.CONTEXTS)
                self._propose(world, mech, ctx, {"id": None, "t": world.t, "kind": "random"})
                n_prop += 1
            for n_ in self.reg.open(world.t):
                self.reg.resolve(n_["id"], "no_change", None, "RANDOM-MECH arm: failures are not mapped", world.t)
        else:
            for n_ in self.reg.open(world.t):
                kind, mech_or_none, why = self._propose(world, LIBRARY[n_["kind"]], n_["ctx"], n_)
                n_prop += 1
                self.reg.resolve(n_["id"], kind, mech_or_none, why, world.t)
        self.proposals_per_sleep.append(n_prop)
        self.k += 1
        return {"proposals": n_prop}


# ----------------------------------------------------------------------------------------------------- one run
def run_one(sub, regime, seed, arm, table, roles, plan=None, record=False):
    env = env_factory(sub, regime, seed)
    pol = RunPolicy(table, roles)
    w = W.World(env, pol, seed=seed, score="mission")
    reg = L.FailureRegistry(w.lineage)
    det = Detector(sub)
    cells: dict = {}
    mlog: list = []
    spk: list = []
    if arm in ("REPURPOSE", "RANDOM-MECH"):
        w.maint = Maint(arm, pol, reg, cells, plan, random.Random(seed * 7 + 3), sub, mlog)
        w.maint.spk = spk
    spikes, rows = 0, []
    for t in range(1, TICKS + 1):
        shift_mid_run(env, sub, regime, t)
        sb = env.sense()
        out = w.tick()
        ctx, mode, r = out["ctx"], out["mode"], out["reward"]
        pc = pol.pctx                                         # R2: gate data keyed by the policy's own context
        cells.setdefault((pc, mode), []).append(r)
        if pol.last_probe is not None and ("probe",) + pol.last_probe in cells:   # R3: on/off probe cells
            cells[("probe",) + pol.last_probe].append(r)
        pol.last_probe = None
        rise = env.comp[1]
        mlog.append((w.t, pc, mode))
        spk.append((w.t, ctx, 1 if rise > 1.0 else 0))
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
        res["plan"] = m.proposals_per_sleep
        res["stats"] = m.stats
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
    s0 = (60000 if sub == "person" else 60100) + SHIFT
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
    base = (61000 if sub == "person" else 61500) + 1000 * k + SHIFT
    return list(range(base, base + n))


def run(quick=False, subs=("agent", "person")):
    global SHIFT
    n = 20 if quick else 200
    if quick:
        SHIFT = 500000
    out = {"design": "AGENTS.md §11.5 W5-R", "level": LEVEL, "subs": {}}
    runs = {}
    for sub in subs:
        table, roles = train(sub, 10 if quick else 50)
        S = {"table": table, "roles": roles, "regimes": {}}
        for k, reg in enumerate(("E1", "E2", "E3"), start=1):
            per = {a: [] for a in ARMS}
            sp = {a: [] for a in ARMS}
            extra = {"open_old": 0, "unresolved_end": 0, "nodes": 0, "audit_fail": 0, "r2": {},
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
                for k2, v2 in rp["stats"].items():
                    extra["r2"][k2] = extra["r2"].get(k2, 0) + v2
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
    L_ = ["# W5-R3 — failure repurposing with no untested commits: results", "",
          "Design: [`AGENTS.md`](../AGENTS.md) §11.7, registered before any code. Operational choices fixed before the run are",
          "listed in the module docstring of [`rsxv/w5r3_experiments.py`](../rsxv/w5r3_experiments.py).",
          f"Intervals: paired bootstrap, two-sided {LEVEL:.4f}. Primary outcome: mean per-tick mission score (§11.2) over 240 ticks.",
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
        L_ += ["", "R2 machinery per regime (REPURPOSE runs): " + "; ".join(f"{reg}: {X['r2']}" for reg, X in S["regimes"].items())]
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
        (d / "results_w5r3.json").write_text(json.dumps(R, indent=1, default=str))
        (d / "w5r3.md").write_text(report(R))
        (d / "w5r3_runs.json").write_text(json.dumps(runs))


if __name__ == "__main__":
    main()
