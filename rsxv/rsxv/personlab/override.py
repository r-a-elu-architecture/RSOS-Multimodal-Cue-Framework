"""PERSONLAB step 5b (spec/PERSONLAB.md §7b): stress per turn and the profile-targeted override, with a placebo profile."""
from __future__ import annotations

import re

import numpy as np

from .person import STRATEGY_TO_ACTION

STOP = frozenset("""
that this with have what your about they them just know like feel feeling feels really think would could there been
were will when more some also very make want need from then than into much well even only does doing done because
being going thing things something anything everything time sure maybe right good help said tell told okay yeah
here where which while those these their thats dont cant youre theyre about sounds sound understand totally
""".split())
WORD = re.compile(r"[a-z]{4,}")
BANDS = ((2.0, "low"), (3.5, "mid"), (9.9, "high"))


def content(text: str) -> set:
    return {w for w in WORD.findall((text or "").lower().replace("'", "")) if w not in STOP}


def statement_words(profile: dict, text: str) -> list:
    """Content-word sets of the quotes of the profile's beliefs and identity statements. `text` is the builder input."""
    out = []
    for lv in ("beliefs", "identity"):
        for st in (profile.get("levels") or {}).get(lv, {}).get("statements", []):
            a, b = st["source"]["span"]
            out.append(content(text[a:b]))
    return out


def targets(block_texts: list, stmt_sets: list) -> bool:
    words = [content(t) for t in block_texts]
    return any(len(w & s) >= 2 for w in words for s in stmt_sets)


def band(x: float) -> str:
    return next(name for hi, name in BANDS if x <= hi)


def blocks(dialog: list, cut: int):
    """Blocks of supporter turns between consecutive seeker turns. Yields (i, j, texts, first_strategy, starts_at),
    where i and j are seeker numbers (1-based) and starts_at is the dialog index of the block's first supporter turn."""
    seekers = [n for n, t in enumerate(dialog) if t["speaker"] == "seeker"]
    for a in range(len(seekers) - 1):
        lo, hi = seekers[a], seekers[a + 1]
        sup = [n for n in range(lo + 1, hi) if dialog[n]["speaker"] == "supporter"]
        if not sup:
            continue
        yield a + 1, a + 2, [dialog[n]["content"] for n in sup], (dialog[sup[0]].get("annotation") or {}).get("strategy"), sup[0]


def events(conv_id, dialog, cut, stress: dict, own: list, placebo: list):
    """§7b events in the held-out half. stress: {seeker number: mean rating}."""
    out = []
    for i, j, texts, strat, start in blocks(dialog, cut):
        if start < cut or i not in stress or j not in stress:
            continue
        fb = (dialog[[n for n, t in enumerate(dialog) if t["speaker"] == "seeker"][j - 1]].get("annotation") or {}).get("feedback")
        out.append({"conv": conv_id, "d": stress[j] - stress[i], "action": STRATEGY_TO_ACTION.get(strat, "NONE"),
                    "band": band(stress[i]), "t": targets(texts, own), "p": targets(texts, placebo),
                    "fb": float(fb) if fb not in (None, "") else None})
    return out


def stratified(ev: list, key: str):
    """Stratified (action x band) difference in mean d between key=True and key=False; None if no stratum has both."""
    S = {}
    for e in ev:
        S.setdefault((e["action"], e["band"]), {True: [], False: []})[e[key]].append(e["d"])
    w = num = 0.0
    for g in S.values():
        n1, n0 = len(g[True]), len(g[False])
        if n1 and n0:
            wt = n1 * n0 / (n1 + n0)
            num += wt * (np.mean(g[True]) - np.mean(g[False])); w += wt
    return num / w if w else None


def bootstrap(ev: list, B=2000, seed=12345, level=0.975):
    convs = sorted({e["conv"] for e in ev})
    by = {c: [e for e in ev if e["conv"] == c] for c in convs}
    rng = np.random.default_rng(seed)
    T, P, D = [], [], []
    for _ in range(B):
        samp = [e for c in rng.choice(convs, len(convs)) for e in by[c]]
        t, p = stratified(samp, "t"), stratified(samp, "p")
        if t is None or p is None:
            continue
        T.append(t); P.append(p); D.append(t - p)
    a = (1 - level) / 2
    q = lambda xs: (float(np.quantile(xs, a)), float(np.quantile(xs, 1 - a)))
    return {"target": (stratified(ev, "t"), *q(T)), "placebo": (stratified(ev, "p"), *q(P)),
            "target_minus_placebo": (stratified(ev, "t") - stratified(ev, "p"), *q(D)), "draws": len(T)}


def weighted_kappa(a: list, b: list, k=5) -> float:
    """Quadratic-weighted kappa for integer ratings 1..k."""
    O = np.zeros((k, k))
    for x, y in zip(a, b):
        O[x - 1, y - 1] += 1
    n = O.sum()
    E = np.outer(O.sum(1), O.sum(0)) / n
    W = np.array([[(i - j) ** 2 / (k - 1) ** 2 for j in range(k)] for i in range(k)])
    return 1 - (W * O).sum() / (W * E).sum()
