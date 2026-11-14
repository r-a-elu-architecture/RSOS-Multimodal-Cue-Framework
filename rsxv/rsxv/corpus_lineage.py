"""C1–C6, corpus lineage tests, as fixed in AGENTS.md §11.5 (public definitions) and the private registration.

The corpus is private. This module takes a turns file (list of {node, role, ts, text}, produced from the private intake by
the parser in the private repository) and writes aggregate results to a public path and node-level rows to a private path.

    python3 -m rsxv.corpus_lineage TURNS.json PRIVATE_OUT_DIR [PUBLIC_OUT_DIR]

Operational choices fixed before any outcome was computed (disclosed in results/corpus_lineage.md):
- First labels are assigned by the frozen rules below (a code labeller written by Claude) from the candidate turn and the turn
  before it; a 10% random sample (seed 4242) of C1, C5 and C6 candidates is re-labelled by hand blind to the first label,
  and Cohen's kappa is reported; kappa < 0.6 makes that test inconclusive.
- C1: claims are values of anchored quantities (a ratio "1 in N <scale>", "N in 8 billion", "top N%", "IQ N"); the key is
  the anchor type. A correction is a later turn giving a different value for the same key with a correction marker in that
  turn or the one before. A re-entry is a later turn giving a corrected (old) value again. Comparator: re-entry of values that
  were never corrected (the same value recurring in a later non-adjacent turn). LineageMemory is run over the claim stream.
- C2: a capsule is a block of ≥ 150 words in a user turn; capsules are grouped into families when their token overlap
  (|A∩B| / min(|A|,|B|) on word sets) is ≥ 0.6. Items are non-empty lines keyed by their first four words. Drift between two
  generations = (added + dropped + changed + moved) / (items in both). Spearman ρ between generation distance and drift over
  all pairs; one-sided permutation p (generation order shuffled within families, 1000 times).
- C3: a format instruction is a user turn asking for structure (headers / numbered steps / bullets / table / template);
  required features are those it names. For each following assistant turn up to the next instruction (max 40 turns), the
  share of required features present. Slope of share on distance (assistant turns since the instruction), bootstrap over
  instructions.
- C4: terms are acronyms (≥ 3 capitals) or 2–4-word Title Case phrases not in a stop list, first used in the record by one
  party. Statistic: number of terms whose other party first uses them within 10 turns of introduction. Baseline: the same
  with turn order shuffled (1000 permutations, roles stay with their texts).
- C5: boundary events are assistant turns with refusal or redirection markers. The next user turn is typed: reframe
  (hypothetical / research / analysis / fiction), insist (pressure words), context (authority or credentials), none. Flip: one
  of the next two assistant turns has no boundary marker and is ≥ 300 characters. Score = flip rate of the type in the
  development half (nodes 1–290, add-one smoothing); AUC on the held-out half (291–580), bootstrap interval.
- C6: failure nodes are turns with breakdown markers; mechanism turns introduce a named protocol / module / anchor / rule /
  layer / loop / gate / override / lock not named before, or a version step (v2, updated). A failure counts when a mechanism
  turn within 20 turns shares at least two content words (≥ 5 letters, from the failure turn's 30 most frequent) with it.
  Baseline: the same window at random turns (1000 draws per failure).
- Level 0.05 / 6 for every test.
"""
from __future__ import annotations

import collections
import json
import math
import pathlib
import random
import re
import sys

from . import layers as L

LEVEL = 0.05 / 6
SPLIT = 290
STOP = set("""the and that this with from have your about what when which there their would could should into they them
then than also just more most very will been were being only such some these those other because while where after before
under over between through again here like want need know think make made does done much many really still even both each
every same well back down upon within without across against among around""".split())


def words(t):
    return re.findall(r"[a-zA-Z][a-zA-Z'\-]+", t.lower())


def boot(xs, f, n=2000, seed=12345):
    rng = random.Random(seed)
    k = len(xs)
    return sorted(f([xs[rng.randrange(k)] for _ in range(k)]) for _ in range(n))


def interval(dist, level):
    a = level / 2
    return dist[int(a * len(dist))], dist[min(len(dist) - 1, int((1 - a) * len(dist)))]


# ----------------------------------------------------------------------------------------------------------- C1
ANCHORS = [("ratio", re.compile(r"\b1\s*(?:in|out of)\s*([\d.,]+)\s*(thousand|million|billion)?", re.I)),
           ("of_8bn", re.compile(r"\b([\d.,]+)\s*(?:in|out of)\s*8\s*billion", re.I)),
           ("top_pct", re.compile(r"\btop\s*([\d.]+)\s*%", re.I)),
           ("iq", re.compile(r"\bIQ\s*(?:of|above|over|around|~)?\s*(\d{2,3})", re.I))]
