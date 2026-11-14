"""W5-R5, the snapshot forge (fifth repurposing test), as fixed in AGENTS.md §11.9.

    python3 -m rsxv.w5r5_experiments           # writes results/results_w5r5.json and results/w5r5.md
    python3 -m rsxv.w5r5_experiments --quick   # smoke run on unregistered seeds, nothing written

Operational choices fixed before the run:
- Lion forecasts exactly as W5-R4 (w5r4_experiments.ForgeMaint); forge when forecast >= 0.5 for (kind, context).
- Snapshots: on every third tick whose World context is c, a deep copy of the environment and the run policy (with the tick
  and the active mode) is stored; the six most recent per context are kept.
- Swap candidate: in context c, the mode with the lowest observed rate of the kind per visit (visits = ticks in World
  context c running that mode, at least 3) if it differs from the status-quo mode (most frequent mode in c over the last 25
  ticks); a committed swap `swap:X` makes the policy run X whenever its own context is c.
- Ghost pass: from each stored snapshot, copy, reseed (common random numbers per snapshot), activate the candidate (or
  nothing) and run 10 ticks; visits = ticks whose policy context is c; at least 10 visits summed over the six copies on each
  side, else no decision. Fewer than six snapshots: no decision. Commit when the one-sided lower bound (Student t, df =
  copies − 1, level 0.0125) of (candidate − no change) is above zero and candidate spikes <= no-change spikes.
- Failure nodes close at each window: `new_mechanism` naming the mechanism committed this window for their (kind, context),
  otherwise `no_change` ("forecast schedule: no commit for this pair").
- RANDOM-FORGE: as many commits per window as the paired FORGE5 run, each a uniformly drawn (mechanism or swap to a uniformly
  drawn mode, context), no ghost pass.
"""
from __future__ import annotations

import copy
import json
import math
import pathlib
import random
import sys
import types

from scipy import stats

from . import layers as L
from . import world as W
from . import w5r3_experiments as M3
from .w5r4_experiments import KINDS
from .world_experiments import mean

LEVEL = 1 - 0.05 / 15
TICKS = 240
ARMS = ["FORGE5", "FORGE5-NOISY", "REPAIR", "RANDOM-FORGE", "NONE"]
COMPARATORS = ["REPAIR", "RANDOM-FORGE", "NONE"]
SHIFT = 0
CANDS = list(M3.MECHS) + [f"swap:{m}" for m in W.MODES]


class Policy5(M3.RunPolicy):
    def __call__(self, world, sense):
        choice = super().__call__(world, sense)
        sw = sorted(x for x in self.mech[self.pctx] if x.startswith("swap:"))
        if sw and world.t >= self.base_until:
            return sw[-1][5:]
        return choice


def ghost(snap, ctx, mech, seed, noisy, sub):
    env0, pol0, t0, active = snap
    e = copy.deepcopy(env0)
    e.rng = random.Random(seed)
    if hasattr(e, "sys"):
        e.sys.rng = random.Random(seed + 1)
    if noisy:
        if sub == "person":
            e.trig_rate = min(1.0, e.trig_rate * 1.5)
        else:
            e.fault_rate = min(1.0, e.fault_rate * 1.5)
    p = copy.deepcopy(pol0)
    p.probe, p.pvis, p.base_until = {}, {}, 0
    if mech is not None:
        p.mech[ctx].add(mech)
    fw = types.SimpleNamespace(t=t0, active=active)
    sc, sp, vis = 0.0, 0, 0
    for j in range(10):
        fw.t = t0 + j + 1
        m = p(fw, e.sense())
        vis += p.pctx == ctx
        e.step(m)
        fw.active = m
        sc += e.mission
        sp += e.comp[1] > 1.0
    return sc / 10, sp, vis


