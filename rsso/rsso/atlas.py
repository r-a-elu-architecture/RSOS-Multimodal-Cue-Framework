"""ATLAS: the trigger atlas and the transfer engine (spec/ATLAS.md).

A person's triggers as a measured, weighted network. Over a week or more the person samples moments across the day:
what was present (objects, sounds, smells, tastes, touch, places, thoughts, symbols, people) and their state before and
after (0-10, higher is worse), plus control moments with no particular trigger. Every node gets a weight, the shift it
brings beyond the control moments, with a 95% interval, a verdict and the number of exposures it still needs before
the weight is stable. Combinations get their own nodes, because a sound with one object may trigger a state where
either alone does not.

From the map:
  reroute     a high-weight trigger appears: the strongest anchor is offered or fired, as the autonomy gate allows
  predict     does the map predict the state of moments it has not seen (leave one out)
  transfer    treat one node, map again, and measure the change on nodes that were never treated, against a repeat
              mapping with no treatment (so that habituation is not counted as transfer)
  sweep       higher nodes by abstraction (words, agency, identity, values, meaning) and by scope (room, city, country,
              world, all living things): does transfer rise, peak or fall with the level
  route       the original glyphs walked in ledger order as a memory route, recalled and timed

A seeded simulated world with known triggers checks every measure. docs/js/atlas.js is identical (tested).
"""
from __future__ import annotations

import math
import sys

from . import gate as G
from . import peak as P
from . import trial as T

SENSES = ("sight", "sound", "smell", "taste", "touch", "place", "thought", "symbol", "person")
SENSE_NAMES = {"sight": "Sight", "sound": "Sound", "smell": "Smell", "taste": "Taste", "touch": "Touch", "place": "Place",
               "thought": "Thought", "symbol": "Symbol", "person": "Person", "combo": "Combination", "higher": "Higher node"}
PHASES = ("map", "map2", "after")
METHODS = ("network", "timeline", "sham", "none")
MARGIN = 1.0           # a weight within one point of zero is no trigger
READY = 1.0            # a weight is stable when its 95% interval is at most one point either side
HIGHER = [
    {"id": "words", "dim": "abstraction", "rank": 1, "label": "The words for the feeling"},
    {"id": "agency", "dim": "abstraction", "rank": 2, "label": "The one who chooses"},
    {"id": "identity", "dim": "abstraction", "rank": 3, "label": "Who you are"},
    {"id": "values", "dim": "abstraction", "rank": 4, "label": "What matters to you"},
    {"id": "meaning", "dim": "abstraction", "rank": 5, "label": "What your life is for"},
    {"id": "room", "dim": "scope", "rank": 1, "label": "The room you are in"},
    {"id": "city", "dim": "scope", "rank": 2, "label": "The whole city"},
    {"id": "country", "dim": "scope", "rank": 3, "label": "The whole country"},
    {"id": "world", "dim": "scope", "rank": 4, "label": "The whole world"},
    {"id": "all", "dim": "scope", "rank": 5, "label": "All living things"},
]


def r1(x):
    return None if x is None else math.floor(x * 10 + 0.5) / 10


def r2(x):
    return None if x is None else math.floor(x * 100 + 0.5) / 100


def _v(x):
    return int(x) if isinstance(x, float) and x.is_integer() else x


def _mean(xs):
    return sum(xs) / len(xs)


def _var(xs):
    return T._var(xs)


def _ci_one(xs):
    """Mean with a 95% t interval (None when fewer than two)."""
    m = _mean(xs)
    if len(xs) < 2:
        return m, None, None
    h = T.tcrit(len(xs) - 1) * math.sqrt(_var(xs) / len(xs))
    return m, m - h, m + h


def _ci_diff(a, b):
    """Mean of a minus mean of b with a 95% Welch interval."""
    d = _mean(a) - _mean(b)
    if len(a) < 2 or len(b) < 2:
        return d, None, None
    va, vb = _var(a) / len(a), _var(b) / len(b)
    se = math.sqrt(va + vb)
    if se == 0:
        return d, d, d
    den = va * va / (len(a) - 1) + vb * vb / (len(b) - 1)
    df = max(1, int(math.floor((va + vb) * (va + vb) / den))) if den > 0 else len(a) + len(b) - 2
    h = T.tcrit(df) * se
    return d, d - h, d + h


# ---------------------------------------------------------------- the atlas

def make_atlas(id_: str, state="Stress", created=0) -> dict:
    return {"schema": "rsos-atlas/1", "id": id_, "state": state, "created": created, "nodes": [], "exposures": [],
            "treatments": [], "sweep": [], "routes": []}


