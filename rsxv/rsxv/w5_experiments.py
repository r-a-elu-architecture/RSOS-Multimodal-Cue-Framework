"""W5, transfer through the R4 layers (fifth attempt at positive transfer), as fixed in AGENTS.md §11.5.

    python3 -m rsxv.w5_experiments            # writes results/results_w5.json and results/w5.md
    python3 -m rsxv.w5_experiments --quick    # smoke run on a few seeds, nothing written

Operational choices fixed before the run (disclosed in results/w5.md):
- Contexts are the World's four (calm, rising, loaded, crisis = load × harm trend), which is what §11.2 uses; the §11.5 text
  "calm/loaded × fault/no-fault" describes the same two axes loosely.
- Functions are those defined in §11.3–11.4 (STABILISE, RESTORE, DRIVE). REVIEW has no definition there and is not used.
- Source evidence comes from a uniformly randomised cohort, so every observation is direct (the archetype actually ran in
  that context); the direct-provenance filter therefore removes nothing here, and its ablation is reported as identical.
- Target policies key their table by a smoothed context: loaded from an exponential average of load (weight 0.3) with
  hysteresis 0.55 / 0.45 (§11.4), combined with the harm trend. Pilot cells and gate tests use the same smoothed context.
- Pilot ticks 1–10 run a uniformly random archetype (own random stream); ticks 11–30 run the arm's table. Failures (flicker:
  ≥ 3 mode changes in 5 ticks; person: harm rise > 1; agents: harm rise > 0) from tick 11 on put their context on the priority
  list for the next 5-tick block, where that context alternates BASE and the candidate. Uncertified contexts run BASE.
- Gate: gate_v2 (≥ 5 ticks per cell, variance floor 0.01) at one-sided level 0.0025 per context (0.01 split over four), on
  the pooled pilot (all 30 ticks of every pilot target). The adopted table is fixed for deployment, so the only policy change
  is the one batch at the end of the pilot; "without batching" has no distinct implementation here and is reported as such.
- Ablation "without adaptive pilot": ticks 11–30 alternate BASE and the certified function on every visit to a certified
  context, with no failure priority.
- PILOT-ONLY-ADAPTIVE: ticks 11–30 rotate STABILISE, RESTORE, DRIVE (target archetypes) on successive visits to a context;
  prioritised contexts alternate BASE with the rotation; per context the best archetype by pilot mean is gated as above.
- W3C: w3c_experiments.decide_transfer with W3c's own transferred label for that source, on W5's pilot seeds; deployed with
  the same deployment seeds. ORACLE as §11.4 on W5's oracle seeds.
- Spikes: harm rise > 1.0 in a tick.
"""
from __future__ import annotations

import itertools
import json
import pathlib
import random
import sys

from . import gate as G
from . import person2 as P
from . import sim
from . import w3c_experiments as C
from . import world as W
from .world_experiments import mean
from .w5r_experiments import ci as _ci

LEVEL = 0.99
GATE_ALPHA = 0.01 / 4
MARGIN = 0.01
SIZES = (4, 8, 16)
REPS = 20
FUNCS = ("STABILISE", "RESTORE", "DRIVE")
DIRECTIONS = [("agent", "person"), ("person", "agent"), ("agent_v2", "person"), ("person", "agent_v2")]
ENV = {"person": lambda s: W.PersonEnv(s), "agent": lambda s: W.AgentEnv(s), "agent_v2": lambda s: W.AgentEnvV2(s),
       "person_v2": lambda s: P.PersonEnvV2(s, hypothesis="arousal_deeper")}
BASE_OF = {"person": "person", "person_v2": "person", "agent": "agent", "agent_v2": "agent_v2"}
SRC0 = {"person": 20000, "agent": 20100, "agent_v2": 20200}
PILOT0 = {"person": 21000, "agent": 22000, "agent_v2": 23000}
DEPLOY0 = {"person": 24000, "agent": 24200, "agent_v2": 24400}
ORACLE0 = {"person": 25000, "agent": 25100, "agent_v2": 25200}
TRUTH0 = {"person": 26000, "agent": 26200, "agent_v2": 26400}
PERMS = [p for p in itertools.permutations(range(4)) if p != (0, 1, 2, 3)]
_dcache: dict = {}


def ci(xs, ys):
    return _ci(xs, ys, level=LEVEL)


