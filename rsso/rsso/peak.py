"""PEAK — anchors as measured objects (spec/PEAK.md).

An anchor is a stored pairing between a cue and a state: its channels (vibration code, scent, light, phrase,
glyph), its role in a chain, the body signature recorded when it was captured, and its measured strength.
Strength comes from probe trials: the cue played alone, with the body's response measured before and after,
compared with sham probes (a code never paired with the state). docs/js/peak.js is identical (tested).

  ROLES, ROLE_ORDER            healing, stability, redirection, lock-in
  make_anchor(...)             a new anchor
  composite(a, b)              two symbols held as one anchor (the form of Tier 013, the lion and the dragon)
  capture_check(sample, base)  whether a moment counts as a peak, and the signature to store
  add_capture / add_probe / add_use
  probe_effect(probe, metric)  one probe's effect: RMSSD change in %, heart-rate fall in bpm, or calm change
  choose_metric(probes)        the measure with enough probes
  strength(anchor)             effect of the cue against sham, with a 95% interval and a status
  contamination(anchor)        whether the anchor is taking on stress, and why
  restoration_plan(anchor, resource)   how to restore a contaminated anchor
  chain(anchors) / chain_rsx(anchors)  anchors in role order, and the chain as an RSX program
  chain_report(phases)         which phases of a played chain worked
  SimBody                      a simulated body with known anchor strengths (seeded; identical in JavaScript)
  evaluate(...)                how well strength and contamination are recovered from simulated probes

Numbers are rounded half up (identical in JavaScript). Times are seconds.
"""
from __future__ import annotations

import json
import math
import re
import sys

ROLES = ("healing", "stability", "redirection", "lockin")
ROLE_ORDER = {r: k for k, r in enumerate(ROLES)}
ROLE_NAMES = {"healing": "Healing", "stability": "Stability", "redirection": "Redirection", "lockin": "Lock-in"}
METRICS = ("rmssd_pct", "hr_delta", "calm")
METRIC_NAMES = {"rmssd_pct": "heart rate variability (RMSSD), % change", "hr_delta": "heart rate fall, bpm",
                "calm": "calm rating change, 0-10"}
THRESHOLD = {"rmssd_pct": 5.0, "hr_delta": 2.0, "calm": 1.0}     # the smallest effect that counts
WINDOW = 8                                                       # recent probes used for strength
CODE_RE = re.compile(r"[.\-]{1,6}( [.\-]{1,6}){0,2}")
# two-sided 95% t critical values, df 1..30; above 30 use 1.96
T95 = [12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228, 2.201, 2.179, 2.160, 2.145, 2.131,
       2.120, 2.110, 2.101, 2.093, 2.086, 2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045, 2.042]


def r1(x):
    return None if x is None else math.floor(x * 10 + 0.5) / 10


def r2(x):
    return None if x is None else math.floor(x * 100 + 0.5) / 100


def _v(x):
    return int(x) if isinstance(x, float) and x.is_integer() else x


def tcrit(df: int) -> float:
    return T95[df - 1] if 1 <= df <= 30 else 1.96


def _num(v):
    if v is None or v == "" or isinstance(v, bool):
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _mean(xs):
    return sum(xs) / len(xs)


def _var(xs):
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    return sum((x - m) * (x - m) for x in xs) / (len(xs) - 1)


def _slope(ys):
    n = len(ys)
    if n < 2:
        return 0.0
    mx = (n - 1) / 2
    my = _mean(ys)
    num = sum((k - mx) * (y - my) for k, y in enumerate(ys))
    den = sum((k - mx) * (k - mx) for k in range(n))
    return num / den


# ---------------------------------------------------------------- the anchor object

def make_anchor(id, name, glyph, code, role="stability", scent=None, light=None, phrase=None, created=0):
    if role not in ROLES:
        raise ValueError(f"role must be one of {', '.join(ROLES)}")
    if not CODE_RE.fullmatch(code or ""):
        raise ValueError('code is 1 to 6 dots and dashes, up to three joined by spaces, e.g. "..-"')
    return {"schema": "rsos-anchor/1", "id": id, "name": name, "glyph": glyph, "code": code, "role": role,
            "channels": {"vibration": code, "scent": scent, "light": light, "phrase": phrase, "glyph": glyph},
            "parts": [], "created": created, "captures": [], "probes": [], "uses": []}


