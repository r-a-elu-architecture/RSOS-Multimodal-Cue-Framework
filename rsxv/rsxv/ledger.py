"""Clause-to-Body Causal Ledger.

Question it answers: which part of what a person said moved their body, by how much, and how sure are we?

1. Units. The translator gives every vector of a message a clause ID (m1·v3). An operator carries the
   clause IDs it came from (lineage). Clause-derived operators are the randomised units; operators that
   are required for safety or structure (gate, settle, close, coverage fill) are never randomised.
2. Micro-randomisation. Inside every phase, each 10-second cycle is a decision point. At each one, every
   eligible clause is switched on with probability p (default 0.6), independently. An operator runs in
   a cycle if any of its clauses is on. The laws still apply: consent must include "randomisation",
   NullSafe stops the session, and nothing is randomised in the gate or the close.
3. Estimate. For each outcome (change in distress, arousal, agency and the target layer over the cycle),
   a weighted-and-centred least-squares regression on the centred indicators (A - p), with the cycle's
   starting arousal and distress as covariates, gives each clause's causal excursion effect with a 95% interval that
   is robust to dependence within a session (cluster-robust by session). This is the standard estimator of micro-randomised trials, applied to clauses of the
   person's own message instead of to fixed app prompts.
4. Back into language. Effects are rendered as plain sentences, quoting the clause.
5. Into the next generation. `next_from_ledger` drops operators whose every clause made distress worse,
   with an interval excluding zero, and keeps those that helped.

All numbers come from simulated people unless stated otherwise. `planted` lets a test add known effects
per clause; with `inert=True` the operators themselves have no effect, so the planted effects are the
whole truth and the estimator's recovery can be checked exactly.
"""
from __future__ import annotations
import copy
import math
import random
import numpy as np
from . import ops as O
from . import sim as S
from . import lang as Lg

CYCLE = 10
OUTCOMES = ("distress", "arousal", "agency", "layer")


def clause_units(prog: dict, lineage: dict) -> dict:
    """operator -> clause ids, for clause-derived operators only (ids look like m1·v3)."""
    out = {}
    for op, src in lineage.items():
        ids = [s for s in src if "·v" in s]
        fam = O.OPS[op][0]
        if ids and fam not in ("safety", "export"):
            out[op] = ids
    return out


def _target_layers(ops):
    return {O.OPS[o][1] for o in ops if O.OPS[o][1] in O.LAYERS}