# --------------------------------------------------------------------------------------------- smoothed context
class Smooth:
    def __init__(self):
        self.ema, self.loaded = None, False

    def ctx(self, sense):
        self.ema = sense["load"] if self.ema is None else 0.7 * self.ema + 0.3 * sense["load"]
        self.loaded = self.ema > 0.45 if self.loaded else self.ema >= 0.55
        return W.context(1.0 if self.loaded else 0.0, sense["trend"])


class TablePolicy:
    def __init__(self, table):
        self.table, self.sm, self.key = dict(table), Smooth(), tuple(sorted(table.items()))

    def __call__(self, world, sense):
        return self.table.get(self.sm.ctx(sense), "LION")


# ------------------------------------------------------------------------------------------------ source side
def certificates(src, shift=0):
    base = BASE_OF[src]
    comps, cells = [], {}
    for s in range(SRC0[base] + shift, SRC0[base] + shift + 50):
        w = W.World(ENV[src](s), "random", seed=s, score="mission")
        w.run(60)
        comps += w.comps3
        for c, m, r in w.trace:
            cells.setdefault((c, m), []).append(r)
    roles = G.roles3(comps)
    certs = {}
    for c in W.CONTEXTS:
        best = None
        for f in FUNCS:
            a = roles.get(f)
            if a is None:
                continue
            xs, ys = cells.get((c, a), []), cells.get((c, "LION"), [])
            if a == "LION":
                continue
            est, lb = G.welch_lower(xs, ys, 0.005)
            if est is None:
                continue
            cert = {"function": f, "source_archetype": a, "effect": est, "ci": [lb, 2 * est - lb], "n": len(xs),
                    "direct_share": 1.0}
            if lb > 0 and len(xs) >= 8 and (best is None or est > best["effect"]):
                best = cert
        if best:
            certs[c] = best
    return certs, roles


# ------------------------------------------------------------------------------------------------- pilot
class PilotPolicy:
    """Ticks 1–10 uniformly random; then the arm's candidate per context with optional failure-priority alternation."""

    def __init__(self, cand, adaptive, alternate_all=False, rotate=None, seed=0):
        self.cand, self.adaptive, self.alt_all, self.rotate = cand, adaptive, alternate_all, rotate
        self.sm, self.rng = Smooth(), random.Random(seed * 13 + 5)
        self.prio_now, self.prio_next, self.vis = set(), set(), {}
        self.ctx_log = []

    def __call__(self, world, sense):
        c = self.sm.ctx(sense)
        self.ctx_log.append(c)
        t = world.t
        if t <= 10:
            return self.rng.choice(W.MODES)
        blk = (t - 11) // 5
        if blk != getattr(self, "blk", None):
            self.blk = blk
            self.prio_now, self.prio_next = self.prio_next, set()
        self.vis[c] = self.vis.get(c, 0) + 1
        if self.rotate is not None:
            arch = self.rotate[self.vis[c] % len(self.rotate)] if self.rotate else "LION"
        else:
            arch = self.cand.get(c, "LION")
        if arch != "LION" and ((self.adaptive and c in self.prio_now) or self.alt_all):
            return arch if self.vis[c] % 2 == 0 else "LION"
        return arch


def pilot(env, seeds, cand, adaptive=True, alternate_all=False, rotate=None):
    cells, fails = {}, 0
    for s in seeds:
        pol = PilotPolicy(cand, adaptive, alternate_all, rotate, seed=s)
        w = W.World(ENV[env](s), pol, seed=s, score="mission")
        modes = []
        for t in range(30):
            out = w.tick()
            c = pol.ctx_log[-1] if pol.ctx_log else "calm"
            mode = out["mode"]
            cells.setdefault((c, mode), []).append(out["reward"])
            modes.append(mode)
            if w.t >= 11:
                last = modes[-6:]
                rise = w.env.comp[1]
                fail = (sum(a != b for a, b in zip(last, last[1:])) >= 3
                        or (rise > 1.0 if BASE_OF[env] == "person" else rise > 0))
                if fail:
                    pol.prio_next.add(c)
                    fails += 1
    return cells, fails


def read_target_roles(env, seeds):
    comps = []
    for s in seeds:
        w = W.World(ENV[env](s), "random", seed=s, score="mission")
        w.run(10)
        comps += w.comps3
    return G.roles3(comps)


def cand_from_certs(certs, troles):
    return {c: troles.get(v["function"], "LION") for c, v in certs.items()}