def add_node(a: dict, id_: str, label: str, sense: str) -> dict:
    if sense not in SENSES:
        raise ValueError("sense must be one of " + ", ".join(SENSES))
    if any(n["id"] == id_ for n in a["nodes"]):
        raise ValueError("a node with this id exists")
    n = {"id": id_, "label": label, "sense": sense}
    a["nodes"].append(n)
    return n


def add_combo(a: dict, id_: str, of: list, label="") -> dict:
    ids = {n["id"] for n in a["nodes"] if n["sense"] != "combo"}
    if len(of) < 2 or any(x not in ids for x in of):
        raise ValueError("a combination joins two or more existing nodes")
    n = {"id": id_, "label": label or " + ".join(of), "sense": "combo", "of": list(of)}
    a["nodes"].append(n)
    return n


def expose(a: dict, ts, nodes: list, before, after, phase="map") -> dict:
    """One sampled moment. nodes: what was present (empty for a control moment). before/after: the state, 0-10."""
    if phase not in PHASES:
        raise ValueError("phase must be one of " + ", ".join(PHASES))
    e = {"ts": ts, "nodes": list(nodes), "before": before, "after": after, "phase": phase}
    a["exposures"].append(e)
    return e


def _shift(e):
    return e["after"] - e["before"]


def _present(e, n):
    if n.get("sense") == "combo":
        return all(x in e["nodes"] for x in n["of"])
    return n["id"] in e["nodes"]


def _inverse(M):
    """Gauss-Jordan inverse with partial pivoting; a tiny ridge keeps nodes that always appear together finite."""
    n = len(M)
    A = [[M[i][j] + (1e-6 if i == j else 0.0) for j in range(n)] + [1.0 if k == i else 0.0 for k in range(n)] for i in range(n)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(A[r][c]))
        A[c], A[p] = A[p], A[c]
        piv = A[c][c]
        A[c] = [x / piv for x in A[c]]
        for r in range(n):
            if r != c and A[r][c] != 0:
                f = A[r][c]
                A[r] = [x - f * y for x, y in zip(A[r], A[c])]
    return [row[n:] for row in A]


def fit(a: dict, phase="map") -> dict:
    """Least squares over the sampled moments: shift = baseline + a weight for each node present + an interaction
    for each combination present. Control moments fix the baseline. Returns the columns, coefficients, standard
    errors, residual degrees of freedom and leave-one-out predictions."""
    ex = [e for e in a["exposures"] if e["phase"] == phase]
    cols = []
    for n in a["nodes"]:
        if any(_present(e, n) for e in ex):
            cols.append(n)
    X = [[1.0] + [1.0 if _present(e, n) else 0.0 for n in cols] for e in ex]
    y = [float(_shift(e)) for e in ex]
    p, m = len(cols) + 1, len(ex)
    if m < p + 2:
        return {"cols": cols, "beta": None, "se": None, "df": m - p, "loo": None, "y": y, "base": None}
    XtX = [[sum(X[k][i] * X[k][j] for k in range(m)) for j in range(p)] for i in range(p)]
    Xty = [sum(X[k][i] * y[k] for k in range(m)) for i in range(p)]
    inv = _inverse(XtX)
    beta = [sum(inv[i][j] * Xty[j] for j in range(p)) for i in range(p)]
    res = [y[k] - sum(X[k][i] * beta[i] for i in range(p)) for k in range(m)]
    df = m - p
    s2 = sum(r * r for r in res) / df
    se = [math.sqrt(max(0.0, s2 * inv[i][i])) for i in range(p)]
    loo = []
    for k in range(m):
        h = sum(X[k][i] * sum(inv[i][j] * X[k][j] for j in range(p)) for i in range(p))
        loo.append(y[k] - res[k] / (1 - h) if h < 0.999 else None)
    return {"cols": cols, "beta": beta, "se": se, "df": df, "loo": loo, "y": y, "base": beta[0], "ex": ex}


def _raw(a: dict, phase) -> dict:
    """Unrounded weight, standard error and degrees of freedom of each node in the fit."""
    F = fit(a, phase)
    if F["beta"] is None:
        return {}
    return {n["id"]: (F["beta"][k + 1], F["se"][k + 1], F["df"]) for k, n in enumerate(F["cols"])}


