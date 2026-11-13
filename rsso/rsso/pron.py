"""PRON: pronunciation feedback from sound and, optionally, the camera (roadmap item 10; spec/MACHINES.md §4).

A recording is compared with a model on three things a learner can change, after removing what they should not
change (their own voice pitch, vocal tract and speed):

  * melody: the pitch contour in semitones from each speaker's own median;
  * vowels: the shape of the spectrum (log power in 14 bands) in the middle of each syllable;
  * rhythm: the share of the phrase each syllable takes.

The largest difference over its threshold becomes the feedback, with where it happens. With the camera on, mouth
opening and lip rounding per syllable are checked against the vowel's target. Everything is plain arithmetic at
8 kHz, identical in docs/js/pron.js (tested). Drills are synthesised from a vowel and melody model, so every test
has a known answer. Built and tested in simulation; effect unproven in people (claim C14).
"""
from __future__ import annotations

import json
import math
import sys

from . import peak as P

SR = 8000
FRAME, HOP = 200, 160                        # 25 ms frames every 20 ms
VOWELS = {"a": (730, 1090), "e": (530, 1840), "i": (270, 2290), "o": (570, 840), "u": (300, 870)}
MOUTH = {"a": {"open": 0.62, "round": 0.2}, "e": {"open": 0.38, "round": 0.1}, "i": {"open": 0.18, "round": 0.05},
         "o": {"open": 0.45, "round": 0.7}, "u": {"open": 0.2, "round": 0.85}}
THRESH = {"melody": 2.0, "vowels": 5.5, "rhythm": 0.36}
NAMES = {"melody": "melody", "vowels": "vowel sound", "rhythm": "rhythm"}

DRILLS = [
    {"id": "question", "title": "A rising question", "syllables": [
        {"v": "e", "ms": 160, "f0": [120, 124]}, {"v": "a", "ms": 230, "f0": [126, 120]},
        {"v": "i", "ms": 170, "f0": [119, 118]}, {"v": "o", "ms": 280, "f0": [126, 182]}]},
    {"id": "statement", "title": "A falling statement", "syllables": [
        {"v": "a", "ms": 200, "f0": [150, 160]}, {"v": "o", "ms": 260, "f0": [165, 150]},
        {"v": "e", "ms": 160, "f0": [140, 128]}, {"v": "u", "ms": 260, "f0": [122, 95]}]},
    {"id": "stress", "title": "Stress on the second syllable", "syllables": [
        {"v": "o", "ms": 140, "f0": [130, 130]}, {"v": "e", "ms": 320, "f0": [150, 165]},
        {"v": "a", "ms": 150, "f0": [135, 125]}]},
    {"id": "i_e", "title": "i against e", "syllables": [
        {"v": "i", "ms": 240, "f0": [140, 135]}, {"v": "e", "ms": 240, "f0": [135, 130]},
        {"v": "i", "ms": 240, "f0": [132, 120]}]},
    {"id": "u_o", "title": "u against o", "syllables": [
        {"v": "u", "ms": 240, "f0": [140, 135]}, {"v": "o", "ms": 240, "f0": [135, 130]},
        {"v": "u", "ms": 240, "f0": [132, 120]}]},
]


def r1(x):
    return None if x is None else math.floor(x * 10 + 0.5) / 10


def r2(x):
    return None if x is None else math.floor(x * 100 + 0.5) / 100


def _v(x):
    return int(x) if isinstance(x, float) and x.is_integer() else x


# ---------------------------------------------------------------- synthesis (drills and simulated learners)