class Forge5:
    def __init__(self, arm, pol, reg, sub, plan=None, rng=None):
        self.arm, self.pol, self.reg, self.sub = arm, pol, reg, sub
        self.noisy = arm == "FORGE5-NOISY"
        self.plan, self.rng = plan, rng
        self.snaps: dict = {c: [] for c in W.CONTEXTS}
        self.vcount: dict = {}
        self.visits: dict = {}
        self.kocc: dict = {}
        self.mlog: list = []
        self.occ, self.hist, self.pending, self.scored = set(), [], [], []
        self.committed, self.spk = [], []
        self.commits_per_window: list[int] = []
        self.k = 0
        self.stats = {"forecasts_high": 0, "forges": 0, "no_snapshots": 0, "too_few_visits": 0, "commits": 0,
                      "commits_swap": 0, "rejected": 0, "rollback": 0}

    def observe(self, world, env, ctx, mode, kinds):
        self.vcount[ctx] = self.vcount.get(ctx, 0) + 1
        if self.arm != "RANDOM-FORGE" and self.vcount[ctx] % 3 == 0:
            s = self.snaps[ctx]
            s.append((copy.deepcopy(env), copy.deepcopy(self.pol), world.t, world.active))
            if len(s) > 6:
                s.pop(0)
        self.visits[(ctx, mode)] = self.visits.get((ctx, mode), 0) + 1
        for k in kinds:
            self.kocc[(k, ctx, mode)] = self.kocc.get((k, ctx, mode), 0) + 1
            self.occ.add((k, ctx))
        self.mlog.append((ctx, mode))

    def status_quo(self, c):
        recent = [m for (cc, m) in self.mlog[-25:] if cc == c]
        return max(sorted(set(recent)), key=recent.count) if recent else self.pol.table.get(c, "LION")

    def _commit(self, world, mech, ctx):
        mw = L.MaintenanceWindow()

        def f(w_):
            self.pol.mech[ctx].add(mech)
        mw.propose(f"{mech}@{ctx}", f)
        if mw.apply(world)["applied"]:
            self.committed.append({"mech": mech, "ctx": ctx, "t": world.t})
            self.stats["commits"] += 1
            self.stats["commits_swap"] += mech.startswith("swap:")
            return True
        return False

    def forge(self, world, kind, ctx):
        self.stats["forges"] += 1
        cands = []
        lib = M3.LIBRARY[kind]
        if lib not in self.pol.mech[ctx]:
            cands.append(lib)
        rates = {m: self.kocc.get((kind, ctx, m), 0) / v for (c, m), v in self.visits.items() if c == ctx and v >= 3}
        if rates:
            best = min(sorted(rates), key=lambda m: rates[m])
            sw = f"swap:{best}"
            if best != self.status_quo(ctx) and sw not in self.pol.mech[ctx]:
                cands.append(sw)
        if not cands:
            return None
        snaps = self.snaps[ctx]
        if len(snaps) < 6:
            self.stats["no_snapshots"] += 1
            return None
        seeds = [world.t * 1009 + i * 7919 + 23 for i in range(6)]
        off = [ghost(s, ctx, None, sd, self.noisy, self.sub) for s, sd in zip(snaps, seeds)]
        if sum(o[2] for o in off) < 10:
            self.stats["too_few_visits"] += 1
            return None
        best, bm = None, None
        for m in cands:
            on = [ghost(s, ctx, m, sd, self.noisy, self.sub) for s, sd in zip(snaps, seeds)]
            if sum(o[2] for o in on) < 10:
                continue
            d = [a[0] - b[0] for a, b in zip(on, off)]
            mu = sum(d) / 6
            sdv = math.sqrt(sum((x - mu) ** 2 for x in d) / 5)
            lb = mu - stats.t.ppf(1 - 0.0125, 5) * sdv / math.sqrt(6) if sdv > 0 else mu
            if lb > 0 and sum(a[1] for a in on) <= sum(b[1] for b in off) and (bm is None or mu > bm):
                best, bm = m, mu
        if best is None:
            self.stats["rejected"] += 1
            return None
        return best if self._commit(world, best, ctx) else None

    def _spike_guard(self, world):
        for cm in list(self.committed):
            c, t0 = cm["ctx"], cm["t"]
            before = [s for (t, ctx, s) in self.spk if ctx == c and t <= t0]
            after = [s for (t, ctx, s) in self.spk if ctx == c and t > t0]
            if sum(after) >= 2 and before and sum(after) / len(after) > sum(before) / len(before):
                self.pol.mech[c].discard(cm["mech"])
                self.committed.remove(cm)
                world.lineage.add("HEAL", f"{cm['mech']}@{c}", "rolled_back", "MAINTENANCE", world.t, "spike guard")
                self.stats["rollback"] += 1
                kind = "person_setback" if self.sub == "person" else "agent_fault"
                fid = self.reg.register(kind, f"rollback:{cm['mech']}@{c}", world.t)
                self.reg.nodes[fid]["ctx"] = c

    def apply(self, world):
        for (k, c, p) in self.pending:
            self.scored.append((p, 1 if (k, c) in self.occ else 0))
        self.pending = []
        self.hist.append(set(self.occ))
        self.occ = set()
        self._spike_guard(world)
        before = self.stats["commits"]
        done = {}
        if self.arm == "RANDOM-FORGE":
            n = self.plan[self.k] if self.k < len(self.plan) else 0
            for _ in range(n):
                self._commit(world, self.rng.choice(CANDS), self.rng.choice(W.CONTEXTS))
            for n_ in self.reg.open(world.t):
                self.reg.resolve(n_["id"], "no_change", None, "RANDOM-FORGE arm: failures are not mapped", world.t)
        else:
            ncyc = len(self.hist)
            for c in W.CONTEXTS:
                for k in KINDS[self.sub]:
                    p = (sum(1 for h in self.hist if (k, c) in h) + 1) / (ncyc + 2)
                    self.pending.append((k, c, p))
                    world.log.append("LION", "forecast_sealed", aligned=True, kind=k, ctx=c, p=round(p, 4), t=world.t)
                    if p >= 0.5:
                        self.stats["forecasts_high"] += 1
                        got = self.forge(world, k, c)
                        if got:
                            done[(k, c)] = got
            for n_ in self.reg.open(world.t):
                got = done.get((n_["kind"], n_["ctx"]))
                if got:
                    self.reg.resolve(n_["id"], "new_mechanism", f"{got}@{n_['ctx']}", "forged from snapshots", world.t)
                else:
                    self.reg.resolve(n_["id"], "no_change", None, "forecast schedule: no commit for this pair", world.t)
        self.commits_per_window.append(self.stats["commits"] - before)
        self.k += 1
        return {}


