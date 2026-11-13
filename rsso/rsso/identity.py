"""IDENTITY: identity profiles, level by level (spec/IDENTITY.md).

A profile is headed by a symbol and a login code and holds a tree of seven levels: mission, identity, values,
beliefs, skills, behaviour and environment. Each level has a statement, an image and its own vibration code. The
profile also holds its environment (clothing, scent, music, the practice space), a language, a policy, an anchor
tree (a central image with contexts fixed to its parts), versions with what changed, and the measures that make an
identity testable:

  coherence      how true each level feels now (0-10), combined into one score; its trend over months
  drift          coherence after mirroring other people, against the person's baseline
  generalisation does the behaviour start in contexts that were never trained
  recall walks   the anchor tree walked part by part, timed, against a single image
  rehearsals     a value conflict imagined, the body's reaction measured, the value's anchor brings it back
  switching      login, schedule and interrupt between profiles, and how long a switch takes to settle

Programs: the symbol by day, the whole chain at night, the four-step sequence on a negative state, the prepared
identity week, and a dose plan. A library of ready profiles. A seeded simulation with known answers checks every
measure. docs/js/identity.js is identical (tested).
"""
from __future__ import annotations

import math
import sys

from . import peak as P
from . import trial as T

LEVELS = ("mission", "identity", "values", "beliefs", "skills", "behaviour", "environment")
LEVEL_NAMES = {"mission": "Mission", "identity": "Identity", "values": "Values", "beliefs": "Beliefs", "skills": "Skills",
               "behaviour": "Behaviour", "environment": "Environment"}
LEVEL_ASK = {"mission": "What is it for, beyond you?",
             "identity": "Who are you, in this?",
             "values": "What matters most here?",
             "beliefs": "What do you know to be true?",
             "skills": "What can you do?",
             "behaviour": "What do you do, and when?",
             "environment": "Where, and with what around you?"}
ENV_KEYS = ("clothing", "scent", "music", "space")
CONTEXTS = ("baseline", "after_mirroring")
SWITCH_BY = ("login", "schedule", "interrupt", "person")
REACTION = -10.0            # RMSSD drop (% of the level before) that counts as a reaction to a value conflict
DOSE = {"per_day": 12, "days": 30}


def r1(x):
    return None if x is None else math.floor(x * 10 + 0.5) / 10


def _v(x):
    return int(x) if isinstance(x, float) and x.is_integer() else x


def _mean(xs):
    return sum(xs) / len(xs)


def _sd(xs):
    m = _mean(xs)
    return math.sqrt(sum((x - m) * (x - m) for x in xs) / len(xs))


