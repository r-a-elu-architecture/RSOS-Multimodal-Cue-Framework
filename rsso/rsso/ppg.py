"""Heart rate and HRV from a fingertip over the phone camera (photoplethysmography), spec/PEAK.md section 4.

With the flash on and a fingertip covering the camera, the frame's red brightness dips with each heartbeat as
blood fills the fingertip. The page samples the mean red value of each frame; this module turns that series
into beats, heart rate and RMSSD, with a quality score. docs/js/ppg.js is identical (tested) and also holds the
camera capture.

  analyze(samples)   samples: [[t_ms, red], ...] at about 30 frames a second, 20-60 s long
"""
from __future__ import annotations

import math

MIN_RR, MAX_RR = 333, 1500          # 40-180 beats a minute
DETREND_MS, SMOOTH = 750, 2         # +-0.75 s baseline, +-2 frame smoothing


def r1(x):
    return None if x is None else math.floor(x * 10 + 0.5) / 10


def _v(x):
    return int(x) if isinstance(x, float) and x.is_integer() else x


def analyze(samples: list) -> dict:
    s = [(float(t), float(v)) for t, v in samples]
    out = {"ok": False, "rmssd_ok": False, "hr": None, "rmssd": None, "beats": 0, "quality": 0, "seconds": 0, "say": ""}
    if len(s) < 2:
        out["say"] = "No signal. Cover the camera fully with a fingertip, flash on."
        return out
    secs = (s[-1][0] - s[0][0]) / 1000
    out["seconds"] = _v(r1(secs))
    if secs < 10 or len(s) < 150:
        out["say"] = "Too short. Hold still for at least 20 seconds."
        return out
    n = len(s)
    det, lo = [], 0
    for i in range(n):
        t = s[i][0]
        tot, k = 0.0, 0
        j = i
        while j >= 0 and t - s[j][0] <= DETREND_MS:
            tot += s[j][1]
            k += 1
            j -= 1
        j = i + 1
        while j < n and s[j][0] - t <= DETREND_MS:
            tot += s[j][1]
            k += 1
            j += 1
        det.append(s[i][1] - tot / k)
    y = []
    for i in range(n):
        tot, k = 0.0, 0
        for j in range(max(0, i - SMOOTH), min(n, i + SMOOTH + 1)):
            tot += det[j]
            k += 1
        y.append(-(tot / k))           # brightness dips with each beat: invert so beats are peaks
    m = sum(y) / n
    sd = math.sqrt(sum((v - m) * (v - m) for v in y) / n)
    if sd <= 0:
        out["say"] = "The signal is flat. Cover the camera fully and turn the flash on."
        return out
    thr = m + 0.3 * sd
    peaks = []
    for i in range(1, n - 1):
        if y[i] > y[i - 1] and y[i] >= y[i + 1] and y[i] > thr:
            if peaks and s[i][0] - s[peaks[-1]][0] < MIN_RR:
                if y[i] > y[peaks[-1]]:
                    peaks[-1] = i
            else:
                peaks.append(i)
    pt = []
    for i in peaks:                    # sub-frame peak time by parabolic interpolation
        den = y[i - 1] - 2 * y[i] + y[i + 1]
        off = 0.5 * (y[i - 1] - y[i + 1]) / den if den != 0 else 0.0
        off = max(-0.5, min(0.5, off))
        dt = (s[i + 1][0] - s[i - 1][0]) / 2
        pt.append(s[i][0] + off * dt)
    rr = [pt[k] - pt[k - 1] for k in range(1, len(pt))]
    rr = [x for x in rr if MIN_RR <= x <= MAX_RR]
    out["beats"] = len(peaks)
    if len(rr) < 5:
        out["say"] = "Too few clear beats. Press lightly, keep still, and try again."
        return out
    srt = sorted(rr)
    med = srt[len(srt) // 2] if len(srt) % 2 else (srt[len(srt) // 2 - 1] + srt[len(srt) // 2]) / 2
    keep = [abs(x - med) <= 0.25 * med for x in rr]
    good = [x for x, k in zip(rr, keep) if k]
    q = len(good) / len(rr)
    out["quality"] = _v(r1(q * 100))
    diffs = [rr[k] - rr[k - 1] for k in range(1, len(rr)) if keep[k] and keep[k - 1] and abs(rr[k] - rr[k - 1]) <= 0.2 * med]
    out["hr"] = _v(r1(60000 / (sum(good) / len(good))))
    out["rmssd"] = _v(r1(math.sqrt(sum(d * d for d in diffs) / len(diffs)))) if diffs else None
    out["ok"] = q >= 0.7 and len(good) >= 8
    out["rmssd_ok"] = out["ok"] and q >= 0.95 and len(diffs) >= 8
    out["say"] = ("Good reading." if out["ok"] else "Noisy reading: keep the finger still and press lightly, then try again.")
    return out


def synthetic(bpm=72, swing=30, seconds=30, fps=30, noise=0.4, drift=4.0, seed=5, jitter_ms=4):
    """A fingertip signal: red brightness dips with each beat; RR alternates +-swing ms around 60000/bpm."""
    from .peak import Rng
    rng = Rng(seed)
    beats, t, k = [], 400.0, 0
    base = 60000 / bpm
    while t < seconds * 1000 + 1000:
        beats.append(t)
        t += base + (swing if k % 2 else -swing)
        k += 1
    out, n = [], int(seconds * fps)
    for i in range(n):
        ts = i * 1000 / fps + jitter_ms * (rng.u() - 0.5)
        v = 180 + drift * math.sin(ts / 4000)
        for b in beats:
            d = ts - b
            if -150 < d < 600:
                v -= 3.0 * math.exp(-((d - 90) / 70) ** 2) + 1.0 * math.exp(-((d - 330) / 90) ** 2)
        out.append([round(ts, 1), round(v + noise * rng.gauss(), 3)])
    rr = [beats[k] - beats[k - 1] for k in range(1, len(beats))]
    true_rmssd = math.sqrt(sum((rr[k] - rr[k - 1]) ** 2 for k in range(1, len(rr))) / (len(rr) - 1))
    return out, 60000 / (sum(rr) / len(rr)), true_rmssd


def accuracy() -> list[dict]:
    """Camera reading against the known heart rate and RMSSD of synthetic fingertip signals."""
    rows = []
    for bpm, swing in ((60, 25), (72, 30), (95, 15), (120, 10)):
        for noise in (0.4, 1.2):
            sig, hr, rm = synthetic(bpm, swing, noise=noise)
            r = analyze(sig)
            rows.append({"bpm": bpm, "noise": noise, "true_hr": _v(r1(hr)), "hr": r["hr"], "true_rmssd": _v(r1(rm)),
                         "rmssd": r["rmssd"], "quality": r["quality"], "ok": r["ok"], "rmssd_ok": r["rmssd_ok"]})
    return rows
