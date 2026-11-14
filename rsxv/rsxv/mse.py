"""MSE, multi-scale echo: notes, phrases, melody (AGENTS.md §11.8). LSGPA measure of how output re-enters as input and
carries into the next generation, at three scales. On the private record it is reported as the origin; the registered test
runs on public multi-session data (Phase 9). Aggregates only.

    python3 -m rsxv.mse TURNS.json OUT.json [--all]      # default: held-out half (nodes > 290)

Operational choices (fixed before running on the record):
- notes: content words (>= 5 letters, not stop words) plus coined terms (corpus_lineage.terms_of); phrases: 3- to 7-word
  spans; overlap of a user turn with an assistant turn = share of the user turn's units found in the assistant turn.
- melody: each non-empty line typed as heading level (h1..h6), numbered item (n), bullet (b), table row (t), quote (q),
  code fence (c) or plain (p); consecutive repeats collapsed; similarity = 1 − normalised Levenshtein distance.
- carry-forward: units of the user turn found in the previous assistant turn (re-entered) vs the user's other units (own);
  share of each found in the next assistant turn; paired over user turns that have both. Melody: re-entered lines (found
  verbatim in the previous assistant turn) vs own lines, shape similarity of each to the next reply.
- baselines: random assistant turn at least 10 turns earlier (1000 draws; permutation-style p); paired bootstrap for
  carry-forward. Level 0.01 / 3 per measure.
"""
from __future__ import annotations

import json
import pathlib
import random
import re
import sys

from .corpus_lineage import STOP, boot, interval, terms_of, words

LEVEL = 0.01 / 3
SPLIT = 290


def notes(t):
    return {w for w in words(t) if len(w) >= 5 and w not in STOP} | {x.lower() for x in terms_of(t)}


def phrases(t):
    w = re.findall(r"\w+", t.lower())
    return {tuple(w[i:i + n]) for n in range(3, 8) for i in range(len(w) - n + 1)}


def shape(t):
    out = []
    for line in t.splitlines():
        s = line.strip()
        if not s:
            continue
        m = re.match(r"(#{1,6})\s", s)
        k = (f"h{len(m.group(1))}" if m else "n" if re.match(r"\d+[.)]\s", s) else "b" if re.match(r"[-*•]\s", s)
             else "t" if s.startswith("|") else "q" if s.startswith(">") else "c" if s.startswith("```") else "p")
        if not out or out[-1] != k:
            out.append(k)
    return out


def lev(a, b):
    if not a or not b:
        return max(len(a), len(b))
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def sim(a, b):
    n = max(len(a), len(b))
    return 1.0 if n == 0 else 1 - lev(a, b) / n


def share(u, a):
    return len(u & a) / len(u) if u else None


