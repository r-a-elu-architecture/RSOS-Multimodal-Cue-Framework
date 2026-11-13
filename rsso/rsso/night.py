"""SLEEP and REWARD (spec/NIGHT.md): closed-loop cueing during sleep, and reward codes for outside success events.

SLEEP
  A controller that replays the day's codes only in deep sleep (N3, held for a while), below waking level, stopping
  on any arousal, with a nightly limit; trauma-related cues are never replayed: a nightmare gets a safety code or a
  gentle waking instead. Night reports, the next-day recall test for cued against uncued items (targeted memory
  reactivation) and a night diary for nightmares. A seeded simulated sleeper with a known hypnogram, a device that
  misreads stages, cue-caused arousals and a known memory benefit checks it, against random cueing and no cueing.

REWARD
  An outside sensor or the person reports a success (a ball through the rim, a correct answer, a good move) and the
  area's reward code plays within a fraction of a second, within the safety limits; the code can be replayed at
  night. Code families per learning area (a shared prefix), a motion detector that recognises a good move from a
  template, the notice test (vibration alone or with light), and a simulated training study.

docs/js/night.js is identical (tested).
"""
from __future__ import annotations

import math
import sys

from . import peak as P
from . import trial as T

EPOCH = 30                                       # seconds per sleep epoch
STAGES = ("W", "N1", "N2", "N3", "REM")
STAGE_NAMES = {"W": "Awake", "N1": "Light (N1)", "N2": "Light (N2)", "N3": "Deep (N3)", "REM": "REM"}
POLICY = {"stable_epochs": 3, "pause_epochs": 10, "start": 0.3, "max": 0.6, "step_down": 0.7, "step_up": 0.02,
          "up_every": 20, "limit": 300, "detect_arousal": 0.9}
ACC = {"W": 0.85, "N1": 0.4, "N2": 0.8, "N3": 0.8, "REM": 0.75}          # a consumer headband's stage accuracy
NEIGHBOUR = {"W": ("N1", "N1"), "N1": ("W", "N2"), "N2": ("N1", "N3"), "N3": ("N2", "N2"), "REM": ("N1", "N2")}
AROUSE = {"W": 0.0, "N1": 0.25, "N2": 0.08, "N3": 0.03, "REM": 0.1}      # arousal chance per cue at mid intensity
TRAUMA_MODES = ("safety", "wake")
REWARD = {"budget_ms": 300, "refractory_ms": 1500, "per_minute": 20, "device_ms": 40}


def r1(x):
    return None if x is None else math.floor(x * 10 + 0.5) / 10


def r2(x):
    return None if x is None else math.floor(x * 100 + 0.5) / 100


def _v(x):
    return int(x) if isinstance(x, float) and x.is_integer() else x


def _mean(xs):
    return sum(xs) / len(xs)


def _ci(xs):
    m = _mean(xs)
    if len(xs) < 2:
        return m, None, None
    h = T.tcrit(len(xs) - 1) * math.sqrt(T._var(xs) / len(xs))
    return m, m - h, m + h


def _ci_diff(a, b):
    d = _mean(a) - _mean(b)
    if len(a) < 2 or len(b) < 2:
        return d, None, None
    va, vb = T._var(a) / len(a), T._var(b) / len(b)
    se = math.sqrt(va + vb)
    if se == 0:
        return d, d, d
    den = va * va / (len(a) - 1) + vb * vb / (len(b) - 1)
    df = max(1, int(math.floor((va + vb) * (va + vb) / den))) if den > 0 else len(a) + len(b) - 2
    h = T.tcrit(df) * se
    return d, d - h, d + h


