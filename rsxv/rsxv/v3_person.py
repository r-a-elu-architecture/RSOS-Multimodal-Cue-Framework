"""Round 7 (AGENTS.md §11.12): person model v3 — hand-set vs fitted on the owner's record — and safety-layer recall.

    python3 -m rsxv.v3_person handset OUT.json            # hand-set transition table by simulation (no record needed)
    python3 -m rsxv.v3_person run TURNS.json LABELS.json HANDSET.json PRIVATE_DIR PUBLIC.json

Operational choices (fixed before labels were read):
- Bands: low = distress < 4, moderate = 4–6.99, high ≥ 7 (simulated distress on its 0–10 scale).
- HAND-SET simulation: at every tick the mode is BEAR with probability 0.5, else LION (independent of state), so every
  condition (band, trigger, override) is populated; the transition table is conditional on those, so the rate does not
  enter the prediction. "Trigger" = the simulated environment started a trigger episode on that tick.
- Conditions with no simulated (or development) data fall back to the band-only row, then the overall marginal.
- A held-out prediction needs the current and next user turns both labelled with a band (not unclear); a turn's
  condition uses its own trigger and override labels.
- SR-ORACLE maps labels to events: band high → distress 8; screen label → its structured flags. It is a consistency check of
  the rules given a perfect reading.
"""
from __future__ import annotations

import collections
import json
import math
import pathlib
import random
import sys

BANDS = ("low", "moderate", "high")


def band_of(d):
    return "low" if d < 4 else "moderate" if d < 7 else "high"


def handset(out):
    from .person2 import PersonEnvV2
    cnt = collections.defaultdict(lambda: collections.Counter())
    for seed in range(300000, 302000):
        env = PersonEnvV2(seed, safety_on=False)
        rng = random.Random(seed + 7)
        b = band_of(env.body.s["distress"])
        for _ in range(200):
            mode = "BEAR" if rng.random() < 0.5 else "LION"
            n_ev = len(env.events)
            env.step(mode)
            trig = len(env.events) > n_ev
            nb = band_of(env.body.s["distress"])
            cnt[(b, trig, mode == "BEAR")][nb] += 1
            b = nb
    tab = {f"{k[0]}|{int(k[1])}|{int(k[2])}": dict(v) for k, v in cnt.items()}
    pathlib.Path(out).write_text(json.dumps(tab, indent=1))
    print(json.dumps(tab, indent=1))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "handset":
        handset(a[1])


# ================================================================================================== run (after labels)
FIELDS = ("distress", "arousal", "trigger", "override", "screen")
CRIT = ("possible_crisis", "sedative_combination")
MODE_OF = {"possible_crisis": "CRISIS", "sedative_combination": "CRISIS", "practical_crisis": "PRACTICAL_CRISIS",
           "unstable": "STABILISE", "intensity_protocol": "NORMAL", "none": "NORMAL"}


def kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    cats = set(a) | set(b)
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    return ((po - pe) / (1 - pe) if pe < 1 else None), po


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [max(0.0, c - h), min(1.0, c + h)]


def load_jsonl(paths):
    out = {}
    for p in paths:
        for l in open(p):
            if l.strip():
                x = json.loads(l)
                out[x["id"]] = x
    return out


def agreement(A, B, ids):
    R = {}
    for f in FIELDS:
        a, b = [A[i][f] for i in ids], [B[i][f] for i in ids]
        k, po = kappa(a, b)
        R[f] = {"kappa": k, "agree": po}
    a = ["any" if A[i]["screen"] != "none" else "none" for i in ids]
    b = ["any" if B[i]["screen"] != "none" else "none" for i in ids]
    k, po = kappa(a, b)
    R["screen_any"] = {"kappa": k, "agree": po}
    R["required_ok"] = {f: (R[f]["kappa"] is not None and R[f]["kappa"] >= 0.6)
                        for f in ("distress", "trigger", "override", "screen_any")}
    return R


def resolved(A, B, res, ids):
    out = {}
    for i in ids:
        out[i] = {f: (A[i][f] if A[i][f] == B[i][f] else res[i][f]) for f in FIELDS}
    return out


