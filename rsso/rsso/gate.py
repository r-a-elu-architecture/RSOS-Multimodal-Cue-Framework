"""The autonomy gate (spec/GATE.md): part of CONTAIN.

A device may act on its own only when the evidence allows it, one anchor at a time. Each anchor sits at a stage:

  0 manual     the person fires the anchor themselves
  1 suggest    the device detects stress and offers the anchor; the person confirms
  2 auto       the device may fire the anchor by itself, within CONTAIN's limits
  3 pressure   also allowed during deliberate pressure practice (stress inoculation), only with an explicit opt-in

The stage is earned from four kinds of evidence: manual training (captures at a peak, PEAK), proven strength (probe
trials against sham, PEAK), few false alarms (offers the person marked "not needed"), and no wear-out or contamination
(uses outside training, PEAK's contamination check). When the evidence weakens the gate closes again by itself.

Also here: consent records for profiling, the flag for anything that works below the person's awareness, and the
audit log of every automatic decision. docs/js/gate.js is identical (tested).
"""
from __future__ import annotations

import math
import sys

from . import peak as P

STAGES = ("manual", "suggest", "auto", "pressure")
STAGE_NAMES = {"manual": "Manual", "suggest": "Suggest", "auto": "Automatic", "pressure": "Under pressure"}
NEED = {
    "suggest": {"captures": 5, "status": ("strong", "present")},
    "auto": {"captures": 8, "status": ("strong",), "offers": 10, "false_alarm_max": 25.0, "wear_max": 25},
    "pressure": {"auto_days": 30, "offers": 30, "false_alarm_max": 15.0, "wear_max": 10},
}
OUTCOMES = ("helped", "not_needed", "dismissed", "ignored")
WINDOW = 30                     # recent offers that count for the false-alarm rate
WEAR_WARN = 15                  # uses outside training since the last pairing: warn
CONSENT_SCOPES = ("speech_profiling", "emotion_detection", "night_cueing", "automatic_firing", "research_sharing")
BELOW_AWARENESS = {"night_cueing": "Plays while you sleep", "blind_probe": "Sham or real is not shown until afterwards",
                   "automatic_firing": "The device fires without asking", "speech_profiling": "Your words are analysed"}


def r1(x):
    return None if x is None else math.floor(x * 10 + 0.5) / 10


def _v(x):
    return int(x) if isinstance(x, float) and x.is_integer() else x


# ---------------------------------------------------------------- evidence

def record_offer(offers: list, anchor_id: str, ts, outcome: str, stage="suggest", stress=None) -> dict:
    if outcome not in OUTCOMES:
        raise ValueError("outcome must be one of " + ", ".join(OUTCOMES))
    o = {"anchor": anchor_id, "ts": ts, "outcome": outcome, "stage": stage}
    if stress is not None:
        o["stress"] = bool(stress)
    offers.append(o)
    return o


def false_alarms(offers: list, anchor_id: str) -> dict:
    mine = [o for o in offers if o["anchor"] == anchor_id and o["outcome"] != "ignored"][-WINDOW:]
    fa = sum(1 for o in mine if o["outcome"] == "not_needed")
    helped = sum(1 for o in mine if o["outcome"] == "helped")
    return {"offers": len(mine), "false": fa, "helped": helped, "rate": _v(r1(fa / len(mine) * 100)) if mine else None}


def wear(anchor: dict) -> dict:
    """Uses outside training since the last pairing at a peak. Each unpaired use teaches the cue a little that it
    predicts nothing in particular (latent inhibition, extinction); a new pairing renews it."""
    last = max((c.get("ts", 0) for c in anchor.get("captures", [])), default=None)
    since = [u for u in anchor.get("uses", []) if last is None or u.get("ts", 0) > last]
    n = len(since)
    level = "high" if n >= NEED["auto"]["wear_max"] else "medium" if n >= WEAR_WARN else "low"
    say = {"low": "Fresh: recently paired at a peak.",
           "medium": "Used " + str(n) + " times since its last pairing. Pair it at a peak again soon.",
           "high": "Used " + str(n) + " times since its last pairing: it may be wearing out. Pair it at a peak before automatic use."}[level]
    return {"unpaired_uses": n, "level": level, "say": say}


# ---------------------------------------------------------------- the gate

def _check(id_, name, met, have, need):
    return {"id": id_, "name": name, "met": bool(met), "have": have, "need": need}