def weights(a: dict, phase="map") -> dict:
    """Each node's weight: the shift it adds beyond the baseline of control moments, estimated together with every
    other node present at the same moments, with a 95% interval, a verdict (trigger, soothing, none, unclear, too few)
    and readiness. For a combination the weight is its interaction: what the parts bring together beyond each alone."""
    F = fit(a, phase)
    ex = [e for e in a["exposures"] if e["phase"] == phase]
    out = {}
    for n in a["nodes"]:
        cnt = sum(1 for e in ex if _present(e, n))
        base = {"n": cnt, "weight": None, "lo": None, "hi": None, "verdict": "too_few", "ready": False, "need": 3}
        if F["beta"] is None or n not in F["cols"]:
            out[n["id"]] = base
            continue
        i = F["cols"].index(n) + 1
        w, se = F["beta"][i], F["se"][i]
        t = T.tcrit(F["df"])
        lo, hi = w - t * se, w + t * se
        if cnt < 3:
            verdict = "too_few"
        elif lo > 0:
            verdict = "trigger"
        elif hi < 0:
            verdict = "soothing"
        elif lo > -MARGIN and hi < MARGIN:
            verdict = "none"
        else:
            verdict = "unclear"
        need = cnt if t * se <= READY else int(math.ceil(cnt * (t * se / READY) * (t * se / READY)))
        out[n["id"]] = {"n": cnt, "weight": _v(r1(w)), "lo": _v(r1(lo)), "hi": _v(r1(hi)), "verdict": verdict,
                        "ready": cnt >= 3 and t * se <= READY, "need": max(3, need)}
    return out


def combos(a: dict, phase="map") -> list:
    """Each combination: its interaction and whether the parts trigger only together, more together, or add up."""
    W = weights(a, phase)
    out = []
    for n in a["nodes"]:
        if n["sense"] != "combo":
            continue
        w = W[n["id"]]
        res = {"id": n["id"], "of": n["of"], "n": w["n"], "interaction": w["weight"], "lo": w["lo"], "hi": w["hi"], "verdict": "too_few"}
        if w["verdict"] != "too_few":
            parts_trigger = any(W[x]["verdict"] == "trigger" for x in n["of"])
            res["verdict"] = ("together_more" if parts_trigger else "only_together") if w["lo"] > 0 else "together_less" if w["hi"] < 0 else "additive"
        out.append(res)
    return out


def edges(a: dict, phase="map", min_share=0.2) -> list:
    """Nodes that appear together: the share of moments with either in which both are present."""
    ids = [n["id"] for n in a["nodes"] if n["sense"] != "combo"]
    ex = [set(e["nodes"]) for e in a["exposures"] if e["phase"] == phase and e["nodes"]]
    out = []
    for i, x in enumerate(ids):
        for y in ids[i + 1:]:
            both = sum(1 for s in ex if x in s and y in s)
            either = sum(1 for s in ex if x in s or y in s)
            if both and both / either >= min_share:
                out.append({"a": x, "b": y, "share": _v(r2(both / either)), "n": both})
    return out


def readiness(a: dict, phase="map") -> dict:
    W = weights(a, phase)
    real = [n for n in a["nodes"] if n["sense"] != "combo"]
    ex = [e for e in a["exposures"] if e["phase"] == phase]
    by = {s: sum(1 for e in ex for n in real if n["sense"] == s and n["id"] in e["nodes"]) for s in SENSES}
    ready = [n["id"] for n in real if W[n["id"]]["ready"]]
    nxt = sorted((n for n in real if not W[n["id"]]["ready"]), key=lambda n: (W[n["id"]]["n"] - W[n["id"]]["need"], n["id"]))[:5]
    controls = sum(1 for e in ex if not e["nodes"])
    say = (f"{len(ready)} of {len(real)} nodes have a stable weight. " +
           ("Add control moments (nothing in particular present): at least five. " if controls < 5 else "") +
           ("Sample next: " + ", ".join(n["label"] for n in nxt) + "." if nxt else "The map is ready."))
    return {"nodes": len(real), "ready": len(ready), "moments": len(ex), "controls": controls, "by_sense": by,
            "missing_senses": [s for s in SENSES if by[s] == 0], "next": [n["id"] for n in nxt], "say": say}