def synth(syllables, rng=None, f0_scale=1.0, formant_scale=1.0, tempo=1.0, noise=0.01) -> list:
    """A vowel string: glottal pulses through three resonators (F1, F2, F3), syllables separated by 50 ms of quiet
    breath. f0_scale shifts the voice, formant_scale the vocal tract, tempo the speed: the things feedback ignores."""
    rng = rng or P.Rng(1)
    out = [0.0] * int(0.08 * SR)
    for k, s in enumerate(syllables):
        n = int(s["ms"] / tempo * SR / 1000)
        F1, F2 = VOWELS[s["v"]]
        res = [_reson(F1 * formant_scale, 90), _reson(F2 * formant_scale, 110), _reson(2500 * formant_scale, 150)]
        st = [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]
        phase = 0.0
        for i in range(n):
            f0 = (s["f0"][0] + (s["f0"][1] - s["f0"][0]) * i / max(1, n - 1)) * f0_scale
            phase += f0 / SR
            x = 1.0 if phase >= 1 else 0.0
            if phase >= 1:
                phase -= 1
            x += (rng.u() - 0.5) * noise
            for j in range(3):
                a, b, c = res[j]
                y = a * x + b * st[j][0] + c * st[j][1]
                st[j][1] = st[j][0]
                st[j][0] = y
                x = y
            env = min(1.0, i / (0.02 * SR), (n - i) / (0.02 * SR))
            out.append(x * env)
        if k < len(syllables) - 1:
            out += [(rng.u() - 0.5) * noise for _ in range(int(0.05 / tempo * SR))]
    return out + [0.0] * int(0.08 * SR)


def _reson(f, bw):
    c = -math.exp(-2 * math.pi * bw / SR)
    b = 2 * math.exp(-math.pi * bw / SR) * math.cos(2 * math.pi * f / SR)
    return (1 - b - c, b, c)


# ---------------------------------------------------------------- features

NFFT = 256
EDGES = [200 * math.pow(3600 / 200, k / 14) for k in range(15)]          # 14 log-spaced bands, 200-3600 Hz