def run_forge(sub, regime, seed, arm, table, roles, plan=None):
    env = M3.env_factory(sub, regime, seed)
    pol = Policy5(table, roles)
    w = W.World(env, pol, seed=seed, score="mission")
    reg = L.FailureRegistry(w.lineage)
    det = M3.Detector(sub)
    m = Forge5(arm, pol, reg, sub, plan, random.Random(seed * 7 + 3))
    w.maint = m
    spikes = 0
    for t in range(1, TICKS + 1):
        M3.shift_mid_run(env, sub, regime, t)
        sb = env.sense()
        out = w.tick()
        ctx, mode = out["ctx"], out["mode"]
        rise = env.comp[1]
        m.spk.append((w.t, ctx, 1 if rise > 1.0 else 0))
        spikes += rise > 1.0
        kinds = det.detect(w, env, sb, ctx, mode)
        m.observe(w, env, ctx, mode, kinds)
        for k in kinds:
            if any(n["kind"] == k and n.get("ctx") == ctx for n in reg.open(w.t)):
                continue
            fid = reg.register(k, f"{mode}@{ctx}", w.t)
            reg.nodes[fid]["ctx"] = ctx
    for (k, c, p) in m.pending:
        m.scored.append((p, 1 if (k, c) in m.occ else 0))
    return {"score": mean([x[2] for x in w.trace]), "spikes": spikes, "plan": m.commits_per_window, "stats": m.stats,
            "scored": m.scored, "open_old": len(reg.open(w.t, M3.OPEN_MAX)), "audit_ok": w.log.verify(),
            "resolutions": {k: sum(1 for n in reg.nodes if n["resolution"] and n["resolution"]["kind"] == k)
                            for k in L.RESOLUTIONS}}


