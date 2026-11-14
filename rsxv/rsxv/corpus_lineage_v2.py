"""Corpus v2 (AGENTS.md §11.6): C1b, C6b (two labellers, kappa ≥ 0.6), C4b own-use adoption, LSGPA R1 verbatim re-entry
and R2 propagation. Aggregates only are public; labels and node-level rows stay private.

    python3 -m rsxv.corpus_lineage_v2 TURNS.json LABEL_DIR PRIVATE_OUT_DIR PUBLIC_OUT.json

Operational choices fixed before outcomes were computed (disclosed in results/corpus_v2.md):
- Labeller A and labeller B were both separate model instances given the same written instructions and the same excerpts
  (candidate lines and the start of the previous turn), blind to each other; the registration named labeller A as Claude in
  the session — the session's own reading is the third read that resolves disagreements.
- C1b labels are item-level: does the turn correct, soften or withdraw an earlier estimate or internal claim (with key, old
  and new value when yes). Kappa is computed on that item-level label.
- C6b mechanism turns outside the candidate set count as "no".
- R1, R2: spans are 8-word windows on lower-cased word tokens; the held-out half is nodes 291–580.
"""
from __future__ import annotations

import json
import pathlib
import random
import re
import sys

from .corpus_lineage import LEVEL as _L, STOP, adoption, boot, interval, terms_of, topwords, words

LEVEL = 0.01
SPLIT = 290


def kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    cats = set(a) | set(b)
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    return ((po - pe) / (1 - pe) if pe < 1 else None), po


def load_labels(p):
    d = {}
    for line in open(p):
        if line.strip():
            x = json.loads(line)
            d.setdefault(x["id"], x)
    return d


def grams(text, n=8):
    w = re.findall(r"\w+", text.lower())
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


# ------------------------------------------------------------------------------------------------- C6b
def c6b(turns, A, B, res, items):
    ids = [i["id"] for i in items]
    out = {}
    lab = {}
    for k in ("failure_event", "mechanism_turn"):
        a, b = [A[i][k] for i in ids], [B[i][k] for i in ids]
        kp, po = kappa(a, b)
        out[f"kappa_{k}"], out[f"agree_{k}"] = kp, po
        r = res.get(f"c6b_{k}", {})
        lab[k] = {i: (A[i][k] if A[i][k] == B[i][k] else r[i]) for i in ids}
    node_of = {i["id"]: i["node"] for i in items}
    idx = {t["node"]: n for n, t in enumerate(turns)}
    fails = [idx[node_of[i]] for i in ids if lab["failure_event"][i] == "yes"]
    mech = {idx[node_of[i]] for i in ids if lab["mechanism_turn"][i] == "yes"}
    tw = {}

    def hit(i, ctxw):
        return any(j in mech and len(ctxw & set(words(turns[j]["text"]))) >= 2 for j in range(i + 1, min(len(turns), i + 21)))
    obs = [hit(i, tw.setdefault(i, topwords(turns[i]["text"]))) for i in fails]
    rng = random.Random(4242)
    null = [sum(hit(rng.randrange(len(turns)), tw[i]) for i in fails) / max(1, len(fails)) for _ in range(1000)]
    rate = sum(obs) / max(1, len(fails))
    p = (sum(x >= rate for x in null) + 1) / 1001
    ok_k = all(out[f"kappa_{k}"] is not None and out[f"kappa_{k}"] >= 0.6 for k in ("failure_event", "mechanism_turn"))
    out.update({"failure_events": len(fails), "mechanism_turns": len(mech), "followed": sum(obs), "rate": rate,
                "baseline_mean": sum(null) / len(null), "p": p,
                "status": ("PASS" if p < LEVEL else "FAIL") if ok_k else "INCONCLUSIVE (kappa < 0.6)"})
    rows = [{"node": turns[i]["node"], "hit": o} for i, o in zip(fails, obs)]
    return out, rows


# ------------------------------------------------------------------------------------------------- C1b
def c1b(A, B, res, items):
    ids = [i["id"] for i in items]
    a, b = [A[i]["corrects"] for i in ids], [B[i]["corrects"] for i in ids]
    kp, po = kappa(a, b)
    r = res.get("c1b_corrects", {})
    final = {i: (A[i]["corrects"] if A[i]["corrects"] == B[i]["corrects"] else r[i]) for i in ids}
    yes = [i for i in ids if final[i] == "yes"]
    return {"kappa": kp, "agree": po, "corrections": len(yes),
            "status": "INCONCLUSIVE (kappa < 0.6)" if kp is None or kp < 0.6 else "computed"}, yes