def gate(anchor: dict, offers: list, now=0, optins: dict | None = None, history: dict | None = None) -> dict:
    """The highest stage this anchor may use now, every check behind it, and what the next stage needs.
    history: {"auto_since": ts} when the anchor has been automatic since then (for the pressure stage)."""
    optins, history = optins or {}, history or {}
    s, c, w, fa = P.strength(anchor), P.contamination(anchor), wear(anchor), false_alarms(offers, anchor["id"])
    caps = len(anchor.get("captures", []))
    checks = {
        "suggest": [_check("captures", "Paired at a peak by hand", caps >= NEED["suggest"]["captures"], caps, NEED["suggest"]["captures"]),
                    _check("strength", "Probes show an effect", s["status"] in NEED["suggest"]["status"], s["status"], "present or strong"),
                    _check("clean", "Not taking on stress", c["risk"] != "high", c["risk"], "not high")],
        "auto": [_check("captures", "Paired at a peak by hand", caps >= NEED["auto"]["captures"], caps, NEED["auto"]["captures"]),
                 _check("strength", "Probes show a strong effect", s["status"] in NEED["auto"]["status"], s["status"], "strong"),
                 _check("offers", "Enough confirmed offers", fa["offers"] >= NEED["auto"]["offers"], fa["offers"], NEED["auto"]["offers"]),
                 _check("false_alarms", "Few false alarms", fa["rate"] is not None and fa["rate"] <= NEED["auto"]["false_alarm_max"],
                        fa["rate"], "at most " + str(_v(NEED["auto"]["false_alarm_max"])) + "%"),
                 _check("wear", "Not worn out", w["unpaired_uses"] < NEED["auto"]["wear_max"], w["unpaired_uses"], "under " + str(NEED["auto"]["wear_max"])),
                 _check("clean", "Not taking on stress", c["risk"] == "low", c["risk"], "low")],
    }
    auto_days = (now - history["auto_since"]) / 86400 if history.get("auto_since") is not None else 0
    checks["pressure"] = [
        _check("optin", "You chose pressure practice", bool(optins.get("pressure")), bool(optins.get("pressure")), True),
        _check("auto_days", "Automatic for a month", auto_days >= NEED["pressure"]["auto_days"], _v(r1(auto_days)), NEED["pressure"]["auto_days"]),
        _check("offers", "Many confirmed offers", fa["offers"] >= NEED["pressure"]["offers"], fa["offers"], NEED["pressure"]["offers"]),
        _check("false_alarms", "Very few false alarms", fa["rate"] is not None and fa["rate"] <= NEED["pressure"]["false_alarm_max"],
               fa["rate"], "at most " + str(_v(NEED["pressure"]["false_alarm_max"])) + "%"),
        _check("wear", "Fresh", w["unpaired_uses"] < NEED["pressure"]["wear_max"], w["unpaired_uses"], "under " + str(NEED["pressure"]["wear_max"])),
    ]
    stage = "manual"
    for st in ("suggest", "auto", "pressure"):
        if all(k["met"] for k in checks[st]):
            stage = st
        else:
            break
    nxt = STAGES[min(STAGES.index(stage) + 1, 3)] if stage != "pressure" else None
    needs = [k["name"] for k in checks[nxt] if not k["met"]] if nxt else []
    say = {"manual": "Manual only: you fire this anchor yourself.",
           "suggest": "The device may suggest this anchor when it detects stress; you confirm.",
           "auto": "The device may fire this anchor by itself, within the safety limits.",
           "pressure": "Automatic, including during your pressure practice."}[stage]
    return {"anchor": anchor["id"], "stage": stage, "stage_name": STAGE_NAMES[stage], "next": nxt,
            "needs": needs, "checks": checks, "say": say, "strength": s["status"], "risk": c["risk"], "wear": w, "false_alarms": fa}


def may_fire(anchor: dict, mode: str, offers: list, now=0, optins=None, history=None, consents=None) -> dict:
    """Ask the gate before the device offers (mode "suggest") or fires (mode "auto" or "pressure") an anchor."""
    g = gate(anchor, offers, now, optins, history)
    allowed = STAGES.index(g["stage"]) >= STAGES.index(mode)
    reasons = [] if allowed else ["this anchor is at stage " + g["stage_name"].lower() + "; " + mode + " needs: " + "; ".join(
        k["name"].lower() for k in g["checks"][mode] if not k["met"])]
    if allowed and mode in ("auto", "pressure") and not has_consent(consents or [], "automatic_firing", now):
        allowed, reasons = False, ["automatic firing has no consent on record"]
    flag = BELOW_AWARENESS["automatic_firing"] if mode in ("auto", "pressure") else None
    return {"decision": "allow" if allowed else "deny", "mode": mode, "stage": g["stage"], "reasons": reasons, "flag": flag}


# ---------------------------------------------------------------- consent, flags, audit

def give_consent(consents: list, scope: str, by: str, ts, note="") -> dict:
    if scope not in CONSENT_SCOPES:
        raise ValueError("scope must be one of " + ", ".join(CONSENT_SCOPES))
    c = {"scope": scope, "by": by, "given": ts, "withdrawn": None, "note": note}
    consents.append(c)
    return c


