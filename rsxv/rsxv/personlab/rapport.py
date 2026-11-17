"""RAPPORT_ESCONV (spec/RAPPORT_ESCONV.md): VAKOG matching and echo against the seekers' own ratings."""
from __future__ import annotations

import random
import re

import numpy as np

from .override import content
from .person import STRATEGY_TO_ACTION

SENSES = {
    "V": "see sees saw seen seeing look looks looked looking picture pictures clear clearly view views imagine show shows "
         "showed appear appears bright dark focus focused vision visualise visualize watch watching perspective",
    "A": "hear hears heard hearing sound sounds sounded listen listens listened listening say says said tell tells told "
         "talk talks talked talking voice loud quiet ring rings call called discuss discussed",
    "K": "feel feels felt feeling feelings touch touched hold holding held grasp heavy pressure tense tension hurt hurts "
         "warm comfortable uncomfortable stuck grip handle handled weight pain painful calm",
    "O": "smell smells smelled smelt scent fragrance stink",
    "G": "taste tastes tasted bitter sweet sour flavour flavor",
}
SENSE_WORDS = {s: set(v.split()) for s, v in SENSES.items()}
TOK = re.compile(r"[a-z]+")


def channel(text: str):
    toks = TOK.findall((text or "").lower())
    counts = {s: sum(t in w for t in toks) for s, w in SENSE_WORDS.items()}
    top = max(counts.values())
    if top == 0:
        return None
    best = [s for s, c in counts.items() if c == top]
    return best[0] if len(best) == 1 else None


def echo(seeker_text: str, block_text: str, share=0.25) -> bool:
    sw = content(seeker_text)
    return bool(sw) and len(sw & content(block_text)) / len(sw) >= share


def phrase_echo(seeker_text: str, block_text: str) -> bool:
    a = TOK.findall((seeker_text or "").lower()); b = " ".join(TOK.findall((block_text or "").lower()))
    return any(" ".join(a[i:i + 3]) in b for i in range(len(a) - 2))


def events(D: list, exclude: set, seed=2030):
    """One event per supporter block followed by a rated seeker turn, in conversations not excluded."""
    keep = [n for n in range(len(D)) if n not in exclude]
    pool = [(n, t["content"]) for n in keep for t in D[n]["dialog"] if t["speaker"] == "seeker"]
    rng = random.Random(seed)
    out = []
    for n in keep:
        d = D[n]["dialog"]
        seek = [i for i, t in enumerate(d) if t["speaker"] == "seeker"]
        for a in range(len(seek) - 1):
            lo, hi = seek[a], seek[a + 1]
            sup = [i for i in range(lo + 1, hi) if d[i]["speaker"] == "supporter"]
            fb = (d[hi].get("annotation") or {}).get("feedback")
            if not sup or fb in (None, ""):
                continue
            s_text, block = d[lo]["content"], " ".join(d[i]["content"] for i in sup)
            while True:
                pn, p_text = pool[rng.randrange(len(pool))]
                if pn != n:
                    break
            cs, cb, cp = channel(s_text), channel(block), channel(p_text)
            m, e = (cs is not None and cs == cb), echo(s_text, block)
            mp, ep = (cp is not None and cp == cb), echo(p_text, block)
            stage = min(2, 3 * a // max(1, len(seek)))
            out.append({"conv": n, "y": float(fb), "action": STRATEGY_TO_ACTION.get((d[sup[0]].get("annotation") or {}).get("strategy"), "NONE"),
                        "stage": stage, "MATCH": m, "ECHO": e, "BOTH": m and e, "NEITHER": not m and not e,
                        "MATCH_p": mp, "ECHO_p": ep, "BOTH_p": mp and ep, "NEITHER_p": not mp and not ep,
                        "phrase": phrase_echo(s_text, block), "ch_seeker": cs, "ch_block": cb})
    return out


def stratified(ev, feat, base=None):
    """Stratified difference in mean y, feature True against base (default: feature False)."""
    S = {}
    for e in ev:
        if e[feat]:
            g = True
        elif base is None or e[base]:
            g = False
        else:
            continue
        S.setdefault((e["action"], e["stage"]), {True: [], False: []})[g].append(e["y"])
    w = num = 0.0
    for g in S.values():
        n1, n0 = len(g[True]), len(g[False])
        if n1 and n0:
            wt = n1 * n0 / (n1 + n0); num += wt * (np.mean(g[True]) - np.mean(g[False])); w += wt
    return num / w if w else None


def test(ev, feat, B=2000, seed=12345, level=1 - 0.05 / 3, min_n=100):
    base = "NEITHER" if feat == "BOTH" else None
    n1 = sum(e[feat] for e in ev)
    n0 = sum((e[base] if base else not e[feat]) for e in ev)
    if n1 < min_n or n0 < min_n:
        return {"n_with": n1, "n_without": n0, "verdict": "NOT TESTABLE"}
    convs = sorted({e["conv"] for e in ev}); by = {}
    for e in ev:
        by.setdefault(e["conv"], []).append(e)
    rng = np.random.default_rng(seed)
    est, dif = [], []
    for _ in range(B):
        s = [e for c in rng.choice(convs, len(convs)) for e in by[c]]
        a = stratified(s, feat, base); p = stratified(s, feat + "_p", base + "_p" if base else None)
        if a is None or p is None:
            continue
        est.append(a); dif.append(a - p)
    q = lambda xs: (float(np.quantile(xs, (1 - level) / 2)), float(np.quantile(xs, 1 - (1 - level) / 2)))
    e0, p0 = stratified(ev, feat, base), stratified(ev, feat + "_p", base + "_p" if base else None)
    ci, cd = q(est), q(dif)
    if ci[1] < 0:
        v = "NEGATIVE"
    elif ci[0] <= 0:
        v = "NO EFFECT"
    elif cd[0] > 0:
        v = "HOLDS"
    else:
        v = "NOT SPECIFIC"
    return {"n_with": n1, "n_without": n0, "estimate": e0, "ci": ci, "placebo": p0, "minus_placebo": e0 - p0,
            "minus_placebo_ci": cd, "verdict": v}