def _fft_power(w):
    """Power spectrum of a frame zero-padded to 256 (iterative radix-2), bins 0..128."""
    n = NFFT
    re = list(w) + [0.0] * (n - len(w))
    im = [0.0] * n
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j |= bit
        if i < j:
            re[i], re[j] = re[j], re[i]
    size = 2
    while size <= n:
        ang = -2 * math.pi / size
        for start in range(0, n, size):
            for k in range(size // 2):
                c, s_ = math.cos(ang * k), math.sin(ang * k)
                a_, b_ = start + k, start + k + size // 2
                tr = re[b_] * c - im[b_] * s_
                ti = re[b_] * s_ + im[b_] * c
                re[b_], im[b_] = re[a_] - tr, im[a_] - ti
                re[a_], im[a_] = re[a_] + tr, im[a_] + ti
        size *= 2
    return [re[k] * re[k] + im[k] * im[k] for k in range(n // 2 + 1)]


def _smooth(pw, h=4):
    """A moving average over 9 bins (280 Hz): the spectral envelope without the voice's harmonics."""
    n = len(pw)
    return [sum(pw[max(0, k - h):min(n, k + h + 1)]) / (min(n, k + h + 1) - max(0, k - h)) for k in range(n)]


def features(x: list) -> list:
    """Per 20 ms frame: level (dB), pitch (Hz or None) and band profile (log power in 14 bands, mean removed)."""
    out = []
    win = [0.5 - 0.5 * math.cos(2 * math.pi * i / (FRAME - 1)) for i in range(FRAME)]
    bins = [[k for k in range(NFFT // 2 + 1) if EDGES[b] <= k * SR / NFFT < EDGES[b + 1]] for b in range(14)]
    for s0 in range(0, len(x) - FRAME + 1, HOP):
        fr = x[s0:s0 + FRAME]
        e = sum(v * v for v in fr) / FRAME
        pw = _smooth(_fft_power([fr[i] * win[i] for i in range(FRAME)]))
        prof = [10 * math.log10(sum(pw[k] for k in bb) / len(bb) + 1e-12) for bb in bins]
        m = sum(prof) / len(prof)
        out.append({"db": 10 * math.log10(e + 1e-12), "f0": _pitch(fr), "prof": [q - m for q in prof]})
    # pitch: a median of three frames removes single-frame octave slips
    raw = [f["f0"] for f in out]
    for i in range(len(out)):
        w = [v for v in raw[max(0, i - 1):i + 2] if v]
        out[i]["f0"] = _median(w) if raw[i] and len(w) >= 2 else raw[i]
    return out


def _pitch(fr):
    """Pitch by normalised autocorrelation of the centre-clipped frame over 70-400 Hz. The shortest lag that is a peak within 70% of
    the best, and repeating at twice the lag, is taken: this avoids reading half the pitch or a
    formant as the pitch; None when not clearly voiced."""
    top = max(abs(v) for v in fr)
    if top == 0:
        return None
    cl = 0.3 * top
    y = [(v - cl if v > cl else (v + cl if v < -cl else 0.0)) for v in fr]

    def r(L):
        num = a = b = 0.0
        for i in range(FRAME - L):
            u, v = y[i], y[i + L]
            num += u * v
            a += u * u
            b += v * v
        return num / math.sqrt(a * b) if a > 0 and b > 0 else 0.0
    lo, hi = SR // 400, SR // 70
    rs = {L: r(L) for L in range(lo, hi + 1)}
    best = max(rs.values())
    if best < 0.5:
        return None
    for L in range(lo + 1, hi):
        if rs[L] >= 0.7 * best and rs[L] > 0.45 and rs[L] >= rs[L - 1] and rs[L] >= rs[L + 1]:
            # a true period repeats: the double lag must correlate too (a formant's ringing does not)
            if 2 * L + 1 > hi or max(rs[2 * L - 1], rs[2 * L], rs[2 * L + 1]) >= 0.6 * best:
                return SR / L
    return SR / max(rs, key=lambda L: rs[L])


def syllables_of(F) -> list:
    """Syllable spans [start, end) in frames: runs of at least three frames above a threshold set
    between the background (the quietest tenth of frames) and the loudest, never more than 32 dB below it (a vowel string with short breaks between syllables; a real recording needs a clear break too)."""
    top = max(f["db"] for f in F)
    quiet = sorted(f["db"] for f in F if f["db"] > -100)
    floor = quiet[len(quiet) // 10] if quiet else top - 60
    thr = max(top - 32, floor + 0.4 * (top - floor))
    on = [f["db"] > thr for f in F]
    out, start = [], None
    for i, v in enumerate(on + [False]):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if i - start >= 3:
                out.append([start, i])
            start = None
    return out


# ---------------------------------------------------------------- comparison

def _dist(p, q):
    return math.sqrt(sum((p[i] - q[i]) * (p[i] - q[i]) for i in range(len(p))) / len(p))


def _st(f, ref):
    return 12 * math.log(f / ref) / math.log(2)


def _median(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def _syl_view(F, syl):
    """Per syllable: length in frames, pitch at five points (semitones from the speaker's median) and the mean band
    profile of its middle 60%."""
    voiced = [F[i]["f0"] for a, b in syl for i in range(a, b) if F[i]["f0"]]
    ref = _median(voiced) if voiced else None

    def fold(f):
        # an octave slip (a strong harmonic read as the pitch, or the reverse) folded back towards the speaker's median
        while f > 1.6 * ref:
            f /= 2
        while f < ref / 1.6:
            f *= 2
        return f
    out = []
    for a, b in syl:
        n = b - a
        pts = []
        for q in (0.1, 0.3, 0.5, 0.7, 0.9):
            i = a + min(n - 1, int(q * n))
            near = [fold(F[j]["f0"]) for j in range(max(a, i - 1), min(b, i + 2)) if F[j]["f0"]]
            pts.append(_st(_median(near), ref) if near and ref else None)
        m0, m1 = a + int(0.2 * n), max(a + int(0.2 * n) + 1, a + int(0.8 * n))
        prof = _detrend([sum(F[i]["prof"][k] for i in range(m0, m1)) / (m1 - m0) for k in range(14)])
        out.append({"n": n, "pts": pts, "prof": prof})
    return out


def _detrend(p):
    """Remove the mean and the straight-line tilt across bands (voice quality, microphone)."""
    n = len(p)
    mx = (n - 1) / 2
    my = sum(p) / n
    sxx = sum((k - mx) * (k - mx) for k in range(n))
    b = sum((k - mx) * (p[k] - my) for k in range(n)) / sxx
    return [p[k] - my - b * (k - mx) for k in range(n)]


def _shifted(p, sh):
    """The profile moved by `sh` bands along the log-frequency axis (linear interpolation, edges held)."""
    n = len(p)
    out = []
    for k in range(n):
        x = min(n - 1.0, max(0.0, k + sh))
        i = min(n - 2, int(x))
        f = x - i
        out.append(p[i] * (1 - f) + p[i + 1] * f)
    return _detrend(out)


def _tract_shift(model, learner):
    """One shift for the whole recording (a longer or shorter vocal tract moves every formant by the same ratio, which
    on log-spaced bands is a shift): the one in -1.2..1.2 bands that best matches the syllables, by their median distance."""
    best, bs = None, 0.0
    for k in range(-12, 13):
        sh = k / 10
        d = _median([_dist(m, _shifted(l, sh)) for m, l in zip(model, learner)])
        if best is None or d < best - 1e-12:
            best, bs = d, sh
    return bs


def compare(learner: list, model: list, vowels=None) -> dict:
    """Compare a learner's recording with the model (sample lists at 8 kHz), syllable by syllable. Returns scores
    0-100 for melody, vowels and rhythm, the measured differences (the largest over syllables), the syllable where
    each is largest and one piece of feedback."""
    FL, FM = features(learner), features(model)
    sl, sm = syllables_of(FL), syllables_of(FM)
    if len(sl) != len(sm):
        return {"scores": {k: None for k in THRESH}, "measured": {k: None for k in THRESH}, "at": {k: None for k in THRESH},
                "syllables": [len(sm), len(sl)], "worst": "count",
                "say": f"The model has {len(sm)} syllables and this recording {len(sl)}: say each vowel clearly, with a short break between."}
    VM, VL = _syl_view(FM, sm), _syl_view(FL, sl)
    sh = _tract_shift([v["prof"] for v in VM], [v["prof"] for v in VL])
    for v in VL:
        v["prof"] = _shifted(v["prof"], sh)
    tm, tl = sum(v["n"] for v in VM), sum(v["n"] for v in VL)
    per = {"melody": [], "vowels": [], "rhythm": []}
    for m, l in zip(VM, VL):
        d = [abs(x - y) for x, y in zip(m["pts"], l["pts"]) if x is not None and y is not None]
        per["melody"].append(sum(d) / len(d) if d else 0.0)
        per["vowels"].append(_dist(m["prof"], l["prof"]))
        per["rhythm"].append(abs(math.log((l["n"] / tl) / (m["n"] / tm))))
    meas = {k: max(v) for k, v in per.items()}
    at = {k: max(range(len(v)), key=lambda i: v[i]) for k, v in per.items()}
    score = {k: _v(r1(max(0.0, 100 * (1 - meas[k] / (2 * THRESH[k]))))) for k in THRESH}
    over = {k: meas[k] / THRESH[k] for k in THRESH if meas[k] > THRESH[k]}
    worst = max(over, key=lambda k: over[k]) if over else None
    return {"scores": score, "measured": {k: _v(r2(v)) for k, v in meas.items()}, "at": at,
            "syllables": [len(sm), len(sl)], "worst": worst, "say": feedback(worst, at.get(worst) if worst else None, vowels)}


def feedback(worst, k, vowels=None) -> str:
    if worst is None:
        return "Close to the model. Try it a little faster, or try the next drill."
    where = (f"syllable {k + 1}" + (f" ('{vowels[k]}')" if vowels and k is not None and k < len(vowels) else "")) if k is not None else "the phrase"
    return {"melody": f"The melody differs most on {where}: listen to whether the voice rises or falls there, and copy it.",
            "vowels": f"The vowel sound differs most on {where}: listen to the model's vowel there and shape your mouth to match.",
            "rhythm": f"The rhythm differs most on {where}: make it as long, compared with the others, as in the model."}[worst]


# ---------------------------------------------------------------- the camera (optional)

def mouth_feedback(trace: list, spans: list, vowels: list) -> dict:
    """trace: [{t, open, round}] per video frame, open = lip gap / mouth width, round = 1 - width / resting width
    (both 0-1); spans: [[t0, t1]] per syllable in seconds; vowels: the target vowel per syllable. Each syllable's
    median opening and rounding is compared with the vowel's target; the largest miss is the feedback."""
    rows, worst = [], None
    for k, (t0, t1) in enumerate(spans):
        fr = [p for p in trace if t0 <= p["t"] < t1]
        if not fr:
            rows.append({"syllable": k + 1, "vowel": vowels[k], "open": None, "round": None, "ok": None})
            continue
        o, r = _median([p["open"] for p in fr]), _median([p["round"] for p in fr])
        tg = MOUTH[vowels[k]]
        do, dr = o - tg["open"], r - tg["round"]
        miss = max(abs(do) / 0.15, abs(dr) / 0.25)
        rows.append({"syllable": k + 1, "vowel": vowels[k], "open": _v(r2(o)), "round": _v(r2(r)), "ok": miss <= 1})
        if miss > 1 and (worst is None or miss > worst[0]):
            worst = (miss, k, "open" if abs(do) / 0.15 >= abs(dr) / 0.25 else "round", do, dr)
    if worst is None:
        say = "Mouth shapes match the vowels." if any(r["ok"] for r in rows) else "No face seen; check the light and the camera."
    else:
        _, k, what, do, dr = worst
        v = vowels[k]
        say = (f"On '{v}' (syllable {k + 1}), " + (("open your mouth more" if do < 0 else "open your mouth less") if what == "open"
                                                    else ("round your lips more" if dr < 0 else "spread your lips, less rounded")) + ".")
    return {"rows": rows, "say": say}


def sim_mouth(rng, vowels, spans, fps=30, wrong=None):
    """A mouth trace with known answers: each syllable near its vowel's target; `wrong` = (syllable, vowel used)."""
    out, t, end = [], 0.0, spans[-1][1] + 0.1
    while t < end:
        v = None
        for k, (a, b) in enumerate(spans):
            if a <= t < b:
                v = wrong[1] if wrong and wrong[0] == k else vowels[k]
        tg = MOUTH[v] if v else {"open": 0.05, "round": 0.1}
        out.append({"t": t, "open": max(0.0, tg["open"] + rng.gauss() * 0.08), "round": min(1.0, max(0.0, tg["round"] + rng.gauss() * 0.12))})
        t += 1 / fps
    return out


# ---------------------------------------------------------------- simulation

def learner(drill, kind, rng):
    """A simulated learner saying a drill, in another voice at another speed; kind: correct, melody, vowels, rhythm.
    Returns (samples, the syllable with the error or None)."""
    syl = [dict(s, f0=list(s["f0"])) for s in drill["syllables"]]
    k = None
    if kind == "melody":
        k = len(syl) - 1
        a, b = syl[k]["f0"]
        syl[k]["f0"] = [a, a * math.pow(2, (-4 if b > a else 4) / 12)]   # the model rises: a fall of 4 semitones, and the reverse
    elif kind == "vowels":
        k = int(rng.u() * len(syl)) % len(syl)
        swap = {"a": "i", "e": "u", "i": "a", "o": "i", "u": "e"}
        syl[k]["v"] = swap[syl[k]["v"]]
    elif kind == "rhythm":
        k = min(range(len(syl)), key=lambda i: syl[i]["ms"])             # the shortest syllable held 2.2 times as long
        syl[k]["ms"] = int(syl[k]["ms"] * 2.2)
    f0s = math.pow(2, (-3 + rng.u() * 9) / 12)
    fs = 0.92 + rng.u() * 0.2
    tempo = 0.85 + rng.u() * 0.35
    return synth(syl, rng, f0_scale=f0s, formant_scale=fs, tempo=tempo, noise=0.02), k


def evaluate(n=40, seed=5) -> dict:
    rng = P.Rng(seed)
    out = {}
    models = {d["id"]: synth(d["syllables"]) for d in DRILLS}
    for kind in ("correct", "melody", "vowels", "rhythm"):
        right = flagged = located = total = 0
        for r in range(n):
            d = DRILLS[r % len(DRILLS)]
            if kind == "melody" and d["syllables"][-1]["f0"][0] == d["syllables"][-1]["f0"][1]:
                d = DRILLS[0]
            x, k = learner(d, kind, rng)
            c = compare(x, models[d["id"]], [s["v"] for s in d["syllables"]])
            total += 1
            flagged += c["worst"] is not None
            if kind != "correct" and c["worst"] == kind:
                right += 1
                located += c["at"][kind] == k
        out[kind] = {"n": total, "flagged": _v(r1(flagged / total * 100)), "named_right": _v(r1(right / total * 100)),
                     "located": _v(r1(located / total * 100))}
    # the camera
    mrng = P.Rng(seed + 1)
    ok_w = ok_c = 0
    for r in range(n):
        d = DRILLS[r % len(DRILLS)]
        vs = [s["v"] for s in d["syllables"]]
        spans, t = [], 0.1
        for s in d["syllables"]:
            spans.append([t, t + s["ms"] / 1000])
            t += s["ms"] / 1000 + 0.05
        k = r % len(vs)
        wrongv = {"a": "i", "e": "u", "i": "a", "o": "i", "u": "e"}[vs[k]]
        ok_w += mouth_feedback(sim_mouth(mrng, vs, spans, wrong=(k, wrongv)), spans, vs)["say"].startswith(f"On '{vs[k]}' (syllable {k + 1})")
        ok_c += mouth_feedback(sim_mouth(mrng, vs, spans), spans, vs)["say"] == "Mouth shapes match the vowels."
    out["camera"] = {"n": n, "wrong_found": _v(r1(ok_w / n * 100)), "correct_passed": _v(r1(ok_c / n * 100))}
    return out


def report(ev: dict) -> str:
    rows = [("A correct learner (other voice, other speed)", "correct"), ("The last syllable falls where the model rises, or the reverse", "melody"),
            ("One vowel replaced", "vowels"), ("The shortest syllable held 2.2 times as long", "rhythm")]
    L = ["# Pronunciation feedback on simulated learners", "",
         "Generated by `python -m rsso.pron --evaluate`. Drills are synthesised from a vowel and melody model; each learner speaks in another "
         "voice (pitch -3 to +6 semitones), with another vocal tract (formants x0.92-1.12) and at another speed (x0.85-1.2), which feedback must ignore. "
         "Built and tested in simulation; effect unproven in people (claim C14).", "",
         "| Learner | Runs | Any feedback given | The right thing named | And the right syllable |", "|---|---|---|---|---|"]
    for title, k in rows:
        e = ev[k]
        L.append(f"| {title} | {e['n']} | {e['flagged']}% | " + ("–" if k == "correct" else f"{e['named_right']}%") + " | " + ("–" if k == "correct" else f"{e['located']}%") + " |")
    c = ev["camera"]
    L += ["", f"Camera (simulated mouth traces, {c['n']} runs each): a wrong mouth shape on one vowel found on the right syllable in {c['wrong_found']}%; "
          f"correct shapes passed in {c['correct_passed']}%.", "",
          "Reading: on the correct learner, any feedback is a false alarm. The model's voice is synthetic; real voices, consonants and noise "
          "will lower these numbers, which is what the protocol kit measures."]
    return "\n".join(L) + "\n"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["--evaluate"]:
        import pathlib
        path = pathlib.Path(__file__).resolve().parents[1] / "results" / "pron.md"
        ev = evaluate()
        path.write_text(report(ev), encoding="utf-8")
        print(json.dumps(ev))
        return 0
    print("usage: python -m rsso.pron --evaluate")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