def _median(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


# ---------------------------------------------------------------- the night plan

def make_plan(codes: list, channels=("vibration",), trauma="safety", safety_code=". .", limit=POLICY["limit"], max_intensity=POLICY["max"]) -> dict:
    """codes: [{code, label, area, trauma}] practised today. Trauma-related codes are never played during sleep."""
    if trauma not in TRAUMA_MODES:
        raise ValueError("trauma must be one of " + ", ".join(TRAUMA_MODES))
    play = [c for c in codes if not c.get("trauma")]
    held = [c for c in codes if c.get("trauma")]
    return {"schema": "rsos-night/1", "codes": play, "held": held, "channels": list(channels), "trauma": trauma, "safety_code": safety_code,
            "limit": int(limit), "max_intensity": min(float(max_intensity), 0.9),
            "say": (f"{len(play)} code{'s' if len(play) != 1 else ''} to replay in deep sleep" +
                    (f"; {len(held)} trauma-related code{'s' if len(held) != 1 else ''} held back, never played during sleep" if held else "") +
                    f"; a nightmare gets {'the safety code' if trauma == 'safety' else 'a gentle waking'}.")}


class Controller:
    """Decides, epoch by epoch, whether to cue. It sees only what a device sees: the estimated stage and whether an
    arousal was detected."""

    def __init__(self, plan: dict, kind="closed"):
        self.plan, self.kind = plan, kind
        self.stable, self.pause, self.n, self.intensity, self.quiet = 0, 0, 0, POLICY["start"], 0
        self.k = 0

    def step(self, i: int, est: str, aroused: bool, rng) -> dict | None:
        if self.kind == "none" or not self.plan["codes"]:
            return None
        if self.kind == "random":
            if rng.u() < 0.25 and self.n < self.plan["limit"]:
                return self._cue(i, self.plan["max_intensity"])
            return None
        if aroused or est == "W":
            if aroused:
                self.intensity = max(0.1, self.intensity * POLICY["step_down"])
            self.pause = i + POLICY["pause_epochs"]
            self.stable = 0
            return None
        self.stable = self.stable + 1 if est == "N3" else 0
        if i < self.pause or self.stable < POLICY["stable_epochs"] or self.n >= self.plan["limit"]:
            return None
        self.quiet += 1
        if self.quiet >= POLICY["up_every"]:
            self.quiet = 0
            self.intensity = min(self.plan["max_intensity"], self.intensity + POLICY["step_up"])
        return self._cue(i, self.intensity)

    def _cue(self, i, x):
        c = self.plan["codes"][self.k % len(self.plan["codes"])]
        self.k += 1
        self.n += 1
        return {"epoch": i, "code": c["code"], "intensity": _v(r2(x))}


# ---------------------------------------------------------------- a simulated sleeper

class Sleeper:
    """A night of 30-second epochs with sleep cycles: deep sleep early, REM later, brief awakenings; a device that
    misreads stages; cues that wake the sleeper with a chance that rises with intensity and lightness of sleep."""

    def __init__(self, seed=1, hours=8.0, arousability=1.0, acc=None, nightmares=0.0):
        self.rng = P.Rng(seed)
        self.arousability, self.acc = arousability, acc or ACC
        n = int(hours * 3600 / EPOCH)
        rng, h = self.rng, []

        def add(stage, minutes):
            for _ in range(max(0, int(math.floor(minutes * 2 + 0.5)))):
                h.append(stage)
        add("W", 6 + rng.u() * 10)
        add("N1", 3 + rng.u() * 4)
        n3 = [35, 25, 12, 5, 0, 0, 0]
        rem = [8, 15, 22, 28, 32, 35, 35]
        c = 0
        while len(h) < n:
            add("N2", 10 + rng.u() * 15)
            add("N3", n3[min(c, 6)] * (0.7 + 0.6 * rng.u()))
            add("N2", 5 + rng.u() * 5)
            add("REM", rem[min(c, 6)] * (0.7 + 0.6 * rng.u()))
            if rng.u() < 0.5:
                add("W", 0.5 + rng.u())
            c += 1
        self.plan = h[:n]
        self.nightmare_epochs = set()
        if nightmares > 0:
            rems = [i for i, s in enumerate(self.plan) if s == "REM"]
            k = int(math.floor(nightmares + rng.u()))
            for _ in range(k):
                if rems:
                    start = rems[int(math.floor(rng.u() * len(rems)))]
                    for j in range(start, min(start + 6, len(self.plan))):
                        if self.plan[j] == "REM":
                            self.nightmare_epochs.add(j)

    def estimate(self, stage):
        if self.rng.u() < self.acc[stage]:
            return stage
        a, b = NEIGHBOUR[stage]
        return a if self.rng.u() < 0.5 else b

    def run(self, controller: Controller | None, plan: dict | None = None) -> dict:
        """Play the night. Returns the true and estimated hypnograms, cues, arousals and the report."""
        true, est, cues, arousals = list(self.plan), [], [], []
        wake_until, aroused_flag = -1, False
        for i in range(len(true)):
            if i <= wake_until:
                true[i] = "W" if i < wake_until else "N1"
            e = self.estimate(true[i])
            est.append(e)
            seen = aroused_flag and self.rng.u() < POLICY["detect_arousal"]
            aroused_flag = False
            cue = controller.step(i, e, seen, self.rng) if controller else None
            if cue:
                cue["stage"] = true[i]
                p = min(0.9, AROUSE[true[i]] * (0.2 + 1.6 * cue["intensity"] * cue["intensity"]) * self.arousability) if true[i] != "W" else 0.0
                if self.rng.u() < p:
                    cue["aroused"] = True
                    arousals.append(i)
                    aroused_flag = True
                    wake_until = i + 1 + int(math.floor(self.rng.u() * 2))
                else:
                    cue["aroused"] = False
                cues.append(cue)
        return {"true": true, "est": est, "cues": cues, "arousals": arousals, "report": night_report(true, cues, arousals)}


def night_report(true: list, cues: list, arousals: list) -> dict:
    onset = next((i for i, s in enumerate(true) if s != "W"), len(true))
    sleep = [s for s in true[onset:] if s != "W"]
    waso = sum(1 for s in true[onset:] if s == "W")
    by = {s: sum(1 for c in cues if c["stage"] == s) for s in STAGES}
    good = sum(1 for c in cues if c["stage"] in ("N3", "N2") and not c["aroused"])
    return {"epochs": len(true), "sleep_min": _v(r1(len(sleep) * EPOCH / 60)), "n3_min": _v(r1(sum(1 for s in true if s == "N3") * EPOCH / 60)),
            "rem_min": _v(r1(sum(1 for s in true if s == "REM") * EPOCH / 60)), "waso_min": _v(r1(waso * EPOCH / 60)),
            "efficiency": _v(r1(len(sleep) / len(true) * 100)) if true else None,
            "cues": len(cues), "by_stage": by, "in_n3": _v(r1(by["N3"] / len(cues) * 100)) if cues else None,
            "arousals": len(arousals), "good": good}


# ---------------------------------------------------------------- next-day recall (targeted memory reactivation)

def tmr_analyze(nights: list) -> dict:
    """nights: [{cued_before, cued_after, uncued_before, uncued_after}] counts of items recalled in the evening and the
    next morning. The advantage is the retention of cued items minus that of uncued items, in percentage points."""
    d = []
    for n in nights:
        if n.get("cued_before") and n.get("uncued_before"):
            d.append(n["cued_after"] / n["cued_before"] * 100 - n["uncued_after"] / n["uncued_before"] * 100)
    if len(d) < 3:
        return {"nights": len(d), "advantage": None, "lo": None, "hi": None, "verdict": "too_few",
                "say": "Three or more cued nights are needed: learn in the evening, test, sleep with half the items cued, test again in the morning."}
    m, lo, hi = _ci(d)
    verdict = "helps" if lo > 0 else "hurts" if hi < 0 else "unclear"
    say = {"helps": "Cued items were kept better", "hurts": "Cued items were kept worse", "unclear": "No clear difference yet between cued and uncued items"}[verdict]
    return {"nights": len(d), "advantage": _v(r1(m)), "lo": _v(r1(lo)), "hi": _v(r1(hi)), "verdict": verdict,
            "say": say + f": {_v(r1(m))} points of retention [{_v(r1(lo))}, {_v(r1(hi))}] over {len(d)} nights."}


def diary_compare(entries: list, metric="nightmares") -> dict:
    """entries: [{night, cueing: bool, nightmares, distress (0-10)}]. Cueing nights against nights without."""
    on = [e[metric] for e in entries if e.get("cueing") and e.get(metric) is not None]
    off = [e[metric] for e in entries if not e.get("cueing") and e.get(metric) is not None]
    if len(on) < 3 or len(off) < 3:
        return {"on": len(on), "off": len(off), "difference": None, "lo": None, "hi": None, "verdict": "too_few",
                "say": "Three or more nights with and without cueing are needed."}
    d, lo, hi = _ci_diff(on, off)
    verdict = "lower" if hi < 0 else "higher" if lo > 0 else "unclear"
    name = {"nightmares": "nightmares", "distress": "distress"}.get(metric, metric)
    say = {"lower": f"Fewer {name} on cueing nights", "higher": f"More {name} on cueing nights", "unclear": f"No clear difference in {name} yet"}[verdict]
    return {"on": len(on), "off": len(off), "difference": _v(r2(d)), "lo": _v(r2(lo)), "hi": _v(r2(hi)), "verdict": verdict,
            "say": say + f": {_v(r2(d))} [{_v(r2(lo))}, {_v(r2(hi))}]."}


def nightmare_response(plan: dict, sleeper: Sleeper, sensitivity=0.8) -> dict:
    """Nightmares in REM, detected from a heart-rate surge with `sensitivity` per epoch; the plan's response is the
    safety code (ends the nightmare with a chance of 0.6 each epoch) or a gentle waking (ends it at once)."""
    eps = sorted(sleeper.nightmare_epochs)
    minutes, wakings, codes = 0, 0, 0
    active_end = -1
    for i in eps:
        if i <= active_end:
            continue
        j = i
        while j in sleeper.nightmare_epochs:
            if sleeper.rng.u() < sensitivity:
                if plan["trauma"] == "wake":
                    wakings += 1
                    break
                codes += 1
                if sleeper.rng.u() < 0.6:
                    break
            minutes += 1
            j += 1
        while j in sleeper.nightmare_epochs:
            j += 1
        active_end = j
    return {"nightmares": len({i for i in eps if i - 1 not in sleeper.nightmare_epochs}), "minutes": _v(r1(minutes * EPOCH / 60)),
            "wakings": wakings, "safety_codes": codes}


# ---------------------------------------------------------------- REWARD

SUFFIXES = (".", "-", "..", ".-", "-.", "--", "...", "..-", ".-.", ".--", "-..", "-.-", "--.", "---")


def family(prefix: str, n: int) -> list:
    """n reward codes for one learning area: the area's prefix, then a distinct suffix."""
    if not prefix or any(ch not in ".-" for ch in prefix):
        raise ValueError("the prefix is dots and dashes")
    if n > len(SUFFIXES):
        raise ValueError("at most " + str(len(SUFFIXES)) + " codes in a family")
    return [prefix + " " + s for s in SUFFIXES[:n]]


def families_ok(areas: dict) -> list:
    """areas: {name: prefix}. Prefixes must differ and none may start another, so the body knows the area first."""
    out = []
    names = sorted(areas)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            x, y = areas[a], areas[b]
            if x == y:
                out.append(a + " and " + b + " share a prefix")
            elif x.startswith(y) or y.startswith(x):
                out.append(a + " and " + b + ": one prefix starts the other")
    return out


def reward_state(area: str, code: str) -> dict:
    return {"area": area, "code": code, "log": []}


def on_event(state: dict, ev: dict) -> dict:
    """ev: {t_ms, source, success, detect_ms}. Plays the reward code for a success within the refractory period and
    the per-minute limit. latency_ms: from the success to the code starting."""
    log = state["log"]
    if not ev.get("success"):
        d = {"t_ms": ev["t_ms"], "source": ev.get("source", "manual"), "play": False, "why": "not a success", "latency_ms": None}
        log.append(d)
        return d
    played = [e for e in log if e["play"]]
    if played and ev["t_ms"] - played[-1]["t_ms"] < REWARD["refractory_ms"]:
        why = "too soon after the last reward"
    elif sum(1 for e in played if ev["t_ms"] - e["t_ms"] < 60000) >= REWARD["per_minute"]:
        why = "the per-minute limit"
    else:
        why = None
    lat = (ev.get("detect_ms") or 0) + REWARD["device_ms"]
    d = {"t_ms": ev["t_ms"], "source": ev.get("source", "manual"), "play": why is None, "why": why, "latency_ms": lat if why is None else None,
         "code": state["code"] if why is None else None}
    log.append(d)
    return d


def reward_report(state: dict) -> dict:
    log = state["log"]
    succ = [e for e in log if e["why"] != "not a success"]
    played = [e for e in log if e["play"]]
    lat = [e["latency_ms"] for e in played]
    within = sum(1 for x in lat if x <= REWARD["budget_ms"])
    return {"successes": len(succ), "rewarded": len(played), "blocked": len(succ) - len(played),
            "median_ms": _v(r1(_median(lat))) if lat else None, "within": _v(r1(within / len(lat) * 100)) if lat else None,
            "say": ("No successes yet." if not succ else
                    f"{len(played)} of {len(succ)} successes rewarded; median {_v(r1(_median(lat))) if lat else '—'} ms from the success to the code, "
                    f"{_v(r1(within / len(lat) * 100)) if lat else 0}% within {REWARD['budget_ms']} ms.")}


# ---------------------------------------------------------------- recognising a good move

TEMPLATE_N = 32


def move_shape(t_ms: float, good=True) -> float:
    """Acceleration magnitude (g above rest) of a move at t_ms from its start. Good: a smooth wind-up at 150 ms, a
    sharp release at 300 ms and a follow-through at 420 ms. Poor: no wind-up, a slow release and a second push."""
    g = lambda z: math.exp(-z * z)
    if good:
        return 0.6 * g((t_ms - 150) / 48) + 2.2 * g((t_ms - 300) / 30) + 0.8 * g((t_ms - 420) / 42)
    return 0.15 * g((t_ms - 150) / 48) + 1.8 * g((t_ms - 300) / 50) + 1.2 * g((t_ms - 390) / 30)


def template(n=TEMPLATE_N) -> list:
    """The good move as the detector sees it: from 450 ms before the release peak to 150 ms after it."""
    return [move_shape(-150 + 600 * k / (n - 1)) for k in range(n)]


def _resample(xs, n):
    if len(xs) == n:
        return list(xs)
    out = []
    for k in range(n):
        p = k * (len(xs) - 1) / (n - 1)
        i = int(math.floor(p))
        f = p - i
        out.append(xs[i] if i + 1 >= len(xs) else xs[i] * (1 - f) + xs[i + 1] * f)
    return out


def _corr(a, b):
    ma, mb = _mean(a), _mean(b)
    sab = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    saa = sum((x - ma) * (x - ma) for x in a)
    sbb = sum((y - mb) * (y - mb) for y in b)
    return sab / math.sqrt(saa * sbb) if saa > 0 and sbb > 0 else 0.0


def detect_moves(samples: list, tmpl=None, hz=100, peak_g=1.5, match=0.85) -> list:
    """samples: acceleration magnitude in g above rest, at `hz`. A move is a peak above `peak_g` that stays the
    largest for 150 ms; the 600 ms ending 150 ms after it is compared with the template, and a correlation of `match`
    or more is a good move. The decision is made 150 ms after the peak (detect_ms)."""
    tmpl = tmpl or template()
    pre, post, back = int(0.45 * hz), int(0.15 * hz), int(0.3 * hz)
    out, i, n = [], pre, len(samples)
    while i < n - post:
        if samples[i] >= peak_g and samples[i] == max(samples[i - back:i + post + 1]):
            w = _resample(samples[i - pre:i + post], TEMPLATE_N)
            r = _corr(w, tmpl)
            out.append({"t_ms": _v(r1(i * 1000 / hz)), "peak": _v(r2(samples[i])), "r": _v(r2(r)), "success": r >= match, "detect_ms": _v(r1(post * 1000 / hz))})
            i += post + back
        else:
            i += 1
    return out


def sim_move(rng, good=True, hz=100, noise=0.15) -> list:
    """One second of rest, a 600 ms move (good or poor, scaled and noisy), one second of rest."""
    scale = 0.85 + 0.3 * rng.u()
    n = int(0.6 * hz)
    sig = [abs(rng.gauss() * noise * 0.3) for _ in range(hz)]
    sig += [move_shape(k * 1000 / hz, good) * scale + rng.gauss() * noise for k in range(n)]
    sig += [abs(rng.gauss() * noise * 0.3) for _ in range(hz)]
    return [max(0.0, x) for x in sig]


# ---------------------------------------------------------------- the notice test (light with vibration)

def notice_report(trials: list) -> dict:
    """trials: [{channel: "vibration" | "both", noticed: bool, latency_ms}]. Does adding light make a cue noticed more
    often, or sooner?"""
    out = {}
    for ch in ("vibration", "both"):
        xs = [t for t in trials if t["channel"] == ch]
        lat = [t["latency_ms"] for t in xs if t["noticed"] and t.get("latency_ms") is not None]
        out[ch] = {"n": len(xs), "noticed": _v(r1(sum(1 for t in xs if t["noticed"]) / len(xs) * 100)) if xs else None,
                   "median_ms": _v(r1(_median(lat))) if lat else None, "_lat": lat}
    a, b = out["both"]["_lat"], out["vibration"]["_lat"]
    for ch in out:
        del out[ch]["_lat"]
    if len(a) >= 3 and len(b) >= 3:
        d, lo, hi = _ci_diff(a, b)
        out["faster"] = {"difference_ms": _v(r1(d)), "lo": _v(r1(lo)), "hi": _v(r1(hi))}
        out["say"] = ("With light, cues were noticed sooner" if hi < 0 else "With light, cues were noticed later" if lo > 0
                      else "No clear difference in how fast cues were noticed") + f": {_v(r1(d))} ms [{_v(r1(lo))}, {_v(r1(hi))}]."
    else:
        out["faster"] = None
        out["say"] = "Run at least three trials of each kind."
    return out


# ---------------------------------------------------------------- simulation with known answers

def _policy_night(seed, kind, arousability=1.0, acc=None):
    s = Sleeper(seed, arousability=arousability, acc=acc)
    plan = make_plan([{"code": "..-", "label": "today"}])
    return s.run(Controller(plan, kind) if kind != "none" else None)


def _memory(rng, good, arousals, benefit, items=20):
    """Evening recall is the same for both sets; overnight, uncued items lose 12 points of retention on average and
    cued items lose less by `benefit` times the share of reactivation reached, and more by benefit / 6 with each
    cue-caused arousal (no benefit, no harm)."""
    gain = benefit * (1 - math.exp(-good / 40.0)) - benefit / 6 * arousals
    before = items
    keep_u = max(0.0, min(1.0, 0.88 + rng.gauss() * 0.03))
    keep_c = max(0.0, min(1.0, keep_u + gain))
    after_u = sum(1 for _ in range(before) if rng.u() < keep_u)
    after_c = sum(1 for _ in range(before) if rng.u() < keep_c)
    return {"cued_before": before, "cued_after": after_c, "uncued_before": before, "uncued_after": after_u}


def _tmr_person(seed, benefit, nights=7, kind="closed"):
    rng, rows = P.Rng(seed * 3 + 7), []
    for k in range(nights):
        out = _policy_night(seed * 100 + k, kind)
        rows.append(_memory(rng, out["report"]["good"], out["report"]["arousals"], benefit))
    return tmr_analyze(rows)


def _training(seed, n, reward, replay):
    """A 2 x 2 study: each athlete gets reward codes or not, night replay or not; accuracy over 50 test shots after
    four weeks, from a 40% start with a personal learning rate. Returns the main effects with intervals."""
    rng = P.Rng(seed)
    arms = {(a, b): [] for a in (0, 1) for b in (0, 1)}
    for i in range(n):
        a, b = (i % 2, (i // 2) % 2)
        p = 0.40 + 0.06 + rng.gauss() * 0.04 + a * reward + b * replay
        p = max(0.05, min(0.95, p))
        arms[(a, b)].append(sum(1 for _ in range(50) if rng.u() < p) / 50 * 100)
    ra = arms[(1, 0)] + arms[(1, 1)]
    r0 = arms[(0, 0)] + arms[(0, 1)]
    na = arms[(0, 1)] + arms[(1, 1)]
    n0 = arms[(0, 0)] + arms[(1, 0)]
    return _ci_diff(ra, r0), _ci_diff(na, n0)


def _moves(seed, n=40):
    rng = P.Rng(seed)
    tp = fp = fn = tn = 0
    for k in range(n):
        good = k % 2 == 0
        ev = detect_moves(sim_move(rng, good))
        hit = any(e["success"] for e in ev)
        if good:
            tp, fn = tp + hit, fn + (not hit)
        else:
            fp, tn = fp + hit, tn + (not hit)
    return tp, fn, fp, tn


def evaluate(n=60) -> dict:
    res = {}
    base = [_policy_night(9000 + i, "none")["report"] for i in range(n)]
    for kind in ("closed", "random"):
        rows = [_policy_night(9000 + i, kind)["report"] for i in range(n)]
        res[("policy", kind)] = {"cues": _v(r1(_mean([r["cues"] for r in rows]))), "in_n3": _v(r1(_mean([r["in_n3"] or 0 for r in rows]))),
                                 "arousals": _v(r1(_mean([r["arousals"] for r in rows]))),
                                 "waso": _v(r1(_mean([r["waso_min"] - b["waso_min"] for r, b in zip(rows, base)]))),
                                 "n3_lost": _v(r1(_mean([b["n3_min"] - r["n3_min"] for r, b in zip(rows, base)]))),
                                 "good": _v(r1(_mean([r["good"] for r in rows])))}
    rows = [_policy_night(9000 + i, "closed", acc={"W": 0.8, "N1": 0.3, "N2": 0.65, "N3": 0.6, "REM": 0.6})["report"] for i in range(n)]
    res[("policy", "closed_poor")] = {"cues": _v(r1(_mean([r["cues"] for r in rows]))), "in_n3": _v(r1(_mean([r["in_n3"] or 0 for r in rows]))),
                                      "arousals": _v(r1(_mean([r["arousals"] for r in rows]))),
                                      "waso": _v(r1(_mean([r["waso_min"] - b["waso_min"] for r, b in zip(rows, base)]))),
                                      "n3_lost": _v(r1(_mean([b["n3_min"] - r["n3_min"] for r, b in zip(rows, base)]))),
                                      "good": _v(r1(_mean([r["good"] for r in rows])))}
    for benefit, kind in ((0.06, "closed"), (0.0, "closed"), (0.06, "random")):
        vs = [_tmr_person(i + 1, benefit, 7, kind) for i in range(n)]
        groups = []
        for g in range(n // 3):
            adv = [_tmr_person(500 + g * 20 + k, benefit, 7, kind)["advantage"] for k in range(20)]
            m, lo, hi = _ci(adv)
            groups.append("helps" if lo > 0 else "hurts" if hi < 0 else "unclear")
        res[("tmr", benefit, kind)] = {"helps": _v(r1(sum(1 for v in vs if v["verdict"] == "helps") / n * 100)),
                                       "hurts": _v(r1(sum(1 for v in vs if v["verdict"] == "hurts") / n * 100)),
                                       "mean": _v(r1(_mean([v["advantage"] for v in vs]))),
                                       "group_helps": _v(r1(groups.count("helps") / len(groups) * 100)),
                                       "group_hurts": _v(r1(groups.count("hurts") / len(groups) * 100))}
    for (rw, rp), name in (((0.04, 0.02), "both"), ((0.0, 0.0), "none")):
        for size in (40, 80):
            hits_r = hits_n = 0
            for i in range(n):
                (dr, lr, hr), (dn, ln, hn) = _training(11000 + i, size, rw, rp)
                hits_r += lr > 0
                hits_n += ln > 0
            res[("train", name, size)] = {"reward": _v(r1(hits_r / n * 100)), "replay": _v(r1(hits_n / n * 100))}
    tp = fn = fp = tn = 0
    for i in range(n):
        a, b, c, d = _moves(12000 + i, 10)
        tp, fn, fp, tn = tp + a, fn + b, fp + c, tn + d
    res["moves"] = {"sensitivity": _v(r1(tp / (tp + fn) * 100)), "false": _v(r1(fp / (fp + tn) * 100)), "detect_ms": 150 + REWARD["device_ms"]}
    for mode in TRAUMA_MODES:
        rows = []
        for i in range(n):
            s = Sleeper(13000 + i, nightmares=1.0)
            rows.append(nightmare_response(make_plan([], trauma=mode), s))
        none = []
        for i in range(n):
            s = Sleeper(13000 + i, nightmares=1.0)
            none.append(sum(1 for _ in s.nightmare_epochs) * EPOCH / 60)
        res[("nightmare", mode)] = {"minutes": _v(r1(_mean([r["minutes"] for r in rows]))), "untreated": _v(r1(_mean(none))),
                                    "wakings": _v(r1(_mean([r["wakings"] for r in rows])))}
    return {"n": n, "res": res}


def report(ev: dict) -> str:
    R, n = ev["res"], ev["n"]
    L = ["# SLEEP and REWARD on simulated people", "",
         f"Generated by `python -m rsso.night --evaluate`. {n} simulated people per row. Built and tested in simulation; effect unproven in people.", "",
         "## Cueing during sleep (claims C8, C36)", "",
         "An 8-hour night of 30-second epochs with sleep cycles. The device reads the stage correctly 80% of the time in deep sleep (N3) "
         "and 40% in N1; a cue can wake the sleeper, more often in light sleep and at higher intensity. Closed loop: cue only after 90 seconds "
         "of N3 as read by the device, start low, lower the intensity after an arousal and pause five minutes, at most 300 cues. Random: a cue "
         "in a quarter of all epochs at the highest allowed intensity. Differences are against the same person's night with no cues.", "",
         "| Policy | Cues | In deep sleep | Arousals caused | Extra time awake (min) | Deep sleep lost (min) | Cues that reached N2 or N3 without waking |",
         "|---|---|---|---|---|---|---|"]
    for k, name in (("closed", "Closed loop"), ("closed_poor", "Closed loop, poorer device (N3 read right 60%)"), ("random", "Random")):
        x = R[("policy", k)]
        L.append(f"| {name} | {x['cues']} | {x['in_n3']}% | {x['arousals']} | {x['waso']} | {x['n3_lost']} | {x['good']} |")
    L += ["", "## Next-day recall, cued against uncued items (claims C7, C8)", "",
          "Twenty items cued and twenty not, recalled in the evening and the next morning, over seven nights per person. Where cueing helps, "
          "cued items lose up to 6 points less retention overnight, in proportion to the cues that reached N2 or N3 without waking, and each "
          "cue-caused arousal costs a sixth of that.", "",
          "| Truth | Policy | One person: called helps | One person: called hurts | Mean advantage (points) | Group of 20: called helps | Group of 20: called hurts |", "|---|---|---|---|---|---|---|"]
    for (b, k), name in (((0.06, "closed"), "Helps"), ((0.0, "closed"), "No effect"), ((0.06, "random"), "Helps")):
        x = R[("tmr", b, k)]
        L.append(f"| {name} | {'Closed loop' if k == 'closed' else 'Random'} | {x['helps']}% | {x['hurts']}% | {x['mean']} | {x['group_helps']}% | {x['group_hurts']}% |")
    L += ["", "## Nightmares (claims C5, C33)", "",
          "One nightmare a night on average, in REM, detected from a heart-rate surge in 80% of its epochs. The trauma-related code itself is never played.", "",
          "| Response | Nightmare minutes | Without response | Wakings |", "|---|---|---|---|"]
    for mode, name in (("safety", "Safety code"), ("wake", "Gentle waking")):
        x = R[("nightmare", mode)]
        L.append(f"| {name} | {x['minutes']} | {x['untreated']} | {x['wakings']} |")
    L += ["", "## Reward codes in training (claims C9, C28)", "",
          "A 2 x 2 study over four weeks: reward codes on success or not, night replay or not; accuracy over 50 test shots. Where they work, "
          "reward codes add 4 points and night replay 2 points.", "",
          "| Truth | Athletes | Reward effect found | Night-replay effect found |", "|---|---|---|---|"]
    for name, label in (("both", "Both work"), ("none", "Neither works")):
        for size in (40, 80):
            x = R[("train", name, size)]
            L.append(f"| {label} | {size} | {x['reward']}% | {x['replay']}% |")
    x = R["moves"]
    t = R[("tmr", 0.06, "closed")]
    w = R[("train", "both", 80)]
    L += ["", f"A good move recognised from a wrist accelerometer by its shape: {x['sensitivity']}% of good moves, {x['false']}% of poor ones; the decision "
          f"is made 150 ms after the release, so the reward code starts about {x['detect_ms']} ms after it, within the 300 ms aim.", "",
          "Reading: closed-loop cueing puts nearly every cue in deep sleep and rarely wakes the sleeper; random cueing at the allowed strength "
          "wakes them many times a night, adds time awake, and in the memory model turns a benefit into a loss (claim C36). A memory benefit of "
          f"this size is found in {t['helps']}% of single people over a week of nights, and in {t['group_helps']}% of groups of 20: it is a group "
          f"question. Reward codes and night replay are small effects: with 80 athletes the reward effect is found in {w['reward']}% of studies "
          f"and the replay effect in {w['replay']}%.", ""]
    return "\n".join(L)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["--evaluate"]:
        import pathlib
        path = pathlib.Path(__file__).resolve().parents[1] / "results" / "night.md"
        path.write_text(report(evaluate()), encoding="utf-8")
        print(f"wrote {path}")
        return 0
    print("usage: python -m rsso.night --evaluate")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