def predict(a: dict, phase="map") -> dict:
    """Leave one out: each moment's shift predicted by the map fitted without it, against predicting the average
    shift of the other moments."""
    F = fit(a, phase)
    if F["beta"] is None or len(F["y"]) < 10:
        return {"n": len(F["y"]), "r": None, "mae": None, "mae_null": None, "verdict": "too_few",
                "say": "More sampled moments are needed to test the map: at least two more than its nodes, and ten in all."}
    m = len(F["y"])
    tot = sum(F["y"])
    real, pred, null = [], [], []
    for k in range(m):
        if F["loo"][k] is None:
            continue
        real.append(F["y"][k])
        pred.append(F["loo"][k])
        null.append((tot - F["y"][k]) / (m - 1))
    mae = _mean([abs(x - y) for x, y in zip(real, pred)])
    mae0 = _mean([abs(x - y) for x, y in zip(real, null)])
    mx, my = _mean(real), _mean(pred)
    sxy = sum((x - mx) * (y - my) for x, y in zip(real, pred))
    sxx = sum((x - mx) * (x - mx) for x in real)
    syy = sum((y - my) * (y - my) for y in pred)
    r = sxy / math.sqrt(sxx * syy) if sxx > 0 and syy > 0 else 0.0
    verdict = "predicts" if mae <= 0.9 * mae0 and r >= 0.3 else "does_not_predict"
    say = (f"The map predicts moments it has not seen: error {_v(r1(mae))} points against {_v(r1(mae0))} without it (r = {_v(r2(r))})."
           if verdict == "predicts" else f"The map does not yet predict new moments better than the average (error {_v(r1(mae))} against {_v(r1(mae0))}).")
    return {"n": len(real), "r": _v(r2(r)), "mae": _v(r1(mae)), "mae_null": _v(r1(mae0)), "verdict": verdict, "say": say}


# ---------------------------------------------------------------- rerouting

def reroute(a: dict, present: list, anchors: list, offers=None, now=0, optins=None, history=None, consents=None, threshold=2.0) -> dict:
    """A trigger with a weight of at least `threshold` is present: offer or fire the strongest anchor, as the autonomy
    gate allows. history: {anchor_id: {"auto_since": ts}}."""
    W = weights(a)
    hits = sorted((n for n in present if n in W and W[n]["verdict"] == "trigger" and W[n]["weight"] >= threshold),
                  key=lambda n: (-W[n]["weight"], n))
    if not hits:
        return {"action": "none", "trigger": None, "weight": None, "anchor": None, "reasons": ["no high-weight trigger present"]}
    trig = hits[0]
    ranked = []
    for an in anchors:
        s = P.strength(an)
        if s["status"] in ("strong", "present"):
            ranked.append((-(s["estimate"] or 0), an["id"], an))
    ranked.sort(key=lambda x: (x[0], x[1]))
    if not ranked:
        return {"action": "none", "trigger": trig, "weight": W[trig]["weight"], "anchor": None, "reasons": ["no anchor with a proven effect"]}
    reasons = []
    for _, aid, an in ranked:
        h = (history or {}).get(aid)
        for mode in ("auto", "suggest"):
            d = G.may_fire(an, mode, offers or [], now, optins, h, consents)
            if d["decision"] == "allow":
                return {"action": "fire" if mode == "auto" else "suggest", "trigger": trig, "weight": W[trig]["weight"], "anchor": aid,
                        "reasons": [], "flag": d["flag"]}
        reasons.append(aid + ": " + "; ".join(d["reasons"]))
    return {"action": "none", "trigger": trig, "weight": W[trig]["weight"], "anchor": None, "reasons": reasons}


# ---------------------------------------------------------------- the transfer engine

def choose_node(a: dict, by="weight", phase="map"):
    """The node to work on: the strongest trigger across the senses, or (by level) the higher node with the largest
    benefit in the sweep so far."""
    if by == "level":
        rep = sweep_report(a)
        return rep["best"]
    W = weights(a, phase)
    cand = sorted((n["id"] for n in a["nodes"] if n["sense"] != "combo" and W[n["id"]]["verdict"] == "trigger"),
                  key=lambda i: (-W[i]["weight"], i))
    return cand[0] if cand else None


def add_treatment(a: dict, ts, node: str, method="network", note="") -> dict:
    if method not in METHODS:
        raise ValueError("method must be one of " + ", ".join(METHODS))
    t = {"ts": ts, "node": node, "method": method, "note": note}
    a["treatments"].append(t)
    return t