def withdraw_consent(consents: list, scope: str, ts) -> int:
    n = 0
    for c in consents:
        if c["scope"] == scope and c["withdrawn"] is None:
            c["withdrawn"] = ts
            n += 1
    return n


def has_consent(consents: list, scope: str, now=0) -> bool:
    return any(c["scope"] == scope and c["given"] <= now and (c["withdrawn"] is None or c["withdrawn"] > now) for c in consents)


def flag(kind: str):
    """The visible label for anything that works below the person's awareness, or None."""
    return BELOW_AWARENESS.get(kind)


def audit(log: list, ts, actor: str, action: str, anchor=None, decision=None, reasons=None, flag_=None) -> dict:
    e = {"ts": ts, "actor": actor, "action": action, "anchor": anchor, "decision": decision, "reasons": list(reasons or []), "flag": flag_}
    log.append(e)
    return e


def audit_summary(log: list, since=0) -> dict:
    rows = [e for e in log if e["ts"] >= since]
    by = {}
    for e in rows:
        k = e["action"] + ":" + (e["decision"] or "none")
        by[k] = by.get(k, 0) + 1
    return {"entries": len(rows), "automatic": sum(1 for e in rows if e["actor"] == "device"),
            "denied": sum(1 for e in rows if e["decision"] == "deny"), "flagged": sum(1 for e in rows if e["flag"]),
            "by": {k: by[k] for k in sorted(by)}}


# ---------------------------------------------------------------- simulation