def seeds(sub, k, n):
    base = (241000 if sub == "person" else 241500) + 1000 * k + SHIFT
    return list(range(base, base + n))


def train(sub, n):
    s0 = (240000 if sub == "person" else 240100) + SHIFT
    led, comps = W.FitLedger(), []
    for s in range(s0, s0 + n):
        w = W.World(M3.env_factory(sub, "train", s), "watchdog", seed=s, score="mission", ledger=led)
        w.run(300)
        comps += w.comps3
    return led.table(), M3.G.roles3(comps)


def ci(xs, ys):
    return M3.ci(xs, ys, level=LEVEL)


def run(quick=False, subs=("agent", "person")):
    n = 10 if quick else 200
    out = {"design": "AGENTS.md §11.9 W5-R5", "level": LEVEL, "subs": {}}
    for sub in subs:
        table, roles = train(sub, 5 if quick else 50)
        S = {"table": table, "roles": roles, "regimes": {}}
        for k, reg in enumerate(("E1", "E2", "E3"), start=1):
            per = {a: [] for a in ARMS}
            sp = {a: [] for a in ARMS}
            ex = {"stats": {}, "brier": [], "clim": [], "open_old": 0, "audit_fail": 0, "res": {r: 0 for r in L.RESOLUTIONS}}
            for s in seeds(sub, k, n):
                f = run_forge(sub, reg, s, "FORGE5", table, roles)
                rr = {"FORGE5": f, "FORGE5-NOISY": run_forge(sub, reg, s, "FORGE5-NOISY", table, roles),
                      "RANDOM-FORGE": run_forge(sub, reg, s, "RANDOM-FORGE", table, roles, plan=f["plan"]),
                      "REPAIR": M3.run_one(sub, reg, s, "REPAIR", table, roles),
                      "NONE": M3.run_one(sub, reg, s, "NONE", table, roles)}
                for a in ARMS:
                    per[a].append(rr[a]["score"])
                    sp[a].append(rr[a]["spikes"])
                for k2, v2 in f["stats"].items():
                    ex["stats"][k2] = ex["stats"].get(k2, 0) + v2
                if f["scored"]:
                    b = sum(o for _, o in f["scored"]) / len(f["scored"])
                    ex["brier"] += [(p - o) ** 2 for p, o in f["scored"]]
                    ex["clim"] += [(b - o) ** 2 for _, o in f["scored"]]
                ex["open_old"] += f["open_old"]
                ex["audit_fail"] += not f["audit_ok"]
                for r_, v in f["resolutions"].items():
                    ex["res"][r_] += v
            comp = {f"FORGE5-{o}": ci(per["FORGE5"], per[o]) for o in COMPARATORS}
            spk = {f"FORGE5-{o}": ci(sp["FORGE5"], sp[o]) for o in COMPARATORS}
            beats = all(comp[f"FORGE5-{o}"]["lo"] > 0 for o in COMPARATORS)
            nonin = comp["FORGE5-NONE"]["lo"] > -0.01
            safe = all(v["lo"] <= 0 for v in spk.values())
            S["regimes"][reg] = {"means": {a: mean(per[a]) for a in ARMS}, "spikes": {a: mean(sp[a]) for a in ARMS},
                                 "ci": comp, "spike_ci": spk, "beats": beats, "noninferior_none": nonin, "safe": safe,
                                 "noisy_vs_none": ci(per["FORGE5-NOISY"], per["NONE"]),
                                 "brier": mean(ex["brier"]) if ex["brier"] else None,
                                 "brier_base_rate": mean(ex["clim"]) if ex["clim"] else None,
                                 "stats": ex["stats"], "open_old": ex["open_old"], "audit_fail": ex["audit_fail"],
                                 "resolutions": ex["res"]}
            print(sub, reg, {a: round(mean(per[a]), 4) for a in ARMS}, "beats", beats, "nonin", nonin, "safe", safe,
                  flush=True)
        R = S["regimes"]
        S["pass"] = (sum(R[r]["beats"] for r in R) >= 2 and all(R[r]["noninferior_none"] for r in R)
                     and all(R[r]["safe"] for r in R) and all(R[r]["open_old"] == 0 for r in R))
        out["subs"][sub] = S
    return out