def _median(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def _welch(a, b):
    """Difference of means b - a with a 95% Welch interval."""
    va, vb = T._var(a), T._var(b)
    se = math.sqrt(va / len(a) + vb / len(b))
    d = _mean(b) - _mean(a)
    if se == 0:
        return d, d, d
    num = (va / len(a) + vb / len(b)) ** 2
    den = (va / len(a)) ** 2 / (len(a) - 1) + (vb / len(b)) ** 2 / (len(b) - 1)
    df = max(1, int(math.floor(num / den))) if den > 0 else len(a) + len(b) - 2
    t = T.tcrit(df)
    return d, d - t * se, d + t * se


def _paired(ds):
    """Mean of paired differences with a 95% t interval."""
    if len(ds) < 3:
        return None
    m = _mean(ds)
    se = math.sqrt(T._var(ds) / len(ds))
    t = T.tcrit(len(ds) - 1)
    return {"difference": _v(r1(m)), "lo": _v(r1(m - t * se)), "hi": _v(r1(m + t * se)), "n": len(ds)}


def _slope(xs, ys):
    """OLS slope with a 95% interval."""
    n = len(xs)
    mx, my = _mean(xs), _mean(ys)
    sxx = sum((x - mx) * (x - mx) for x in xs)
    if sxx == 0:
        return 0.0, 0.0, 0.0
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    res = sum((y - my - b * (x - mx)) ** 2 for x, y in zip(xs, ys))
    se = math.sqrt(res / (n - 2) / sxx) if n > 2 else 0.0
    t = T.tcrit(n - 2) if n > 2 else 0.0
    return b, b - t * se, b + t * se


# ---------------------------------------------------------------- the profile

def make_profile(id_: str, name: str, symbol: str, code: str, language="", created=0) -> dict:
    return {"schema": "rsos-identity/1", "id": id_, "name": name, "symbol": symbol, "code": code, "language": language,
            "created": created, "levels": {l: {"text": "", "image": "", "code": ""} for l in LEVELS},
            "environment": {k: "" for k in ENV_KEYS}, "futures": [],
            "policy": {"anchors": [], "max_stage": "suggest", "night_chain": False},
            "tree": {"center": "", "parts": []}, "versions": [], "ratings": [], "contexts": [], "walks": [], "rehearsals": []}


def set_level(p: dict, level: str, text=None, image=None, code=None) -> dict:
    if level not in LEVELS:
        raise ValueError("level must be one of " + ", ".join(LEVELS))
    L = p["levels"][level]
    if text is not None:
        L["text"] = text
    if image is not None:
        L["image"] = image
    if code is not None:
        L["code"] = code
    return L


def _code_ok(c: str) -> bool:
    return bool(c.strip()) and all(ch in ".- " for ch in c) and len(c.split()) <= 3 and all(len(w) <= 6 for w in c.split())


def issues(p: dict) -> list:
    """What still needs work before the profile can be played: missing levels, invalid or confusable codes."""
    out = []
    if not p.get("symbol"):
        out.append({"field": "symbol", "say": "Choose a symbol to head the profile."})
    if not _code_ok(p.get("code", "")):
        out.append({"field": "code", "say": "The login code needs dots and dashes only, up to three groups."})
    for l in LEVELS:
        if not p["levels"][l]["text"].strip():
            out.append({"field": l, "say": LEVEL_NAMES[l] + ": not written yet. " + LEVEL_ASK[l]})
    seen = {}
    if p.get("code"):
        seen[p["code"]] = "the login code"
    for l in LEVELS:
        c = p["levels"][l]["code"]
        if not c:
            continue
        if not _code_ok(c):
            out.append({"field": l, "say": LEVEL_NAMES[l] + ": the code needs dots and dashes only, up to three groups."})
        elif c in seen:
            out.append({"field": l, "say": LEVEL_NAMES[l] + ": the same code as " + seen[c] + "; the body cannot tell them apart."})
        else:
            for other, who in seen.items():
                if c.replace(" ", "").startswith(other.replace(" ", "")) or other.replace(" ", "").startswith(c.replace(" ", "")):
                    out.append({"field": l, "say": LEVEL_NAMES[l] + ": the code starts like " + who + "; make it differ in the first pulses."})
                    break
            seen[c] = LEVEL_NAMES[l].lower()
    return out


def completeness(p: dict) -> dict:
    filled = [l for l in LEVELS if p["levels"][l]["text"].strip()]
    coded = [l for l in LEVELS if p["levels"][l]["code"]]
    env = [k for k in ENV_KEYS if p["environment"].get(k)]
    return {"levels": len(filled), "codes": len(coded), "environment": len(env), "of": len(LEVELS),
            "ready": len(filled) == len(LEVELS) and not any(i["field"] in ("code", "symbol") for i in issues(p))}


# ---------------------------------------------------------------- versions

def save_version(p: dict, ts, note="") -> dict:
    v = {"v": len(p["versions"]) + 1, "ts": ts, "note": note, "symbol": p["symbol"], "code": p["code"],
         "levels": {l: p["levels"][l]["text"] for l in LEVELS}, "environment": dict(p["environment"])}
    p["versions"].append(v)
    return v


def diff(a: dict, b: dict) -> list:
    out = []
    for f in ("symbol", "code"):
        if a.get(f) != b.get(f):
            out.append({"field": f, "before": a.get(f), "after": b.get(f)})
    for l in LEVELS:
        if a["levels"].get(l, "") != b["levels"].get(l, ""):
            out.append({"field": l, "before": a["levels"].get(l, ""), "after": b["levels"].get(l, "")})
    for k in ENV_KEYS:
        if a["environment"].get(k, "") != b["environment"].get(k, ""):
            out.append({"field": "environment." + k, "before": a["environment"].get(k, ""), "after": b["environment"].get(k, "")})
    return out


# ---------------------------------------------------------------- coherence and drift

def rate(p: dict, ts, scores: dict, context="baseline") -> dict:
    if context not in CONTEXTS:
        raise ValueError("context must be one of " + ", ".join(CONTEXTS))
    r = {"ts": ts, "context": context, "scores": {l: scores[l] for l in LEVELS if scores.get(l) is not None}}
    p["ratings"].append(r)
    return r


def coherence(scores: dict):
    """One score, 0-10: how true the levels feel on average, less how unevenly. A profile felt at 8 on every level
    scores 8; one at 10 on values and 4 on behaviour scores lower than its mean."""
    vals = [float(scores[l]) for l in LEVELS if scores.get(l) is not None]
    if len(vals) < 3:
        return None
    m, s = _mean(vals), _sd(vals)
    weakest = min((l for l in LEVELS if scores.get(l) is not None), key=lambda l: scores[l])
    return {"score": _v(r1(max(0.0, min(10.0, m - s)))), "mean": _v(r1(m)), "spread": _v(r1(s)), "weakest": weakest}


def trend(p: dict, context="baseline") -> dict:
    rows = sorted((r for r in p["ratings"] if r["context"] == context), key=lambda r: r["ts"])
    pts = [((r["ts"] - rows[0]["ts"]) / 86400, coherence(r["scores"])) for r in rows]
    pts = [(x, c["score"]) for x, c in pts if c is not None]
    if len(pts) < 4 or pts[-1][0] - pts[0][0] < 7:
        return {"n": len(pts), "per_month": None, "lo": None, "hi": None, "verdict": "too_few",
                "say": "Rate the levels at least four times over a week or more to see a trend."}
    b, lo, hi = _slope([x for x, _ in pts], [y for _, y in pts])
    verdict = "rising" if lo > 0 else "falling" if hi < 0 else "no_clear_change"
    say = {"rising": "Coherence is rising", "falling": "Coherence is falling",
           "no_clear_change": "No clear change in coherence yet"}[verdict]
    return {"n": len(pts), "per_month": _v(r1(b * 30)), "lo": _v(r1(lo * 30)), "hi": _v(r1(hi * 30)), "verdict": verdict,
            "first": pts[0][1], "last": pts[-1][1],
            "say": say + f": {_v(r1(b * 30))} points a month [{_v(r1(lo * 30))}, {_v(r1(hi * 30))}]."}


def drift(p: dict, margin=1.0) -> dict:
    """Coherence after mirroring other people against the baseline. Drifts: the interval is below zero. Holds: the
    interval lies within the margin either side of zero."""
    a = [c["score"] for c in (coherence(r["scores"]) for r in p["ratings"] if r["context"] == "baseline") if c]
    b = [c["score"] for c in (coherence(r["scores"]) for r in p["ratings"] if r["context"] == "after_mirroring") if c]
    if len(a) < 3 or len(b) < 3:
        return {"n_baseline": len(a), "n_after": len(b), "difference": None, "lo": None, "hi": None, "verdict": "too_few",
                "say": "Rate the levels at least three times on ordinary days and three times right after time with other people."}
    d, lo, hi = _welch(a, b)
    verdict = "drifts" if hi < 0 else "holds" if lo > -margin and hi < margin else "unclear"
    say = {"drifts": "Mirroring others pulls you away from this profile",
           "holds": "You keep this profile while mirroring others",
           "unclear": "Not clear yet whether mirroring others moves you"}[verdict]
    return {"n_baseline": len(a), "n_after": len(b), "difference": _v(r1(d)), "lo": _v(r1(lo)), "hi": _v(r1(hi)),
            "verdict": verdict, "say": say + f": {_v(r1(d))} points [{_v(r1(lo))}, {_v(r1(hi))}]."}


# ---------------------------------------------------------------- generalisation

def add_context(p: dict, ts, context: str, trained: bool, fired: bool, latency_s=None) -> dict:
    c = {"ts": ts, "context": context, "trained": bool(trained), "fired": bool(fired), "latency_s": latency_s}
    p["contexts"].append(c)
    return c


def generalisation(p: dict) -> dict:
    tr = [c for c in p["contexts"] if c["trained"]]
    un = [c for c in p["contexts"] if not c["trained"]]
    rt = sum(1 for c in tr if c["fired"]) / len(tr) * 100 if tr else None
    ru = sum(1 for c in un if c["fired"]) / len(un) * 100 if un else None
    lat = [c["latency_s"] for c in p["contexts"] if c["fired"] and c["latency_s"] is not None]
    score = None if rt in (None, 0) or ru is None else min(100.0, ru / rt * 100)
    names = sorted(set(c["context"] for c in un if c["fired"]))
    if score is None:
        say = "Log contexts where you meant to act, trained and new, to see whether the behaviour travels."
    else:
        say = f"The behaviour started in {_v(r1(ru))}% of new contexts and {_v(r1(rt))}% of trained ones: it travels " + (
            "well." if score >= 75 else "partly." if score >= 40 else "little so far; train it in more places.")
    return {"trained": len(tr), "new": len(un), "trained_rate": _v(r1(rt)), "new_rate": _v(r1(ru)), "score": _v(r1(score)),
            "median_latency_s": _v(r1(_median(lat))) if lat else None, "travelled_to": names, "say": say}


# ---------------------------------------------------------------- the anchor tree and recall walks

def set_tree(p: dict, center: str, parts: list) -> dict:
    """parts: [{part, context, code}], up to five, each context fixed to a part of the central image."""
    if len(parts) > 5:
        raise ValueError("an anchor tree holds up to five parts")
    p["tree"] = {"center": center, "parts": [{"part": x.get("part", ""), "context": x.get("context", ""), "code": x.get("code", "")} for x in parts]}
    return p["tree"]


def add_walk(p: dict, ts, kind: str, results: list) -> dict:
    """kind: "tree" (recall each context from its part) or "single" (recall the contexts from one image).
    results: [{part, ok, ms}]."""
    if kind not in ("tree", "single"):
        raise ValueError("kind must be tree or single")
    w = {"ts": ts, "kind": kind, "results": [{"part": r.get("part", ""), "ok": bool(r.get("ok")), "ms": r.get("ms")} for r in results]}
    p["walks"].append(w)
    return w


def walks_report(p: dict) -> dict:
    out = {}
    for kind in ("tree", "single"):
        ws = sorted((w for w in p["walks"] if w["kind"] == kind), key=lambda w: w["ts"])
        cyc = []
        for i, w in enumerate(ws):
            n = len(w["results"])
            ok = sum(1 for r in w["results"] if r["ok"])
            ms = [r["ms"] for r in w["results"] if r["ok"] and r["ms"] is not None]
            cyc.append({"cycle": i + 1, "accuracy": _v(r1(ok / n * 100)) if n else None, "median_ms": _v(r1(_median(ms))) if ms else None})
        timed = [(c["cycle"], c["median_ms"]) for c in cyc if c["median_ms"] is not None]
        sl = _slope([x for x, _ in timed], [y for _, y in timed])[0] if len(timed) >= 3 else None
        last = [c["accuracy"] for c in cyc[-3:] if c["accuracy"] is not None]
        out[kind] = {"walks": len(ws), "cycles": cyc, "ms_per_cycle": _v(r1(sl)), "recent_accuracy": _v(r1(_mean(last))) if last else None}
    t, s = out["tree"]["cycles"], out["single"]["cycles"]
    k = min(len(t), len(s))
    out["compare"] = None
    if k >= 3:
        da = [t[i]["accuracy"] - s[i]["accuracy"] for i in range(k) if t[i]["accuracy"] is not None and s[i]["accuracy"] is not None]
        dm = [t[i]["median_ms"] - s[i]["median_ms"] for i in range(k) if t[i]["median_ms"] is not None and s[i]["median_ms"] is not None]
        out["compare"] = {"cycles": k, "accuracy": _paired(da), "ms": _paired(dm)}
        a, m = out["compare"]["accuracy"], out["compare"]["ms"]
        parts = []
        if a and a["lo"] > 0:
            parts.append(f"recalled better from the tree ({a['difference']} points [{a['lo']}, {a['hi']}])")
        elif a and a["hi"] < 0:
            parts.append(f"recalled better from one image ({a['difference']} points [{a['lo']}, {a['hi']}])")
        if m and m["hi"] < 0:
            parts.append(f"recalled faster from the tree ({m['difference']} ms [{m['lo']}, {m['hi']}])")
        elif m and m["lo"] > 0:
            parts.append(f"recalled faster from one image ({m['difference']} ms)")
        out["say"] = ("Contexts are " + " and ".join(parts) + ".") if parts else f"No clear difference between the tree and one image after {k} walks of each."
    else:
        out["say"] = "Walk the tree and a single image three times each to compare them."
    return out


# ---------------------------------------------------------------- value-conflict rehearsal

def add_rehearsal(p: dict, ts, value: str, kind: str, before, during, after, distress=None) -> dict:
    """A value conflict rehearsed: RMSSD (ms) before, while imagining the situation that violates the value, and
    after the value's anchor. kind: "violation" or "neutral" (an ordinary situation, the comparison)."""
    if kind not in ("violation", "neutral"):
        raise ValueError("kind must be violation or neutral")
    r = {"ts": ts, "value": value, "kind": kind, "before": before, "during": during, "after": after, "distress": distress}
    p["rehearsals"].append(r)
    return r


def reaction(r: dict) -> dict:
    b, d, a = r.get("before"), r.get("during"), r.get("after")
    if not b or d is None:
        return {"reaction": None, "recovery": None, "reacted": None}
    rc = (d - b) / b * 100
    rv = None if a is None else (a - d) / b * 100
    return {"reaction": _v(r1(rc)), "recovery": _v(r1(rv)), "reacted": rc <= REACTION}


def rehearsals_report(p: dict) -> dict:
    per, neutral = {}, []
    for r in p["rehearsals"]:
        x = reaction(r)
        if x["reaction"] is None:
            continue
        if r["kind"] == "neutral":
            neutral.append(x)
            continue
        per.setdefault(r["value"], []).append(x)
    values = []
    for v in sorted(per):
        xs = per[v]
        rec = [x["recovery"] for x in xs if x["recovery"] is not None]
        values.append({"value": v, "n": len(xs), "reaction": _v(r1(_mean([x["reaction"] for x in xs]))),
                       "recovery": _v(r1(_mean(rec))) if rec else None,
                       "reacted": _v(r1(sum(1 for x in xs if x["reacted"]) / len(xs) * 100))})
    strongest = min(values, key=lambda v: v["reaction"])["value"] if values else None
    nfa = _v(r1(sum(1 for x in neutral if x["reacted"]) / len(neutral) * 100)) if neutral else None
    return {"values": values, "neutral": len(neutral), "neutral_reacted": nfa, "strongest": strongest,
            "say": ("Rehearse a value conflict and an ordinary situation, with the heart measured, to see which value the body defends."
                    if not values else f"Your body reacts most to a conflict with {strongest}.")}


# ---------------------------------------------------------------- switching between profiles

def switch(log: list, ts, to: str, by="person") -> dict:
    if by not in SWITCH_BY:
        raise ValueError("by must be one of " + ", ".join(SWITCH_BY))
    e = {"ts": ts, "to": to, "by": by, "settled": None}
    log.append(e)
    return e


def settle(log: list, ts) -> dict | None:
    """The person confirms the switched-to profile feels like them now: the time since the switch is its latency."""
    if not log or log[-1]["settled"] is not None:
        return None
    log[-1]["settled"] = ts - log[-1]["ts"]
    return log[-1]


def interrupt(log: list, ts, base: str) -> dict:
    """The global interrupt: back to the base profile at once, whatever is running."""
    return switch(log, ts, base, "interrupt")


def current(log: list, base: str) -> str:
    return log[-1]["to"] if log else base


def _minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def profile_at(schedule: list, minute: int):
    """schedule: [{from: "08:00", to: "12:00", profile}]; the profile for this minute of the day, or None."""
    for s in schedule:
        a, b = _minutes(s["from"]), _minutes(s["to"])
        if (a <= minute < b) if a <= b else (minute >= a or minute < b):
            return s["profile"]
    return None


def switch_report(log: list) -> dict:
    by = {k: sum(1 for e in log if e["by"] == k) for k in SWITCH_BY}
    lat = [e["settled"] for e in log if e["settled"] is not None]
    return {"switches": len(log), "by": by, "settled": len(lat), "median_settle_s": _v(r1(_median(lat))) if lat else None}


# ---------------------------------------------------------------- programs

def _q(s) -> str:
    return '"' + str(s).replace('"', "'").replace("\n", " ") + '"'


def _head(pid: str, title: str, per_day=20) -> list:
    return [f"PROTOCOL {pid} {_q(title)}", "VERSION 1.0", f"SAFETY max_per_hour=6 max_per_day={per_day} refractory=90s haptic_max=0.4",
            "BREATH inhale=4s exhale=6s", ""]


def _slug(p) -> str:
    s = "".join(ch if ch.isalnum() else "_" for ch in (p.get("id") or "identity").lower())
    return ("id_" + s)[:40]


def _symbol_tier(p, n=1) -> list:
    who = p["levels"]["identity"]["text"] or p["name"]
    return [f"TIER {n} SYMBOL {{", f"  GLYPH {_q(p['symbol'])}", f"  V {_q(p['levels']['identity']['image'] or ('see ' + p['symbol'] + ' in front of you'))}",
            f"  A {_q(who)}", f"  K {_q('feel the code ' + p['code'])}", f"  WORD {_q(p['name'])}"] + (
        [f"  O {_q(p['environment']['scent'])}"] if p["environment"].get("scent") else []) + [f"  TACTON {_q(p['code'])}", "}"]


def _level_tier(p, l, n) -> list:
    L = p["levels"][l]
    return [f"TIER {n} {l.upper()} {{", f"  V {_q(L['image'] or ('see ' + LEVEL_NAMES[l].lower()))}", f"  A {_q(L['text'] or LEVEL_NAMES[l])}",
            f"  K {_q('feel ' + LEVEL_NAMES[l].lower() + ' in the body')}"] + ([f"  TACTON {_q(L['code'])}"] if L["code"] else []) + ["}"]


def day_rsx(p: dict) -> str:
    """By day: the symbol alone, a few seconds, the whole profile behind it."""
    L = _head(_slug(p) + "_day", p["name"] + ": the symbol") + _symbol_tier(p) + [
        "", "PHASE login breath=inhale {", "  ACTIVATE SYMBOL", "}",
        "PHASE seal breath=exhale {", f"  SAY {_q(p['levels']['identity']['text'] or p['name'])}", f"  MARK {_q('login ' + p['id'])}", "}"]
    return "\n".join(L) + "\n"


def night_rsx(p: dict) -> str:
    """At night: the whole chain from the symbol down to the environment, one level per breath."""
    L = _head(_slug(p) + "_night", p["name"] + ": the whole chain") + _symbol_tier(p)
    for i, l in enumerate(LEVELS):
        L += _level_tier(p, l, i + 2)
    L += ["", "PHASE symbol breath=inhale {", "  ACTIVATE SYMBOL", "}"]
    for l in LEVELS:
        L += [f"PHASE {l} breath=exhale {{", f"  ACTIVATE {l.upper()}", "}"]
    L += ["PHASE close breath=inhale {", "  ACTIVATE SYMBOL", f"  MARK {_q('chain ' + p['id'])}", "}"]
    return "\n".join(L) + "\n"


def sequence_rsx(p: dict, state="the old state") -> str:
    """On a negative state, four steps: the identity peak, Core Transformation, future-pacing, a movement peak with
    the code."""
    fut = [f for f in (p.get("futures") or [x["context"] for x in p["tree"]["parts"]]) if f][:3] or ["The next time it starts"]
    L = _head(_slug(p) + "_seq", p["name"] + ": four steps") + _symbol_tier(p) + [
        "", "FUTURES " + " | ".join(_q(f) for f in fut), "",
        "PHASE peak breath=inhale {", "  ACTIVATE SYMBOL", f"  SAY {_q(p['levels']['identity']['text'] or p['name'])}", "}",
        "PHASE core dur=20s {", f"  FEEL {_q('Notice ' + state + ' and ask it what it wants for you')}", "  WAIT 6s",
        "  FEEL \"Ask what that would give you, and again, until you reach a core state\"", "  WAIT 6s",
        "  FEEL \"Let the core state flow back through the old state\"", "}",
        "PHASE future breath=exhale {", "  FOR FUTURE {", f"    SEE {_q('$future, as ' + p['name'])}", "    WAIT 1s", "  }", "}",
        "PHASE movement dur=6s {", "  GESTURE \"Move: stand, breathe out, fist or step forward\"", "  ACTIVATE SYMBOL",
        f"  MARK {_q('sequence ' + p['id'])}", "}"]
    return "\n".join(L) + "\n"


def level_rsx(p: dict, level: str, day: int) -> str:
    L = _head(_slug(p) + "_d" + str(day), p["name"] + ": day " + str(day) + ", " + LEVEL_NAMES[level].lower()) + _symbol_tier(p) + _level_tier(p, level, 2)
    fut = [f for f in (p.get("futures") or [x["context"] for x in p["tree"]["parts"]]) if f][:1] or ["Tomorrow"]
    L += ["", "FUTURES " + _q(fut[0]), "", "PHASE symbol breath=inhale {", "  ACTIVATE SYMBOL", "}",
          f"PHASE {level} breath=exhale {{", f"  ACTIVATE {level.upper()}", "}",
          "PHASE future breath=exhale {", "  FOR FUTURE {", f"    SEE {_q('$future, living this')}", "  }", f"  MARK {_q('day ' + str(day))}", "}"]
    return "\n".join(L) + "\n"


def install_rsx(p: dict) -> str:
    """Day 8 of the week: the symbol installed in a light trance, then three future situations."""
    fut = [f for f in (p.get("futures") or [x["context"] for x in p["tree"]["parts"]]) if f][:3]
    while len(fut) < 3:
        fut.append(["At work", "At home", "Under pressure"][len(fut)])
    L = _head(_slug(p) + "_install", p["name"] + ": installing the symbol") + _symbol_tier(p) + [
        "", "FUTURES " + " | ".join(_q(f) for f in fut), "",
        "PHASE settle dur=20s {", "  FEEL \"Let the eyes close; each breath out a little heavier\"", "  TONE 110Hz 18s", "}",
        "PHASE descend breath=exhale {", "  FEEL \"Counting down from five, down a little more with each number\"", "}",
        "PHASE install breath=inhale {", "  ACTIVATE SYMBOL", f"  SAY {_q('All seven levels, gathered in ' + p['symbol'])}", "}",
        "PHASE future dur=12s {", "  FOR FUTURE {", f"    SEE {_q('$future: ' + p['symbol'] + ' is there and you act from it')}", "    WAIT 3s", "  }", "}",
        "PHASE return dur=8s {", "  SAY \"Counting up from one to five, eyes open, awake and clear\"", f"  MARK {_q('installed ' + p['id'])}", "}"]
    return "\n".join(L) + "\n"


def week_plan(p: dict) -> list:
    """The prepared identity week: one level a day for seven days, each with future-pacing; on day 8 the symbol is
    installed in trance with three future situations."""
    days = [{"day": i + 1, "level": l, "title": LEVEL_NAMES[l], "practice": p["levels"][l]["text"] or LEVEL_ASK[l],
             "rsx": level_rsx(p, l, i + 1)} for i, l in enumerate(LEVELS)]
    days.append({"day": 8, "level": "symbol", "title": "The symbol", "practice": "Install " + p["symbol"] + " in a light trance, with three future situations.",
                 "rsx": install_rsx(p)})
    return days


def dose_plan(start="08:00", end="21:00", per_day=DOSE["per_day"], days=DOSE["days"]) -> dict:
    """Times for a month's dose of short symbol practices, evenly spread over the waking day."""
    a, b = _minutes(start), _minutes(end)
    step = (b - a) / (per_day - 1) if per_day > 1 else 0
    times = []
    for i in range(per_day):
        m = int(math.floor(a + i * step + 0.5))
        times.append(f"{m // 60:02d}:{m % 60:02d}")
    return {"per_day": per_day, "days": days, "total": per_day * days, "times": times,
            "say": f"{per_day} short practices a day for {days} days, {per_day * days} in all; the symbol by day and the whole chain once at night."}


# ---------------------------------------------------------------- library

LIBRARY = [
    {"id": "steady", "name": "Steady under pressure", "symbol": "🦁", "code": "..-",
     "levels": {"mission": "People around me are safer because I stay clear when it counts.",
                "identity": "I am the one who stays steady.",
                "values": "Clarity, courage, care.",
                "beliefs": "Pressure is information. I can feel it and still choose.",
                "skills": "I can slow my breath, name what is happening and choose the next step.",
                "behaviour": "When pressure rises I breathe out long, lower my voice and act on one thing.",
                "environment": "A clear desk, a grounded stance, cedar on the wrist."},
     "environment": {"clothing": "Something with structure", "scent": "Cedar", "music": "Low strings", "space": "A clear desk"}},
    {"id": "learner", "name": "Focused learner", "symbol": "🦉", "code": ".-.",
     "levels": {"mission": "What I learn I pass on, so others start further ahead.",
                "identity": "I am a learner who finishes.",
                "values": "Curiosity, patience, precision.",
                "beliefs": "Not knowing yet is the beginning of knowing.",
                "skills": "I can break a subject into steps and test myself on each.",
                "behaviour": "I start with the hardest twenty minutes, then test myself before I stop.",
                "environment": "One window, phone in another room, rosemary nearby."},
     "environment": {"clothing": "Comfortable, the same each session", "scent": "Rosemary", "music": "None, or steady rain", "space": "One window, nothing else open"}},
    {"id": "maker", "name": "Creative maker", "symbol": "🐉", "code": "-..",
     "levels": {"mission": "I make things that did not exist and leave the world more alive.",
                "identity": "I am a maker.",
                "values": "Play, craft, courage to show.",
                "beliefs": "The first version is supposed to be rough.",
                "skills": "I can generate many options fast and then choose one to finish.",
                "behaviour": "I make something every day, and I show it before it feels ready.",
                "environment": "Tools within reach, music on, space to move."},
     "environment": {"clothing": "Clothes I can get dirty", "scent": "Orange peel", "music": "Fast, without words", "space": "Tools within reach"}},
    {"id": "calm_parent", "name": "Calm parent", "symbol": "🌳", "code": "--.",
     "levels": {"mission": "My children grow up knowing that strong feelings can be held.",
                "identity": "I am the calm in the house.",
                "values": "Warmth, patience, honesty.",
                "beliefs": "A child's storm is not about me; it is a moment to help.",
                "skills": "I can notice my rising heat, pause and kneel to their level.",
                "behaviour": "When voices rise I lower mine, breathe out and name the feeling.",
                "environment": "Soft light in the evening, a quiet corner, lavender."},
     "environment": {"clothing": "Soft", "scent": "Lavender", "music": "Quiet", "space": "A quiet corner"}},
    {"id": "athlete", "name": "Athlete at rest", "symbol": "🐆", "code": ".--",
     "levels": {"mission": "I show what a trained body and a quiet mind can do together.",
                "identity": "I am an athlete, also when I rest.",
                "values": "Discipline, recovery, joy in effort.",
                "beliefs": "Rest is training. The body adapts while I sleep.",
                "skills": "I can switch from full effort to full rest on one breath.",
                "behaviour": "After hard effort I breathe out long, stretch and stop thinking about it.",
                "environment": "Kit ready the night before, cool room, eucalyptus."},
     "environment": {"clothing": "Training kit", "scent": "Eucalyptus", "music": "A pre-start track", "space": "Kit ready the night before"}},
    {"id": "speaker", "name": "Clear speaker", "symbol": "🦅", "code": "-.-",
     "levels": {"mission": "What matters gets said clearly, so people can act on it.",
                "identity": "I am someone worth listening to.",
                "values": "Truth, clarity, respect for the listener.",
                "beliefs": "Nerves are energy for the room.",
                "skills": "I can open with one sentence, pause and look at one person at a time.",
                "behaviour": "Before I speak I plant my feet, breathe out and say the first sentence slowly.",
                "environment": "Feet on the floor, water at hand, peppermint."},
     "environment": {"clothing": "What I would wear to be taken seriously", "scent": "Peppermint", "music": "One track before", "space": "Standing, feet planted"}},
]


def from_template(tid: str, id_=None, created=0) -> dict:
    t = next(x for x in LIBRARY if x["id"] == tid)
    p = make_profile(id_ or t["id"], t["name"], t["symbol"], t["code"], "", created)
    for l in LEVELS:
        p["levels"][l]["text"] = t["levels"][l]
    p["environment"] = dict(t["environment"])
    return p


# ---------------------------------------------------------------- simulation with known answers

class SimIdentity:
    """A simulated person practising a profile. Each level's truth starts low and rises toward a ceiling by
    `growth` points a month (0 means practice does nothing); ratings are the truth plus noise, rounded to whole
    points. After mirroring other people, every level is pulled down by `pull` and the weaker levels more."""

    def __init__(self, seed=1, growth=1.0, pull=0.0, noise=1.0, start=4.0):
        self.rng = P.Rng(seed)
        self.growth, self.pull, self.noise = growth, pull, noise
        self.base = [start + self.rng.u() * 2 for _ in LEVELS]

    def truth(self, day):
        return [min(9.0, b + self.growth * day / 30) for b in self.base]

    def rate(self, day, mirrored=False):
        out = {}
        for i, l in enumerate(LEVELS):
            t = self.truth(day)[i] - (self.pull * (1 + 0.5 * (i % 2)) if mirrored else 0)
            x = math.floor(t + self.rng.gauss() * self.noise + 0.5)
            out[l] = max(0, min(10, x))
        return out


def _sim_trend(seed, growth, weeks):
    s, p = SimIdentity(seed, growth), make_profile("s", "Sim", "🦁", "..-")
    for w in range(weeks):
        rate(p, w * 7 * 86400, s.rate(w * 7))
    return trend(p)["verdict"]


def _sim_drift(seed, pull, n=10):
    s, p = SimIdentity(seed, 0.0, pull), make_profile("s", "Sim", "🦁", "..-")
    for k in range(n):
        rate(p, k * 86400, s.rate(30), "baseline")
        rate(p, k * 86400 + 3600, s.rate(30, True), "after_mirroring")
    return drift(p)["verdict"]


def _sim_walks(seed, advantage, cycles=6, parts=5):
    """Recall walks with a known tree advantage (extra retrieval paths raise recall and speed it) or none."""
    rng, p = P.Rng(seed), make_profile("s", "Sim", "🦁", "..-")
    for c in range(cycles):
        for kind in ("tree", "single"):
            base = 0.35 + 0.3 * (1 - 0.8 ** c)
            pr = min(0.97, 1 - (1 - base) ** (1 + advantage) if kind == "tree" else base)
            res = []
            for k in range(parts):
                ok = rng.u() < pr
                ms = math.floor(2600 * (c + 1) ** -0.35 * (1 - 0.2 * advantage if kind == "tree" else 1) * (1 + 0.15 * rng.gauss()) + 0.5)
                res.append({"part": "p" + str(k), "ok": ok, "ms": ms})
            add_walk(p, c * 86400 + (0 if kind == "tree" else 1), kind, res)
    c = walks_report(p)["compare"]
    return (c["accuracy"] is not None and c["accuracy"]["lo"] > 0), (c["ms"] is not None and c["ms"]["hi"] < 0)


def _sim_rehearsal(seed, true_drop, noise):
    """One rehearsal pair: a violation with a true RMSSD drop, and a neutral one with none. noise: measurement sd in %."""
    rng = P.Rng(seed)
    b = 40 + rng.u() * 30
    v = reaction({"before": b, "during": b * (1 + (true_drop + rng.gauss() * noise) / 100), "after": b})
    n = reaction({"before": b, "during": b * (1 + (rng.gauss() * noise) / 100), "after": b})
    return v["reacted"], n["reacted"]


def evaluate(n=200) -> dict:
    res = {}
    for g in (1.0, 0.0):
        for weeks in (8, 26):
            vs = [_sim_trend(1000 + i, g, weeks) for i in range(n)]
            res[("trend", g, weeks)] = {"rising": _v(r1(vs.count("rising") / n * 100)), "falling": _v(r1(vs.count("falling") / n * 100))}
    for pull in (1.5, 0.0):
        vs = [_sim_drift(2000 + i, pull) for i in range(n)]
        res[("drift", pull)] = {k: _v(r1(vs.count(k) / n * 100)) for k in ("drifts", "holds", "unclear")}
    for adv in (1.0, 0.0):
        for cyc in (6, 12):
            xs = [_sim_walks(3000 + i, adv, cyc) for i in range(n)]
            res[("walks", adv, cyc)] = {"better": _v(r1(sum(1 for x in xs if x[0]) / n * 100)), "faster": _v(r1(sum(1 for x in xs if x[1]) / n * 100))}
    for noise, label in ((4.0, "chest"), (8.0, "camera")):
        xs = [_sim_rehearsal(4000 + i, -18.0, noise) for i in range(n)]
        res[("rehearsal", label)] = {"sensitivity": _v(r1(sum(1 for x in xs if x[0]) / n * 100)),
                                     "false": _v(r1(sum(1 for x in xs if x[1]) / n * 100))}
    return {"n": n, "res": res}


def report(ev: dict) -> str:
    R, n = ev["res"], ev["n"]
    L = ["# IDENTITY measures on simulated people", "",
         f"Generated by `python -m rsso.identity --evaluate`. {n} simulated people per row, each with a known answer. "
         "Built and tested in simulation; effect unproven in people.", "",
         "## Coherence over months (claim C41)", "",
         "Weekly ratings of the seven levels, each whole points with noise (sd 1). Practice raises every level by a known amount a month, or not at all.", "",
         "| Truth | Weeks rated | Called rising | Called falling |", "|---|---|---|---|"]
    for g, name in ((1.0, "Rises 1 point a month"), (0.0, "No change")):
        for w in (8, 26):
            x = R[("trend", g, w)]
            L.append(f"| {name} | {w} | {x['rising']}% | {x['falling']}% |")
    L += ["", "## Drift while mirroring others (claim C89)", "",
          "Ten ratings on ordinary days and ten right after time with other people. Drifters lose 1.5 points (more on some levels); stable people lose nothing. "
          "Holds means the interval lies within one point of zero.", "",
          "| Truth | Drifts | Holds | Unclear |", "|---|---|---|---|"]
    for pull, name in ((1.5, "Drifts"), (0.0, "Stable")):
        x = R[("drift", pull)]
        L.append(f"| {name} | {x['drifts']}% | {x['holds']}% | {x['unclear']}% |")
    L += ["", "## The anchor tree against one image (claim C16)", "",
          "Recall walks of five contexts, from a tree (each context on its own part) and from a single image, with recall improving over walks. Where the tree helps, each context has "
          "two retrieval paths instead of one and is reached 20% faster; otherwise both are the same.", "",
          "| Truth | Walks of each | Tree recalled better (interval above zero) | Tree recalled faster (interval below zero) |", "|---|---|---|---|"]
    for adv, name in ((1.0, "Tree helps"), (0.0, "No difference")):
        for cyc in (6, 12):
            x = R[("walks", adv, cyc)]
            L.append(f"| {name} | {cyc} | {x['better']}% | {x['faster']}% |")
    L += ["", "## Detecting a value conflict in the body (claim C62)", "",
          f"A rehearsed value conflict lowers RMSSD by 18% on average; an ordinary situation by nothing. A reaction is counted at a drop of {_v(-REACTION)}% or more.", "",
          "| Measurement | Conflicts detected | Ordinary situations wrongly flagged |", "|---|---|---|"]
    for label, name in (("chest", "Chest strap (noise 4%)"), ("camera", "Phone camera (noise 8%)")):
        x = R[("rehearsal", label)]
        L.append(f"| {name} | {x['sensitivity']}% | {x['false']}% |")
    L += ["", "Reading: each measure finds a real change when there is one and rarely calls one when there is not, given enough ratings. Eight weeks "
          "is often too short to see a rise of one point a month; six months is enough. With five contexts a walk, recall speed shows a tree's "
          "advantage sooner than accuracy does. Single rehearsals measured by camera are noisy: "
          "repeat each value conflict and compare it with ordinary situations before trusting it.", ""]
    return "\n".join(L)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["--evaluate"]:
        import pathlib
        path = pathlib.Path(__file__).resolve().parents[1] / "results" / "identity.md"
        path.write_text(report(evaluate()), encoding="utf-8")
        print(f"wrote {path}")
        return 0
    print("usage: python -m rsso.identity --evaluate")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
