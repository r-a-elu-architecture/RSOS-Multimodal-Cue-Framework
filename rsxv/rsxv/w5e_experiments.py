"""W5e, W5d with the calibrated J1 predictor in the tube (twelfth transfer test), as fixed in AGENTS.md §11.9: a certified
context that the gate admits and the spike guard keeps is still routed to the fallback when J1 predicts a jam; the fallback
archetype must also have a pilot spike rate no higher than BASE's. Comparators unchanged. W5d notes follow.

W5d, negative certificates and a fail-safe tube (ninth transfer test), as fixed in AGENTS.md §11.8: W5c plus
- warnings: on the source cohort a non-Lion archetype a in context c is warned when its spike rate in c exceeds Lion's and the
  two-sided 99% upper bound of its effect against Lion is below zero (n >= 8); the warning travels as the function a holds on
  the source, or "unassigned"; on the target the archetypes holding a warned function in c (for "unassigned": every target
  archetype without a role) are excluded from the random role-reading ticks in c (BASE instead), the candidate and the
  fallback;
- fail-safe tube: a certified context is predicted to jam when the gate rejects it, the spike guard removes it or its
  candidate cell holds < 5 ticks; it then runs the target's own best non-warned archetype from the pilot with >= 5 ticks and
  a one-sided lower bound against BASE above -0.01 at the gate level, else BASE. Fallback contexts are not certificates and are
  excluded from the certificate audit; jam predictions are scored against the truth cohort (spike rates included).
Comparators (PILOT-ONLY, RANDOM-FUNC, W3C, NONE) have no warnings and no tube. W5c notes follow.

W5c, transfer with a spike guard in the pilot (seventh attempt), as fixed in AGENTS.md §11.7: W5b plus — after the gate,
a context whose candidate had a higher spike rate per tick than BASE in that context in the pooled pilot is not adopted.
W5b notes follow. Built from
w5_experiments.py; the §11.5 operational choices below still hold except where §11.6 replaces them:
- Pilot ticks 11–30 alternate the candidate and BASE on every visit to every candidate context; a failure in context c makes
  the next visit to c run BASE. PILOT-ONLY alternates the rotated archetype with BASE the same way.
- RANDOM-FUNC replaces RANDOM-CERT: per certified context a different non-Lion archetype (from the archetypes holding the
  other functions on the target, else from all non-Lion archetypes other than the certified one); 20 draws, seeds 0–19.
- Ablation W5b-NO-FAIL: the same pilot without the failure rule.
- The safety gate applies against the registered comparators (PILOT-ONLY, NONE, RANDOM-FUNC, W3C), not the ablation.

Original W5 notes:

    python3 -m rsxv.w5e_experiments           # writes results/results_w5e.json and results/w5e.md
    python3 -m rsxv.w5e_experiments --quick    # smoke run on a few seeds, nothing written

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

LEVEL = 1 - 0.05 / 12
GATE_ALPHA = 0.05 / 12 / 4
WARNS: dict = {}
CUR_WARN: dict = {}
LAST_WARN: dict = {}
MARGIN = 0.01
SIZES = (4, 8, 16)
REPS = 20
FUNCS = ("STABILISE", "RESTORE", "DRIVE")
DIRECTIONS = [("agent", "person"), ("person", "agent"), ("agent_v2", "person"), ("person", "agent_v2")]
ENV = {"person": lambda s: W.PersonEnv(s), "agent": lambda s: W.AgentEnv(s), "agent_v2": lambda s: W.AgentEnvV2(s),
       "person_v2": lambda s: P.PersonEnvV2(s, hypothesis="arousal_deeper")}
BASE_OF = {"person": "person", "person_v2": "person", "agent": "agent", "agent_v2": "agent_v2"}
SRC0 = {"person": 231000, "agent": 231100, "agent_v2": 231200}
PILOT0 = {"person": 232000, "agent": 233000, "agent_v2": 234000}
DEPLOY0 = {"person": 235000, "agent": 235200, "agent_v2": 235400}
ORACLE0 = {"person": 235600, "agent": 235700, "agent_v2": 235800}
TRUTH0 = {"person": 236000, "agent": 236200, "agent_v2": 236400}
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
    comps, cells, spk = [], {}, {}
    for s in range(SRC0[base] + shift, SRC0[base] + shift + 50):
        w = W.World(ENV[src](s), "random", seed=s, score="mission")
        for _ in range(60):
            out = w.tick()
            spk.setdefault((out["ctx"], out["mode"]), []).append(1 if w.env.comp[1] > 1.0 else 0)
        comps += w.comps3
        for c, m, r in w.trace:
            cells.setdefault((c, m), []).append(r)
    roles = G.roles3(comps)
    inv = {}
    for f, a in roles.items():
        inv.setdefault(a, f)
    warn = {}
    for c in W.CONTEXTS:
        for a in W.MODES:
            if a == "LION":
                continue
            xs, ys = cells.get((c, a), []), cells.get((c, "LION"), [])
            if len(xs) < 8 or len(ys) < 2:
                continue
            est, lb = G.welch_lower(xs, ys, 0.005)
            if est is None:
                continue
            ub = 2 * est - lb
            sa, sb = spk.get((c, a), []), spk.get((c, "LION"), [])
            if sa and sb and sum(sa) / len(sa) > sum(sb) / len(sb) and ub < 0:
                warn.setdefault(c, set()).add(inv.get(a, "unassigned"))
    global LAST_WARN
    LAST_WARN = {c: sorted(v) for c, v in warn.items()}
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
    """Ticks 1–10 uniformly random; then the candidate per context, alternating with BASE on every visit; with the failure
    rule, the next visit to a context that just failed runs BASE."""

    def __init__(self, cand, fail_rule=True, rotate=None, seed=0):
        self.cand, self.fail_rule, self.rotate = cand, fail_rule, rotate
        self.sm, self.rng = Smooth(), random.Random(seed * 13 + 5)
        self.force_base, self.vis, self.rot_i = set(), {}, {}
        self.prio_next = self.force_base                      # pilot() adds failed contexts here
        self.ctx_log = []

    def __call__(self, world, sense):
        c = self.sm.ctx(sense)
        self.ctx_log.append(c)
        if world.t <= 10:
            m = self.rng.choice(W.MODES)
            return "LION" if m in getattr(self, "warned", {}).get(c, ()) else m
        if self.fail_rule and c in self.force_base:
            self.force_base.discard(c)
            return "LION"
        self.vis[c] = self.vis.get(c, 0) + 1
        if self.rotate is not None:
            if not self.rotate or self.vis[c] % 2 == 1:
                return "LION"
            self.rot_i[c] = self.rot_i.get(c, -1) + 1
            return self.rotate[self.rot_i[c] % len(self.rotate)]
        arch = self.cand.get(c, "LION")
        if arch == "LION":
            return "LION"
        return arch if self.vis[c] % 2 == 0 else "LION"


SPK: dict = {}


def spike_guard(gated, spk):
    out = {}
    for c, a in gated.items():
        if a != "LION":
            xa, xb = spk.get((c, a), []), spk.get((c, "LION"), [])
            if xa and xb and sum(xa) / len(xa) > sum(xb) / len(xb):
                a = "LION"
        out[c] = a
    return out


def pilot(env, seeds, cand, fail_rule=True, rotate=None, warned=None):
    cells, fails = {}, 0
    SPK.clear()
    for s in seeds:
        pol = PilotPolicy(cand, fail_rule, rotate, seed=s)
        pol.warned = warned or {}
        w = W.World(ENV[env](s), pol, seed=s, score="mission")
        modes = []
        for t in range(30):
            out = w.tick()
            c = pol.ctx_log[-1] if pol.ctx_log else "calm"
            mode = out["mode"]
            cells.setdefault((c, mode), []).append(out["reward"])
            SPK.setdefault((c, mode), []).append(1 if w.env.comp[1] > 1.0 else 0)
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


def _j1(cells, spk, c, a):
    """J1 rule (§11.9), as calibrated in rsxv/j1_calibration.py."""
    xa, xb = cells.get((c, a), []), cells.get((c, "LION"), [])
    sa, sb = spk.get((c, a), []), spk.get((c, "LION"), [])
    if len(xa) < 5 or len(xb) < 5:
        return True
    return (sum(sa) / len(sa) > sum(sb) / len(sb)) or (mean(xa) <= mean(xb))


def warned_arch(troles):
    out = {}
    for c, fs in CUR_WARN.items():
        s_ = set()
        for f in fs:
            if f == "unassigned":
                s_ |= {m for m in W.MODES if m != "LION" and m not in troles.values()}
            elif f in troles and troles[f] != "LION":
                s_.add(troles[f])
        out[c] = s_
    return out


def cand_from_certs(certs, troles):
    return {c: troles.get(v["function"], "LION") for c, v in certs.items()}


def decide_w5(env, seeds, certs, fail_rule=True, randomise=None, guard=True, tube=True):
    troles = read_target_roles(env, seeds)
    cand = cand_from_certs(certs, troles)
    if randomise is not None:
        cand = random_func(cand, troles, randomise)
    wa = warned_arch(troles) if tube else {}
    cand = {c: ("LION" if a in wa.get(c, ()) else a) for c, a in cand.items()}
    cells, fails = pilot(env, seeds, cand, fail_rule, warned=wa)
    gated0, vmap = G.gate_v2(cand, cells, alpha=GATE_ALPHA)
    gated = spike_guard(gated0, dict(SPK)) if guard else gated0
    jams, fallback = [], {}
    if tube:
        for c, a in cand.items():
            if a == "LION":
                continue
            jam = gated0.get(c) != a or gated.get(c) != a or len(cells.get((c, a), [])) < 5 or _j1(cells, SPK, c, a)
            jams.append((c, a, jam))
            if jam:
                best, bm = "LION", None
                for m in W.MODES:
                    if m == "LION" or m in wa.get(c, ()) or len(cells.get((c, m), [])) < 5:
                        continue
                    sm, sb = SPK.get((c, m), []), SPK.get((c, "LION"), [])
                    if not sm or not sb or sum(sm) / len(sm) > sum(sb) / len(sb):
                        continue
                    est, lb = G.welch_lower(cells[(c, m)], cells.get((c, "LION"), []), GATE_ALPHA, min_n=5, var_floor=0.01)
                    if lb is not None and lb > -0.01 and (bm is None or est > bm):
                        best, bm = m, est
                gated[c] = best
                if best != "LION":
                    fallback[c] = best
    return gated, {"cand": cand, "roles": troles, "fails": fails, "jams": jams, "fallback": fallback,
                   "warned": {c: sorted(v) for c, v in wa.items()}}


def random_func(cand, troles, seed):
    rng = random.Random(seed)
    out = {}
    for c, a in cand.items():
        opts = sorted({v for v in troles.values() if v not in (a, "LION")})
        if not opts:
            opts = [m for m in W.MODES if m not in (a, "LION")]
        out[c] = rng.choice(opts)
    return out


def decide_pilot_only(env, seeds):
    troles = read_target_roles(env, seeds)
    rot = [troles[f] for f in FUNCS if f in troles and troles[f] != "LION"]
    cells, fails = pilot(env, seeds, {}, True, rotate=rot)
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


TRUTH_SPK: dict = {}


def truth(env):
    base = BASE_OF[env]
    cells = {}
    spk = TRUTH_SPK.setdefault(env, {})
    for s in range(TRUTH0[base], TRUTH0[base] + 200):
        w = W.World(ENV[env](s), "random", seed=s, score="mission")
        sm = Smooth()
        for _ in range(60):
            c = sm.ctx(w.env.sense())
            out = w.tick()
            cells.setdefault((c, out["mode"]), []).append(out["reward"])
            spk.setdefault((c, out["mode"]), []).append(1 if w.env.comp[1] > 1.0 else 0)
    return G.truth_effects(cells)


def avg(lists):
    return [mean(col) for col in zip(*lists)]


def direction(src, tgt, size, certs, w3c_label, shift=0, quick=False):
    base = BASE_OF[tgt]
    dseeds = list(range(DEPLOY0[base] + shift, DEPLOY0[base] + shift + (20 if quick else 200)))
    reps = 2 if quick else REPS
    arms = {k: ([], []) for k in ("W5", "PILOT-ONLY-ADAPTIVE", "W3C", "RANDOM-CERT", "W5-NO-ADAPT")}  # names kept internally
    log, adopted_ctx, jam_log = [], [], []
    global CUR_WARN
    CUR_WARN = WARNS.get(src, {})
    for r in range(reps):
        seeds = list(range(PILOT0[base] + shift + 16 * r, PILOT0[base] + shift + 16 * r + size))
        g5, i5 = decide_w5(tgt, seeds, certs)
        gpo, ipo = decide_pilot_only(tgt, seeds)
        gna, _ = decide_w5(tgt, seeds, certs, fail_rule=False)
        p3, i3 = C.decide_transfer(tgt if tgt != "person_v2" else "person", seeds, w3c_label) \
            if tgt != "person_v2" else (None, None)
        rnd_s, rnd_p = [], []
        for d in (range(2) if quick else range(20)):
            gr, _ = decide_w5(tgt, seeds, certs, randomise=d, guard=False, tube=False)  # comparator unchanged
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
        adopted_ctx += [(c, a) for c, a in g5.items() if a != "LION" and c not in i5.get("fallback", {})]
        jam_log.extend(i5.get("jams", []))
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
    sp_ci = {f"W5-{o}": ci(spk["W5"], spk[o]) for o in ("PILOT-ONLY-ADAPTIVE", "NONE", "RANDOM-CERT", "W3C") if o in spk}
    safe = all(c["lo"] <= 0 for c in sp_ci.values())
    return {"source": src, "target": tgt, "size": size, "arms": {k: mean(v) for k, v in per.items()},
            "spikes": {k: mean(v) for k, v in spk.items()}, "oracle": max(ovals.values()), "oracle_policies": ovals,
            "contrasts": con, "beats_all": beats, "noninferior": nonin, "safe": safe, "spike_contrasts": sp_ci,
            "extra": {"W5-W3C": ci(per["W5"], per["W3C"]) if "W3C" in per else None,
                      "W5-W5-NO-ADAPT": ci(per["W5"], per["W5-NO-ADAPT"])},
            "adopted": f"{sum(1 for e in log if any(a != 'LION' for a in e['W5'].values()))}/{reps}",
            "adopted_ctx": adopted_ctx, "jams": jam_log, "log": log}


def run(quick=False, shift=0, dirs=None, person_alt=False):
    certs, roles = {}, {}
    for src in ("person", "agent", "agent_v2"):
        s = "person_v2" if (person_alt and src == "person") else src
        certs[src], roles[src] = certificates(s, shift)
        WARNS[src] = LAST_WARN
    w3c = json.loads((pathlib.Path(__file__).resolve().parents[1] / "results" / "results_w3c.json").read_text())
    labels = {k: v["label"] for k, v in w3c["source"].items()}
    tr = {t: truth(t) for t in ("person", "agent", "agent_v2")} if not quick else {}
    ts = {t: TRUTH_SPK[t] for t in tr}
    runs = []
    for s, t in (dirs or DIRECTIONS):
        tt = "person_v2" if (person_alt and t == "person") else t
        for n in ((8,) if quick or shift else SIZES):
            d = direction(s, tt, n, certs[s], labels[s], shift, quick)
            if tr:
                te = tr[BASE_OF[t]]
                false = [(c, a) for c, a in d["adopted_ctx"] if te.get((c, a), 0.0) < 0]
                d["false_certificates"] = {"adopted": len(d["adopted_ctx"]), "false": len(false)}
                sp = ts[BASE_OF[t]]
                rate = lambda k: (sum(sp[k]) / len(sp[k])) if sp.get(k) else 0.0
                ok = [jam == (te.get((c, a), 0.0) <= 0 or rate((c, a)) > rate((c, "LION"))) for c, a, jam in d["jams"]]
                d["jam_accuracy"] = {"n": len(ok), "correct": sum(ok), "predicted_jams": sum(j for _, _, j in d["jams"])}
            runs.append(d)
            print(f"{s}->{tt} n={n}: W5 {d['arms']['W5']:+.4f} beats={d['beats_all']} nonin={d['noninferior']} "
                  f"safe={d['safe']} adopted={d['adopted']}", flush=True)
    return {"certificates": certs, "roles": roles, "runs": runs, "warns": {k: v for k, v in WARNS.items()}}


def evaluate(R):
    at8 = [r for r in R["runs"] if r["size"] == 8]
    fc = [r.get("false_certificates", {"adopted": 0, "false": 0}) for r in at8]
    adopted, false = sum(x["adopted"] for x in fc), sum(x["false"] for x in fc)
    audit = adopted == 0 or false / adopted <= 0.05
    primary = (sum(r["beats_all"] for r in at8) >= 2 and all(all(r["noninferior"].values()) for r in at8)
               and all(r["safe"] for r in at8) and audit)
    strong = (sum(r["beats_all"] for r in at8) >= 3 and all(all(r["noninferior"].values()) for r in at8)
              and all(r["safe"] for r in at8) and audit)
    ja = [r.get("jam_accuracy", {"n": 0, "correct": 0}) for r in at8]
    return {"primary_pass": primary, "strong_pass": strong, "audit": {"adopted": adopted, "false": false, "ok": audit},
            "jam_accuracy": {"n": sum(x["n"] for x in ja), "correct": sum(x["correct"] for x in ja)},
            "directions_beating": [f"{r['source']}->{r['target']}" for r in at8 if r["beats_all"]]}


def fmt(c):
    return "—" if c is None else f"{c['diff']:+.4f} [{c['lo']:+.4f}, {c['hi']:+.4f}]"


NAMES = {"W5-NO-ADAPT": "W5c-NO-FAIL", "PILOT-ONLY-ADAPTIVE": "PILOT-ONLY", "RANDOM-CERT": "RANDOM-FUNC", "W5": "W5c"}


def nm(k):
    for a, b in sorted(NAMES.items(), key=lambda x: -len(x[0])):
        k = k.replace(a, b)
    return k


def report(R) -> str:
    E = R["eval"]
    L = ["# W5e — W5d with the calibrated jam predictor (twelfth transfer test): results", "",
         "Design: [`AGENTS.md`](../AGENTS.md) §11.9, registered before any code; operational choices fixed before the run are in",
         "the docstring of [`rsxv/w5e_experiments.py`](../rsxv/w5e_experiments.py). Level 0.05 / 12 (99.58% paired bootstrap intervals).",
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
        L += [f"| {nm(k)} | {v:+.4f} | {r['spikes'].get(k, float('nan')):.3f} |" for k, v in r["arms"].items()]
        L += [f"| ORACLE (upper bound) | {r['oracle']:+.4f} | |", "", "| Contrast (99%) | Estimate |", "|---|---|"]
        L += [f"| {nm(k)} | {fmt(c)} |" for k, c in r["contrasts"].items()]
        L += [f"| W5-W3C | {fmt(r['extra']['W5-W3C'])} |", f"| W5c − W5c-NO-FAIL (ablation) | {fmt(r['extra']['W5-W5-NO-ADAPT'])} |"]
        fc = r.get("false_certificates")
        L += ["", f"Beats PILOT-ONLY, NONE and RANDOM-FUNC: **{'yes' if r['beats_all'] else 'no'}**. "
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
    L += [f"**Strong pass (three of four directions): {'YES' if E.get('strong_pass') else 'NO'}.** Jam prediction: "
          f"{E['jam_accuracy']['correct']} of {E['jam_accuracy']['n']} correct at pilot 8. Warnings issued by each source: {R.get('warns')}.", "",
          f"**W5e overall: {'PASS' if R['pass'] else 'FAIL'}.**", "",
          "Ablation W5c-NO-FAIL: the same pilot without the failure rule (reported, not a pass condition).", ""]
    return "\n".join(L)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    quick = "--quick" in argv
    R = run(quick, shift=500000 if quick else 0)
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
        (d / "results_w5e.json").write_text(json.dumps(R, indent=1, default=str))
        (d / "w5e.md").write_text(report(R))


if __name__ == "__main__":
    main()