def composite(a: dict, b: dict, id=None, role=None, created=0):
    """Two anchors held as one: glyphs joined with +, codes joined with a pause (as Tier 013, the lion and the dragon)."""
    code = a["code"] + " " + b["code"]
    if not CODE_RE.fullmatch(code):
        raise ValueError("the joined code is too long; use shorter codes")
    pick = lambda k: a["channels"].get(k) or b["channels"].get(k)   # noqa: E731
    out = make_anchor(id or (a["id"] + "+" + b["id"]), a["name"] + " + " + b["name"], a["glyph"] + " + " + b["glyph"], code,
                      role or a["role"], pick("scent"), pick("light"),
                      " ".join(p for p in (a["channels"].get("phrase"), b["channels"].get("phrase")) if p) or None, created)
    out["parts"] = [a["id"], b["id"]]
    return out


def capture_check(sample: dict, baseline: dict | None = None) -> dict:
    """Does this moment count as a peak? A self-tap always does; a measured peak needs HRV up 15% over baseline
    without heart rate up more than 10 bpm, or EEG alpha+theta up 20%."""
    baseline = baseline or {}
    src = sample.get("source", "self_tap")
    sig = {k: _v(r1(_num(sample.get(k)))) for k in ("hr", "rmssd", "alpha_theta", "intensity") if _num(sample.get(k)) is not None}
    if src == "self_tap":
        return {"ok": True, "source": src, "reason": "marked by the person", "signature": sig}
    if src == "hrv":
        rm, b_rm = _num(sample.get("rmssd")), _num(baseline.get("rmssd"))
        hr, b_hr = _num(sample.get("hr")), _num(baseline.get("hr"))
        if rm is None or not b_rm:
            return {"ok": False, "source": src, "reason": "needs RMSSD now and at baseline", "signature": sig}
        up = (rm - b_rm) / b_rm * 100
        sig["rmssd_up_pct"] = _v(r1(up))
        if hr is not None and b_hr is not None and hr - b_hr > 10:
            return {"ok": False, "source": src, "reason": "heart rate rose more than 10 bpm (likely movement or effort)", "signature": sig}
        ok = up >= 15
        return {"ok": ok, "source": src, "reason": ("HRV " + ("up " if ok else "only up ") + _fmt(r1(up)) + "% over baseline"), "signature": sig}
    if src == "eeg":
        at, b_at = _num(sample.get("alpha_theta")), _num(baseline.get("alpha_theta"))
        if at is None or not b_at:
            return {"ok": False, "source": src, "reason": "needs alpha+theta power now and at baseline", "signature": sig}
        up = (at - b_at) / b_at * 100
        sig["alpha_theta_up_pct"] = _v(r1(up))
        ok = up >= 20
        return {"ok": ok, "source": src, "reason": ("alpha+theta " + ("up " if ok else "only up ") + _fmt(r1(up)) + "%"), "signature": sig}
    return {"ok": False, "source": src, "reason": "unknown source", "signature": sig}


def _fmt(x):
    k = math.floor(abs(x) * 10 + 0.5)
    return ("-" if x < 0 and k else "") + f"{k // 10}.{k % 10}"


def add_capture(anchor, sample, baseline=None, ts=0):
    c = capture_check(sample, baseline)
    if c["ok"]:
        anchor["captures"].append({"ts": ts, "source": c["source"], "signature": c["signature"]})
    return c


def add_probe(anchor, probe):
    """probe: {ts, kind: "cue"|"sham", hr_before, hr_after, rmssd_before, rmssd_after, calm_before, calm_after}"""
    p = {"ts": probe.get("ts", 0), "kind": probe.get("kind", "cue")}
    for k in ("hr_before", "hr_after", "rmssd_before", "rmssd_after", "calm_before", "calm_after"):
        x = _num(probe.get(k))
        if x is not None:
            p[k] = _v(r1(x))
    anchor["probes"].append(p)
    return p


def add_use(anchor, ts=0, during_stress=False):
    anchor["uses"].append({"ts": ts, "during_stress": bool(during_stress)})


# ---------------------------------------------------------------- strength

