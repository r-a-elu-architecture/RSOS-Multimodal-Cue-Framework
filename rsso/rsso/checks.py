"""CHECKS — built-in cognitive tests (spec/CHECKS.md).

Short browser tasks with standard scoring, so that claims about memory, attention, reaction and reading can be
measured over time instead of asserted: n-back (working memory), digit span, reaction time (calm and under time
pressure), word recall, reading speed and comprehension, and a dot-probe task for attention drawn to threat.
Generators are seeded (identical sequences in Python and JavaScript); scoring is identical too (tested).
docs/js/checks.js mirrors this module.

These are research measures, not diagnostic tests. Scores vary with sleep, time of day and practice; compare a
person with themselves over time.
"""
from __future__ import annotations

import math

from .peak import Rng

LETTERS = "BCDFGHJKLMNPQRSTVWXZ"
WORDS = ["anchor", "basket", "candle", "garden", "harbor", "island", "jacket", "kettle", "ladder", "marble", "napkin",
         "orchard", "pencil", "quarry", "ribbon", "saddle", "tunnel", "violin", "window", "yogurt", "bridge", "carpet",
         "falcon", "glacier", "hammer", "lantern", "meadow", "needle", "pepper", "rocket", "silver", "timber", "valley",
         "walnut", "zipper", "button", "copper", "feather", "orange", "pillow"]
THREAT = ["danger", "attack", "failure", "reject", "panic", "threat", "injury", "shame", "abandon", "collapse",
          "assault", "terror", "humiliate", "disaster", "betray", "hostile", "punish", "fear", "violent", "ruin"]
NEUTRAL = ["window", "garden", "pencil", "cabinet", "lantern", "harbor", "teacup", "meadow", "notebook", "staircase",
           "blanket", "kettle", "orchard", "library", "ribbon", "carpet", "basket", "pillow", "candle", "button"]
PASSAGES = [
    {"id": "bees", "title": "How bees share a map",
     "text": "A honeybee that finds a good patch of flowers returns to the hive and dances. On the vertical comb, the "
             "angle of her waggle run from straight up matches the angle between the sun and the flowers. The length of "
             "the run tells the distance: a longer waggle means a farther patch. Other bees follow her closely, feeling "
             "the vibrations in the dark, and then fly out on the bearing she showed. Because the sun moves across the "
             "sky, a dancer who keeps dancing for an hour slowly turns her run to keep the bearing true. Scouts that "
             "find poor patches dance briefly or not at all, so the colony sends most foragers to the richest flowers "
             "without any bee ever seeing the whole field.",
     "questions": [["What does the angle of the waggle run show?", ["The direction relative to the sun", "The number of flowers", "The time of day", "The danger on the way"], 0],
                   ["What does a longer waggle run mean?", ["Better nectar", "A farther patch", "Rain is coming", "More bees are needed"], 1],
                   ["Why do most foragers go to the richest flowers?", ["The queen chooses", "Scouts from poor patches dance briefly", "The richest flowers are nearest", "Bees follow the scent trail"], 1]]},
    {"id": "tides", "title": "Why there are two tides a day",
     "text": "Most coasts see two high tides and two low tides each day. The moon's gravity pulls the ocean toward it, "
             "raising a bulge of water on the side of the earth that faces the moon. A second bulge forms on the far "
             "side, because there the moon pulls the solid earth slightly more than the distant water, leaving the water "
             "behind. As the earth turns, a coast passes through both bulges, so it meets two high tides. The moon also "
             "moves along its orbit, which is why the tides arrive about fifty minutes later each day. When the sun and "
             "the moon line up, at new and full moon, their pulls add together and the tides are largest.",
     "questions": [["Why is there a bulge on the side facing away from the moon?", ["The sun pushes it there", "The moon pulls the earth more than the far water", "Wind piles the water up", "The earth spins faster there"], 1],
                   ["Why do tides come about fifty minutes later each day?", ["The moon moves along its orbit", "The oceans slow down", "The earth's day is getting longer", "Clocks are adjusted"], 0],
                   ["When are tides largest?", ["At half moon", "When the sun and moon line up", "In winter only", "When the moon is farthest away"], 1]]},
    {"id": "lighthouse", "title": "How a lighthouse is recognised",
     "text": "At night every lighthouse looks like a point of light, so sailors tell them apart by their rhythm. Each "
             "light has its own character, written on charts: a single flash every ten seconds, for example, or two "
             "quick flashes and a long pause, or a steady light that is briefly cut off. Some lights show different "
             "colours in different directions, so a ship that sees red knows it is heading toward rocks and should turn "
             "until the light shows white. Before electricity, keepers wound clockwork that turned the lens through the "
             "night. Today most lights run automatically, but the rhythms have stayed the same, because the charts still "
             "use them.",
     "questions": [["How do sailors tell lighthouses apart at night?", ["By their height", "By their rhythm of flashes", "By radio only", "By the keeper's signal"], 1],
                   ["What should a ship do if it sees a red sector?", ["Keep its course", "Turn until the light shows white", "Stop and anchor", "Signal back in red"], 1],
                   ["Why have the rhythms stayed the same?", ["The charts still use them", "The lenses cannot change", "Law forbids changes", "Keepers prefer them"], 0]]},
]