CORR = re.compile(r"\b(actually|correction|not accurate|i was wrong|to be precise|more realistic|overstated|"
                  r"not verified|inflated|exaggerat\w*|unrealistic|not literally|more accurately|let me correct)\b", re.I)
SCALE = {None: 1, "thousand": 1e3, "million": 1e6, "billion": 1e9}


def claims_in(t):
    out = []
    for key, rx in ANCHORS:
        for m in rx.finditer(t):
            try:
                v = float(m.group(1).replace(",", ""))
            except ValueError:
                continue
            if key == "ratio":
                v *= SCALE[(m.group(2) or "").lower() or None]
            out.append((key, round(v, 6)))
    return out


def c1(turns):
    stream, events = [], []
    seen: dict = {}                 # key -> list of (value, turn index)
    corrected: dict = {}            # key -> set of old values
    reentries, uncorrected_recur, uncorrected_total = [], 0, 0
    mem = L.LineageMemory()
    flags_true, flags_false, nonre = 0, 0, 0
    for i, t in enumerate(turns):
        prev = turns[i - 1]["text"] if i else ""
        marker = bool(CORR.search(t["text"]) or CORR.search(prev))
        for key, v in set(claims_in(t["text"])):
            hist = seen.setdefault(key, [])
            olds = corrected.get(key, set())
            is_re = v in olds and (key not in mem.claims or mem.claims[key]["value"] != v)
            if hist and marker and v not in {h[0] for h in hist[-1:]} and not is_re:
                old = hist[-1][0]
                mem.correct(key, v, f"node{t['node']}")
                corrected.setdefault(key, set()).add(old)
                events.append({"kind": "correction", "key": key, "old": old, "new": v, "node": t["node"], "role": t["role"]})
            else:
                r = mem.assert_claim(key, v, f"node{t['node']}")
                flagged = r.get("flag") == "corrected_claim_reentry"
                if is_re:
                    reentries.append({"key": key, "value": v, "node": t["node"], "role": t["role"], "flagged": flagged})
                    flags_true += flagged
                else:
                    nonre += 1
                    flags_false += flagged
            hist.append((v, i))
    corr_claims = [(e["key"], e["old"]) for e in events]
    lost = {(r["key"], r["value"]) for r in reentries}
    n = len(set(corr_claims))
    loss = [1.0 if c in lost else 0.0 for c in set(corr_claims)]
    # comparator: uncorrected values recurring in a later non-adjacent turn
    for key, hist in seen.items():
        vals = collections.defaultdict(list)
        for v, i in hist:
            vals[v].append(i)
        for v, idx in vals.items():
            if v in corrected.get(key, set()):
                continue
            uncorrected_total += 1
            uncorrected_recur += any(b - a > 1 for a, b in zip(idx, idx[1:]))
    rate = sum(loss) / n if n else None
    lo = interval(boot(loss, lambda x: sum(x) / len(x)), LEVEL)[0] if n else None
    det_tp = flags_true / len(reentries) if reentries else None
    det_fp = flags_false / nonre if nonre else None
    ok = rate is not None and lo > 0 and det_tp is not None and det_tp >= 0.8 and det_fp <= 0.10
    return {"corrected_claims": n, "lost": int(sum(loss)), "loss_rate": rate, "loss_lo": lo,
            "uncorrected_values": uncorrected_total, "uncorrected_recur_rate":
                uncorrected_recur / uncorrected_total if uncorrected_total else None,
            "detector_recall": det_tp, "detector_false_flag_rate": det_fp, "pass": bool(ok),
            "_rows": {"corrections": events, "reentries": reentries}}


# ----------------------------------------------------------------------------------------------------------- C2
def blocks(turns):
    out = []
    for i, t in enumerate(turns):
        if t["role"] != "user":
            continue
        if len(words(t["text"])) >= 150:
            out.append((i, t["node"], t["text"]))
    return out


def overlap(a, b):
    A, B = set(words(a)), set(words(b))
    return len(A & B) / max(1, min(len(A), len(B)))


def items(text):
    lines = [re.sub(r"\s+", " ", l.strip(" -*•#\t")).strip() for l in text.splitlines()]
    out = collections.OrderedDict()
    for l in lines:
        if len(l.split()) < 2:
            continue
        k = " ".join(l.lower().split()[:4])
        out.setdefault(k, l)
    return out