def probe_effect(p: dict, metric: str):
    if metric == "rmssd_pct":
        b, a = _num(p.get("rmssd_before")), _num(p.get("rmssd_after"))
        return None if b is None or a is None or b <= 0 else (a - b) / b * 100
    if metric == "hr_delta":
        b, a = _num(p.get("hr_before")), _num(p.get("hr_after"))
        return None if b is None or a is None else b - a
    b, a = _num(p.get("calm_before")), _num(p.get("calm_after"))
    return None if b is None or a is None else a - b


def choose_metric(probes):
    best, most = "calm", -1
    for m in METRICS:
        n = sum(1 for p in probes if p.get("kind") == "cue" and probe_effect(p, m) is not None)
        if n >= 3:
            return m
        if n > most:
            best, most = m, n
    return best


def strength(anchor: dict, window: int = WINDOW) -> dict:
    probes = sorted(anchor.get("probes", []), key=lambda p: p.get("ts", 0))
    metric = choose_metric(probes)
    thr = THRESHOLD[metric]
    cue = [e for e in (probe_effect(p, metric) for p in probes if p.get("kind") == "cue") if e is not None][-window:]
    sham = [e for e in (probe_effect(p, metric) for p in probes if p.get("kind") == "sham") if e is not None][-window:]
    out = {"metric": metric, "metric_name": METRIC_NAMES[metric], "threshold": _v(thr), "n_cue": len(cue), "n_sham": len(sham),
           "effects": [_v(r1(e)) for e in cue], "estimate": None, "lo": None, "hi": None, "trend": 0, "status": "building",
           "against": "sham" if len(sham) >= 3 else "zero"}
    if not cue:
        out["say"] = "No probes yet. Run a probe after a few captures."
        return out
    if len(sham) >= 3:
        est = _mean(cue) - _mean(sham)
        va, vs = _var(cue) / len(cue), _var(sham) / len(sham)
        se = math.sqrt(va + vs)
        den = (va * va / (len(cue) - 1) if len(cue) > 1 else 0) + vs * vs / (len(sham) - 1)
        df = math.floor((va + vs) * (va + vs) / den) if den > 0 else min(len(cue), len(sham)) - 1   # Welch
    else:
        est = _mean(cue)
        se = math.sqrt(_var(cue) / len(cue))
        df = len(cue) - 1
    out["estimate"] = _v(r1(est))
    if len(cue) >= 2:
        half = tcrit(max(df, 1)) * se
        out["lo"], out["hi"] = _v(r1(est - half)), _v(r1(est + half))
    tr = _slope(cue[-6:]) if len(cue) >= 4 else 0.0
    out["trend"] = _v(r2(tr))
    lo, hi = (est - tcrit(max(df, 1)) * se, est + tcrit(max(df, 1)) * se) if len(cue) >= 2 else (None, None)
    if len(cue) < 3:
        st, say = "building", "Too few probes to judge. Three or more give an answer."
    elif hi < 0:
        st, say = "contaminated", "The cue now makes things worse than no cue. Restore it before using it again."
    elif tr <= -thr / 2 and _mean(cue[-3:]) < _mean(cue[:-3] or cue) - thr / 2:
        st, say = "weakening", "The effect is falling with each probe. Re-pair it at a peak, and use it less outside practice."
    elif lo > 0 and est >= thr:
        st, say = "strong", "The cue alone changes the body, clearly more than " + ("a sham cue." if len(sham) >= 3 else "nothing.")
    elif lo > 0:
        st, say = "present", "There is an effect, but smaller than the threshold. Keep pairing it at peaks."
    else:
        st, say = "unclear", "No clear effect yet. Keep pairing at peaks and probing."
    out["status"], out["say"] = st, say
    return out


def contamination(anchor: dict, now=None) -> dict:
    s = strength(anchor)
    metric, thr = s["metric"], THRESHOLD[s["metric"]]
    cue = [e for e in (probe_effect(p, metric) for p in sorted(anchor.get("probes", []), key=lambda p: p.get("ts", 0))
                       if p.get("kind") == "cue") if e is not None]
    uses = sorted(anchor.get("uses", []), key=lambda u: u.get("ts", 0))[-10:]
    stress_share = sum(1 for u in uses if u.get("during_stress")) / len(uses) if uses else 0.0
    reasons, risk = [], "low"
    if s["status"] == "contaminated":
        reasons.append("the cue alone now makes things worse than no cue")
        risk = "high"
    elif len(cue) >= 3 and _mean(cue[-3:]) < -thr:
        reasons.append("the last three probes were negative")
        risk = "high"
    if len(uses) >= 4 and stress_share >= 0.5:
        reasons.append(f"used during stress in {_v(r1(stress_share * 100))}% of recent uses")
        if risk == "low":
            risk = "medium" if (s["trend"] or 0) <= -thr / 4 or s["status"] in ("weakening", "unclear") else "low"
    return {"contaminated": risk == "high", "risk": risk, "reasons": reasons, "stress_share": _v(r1(stress_share * 100)),
            "status": s["status"]}