def r1(x):
    return None if x is None else math.floor(x * 10 + 0.5) / 10


def r2(x):
    return None if x is None else math.floor(x * 100 + 0.5) / 100


def _v(x):
    return int(x) if isinstance(x, float) and x.is_integer() else x


def _pick(rng, n):
    return math.floor(rng.u() * n)


def _shuffle(xs, rng):
    xs = list(xs)
    for i in range(len(xs) - 1, 0, -1):
        j = _pick(rng, i + 1)
        xs[i], xs[j] = xs[j], xs[i]
    return xs


def zq(p: float) -> float:
    """Inverse of the standard normal distribution (Acklam's approximation)."""
    a = [-39.69683028665376, 220.9460984245205, -275.9285104469687, 138.3577518672690, -30.66479806614716, 2.506628277459239]
    b = [-54.47609879822406, 161.5858368580409, -155.6989798598866, 66.80131188771972, -13.28068155288572]
    c = [-0.007784894002430293, -0.3223964580411365, -2.400758277161838, -2.549732539343734, 4.374664141464968, 2.938163982698783]
    d = [0.007784695709041462, 0.3224671290700398, 2.445134137142996, 3.754408661907416]
    lo = 0.02425
    if p < lo:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p > 1 - lo:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)


# ---------------------------------------------------------------- n-back

def gen_nback(seed: int, n=2, length=24, targets=8) -> list[dict]:
    rng = Rng(seed)
    pos = sorted(_shuffle(list(range(n, length)), rng)[:targets])
    seq = []
    for i in range(length):
        if i in pos:
            seq.append(seq[i - n])
        else:
            while True:
                ch = LETTERS[_pick(rng, len(LETTERS))]
                if i < n or ch != seq[i - n]:
                    break
            seq.append(ch)
    return [{"i": i, "letter": ch, "target": i >= n and ch == seq[i - n]} for i, ch in enumerate(seq)]


def score_nback(seq: list[dict], pressed: list[dict]) -> dict:
    """pressed: [{i, rt}] for every letter the person marked as a match."""
    pr = {int(p["i"]): p.get("rt") for p in pressed}
    hits = sum(1 for s in seq if s["target"] and s["i"] in pr)
    t = sum(1 for s in seq if s["target"])
    fa = sum(1 for s in seq if not s["target"] and s["i"] in pr)
    nt = len(seq) - t
    hr, fr = (hits + 0.5) / (t + 1), (fa + 0.5) / (nt + 1)
    rts = [float(pr[s["i"]]) for s in seq if s["target"] and s["i"] in pr and pr[s["i"]] is not None]
    return {"task": "nback", "hits": hits, "targets": t, "false_alarms": fa, "non_targets": nt,
            "accuracy": _v(r1((hits + nt - fa) / len(seq) * 100)) if seq else None,
            "d_prime": _v(r2(zq(hr) - zq(fr))), "rt": _v(r1(sum(rts) / len(rts))) if rts else None}


# ---------------------------------------------------------------- digit span

def gen_digits(seed: int, length: int) -> str:
    rng, out = Rng(seed), ""
    while len(out) < length:
        d = str(_pick(rng, 10))
        if not out or d != out[-1]:
            out += d
    return out


def score_span(trials: list[dict]) -> dict:
    """trials: [{length, correct}] in the order given (two per length; stop after two misses at one length)."""
    best, total = 0, 0
    for t in trials:
        if t.get("correct"):
            total += 1
            best = max(best, int(t["length"]))
    return {"task": "span", "span": best, "correct": total, "trials": len(trials)}


def next_span(trials: list[dict], start=3, top=10):
    """The next length to give, or None when the task ends."""
    if not trials:
        return start
    last = int(trials[-1]["length"])
    at = [t for t in trials if int(t["length"]) == last]
    if len(at) < 2:
        return last
    if not any(t.get("correct") for t in at):
        return None
    return last + 1 if last < top else None


