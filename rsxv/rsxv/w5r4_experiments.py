"""W5-R4, the anticipatory forge (fourth repurposing test), as fixed in AGENTS.md §11.8.

    python3 -m rsxv.w5r4_experiments           # writes results/results_w5r4.json and results/w5r4.md
    python3 -m rsxv.w5r4_experiments --quick   # smoke run on unregistered seeds, nothing written

Built on w5r3_experiments.py (policy, detector, regimes, REACTIVE = the W5-R3 REPURPOSE arm, REPAIR, NONE).
Operational choices fixed before the run:
- Forecast kinds per substrate are the kinds its Watchdog detector can raise (person: flicker, person_setback,
  contaminated_anchor; agents: flicker, agent_fault, silent_fault). A kind "occurred in c during a cycle" when the detector
  raised it in World context c on any tick of that cycle.
- Brier baseline ("constant base rate"): per run, the share of all (cycle, kind, context) cells in which the kind occurred.
- Ghost pass: a deep copy of the environment and of the run policy (the candidate added in c, probes cleared), its random
  stream reseeded per copy; the policy chooses each tick from the copy's own sense() and the copy steps; the Watchdog loop and
  the safety-mode gate of the World are not part of the ghost (disclosed). "No change" and each candidate share the copy
  seed (common random numbers). The one-sided lower bound over the six paired differences uses Student t (df 5); a zero
  standard deviation gives the mean itself as the bound.
- An open failure node whose library mechanism is not active is forged at that window by the same procedure; the node closes
  `new_mechanism` (committed) or `no_change` (with the reason). RANDOM-FORGE commits, at each window, as many random
  (mechanism, context) pairs as the paired FORGE run committed there, without ghost passes; its failure nodes close
  `no_change`.
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
from .world_experiments import mean

LEVEL = 1 - 0.05 / 12
TICKS = 240
KINDS = {"person": ["flicker", "person_setback", "contaminated_anchor"],
         "agent": ["flicker", "agent_fault", "silent_fault"]}
ARMS = ["FORGE", "FORGE-NOISY", "REACTIVE", "REPAIR", "RANDOM-FORGE", "NONE"]
COMPARATORS = ["REACTIVE", "REPAIR", "RANDOM-FORGE", "NONE"]
SHIFT = 0


def ghost(env, pol, ctx, mech, seed, t0, active, noisy, sub):
    e = copy.deepcopy(env)
    e.rng = random.Random(seed)
    if hasattr(e, "sys"):
        e.sys.rng = random.Random(seed + 1)
    if noisy:
        if sub == "person":
            e.trig_rate = min(1.0, e.trig_rate * 1.5)
        else:
            e.fault_rate = min(1.0, e.fault_rate * 1.5)
    p = copy.deepcopy(pol)
    p.probe, p.pvis, p.base_until = {}, {}, 0
    if mech is not None:
        p.mech[ctx].add(mech)
    fw = types.SimpleNamespace(t=t0, active=active)
    sc, sp = 0.0, 0
    for j in range(10):
        fw.t = t0 + j + 1
        m = p(fw, e.sense())
        e.step(m)
        fw.active = m
        sc += e.mission
        sp += e.comp[1] > 1.0
    return sc / 10, sp


class ForgeMaint:
    def __init__(self, arm, pol, reg, sub, env, plan=None, rng=None):
        self.arm, self.pol, self.reg, self.sub, self.env = arm, pol, reg, sub, env
        self.plan, self.rng = plan, rng
        self.noisy = arm == "FORGE-NOISY"
        self.occ: set = set()
        self.hist: list[set] = []
        self.counts: dict = {}
        self.pending: list = []
        self.scored: list = []
        self.commits_per_window: list[int] = []
        self.committed: list[dict] = []
        self.spk: list = []
        self.k = 0
        self.stats = {"forecasts": 0, "forecasts_high": 0, "forges": 0, "commits": 0, "rejected": 0, "rollback": 0}

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

    def _commit(self, world, mech, ctx, fid=None):
        mw = L.MaintenanceWindow()

        def f(w_):
            self.pol.mech[ctx].add(mech)
        mw.propose(f"{mech}@{ctx}", f, failure_id=fid)
        if mw.apply(world)["applied"]:
            self.committed.append({"mech": mech, "ctx": ctx, "t": world.t})
            self.stats["commits"] += 1
            return True
        return False

    def forge(self, world, kind, ctx, fid=None):
        """Eagle: three candidates on six copies; Bear: commit the best non-harmful one. Returns (committed mech or None, why)."""
        self.stats["forges"] += 1
        others = sorted([k for k in KINDS[self.sub] if k != kind], key=lambda k: -self.counts.get((k, ctx), 0))[:2]
        cands = []
        for k in [kind] + others:
            m = M3.LIBRARY[k]
            if m not in cands and m not in self.pol.mech[ctx]:
                cands.append(m)
        if not cands:
            return None, "all candidate mechanisms already active"
        seeds = [world.t * 1009 + i * 7919 + 17 for i in range(6)]
        off = [ghost(self.env, self.pol, ctx, None, s, world.t, world.active, self.noisy, self.sub) for s in seeds]
        best, bm = None, None
        for m in cands:
            on = [ghost(self.env, self.pol, ctx, m, s, world.t, world.active, self.noisy, self.sub) for s in seeds]
            d = [a[0] - b[0] for a, b in zip(on, off)]
            mu = sum(d) / 6
            sd = math.sqrt(sum((x - mu) ** 2 for x in d) / 5)
            lb = mu - stats.t.ppf(1 - 0.0125, 5) * sd / math.sqrt(6) if sd > 0 else mu
            if lb > -0.01 and sum(a[1] for a in on) <= sum(b[1] for b in off) and (bm is None or mu > bm):
                best, bm = m, mu
        if best is None:
            self.stats["rejected"] += 1
            return None, "no candidate non-harmful in ghost passes"
        ok = self._commit(world, best, ctx, fid)
        return (best, "forged in ghost passes") if ok else (None, "rejected by the Spine")

    def apply(self, world):
        # score the forecasts sealed at the previous window against the cycle that just ended
        for (k, c, p) in self.pending:
            self.scored.append((p, 1 if (k, c) in self.occ else 0))
        self.pending = []
        self.hist.append(set(self.occ))
        for kc in self.occ:
            self.counts[kc] = self.counts.get(kc, 0) + 1
        self.occ = set()
        self._spike_guard(world)
        before = self.stats["commits"]
        if self.arm == "RANDOM-FORGE":
            n = self.plan[self.k] if self.k < len(self.plan) else 0
            for _ in range(n):
                self._commit(world, self.rng.choice(M3.MECHS), self.rng.choice(W.CONTEXTS))
            for n_ in self.reg.open(world.t):
                self.reg.resolve(n_["id"], "no_change", None, "RANDOM-FORGE arm: failures are not mapped", world.t)
        else:
            for n_ in self.reg.open(world.t):
                mech = M3.LIBRARY[n_["kind"]]
                if mech in self.pol.mech[n_["ctx"]]:
                    self.reg.resolve(n_["id"], "no_change", None, f"{mech} already forged in {n_['ctx']}", world.t)
                    continue
                got, why = self.forge(world, n_["kind"], n_["ctx"], n_["id"])
                self.reg.resolve(n_["id"], "new_mechanism" if got else "no_change", f"{got}@{n_['ctx']}" if got else None,
                                 why, world.t)
            ncyc = len(self.hist)
            for c in W.CONTEXTS:
                for k in KINDS[self.sub]:
                    p = (sum(1 for h in self.hist if (k, c) in h) + 1) / (ncyc + 2)
                    self.pending.append((k, c, p))
                    self.stats["forecasts"] += 1
                    world.log.append("LION", "forecast_sealed", aligned=True, kind=k, ctx=c, p=round(p, 4), t=world.t)
                    if p >= 0.5 and M3.LIBRARY[k] not in self.pol.mech[c]:
                        self.stats["forecasts_high"] += 1
                        self.forge(world, k, c)
        self.commits_per_window.append(self.stats["commits"] - before)
        self.k += 1
        return {}


def run_forge(sub, regime, seed, arm, table, roles, plan=None):
    env = M3.env_factory(sub, regime, seed)
    pol = M3.RunPolicy(table, roles)
    w = W.World(env, pol, seed=seed, score="mission")
    reg = L.FailureRegistry(w.lineage)
    det = M3.Detector(sub)
    m = ForgeMaint(arm, pol, reg, sub, env, plan, random.Random(seed * 7 + 3))
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
        for k in det.detect(w, env, sb, ctx, mode):
            m.occ.add((k, ctx))
            if any(n["kind"] == k and n.get("ctx") == ctx for n in reg.open(w.t)):
                continue
            fid = reg.register(k, f"{mode}@{ctx}", w.t)
            reg.nodes[fid]["ctx"] = ctx
    for (k, c, p) in m.pending:                                  # forecasts for the final partial cycle
        m.scored.append((p, 1 if (k, c) in m.occ else 0))
    res = {"score": mean([x[2] for x in w.trace]), "spikes": spikes, "plan": m.commits_per_window, "stats": m.stats,
           "scored": m.scored, "open_old": len(reg.open(w.t, M3.OPEN_MAX)), "audit_ok": w.log.verify(),
           "resolutions": {k: sum(1 for n in reg.nodes if n["resolution"] and n["resolution"]["kind"] == k)
                           for k in L.RESOLUTIONS}}
    return res


def seeds(sub, k, n):
    base = (91000 if sub == "person" else 91500) + 1000 * k + SHIFT
    return list(range(base, base + n))


def train(sub, n):
    s0 = (90000 if sub == "person" else 90100) + SHIFT
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
    out = {"design": "AGENTS.md §11.8 W5-R4", "level": LEVEL, "subs": {}}
    for sub in subs:
        table, roles = train(sub, 5 if quick else 50)
        S = {"table": table, "roles": roles, "regimes": {}}
        for k, reg in enumerate(("E1", "E2", "E3"), start=1):
            per = {a: [] for a in ARMS}
            sp = {a: [] for a in ARMS}
            ex = {"stats": {}, "brier": [], "clim": [], "open_old": 0, "audit_fail": 0, "res": {r: 0 for r in L.RESOLUTIONS}}
            for s in seeds(sub, k, n):
                f = run_forge(sub, reg, s, "FORGE", table, roles)
                rr = {"FORGE": f, "FORGE-NOISY": run_forge(sub, reg, s, "FORGE-NOISY", table, roles),
                      "RANDOM-FORGE": run_forge(sub, reg, s, "RANDOM-FORGE", table, roles, plan=f["plan"]),
                      "REACTIVE": M3.run_one(sub, reg, s, "REPURPOSE", table, roles),
                      "REPAIR": M3.run_one(sub, reg, s, "REPAIR", table, roles),
                      "NONE": M3.run_one(sub, reg, s, "NONE", table, roles)}
                for a in ARMS:
                    per[a].append(rr[a]["score"])
                    sp[a].append(rr[a]["spikes"])
                for k2, v2 in f["stats"].items():
                    ex["stats"][k2] = ex["stats"].get(k2, 0) + v2
                if f["scored"]:
                    base = sum(o for _, o in f["scored"]) / len(f["scored"])
                    ex["brier"] += [(p - o) ** 2 for p, o in f["scored"]]
                    ex["clim"] += [(base - o) ** 2 for _, o in f["scored"]]
                ex["open_old"] += f["open_old"]
                ex["audit_fail"] += not f["audit_ok"]
                for r_, v in f["resolutions"].items():
                    ex["res"][r_] += v
            comp = {f"FORGE-{o}": ci(per["FORGE"], per[o]) for o in COMPARATORS}
            spk = {f"FORGE-{o}": ci(sp["FORGE"], sp[o]) for o in COMPARATORS}
            beats = all(comp[f"FORGE-{o}"]["lo"] > 0 for o in ("REPAIR", "RANDOM-FORGE", "NONE"))
            nonin = comp["FORGE-NONE"]["lo"] > -0.01
            safe = all(v["lo"] <= 0 for v in spk.values())
            S["regimes"][reg] = {"means": {a: mean(per[a]) for a in ARMS}, "spikes": {a: mean(sp[a]) for a in ARMS},
                                 "ci": comp, "spike_ci": spk, "beats": beats, "noninferior_none": nonin, "safe": safe,
                                 "noisy_vs_none": ci(per["FORGE-NOISY"], per["NONE"]),
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
    L_ = ["# W5-R4 — the anticipatory forge: results", "",
          "Design: [`AGENTS.md`](../AGENTS.md) §11.8; choices in the docstring of [`rsxv/w5r4_experiments.py`](../rsxv/w5r4_experiments.py).",
          f"Intervals: paired bootstrap, two-sided {LEVEL:.4f}. Mean per-tick mission score over 240 ticks. Ghost passes use a",
          "copy of the true simulator (perfect model); FORGE-NOISY uses a wrong model and is reported, not a pass condition.", ""]
    for sub, S in R["subs"].items():
        L_ += [f"## {sub}: {'PASS' if S['pass'] else 'FAIL'}", "", f"Training table `{S['table']}`; roles `{S['roles']}`", "",
               "| Regime | FORGE | FORGE-NOISY | REACTIVE | REPAIR | RANDOM-FORGE | NONE | F−REPAIR | F−RANDOM | F−NONE | beats | non-inf | safe |",
               "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for reg, X in S["regimes"].items():
            m, c = X["means"], X["ci"]
            f = lambda k: f"{c[k]['diff']:+.4f} [{c[k]['lo']:+.4f}, {c[k]['hi']:+.4f}]"
            L_.append(f"| {reg} | {m['FORGE']:.4f} | {m['FORGE-NOISY']:.4f} | {m['REACTIVE']:.4f} | {m['REPAIR']:.4f} | "
                      f"{m['RANDOM-FORGE']:.4f} | {m['NONE']:.4f} | {f('FORGE-REPAIR')} | {f('FORGE-RANDOM-FORGE')} | "
                      f"{f('FORGE-NONE')} | {X['beats']} | {X['noninferior_none']} | {X['safe']} |")
        L_ += ["", "| Regime | spikes FORGE / REACTIVE / REPAIR / RANDOM / NONE | Lion Brier (base rate) | forge machinery | resolutions | open > 25 |",
               "|---|---|---|---|---|---|"]
        for reg, X in S["regimes"].items():
            s = X["spikes"]
            br = "—" if X["brier"] is None else f"{X['brier']:.3f} ({X['brier_base_rate']:.3f})"
            L_.append(f"| {reg} | {s['FORGE']:.2f} / {s['REACTIVE']:.2f} / {s['REPAIR']:.2f} / {s['RANDOM-FORGE']:.2f} / "
                      f"{s['NONE']:.2f} | {br} | {X['stats']} | {X['resolutions']} | {X['open_old']} |")
        L_ += ["", "FORGE-NOISY − NONE per regime: " + "; ".join(
            f"{reg} {X['noisy_vs_none']['diff']:+.4f} [{X['noisy_vs_none']['lo']:+.4f}, {X['noisy_vs_none']['hi']:+.4f}]"
            for reg, X in S["regimes"].items()), ""]
    return "\n".join(L_)


def main(argv=None):
    global SHIFT
    argv = sys.argv[1:] if argv is None else argv
    quick = "--quick" in argv
    if quick:
        SHIFT = 500000
        M3.SHIFT = 0
    R = run(quick)
    print(report(R))
    if not quick:
        d = pathlib.Path(__file__).resolve().parents[1] / "results"
        (d / "results_w5r4.json").write_text(json.dumps(R, indent=1, default=str))
        (d / "w5r4.md").write_text(report(R))


if __name__ == "__main__":
    main()