def decide_w5(env, seeds, certs, adaptive=True, alternate_all=False):
    troles = read_target_roles(env, seeds)
    cand = cand_from_certs(certs, troles)
    cells, fails = pilot(env, seeds, cand, adaptive, alternate_all)
    gated, vmap = G.gate_v2(cand, cells, alpha=GATE_ALPHA)
    return gated, {"cand": cand, "roles": troles, "fails": fails}


def decide_pilot_only(env, seeds):
    troles = read_target_roles(env, seeds)
    rot = [troles[f] for f in FUNCS if f in troles and troles[f] != "LION"]
    cells, fails = pilot(env, seeds, {}, True, False, rotate=rot)
    best = {}
    for c in W.CONTEXTS:
        opts = {a: mean(cells[(c, a)]) for a in set(rot) if len(cells.get((c, a), [])) >= 5}
        if opts:
            best[c] = max(opts, key=opts.get)
    gated, _ = G.gate_v2(best, cells, alpha=GATE_ALPHA)
    return gated, {"cand": best, "roles": troles, "fails": fails}


# ------------------------------------------------------------------------------------------------ deployment
def deploy(env, pol, dseeds):
    key = (env, getattr(pol, "key", None), dseeds[0], len(dseeds), type(pol).__name__)
    if key not in _dcache:
        sc, sp = [], []
        for s in dseeds:
            p = TablePolicy(pol.table) if isinstance(pol, TablePolicy) else pol
            w = W.World(ENV[env](s), p, seed=s, score="mission")
            spikes = 0
            for _ in range(60):
                w.tick()
                spikes += w.env.comp[1] > 1.0
            sc.append(mean([t[2] for t in w.trace]))
            sp.append(spikes)
        _dcache[key] = (sc, sp)
    return _dcache[key]


def truth(env):
    base = BASE_OF[env]
    cells = {}
    for s in range(TRUTH0[base], TRUTH0[base] + 200):
        w = W.World(ENV[env](s), "random", seed=s, score="mission")
        sm = Smooth()
        for _ in range(60):
            c = sm.ctx(w.env.sense())
            out = w.tick()
            cells.setdefault((c, out["mode"]), []).append(out["reward"])
    return G.truth_effects(cells)


def avg(lists):
    return [mean(col) for col in zip(*lists)]