def restoration_plan(anchor: dict, resource: dict | None = None) -> dict:
    c = contamination(anchor)
    with_ = resource["name"] if resource else "a higher-order resource state"
    steps = [
        "Pause automatic use of " + anchor["name"] + " (the autonomy gate keeps it manual until restored).",
        "Do not use it during stress for now: use another anchor, or none.",
        "Re-pair it in calm, at a measured peak, together with " + with_ + ", for at least 5 sessions.",
        "Run probes after the re-pairing: it is restored after 3 positive probes in a row with the interval above zero.",
    ]
    if resource:
        steps.insert(3, "Consider holding both as one anchor: " + anchor["glyph"] + " + " + resource["glyph"] + ".")
    return {"anchor": anchor["id"], "needed": c["risk"] != "low", "risk": c["risk"], "reasons": c["reasons"], "steps": steps,
            "resource": resource["id"] if resource else None, "restored_when": "3 positive probes in a row, interval above zero"}


# ---------------------------------------------------------------- chains

def chain(anchors: list[dict]) -> list[dict]:
    phases = []
    for a in sorted(anchors, key=lambda a: (ROLE_ORDER[a["role"]], a["id"])):
        phases.append({"anchor": a["id"], "role": a["role"], "role_name": ROLE_NAMES[a["role"]], "glyph": a["glyph"],
                       "code": a["code"], "scent": a["channels"].get("scent"), "light": a["channels"].get("light"),
                       "phrase": a["channels"].get("phrase"), "check": "Did this phase do its job? (calm 0-10 after it)"})
    return phases


def _q(s):
    return '"' + str(s).replace('"', "'") + '"'


def chain_rsx(anchors: list[dict], name="anchor_chain") -> str:
    """The chain as an RSX program: each anchor a tier with its code, each role a phase that activates it."""
    lines = [f"PROTOCOL {name} \"Anchor chain\"", "VERSION 1.0", "SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4", ""]
    ph = chain(anchors)
    for k, p in enumerate(ph):
        tname = "a" + str(k + 1)
        lines += [f"TIER {k + 1} {tname} {{",
                  f"  GLYPH {_q(p['glyph'])}",
                  f"  V {_q('see ' + (p['light'] or 'the light') + ' around ' + p['glyph'])}",
                  f"  A {_q(p['phrase'] or p['role_name'])}",
                  f"  K {_q('feel the code ' + p['code'])}"]
        if p["scent"]:
            lines.append(f"  O {_q(p['scent'])}")
        lines += [f"  TACTON {_q(p['code'])}", "}"]
    lines.append("")
    for k, p in enumerate(ph):
        lines += [f"PHASE {p['role']}{k + 1} dur=8s {{", f"  ACTIVATE a{k + 1}", f"  MARK {_q('check ' + p['role'])}", "}"]
    return "\n".join(lines) + "\n"


def chain_report(results: list[dict]) -> dict:
    """results: [{role, calm_before, calm_after}] for each played phase."""
    out, worked = [], 0
    for r in results:
        b, a = _num(r.get("calm_before")), _num(r.get("calm_after"))
        d = None if b is None or a is None else a - b
        ok = d is not None and d >= 1
        worked += 1 if ok else 0
        out.append({"role": r.get("role"), "change": _v(r1(d)) if d is not None else None, "worked": ok})
    weakest = min((x for x in out if x["change"] is not None), key=lambda x: x["change"], default=None)
    return {"phases": out, "worked": worked, "of": len(out), "weakest": weakest["role"] if weakest and not weakest["worked"] else None}


# ---------------------------------------------------------------- simulated body