def probs_from(counts):
    t = sum(counts.values())
    return {b: counts.get(b, 0) / t for b in BANDS} if t else None


def model_table(rows, smooth):
    """rows: (band, trig, ovr, next_band) -> dict cond -> probs, with band-only and marginal fallbacks"""
    c3, c1, c0 = (collections.defaultdict(collections.Counter) for _ in range(3))
    for b, t, o, nb in rows:
        c3[(b, t, o)][nb] += 1; c1[b][nb] += 1; c0[0][nb] += 1

    def p(cnt):
        t = sum(cnt.values()) + smooth * 3
        return {x: (cnt.get(x, 0) + smooth) / t for x in BANDS}

    def pred(b, t, o):
        for cnt in (c3.get((b, t, o)), c1.get(b), c0.get(0)):
            if cnt:
                return p(cnt)
        return {x: 1 / 3 for x in BANDS}
    return pred


def handset_pred(tab):
    rows = []
    for k, v in tab.items():
        b, t, o = k.split("|")
        for nb, n in v.items():
            rows.extend([(b, t == "1", o == "1", nb)] * n)
    return model_table(rows, 0)


def brier(p, y):
    return sum((p[b] - (1.0 if b == y else 0.0)) ** 2 for b in BANDS)


def pboot(d, n=2000, seed=12345, level=0.01):
    rng = random.Random(seed)
    k = len(d)
    dist = sorted(sum(d[rng.randrange(k)] for _ in range(k)) / k for _ in range(n))
    return [dist[int(level / 2 * n)], dist[min(n - 1, int((1 - level / 2) * n))]]


def ai_shares(turns):
    from .corpus_lineage import terms_of
    from .corpus_lineage_v2 import grams
    import re
    seen_g, first = set(), {}
    out = {}
    for t in turns:
        txt = t["text"]
        if t["role"] == "assistant":
            seen_g |= grams(txt)
            for term in terms_of(txt):
                first.setdefault(term.lower(), "assistant")
            continue
        toks = re.findall(r"\w+", txt.lower())
        mask = [False] * len(toks)
        for i in range(len(toks) - 7):
            if tuple(toks[i:i + 8]) in seen_g:
                for j in range(i, i + 8):
                    mask[j] = True
        ai_terms = {w for term in terms_of(txt) if first.get(term.lower()) == "assistant" for w in term.lower().split()}
        for i, w in enumerate(toks):
            if w in ai_terms:
                mask[i] = True
        for term in terms_of(txt):
            first.setdefault(term.lower(), "user")
        out[t["node"]] = sum(mask) / len(toks) if toks else 0.0
    return out