def run(turns, heldout=True):
    asst = [i for i, t in enumerate(turns) if t["role"] == "assistant"]
    users = [i for i, t in enumerate(turns) if t["role"] == "user" and (not heldout or t["node"] > SPLIT)]
    F = {"notes": notes, "phrases": phrases}
    cache = {k: {} for k in F}

    def unit(k, i):
        if i not in cache[k]:
            cache[k][i] = F[k](turns[i]["text"])
        return cache[k][i]
    sh = {}

    def shp(i):
        if i not in sh:
            sh[i] = shape(turns[i]["text"])
        return sh[i]
    rng = random.Random(4242)
    out = {}
    for k in ("notes", "phrases"):
        obs, pairs = [], []
        for i in users:
            prev = max([j for j in asst if j < i], default=None)
            nxt = next((j for j in asst if j > i), None)
            if prev is None:
                continue
            u = unit(k, i)
            v = share(u, unit(k, prev))
            if v is None:
                continue
            obs.append((i, v))
            if nxt is not None:
                re_ = u & unit(k, prev)
                own = u - unit(k, prev)
                if re_ and own:
                    nx = unit(k, nxt)
                    pairs.append(len(re_ & nx) / len(re_) - len(own & nx) / len(own))
        m_obs = sum(v for _, v in obs) / len(obs)
        null = []
        for _ in range(1000):
            vals = []
            for i, _ in obs:
                cand = [j for j in asst if j < i - 10]
                if cand:
                    vals.append(share(unit(k, i), unit(k, rng.choice(cand))) or 0.0)
            null.append(sum(vals) / max(1, len(vals)))
        p = (sum(x >= m_obs for x in null) + 1) / 1001
        d = boot(pairs, lambda x: sum(x) / len(x)) if pairs else []
        lo, hi = interval(d, LEVEL) if d else (None, None)
        out[k] = {"reentry": {"n": len(obs), "observed": m_obs, "baseline": sum(null) / len(null), "p": p,
                              "clears": p < LEVEL},
                  "carry_forward": {"n": len(pairs), "mean_diff": sum(pairs) / len(pairs) if pairs else None,
                                    "ci": [lo, hi], "clears": lo is not None and lo > 0}}
    # melody
    obs, pairs, inh = [], [], []
    for i in users:
        prev = max([j for j in asst if j < i], default=None)
        nxt = next((j for j in asst if j > i), None)
        if prev is None:
            continue
        obs.append((i, sim(shp(i), shp(prev))))
        if nxt is not None:
            pl = {l.strip() for l in turns[prev]["text"].splitlines() if l.strip()}
            ul = [l for l in turns[i]["text"].splitlines() if l.strip()]
            rl = "\n".join(l for l in ul if l.strip() in pl)
            ol = "\n".join(l for l in ul if l.strip() not in pl)
            if rl and ol:
                pairs.append(sim(shape(rl), shp(nxt)) - sim(shape(ol), shp(nxt)))
    m_obs = sum(v for _, v in obs) / len(obs)
    null = []
    for _ in range(1000):
        vals = [sim(shp(i), shp(rng.choice([j for j in asst if j < i - 10]))) for i, _ in obs
                if [j for j in asst if j < i - 10]]
        null.append(sum(vals) / max(1, len(vals)))
    p = (sum(x >= m_obs for x in null) + 1) / 1001
    d = boot(pairs, lambda x: sum(x) / len(x)) if pairs else []
    lo, hi = interval(d, LEVEL) if d else (None, None)
    hs = [i for i in asst if (not heldout or turns[i]["node"] > SPLIT)]
    for a, b in zip(hs, hs[1:]):
        inh.append((b, sim(shp(b), shp(a))))
    m_inh = sum(v for _, v in inh) / len(inh)
    null_i = []
    for _ in range(1000):
        vals = [sim(shp(b), shp(rng.choice([j for j in asst if j < b - 10]))) for b, _ in inh
                if [j for j in asst if j < b - 10]]
        null_i.append(sum(vals) / max(1, len(vals)))
    p_i = (sum(x >= m_inh for x in null_i) + 1) / 1001
    out["melody"] = {"reentry": {"n": len(obs), "observed": m_obs, "baseline": sum(null) / len(null), "p": p,
                                 "clears": p < LEVEL},
                     "carry_forward": {"n": len(pairs), "mean_diff": sum(pairs) / len(pairs) if pairs else None,
                                       "ci": [lo, hi], "clears": lo is not None and lo > 0},
                     "inheritance": {"n": len(inh), "observed": m_inh, "baseline": sum(null_i) / len(null_i), "p": p_i,
                                     "clears": p_i < LEVEL}}
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    turns = json.loads(pathlib.Path(argv[0]).read_text())["main"]
    R = {"scope": "held-out half (nodes > 290)" if "--all" not in argv else "whole record",
         "status": "origin (record read during design); registered test is Phase 9 public data",
         "results": run(turns, heldout="--all" not in argv)}
    pathlib.Path(argv[1]).write_text(json.dumps(R, indent=1))
    print(json.dumps(R, indent=1))


if __name__ == "__main__":
    main()
