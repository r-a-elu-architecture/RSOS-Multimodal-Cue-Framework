"""The test for claim C35: does a vibration rhythm change the EEG at that frequency? (roadmap item 29, spec/MACHINES.md §4)

A rhythmic stimulus can drive a steady-state response in the EEG at its own frequency (a steady-state evoked
potential). The trap is that a vibration motor near the head or the electrodes also puts its drive signal into the
recording electrically, at exactly the same frequency. A comparison of vibration with rest therefore finds "an effect"
even when the brain does nothing.

The design here separates the two:

  * vibration: the band on the wrist, pulsing at the rhythm;
  * sham: the same band driven identically but resting on foam beside the wrist, so it is not felt (the same
    electrical pickup, no sensation);
  * rest: nothing.

Trials start at the motor's onset, so both the brain's response and the pickup are phase-locked to it. Per trial the
complex Fourier coefficient at the rhythm is taken (scaled by the neighbouring bins' noise). The brain's response is
the distance between the vibration and sham means, which cancels the pickup before its size is taken: comparing power
instead misses real responses, because a response and the pickup at different phases partly cancel. The pickup is
sham against rest. Each test is a permutation test (p < 0.05); the group pools the per-person z scores. Simulated EEG with known answers checks
that the test finds a real response and does not report pickup as one. Python only (an analysis for recorded data).
Built and tested in simulation; untested in people.
"""
from __future__ import annotations

import json
import math
import sys

import numpy as np

FS = 250
TRIAL_S = 5                    # 0.2 Hz bins: 7.8 Hz and 12 Hz both fall on a bin


def _r(x, k=2):
    return float(math.floor(x * 10 ** k + 0.5) / 10 ** k)


def sim_eeg(rng, cond, f_target=12.0, brain_uv=0.0, pickup_uv=0.0, trials=30, phase=0.0):
    """Trials of one condition (vibration, sham or rest): background EEG (1/f noise and alpha bursts near 10 Hz),
    a phase-locked brain response at f_target when the rhythm is felt, and electrical pickup at f_target whenever the
    motor is driven. `phase` is the person's response delay as a phase: fixed for a person, different between people."""
    n = FS * TRIAL_S
    t = np.arange(n) / FS
    out = []
    for _ in range(trials):
        white = rng.normal(0, 1, n)
        spec = np.fft.rfft(white)
        f = np.fft.rfftfreq(n, 1 / FS)
        spec[1:] /= np.sqrt(f[1:])
        bg = np.fft.irfft(spec, n)
        bg *= 6.0 / bg.std()
        af = 9.5 + rng.uniform(0, 2)
        alpha = rng.uniform(1, 6) * np.sin(2 * np.pi * af * t + rng.uniform(0, 2 * np.pi))
        x = bg + alpha
        if cond == "vibration" and brain_uv:
            x = x + brain_uv * np.sin(2 * np.pi * f_target * t + phase + rng.normal(0, 0.3))
        if cond in ("vibration", "sham") and pickup_uv:
            x = x + pickup_uv * np.sin(2 * np.pi * f_target * t)
        out.append(x)
    return np.array(out)


def coef(trials, f_target):
    """Complex Fourier coefficient at f_target for each trial (Hann window), and the power of the neighbouring bins
    (the background). Trials must start at the motor's onset, so the response and the pickup are phase-locked to it."""
    n = trials.shape[1]
    F = np.fft.rfft(trials * np.hanning(n), axis=1)
    k = int(round(f_target * TRIAL_S))
    nb = [k + d for d in (-5, -4, -3, -2, 2, 3, 4, 5)]
    return F[:, k], float((np.abs(F[:, nb]) ** 2).mean())


def snr(trials, f_target):
    """Log signal-to-noise ratio at f_target for each trial (power: blind to phase)."""
    n = trials.shape[1]
    p = np.abs(np.fft.rfft(trials * np.hanning(n), axis=1)) ** 2
    k = int(round(f_target * TRIAL_S))
    nb = [k + d for d in (-5, -4, -3, -2, 2, 3, 4, 5)]
    return np.log10(p[:, k] / p[:, nb].mean(axis=1))


def _perm(a, b, rng, n=300):
    """The distance between the complex means of two sets of trials, as a z score against label permutations, with
    its permutation p value. Phase-aware: what is identical in both (the pickup) cancels before the size is taken."""
    stat = abs(a.mean() - b.mean())
    allc = np.concatenate([a, b])
    na = len(a)
    null = np.empty(n)
    for i in range(n):
        idx = rng.permutation(len(allc))
        null[i] = abs(allc[idx[:na]].mean() - allc[idx[na:]].mean())
    return float((stat - null.mean()) / null.std()), float((1 + (null >= stat).sum()) / (n + 1))