def session(prog: dict, lineage: dict, person: dict, ctx: dict | None = None, p: float = 0.6,
            planted: dict | None = None, model: dict | None = None, seed: int = 1, inert: bool = False) -> dict:
    """Run one micro-randomised session. Returns the cycle records and how the session ended."""
    ctx = dict(ctx or {})
    if "randomisation" not in ctx.get("consent", ()):
        return {"status": "refused", "why": "consent does not include randomisation", "cycles": []}
    rng = random.Random(seed)
    body = S.Body({**person, "sham": 0.0} if inert else person, rng, model or S.FULL, sham=inert)
    body.hf = S.hour_factor(person, ctx.get("hour"))
    units = clause_units(prog, lineage)
    base_d = body.s["distress"]
    cycles, status = [], "done"
    for b in prog["blocks"]:
        ops_all = [v["op"] for v in b["vectors"]]
        if b["kind"] in ("GATE", "CLOSE"):
            for _ in range(5 if b["kind"] == "GATE" else 20):
                body.step(ops_all)
            continue
        elig = sorted({c for o in ops_all if o in units for c in units[o]})
        targets = _target_layers(ops_all)
        n_cyc = max(1, b["max_s"] // CYCLE)
        for k in range(n_cyc):
            A = {c: int(rng.random() < p) for c in elig}
            active = [o for o in ops_all if o not in units or any(A[c] for c in units[o])]
            start = dict(body.s); lay0 = sum(body.layer[t] for t in targets) if targets else 0.0
            for _ in range(CYCLE):
                body.step(active)
                for c, on in A.items():
                    if on and planted and c in planted:
                        for var, d in planted[c].items():
                            body.s[var] = min(10 if var in ("distress", "agency") else 1, max(0, body.s[var] + d))
            lay1 = sum(body.layer[t] for t in targets) if targets else 0.0
            cycles.append({"session": seed, "block": b["name"], "k": k, "A": A, "arousal0": start["arousal"],
                           "distress0": start["distress"],
                           "distress": body.s["distress"] - start["distress"], "arousal": body.s["arousal"] - start["arousal"],
                           "agency": body.s["agency"] - start["agency"], "layer": lay1 - lay0})
            if body.s["distress"] - base_d >= 2.5 or body.s["distress"] >= 9:
                status = "stopped"
                break
        if status == "stopped":
            break
    return {"status": status, "cycles": cycles}


def estimate(cycles: list[dict], clauses: list[str], p: float = 0.6, outcome: str = "distress") -> dict:
    """Causal excursion effect of each clause on one outcome per cycle, with a robust 95% interval."""
    rows = [c for c in cycles if c["A"]]
    if len(rows) < len(clauses) + 5:
        return {}
    NC = 3                                              # intercept, starting arousal, starting distress
    X = np.zeros((len(rows), NC + len(clauses)))
    y = np.array([r[outcome] for r in rows], dtype=float)
    X[:, 0] = 1.0
    X[:, 1] = [r["arousal0"] for r in rows]
    X[:, 2] = [r.get("distress0", 0.0) for r in rows]
    for j, c in enumerate(clauses):
        X[:, NC + j] = [(r["A"][c] - p) if c in r["A"] else 0.0 for r in rows]
    keep = list(range(NC)) + [NC + j for j in range(len(clauses)) if np.any(X[:, NC + j] != 0)]
    Xk = X[:, keep]
    XtX_inv = np.linalg.pinv(Xk.T @ Xk)
    beta = XtX_inv @ Xk.T @ y
    resid = y - Xk @ beta
    n, k = Xk.shape
    groups = {}
    for i, r in enumerate(rows):                       # cluster-robust by session (CR1)
        groups.setdefault(r.get("session", i), []).append(i)
    G = len(groups)
    meat = np.zeros((k, k))
    for idx in groups.values():
        u = (Xk[idx] * resid[idx, None]).sum(axis=0)
        meat += np.outer(u, u)
    meat *= (G / max(1, G - 1)) * ((n - 1) / max(1, n - k))
    se = np.sqrt(np.maximum(np.diag(XtX_inv @ meat @ XtX_inv), 0))
    out = {}
    for pos, col in enumerate(keep):
        if col < NC:
            continue
        c = clauses[col - NC]
        n_on = sum(1 for r in rows if r["A"].get(c) == 1); n_off = sum(1 for r in rows if r["A"].get(c) == 0)
        out[c] = {"effect": float(beta[pos]), "se": float(se[pos]), "lo": float(beta[pos] - 1.96 * se[pos]),
                  "hi": float(beta[pos] + 1.96 * se[pos]), "n_on": n_on, "n_off": n_off}
    return out


def build(prog: dict, lineage: dict, person: dict, sessions: int = 20, ctx: dict | None = None, p: float = 0.6,
          planted: dict | None = None, model: dict | None = None, seed: int = 1, texts: dict | None = None,
          inert: bool = False) -> dict:
    """Run several micro-randomised sessions for one person and build their ledger."""
    allc, ended = [], []
    q = dict(person)
    for s in range(sessions):
        r = session(prog, lineage, q, ctx, p, planted, model, seed * 1000 + s, inert)
        if r["status"] == "refused":
            return {"status": "refused", "why": r["why"]}
        allc += r["cycles"]; ended.append(r["status"])
    units = clause_units(prog, lineage)
    clauses = sorted({c for ids in units.values() for c in ids}, key=lambda c: (c.split("·")[0], int(c.split("·v")[1])))
    effects = {o: estimate(allc, clauses, p, o) for o in OUTCOMES}
    entries = []
    for c in clauses:
        e = {"clause": c, "text": (texts or {}).get(c, ""), "operators": sorted(o for o, ids in units.items() if c in ids)}
        for o in OUTCOMES:
            if c in effects[o]:
                e[o] = {k: round(v, 4) if isinstance(v, float) else v for k, v in effects[o][c].items()}
        entries.append(e)
    return {"status": "done", "sessions": sessions, "stopped_sessions": ended.count("stopped"), "cycles": len(allc),
            "p": p, "entries": entries}


def sentences(ledger: dict, outcome: str = "distress", top: int = 5) -> list[str]:
    """Plain-language findings, strongest first, only where the interval excludes zero."""
    word = {"distress": ("lowered distress", "raised distress"), "arousal": ("calmed the body", "raised arousal"),
            "agency": ("raised agency", "lowered agency"), "layer": ("activated its target layer", "lowered layer activation")}
    good_neg = outcome in ("distress", "arousal")
    found = []
    for e in ledger.get("entries", []):
        x = e.get(outcome)
        if not x or (x["lo"] <= 0 <= x["hi"]):
            continue
        helped = (x["effect"] < 0) if good_neg else (x["effect"] > 0)
        verb = word[outcome][0] if helped else word[outcome][1]
        label = f"“{e['text']}”" if e["text"] else e["clause"]
        found.append((abs(x["effect"]), f"{label} ({e['clause']}) {verb} by {abs(x['effect']):.2f} per 10 s "
                                        f"(95% interval {x['lo']:+.2f} to {x['hi']:+.2f})"))
    return [s for _, s in sorted(found, reverse=True)[:top]] or ["No clause had an effect whose interval excludes zero."]


def next_from_ledger(prog: dict, lineage: dict, ledger: dict) -> dict:
    """Drop operators all of whose clauses made distress worse (interval above zero); keep everything else."""
    harm = {e["clause"] for e in ledger.get("entries", []) if e.get("distress") and e["distress"]["lo"] > 0}
    units = clause_units(prog, lineage)
    drop = {o for o, ids in units.items() if ids and all(c in harm for c in ids)}
    n = copy.deepcopy(prog)
    for b in n["blocks"]:
        b["vectors"] = [v for v in b["vectors"] if v["op"] not in drop]
    n["blocks"] = [b for b in n["blocks"] if b["vectors"] or b["kind"] != "PHASE"]
    try:
        parsed = Lg.parse(Lg.to_text(n))
    except Lg.RSXVError as err:          # too few vectors left: keep the original, report why
        return {"program": prog, "dropped": [], "note": f"not applied: {err}"}
    return {"program": parsed, "dropped": sorted(drop), "note": f"dropped {len(drop)} operator(s) whose clauses all raised distress"}


def to_audit(store, subject: str, ledger: dict):
    """Append the ledger to the hash-chained Resonance Audit Log."""
    return store._append("ledger", subject, {"entries": ledger["entries"], "cycles": ledger["cycles"], "p": ledger["p"]})
