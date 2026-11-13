"""TRIAL — personal randomised experiments (spec/TRIAL.md).

A person compares two or more ways of practising (arms) in sessions whose arm is chosen at random, in permuted
blocks: each block holds every arm once, in a random order. Each session records an outcome before and after,
and background factors (sleep, caffeine, exercise, hour). The analysis gives each arm's effect against the
reference arm with a 95% interval, a permutation p-value, an estimate adjusted for the background factors and
for drift over time, and a plain verdict. Results from many people pool into one estimate (random effects).
docs/js/trial.js is identical (tested).

  DESIGNS                         the ready-made trials and their arms
  schedule(design, blocks, seed)  the randomised order of sessions
  analyze(trial)                  effects, intervals, p-values, adjustment, balance and verdicts
  pool(results, contrast)         one estimate across people
  consistency(decisions)          how consistently an agent (or person) makes the same choice in the same situation
  SimPerson, evaluate()           simulated people with known effects, and how well trials recover them
"""
from __future__ import annotations

import math
import sys

from .peak import Rng, T95

DESIGNS = {
    "anchor_vs_sham": {"title": "Real anchor or sham", "arms": ["anchor", "sham"], "reference": "sham",
                       "arm_names": {"anchor": "Your anchor's code", "sham": "A sham code, never paired"},
                       "outcome": "Calm, 0-10", "items": [1, 33], "claims": ["C2", "C10", "C12"],
                       "do": "Play the code you are given, then rate calm again after a minute."},
    "cue_vs_none": {"title": "Cue or no cue", "arms": ["cue", "none"], "reference": "none",
                    "arm_names": {"cue": "Play your anchor when stress starts", "none": "Notice the stress, play nothing"},
                    "outcome": "Calm, 0-10", "items": [1, 33], "claims": ["C1", "C12"],
                    "do": "When you notice stress, do what the session says, then rate calm after two minutes."},
    "auto_vs_manual": {"title": "Automatic or by hand", "arms": ["auto", "manual"], "reference": "manual",
                       "arm_names": {"auto": "The device fires the anchor", "manual": "You fire the anchor yourself"},
                       "outcome": "Calm, 0-10", "items": [26, 33], "claims": ["C40"],
                       "do": "Practise as the session says, then rate calm."},
    "order_ct_identity": {"title": "Core Transformation and identity: which order", "reference": "identity_first",
                          "arms": ["ct_first", "identity_peak_first", "hybrid", "identity_first"],
                          "arm_names": {"ct_first": "Core Transformation, then identity, future-pacing, action",
                                        "identity_peak_first": "Identity peak, then Core Transformation, future-pacing, action",
                                        "hybrid": "A short Core Transformation, identity, then a deeper Core Transformation",
                                        "identity_first": "Identity fully, then Core Transformation"},
                          "outcome": "Calm, 0-10", "items": [52, 53], "claims": ["C85", "C88"],
                          "do": "Run the session in the order given, then rate calm and how strongly you felt the identity."},
    "ssit": {"title": "Higher-level imagery (SSIT)", "arms": ["higher", "local", "calm"], "reference": "calm",
             "arm_names": {"higher": "Imagery about a level above the problem, flowing down",
                           "local": "Imagery about the activity itself becoming easy",
                           "calm": "General calming imagery"},
             "outcome": "Ease of an untrained activity, 0-10", "items": [63, 64], "claims": ["C97", "C101"],
             "do": "Do the imagery you are given for five minutes, then rate how easy an activity you did not imagine feels."},
    "identity_language": {"title": "An identity in another language", "arms": ["other", "own"], "reference": "own",
                          "arm_names": {"other": "Practise the identity in its own language (one you are learning)",
                                        "own": "Practise the identity in your first language"},
                          "outcome": "How true the identity feels, 0-10", "items": [24, 51], "claims": ["C82"],
                          "do": "Run the identity session in the language given, then rate how true the identity feels."},
    "network_vs_timeline": {"title": "Network trance or a timeline", "arms": ["network", "timeline"], "reference": "timeline",
                            "arm_names": {"network": "The network trance: descend to the strongest trigger and transform it",
                                          "timeline": "A timeline session: float back above the first event and release it"},
                            "outcome": "Calm while picturing an untreated trigger, 0-10", "items": [60, 63], "claims": ["C94", "C95"],
                            "do": "Run the session given, then picture one trigger you did not work on and rate how calm you feel, before and after."},
}
COVARIATES = ("sleep_h", "caffeine", "exercise", "hour")
ADJUST = ("sleep_h",)          # pre-specified: session order and sleep; the others are checked for balance only
PERMUTATIONS = 1000


