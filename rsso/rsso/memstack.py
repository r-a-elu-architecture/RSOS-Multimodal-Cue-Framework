"""MEMSTACK: tier memory and progress toward a reflex.

From a person's run log (protocol player CSV or rsx RunRecord) and weekly automaticity ratings, MEMSTACK
keeps, for each tier (or program, when no tier is named):

  * runs        practice runs (no trigger) and trigger-paired runs, completed and stopped
  * effect      mean distress drop and agency gain, first runs vs latest runs
  * strength    model estimate of the bundle's associative strength and of the trigger's value
                (Rescorla-Wagner, rsx.conditioning; an estimate from a model, not a measurement)
  * habit       a fitted habit curve on latency: latency_n = 1 s + (L0 - 1 s) * (1 - eta)^n,
                and the estimated number of further trigger runs until latency reaches 3 s
  * reflex      the spec's reflex criterion (spec/OVERRIDE_PROTOCOL.md §8): SRBAI mean >= 4 for two
                consecutive weeks and median latency <= 3 s over at least 10 real triggers

Snapshots (JSON with a schema version and a SHA-256 checksum) move the memory between devices and allow
rollback. docs/js/memstack.js computes the same summary in the player; rsso/tests/test_memstack.py checks
that both give identical numbers.
"""
from __future__ import annotations

import hashlib
import json
import math

SCHEMA = "rsos-memstack/1"
ALPHA = {"V": 0.30, "A": 0.25, "K": 0.30, "trigger": 0.30}   # rsx.conditioning.DEFAULT_ALPHA, VAK bundle
BETA = 0.5
LAT_MIN = 1.0
REFLEX_LATENCY = 3.0
ETA_GRID = [round(0.005 * k, 3) for k in range(1, 61)]           # 0.005 .. 0.300
L0_GRID = [5.0 * 1.15 ** k for k in range(0, 31)]               # 5 s .. ~331 s


def _num(v):
    try:
        f = float(v)
        return f if math.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def _median(xs):
    s = sorted(xs); n = len(s)
    if not n:
        return None
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def _mean(xs):
    return sum(xs) / len(xs) if xs else None


def fit_habit(latencies: list[float]) -> dict | None:
    """Least-squares fit of log latency on the habit curve by grid search (deterministic, identical in JS)."""
    lat = [max(x, 0.5) for x in latencies]
    if len(lat) < 5:
        return None
    best = None
    for eta in ETA_GRID:
        for L0 in L0_GRID:
            sse = 0.0
            for n, y in enumerate(lat):
                pred = LAT_MIN + (L0 - LAT_MIN) * (1 - eta) ** n
                sse += (math.log(y) - math.log(pred)) ** 2
            if best is None or sse < best[0] - 1e-12:
                best = (sse, eta, L0)
    sse, eta, L0 = best
    n_now = len(lat)
    pred_now = LAT_MIN + (L0 - LAT_MIN) * (1 - eta) ** n_now
    if pred_now <= REFLEX_LATENCY:
        remaining = 0
    else:
        need = math.log((REFLEX_LATENCY - LAT_MIN) / (L0 - LAT_MIN)) / math.log(1 - eta)
        remaining = max(0, math.ceil(need - n_now))
    return {"eta": eta, "L0": round(L0, 3), "predicted_latency_now": round(pred_now, 3),
            "runs_to_reflex": remaining, "rmse_log": round(math.sqrt(sse / n_now), 4)}