def transfer(a: dict, treated: str) -> dict:
    """Change on the treated node and on untreated triggers after treatment ("after" against "map2"), beyond the drift
    common to all triggers between the two mappings before treatment ("map2" against "map", as a ratio), so that
    habituation is not counted as transfer.
    Without a repeat mapping, the plain change from "map" to "after" is reported and marked uncontrolled."""
    W0 = weights(a, "map")
    R0, R2, R3 = _raw(a, "map"), _raw(a, "map2"), _raw(a, "after")
    controlled = any(e["phase"] == "map2" for e in a["exposures"])
    base = R2 if controlled else R0
    reactive = [n["id"] for n in a["nodes"] if n["sense"] != "combo" and W0[n["id"]]["verdict"] == "trigger"]
    # drift common to every trigger between the two mappings before treatment (habituation, season, mood), as a ratio
    pairs = [(R0[i][0], R2[i][0]) for i in reactive if i in R0 and i in R2]
    drift = (sum(y for _, y in pairs) / sum(x for x, _ in pairs)) if controlled and pairs and sum(x for x, _ in pairs) > 0 else 1.0
    drift = max(0.0, min(1.5, drift))

    def change(i):
        if i not in base or i not in R3:
            return None
        return (R3[i][0] - base[i][0] * drift, R3[i][1] * R3[i][1] + (drift * base[i][1]) * (drift * base[i][1]), min(R3[i][2], base[i][2]))
    tc = change(treated) if treated in W0 else None
    tr = tc[0] if tc else None
    un = [(i, change(i)) for i in reactive if i != treated]
    un = [(i, c) for i, c in un if c is not None]
    out = {"treated": treated, "controlled": controlled, "drift": _v(r2(drift)), "treated_change": _v(r1(tr)),
           "untreated": [{"id": i, "change": _v(r1(c[0]))} for i, c in un], "mean": None, "lo": None, "hi": None, "ratio": None, "verdict": "too_few"}
    if tr is None or len(un) < 2:
        out["say"] = "Map before treatment, ideally twice, then again after it, with at least two other triggers in the map."
        return out
    m = _mean([c[0] for _, c in un])
    se = math.sqrt(sum(c[1] for _, c in un)) / len(un)
    t = T.tcrit(max(1, min(c[2] for _, c in un)))
    lo, hi = m - t * se, m + t * se
    out.update({"mean": _v(r1(m)), "lo": _v(r1(lo)), "hi": _v(r1(hi))})
    if tr < 0:
        out["ratio"] = _v(r2(m / tr))
    if tr >= -MARGIN:
        out["verdict"], say = "no_change", "The treated node itself did not change by a point or more."
    elif hi < 0:
        out["verdict"], say = "spreads", f"The change spread: untreated triggers fell by {_v(r1(-m))} point{'' if _v(r1(-m)) == 1 else 's'} on average [{_v(r1(-hi))}, {_v(r1(-lo))}], {_v(r1(m / tr * 100))}% of the treated node's change."
    elif lo > -MARGIN / 2 and hi < MARGIN / 2:
        out["verdict"], say = "stays", "The change stayed on the treated node: untreated triggers moved by less than half a point."
    else:
        out["verdict"], say = "unclear", "Not clear yet whether the change spread; map more moments after treatment."
    out["say"] = say + ("" if controlled else " Without a repeat mapping before treatment, part of this may be habituation.")
    return out


# ---------------------------------------------------------------- the level sweep

def add_sweep(a: dict, ts, higher: str, change) -> dict:
    """A session worked through a higher node; change: the change in reactivity of untreated triggers afterwards
    (negative is better)."""
    if not any(h["id"] == higher for h in HIGHER):
        raise ValueError("unknown higher node")
    s = {"ts": ts, "higher": higher, "change": change}
    a["sweep"].append(s)
    return s