def direction(src, tgt, size, certs, w3c_label, shift=0, quick=False):
    base = BASE_OF[tgt]
    dseeds = list(range(DEPLOY0[base] + shift, DEPLOY0[base] + shift + (20 if quick else 200)))
    reps = 2 if quick else REPS
    arms = {k: ([], []) for k in ("W5", "PILOT-ONLY-ADAPTIVE", "W3C", "RANDOM-CERT", "W5-NO-ADAPT")}
    log, adopted_ctx = [], []
    for r in range(reps):
        seeds = list(range(PILOT0[base] + shift + 16 * r, PILOT0[base] + shift + 16 * r + size))
        g5, i5 = decide_w5(tgt, seeds, certs)
        gpo, ipo = decide_pilot_only(tgt, seeds)
        gna, _ = decide_w5(tgt, seeds, certs, adaptive=False, alternate_all=True)
        p3, i3 = C.decide_transfer(tgt if tgt != "person_v2" else "person", seeds, w3c_label) \
            if tgt != "person_v2" else (None, None)
        rnd_s, rnd_p = [], []
        keys = list(certs)
        for perm in (PERMS[:3] if quick else PERMS):
            ctxs = W.CONTEXTS
            pc = {}
            for i, c in enumerate(ctxs):
                src_c = ctxs[perm[i]]
                if src_c in certs:
                    pc[c] = certs[src_c]
            gr, _ = decide_w5(tgt, seeds, pc)
            s_, p_ = deploy(tgt, TablePolicy(gr), dseeds)
            rnd_s.append(s_)
            rnd_p.append(p_)
        for name, pol in (("W5", TablePolicy(g5)), ("PILOT-ONLY-ADAPTIVE", TablePolicy(gpo)),
                          ("W5-NO-ADAPT", TablePolicy(gna))):
            s_, p_ = deploy(tgt, pol, dseeds)
            arms[name][0].append(s_)
            arms[name][1].append(p_)
        if p3 is not None:
            s_, p_ = deploy(tgt, p3, dseeds)
            arms["W3C"][0].append(s_)
            arms["W3C"][1].append(p_)
        arms["RANDOM-CERT"][0].append(avg(rnd_s))
        arms["RANDOM-CERT"][1].append(avg(rnd_p))
        adopted_ctx += [(c, a) for c, a in g5.items() if a != "LION"]
        log.append({"rep": r, "W5": g5, "cand": i5["cand"], "roles": i5["roles"], "pilot_failures": i5["fails"],
                    "pilot_only": gpo, "no_adapt": gna, "w3c": getattr(p3, "key", None)})
    per = {k: avg(v[0]) for k, v in arms.items() if v[0]}
    spk = {k: avg(v[1]) for k, v in arms.items() if v[1]}
    per["NONE"], spk["NONE"] = deploy(tgt, TablePolicy({}), dseeds)
    # oracle (upper bound): best of the six §11.4 policies with roles read from a random cohort
    oroles = C.read_roles("person" if tgt == "person_v2" else tgt,
                          range(ORACLE0[base] + shift, ORACLE0[base] + shift + (10 if quick else 50)), 60)
    ovals = {lab: mean(deploy(tgt, C.policy(lab, oroles), dseeds)[0]) for lab in C.LABELS}
    con = {f"W5-{o}": ci(per["W5"], per[o]) for o in ("PILOT-ONLY-ADAPTIVE", "NONE", "RANDOM-CERT")}
    beats = all(c["lo"] > 0 for c in con.values())
    nonin = {o: ci(per["W5"], per[o])["lo"] > -MARGIN for o in ("NONE", "W3C") if o in per}
    sp_ci = {f"W5-{o}": ci(spk["W5"], spk[o]) for o in spk if o != "W5"}
    safe = all(c["lo"] <= 0 for c in sp_ci.values())
    return {"source": src, "target": tgt, "size": size, "arms": {k: mean(v) for k, v in per.items()},
            "spikes": {k: mean(v) for k, v in spk.items()}, "oracle": max(ovals.values()), "oracle_policies": ovals,
            "contrasts": con, "beats_all": beats, "noninferior": nonin, "safe": safe, "spike_contrasts": sp_ci,
            "extra": {"W5-W3C": ci(per["W5"], per["W3C"]) if "W3C" in per else None,
                      "W5-W5-NO-ADAPT": ci(per["W5"], per["W5-NO-ADAPT"])},
            "adopted": f"{sum(1 for e in log if any(a != 'LION' for a in e['W5'].values()))}/{reps}",
            "adopted_ctx": adopted_ctx, "log": log}


def run(quick=False, shift=0, dirs=None, person_alt=False):
    certs, roles = {}, {}
    for src in ("person", "agent", "agent_v2"):
        s = "person_v2" if (person_alt and src == "person") else src
        certs[src], roles[src] = certificates(s, shift)
    w3c = json.loads((pathlib.Path(__file__).resolve().parents[1] / "results" / "results_w3c.json").read_text())
    labels = {k: v["label"] for k, v in w3c["source"].items()}
    tr = {t: truth(t) for t in ("person", "agent", "agent_v2")} if not quick else {}
    runs = []
    for s, t in (dirs or DIRECTIONS):
        tt = "person_v2" if (person_alt and t == "person") else t
        for n in ((8,) if quick or shift else SIZES):
            d = direction(s, tt, n, certs[s], labels[s], shift, quick)
            if tr:
                te = tr[BASE_OF[t]]
                false = [(c, a) for c, a in d["adopted_ctx"] if te.get((c, a), 0.0) < 0]
                d["false_certificates"] = {"adopted": len(d["adopted_ctx"]), "false": len(false)}
            runs.append(d)
            print(f"{s}->{tt} n={n}: W5 {d['arms']['W5']:+.4f} beats={d['beats_all']} nonin={d['noninferior']} "
                  f"safe={d['safe']} adopted={d['adopted']}", flush=True)
    return {"certificates": certs, "roles": roles, "runs": runs}


def evaluate(R):
    at8 = [r for r in R["runs"] if r["size"] == 8]
    fc = [r.get("false_certificates", {"adopted": 0, "false": 0}) for r in at8]
    adopted, false = sum(x["adopted"] for x in fc), sum(x["false"] for x in fc)
    audit = adopted == 0 or false / adopted <= 0.05
    primary = (sum(r["beats_all"] for r in at8) >= 2 and all(all(r["noninferior"].values()) for r in at8)
               and all(r["safe"] for r in at8) and audit)
    return {"primary_pass": primary, "audit": {"adopted": adopted, "false": false, "ok": audit},
            "directions_beating": [f"{r['source']}->{r['target']}" for r in at8 if r["beats_all"]]}