def analyze(vib, sham, rest, f_target, rng=None) -> dict:
    """One person's recordings (trials x samples per condition): the brain's response is vibration against sham
    (phase-aware, so identical pickup cancels), the pickup is sham against rest, and the naive test vibration against
    rest. A test counts when p < 0.05."""
    rng = rng or np.random.default_rng(0)
    (cv, nv), (cs, ns), (cr, nr) = coef(vib, f_target), coef(sham, f_target), coef(rest, f_target)
    scale = math.sqrt((nv + ns + nr) / 3)          # one background scale for all three, so identical pickup cancels exactly
    cv, cs, cr = cv / scale, cs / scale, cr / scale
    brain, pickup, naive = _perm(cv, cs, rng), _perm(cs, cr, rng), _perm(cv, cr, rng)
    found = brain[1] < 0.05
    verdict = ("a response at the rhythm beyond the electrical pickup" if found else
               "no response beyond the electrical pickup" if pickup[1] < 0.05 and naive[1] < 0.05 else "no response found")
    return {"f": f_target, "brain_z": _r(brain[0]), "brain_p": _r(brain[1], 3), "pickup_p": _r(pickup[1], 3), "naive_p": _r(naive[1], 3),
            "found": bool(found), "pickup_present": bool(pickup[1] < 0.05), "naive_claims": bool(naive[1] < 0.05),
            "power_claims": bool(_welch_low(snr(vib, f_target), snr(sham, f_target)) > 0), "verdict": verdict}


def _welch_low(a, b):
    """Lower end of the 95% interval of a difference of means (Welch): the power-only test."""
    return a.mean() - b.mean() - 1.96 * math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))


def group(results) -> dict:
    """Pooled across people: the mean of the per-person z scores with a t interval (found when it excludes 0)."""
    d = np.array([r["brain_z"] for r in results])
    m, se = d.mean(), d.std(ddof=1) / math.sqrt(len(d))
    t = {5: 2.571, 10: 2.228, 15: 2.131, 20: 2.086, 29: 2.045}.get(len(d) - 1, 2.0)
    return {"n": len(d), "effect": _r(m), "low": _r(m - t * se), "high": _r(m + t * se), "found": bool(m - t * se > 0)}


SCENARIOS = [
    ("A real response and electrical pickup", 0.5, 0.6),
    ("Electrical pickup only, no brain response", 0.0, 0.6),
    ("A real response, no pickup", 0.5, 0.0),
    ("Neither", 0.0, 0.0),
]


def evaluate(people=20, groups=10, seed=35) -> dict:
    rng = np.random.default_rng(seed)
    out = {}
    for f in (12.0, 7.8):
        rows = []
        for title, brain, pickup in SCENARIOS:
            allp, found, effects = [], 0, []
            for _ in range(groups):
                res = []
                for _ in range(people):
                    ph = rng.uniform(0, 2 * np.pi)
                    res.append(analyze(sim_eeg(rng, "vibration", f, brain, pickup, phase=ph), sim_eeg(rng, "sham", f, brain, pickup, phase=ph),
                                       sim_eeg(rng, "rest", f, brain, pickup, phase=ph), f, rng))
                g = group(res)
                found += g["found"]
                effects.append(g["effect"])
                allp += res
            n = len(allp)
            rows.append({"title": title, "true": brain > 0,
                         "person_claims": _r(100 * sum(x["found"] for x in allp) / n, 1),
                         "naive_claims": _r(100 * sum(x["naive_claims"] for x in allp) / n, 1),
                         "power_claims": _r(100 * sum(x["power_claims"] for x in allp) / n, 1),
                         "pickup_flagged": _r(100 * sum(x["pickup_present"] for x in allp) / n, 1),
                         "groups_found": found, "groups": groups, "mean_effect": _r(sum(effects) / groups)})
        out[str(f)] = rows
    return out


def report(ev) -> str:
    L = ["# Claim C35: an EEG response at the vibration rhythm", "",
         "Generated by `python -m rsso.ssep --evaluate`. Simulated EEG with known answers: 10 groups of 20 people per row, 30 trials of 5 s per condition "
         "(vibration felt; sham, driven but not felt; rest). Built and tested in simulation; untested in people.", ""]
    for f, rows in ev.items():
        L += [f"## {float(f):g} Hz", "",
              "| Truth | People with a response found (vibration against sham, with phase) | The same by power alone | Naive test (vibration against rest) claims one | Pickup flagged | Groups of 20 finding a response | Mean group z |",
              "|---|---|---|---|---|---|---|"]
        for r in rows:
            L.append(f"| {r['title']} | {r['person_claims']:g}% | {r['power_claims']:g}% | {r['naive_claims']:g}% | {r['pickup_flagged']:g}% | "
                     f"{r['groups_found']} of {r['groups']} | {r['mean_effect']:g} |")
        L.append("")
    L += ["Reading: when the motor's drive leaks into the recording, a comparison with rest reports a brain response that is not there; "
          "the sham condition removes that, but only when it is subtracted with phase: compared by power alone (log SNR, 95% interval above 0), a real response "
          "and the pickup at different phases partly cancel and most real responses are missed. Trials must therefore start at the motor's onset. A response at the rhythm would still not show that focus improves or that a theta state "
          "follows: the TRIAL design `rhythm_focus` tests focus with the 2-back test."]
    return "\n".join(L) + "\n"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["--evaluate"]:
        import pathlib
        ev = evaluate()
        path = pathlib.Path(__file__).resolve().parents[1] / "results" / "ssep.md"
        path.write_text(report(ev), encoding="utf-8")
        print(json.dumps({f: [(r["title"][:20], r["person_claims"], r["naive_claims"], r["groups_found"]) for r in rows] for f, rows in ev.items()}))
        return 0
    print("usage: python -m rsso.ssep --evaluate")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