def simulate(kind: str, seed: int, days=60, use_gate=True, detector_precision=0.85) -> dict:
    """One simulated person and anchor over `days`. Pairing once a day for the first 10 days, a probe every other day
    (one sham in three), three stress detections a day. With the gate, the device suggests or fires only at the stage
    the gate allows; without it, the device fires automatically from day one. `contaminated` anchors meet an outside
    stressor from day 25 (for example a conflict), which pulls their strength negative."""
    body = P.SimBody(seed=seed, ceiling={"strong": 22.0, "weak": 2.0, "none": 0.0, "contaminated": 22.0}[kind])
    a = P.make_anchor("a", "Sim", "🦁", "..-", "redirection")
    rng, offers, consents, log = P.Rng(seed * 7 + 1), [], [], []
    give_consent(consents, "automatic_firing", "person", 0)
    hist, auto_since, out = {}, None, {"unhelpful_auto": 0, "helpful_auto": 0, "suggested": 0, "auto_day": None, "demoted_day": None, "demotions": []}
    for d in range(days):
        t = d * 86400
        if d < 10 or (d % 7 == 0):
            body.pair()
            P.add_capture(a, {"source": "self_tap"}, None, t + 100)
        if kind == "contaminated" and d >= 25:
            for _ in range(2):
                body.stress_use()
        if d % 2 == 1:
            kd = "sham" if (d // 2) % 3 == 2 else "cue"
            pr = body.probe(kd)
            pr["ts"] = t + 200
            P.add_probe(a, pr)
        for k in range(3):
            ts = t + 3600 * (9 + 4 * k)
            stress = rng.u() < detector_precision
            effective = body.v >= P.THRESHOLD["rmssd_pct"]
            if use_gate:
                mode = "auto" if may_fire(a, "auto", offers, ts, None, {"auto_since": auto_since}, consents)["decision"] == "allow" else (
                    "suggest" if may_fire(a, "suggest", offers, ts)["decision"] == "allow" else None)
            else:
                mode = "auto"
            if mode is None:
                continue
            if mode == "auto":
                if auto_since is None:
                    auto_since = ts
                    out["auto_day"] = out["auto_day"] if out["auto_day"] is not None else d
                if not (stress and effective):
                    out["unhelpful_auto"] += 1
                else:
                    out["helpful_auto"] += 1
            else:
                out["suggested"] += 1
                if auto_since is not None:
                    out["demotions"].append(d)
                    if out["demoted_day"] is None:
                        out["demoted_day"] = d
                auto_since = None
            outcome = ("helped" if effective else "dismissed") if stress else "not_needed"
            record_offer(offers, "a", ts, outcome, mode, stress)
            P.add_use(a, ts, stress)
            audit(log, ts, "device", mode, "a", "allow")
        if use_gate and auto_since is not None:
            g = gate(a, offers, t + 86399, None, {"auto_since": auto_since})
            if g["stage"] in ("manual", "suggest"):
                out["demotions"].append(d)
                if out["demoted_day"] is None:
                    out["demoted_day"] = d
                auto_since = None
    out["final_stage"] = gate(a, offers, days * 86400, None, {"auto_since": auto_since})["stage"] if use_gate else "auto"
    return out


def evaluate(n_each=40) -> dict:
    kinds = ("strong", "weak", "none", "contaminated")
    res = {}
    for g in (True, False):
        for kind in kinds:
            rows = [simulate(kind, 100 * (kinds.index(kind) + 1) + i, use_gate=g) for i in range(n_each)]
            reached = [r for r in rows if r["auto_day"] is not None]
            res[(g, kind)] = {"reached_auto": _v(r1(len(reached) / n_each * 100)),
                              "final_auto": _v(r1(sum(1 for r in rows if r["final_stage"] == "auto") / n_each * 100)),
                              "auto_day": _v(r1(sum(r["auto_day"] for r in reached) / len(reached))) if reached else None,
                              "unhelpful_auto": _v(r1(sum(r["unhelpful_auto"] for r in rows) / n_each)),
                              "helpful_auto": _v(r1(sum(r["helpful_auto"] for r in rows) / n_each)),
                              "demoted": _v(r1(sum(1 for r in rows if any(x >= 25 for x in r["demotions"])) / n_each * 100)),
                              "demoted_after": _v(r1(sum(min(x for x in r["demotions"] if x >= 25) - 25 for r in rows if any(x >= 25 for x in r["demotions"])) /
                                                    max(1, sum(1 for r in rows if any(x >= 25 for x in r["demotions"])))))}
    weak_det = [simulate("strong", 100 + i, detector_precision=0.7) for i in range(n_each)]
    res["detector70"] = {"final_auto": _v(r1(sum(1 for r in weak_det if r["final_stage"] == "auto") / n_each * 100))}
    res["final_auto_strong"] = _v(r1(sum(1 for i in range(n_each) if simulate("strong", 100 + i)["final_stage"] == "auto") / n_each * 100))
    return {"n_each": n_each, "res": res}


def report(ev: dict) -> str:
    L = ["# The autonomy gate on simulated people", "",
         "Generated by `python -m rsso.gate --evaluate`. Simulated people over 60 days, each with one anchor of a known kind: "
         "strong, weak (below the smallest effect that counts), no effect, or strong until an outside stressor from day 25 pulls it negative (contaminated). The anchor "
         "is paired at a peak daily for 10 days and weekly after, probed every other day (one sham in three), and the device "
         "detects stress three times a day with 85% precision. With the gate, the device suggests or fires only at the stage the "
         "gate allows; without it, it fires automatically from day one. Built and tested in simulation; effect unproven in people.", "",
         "| Anchor | Reached automatic (gate) | Day reached | Unhelpful automatic firings, with gate | Without gate | Helpful automatic firings, with gate | Without gate |",
         "|---|---|---|---|---|---|---|"]
    names = {"strong": "Strong", "weak": "Weak", "none": "No effect", "contaminated": "Contaminated from day 25"}
    for kind in ("strong", "weak", "none", "contaminated"):
        g, n = ev["res"][(True, kind)], ev["res"][(False, kind)]
        L.append(f"| {names[kind]} | {g['reached_auto']}% | {g['auto_day'] if g['auto_day'] is not None else '—'} | {g['unhelpful_auto']} | "
                 f"{n['unhelpful_auto']} | {g['helpful_auto']} | {n['helpful_auto']} |")
    c = ev["res"][(True, "contaminated")]
    L += ["", f"**Closing again.** After the outside stressor began on day 25, contaminated anchors lost automatic use in {c['demoted']}% "
          f"of simulated people, " + ("within a day" if c['demoted_after'] < 1 else f"{c['demoted_after']} days after it began on average")
          + f" (the rest were already back at suggest when it began); {c['final_auto']}% were automatic at day 60.", "",
          "Reading: the gate trades a slower start (automatic firing begins after training, proof and confirmed offers) for far "
          "fewer firings that cannot help: anchors with no effect never fire on their own, weak ones rarely and briefly, and a contaminated "
          "anchor loses automatic use within days. Unhelpful firings that remain come from the detector's false alarms; "
          "a better detector lowers them further.", "",
          f"**Detector quality matters.** Strong anchors were still automatic at day 60 in {ev['res']['final_auto_strong']}% of "
          f"simulated people with an 85%-precise detector, and in {ev['res']['detector70']['final_auto']}% with a 70%-precise one: "
          "the gate keeps a noisy detector at suggest, where the person confirms each offer.", ""]
    return "\n".join(L)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["--evaluate"]:
        import pathlib
        path = pathlib.Path(__file__).resolve().parents[1] / "results" / "gate.md"
        path.write_text(report(evaluate()), encoding="utf-8")
        print(f"wrote {path}")
        return 0
    print("usage: python -m rsso.gate --evaluate")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