# ------------------------------------------------------------------------------------------------- C4b
def c4b(turns):
    seq = []
    seen_grams = {"user": set(), "assistant": set()}
    for t in turns:
        other = "assistant" if t["role"] == "user" else "user"
        txt = t["text"]
        g = grams(txt)
        copied = g & seen_grams[other]
        # remove words inside copied spans from term detection
        w = re.findall(r"\w+|\W+", txt)
        toks = re.findall(r"\w+", txt.lower())
        mask = [False] * len(toks)
        for i in range(len(toks) - 7):
            if tuple(toks[i:i + 8]) in copied:
                for j in range(i, i + 8):
                    mask[j] = True
        kept, k = [], 0
        for piece in w:
            if re.match(r"\w+", piece):
                kept.append("" if mask[k] else piece)
                k += 1
            else:
                kept.append(piece)
        seq.append((t["role"], terms_of("".join(kept))))
        seen_grams[t["role"]] |= g
    n, a2u, u2a, first, other = adoption(seq)
    rng = random.Random(4242)
    null = []
    for _ in range(1000):
        s = seq[:]
        rng.shuffle(s)
        null.append(adoption(s)[0])
    p = (sum(x >= n for x in null) + 1) / 1001
    return {"fast_adopted_own_use": n, "assistant_to_user": a2u, "user_to_assistant": u2a,
            "null_mean": sum(null) / len(null), "p": p, "status": "PASS" if p < LEVEL else "FAIL"}


# ------------------------------------------------------------------------------------------------- R1 / R2
def r1_r2(turns):
    asst = [i for i, t in enumerate(turns) if t["role"] == "assistant"]
    G = {i: grams(turns[i]["text"]) for i in asst}
    ev, obs = [], []
    users = [i for i, t in enumerate(turns) if t["role"] == "user" and t["node"] > SPLIT]
    for i in users:
        prev = max([j for j in asst if j < i], default=None)
        if prev is None:
            continue
        g = grams(turns[i]["text"])
        hit = g & G[prev]
        obs.append(1 if hit else 0)
        if hit:
            ev.append((i, prev, hit))
    share = sum(obs) / max(1, len(obs))
    rng = random.Random(4242)
    null = []
    for _ in range(1000):
        c = 0
        for i in users:
            cand = [j for j in asst if j < i - 10]
            if not cand:
                continue
            c += bool(grams(turns[i]["text"]) & G[rng.choice(cand)])
        null.append(c / max(1, len(users)))
    p1 = (sum(x >= share for x in null) + 1) / 1001
    # R2
    diffs = []
    for i, prev, hit in ev:
        nxt = next((j for j in asst if j > i), None)
        if nxt is None:
            continue
        span_words = {w for gr in hit for w in gr if len(w) >= 5 and w not in STOP}
        if not span_words:
            continue
        nw = set(words(turns[nxt]["text"]))
        a = len(span_words & nw) / len(span_words)
        cand = [j for j in asst if j < i - 10 and not (grams(turns[j]["text"]) & grams(turns[i]["text"]))]
        if not cand:
            continue
        j = rng.choice(cand)
        tok = [w for w in words(turns[j]["text"]) if len(w) >= 5 and w not in STOP]
        if len(tok) < len(span_words):
            continue
        st = rng.randrange(0, len(tok) - len(span_words) + 1)
        ctrl = set(tok[st:st + len(span_words)])
        b = len(ctrl & nw) / len(ctrl) if ctrl else 0.0
        diffs.append(a - b)
    d = boot(diffs, lambda x: sum(x) / len(x)) if diffs else []
    lo, hi = interval(d, LEVEL) if d else (None, None)
    return ({"heldout_user_turns": len(obs), "share_with_reentry": share, "baseline_mean": sum(null) / len(null),
             "p": p1, "status": "PASS" if p1 < LEVEL else "FAIL"},
            {"events": len(diffs), "mean_diff": sum(diffs) / len(diffs) if diffs else None, "ci": [lo, hi],
             "status": "PASS" if lo is not None and lo > 0 else "FAIL"})


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    turns = json.loads(pathlib.Path(argv[0]).read_text())["main"]
    L = pathlib.Path(argv[1])
    priv, pub = pathlib.Path(argv[2]), pathlib.Path(argv[3])
    res = json.loads((L / "resolved.json").read_text())
    it1, it6 = json.loads((L / "items_c1b.json").read_text()), json.loads((L / "items_c6b.json").read_text())
    C6, rows6 = c6b(turns, load_labels(L / "labels_A_c6b.jsonl"), load_labels(L / "labels_B_c6b.jsonl"), res, it6)
    C1, yes1 = c1b(load_labels(L / "labels_A_c1b.jsonl"), load_labels(L / "labels_B_c1b.jsonl"), res, it1)
    R1, R2 = r1_r2(turns)
    out = {"C1b": C1, "C6b": C6, "C4b": c4b(turns), "R1": R1, "R2": R2}
    priv.mkdir(parents=True, exist_ok=True)
    (priv / "corpus_v2_rows.json").write_text(json.dumps({"c6b_rows": rows6, "c1b_corrections": yes1, **out}, indent=1))
    pub.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