def sweep_report(a: dict) -> dict:
    out = {"dims": {}, "best": None}
    best = None
    for dim in ("abstraction", "scope"):
        pts = []
        for h in [x for x in HIGHER if x["dim"] == dim]:
            xs = [-s["change"] for s in a["sweep"] if s["higher"] == h["id"]]
            pts.append({"id": h["id"], "rank": h["rank"], "n": len(xs), "benefit": _v(r1(_mean(xs))) if xs else None, "_xs": xs})
        ok = [p for p in pts if p["n"] >= 2]
        shape = "too_few"
        if len(ok) >= 3:
            top = max(ok, key=lambda p: (_mean(p["_xs"]), -p["rank"]))
            lo_end, hi_end = min(ok, key=lambda p: p["rank"]), max(ok, key=lambda p: p["rank"])
            if best is None or _mean(top["_xs"]) > best[0]:
                best = (_mean(top["_xs"]), top["id"])

            def above(p, q):
                d, l, h = _ci_diff(p["_xs"], q["_xs"])
                return l is not None and l > 0
            if top is hi_end and above(top, lo_end):
                shape = "rises"
            elif top is lo_end and above(top, hi_end):
                shape = "falls"
            elif top is not lo_end and top is not hi_end and above(top, lo_end) and above(top, hi_end):
                shape = "peaks"
            else:
                shape = "flat"
            out["dims"][dim] = {"points": [{k: p[k] for k in ("id", "rank", "n", "benefit")} for p in pts], "shape": shape, "top": top["id"]}
        else:
            out["dims"][dim] = {"points": [{k: p[k] for k in ("id", "rank", "n", "benefit")} for p in pts], "shape": shape, "top": None}
    ab = [-s["change"] for s in a["sweep"] if next(h for h in HIGHER if h["id"] == s["higher"])["dim"] == "abstraction"]
    sc = [-s["change"] for s in a["sweep"] if next(h for h in HIGHER if h["id"] == s["higher"])["dim"] == "scope"]
    if len(ab) >= 2 and len(sc) >= 2:
        d, lo, hi = _ci_diff(ab, sc)
        out["abstraction_minus_scope"] = {"difference": _v(r1(d)), "lo": _v(r1(lo)), "hi": _v(r1(hi))}
    else:
        out["abstraction_minus_scope"] = None
    out["best"] = best[1] if best else None
    names = {"rises": "rises with the level", "falls": "falls as the level rises", "peaks": "peaks in the middle",
             "flat": "shows no clear shape yet", "too_few": "needs two sessions at three or more levels"}
    out["say"] = "By abstraction, the benefit " + names[out["dims"]["abstraction"]["shape"]] + "; by scope, it " + names[out["dims"]["scope"]["shape"]] + "."
    return out


# ---------------------------------------------------------------- the glyph route

def glyph_route(glyphs: list, start=0, length=12) -> list:
    """The original glyphs in ledger order from `start`, as a memory route."""
    return glyphs[start:start + length]


def add_route_walk(a: dict, ts, start: int, length: int, results: list) -> dict:
    """results: [{pos, ok, ms}], recalling the glyph after each position."""
    w = {"ts": ts, "start": start, "length": length, "results": [{"pos": r["pos"], "ok": bool(r["ok"]), "ms": r.get("ms")} for r in results]}
    a["routes"].append(w)
    return w