# ---------------------------------------------------------------- reaction time

def score_reaction(rts: list, misses=0) -> dict:
    """rts: reaction times in ms; under 150 ms counts as an anticipation, over 500 ms as a lapse."""
    xs = sorted(float(x) for x in rts if x is not None)
    valid = [x for x in xs if x >= 150]
    out = {"task": "reaction", "n": len(xs), "anticipations": len(xs) - len(valid), "lapses": sum(1 for x in valid if x > 500),
           "misses": int(misses), "median": None, "mean": None, "sd": None}
    if valid:
        k = len(valid)
        med = valid[k // 2] if k % 2 else (valid[k // 2 - 1] + valid[k // 2]) / 2
        m = sum(valid) / k
        out.update({"median": _v(r1(med)), "mean": _v(r1(m)),
                    "sd": _v(r1(math.sqrt(sum((x - m) * (x - m) for x in valid) / (k - 1)))) if k > 1 else None})
    return out


def gen_delays(seed: int, n=15, lo=1500, hi=4000) -> list[int]:
    rng = Rng(seed)
    return [lo + _pick(rng, hi - lo) for _ in range(n)]


# ---------------------------------------------------------------- recall

def gen_words(seed: int, n=12) -> list[str]:
    return _shuffle(WORDS, Rng(seed))[:n]


def score_recall(words: list[str], answer: str) -> dict:
    said = [w for w in "".join(ch if ch.isalpha() else " " for ch in answer.lower()).split() if w]
    seen, correct, intr, rep = set(), 0, 0, 0
    target = {w.lower() for w in words}
    for w in said:
        if w in seen:
            rep += 1
            continue
        seen.add(w)
        if w in target:
            correct += 1
        else:
            intr += 1
    return {"task": "recall", "correct": correct, "of": len(words), "intrusions": intr, "repeats": rep,
            "percent": _v(r1(correct / len(words) * 100)) if words else None}


# ---------------------------------------------------------------- reading

def passage(pid: str) -> dict:
    return next(p for p in PASSAGES if p["id"] == pid)


def word_count(text: str) -> int:
    return len(text.split())


def score_reading(pid: str, ms: float, answers: list) -> dict:
    p = passage(pid)
    words = word_count(p["text"])
    right = sum(1 for q, a in zip(p["questions"], answers) if a is not None and int(a) == q[2])
    wpm = words / (float(ms) / 60000) if ms and ms > 0 else None
    comp = right / len(p["questions"])
    return {"task": "reading", "passage": pid, "words": words, "wpm": _v(r1(wpm)) if wpm else None, "correct": right,
            "of": len(p["questions"]), "comprehension": _v(r1(comp * 100)), "effective_wpm": _v(r1(wpm * comp)) if wpm else None}


# ---------------------------------------------------------------- attention to threat (dot-probe)

def gen_dotprobe(seed: int, n=32) -> list[dict]:
    rng = Rng(seed)
    th, ne = _shuffle(THREAT, rng), _shuffle(NEUTRAL, rng)
    sides = _shuffle((["left"] * (n // 2)) + (["right"] * (n - n // 2)), rng)
    cong = _shuffle(([True] * (n // 2)) + ([False] * (n - n // 2)), rng)
    out = []
    for k in range(n):
        ts = sides[k]
        probe = ts if cong[k] else ("right" if ts == "left" else "left")
        out.append({"k": k, "threat": th[k % len(th)], "neutral": ne[k % len(ne)], "threat_side": ts, "probe_side": probe,
                    "congruent": cong[k]})
    return out


def score_dotprobe(trials: list[dict], responses: list[dict]) -> dict:
    """responses: [{k, side, rt}]. Bias = mean RT when the probe replaces the neutral word minus when it replaces the
    threat word (correct trials, 200-1500 ms). Positive: attention is drawn to threat."""
    by = {int(r["k"]): r for r in responses}
    con, inc, wrong = [], [], 0
    for t in trials:
        r = by.get(t["k"])
        if not r:
            continue
        if r.get("side") != t["probe_side"]:
            wrong += 1
            continue
        rt = float(r["rt"])
        if 200 <= rt <= 1500:
            (con if t["congruent"] else inc).append(rt)
    mc = sum(con) / len(con) if con else None
    mi = sum(inc) / len(inc) if inc else None
    return {"task": "dotprobe", "congruent_rt": _v(r1(mc)) if mc is not None else None, "incongruent_rt": _v(r1(mi)) if mi is not None else None,
            "bias": _v(r1(mi - mc)) if mc is not None and mi is not None else None, "errors": wrong, "n": len(con) + len(inc)}