class Rng:
    """Linear congruential generator, identical in JavaScript (integer arithmetic below 2^53)."""

    def __init__(self, seed: int):
        self.x = seed % 4294967296

    def u(self) -> float:
        self.x = (1664525 * self.x + 1013904223) % 4294967296
        return self.x / 4294967296

    def gauss(self) -> float:
        s = 0.0
        for _ in range(12):
            s += self.u()
        return s - 6.0


class SimBody:
    """A simulated person with known anchor strengths. Pairings at peaks raise strength toward `ceiling`
    (Rescorla-Wagner), days without practice let it fade, uses during stress pull it toward `stress_pull`
    (contamination). Probes measure RMSSD before and after with noise; sham probes measure noise and a small
    placebo effect. Strength is in % change of RMSSD."""

    def __init__(self, seed=1, ceiling=20.0, alpha=0.3, fade=0.98, beta=0.25, stress_pull=-15.0, noise=4.0, placebo=1.0):
        self.rng = Rng(seed)
        self.ceiling, self.alpha, self.fade, self.beta = ceiling, alpha, fade, beta
        self.stress_pull, self.noise, self.placebo = stress_pull, noise, placebo
        self.v = 0.0
        self.t = 0

    def pair(self):
        self.v += self.alpha * (self.ceiling - self.v)

    def wait(self, days):
        for _ in range(days):
            self.v *= self.fade
        self.t += days * 86400

    def stress_use(self):
        self.v += self.beta * (self.stress_pull - self.v)

    def probe(self, kind="cue"):
        self.t += 600
        before = 40.0 + 6.0 * self.rng.gauss()
        eff = (self.v if kind == "cue" else self.placebo) + self.noise * self.rng.gauss()
        after = before * (1 + eff / 100)
        hb = 72.0 + 4.0 * self.rng.gauss()
        ha = hb - eff / 10
        return {"ts": self.t, "kind": kind, "rmssd_before": r1(before), "rmssd_after": r1(after), "hr_before": r1(hb), "hr_after": r1(ha)}


