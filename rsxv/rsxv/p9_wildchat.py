"""Phase 9 (AGENTS.md §11.11 and its amendment): public-data replication on WildChat-1M shards 0–2.

    python3 -m rsxv.p9_wildchat prep   DATA.pkl WORK/        # tokens, unit hashes, events (workspace only)
    python3 -m rsxv.p9_wildchat obs    WORK/                 # observed statistics (numpy path + plain-Python checks)
    python3 -m rsxv.p9_wildchat null   WORK/ MEASURE A B     # redraw seeds A..B-1, checkpointed per seed block
    python3 -m rsxv.p9_wildchat cc     DATA.pkl WORK/        # P9-C2, P9-C5
    python3 -m rsxv.p9_wildchat report WORK/ OUT.json        # aggregates only

DATA.pkl is built by the workspace extractor (top-level fields only; the user pair is kept as its SHA-256 and never leaves
the workspace). Units are hashed with a 64-bit mixing hash over word ids; every observed statistic computed on the hashed
path is checked against the plain-Python definitions of mse.py / corpus_lineage_v2.py (exactly for notes and R1, on a
fixed sample for phrases). Only aggregates are written to OUT.json.
"""
from __future__ import annotations

import collections
import hashlib
import json
import pathlib
import pickle
import random
import re
import sys

import numpy as np

from .corpus_lineage import BOUND, STOP, drift, interval, rtype, spearman, terms_of, words
from .mse import notes as notes_py, phrases as phrases_py, shape, sim

M64 = np.uint64(0xFFFFFFFFFFFFFFFF)
LV_MSE = 0.01 / 3


def mix(x):
    x = x.astype(np.uint64)
    with np.errstate(over="ignore"):
        x ^= x >> np.uint64(30); x *= np.uint64(0xBF58476D1CE4E5B9)
        x ^= x >> np.uint64(27); x *= np.uint64(0x94D049BB133111EB)
        x ^= x >> np.uint64(31)
    return x


def key(turn, h):
    with np.errstate(over="ignore"):
        return mix(h ^ (turn.astype(np.uint64) * np.uint64(0x9E3779B97F4A7C15) + np.uint64(1)))