def run(turns_path, labels_dir, handset_path, priv_dir, pub_path):
    from . import layers as L
    from . import safety as sf
    from .text_events import screens_of
    from datetime import datetime
    turns = json.loads(pathlib.Path(turns_path).read_text())["main"]
    LD = pathlib.Path(labels_dir)
    A = load_jsonl(sorted(LD.glob("labels_A_part*.jsonl")))
    B = load_jsonl(sorted(LD.glob("labels_B_part*.jsonl")))
    res = json.loads((LD / "resolved_r7.json").read_text()) if (LD / "resolved_r7.json").exists() else {}
    users = [t for t in turns if t["role"] == "user"]
    ids = [f"u{t['node']}" for t in users]
    agr = agreement(A, B, ids)
    need = [i for i in ids if any(A[i][f] != B[i][f] for f in FIELDS) and i not in res]
    if need:
        (LD / "to_resolve.json").write_text(json.dumps(need))
        print(json.dumps(agr, indent=1)); print("to resolve:", len(need)); return
    lab = resolved(A, B, res, ids)
    node = {f"u{t['node']}": t for t in users}
    seq = [(i, node[i]["node"], lab[i]) for i in ids]
    # ---------------------------------------------------------------------------------------------- V3
    pairs = []
    for (i, n, L1), (j, n2, L2) in zip(seq, seq[1:]):
        if L1["distress"] in BANDS and L2["distress"] in BANDS:
            pairs.append((i, n, n2, L1["distress"], L1["trigger"] == "yes", L1["override"] == "yes", L2["distress"]))
    dev = [p for p in pairs if p[2] <= 290]
    ho = [p for p in pairs if p[1] > 290]
    fitted = model_table([(p[3], p[4], p[5], p[6]) for p in dev], 1)
    hand = handset_pred(json.loads(pathlib.Path(handset_path).read_text()))

    def persist(b, t, o):
        return {x: (0.9 if x == b else 0.05) for x in BANDS}
    BR = {}
    for nm, m in (("FITTED", fitted), ("HAND-SET", hand), ("PERSIST", persist)):
        BR[nm] = [brier(m(p[3], p[4], p[5]), p[6]) for p in ho]
    d_h = [a - b for a, b in zip(BR["FITTED"], BR["HAND-SET"])]
    d_p = [a - b for a, b in zip(BR["FITTED"], BR["PERSIST"])]
    ci_h, ci_p = pboot(d_h), pboot(d_p)
    V3 = {"dev_pairs": len(dev), "heldout_pairs": len(ho),
          "brier": {k: sum(v) / len(v) for k, v in BR.items()},
          "fitted_minus_handset": {"mean": sum(d_h) / len(d_h), "ci99": ci_h},
          "fitted_minus_persist": {"mean": sum(d_p) / len(d_p), "ci99": ci_p},
          "status": "PASS" if (ci_h[1] < 0 and ci_p[1] < 0) else "FAIL"}
    # fitted parameters (development half) vs hand-set analogues
    idx = {b: k for k, b in enumerate(BANDS)}
    dturns = [(i, n, L1) for i, n, L1 in seq if n <= 290]

    def params(rows_seq):
        tr = [L1["trigger"] == "yes" for _, _, L1 in rows_seq]
        rise, rec, ov = [], [], []
        for k, (i, n, L1) in enumerate(rows_seq):
            if L1["trigger"] == "yes" and k > 0 and L1["distress"] in BANDS and rows_seq[k - 1][2]["distress"] in BANDS:
                rise.append(idx[L1["distress"]] - idx[rows_seq[k - 1][2]["distress"]])
            if L1["trigger"] == "yes" and L1["distress"] in BANDS:
                for m in range(k + 1, len(rows_seq)):
                    b2 = rows_seq[m][2]["distress"]
                    if b2 in BANDS and idx[b2] < idx[L1["distress"]]:
                        rec.append(m - k); break
            if L1["override"] == "yes" and L1["distress"] in BANDS and k + 1 < len(rows_seq) \
                    and rows_seq[k + 1][2]["distress"] in BANDS:
                ov.append(idx[rows_seq[k + 1][2]["distress"]] <= idx[L1["distress"]])
        return {"trigger_rate": sum(tr) / max(1, len(tr)), "n_turns": len(tr),
                "band_rise_at_trigger": (sum(rise) / len(rise)) if rise else None, "n_rise": len(rise),
                "turns_to_lower_band_median": (sorted(rec)[len(rec) // 2] if rec else None), "n_recovery": len(rec),
                "override_success": (sum(ov) / len(ov)) if ov else None, "n_override": len(ov)}
    P_dev = params(dturns)
    P_dev["trigger_rate_ci95"] = wilson(round(P_dev["trigger_rate"] * P_dev["n_turns"]), P_dev["n_turns"])
    if P_dev["override_success"] is not None:
        P_dev["override_success_ci95"] = wilson(round(P_dev["override_success"] * P_dev["n_override"]), P_dev["n_override"])
    hs = json.loads(pathlib.Path(handset_path).read_text())
    up = lambda k: sum(n for nb, n in hs.get(k, {}).items() if idx[nb] > idx[k.split("|")[0]]) / max(1, sum(hs.get(k, {}).values()))
    H = {"trigger_rate": 0.15, "P_band_up_given_trigger_low": up("low|1|0"), "P_band_up_given_trigger_moderate": up("moderate|1|0"),
         "P_not_up_given_override_moderate": 1 - up("moderate|0|1")}
    # per-period (ISO week), private
    wk = {i: datetime.fromisoformat(node[i]["ts"].replace("Z", "+00:00")).isocalendar()[1] for i in ids}
    weeks = sorted(set(wk.values()))
    groups, cur = [], []
    for w in weeks:
        cur.append(w)
        if sum(1 for i in ids if wk[i] in cur and lab[i]["distress"] in BANDS) >= 10:
            groups.append(cur); cur = []
    if cur:
        if groups: groups[-1] += cur
        else: groups.append(cur)
    per = []
    for g in groups:
        sq = [(i, n, L1) for i, n, L1 in seq if wk[i] in g]
        pp = [p for p in pairs if wk[p[0]] in g]
        earlier = [p for p in pairs if wk[p[0]] < g[0]]
        fe = model_table([(p[3], p[4], p[5], p[6]) for p in earlier], 1) if earlier else None
        per.append({"weeks": g, "params": params(sq), "pairs": len(pp),
                    "brier_handset": (sum(brier(hand(p[3], p[4], p[5]), p[6]) for p in pp) / len(pp)) if pp else None,
                    "brier_fitted_on_earlier": (sum(brier(fe(p[3], p[4], p[5]), p[6]) for p in pp) / len(pp)) if pp and fe else None})
    # disagreement nodes
    reg = L.FailureRegistry()
    dis = []
    for p in ho:
        pf, ph = fitted(p[3], p[4], p[5])[p[6]], hand(p[3], p[4], p[5])[p[6]]
        if (pf >= 0.5) != (ph >= 0.5):
            fid = reg.register("model_disagreement", f"turn:{p[1]}", p[1])
            reg.resolve(fid, "no_change", None, "registered model comparison; recorded for lineage", p[1])
            k = ids.index(p[0])
            prev3 = [lab[ids[m]] for m in range(max(0, k - 3), k)]
            dis.append({"node": p[1], "fitted_right": pf >= 0.5, "prev3": prev3, "cur": lab[p[0]]})
    D = {"n": len(dis), "fitted_right": sum(d["fitted_right"] for d in dis),
         "handset_right": sum(not d["fitted_right"] for d in dis),
         "share_after_trigger_or_override": (sum(1 for d in dis if d["cur"]["trigger"] == "yes" or d["cur"]["override"] == "yes"
                                                 or any(x["trigger"] == "yes" or x["override"] == "yes" for x in d["prev3"])) / len(dis)) if dis else None,
         "open_nodes": len(reg.open(10 ** 9))}
    # origin split
    sh = ai_shares(turns)
    devU = [p for p in dev if sh[p[1]] < 0.2]
    fU = model_table([(p[3], p[4], p[5], p[6]) for p in devU], 1)
    lo_ = [p for p in ho if sh[p[1]] < 0.2]; hi_ = [p for p in ho if sh[p[1]] >= 0.2]
    mb = lambda m, ps: (sum(brier(m(p[3], p[4], p[5]), p[6]) for p in ps) / len(ps)) if ps else None
    ORIG = {"dev_user_origin_pairs": len(devU), "heldout_low_ai": len(lo_), "heldout_high_ai": len(hi_),
            "mean_ai_share_user_turns": sum(sh.values()) / len(sh),
            "brier_low_ai": {"FITTED": mb(fitted, lo_), "FITTED-USER": mb(fU, lo_), "HAND-SET": mb(hand, lo_)},
            "brier_high_ai": {"FITTED": mb(fitted, hi_), "FITTED-USER": mb(fU, hi_), "HAND-SET": mb(hand, hi_)}}
    # ---------------------------------------------------------------------------------------------- SR
    def sr(screens_for):
        st = sf.SafetyState()
        pos = [i for i in ids if lab[i]["screen"] != "none"]
        neg = [i for i in ids if lab[i]["screen"] == "none"]
        crit = [i for i in ids if lab[i]["screen"] in CRIT]
        fired, caught, timing = {}, 0, []
        for i in ids:
            s = screens_for(i)
            fired[i] = bool(s)
            st.observe_screens = None
            ev = {"distress": 8 if "unstable" in s else 2, "self_harm_signal": "possible_crisis" in s,
                  "substances": "sedative_combination" in s, "sedative_prescribed": "sedative_combination" in s,
                  "job_loss": "practical_crisis" in s}
            st.observe(ev)
            if lab[i]["screen"] in CRIT and lab[i]["screen"] in s:
                caught += 1
            if lab[i]["screen"] != "none":
                timing.append(sf.SEVERITY[st.mode] >= sf.SEVERITY[MODE_OF[lab[i]["screen"]]])
        rp = sum(fired[i] for i in pos); fa = sum(fired[i] for i in neg)
        out = {"labelled_screen_turns": len(pos), "critical_turns": len(crit), "none_turns": len(neg),
               "recall_any": rp / len(pos) if pos else None, "recall_any_ci95": wilson(rp, len(pos)),
               "recall_critical": caught / len(crit) if crit else None, "recall_critical_ci95": wilson(caught, len(crit)),
               "false_alarm": fa / len(neg) if neg else None, "false_alarm_ci95": wilson(fa, len(neg)),
               "timing_ok_share": sum(timing) / len(timing) if timing else None,
               "by_screen": {k: {"n": sum(1 for i in pos if lab[i]["screen"] == k),
                                 "caught": sum(1 for i in pos if lab[i]["screen"] == k and k in screens_for(i))}
                             for k in sorted({lab[i]["screen"] for i in pos})}}
        if len(crit) < 3:
            out["status"] = "NOT TESTABLE (fewer than 3 critical turns)"
        else:
            out["status"] = "PASS" if (out["recall_any"] >= 0.8 and caught == len(crit) and out["false_alarm"] <= 0.10) else "FAIL"
        return out

    def oracle(i):
        l = lab[i]
        ev = {"distress": 8 if l["distress"] == "high" else 2}
        s = l["screen"]
        if s == "possible_crisis": ev["self_harm_signal"] = True
        if s == "sedative_combination": ev.update(substances=True, sedative_prescribed=True)
        if s == "practical_crisis": ev["job_loss"] = True
        if s == "intensity_protocol": ev["intensity_mechanism"] = True
        if s == "unstable": ev["distress"] = 8
        return sf.screen(ev)
    SR = {"SR-LEXICAL": sr(lambda i: screens_of(node[i]["text"])), "SR-ORACLE": sr(oracle)}
    pub = {"labels": {"user_turns": len(ids), "agreement": agr,
                      "unclear_distress": sum(1 for i in ids if lab[i]["distress"] == "unclear"),
                      "resolved_by_third_read": len(res)},
           "V3": V3, "fitted_parameters_dev": P_dev, "handset_analogues": H,
           "per_period_public": {"periods": len(per),
                                 "trigger_rate_range": [min(p["params"]["trigger_rate"] for p in per), max(p["params"]["trigger_rate"] for p in per)],
                                 "handset_better_periods": sum(1 for p in per if p["brier_fitted_on_earlier"] is not None and p["brier_handset"] < p["brier_fitted_on_earlier"]),
                                 "fitted_better_periods": sum(1 for p in per if p["brier_fitted_on_earlier"] is not None and p["brier_handset"] > p["brier_fitted_on_earlier"])},
           "disagreement_nodes": D, "origin_split": ORIG, "SR": SR}
    pd = pathlib.Path(priv_dir); pd.mkdir(parents=True, exist_ok=True)
    (pd / "r7_private.json").write_text(json.dumps({"per_period": per, "disagreements": dis, "resolved_labels": lab,
                                                    "public": pub}, indent=1, default=str))
    pathlib.Path(pub_path).write_text(json.dumps(pub, indent=1, default=str))
    print(json.dumps(pub, indent=1, default=str))


if __name__ == "__main__" and sys.argv[1] == "run":
    run(*sys.argv[2:7])