def summarize(runs: list[dict], srbai: list[dict] | None = None) -> dict:
    """runs: dicts with run-log columns, in time order (or with 'timestamp'). srbai: {week, srbai}."""
    rows = sorted(runs, key=lambda r: _num(r.get("timestamp")) or 0)
    groups: dict[str, list] = {}
    for r in rows:
        key = (r.get("tier") or "").strip() or (r.get("protocol") or "unknown")
        groups.setdefault(key, []).append(r)
    tiers = {}
    for key, rs in groups.items():
        V = {"V": 0.0, "A": 0.0, "K": 0.0, "trigger": -0.8}
        practice = paired = completed = 0
        drops, gains, lats = [], [], []
        for r in rs:
            done = str(r.get("completed", "1")) in ("1", "1.0", "True", "true")
            completed += done
            is_trigger = bool((r.get("trigger_channel") or "").strip()) or r.get("trigger") == "device"
            if done:
                present = ["V", "A", "K"] + (["trigger"] if is_trigger else [])
                err = 1.0 - sum(V[c] for c in present)
                for c in present:
                    V[c] += ALPHA[c] * BETA * err
                if is_trigger:
                    paired += 1
                else:
                    practice += 1
            sb, sa, ab, aa = (_num(r.get(k)) for k in ("sud_before", "sud_after", "agency_before", "agency_after"))
            if done and sb is not None and sa is not None:
                drops.append(sb - sa)
            if done and ab is not None and aa is not None:
                gains.append(aa - ab)
            lat = _num(r.get("latency_s"))
            if done and is_trigger and lat is not None:
                lats.append(lat)
        k = min(5, len(drops))
        tiers[key] = {
            "runs": len(rs), "completed": completed, "practice": practice, "trigger_runs": paired,
            "distress_drop_first": round(_mean(drops[:k]), 3) if k else None,
            "distress_drop_latest": round(_mean(drops[-k:]), 3) if k else None,
            "agency_gain_latest": round(_mean(gains[-min(5, len(gains)):]), 3) if gains else None,
            "bundle_strength": round(min(1.0, max(0.0, V["V"] + V["A"] + V["K"])), 4),
            "trigger_value": round(V["trigger"], 4),
            "median_latency_last10": round(_median(lats[-10:]), 3) if lats else None,
            "real_triggers": len(lats),
            "habit": fit_habit(lats),
        }
    weeks = sorted(((int(_num(w["week"])), _num(w["srbai"])) for w in (srbai or []) if _num(w.get("srbai")) is not None))
    srbai_ok = any(a[1] >= 4 and b[1] >= 4 and b[0] == a[0] + 1 for a, b in zip(weeks, weeks[1:]))
    for t in tiers.values():
        lat_ok = t["real_triggers"] >= 10 and t["median_latency_last10"] is not None and t["median_latency_last10"] <= REFLEX_LATENCY
        t["reflex"] = {"srbai_two_weeks_at_4": srbai_ok, "latency_at_or_below_3s": lat_ok, "met": srbai_ok and lat_ok}
    return {"schema": SCHEMA, "tiers": tiers, "srbai": [{"week": w, "srbai": s} for w, s in weeks]}


def _norm(o):
    if isinstance(o, float) and o.is_integer():
        return int(o)                      # 5.0 and 5 hash the same, as in JavaScript
    if isinstance(o, dict):
        return {k: _norm(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_norm(v) for v in o]
    return o


def _canonical(obj) -> str:
    return json.dumps(_norm(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def snapshot(runs: list[dict], srbai: list[dict] | None = None) -> dict:
    """A portable memory snapshot: the raw records plus a checksum over them."""
    body = {"schema": SCHEMA, "runs": runs, "srbai": srbai or []}
    return dict(body, sha256=hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest())


def restore(snap: dict) -> tuple[list[dict], list[dict]]:
    if snap.get("schema") != SCHEMA:
        raise ValueError(f"unsupported snapshot schema {snap.get('schema')!r}")
    body = {k: snap[k] for k in ("schema", "runs", "srbai")}
    if hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest() != snap.get("sha256"):
        raise ValueError("snapshot checksum does not match: the file was changed or damaged")
    return snap["runs"], snap["srbai"]


def merge(a: list[dict], b: list[dict]) -> list[dict]:
    """Union of two run lists without duplicates (same timestamp and protocol), in time order."""
    seen, out = set(), []
    for r in sorted(a + b, key=lambda r: _num(r.get("timestamp")) or 0):
        k = (str(r.get("timestamp")), r.get("protocol"), r.get("participant"))
        if k not in seen:
            seen.add(k); out.append(r)
    return out