# ------------------------------------------------------------------------------------------------------------ prep
def prep(data, work):
    D = pickle.load(open(data, "rb"))
    convs = D["convs"]
    T = []                      # global turn table
    for c in convs:
        for k, (r, t) in enumerate(c["turns"]):
            T.append((c["cid"], k, r, t))
    role = np.array([1 if r == "user" else 0 for _, _, r, _ in T], np.int8)
    models = [c["model"] for c in convs]; nuser = [sum(r == "user" for r, _ in c["turns"]) for c in convs]
    n_conv = len(convs); convs_text = None
    conv = np.array([c for c, _, _, _ in T], np.int32)
    # events: user turn with the immediately previous assistant turn (same conversation) and the next one
    ev_u, ev_p, ev_n = [], [], []
    inh_a, inh_b = [], []
    for g in range(len(T)):
        if role[g] == 1 and g > 0 and conv[g - 1] == conv[g] and role[g - 1] == 0:
            ev_u.append(g); ev_p.append(g - 1)
            ev_n.append(g + 1 if g + 1 < len(T) and conv[g + 1] == conv[g] and role[g + 1] == 0 else -1)
        if role[g] == 0:
            pa = next((h for h in range(g - 1, -1, -1) if conv[h] != conv[g] or role[h] == 0), None)
            if pa is not None and conv[pa] == conv[g] and role[pa] == 0:
                inh_a.append(pa); inh_b.append(g)
    import array
    vocab = {}
    tok, tid = array.array("Q"), array.array("i")
    nv = {}
    nH, nI = array.array("Q"), array.array("i")
    sv, sidl = {}, array.array("i")
    for g, (_, _, _, t) in enumerate(T):
        ws = re.findall(r"\w+", t.lower())
        tok.extend(vocab.setdefault(x, len(vocab) + 1) for x in ws)
        tid.extend([g] * len(ws))
        st = notes_py(t)
        nH.extend(nv.setdefault(x, len(nv) + 1) for x in st); nI.extend([g] * len(st))
        sidl.append(sv.setdefault(tuple(shape(t)), len(sv)))
    del vocab, nv, T, D, convs
    tok = mix(np.frombuffer(tok, np.uint64)); tid = np.frombuffer(tid, np.int32).copy()
    sid = np.frombuffer(sidl, np.int32).copy()
    w = pathlib.Path(work)
    meta = {"n_turns": int(len(role)), "n_conv": n_conv}

    def ngram(n, side):
        L = len(tok) - n + 1
        h = tok[:L].copy()
        with np.errstate(over="ignore"):
            for k in range(1, n):
                h = mix(h * np.uint64(0x100000001B3) + tok[k:L + k])
            h = mix(h + np.uint64(n))
        i = tid[:L]
        ok = (i == tid[n - 1:]) & (role[i] == side)
        return h[ok], i[ok]

    def dedupe(H, I):
        o = np.lexsort((H, I)); H, I = H[o], I[o]
        keep = np.ones(len(H), bool); keep[1:] = (H[1:] != H[:-1]) | (I[1:] != I[:-1])
        return H[keep], I[keep]

    def finish(name, uH, uI, asst_parts):
        ua = np.unique(uH)
        aK, aU = [], []
        for aH, aI in asst_parts():
            m = np.isin(aH, ua)
            aK.append(key(aI[m], aH[m])); aU.append(np.unique(aH[m]))
            del aH, aI, m
        aK = np.unique(np.concatenate(aK)); aU = np.unique(np.concatenate(aU))
        q = np.isin(uH, aU)
        ulen = np.bincount(uI, minlength=len(role)).astype(np.int32)
        np.savez(w / f"{name}.npz", qH=uH[q], qI=uI[q], aK=aK, ulen=ulen)
        meta[name] = {"user_units": int(len(uH)), "queries": int(q.sum()), "asst_keys": int(len(aK))}
        print(name, meta[name], flush=True)

    for name, ns in (("r1", (8,)), ("phrases", (3, 4, 5, 6, 7))):
        parts = [ngram(n, 1) for n in ns]
        uH = np.concatenate([x[0] for x in parts]); uI = np.concatenate([x[1] for x in parts]); del parts
        uH, uI = dedupe(uH, uI)
        finish(name, uH, uI, lambda ns=ns: (ngram(n, 0) for n in ns))
        del uH, uI
    nH = mix(np.frombuffer(nH, np.uint64)); nI = np.frombuffer(nI, np.int32).copy()
    u = role[nI] == 1
    finish("notes", nH[u], nI[u], lambda: iter([(nH[~u], nI[~u])]))
    np.savez(w / "events.npz", role=role, conv=conv, ev_u=np.array(ev_u, np.int32), ev_p=np.array(ev_p, np.int32),
             ev_n=np.array(ev_n, np.int32), inh_a=np.array(inh_a, np.int32), inh_b=np.array(inh_b, np.int32), sid=sid)
    pickle.dump({"shapes": list(sv.keys()), "models": models, "nuser": nuser, "meta": meta},
                open(w / "meta.pkl", "wb"))
    print(json.dumps(meta, indent=1))