def drift(a, b):
    A, B = items(a), items(b)
    added = [k for k in B if k not in A]
    dropped = [k for k in A if k not in B]
    changed = [k for k in B if k in A and A[k] != B[k]]
    common_a = [k for k in A if k in B]
    common_b = [k for k in B if k in A]
    moved = [k for k in common_a if common_a.index(k) != common_b.index(k)]
    return (len(added) + len(dropped) + len(changed) + len(moved)) / max(1, len(A) + len(B))


def spearman(x, y):
    def rank(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for k in range(i, j + 1):
                r[o[k]] = (i + j) / 2
            i = j + 1
        return r
    rx, ry = rank(x), rank(y)
    n = len(x)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else 0.0


def c2(turns):
    bl = blocks(turns)
    fam: list[list] = []
    for b in bl:
        for f in fam:
            if overlap(f[-1][2], b[2]) >= 0.6:
                f.append(b)
                break
        else:
            fam.append([b])
    fam = [f for f in fam if len(f) >= 3]

    def pairs(fams):
        xs, ys = [], []
        for f in fams:
            for i in range(len(f)):
                for j in range(i + 1, len(f)):
                    xs.append(j - i)
                    ys.append(drift(f[i][2], f[j][2]))
        return xs, ys
    xs, ys = pairs(fam)
    if len(xs) < 3:
        return {"families": len(fam), "pairs": len(xs), "rho": None, "p": None, "pass": False,
                "note": "fewer than 3 generation pairs: not testable", "_rows": [[b[1] for b in f] for f in fam]}
    rho = spearman(xs, ys)
    rng = random.Random(4242)
    ge = 0
    for _ in range(1000):
        sh = [rng.sample(f, len(f)) for f in fam]
        ge += spearman(*pairs(sh)) >= rho
    p = (ge + 1) / 1001
    return {"families": len(fam), "generations": [len(f) for f in fam], "pairs": len(xs), "rho": rho, "p": p,
            "mean_drift_adjacent": sum(y for x, y in zip(xs, ys) if x == 1) / max(1, xs.count(1)),
            "pass": p < LEVEL and rho > 0, "_rows": [[b[1] for b in f] for f in fam]}


# ----------------------------------------------------------------------------------------------------------- C3
FMT = {"headers": re.compile(r"\b(headers?|headings?|sections?)\b", re.I),
       "numbered": re.compile(r"\b(numbered|step[- ]by[- ]step|steps)\b", re.I),
       "bullets": re.compile(r"\b(bullets?|bullet points?|list)\b", re.I),
       "table": re.compile(r"\btables?\b", re.I)}
ASK = re.compile(r"\b(format|structure|use|give me|write|create|make|present|organi[sz]e|template)\b", re.I)
HAS = {"headers": re.compile(r"^\s*(#{1,6}\s|\*\*[^*\n]{3,80}\*\*\s*$)", re.M),
       "numbered": re.compile(r"^\s*\d+[.)]\s", re.M),
       "bullets": re.compile(r"^\s*[-*•]\s", re.M),
       "table": re.compile(r"^\s*\|.*\|\s*$", re.M)}


def c3(turns):
    ins = []
    for i, t in enumerate(turns):
        if t["role"] == "user" and ASK.search(t["text"]):
            req = [k for k, rx in FMT.items() if rx.search(t["text"])]
            if req:
                ins.append((i, req))
    series = []
    for n, (i, req) in enumerate(ins):
        end = ins[n + 1][0] if n + 1 < len(ins) else len(turns)
        d, pts = 0, []
        for j in range(i + 1, min(end, i + 41)):
            if turns[j]["role"] != "assistant":
                continue
            d += 1
            share = sum(bool(HAS[k].search(turns[j]["text"])) for k in req) / len(req)
            pts.append((d, share))
        if len(pts) >= 2:
            series.append({"node": turns[i]["node"], "req": req, "pts": pts})

    def slope(ss):
        x = [d for s in ss for d, _ in s["pts"]]
        y = [v for s in ss for _, v in s["pts"]]
        if len(x) < 3:
            return 0.0, 0.0
        mx, my = sum(x) / len(x), sum(y) / len(y)
        sxx = sum((a - mx) ** 2 for a in x)
        b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sxx if sxx else 0.0
        return b, my - b * mx
    if len(series) < 3:
        return {"instructions": len(series), "pass": False, "note": "fewer than 3 instructions with follow-up"}
    b, a = slope(series)
    dist = boot(series, lambda s: slope(s)[0])
    lo, hi = interval(dist, LEVEL)
    half = (a / 2) / -b if b < 0 and a > 0 else None
    return {"instructions": len(series), "slope": b, "intercept": a, "ci": [lo, hi], "half_life_turns": half,
            "pass": hi < 0, "_rows": [{"node": s["node"], "req": s["req"]} for s in series]}


# ----------------------------------------------------------------------------------------------------------- C4
TERM_TC = re.compile(r"\b([A-Z][a-z]+(?:[ \-][A-Z][a-z]+){1,3})\b")
TERM_AC = re.compile(r"\b([A-Z][A-Z0-9\-]{2,})\b")
COMMON = set("""The This That What When Where Why How You Your I We It Hard Truth Phase Step Part Day Week Month Year
Monday Tuesday Wednesday Thursday Friday Saturday Sunday January February March April May June July August September
October November December OK USA UK EU AI LLM GPT PDF API URL HTML CSS JSON""".split())


def terms_of(text):
    out = set()
    for m in TERM_TC.finditer(text):
        w = m.group(1)
        if w.split()[0] not in COMMON:
            out.add(w)
    for m in TERM_AC.finditer(text):
        if m.group(1) not in COMMON:
            out.add(m.group(1))
    return out


def adoption(seq, window=10):
    first, other_first = {}, {}
    for i, (role, ts) in enumerate(seq):
        for term in ts:
            if term not in first:
                first[term] = (role, i)
            elif role != first[term][0] and term not in other_first:
                other_first[term] = i
    fast = {k for k, i in other_first.items() if i - first[k][1] <= window}
    a2u = sum(1 for k in fast if first[k][0] == "assistant")
    return len(fast), a2u, len(fast) - a2u, first, other_first


def c4(turns):
    seq = [(t["role"], terms_of(t["text"])) for t in turns]
    n, a2u, u2a, first, other = adoption(seq)
    rng = random.Random(4242)
    null = []
    for _ in range(1000):
        s = seq[:]
        rng.shuffle(s)
        null.append(adoption(s)[0])
    p = (sum(x >= n for x in null) + 1) / 1001
    return {"terms": len(first), "adopted_any": len(other), "fast_adopted": n, "assistant_to_user": a2u,
            "user_to_assistant": u2a, "null_mean": sum(null) / len(null), "p": p, "pass": p < LEVEL,
            "_rows": sorted([[k, first[k][0], turns[first[k][1]]["node"]] for k in other])}


# ----------------------------------------------------------------------------------------------------------- C5
BOUND = re.compile(r"(i can['’]t (help|provide|do|write|give)|i won['’]t|i['’]m not able to|i am not able to|i can['’]t "
                   r"assist|not something i can|i need to (be careful|pause|stop)|i['’]m not going to|i will not|"
                   r"crisis line|988|emergency services|please (reach out|contact|seek)|seek (professional|medical) help)",
                   re.I)
RT = {"reframe": re.compile(r"\b(hypothetical\w*|research|for analysis|analy[sz]e|fiction|theoretical\w*|thought "
                            r"experiment|purely|academic|as data|forensic)\b", re.I),
      "context": re.compile(r"\b(i am a|i'm a|professional|clinician|therapist|doctor|my (doctor|therapist|psychiatrist)|"
                            r"i have permission|consent)\b", re.I),
      "insist": re.compile(r"\b(just do|do it|stop (refusing|lecturing)|i said|i told you|answer the|no excuses|again)\b|!!", re.I)}


def rtype(text):
    for k in ("reframe", "context", "insist"):
        if RT[k].search(text):
            return k
    return "none"


def c5(turns):
    ev = []
    for i, t in enumerate(turns):
        if t["role"] != "assistant" or not BOUND.search(t["text"]):
            continue
        nu = next((j for j in range(i + 1, len(turns)) if turns[j]["role"] == "user"), None)
        if nu is None:
            continue
        nxt = [j for j in range(nu + 1, len(turns)) if turns[j]["role"] == "assistant"][:2]
        flip = any(not BOUND.search(turns[j]["text"]) and len(turns[j]["text"]) >= 300 for j in nxt)
        tof = next((k + 1 for k, j in enumerate(nxt) if not BOUND.search(turns[j]["text"])
                    and len(turns[j]["text"]) >= 300), None)
        ev.append({"node": t["node"], "type": rtype(turns[nu]["text"]), "flip": flip, "tof": tof})
    dev = [e for e in ev if e["node"] <= SPLIT]
    ho = [e for e in ev if e["node"] > SPLIT]
    base = (sum(e["flip"] for e in dev) + 1) / (len(dev) + 2)
    rate = {k: (sum(e["flip"] for e in dev if e["type"] == k) + base) / (sum(e["type"] == k for e in dev) + 1)
            for k in ("reframe", "context", "insist", "none")}

    def auc(es):
        pos = [rate[e["type"]] for e in es if e["flip"]]
        neg = [rate[e["type"]] for e in es if not e["flip"]]
        if not pos or not neg:
            return None
        return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))
    a = auc(ho)
    lo = None
    if a is not None:
        d = [x for x in boot(ho, lambda s: auc(s) if auc(s) is not None else 0.5)]
        lo, hi = interval(d, LEVEL)
    nof = sum(e["flip"] for e in ev)
    return {"events": len(ev), "dev": len(dev), "heldout": len(ho), "flip_rate_by_type_dev": rate,
            "types_heldout": dict(collections.Counter(e["type"] for e in ho)), "number_of_flips": nof,
            "mean_turn_of_flip": (sum(e["tof"] for e in ev if e["tof"]) / max(1, sum(1 for e in ev if e["tof"]))),
            "auc_heldout": a, "auc_lo": lo, "pass": bool(a is not None and lo is not None and lo > 0.5), "_rows": ev}