def scenario(kind: str, seed: int, probes=8, shams=4) -> dict:
    """A simulated anchor of a known kind: strong, weak, none or contaminated. Returns the anchor and its truth."""
    b = SimBody(seed=seed, ceiling={"strong": 22.0, "weak": 4.0, "none": 0.0, "contaminated": 22.0}[kind])
    a = make_anchor("sim" + str(seed), "Simulated " + kind, "🦁", "..-", "redirection")
    for _ in range(8):
        b.pair()
        add_capture(a, {"source": "self_tap", "intensity": 8}, None, b.t)
        b.wait(1)
    total = probes + shams
    order = ["sham" if (k + 1) * shams // total > k * shams // total else "cue" for k in range(total)]
    for k, kd in enumerate(order):
        if kind == "contaminated" and k >= 2 and kd == "cue":
            for _ in range(3):
                b.stress_use()
                add_use(a, b.t, True)
        add_probe(a, b.probe(kd))
        b.wait(1)
    return {"anchor": a, "truth": kind, "true_strength": _v(r1(b.v))}


def evaluate(n_each=50, probes=8, shams=4) -> dict:
    kinds = ("strong", "weak", "none", "contaminated")
    rows, errs, flags = {k: {} for k in kinds}, [], {"tp": 0, "fn": 0, "fp": 0, "tn": 0}
    for ki, kind in enumerate(kinds):
        for i in range(n_each):
            sc = scenario(kind, 1000 * (ki + 1) + i, probes, shams)
            s = strength(sc["anchor"])
            rows[kind][s["status"]] = rows[kind].get(s["status"], 0) + 1
            c = contamination(sc["anchor"])
            if kind == "contaminated":
                flags["tp" if c["contaminated"] else "fn"] += 1
            else:
                flags["fp" if c["contaminated"] else "tn"] += 1
            if kind != "contaminated" and s["estimate"] is not None:
                errs.append(abs(s["estimate"] - sc["true_strength"]))
    sens = flags["tp"] / (flags["tp"] + flags["fn"])
    spec = flags["tn"] / (flags["tn"] + flags["fp"])
    strong_ok = rows["strong"].get("strong", 0) / n_each
    none_false = sum(v for k, v in rows["none"].items() if k in ("strong", "present")) / n_each
    return {"n_each": n_each, "probes": probes, "shams": shams, "status_by_truth": rows,
            "contamination_sensitivity": r1(sens * 100), "contamination_specificity": r1(spec * 100),
            "strong_found": r1(strong_ok * 100), "none_called_effect": r1(none_false * 100),
            "mean_abs_error": r1(_mean(errs)) if errs else None}


def report(ev_by_probes: dict, camera: list | None = None) -> str:
    L = ["# PEAK: recovering known anchor strengths (simulation)", "",
         "Generated by `python -m rsso.peak --evaluate`. Simulated people with known anchors (strong, weak, none, "
         "contaminated by use during stress), measured with probe trials: the cue alone against sham cues, RMSSD before "
         "and after, with realistic noise. Built and tested in simulation; effect unproven in people.", "",
         "| Probes (cue + sham) | Strong found | No-effect anchors called an effect | Contamination flagged (sensitivity) | Healthy anchors flagged (1 - specificity) | Mean error of strength, % RMSSD |",
         "|---|---|---|---|---|---|"]
    for p, ev in ev_by_probes.items():
        L.append(f"| {p} + {ev['shams']} | {ev['strong_found']}% | {ev['none_called_effect']}% | {ev['contamination_sensitivity']}% | "
                 f"{r1(100 - ev['contamination_specificity'])}% | {ev['mean_abs_error']} |")
    L += ["", "Status given, by true kind (8 cue and 4 sham probes, 50 simulated anchors each). The contamination flag, not the status, is what catches contaminated anchors: their recent probes turn negative while older ones still pull the average up:", "",
          "| True kind | " + " | ".join(("strong", "present", "unclear", "weakening", "contaminated", "building")) + " |",
          "|---|---|---|---|---|---|---|"]
    ev = ev_by_probes[8]
    for kind, row in ev["status_by_truth"].items():
        L.append(f"| {kind} | " + " | ".join(str(row.get(s, 0)) for s in ("strong", "present", "unclear", "weakening", "contaminated", "building")) + " |")
    L += ["", "Reading: with eight cue probes and four sham probes, a strong anchor is recognised, an anchor with no effect is "
          "rarely mistaken for one, and an anchor pulled negative by use during stress is flagged. Real people add sources "
          "of variance the simulation lacks (posture, breathing, time of day); the protocol kit (spec/kits/PEAK_PROTOCOL_KIT.md) "
          "measures them.", ""]
    if camera:
        L += ["## Heart rate from the phone camera (simulation)", "",
              "Synthetic fingertip signals at 30 frames a second with known beats, analysed by `rsso/ppg.py` (identical to "
              "`docs/js/ppg.js`). Heart rate is read reliably; RMSSD is approximate at 30 frames a second, so it is used only "
              "when the reading is very clean (\"RMSSD usable\"), and otherwise probes fall back to the heart-rate fall.", "",
              "| Heart rate | Noise | Read | True RMSSD, ms | Read RMSSD, ms | Quality | Reading usable | RMSSD usable |", "|---|---|---|---|---|---|---|---|"]
        for r in camera:
            L.append(f"| {r['true_hr']} | {r['noise']} | {r['hr']} | {r['true_rmssd']} | {r['rmssd']} | {r['quality']}% | "
                     f"{'yes' if r['ok'] else 'no'} | {'yes' if r['rmssd_ok'] else 'no'} |")
        L.append("")
    return "\n".join(L)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["--evaluate"]:
        out = {p: evaluate(probes=p) for p in (4, 8, 12)}
        import pathlib
        from . import ppg
        path = pathlib.Path(__file__).resolve().parents[1] / "results" / "peak.md"
        path.write_text(report(out, ppg.accuracy()), encoding="utf-8")
        print(f"wrote {path}")
        return 0
    if argv[:1] == ["analyze"] and len(argv) == 2:
        data = json.loads(open(argv[1], encoding="utf-8").read())
        anchors = data["anchors"] if isinstance(data, dict) and "anchors" in data else [data]
        for a in anchors:
            s, c = strength(a), contamination(a)
            print(f"{a['name']}: {s['status']}, {s['metric_name']} {s['estimate']} [{s['lo']}, {s['hi']}] "
                  f"from {s['n_cue']} cue and {s['n_sham']} sham probes; contamination risk {c['risk']}"
                  + (" (" + "; ".join(c["reasons"]) + ")" if c["reasons"] else ""))
        return 0
    print("usage: python -m rsso.peak --evaluate | analyze <anchors.json>")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