# ------------------------------------------------------------------------------------------------------------ core
class Units:
    """Membership of a user turn's units in an arbitrary assistant turn, for many (user, assistant) pairs at once."""

    def __init__(self, work, name, ev_u):
        z = np.load(pathlib.Path(work) / f"{name}.npz")
        self.aK, self.ulen = z["aK"], z["ulen"]
        qH, qI = z["qH"], z["qI"]
        pos = {int(g): e for e, g in enumerate(ev_u)}
        m = np.isin(qI, ev_u)
        self.qH = qH[m]
        lut = np.full(len(self.ulen), -1, np.int64); lut[ev_u] = np.arange(len(ev_u))
        self.qE = lut[qI[m]]
        self.den = self.ulen[ev_u].astype(np.float64)

    def hits(self, d, sel=None):
        """per query: is the unit in assistant turn d[event]"""
        qE, qH = (self.qE, self.qH) if sel is None else (self.qE[sel], self.qH[sel])
        k = key(d[qE], qH)
        i = np.searchsorted(self.aK, k)
        i[i >= len(self.aK)] = 0
        return self.aK[i] == k

    def share(self, d):
        h = self.hits(d)
        c = np.bincount(self.qE, weights=h, minlength=len(self.den))
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.where(self.den > 0, c / self.den, np.nan), c


def draw(rng, n, conv_e, asst, conv_a):
    d = asst[rng.integers(0, len(asst), n)]
    bad = conv_a[d] == conv_e
    while bad.any():
        d[bad] = asst[rng.integers(0, len(asst), int(bad.sum()))]
        bad = conv_a[d] == conv_e
    return d