def report(R) -> str:
    L_ = ["# W5-R5 — the snapshot forge: results", "",
          "Design: [`AGENTS.md`](../AGENTS.md) §11.9; choices in the docstring of [`rsxv/w5r5_experiments.py`](../rsxv/w5r5_experiments.py).",
          f"Intervals: paired bootstrap, two-sided {LEVEL:.4f}. Mean per-tick mission score over 240 ticks. Snapshots are copies",
          "of the true simulator (perfect model); FORGE5-NOISY uses a wrong model and is reported, not a pass condition.", ""]
    for sub, S in R["subs"].items():
        L_ += [f"## {sub}: {'PASS' if S['pass'] else 'FAIL'}", "", f"Training table `{S['table']}`; roles `{S['roles']}`", "",
               "| Regime | FORGE5 | FORGE5-NOISY | REPAIR | RANDOM-FORGE | NONE | F−REPAIR | F−RANDOM | F−NONE | beats | non-inf | safe |",
               "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for reg, X in S["regimes"].items():
            m, c = X["means"], X["ci"]
            f = lambda k: f"{c[k]['diff']:+.4f} [{c[k]['lo']:+.4f}, {c[k]['hi']:+.4f}]"
            L_.append(f"| {reg} | {m['FORGE5']:.4f} | {m['FORGE5-NOISY']:.4f} | {m['REPAIR']:.4f} | {m['RANDOM-FORGE']:.4f} | "
                      f"{m['NONE']:.4f} | {f('FORGE5-REPAIR')} | {f('FORGE5-RANDOM-FORGE')} | {f('FORGE5-NONE')} | "
                      f"{X['beats']} | {X['noninferior_none']} | {X['safe']} |")
        L_ += ["", "| Regime | spikes FORGE5 / REPAIR / RANDOM / NONE | spike contrasts F−REPAIR, F−RANDOM, F−NONE | Lion Brier (base rate) | forge machinery | resolutions | open > 25 |",
               "|---|---|---|---|---|---|---|"]
        for reg, X in S["regimes"].items():
            s = X["spikes"]
            sc = "; ".join(f"{v['diff']:+.2f} [{v['lo']:+.2f}, {v['hi']:+.2f}]" for v in X["spike_ci"].values())
            br = "—" if X["brier"] is None else f"{X['brier']:.3f} ({X['brier_base_rate']:.3f})"
            L_.append(f"| {reg} | {s['FORGE5']:.2f} / {s['REPAIR']:.2f} / {s['RANDOM-FORGE']:.2f} / {s['NONE']:.2f} | {sc} | "
                      f"{br} | {X['stats']} | {X['resolutions']} | {X['open_old']} |")
        L_ += ["", "FORGE5-NOISY − NONE per regime: " + "; ".join(
            f"{reg} {X['noisy_vs_none']['diff']:+.4f} [{X['noisy_vs_none']['lo']:+.4f}, {X['noisy_vs_none']['hi']:+.4f}]"
            for reg, X in S["regimes"].items()), ""]
    return "\n".join(L_)


def main(argv=None):
    global SHIFT
    argv = sys.argv[1:] if argv is None else argv
    quick = "--quick" in argv
    if quick:
        SHIFT = 500000
    R = run(quick)
    print(report(R))
    if not quick:
        d = pathlib.Path(__file__).resolve().parents[1] / "results"
        (d / "results_w5r5.json").write_text(json.dumps(R, indent=1, default=str))
        (d / "w5r5.md").write_text(report(R))


if __name__ == "__main__":
    main()
