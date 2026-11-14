"""W5-R6, the snapshot forge with re-verification (sixth repurposing test), as fixed in AGENTS.md §11.10.

    python3 -m rsxv.w5r6_experiments            # primary run: results/results_w5r6.json, results/w5r6.md
    python3 -m rsxv.w5r6_experiments --confirm agent [person]   # confirmation (+100000): results/*_w5r6_confirmation.*
    python3 -m rsxv.w5r6_experiments --quick    # smoke run on unregistered seeds, nothing written

W5-R5 (w5r5_experiments.py) plus, at every window before new forging:
- re-verification: each committed mechanism re-tested from the six most recent snapshots of its context, policy copy with the
  mechanism vs the same copy without it, common random numbers, 10 ticks, >= 10 visits to the context on each side;
  decommissioned (HEAL edge, new failure node in that context) when the one-sided lower bound at 0.0125 of (with − without)
  is not above zero; kept and re-tested later when visits are too few;
- score-drop guard: decommissioned when the context's mean score over the last cycle is more than 0.05 below its mean over
  the cycle before the commit (>= 5 ticks in each).
Operational choices fixed before the run: "cycle" = the 25 ticks before a window; "the cycle before the commit" = the 25
ticks before the commit window; a mechanism committed at this window is first re-verified at the next one; FORGE5 (the
§11.9 arm without re-verification) runs as a reported ablation.
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
from . import w5r5_experiments as M5
from .world_experiments import mean

LEVEL = 1 - 0.05 / 18
TICKS = 240
ARMS = ["FORGE6", "FORGE6-NOISY", "FORGE5", "REPAIR", "RANDOM-FORGE", "NONE"]
COMPARATORS = ["REPAIR", "RANDOM-FORGE", "NONE"]
SHIFT = 0


def ghost2(snap, ctx, add, remove, seed, noisy, sub):
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
    if remove is not None:
        p.mech[ctx].discard(remove)
    if add is not None:
        p.mech[ctx].add(add)
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


class Forge6(M5.Forge5):
    def __init__(self, *a, reverify=True, **k):
        super().__init__(*a, **k)
        self.reverify = reverify
        self.slog: list = []
        for key in ("reverified", "decommissioned_reverify", "decommissioned_scoredrop", "reverify_too_few"):
            self.stats[key] = 0

    def _decommission(self, world, cm, why, key):
        self.pol.mech[cm["ctx"]].discard(cm["mech"])
        self.committed.remove(cm)
        world.lineage.add("HEAL", f"{cm['mech']}@{cm['ctx']}", "decommissioned", "MAINTENANCE", world.t, why)
        self.stats[key] += 1
        kind = "person_setback" if self.sub == "person" else "agent_fault"
        fid = self.reg.register(kind, f"decommissioned:{cm['mech']}@{cm['ctx']}", world.t)
        self.reg.nodes[fid]["ctx"] = cm["ctx"]

    def _reverify(self, world):
        for cm in list(self.committed):
            if cm["t"] >= world.t:
                continue
            c = cm["ctx"]
            # score-drop guard
            last = [r for (t, cc, r) in self.slog if cc == c and world.t - 25 < t <= world.t]
            prev = [r for (t, cc, r) in self.slog if cc == c and cm["t"] - 25 < t <= cm["t"]]
            if len(last) >= 5 and len(prev) >= 5 and mean(last) < mean(prev) - 0.05:
                self._decommission(world, cm, "score-drop guard", "decommissioned_scoredrop")
                continue
            snaps = self.snaps[c]
            if len(snaps) < 6:
                continue
            seeds = [world.t * 1013 + i * 7907 + 31 for i in range(6)]
            on = [ghost2(s, c, cm["mech"], None, sd, self.noisy, self.sub) for s, sd in zip(snaps, seeds)]
            off = [ghost2(s, c, None, cm["mech"], sd, self.noisy, self.sub) for s, sd in zip(snaps, seeds)]
            if sum(o[2] for o in on) < 10 or sum(o[2] for o in off) < 10:
                self.stats["reverify_too_few"] += 1
                continue
            self.stats["reverified"] += 1
            d = [a[0] - b[0] for a, b in zip(on, off)]
            mu = sum(d) / 6
            sdv = math.sqrt(sum((x - mu) ** 2 for x in d) / 5)
            lb = mu - stats.t.ppf(1 - 0.0125, 5) * sdv / math.sqrt(6) if sdv > 0 else mu
            if not lb > 0:
                self._decommission(world, cm, "re-verification: no longer shown to improve", "decommissioned_reverify")

    def apply(self, world):
        if self.reverify and self.arm != "RANDOM-FORGE":
            self._reverify(world)
        return super().apply(world)


def run_forge6(sub, regime, seed, arm, table, roles, plan=None):
    env = M3.env_factory(sub, regime, seed)
    pol = M5.Policy5(table, roles)
    w = W.World(env, pol, seed=seed, score="mission")
    reg = L.FailureRegistry(w.lineage)
    det = M3.Detector(sub)
    inner = {"FORGE6": "FORGE5", "FORGE6-NOISY": "FORGE5-NOISY", "FORGE5": "FORGE5", "RANDOM-FORGE": "RANDOM-FORGE"}[arm]
    m = Forge6(inner, pol, reg, sub, plan, random.Random(seed * 7 + 3), reverify=arm in ("FORGE6", "FORGE6-NOISY"))
    w.maint = m
    spikes = 0
    for t in range(1, TICKS + 1):
        M3.shift_mid_run(env, sub, regime, t)
        sb = env.sense()
        out = w.tick()
        ctx, mode = out["ctx"], out["mode"]
        rise = env.comp[1]
        m.spk.append((w.t, ctx, 1 if rise > 1.0 else 0))
        m.slog.append((w.t, ctx, out["reward"]))
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
    base = (251000 if sub == "person" else 251500) + 1000 * k + SHIFT
    return list(range(base, base + n))


def train(sub, n):
    s0 = (250000 if sub == "person" else 250100) + SHIFT
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
    out = {"design": "AGENTS.md §11.10 W5-R6", "level": LEVEL, "subs": {}}
    for sub in subs:
        table, roles = train(sub, 5 if quick else 50)
        S = {"table": table, "roles": roles, "regimes": {}}
        for k, reg in enumerate(("E1", "E2", "E3"), start=1):
            per = {a: [] for a in ARMS}
            sp = {a: [] for a in ARMS}
            ex = {"stats": {}, "brier": [], "clim": [], "open_old": 0, "audit_fail": 0, "res": {r: 0 for r in L.RESOLUTIONS}}
            for s in seeds(sub, k, n):
                f = run_forge6(sub, reg, s, "FORGE6", table, roles)
                rr = {"FORGE6": f, "FORGE6-NOISY": run_forge6(sub, reg, s, "FORGE6-NOISY", table, roles),
                      "FORGE5": run_forge6(sub, reg, s, "FORGE5", table, roles),
                      "RANDOM-FORGE": run_forge6(sub, reg, s, "RANDOM-FORGE", table, roles, plan=f["plan"]),
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
            comp = {f"FORGE6-{o}": ci(per["FORGE6"], per[o]) for o in COMPARATORS}
            spk = {f"FORGE6-{o}": ci(sp["FORGE6"], sp[o]) for o in COMPARATORS}
            beats = all(comp[f"FORGE6-{o}"]["lo"] > 0 for o in COMPARATORS)
            nonin = comp["FORGE6-NONE"]["lo"] > -0.01
            safe = all(v["lo"] <= 0 for v in spk.values())
            S["regimes"][reg] = {"means": {a: mean(per[a]) for a in ARMS}, "spikes": {a: mean(sp[a]) for a in ARMS},
                                 "ci": comp, "spike_ci": spk, "beats": beats, "noninferior_none": nonin, "safe": safe,
                                 "ablation_6_minus_5": ci(per["FORGE6"], per["FORGE5"]),
                                 "noisy_vs_none": ci(per["FORGE6-NOISY"], per["NONE"]),
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


def report(R, title="# W5-R6 — the snapshot forge with re-verification: results") -> str:
    f = lambda c: f"{c['diff']:+.4f} [{c['lo']:+.4f}, {c['hi']:+.4f}]"
    L_ = [title, "",
          "Design: [`AGENTS.md`](../AGENTS.md) §11.10; choices in the docstring of [`rsxv/w5r6_experiments.py`](../rsxv/w5r6_experiments.py).",
          f"Intervals: paired bootstrap, two-sided {LEVEL:.4f}. Mean per-tick mission score over 240 ticks. Snapshots are copies",
          "of the true simulator (perfect model); FORGE6-NOISY (wrong model) and FORGE5 (no re-verification) are reported, not",
          "pass conditions.", ""]
    for sub, S in R["subs"].items():
        L_ += [f"## {sub}: {'PASS' if S['pass'] else 'FAIL'}", "", f"Training table `{S['table']}`; roles `{S['roles']}`", "",
               "| Regime | FORGE6 | FORGE6-NOISY | FORGE5 | REPAIR | RANDOM-FORGE | NONE | F6−REPAIR | F6−RANDOM | F6−NONE | beats | non-inf | safe |",
               "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for reg, X in S["regimes"].items():
            m, c = X["means"], X["ci"]
            L_.append(f"| {reg} | {m['FORGE6']:.4f} | {m['FORGE6-NOISY']:.4f} | {m['FORGE5']:.4f} | {m['REPAIR']:.4f} | "
                      f"{m['RANDOM-FORGE']:.4f} | {m['NONE']:.4f} | {f(c['FORGE6-REPAIR'])} | {f(c['FORGE6-RANDOM-FORGE'])} | "
                      f"{f(c['FORGE6-NONE'])} | {X['beats']} | {X['noninferior_none']} | {X['safe']} |")
        L_ += ["", "| Regime | spikes F6 / REPAIR / RANDOM / NONE | spike contrasts F6−REPAIR, F6−RANDOM, F6−NONE | F6 − F5 (ablation) | Lion Brier (base rate) | machinery | open > 25 |",
               "|---|---|---|---|---|---|---|"]
        for reg, X in S["regimes"].items():
            s = X["spikes"]
            sc = "; ".join(f"{v['diff']:+.2f} [{v['lo']:+.2f}, {v['hi']:+.2f}]" for v in X["spike_ci"].values())
            br = "—" if X["brier"] is None else f"{X['brier']:.3f} ({X['brier_base_rate']:.3f})"
            L_.append(f"| {reg} | {s['FORGE6']:.2f} / {s['REPAIR']:.2f} / {s['RANDOM-FORGE']:.2f} / {s['NONE']:.2f} | {sc} | "
                      f"{f(X['ablation_6_minus_5'])} | {br} | {X['stats']} | {X['open_old']} |")
        L_ += ["", "FORGE6-NOISY − NONE: " + "; ".join(f"{reg} {f(X['noisy_vs_none'])}" for reg, X in S["regimes"].items()), ""]
    return "\n".join(L_)


def main(argv=None):
    global SHIFT
    argv = sys.argv[1:] if argv is None else argv
    d = pathlib.Path(__file__).resolve().parents[1] / "results"
    if "--quick" in argv:
        SHIFT = 500000
        print(report(run(True)))
        return
    if "--confirm" in argv:
        subs = tuple(a for a in argv if a in ("agent", "person")) or ("agent",)
        SHIFT = 100000
        M3.CONFIRM = True
        R = run(False, subs=subs)
        rep = report(R, "# W5-R6 confirmation: every seed + 100000 (persons: calm_better where the regime sets none)")
        (d / "results_w5r6_confirmation.json").write_text(json.dumps(R, indent=1, default=str))
        (d / "w5r6_confirmation.md").write_text(rep)
        print(rep)
        return
    R = run(False)
    (d / "results_w5r6.json").write_text(json.dumps(R, indent=1, default=str))
    (d / "w5r6.md").write_text(report(R))
    print(report(R))


if __name__ == "__main__":
    main()