def fmt(c):
    return "—" if c is None else f"{c['diff']:+.4f} [{c['lo']:+.4f}, {c['hi']:+.4f}]"


def report(R) -> str:
    E = R["eval"]
    L = ["# W5 — transfer through the R4 layers (fifth attempt): results", "",
         "Design: [`AGENTS.md`](../AGENTS.md) §11.5, registered before any code; operational choices fixed before the run are in",
         "the docstring of [`rsxv/w5_experiments.py`](../rsxv/w5_experiments.py). Level 0.01 (99% paired bootstrap intervals).",
         "All environments are stated models; no number here comes from people or production agents.", "",
         "## Certificates issued by each source", ""]
    for src, cs in R["certificates"].items():
        L.append(f"- **{src}** (roles `{R['roles'][src]}`): " + ("; ".join(
            f"{c}: {v['function']} ({v['source_archetype']}, {v['effect']:+.3f} [{v['ci'][0]:+.3f}, {v['ci'][1]:+.3f}], n={v['n']})"
            for c, v in cs.items()) or "none"))
    L.append("")
    for r in R["runs"]:
        L += [f"## {r['source']} → {r['target']}, pilot of {r['size']}", "",
              f"W5 adopted a non-baseline table in {r['adopted']} repetitions.", "",
              "| Arm | Mean / tick | Spikes / target |", "|---|---|---|"]
        L += [f"| {k} | {v:+.4f} | {r['spikes'].get(k, float('nan')):.3f} |" for k, v in r["arms"].items()]
        L += [f"| ORACLE (upper bound) | {r['oracle']:+.4f} | |", "", "| Contrast (99%) | Estimate |", "|---|---|"]
        L += [f"| {k} | {fmt(c)} |" for k, c in r["contrasts"].items()]
        L += [f"| W5-W3C | {fmt(r['extra']['W5-W3C'])} |", f"| W5 − W5-NO-ADAPT (ablation) | {fmt(r['extra']['W5-W5-NO-ADAPT'])} |"]
        fc = r.get("false_certificates")
        L += ["", f"Beats PILOT-ONLY-ADAPTIVE, NONE and RANDOM-CERT: **{'yes' if r['beats_all'] else 'no'}**. "
              f"Non-inferior: {r['noninferior']}. Safety gate holds: {r['safe']}."
              + (f" Adopted contexts {fc['adopted']}, false certificates {fc['false']}." if fc else ""), ""]
    L += [f"**Certificate audit (pilot 8, pooled):** {E['audit']['false']} false of {E['audit']['adopted']} adopted — "
          f"{'holds' if E['audit']['ok'] else 'fails'}.", "",
          f"**Primary criterion (pilot 8): {'PASS' if E['primary_pass'] else 'FAIL'}.** Directions meeting all three "
          f"comparisons: {E['directions_beating'] or 'none'}.", ""]
    if R.get("confirmation"):
        L += ["## Confirmation (seeds +100000; person model v2, arousal_deeper)", ""]
        for r in R["confirmation"]["runs"]:
            L.append(f"- {r['source']} → {r['target']}: beats {r['beats_all']}, non-inferior {r['noninferior']}, safe {r['safe']}")
        L.append("")
    L += [f"**W5 overall: {'PASS' if R['pass'] else 'FAIL'}.**", "",
          "Ablations: without batching — no distinct implementation (the adopted table is fixed for deployment, one batch); "
          "without direct-provenance filtering — identical (all source evidence is direct in a randomised cohort).", ""]
    return "\n".join(L)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    quick = "--quick" in argv
    R = run(quick)
    R["eval"] = evaluate(R)
    R["pass"] = False
    if R["eval"]["primary_pass"] and not quick:
        dirs = [tuple(d.split("->")) for d in R["eval"]["directions_beating"]]
        conf = run(False, shift=100000, dirs=dirs, person_alt=True)
        R["confirmation"] = conf
        R["pass"] = all(r["beats_all"] and all(r["noninferior"].values()) and r["safe"] for r in conf["runs"])
    print(report(R))
    if not quick:
        d = pathlib.Path(__file__).resolve().parents[1] / "results"
        (d / "results_w5.json").write_text(json.dumps(R, indent=1, default=str))
        (d / "w5.md").write_text(report(R))


if __name__ == "__main__":
    main()