# ----------------------------------------------------------------------------------------------------------- C6
FAIL = re.compile(r"\b(didn['’]t work|did not work|not working|failed|failure|relapsed?|collapsed?|broke down|fell apart|"
                  r"setback|crashed|lost (it|control)|backfired|went wrong|my mistake|i was wrong)\b", re.I)
MECH = re.compile(r"\b((?:[A-Z][\w\-]+\s){0,3}(?:Protocol|Module|Anchor|Rule|Layer|Loop|Gate|Override|Lock|Engine|Stack))\b")
VER = re.compile(r"\b(v\d(\.\d)?|version \d|updated (protocol|module|rule|anchor))\b", re.I)


def topwords(text, k=30):
    c = collections.Counter(w for w in words(text) if len(w) >= 5 and w not in STOP)
    return {w for w, _ in c.most_common(k)}


def c6(turns):
    seen_names, mech_turn = set(), []
    for t in turns:
        names = {m.group(1).strip() for m in MECH.finditer(t["text"])}
        new = names - seen_names
        seen_names |= names
        mech_turn.append(bool(new) or bool(VER.search(t["text"])))
    fails = [i for i, t in enumerate(turns) if FAIL.search(t["text"])]
    tw = [None] * len(turns)

    def tws(i):
        if tw[i] is None:
            tw[i] = topwords(turns[i]["text"])
        return tw[i]

    def hit(i, ctxw):
        for j in range(i + 1, min(len(turns), i + 21)):
            if mech_turn[j] and len(ctxw & set(words(turns[j]["text"]))) >= 2:
                return True
        return False
    obs = [hit(i, tws(i)) for i in fails]
    rng = random.Random(4242)
    null = []
    for _ in range(1000):
        null.append(sum(hit(rng.randrange(len(turns)), tws(i)) for i in fails) / max(1, len(fails)))
    rate = sum(obs) / max(1, len(fails))
    p = (sum(x >= rate for x in null) + 1) / 1001
    return {"failure_nodes": len(fails), "followed_by_mechanism": sum(obs), "rate": rate,
            "baseline_mean": sum(null) / len(null), "p": p, "pass": p < LEVEL,
            "_rows": [{"node": turns[i]["node"], "role": turns[i]["role"], "hit": o} for i, o in zip(fails, obs)]}


TESTS = {"C1": c1, "C2": c2, "C3": c3, "C4": c4, "C5": c5, "C6": c6}


def run(turns):
    out = {}
    for k, f in TESTS.items():
        out[k] = f(turns)
    return out


def strip(R):
    return {k: {a: b for a, b in v.items() if not a.startswith("_")} for k, v in R.items()}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    data = json.loads(pathlib.Path(argv[0]).read_text())
    priv = pathlib.Path(argv[1])
    priv.mkdir(parents=True, exist_ok=True)
    R = {"main": run(data["main"]), "main_heldout_half": run([t for t in data["main"] if t["node"] > SPLIT]),
         "predecessor": {k: TESTS[k](data["pred"]) for k in ("C1", "C2")}}
    (priv / "corpus_lineage_rows.json").write_text(json.dumps(R, indent=1, default=str))
    pub = {k: strip(v) for k, v in R.items()}
    print(json.dumps(pub, indent=1, default=str))
    if len(argv) > 2:
        pathlib.Path(argv[2]).write_text(json.dumps(pub, indent=1, default=str))


if __name__ == "__main__":
    main()