def route_report(a: dict) -> dict:
    ws = sorted(a["routes"], key=lambda w: w["ts"])
    walks = []
    for i, w in enumerate(ws):
        n = len(w["results"])
        ok = sum(1 for r in w["results"] if r["ok"])
        ms = sorted(r["ms"] for r in w["results"] if r["ok"] and r["ms"] is not None)
        med = None if not ms else (ms[len(ms) // 2] if len(ms) % 2 else (ms[len(ms) // 2 - 1] + ms[len(ms) // 2]) / 2)
        walks.append({"walk": i + 1, "accuracy": _v(r1(ok / n * 100)) if n else None, "median_ms": _v(r1(med))})
    acc = [w["accuracy"] for w in walks if w["accuracy"] is not None]
    say = ("Walk the route to start." if not walks else
           f"{len(walks)} walks; the last recalled {acc[-1]}% of the route" + (f", up from {acc[0]}% on the first." if len(acc) > 1 else "."))
    return {"walks": walks, "say": say}


# ---------------------------------------------------------------- simulation with known answers

class SimWorld:
    """A simulated person with known triggers. n_nodes nodes across the senses; the first n_triggers carry a true
    weight (points added to the state), the rest none. Nodes 0 and 1 of the nulls (indices n_triggers and
    n_triggers + 1) together add `interaction`. Ratings are whole points 0-10 with noise."""

    def __init__(self, seed=1, n_nodes=12, n_triggers=4, strength=3.0, noise=1.5, interaction=3.0):
        self.rng = P.Rng(seed)
        self.n, self.noise = n_nodes, noise
        self.w = [strength * (0.6 + 0.8 * self.rng.u()) if i < n_triggers else 0.0 for i in range(n_nodes)]
        self.pair = (n_triggers, n_triggers + 1)
        self.inter = interaction

    def atlas(self):
        a = make_atlas("sim", "Stress")
        for i in range(self.n):
            add_node(a, "n" + str(i), "Node " + str(i), SENSES[i % len(SENSES)])
        add_combo(a, "pair", ["n" + str(self.pair[0]), "n" + str(self.pair[1])])
        return a

    def moment(self, a, ts, phase, scale=None):
        u = self.rng.u()
        if u < 0.2:
            nodes = []
        elif u < 0.32:
            nodes = list(self.pair)
        else:
            k = int(math.floor(self.rng.u() * self.n))
            nodes = [k]
            if self.rng.u() < 0.3:
                j = int(math.floor(self.rng.u() * self.n))
                if j != k:
                    nodes.append(j)
        shift = sum(self.w[k] * (scale[k] if scale else 1.0) for k in nodes)
        if self.pair[0] in nodes and self.pair[1] in nodes:
            shift += self.inter * (scale[self.pair[0]] if scale else 1.0)
        before = 2 + int(math.floor(self.rng.u() * 4))
        after = max(0, min(10, int(math.floor(before + shift + self.rng.gauss() * self.noise + 0.5))))
        expose(a, ts, ["n" + str(k) for k in nodes], before, after, phase)

    def sample(self, a, days, per_day=10, phase="map", t0=0, scale=None):
        for d in range(days):
            for k in range(per_day):
                self.moment(a, t0 + d * 86400 + k * 5400, phase, scale)


def sim_demo(seed, days=14) -> dict:
    s = SimWorld(seed)
    a = s.atlas()
    s.sample(a, days)
    return {"atlas": a, "truth": list(s.w), "pair": list(s.pair), "interaction": s.inter}


def _sim_map(seed, days, triggers=4, interaction=3.0):
    s = SimWorld(seed, n_triggers=triggers, interaction=interaction)
    a = s.atlas()
    s.sample(a, days)
    W = weights(a)
    true = ["n" + str(i) for i in range(triggers)]
    null = ["n" + str(i) for i in range(triggers, s.n)]
    found = sum(1 for i in true if W[i]["verdict"] == "trigger")
    false = sum(1 for i in null if W[i]["verdict"] == "trigger")
    c = combos(a)[0]["verdict"]
    return found, len(true), false, len(null), c, predict(a)["verdict"], readiness(a)["ready"]


def _sim_transfer(seed, spread, habituation=0.15, control=True, days=7):
    """Treat the strongest trigger (its weight falls by 80%); untreated triggers fall by `spread` of that; every
    weight also falls by `habituation` per mapping."""
    s = SimWorld(seed, n_triggers=5)
    a = s.atlas()
    s.sample(a, days, phase="map")
    h1 = [1 - habituation] * s.n
    if control:
        s.sample(a, days, phase="map2", t0=(days + 1) * 86400, scale=h1)
    node = choose_node(a)
    if node is None:
        return "too_few"
    k = int(node[1:])
    h2 = [(1 - habituation) * ((1 - habituation) if control else 1.0)] * s.n
    sc = [h2[i] * (0.2 if i == k else (1 - 0.8 * spread) if s.w[i] > 0 else 1.0) for i in range(s.n)]
    s.sample(a, days, phase="after", t0=(2 * days + 2) * 86400, scale=sc)
    return transfer(a, node)["verdict"]


def _sim_sweep(seed, peaked, per_rank=4):
    rng, a = P.Rng(seed), make_atlas("s")
    for h in HIGHER:
        true = (2.0 - 0.6 * abs(h["rank"] - 3)) if peaked else 1.0
        for k in range(per_rank):
            add_sweep(a, 0, h["id"], -(true + rng.gauss() * 0.8))
    return sweep_report(a)


def evaluate(n=100) -> dict:
    res = {}
    for days in (3, 7, 14):
        rows = [_sim_map(5000 + i, days) for i in range(n)]
        res[("map", days)] = {"found": _v(r1(sum(r[0] for r in rows) / sum(r[1] for r in rows) * 100)),
                              "false": _v(r1(sum(r[2] for r in rows) / sum(r[3] for r in rows) * 100)),
                              "only_together": _v(r1(sum(1 for r in rows if r[4] == "only_together") / n * 100)),
                              "predicts": _v(r1(sum(1 for r in rows if r[5] == "predicts") / n * 100)),
                              "ready": _v(r1(_mean([r[6] for r in rows])))}
    rows = [_sim_map(6000 + i, 7, triggers=0, interaction=0.0) for i in range(n)]
    res[("map", "null")] = {"false": _v(r1(sum(r[2] for r in rows) / sum(r[3] for r in rows) * 100)),
                            "only_together": _v(r1(sum(1 for r in rows if r[4] == "only_together") / n * 100)),
                            "predicts": _v(r1(sum(1 for r in rows if r[5] == "predicts") / n * 100))}
    for spread in (0.5, 0.0):
        for control, days in ((True, 7), (True, 14), (False, 7)):
            vs = [_sim_transfer(7000 + i, spread, control=control, days=days) for i in range(n)]
            res[("transfer", spread, control, days)] = {k: _v(r1(vs.count(k) / n * 100)) for k in ("spreads", "stays", "unclear", "no_change")}
    for peaked in (True, False):
        for per in (4, 8):
            rs = [_sim_sweep(8000 + i, peaked, per) for i in range(n)]
            res[("sweep", peaked, per)] = {k: _v(r1(sum(1 for r in rs if r["dims"]["abstraction"]["shape"] == k) / n * 100)) for k in ("peaks", "rises", "falls", "flat")}
            res[("sweep", peaked, per)]["top3"] = _v(r1(sum(1 for r in rs if r["dims"]["abstraction"]["top"] == "identity") / n * 100))
    return {"n": n, "res": res}


def report(ev: dict) -> str:
    R, n = ev["res"], ev["n"]
    L = ["# ATLAS on simulated people", "",
         f"Generated by `python -m rsso.atlas --evaluate`. {n} simulated people per row. Each has 12 possible triggers across the senses, "
         "4 of them real (each adding 1.8 to 4.2 points of stress), and two that only trigger together (3 points). Ten moments a day are "
         "sampled, one in five a control moment; ratings are whole points with noise. Built and tested in simulation; effect unproven in people.", "",
         "## The map (claims C93, C96)", "",
         "| Days sampled | Real triggers found | Null nodes called triggers | The pair found to trigger only together | Map predicts unseen moments | Nodes with a stable weight (of 12) |",
         "|---|---|---|---|---|---|"]
    for d in (3, 7, 14):
        x = R[("map", d)]
        L.append(f"| {d} | {x['found']}% | {x['false']}% | {x['only_together']}% | {x['predicts']}% | {x['ready']} |")
    x = R[("map", "null")]
    L += ["", f"With no real triggers and no pair (7 days), {x['false']}% of nodes were called triggers, the pair was called a combination in "
          f"{x['only_together']}%, and the map was said to predict in {x['predicts']}% of people.", "",
          "## Transfer to untreated triggers (claims C94, C95)", "",
          "Map, map again with no treatment, treat the strongest trigger (it falls by 80%), map a third time. Where the change spreads, "
          "untreated triggers fall by 40%; otherwise they do not. Every weight also falls by 15% from one mapping to the next by itself "
          "(habituation); the repeat mapping measures that drift and removes it.", "",
          "| Truth | Repeat mapping before treatment | Days per mapping | Called spreads | Called stays | Unclear | Treated node did not change |", "|---|---|---|---|---|---|---|"]
    for spread, name in ((0.5, "Spreads"), (0.0, "Stays")):
        for control, days in ((True, 7), (True, 14), (False, 7)):
            x = R[("transfer", spread, control, days)]
            L.append(f"| {name} | {'yes' if control else 'no'} | {days} | {x['spreads']}% | {x['stays']}% | {x['unclear']}% | {x['no_change']}% |")
    L += ["", "## The level sweep (claims C99, C100)", "",
          "Sessions at each of five higher nodes by abstraction. Peaked: the benefit is highest at the middle level (identity, 2 points) and "
          "falls by 0.6 points a level either side; flat: 1 point at every level. Session-to-session noise 0.8 points.", "",
          "| Truth | Sessions per level | Called peaks | Rises | Falls | Flat | Middle level found best |", "|---|---|---|---|---|---|---|"]
    for peaked, name in ((True, "Peaked"), (False, "Flat")):
        for per in (4, 8):
            x = R[("sweep", peaked, per)]
            L.append(f"| {name} | {per} | {x['peaks']}% | {x['rises']}% | {x['falls']}% | {x['flat']}% | {x['top3']}% |")
    L += ["", "Reading: a week of sampling (ten moments a day) finds most real triggers and few false ones; combinations and stable weights "
          "need two weeks. Transfer needs two weeks per mapping to be seen in two thirds of people. Without a repeat mapping before "
          "treatment, habituation looks like transfer: a change that did not spread is called \"spreads\" twice as often. Showing that a change "
          "stayed put (less than half a point on untreated triggers) needs more data than three two-week mappings give; with this design the "
          "honest reading of a negative result is \"unclear\". The level sweep needs about eight sessions per level to tell a peak from a flat line.", ""]
    return "\n".join(L)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["--evaluate"]:
        import pathlib
        path = pathlib.Path(__file__).resolve().parents[1] / "results" / "atlas.md"
        path.write_text(report(evaluate()), encoding="utf-8")
        print(f"wrote {path}")
        return 0
    print("usage: python -m rsso.atlas --evaluate")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