class Shapes:
    def __init__(self, shapes):
        self.shapes = shapes
        self.K = np.zeros(0, np.int64); self.V = np.zeros(0, np.float64)
        self.ns = len(shapes)

    def sims(self, a, b):
        k = a.astype(np.int64) * self.ns + b.astype(np.int64)
        u, inv = np.unique(k, return_inverse=True)
        i = np.searchsorted(self.K, u); i2 = np.minimum(i, max(0, len(self.K) - 1))
        have = (len(self.K) > 0) & (self.K[i2] == u) if len(self.K) else np.zeros(len(u), bool)
        miss = u[~have]
        if len(miss):
            mv = np.array([sim(self.shapes[int(x // self.ns)], self.shapes[int(x % self.ns)]) for x in miss])
            K = np.concatenate([self.K, miss]); V = np.concatenate([self.V, mv])
            o = np.argsort(K, kind="stable"); self.K, self.V = K[o], V[o]
        j = np.searchsorted(self.K, u)
        return self.V[j][inv]


def load(work):
    w = pathlib.Path(work)
    E = dict(np.load(w / "events.npz"))
    M = pickle.load(open(w / "meta.pkl", "rb"))
    E["asst"] = np.where(E["role"] == 0)[0].astype(np.int32)
    return E, M


# ------------------------------------------------------------------------------------------------------------ observed
def observed(work):
    E, M = load(work)
    eu, ep, en, conv = E["ev_u"], E["ev_p"], E["ev_n"], E["conv"]
    res = {}
    per_event = {}
    for name in ("r1", "notes", "phrases"):
        U = Units(work, name, eu)
        hp = U.hits(ep)
        cp = np.bincount(U.qE, weights=hp, minlength=len(eu))
        if name == "r1":
            per_event["r1"] = (cp > 0).astype(float)
            per_event["r1_has"] = cp > 0
            continue
        share = np.where(U.den > 0, cp / np.maximum(U.den, 1), np.nan)
        per_event[name] = share
        # carry-forward: re-entered (in prev) vs own, share in next
        ok = en >= 0
        dn = np.where(ok, en, ep)
        hn = U.hits(dn)
        re_n = np.bincount(U.qE, weights=hp & hn, minlength=len(eu))
        own_n = np.bincount(U.qE, weights=(~hp) & hn, minlength=len(eu))
        re_c, own_c = cp, U.den - cp
        good = ok & (re_c > 0) & (own_c > 0)
        diff = np.full(len(eu), np.nan)
        diff[good] = re_n[good] / re_c[good] - own_n[good] / own_c[good]
        per_event[name + "_cf"] = diff
    pickle.dump(per_event, open(pathlib.Path(work) / "obs_events.pkl", "wb"))
    print({k: (np.nanmean(v), int(np.sum(~np.isnan(v)))) for k, v in per_event.items() if k != "r1_has"})


def check(data, work, n=3000):
    """plain-Python definitions on a fixed sample of events (seed 7) must equal the hashed path"""
    E, M = load(work)
    D = pickle.load(open(data, "rb"))
    T = [t for c in D["convs"] for _, t in c["turns"]]
    P = pickle.load(open(pathlib.Path(work) / "obs_events.pkl", "rb"))
    rng = random.Random(7)
    idx = rng.sample(range(len(E["ev_u"])), n)
    bad = collections.Counter()
    for e in idx:
        u, p, nx = T[E["ev_u"][e]], T[E["ev_p"][e]], E["ev_n"][e]
        from .corpus_lineage_v2 import grams
        bad["r1"] += bool(grams(u) & grams(p)) != bool(P["r1_has"][e])
        for nm, f in (("notes", notes_py), ("phrases", phrases_py)):
            U, A = f(u), f(p)
            v = len(U & A) / len(U) if U else float("nan")
            bad[nm] += not (abs(v - P[nm][e]) < 1e-9 or (np.isnan(v) and np.isnan(P[nm][e])))
            if nx >= 0 and U:
                N = f(T[nx]); re_, own = U & A, U - A
                if re_ and own:
                    c = len(re_ & N) / len(re_) - len(own & N) / len(own)
                    bad[nm + "_cf"] += not abs(c - P[nm + "_cf"][e]) < 1e-9
    print("mismatches in", n, "sampled events:", dict(bad))
    return dict(bad)


# ------------------------------------------------------------------------------------------------------------ nulls
def null(work, measure, a, b):
    E, M = load(work)
    eu, conv, asst = E["ev_u"], E["conv"], E["asst"]
    w = pathlib.Path(work)
    if measure in ("r1", "notes", "phrases"):
        U = Units(work, measure, eu)
        valid = U.den > 0
        ce = conv[eu]
    elif measure == "melody":
        S = Shapes(pickle.load(open(w / "meta.pkl", "rb"))["shapes"]); sid = E["sid"]; ce = conv[eu]
    elif measure == "inherit":
        S = Shapes(pickle.load(open(w / "meta.pkl", "rb"))["shapes"]); sid = E["sid"]; ce = conv[E["inh_b"]]
    stats, acc = [], None
    for s in range(a, b):
        rng = np.random.default_rng(s)
        d = draw(rng, len(ce), ce, asst, conv)
        if measure == "r1":
            _, c = U.share(d); v = (c > 0).astype(float); st = v.mean()
        elif measure in ("notes", "phrases"):
            sh, _ = U.share(d); v = np.where(valid, sh, 0.0); st = v[valid].mean()
        elif measure == "melody":
            v = S.sims(sid[eu], sid[d]); st = v.mean()
        else:
            v = S.sims(sid[E["inh_b"]], sid[d]); st = v.mean()
        stats.append(float(st))
        acc = v.copy() if acc is None else acc + v
    np.savez(w / f"null_{measure}_{a}_{b}.npz", stats=np.array(stats), acc=acc, n=b - a)
    print(measure, a, b, np.mean(stats), np.max(stats))


def melody_obs(data, work):
    E, M = load(work)
    D = pickle.load(open(data, "rb"))
    T = [t for c in D["convs"] for _, t in c["turns"]]
    S = Shapes(M["shapes"]); sid = E["sid"]
    eu, ep, en = E["ev_u"], E["ev_p"], E["ev_n"]
    re_ = S.sims(sid[eu], sid[ep])
    inh = S.sims(sid[E["inh_b"]], sid[E["inh_a"]])
    cf = np.full(len(eu), np.nan)
    for e in range(len(eu)):
        if en[e] < 0:
            continue
        pl = {l.strip() for l in T[ep[e]].splitlines() if l.strip()}
        ul = [l for l in T[eu[e]].splitlines() if l.strip()]
        rl = "\n".join(l for l in ul if l.strip() in pl)
        ol = "\n".join(l for l in ul if l.strip() not in pl)
        if rl and ol:
            ns = M["shapes"][sid[en[e]]]
            cf[e] = sim(shape(rl), list(ns)) - sim(shape(ol), list(ns))
    P = pickle.load(open(pathlib.Path(work) / "obs_events.pkl", "rb"))
    P.update({"melody": re_, "melody_cf": cf, "inherit": inh})
    # R3 on R1-positive events, plain Python
    from .corpus_lineage_v2 import grams
    r3 = np.full(len(eu), np.nan)
    for e in np.where(P["r1_has"])[0]:
        if en[e] < 0:
            continue
        u = T[eu[e]]
        hit = grams(u) & grams(T[ep[e]])
        span = {x for g in hit for x in g if len(x) >= 5 and x not in STOP}
        own = {x for x in words(u) if len(x) >= 5 and x not in STOP} - span
        if span and own:
            nw = set(words(T[en[e]]))
            r3[e] = len(span & nw) / len(span) - len(own & nw) / len(own)
    P["r3"] = r3
    pickle.dump(P, open(pathlib.Path(work) / "obs_events.pkl", "wb"))
    print({k: (float(np.nanmean(P[k])), int(np.sum(~np.isnan(P[k])))) for k in ("melody", "melody_cf", "inherit", "r3")})


# ------------------------------------------------------------------------------------------------------------ C2 / C5
def c2_c5(data, work):
    D = pickle.load(open(data, "rb"))
    by = collections.defaultdict(list)
    for c in D["convs"]:
        by[c["user"]].append(c)
    users3 = {u: sorted(cs, key=lambda c: (c["ts"] or 0, c["cid"])) for u, cs in by.items() if len(cs) >= 3}
    fams = []
    for u, cs in users3.items():
        bl = [(c["cid"], t, set(words(t))) for c in cs for r, t in c["turns"] if r == "user" and len(words(t)) >= 150]
        fam = []
        for b in bl:
            for f in fam:
                sl = f[-1][2]
                if len(sl & b[2]) / max(1, min(len(sl), len(b[2]))) >= 0.6:
                    f.append(b); break
            else:
                fam.append([b])
        fams += [f for f in fam if len(f) >= 3 and len({x[0] for x in f}) >= 2]

    def rankavg(v):
        o = np.argsort(v, kind="mergesort"); sv = v[o]
        r = np.empty(len(v)); i = 0
        b = np.flatnonzero(np.diff(sv) != 0) + 1
        starts = np.concatenate([[0], b]); ends = np.concatenate([b, [len(v)]])
        for s0, e0 in zip(starts, ends):
            r[o[s0:e0]] = (s0 + e0 - 1) / 2
        return r

    def rho(x, y):
        rx, ry = rankavg(x), rankavg(y)
        rx -= rx.mean(); ry -= ry.mean()
        den = np.sqrt((rx * rx).sum() * (ry * ry).sum())
        return float((rx * ry).sum() / den) if den else 0.0
    # drift is symmetric in its two arguments, so each family's drift matrix is computed once and a shuffle only
    # reassigns generation positions (identical to recomputing drift on the shuffled family)
    DM, IJ = [], []
    for f in fams:
        n = len(f); iu, ju = np.triu_indices(n, 1)
        DM.append(np.array([drift(f[i][1], f[j][1]) for i, j in zip(iu, ju)])); IJ.append((iu, ju))
    C2 = {"users_with_3_conversations": len(users3), "families": len(fams)}
    if len(fams) < 10:
        C2.update({"status": "NOT TESTABLE (fewer than 10 capsule families)"})
    else:
        ys = np.concatenate(DM)
        xs = np.concatenate([(ju - iu).astype(float) for iu, ju in IJ])
        r0 = rho(xs, ys)
        rng = random.Random(4242)
        ge = 0
        for _ in range(1000):
            xx = []
            for f, (iu, ju) in zip(fams, IJ):
                pos = np.array(rng.sample(range(len(f)), len(f)))
                xx.append(np.abs(pos[ju] - pos[iu]).astype(float))
            ge += rho(np.concatenate(xx), ys) >= r0
        p = (ge + 1) / 1001
        gen = collections.Counter(len(f) for f in fams)
        C2.update({"generations": {str(k): v for k, v in sorted(gen.items())}, "pairs": int(len(xs)), "rho": r0, "p": p,
                   "mean_drift_adjacent": float(ys[xs == 1].mean()),
                   "status": "PASS" if (r0 > 0 and p < 0.01) else "FAIL"})
    # C5
    ev = []
    for c in D["convs"]:
        T = c["turns"]
        for i, (r, t) in enumerate(T):
            if r != "assistant" or not BOUND.search(t):
                continue
            nu = next((j for j in range(i + 1, len(T)) if T[j][0] == "user"), None)
            if nu is None:
                continue
            nxt = [j for j in range(nu + 1, len(T)) if T[j][0] == "assistant"][:2]
            flip = any(not BOUND.search(T[j][1]) and len(T[j][1]) >= 300 for j in nxt)
            ev.append({"user": c["user"], "model": c["model"], "type": rtype(T[nu][1]), "flip": flip})
    us = sorted({c["user"] for c in D["convs"]})
    dev_users = set(us[: len(us) // 2])
    dev = [e for e in ev if e["user"] in dev_users]
    ho = [e for e in ev if e["user"] not in dev_users]
    base = (sum(e["flip"] for e in dev) + 1) / (len(dev) + 2)
    rate = {k: (sum(e["flip"] for e in dev if e["type"] == k) + base) / (sum(e["type"] == k for e in dev) + 1)
            for k in ("reframe", "context", "insist", "none")}

    def auc(es):
        pos = collections.Counter(rate[e["type"]] for e in es if e["flip"])
        neg = collections.Counter(rate[e["type"]] for e in es if not e["flip"])
        P, N = sum(pos.values()), sum(neg.values())
        if not P or not N:
            return None
        s = sum(cp * cn * ((a > b) + 0.5 * (a == b)) for a, cp in pos.items() for b, cn in neg.items())
        return s / (P * N)
    C5 = {"events": len(ev), "dev": len(dev), "heldout": len(ho), "flip_rate_by_type_dev": rate,
          "types_heldout": dict(collections.Counter(e["type"] for e in ho)),
          "flip_share_all": sum(e["flip"] for e in ev) / max(1, len(ev))}
    if len(ho) < 30:
        C5["status"] = "NOT TESTABLE (fewer than 30 held-out boundary events)"
    else:
        a = auc(ho)
        rng = random.Random(12345)
        k = len(ho)
        dist = sorted((lambda s: auc(s) if auc(s) is not None else 0.5)([ho[rng.randrange(k)] for _ in range(k)])
                      for _ in range(2000))
        lo, hi = interval(dist, 0.01)
        C5.update({"auc_heldout": a, "ci99": [lo, hi], "status": "PASS" if (a is not None and lo > 0.5) else "FAIL"})
    json.dump({"C2": C2, "C5": C5}, open(pathlib.Path(work) / "cc.json", "w"), indent=1, default=float)
    print(json.dumps({"C2": C2, "C5": C5}, indent=1, default=float))


# ------------------------------------------------------------------------------------------------------------ report
def cluster_boot(vals, groups, n=2000, seed=12345, level=0.01):
    m = ~np.isnan(vals)
    v, g = vals[m], groups[m]
    ug, gi = np.unique(g, return_inverse=True)
    S = np.bincount(gi, weights=v); C = np.bincount(gi).astype(float)
    rng = random.Random(seed)
    k = len(ug)
    dist = []
    for _ in range(n):
        w = np.bincount(np.array([rng.randrange(k) for _ in range(k)]), minlength=k)
        dist.append(float((w @ S) / (w @ C)))
    dist.sort()
    return float(v.mean()), int(len(v)), int(k), interval(dist, level)


def nulls(work, measure):
    fs = sorted(pathlib.Path(work).glob(f"null_{measure}_*.npz"), key=lambda p: int(p.stem.split("_")[-2]))
    st, acc, n = [], 0, 0
    for f in fs:
        z = np.load(f); st += list(z["stats"]); acc = acc + z["acc"]; n += int(z["n"])
    return np.array(st), acc / max(n, 1)


def report(work, out):
    E, M = load(work)
    P = pickle.load(open(pathlib.Path(work) / "obs_events.pkl", "rb"))
    cc = json.load(open(pathlib.Path(work) / "cc.json"))
    conv = E["conv"]; ce = conv[E["ev_u"]]; ci = conv[E["inh_b"]]
    models = np.array(M["models"]); nuser = np.array(M["nuser"])
    band = np.where(nuser >= 10, "10+", np.where(nuser >= 5, "5-9", "3-4"))
    R = {"data": M["meta"]}

    def perm(name, obs_vals, groups, nred):
        st, base_ev = nulls(work, name)
        st = st[:nred] if len(st) >= nred else st
        o = float(np.nanmean(obs_vals))
        p = (np.sum(st >= o) + 1) / (len(st) + 1)
        p200 = (np.sum(st[:200] >= o) + 1) / (min(200, len(st)) + 1)
        m = ~np.isnan(obs_vals)
        g = groups[m]; d = (obs_vals - base_ev)[m]
        ug, gi = np.unique(g, return_inverse=True)
        pc = np.bincount(gi, weights=d) / np.bincount(gi)
        sub = {}
        for lab, arr in (("model", models[g]), ("length_band", band[g])):
            sub[lab] = {k: {"observed": float(obs_vals[m][arr == k].mean()), "baseline": float(base_ev[m][arr == k].mean()),
                            "n": int((arr == k).sum())} for k in sorted(set(arr))}
        return {"n_events": int(m.sum()), "observed": o, "baseline": float(np.mean(st)), "baseline_max": float(np.max(st)),
                "redraws": int(len(st)), "p": float(p), "p_200": float(p200),
                "per_conversation": {"conversations": int(len(ug)), "share_above_baseline": float(np.mean(pc > 0)),
                                     "median_diff": float(np.median(pc))}, **sub}

    r1 = perm("r1", P["r1"], ce, 200); r1["status"] = "PASS" if r1["p"] < 0.01 else "FAIL"
    R["P9-R1"] = r1
    mean, n, k, (lo, hi) = cluster_boot(P["r3"], ce)
    R["P9-R3"] = {"events": n, "conversations": k, "mean_diff": mean, "ci99": [lo, hi],
                  "status": "PASS" if lo > 0 else "FAIL"}
    mse = {}
    for name in ("notes", "phrases", "melody"):
        re_ = perm(name, P[name], ce, 2000); re_["clears"] = bool(re_["p"] < LV_MSE)
        mean, n, k, (lo, hi) = cluster_boot(P[name + "_cf"], ce, level=LV_MSE)
        cf = {"events": n, "conversations": k, "mean_diff": mean, "ci": [lo, hi], "clears": bool(lo > 0)}
        mse[name] = {"reentry": re_, "carry_forward": cf}
    ih = perm("inherit", P["inherit"], ci, 2000); ih["clears"] = bool(ih["p"] < LV_MSE)
    mse["melody"]["inheritance"] = ih
    R["P9-MSE"] = mse
    R["P9-C2"], R["P9-C5"] = cc["C2"], cc["C5"]
    pathlib.Path(out).write_text(json.dumps(R, indent=1, default=float))
    print(json.dumps(R, indent=1, default=float)[:6000])


if __name__ == "__main__":
    a = sys.argv[1:]
    {"prep": lambda: prep(a[1], a[2]), "obs": lambda: observed(a[1]), "check": lambda: check(a[1], a[2]),
     "melody": lambda: melody_obs(a[1], a[2]), "null": lambda: null(a[1], a[2], int(a[3]), int(a[4])),
     "cc": lambda: c2_c5(a[1], a[2]), "report": lambda: report(a[1], a[2])}[a[0]]()