def r1(x):
    return None if x is None else math.floor(x * 10 + 0.5) / 10


def r2(x):
    return None if x is None else math.floor(x * 100 + 0.5) / 100


def r3(x):
    return None if x is None else math.floor(x * 1000 + 0.5) / 1000


def _v(x):
    return int(x) if isinstance(x, float) and x.is_integer() else x


def tcrit(df):
    return T95[df - 1] if 1 <= df <= 30 else 1.96


def _num(v):
    if v is None or v == "" or isinstance(v, bool):
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _mean(xs):
    return sum(xs) / len(xs)


def _var(xs):
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    return sum((x - m) * (x - m) for x in xs) / (len(xs) - 1)


# ---------------------------------------------------------------- schedule

def shuffle(xs, rng):
    xs = list(xs)
    for i in range(len(xs) - 1, 0, -1):
        j = math.floor(rng.u() * (i + 1))
        xs[i], xs[j] = xs[j], xs[i]
    return xs


def schedule(design: str, blocks: int, seed: int) -> list[str]:
    arms = DESIGNS[design]["arms"]
    rng = Rng(seed)
    out = []
    for _ in range(blocks):
        out += shuffle(arms, rng)
    return out


def new_trial(design: str, blocks: int, seed: int, id="t1", created=0):
    return {"schema": "rsos-trial/1", "id": id, "design": design, "blocks": blocks, "seed": seed, "created": created,
            "schedule": schedule(design, blocks, seed), "sessions": []}


def record(trial: dict, before, after, cov: dict | None = None, ts=0):
    """Record the next scheduled session. Returns the session, or None when the schedule is complete."""
    i = len(trial["sessions"])
    if i >= len(trial["schedule"]):
        return None
    s = {"i": i, "arm": trial["schedule"][i], "ts": ts, "before": _v(r1(float(before))), "after": _v(r1(float(after))), "cov": {}}
    for k in COVARIATES:
        x = _num((cov or {}).get(k))
        if x is not None:
            s["cov"][k] = _v(x)
    trial["sessions"].append(s)
    return s


# ---------------------------------------------------------------- analysis

