"""TURN_RATINGS (spec/TURN_RATINGS.md): does the supporter's action predict the person's own next rating? ESConv.

    python3 -m rsxv.personlab.turn_ratings pilot PATH/ESConv.json [OUT.json]   # stage P, counts only (§4)
    python3 -m rsxv.personlab.turn_ratings main  PATH/ESConv.json [OUT.json]   # stage M (§5-§6)

Aggregates only. Nothing about any conversation is printed or written.
"""
from __future__ import annotations

import json
import random
import sys

import numpy as np

from .person import STRATEGY_TO_ACTION

ACTIONS = ["STABILISE", "EXPLORE", "SUGGEST", "SHARE", "NONE"]
SPLIT_SEED, BOOT_SEED, B = 2101, 12345, 2000
LEVEL = 1 - 0.01 / 2
DELTA = 0.01


def _num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if 1 <= v <= 5 else None


def start_of(conv: dict):
    return _num(((conv.get("survey_score") or {}).get("seeker") or {}).get("initial_emotion_intensity"))


def min_stage(a: int, n_seek: int) -> int:
    """RAPPORT_ESCONV's stage rule: first, middle or last third of the seeker turns."""
    return min(2, 3 * a // max(1, n_seek))


def events(D: list) -> list:
    """§2: one event per supporter block followed by a rated seeker turn."""
    out = []
    for n, conv in enumerate(D):
        d = conv["dialog"]
        seek = [i for i, t in enumerate(d) if t["speaker"] == "seeker"]
        start = start_of(conv)
        prev = None
        rated_at = {}
        for i in seek:
            r = _num((d[i].get("annotation") or {}).get("feedback"))
            if r is not None:
                rated_at[i] = r
        if seek and seek[0] in rated_at:
            prev = rated_at[seek[0]]
        for a in range(len(seek) - 1):
            lo, hi = seek[a], seek[a + 1]
            sup = [i for i in range(lo + 1, hi) if d[i]["speaker"] == "supporter"]
            y = rated_at.get(hi)
            if sup and y is not None:
                acts = {STRATEGY_TO_ACTION.get((d[i].get("annotation") or {}).get("strategy"), "NONE") for i in sup}
                out.append({"conv": n, "y": y, "p": prev, "stage": min_stage(a, len(seek)), "start": start,
                            "act": {k: (k in acts) for k in ACTIONS}})
            if y is not None:
                prev = y
    return out


def split(n_conv: int, seed: int = SPLIT_SEED):
    """§3: permute conversations, first half development, second half test."""
    idx = list(range(n_conv))
    random.Random(seed).shuffle(idx)
    h = n_conv // 2
    return set(idx[:h]), set(idx[h:])


def usable(ev: list) -> list:
    return [e for e in ev if e["p"] is not None and e["start"] is not None]


def pilot(D: list) -> dict:
    """§4: counts only; nothing pairs an action with a rating."""
    ev = events(D)
    dev, test = split(len(D))
    u = usable(ev)
    rated = sum(_num((t.get("annotation") or {}).get("feedback")) is not None
                for c in D for t in c["dialog"] if t["speaker"] == "seeker")
    per = {}
    for e in u:
        per[e["conv"]] = per.get(e["conv"], 0) + 1
    pc = sorted(per.values())
    q = lambda f: float(np.quantile(pc, f)) if pc else None
    ys = [e["y"] for e in u]
    ut = [e for e in u if e["conv"] in test]
    return {
        "conversations": len(D), "rated_seeker_turns": rated, "events": len(ev),
        "events_without_previous_rating": sum(e["p"] is None for e in ev),
        "events_without_start": sum(e["start"] is None for e in ev),
        "usable_events": len(u), "usable_dev": sum(e["conv"] in dev for e in u), "usable_test": len(ut),
        "events_per_conversation": {"q25": q(0.25), "median": q(0.5), "q75": q(0.75)},
        "action_true_all": {k: sum(e["act"][k] for e in u) for k in ACTIONS},
        "action_true_test": {k: sum(e["act"][k] for e in ut) for k in ACTIONS},
        "indicators_per_block": {str(m): sum(sum(e["act"].values()) == m for e in u) for m in range(1, 6)},
        "rating_distribution": {str(r): ys.count(float(r)) for r in range(1, 6)},
        "share_at_5": (ys.count(5.0) / len(ys)) if ys else None,
        "amendment_needed": len(ut) < 1500 or any(v < 100 for v in
                                                   {k: sum(e["act"][k] for e in ut) for k in ACTIONS}.values()),
    }


def features(e: dict, model: str) -> list:
    """§5 design rows."""
    if model == "B0":
        return []
    x = [1.0, e["p"], float(e["stage"] == 1), float(e["stage"] == 2), e["start"]]
    if model in ("M1", "M2"):
        x += [float(e["act"][k]) for k in ACTIONS]
    if model == "M2":
        x += [float(e["act"][k] and e["stage"] == s) for k in ACTIONS for s in (1, 2)]
    return x


def fit(ev: list, model: str):
    if model == "B0":
        return None
    X = np.array([features(e, model) for e in ev])
    y = np.array([e["y"] for e in ev])
    return np.linalg.lstsq(X, y, rcond=None)[0]


def predict(beta, ev: list, model: str) -> np.ndarray:
    if model == "B0":
        return np.array([e["p"] for e in ev])
    X = np.array([features(e, model) for e in ev])
    return np.clip(X @ beta, 1.0, 5.0)


def verdict(lo: float, hi: float, delta: float = DELTA) -> str:
    """§6, for (richer − simpler) mean squared error."""
    if hi < 0:
        return "SIGNAL"
    if lo > delta:
        return "WORSE"
    if -delta <= lo and hi <= delta:
        return "NULL"
    return "INCONCLUSIVE"


def contrast(err_a: np.ndarray, err_b: np.ndarray, convs: list, B: int = B, seed: int = BOOT_SEED, level: float = LEVEL):
    """Mean of err_a − err_b with a bootstrap over test conversations."""
    d = err_a - err_b
    by = {}
    for i, c in enumerate(convs):
        by.setdefault(c, []).append(i)
    keys = sorted(by)
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(B):
        idx = [i for c in rng.choice(keys, len(keys)) for i in by[c]]
        bs.append(float(d[idx].mean()))
    lo, hi = np.quantile(bs, (1 - level) / 2), np.quantile(bs, 1 - (1 - level) / 2)
    return {"estimate": float(d.mean()), "ci": [float(lo), float(hi)]}


def main_stage(D: list, B: int = B) -> dict:
    """§5-§6. Fits on the development half only; contrasts on the test half."""
    u = usable(events(D))
    dev, test = split(len(D))
    ed = [e for e in u if e["conv"] in dev]
    et = [e for e in u if e["conv"] in test]
    convs = [e["conv"] for e in et]
    y = np.array([e["y"] for e in et])
    betas, err, mse, clip = {}, {}, {}, {}
    for m in ("B0", "B1", "M1", "M2"):
        betas[m] = fit(ed, m)
        yhat = predict(betas[m], et, m)
        err[m] = (yhat - y) ** 2
        mse[m] = float(err[m].mean())
        clip[m] = float(np.mean((yhat <= 1.0) | (yhat >= 5.0)))
    q1 = contrast(err["M1"], err["B1"], convs, B)
    q2 = contrast(err["M2"], err["M1"], convs, B)
    b1b0 = contrast(err["B1"], err["B0"], convs, B)
    q1["verdict"], q2["verdict"] = verdict(*q1["ci"]), verdict(*q2["ci"])
    # Information: M1 action coefficients with intervals from refits on development-conversation bootstraps.
    byd = {}
    for e in ed:
        byd.setdefault(e["conv"], []).append(e)
    keys = sorted(byd)
    rng = np.random.default_rng(BOOT_SEED + 1)
    coefs = []
    for _ in range(B):
        s = [e for c in rng.choice(keys, len(keys)) for e in byd[c]]
        coefs.append(fit(s, "M1")[5:10])
    coefs = np.array(coefs)
    act = {k: {"coef": float(betas["M1"][5 + j]),
               "ci": [float(np.quantile(coefs[:, j], (1 - LEVEL) / 2)), float(np.quantile(coefs[:, j], 1 - (1 - LEVEL) / 2))]}
           for j, k in enumerate(ACTIONS)}
    return {"n_dev": len(ed), "n_test": len(et), "test_conversations": len(set(convs)), "mse": mse, "clip_share": clip,
            "Q1_M1_minus_B1": q1, "Q2_M2_minus_M1": q2, "B1_minus_B0": b1b0, "M1_action_coefficients": act,
            "level": LEVEL, "delta": DELTA}


def _cli(argv):
    stage, path = argv[0], argv[1]
    D = json.load(open(path, encoding="utf-8"))
    res = pilot(D) if stage == "pilot" else main_stage(D)
    res = {"spec": "spec/TURN_RATINGS.md", "stage": stage, "data": "ESConv.json, thu-coai f262d06", **res}
    txt = json.dumps(res, indent=1, sort_keys=True)
    if len(argv) > 2:
        open(argv[2], "w", encoding="utf-8").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    _cli(sys.argv[1:])