def _solve(A, b):
    """Gaussian elimination with partial pivoting. Returns x, or None when singular."""
    n = len(A)
    M = [list(A[i]) + [b[i]] for i in range(n)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        if abs(M[p][c]) < 1e-12:
            return None
        M[c], M[p] = M[p], M[c]
        for r in range(n):
            if r != c:
                f = M[r][c] / M[c][c]
                for k in range(c, n + 1):
                    M[r][k] -= f * M[c][k]
    return [M[i][n] / M[i][i] for i in range(n)]


def _ols(X, y):
    """Coefficients and their standard errors, or None."""
    n, p = len(X), len(X[0])
    if n <= p:
        return None
    XtX = [[sum(X[r][i] * X[r][j] for r in range(n)) for j in range(p)] for i in range(p)]
    Xty = [sum(X[r][i] * y[r] for r in range(n)) for i in range(p)]
    beta = _solve(XtX, Xty)
    if beta is None:
        return None
    res = [y[r] - sum(X[r][j] * beta[j] for j in range(p)) for r in range(n)]
    s2 = sum(e * e for e in res) / (n - p)
    se = []
    for j in range(p):
        unit = [1.0 if k == j else 0.0 for k in range(p)]
        col = _solve(XtX, unit)
        se.append(math.sqrt(max(0.0, s2 * col[j])))
    return {"beta": beta, "se": se, "df": n - p}


def _perm_p(a, b, seed=12345):
    obs = abs(_mean(a) - _mean(b))
    pool_, na = a + b, len(a)
    rng = Rng(seed)
    hit = 0
    for _ in range(PERMUTATIONS):
        sh = shuffle(pool_, rng)
        if abs(_mean(sh[:na]) - _mean(sh[na:])) >= obs - 1e-12:
            hit += 1
    return (hit + 1) / (PERMUTATIONS + 1)


def analyze(trial: dict) -> dict:
    d = DESIGNS[trial["design"]]
    ref = d["reference"]
    S = [s for s in trial["sessions"] if _num(s.get("before")) is not None and _num(s.get("after")) is not None]
    chg = {a: [s["after"] - s["before"] for s in S if s["arm"] == a] for a in d["arms"]}
    out = {"design": trial["design"], "title": d["title"], "outcome": d["outcome"], "reference": ref, "sessions": len(S),
           "planned": len(trial["schedule"]), "arms": [], "contrasts": [], "balance": {}, "adjusted": None}
    for a in d["arms"]:
        xs = chg[a]
        out["arms"].append({"arm": a, "name": d["arm_names"][a], "n": len(xs), "mean": _v(r2(_mean(xs))) if xs else None,
                            "sd": _v(r2(math.sqrt(_var(xs)))) if len(xs) >= 2 else None})
    for a in d["arms"]:
        if a == ref:
            continue
        xa, xr = chg[a], chg[ref]
        c = {"arm": a, "against": ref, "n": len(xa), "n_ref": len(xr), "diff": None, "lo": None, "hi": None, "p": None}
        if xa and xr:
            diff = _mean(xa) - _mean(xr)
            c["diff"] = _v(r2(diff))
            if len(xa) >= 2 and len(xr) >= 2:
                va, vr = _var(xa) / len(xa), _var(xr) / len(xr)
                se = math.sqrt(va + vr)
                den = (va * va / (len(xa) - 1) if len(xa) > 1 else 0) + (vr * vr / (len(xr) - 1) if len(xr) > 1 else 0)
                df = math.floor((va + vr) * (va + vr) / den) if den > 0 else min(len(xa), len(xr)) - 1   # Welch
                h = tcrit(max(df, 1)) * se
                c["lo"], c["hi"], c["se"] = _v(r2(diff - h)), _v(r2(diff + h)), _v(r3(se))
                c["p"] = _v(r3(_perm_p(xa, xr)))
        if len(xa) < 3 or len(xr) < 3:
            c["verdict"], c["say"] = "too_few", "Too few sessions yet: three or more in each arm give an answer."
        elif c["lo"] is not None and c["lo"] > 0:
            c["verdict"], c["say"] = "better", d["arm_names"][a] + " works better for you, by " + _fmt(c["diff"]) + " points."
        elif c["hi"] is not None and c["hi"] < 0:
            c["verdict"], c["say"] = "worse", d["arm_names"][ref] + " works better for you, by " + _fmt(-c["diff"]) + " points."
        else:
            c["verdict"], c["say"] = "unclear", "No clear difference yet. More sessions make the interval narrower."
        out["contrasts"].append(c)
    present = [k for k in COVARIATES if S and all(k in s["cov"] for s in S) and len({s["cov"][k] for s in S}) > 1]
    for k in present:
        out["balance"][k] = {a: _v(r2(_mean([s["cov"][k] for s in S if s["arm"] == a]))) if chg[a] else None for a in d["arms"]}
    others = [a for a in d["arms"] if a != ref]
    adj_k = [k for k in ADJUST if k in present]
    X = [[1.0] + [1.0 if s["arm"] == a else 0.0 for a in others] + [float(s["i"])] + [float(s["cov"][k]) for k in adj_k] for s in S]
    y = [float(s["after"] - s["before"]) for s in S]
    fit = _ols(X, y) if S and all(chg[a] for a in d["arms"]) else None
    if fit:
        adj = []
        for j, a in enumerate(others):
            b, se = fit["beta"][1 + j], fit["se"][1 + j]
            h = tcrit(fit["df"]) * se
            adj.append({"arm": a, "diff": _v(r2(b)), "lo": _v(r2(b - h)), "hi": _v(r2(b + h))})
        out["adjusted"] = {"for": ["session order"] + adj_k, "contrasts": adj,
                           "trend_per_session": _v(r2(fit["beta"][1 + len(others)]))}
    return out


def _fmt(x):
    k = math.floor(abs(x) * 100 + 0.5)
    s = f"{k // 100}.{k % 100:02d}".rstrip("0").rstrip(".")
    return ("-" if x < 0 and k else "") + s


def pool(results: list[dict], arm: str) -> dict:
    """Random-effects pooling (DerSimonian-Laird) of one contrast across people."""
    ds, vs = [], []
    for r in results:
        for c in r["contrasts"]:
            if c["arm"] == arm and c.get("se"):
                ds.append(float(c["diff"]))
                vs.append(float(c["se"]) ** 2)
    k = len(ds)
    out = {"arm": arm, "people": k, "estimate": None, "lo": None, "hi": None, "tau": None}
    if k < 2:
        return out
    w = [1 / v for v in vs]
    sw = sum(w)
    fe = sum(wi * di for wi, di in zip(w, ds)) / sw
    q = sum(wi * (di - fe) ** 2 for wi, di in zip(w, ds))
    c = sw - sum(wi * wi for wi in w) / sw
    tau2 = max(0.0, (q - (k - 1)) / c) if c > 0 else 0.0
    ws = [1 / (v + tau2) for v in vs]
    est = sum(wi * di for wi, di in zip(ws, ds)) / sum(ws)
    se = math.sqrt(1 / sum(ws))
    out.update({"estimate": _v(r2(est)), "lo": _v(r2(est - 1.96 * se)), "hi": _v(r2(est + 1.96 * se)), "tau": _v(r2(math.sqrt(tau2)))})
    return out


def consistency(decisions: list[dict]) -> dict:
    """decisions: [{scenario, choice}]. The share of repeated decisions that match the most common choice."""
    by = {}
    for x in decisions:
        by.setdefault(str(x["scenario"]), []).append(str(x["choice"]))
    num_, den = 0, 0
    per = []
    for sc in sorted(by):
        cs = by[sc]
        if len(cs) < 2:
            continue
        counts = {}
        for c in cs:
            counts[c] = counts.get(c, 0) + 1
        top = max(sorted(counts), key=lambda c: counts[c])
        num_ += counts[top]
        den += len(cs)
        per.append({"scenario": sc, "n": len(cs), "modal": top, "agree": _v(r1(counts[top] / len(cs) * 100))})
    return {"scenarios": len(per), "consistency": _v(r1(num_ / den * 100)) if den else None, "per": per}


# ---------------------------------------------------------------- simulation

class SimPerson:
    """A simulated person with known arm effects (mean change in the outcome), noise, drift over sessions,
    and a sleep effect (each hour of sleep above 7 adds `sleep_effect`)."""

    def __init__(self, effects: dict, seed=1, noise=1.5, trend=0.0, sleep_effect=0.3):
        self.effects, self.rng = effects, Rng(seed)
        self.noise, self.trend, self.sleep_effect = noise, trend, sleep_effect

    def run(self, trial: dict) -> dict:
        for i, arm in enumerate(trial["schedule"]):
            sleep = 5 + math.floor(self.rng.u() * 9) / 2
            cov = {"sleep_h": sleep, "caffeine": 1 if self.rng.u() < 0.4 else 0,
                   "exercise": 1 if self.rng.u() < 0.3 else 0, "hour": 7 + math.floor(self.rng.u() * 15)}
            before = 4 + math.floor(self.rng.u() * 3)
            change = self.effects[arm] + self.trend * i + self.sleep_effect * (sleep - 7) + self.noise * self.rng.gauss()
            record(trial, before, before + change, cov, ts=i * 86400)
        return trial


def evaluate(n_people=200) -> dict:
    """Two-arm trial (anchor or sham): how often a true difference is found, and how often a false one is."""
    out = {"power": {}, "false": {}, "pooled": None}
    for blocks in (4, 8, 12):
        found = false = 0
        for p in range(n_people):
            t = SimPerson({"anchor": 1.5, "sham": 0.0}, seed=10_000 + p).run(new_trial("anchor_vs_sham", blocks, 500 + p))
            found += analyze(t)["contrasts"][0]["verdict"] == "better"
            t0 = SimPerson({"anchor": 0.0, "sham": 0.0}, seed=20_000 + p).run(new_trial("anchor_vs_sham", blocks, 900 + p))
            false += analyze(t0)["contrasts"][0]["verdict"] in ("better", "worse")
        out["power"][blocks] = _v(r1(found / n_people * 100))
        out["false"][blocks] = _v(r1(false / n_people * 100))
    # 30 people whose true effects vary around 1.0 (sd 0.5), 8 blocks each
    rng, res = Rng(4242), []
    for p in range(30):
        eff = 1.0 + 0.5 * rng.gauss()
        t = SimPerson({"anchor": eff, "sham": 0.0}, seed=30_000 + p, trend=0.05).run(new_trial("anchor_vs_sham", 8, 1300 + p))
        res.append(analyze(t))
    out["pooled"] = pool(res, "anchor")
    # drift and background factors: people who improve over time whatever the arm, with sleep affecting calm.
    # Randomisation keeps the raw difference unbiased; adjustment makes it more precise.
    raw_err, adj_err, n_adj = 0.0, 0.0, 0
    for p in range(100):
        t = SimPerson({"anchor": 1.0, "sham": 0.0}, seed=40_000 + p, trend=0.15, sleep_effect=0.6).run(new_trial("anchor_vs_sham", 8, 2000 + p))
        a = analyze(t)
        if a["adjusted"]:
            raw_err += abs(a["contrasts"][0]["diff"] - 1.0)
            adj_err += abs(a["adjusted"]["contrasts"][0]["diff"] - 1.0)
            n_adj += 1
    out["drift"] = {"people": n_adj, "raw_error": _v(r2(raw_err / n_adj)), "adjusted_error": _v(r2(adj_err / n_adj)), "true": 1.0}
    return out


def report(ev: dict) -> str:
    L = ["# TRIAL: recovering known effects in personal randomised trials (simulation)", "",
         "Generated by `python -m rsso.trial --evaluate`. Simulated people compare a real anchor with a sham code in "
         "permuted blocks; each session's calm change (0-10) carries noise (sd 1.5 points), a sleep effect and, where "
         "stated, drift over time. Built and tested in simulation; effect unproven in people.", "",
         "| Blocks (sessions per arm) | A true difference of 1.5 points found | A difference claimed when there is none |", "|---|---|---|"]
    for b in (4, 8, 12):
        L.append(f"| {b} | {ev['power'][b]}% | {ev['false'][b]}% |")
    p = ev["pooled"]
    L += ["", f"**Pooling across 30 people** whose true effects vary around 1.0 point (sd 0.5), 8 blocks each: pooled estimate "
          f"{p['estimate']} [{p['lo']}, {p['hi']}], between-person spread {p['tau']} (true 0.5).", "",
          f"**Drift and background factors.** {ev['drift']['people']} simulated people who improve by 0.15 points every session "
          f"whatever the arm, with sleep moving calm by 0.6 points an hour; true difference {ev['drift']['true']}. Average error "
          f"of the raw difference {ev['drift']['raw_error']}; adjusted for session order and background factors "
          f"{ev['drift']['adjusted_error']}. Random order keeps the raw difference fair; adjustment makes it more precise.", "",
          "Reading: one person's trial rarely claims an effect that is not there (under 5%). Finding a real effect of 1.5 "
          "points needs about twelve sessions of each arm to succeed more often than not, so personal trials answer large "
          "effects for one person, and pooling many people answers moderate ones, with how much people differ. The protocol "
          "kit (spec/kits/TRIAL_PROTOCOL_KIT.md) runs the same design with real people.", ""]
    return "\n".join(L)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["--evaluate"]:
        import pathlib
        path = pathlib.Path(__file__).resolve().parents[1] / "results" / "trial.md"
        path.write_text(report(evaluate()), encoding="utf-8")
        print(f"wrote {path}")
        return 0
    if argv[:1] == ["analyze"] and len(argv) == 2:
        import json
        t = json.loads(open(argv[1], encoding="utf-8").read())
        a = analyze(t)
        print(f"{a['title']}: {a['sessions']} of {a['planned']} sessions")
        for c in a["contrasts"]:
            print(f"  {c['arm']} against {c['against']}: {c['diff']} [{c['lo']}, {c['hi']}], p {c['p']}. {c['say']}")
        return 0
    print("usage: python -m rsso.trial --evaluate | analyze <trial.json>")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
