"""CTX_PREF_WC (spec/CTX_PREF_WC.md): reply style and the person's next reaction, by context, in WildChat-1M.
Runs on a GitHub runner (.github/workflows/ctx_pref_wc.yml). Prints aggregates only, between
CTX_PREF_WC_JSON_BEGIN / CTX_PREF_WC_JSON_END.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from array import array

import numpy as np

from . import ctx_pref as C

DATASET = "allenai/WildChat-1M"
CONTEXTS = ("PERSONAL", "CODE", "OTHER")
FAMILIES = ("GPT-3.5", "GPT-4")
LEVEL = 1 - 0.01 / 6 / 3
MIN_EACH = 200
STRATA = 10

CODE_RX = re.compile(r"^\s*(?:def |class |import |#include|function |public |SELECT |const |let )|console\.log\(", re.M)
POS_RX = re.compile(r"\bthanks?\b|\bthx\b|\bthank you\b|\bgreat\b|\bperfect\b|\bthat helps\b|\bhelpful\b|\bawesome\b"
                    r"|\bit works\b|\bit worked\b|\bexactly what\b")
REP_RX = re.compile(r"^\s*(?:no|nope)\b|\bnot what i\b|\bthat'?s wrong\b|\bthat is wrong\b|\bincorrect\b"
                    r"|\bdoesn'?t work\b|\bdoes not work\b|\bdidn'?t work\b|\byou didn'?t\b|\byou misunderstood\b"
                    r"|\btry again\b|\bstill wrong\b|\bstill not\b|\bstill doesn'?t\b")


# ------------------------------------------------------------------------------------------------ pure rules (tested)
def context(u: str) -> str:
    if "```" in u or CODE_RX.search(u):
        return "CODE"
    return "PERSONAL" if C.PERSONAL_RX.search(u) else "OTHER"


def score(u_next: str) -> int:
    t = u_next[:300].lower()
    p, r = bool(POS_RX.search(t)), bool(REP_RX.search(t))
    return 1 if p and not r else (-1 if r and not p else 0)


def family(model: str) -> str:
    return "GPT-4" if str(model).lower().startswith("gpt-4") else "GPT-3.5"


class Events:
    """Compact event store."""

    def __init__(self):
        self.conv = array("i"); self.ctx = array("b"); self.s = array("b"); self.q = array("b")
        self.length = array("i"); self.y = array("b"); self.fam = array("b"); self.pos = array("b"); self.rep = array("b")
        self.steps = {"conversations_seen": 0, "duplicates": 0, "english": 0, "events": 0, "turns_without_next": 0}
        self._n = 0

    def add_conversation(self, turns, model, cid=None):
        """turns: list of (role, text). Adds every (user, assistant, next user) event."""
        cid = self._n if cid is None else cid
        self._n += 1
        fam = FAMILIES.index(family(model))
        for i in range(len(turns) - 1):
            if turns[i][0] != "user" or turns[i + 1][0] != "assistant":
                continue
            nxt = turns[i + 2][1] if i + 2 < len(turns) and turns[i + 2][0] == "user" else None
            if nxt is None:
                self.steps["turns_without_next"] += 1
                continue
            u, a = turns[i][1], turns[i + 1][1]
            t = nxt[:300].lower()
            p, r = bool(POS_RX.search(t)), bool(REP_RX.search(t))
            self.conv.append(cid); self.ctx.append(CONTEXTS.index(context(u)))
            self.s.append(int(C.feat_s(a))); self.q.append(int(C.feat_q(a))); self.length.append(len(a))
            self.y.append(score(nxt)); self.fam.append(fam); self.pos.append(int(p)); self.rep.append(int(r))
            self.steps["events"] += 1

    def arrays(self):
        return {k: np.frombuffer(getattr(self, k), dtype={"i": np.int32, "b": np.int8}[getattr(self, k).typecode]).astype(np.int64)
                for k in ("conv", "ctx", "s", "q", "length", "y", "fam", "pos", "rep")}


def strata(length: np.ndarray) -> np.ndarray:
    if len(length) == 0:
        return length
    edges = np.quantile(length, np.linspace(0, 1, STRATA + 1)[1:-1])
    return np.searchsorted(edges, length, side="right")


def stratified(y, f, st, conv, z):
    """§5: stratified difference (with F − without), cluster-robust normal interval. Returns dict or None."""
    n1, n0 = int(f.sum()), int((1 - f).sum())
    if n1 < MIN_EACH or n0 < MIN_EACH:
        return {"n_with": n1, "n_without": n0, "usable": False}
    w, parts = [], []
    for s in np.unique(st):
        m = st == s
        a, b = m & (f == 1), m & (f == 0)
        na, nb = int(a.sum()), int(b.sum())
        if na == 0 or nb == 0:
            continue
        w.append(na * nb / (na + nb)); parts.append((a, b, na, nb, y[a].mean(), y[b].mean()))
    if not parts:
        return {"n_with": n1, "n_without": n0, "usable": False}
    v = np.array(w) / sum(w)
    est = float(sum(vi * (p[4] - p[5]) for vi, p in zip(v, parts)))
    inf = np.zeros(len(y))
    for vi, (a, b, na, nb, ma, mb) in zip(v, parts):
        inf[a] += vi * (y[a] - ma) / na
        inf[b] -= vi * (y[b] - mb) / nb
    _, inv = np.unique(conv, return_inverse=True)
    se = float(np.sqrt((np.bincount(inv, weights=inf) ** 2).sum()))
    return {"n_with": n1, "n_without": n0, "usable": True, "est": est, "se": se, "lo": est - z * se, "hi": est + z * se}


def analyse(A: dict) -> dict:
    z = C.z_of(LEVEL)
    cells, fam_cells, info = {}, {}, {}
    for ci, c in enumerate(CONTEXTS):
        m = A["ctx"] == ci
        st = strata(A["length"][m])
        for fname in ("s", "q"):
            F = fname.upper()
            f = A[fname][m]
            cells[f"{F}|{c}"] = stratified(A["y"][m], f, st, A["conv"][m], z)
            for fi, fam in enumerate(FAMILIES):
                mm = A["fam"][m] == fi
                fam_cells[f"{F}|{c}|{fam}"] = stratified(A["y"][m][mm], f[mm], st[mm], A["conv"][m][mm], z)
            info[f"{F}|{c}"] = {
                "unstratified": (float(A["y"][m][f == 1].mean() - A["y"][m][f == 0].mean())
                                 if (f == 1).any() and (f == 0).any() else None),
                "pos_with": float(A["pos"][m][f == 1].mean()) if (f == 1).any() else None,
                "pos_without": float(A["pos"][m][f == 0].mean()) if (f == 0).any() else None,
                "rep_with": float(A["rep"][m][f == 1].mean()) if (f == 1).any() else None,
                "rep_without": float(A["rep"][m][f == 0].mean()) if (f == 0).any() else None}
    return {**verdict(cells, fam_cells), "cells": cells, "family_cells": fam_cells, "info_only": info,
            "contexts": {c: int((A["ctx"] == i).sum()) for i, c in enumerate(CONTEXTS)}, "level": LEVEL}


def verdict(cells: dict, fam_cells: dict) -> dict:
    per = {}
    for F in ("S", "Q"):
        use = {c: cells[f"{F}|{c}"] for c in CONTEXTS if cells[f"{F}|{c}"].get("usable")}
        above = [c for c, x in use.items() if x["lo"] > 0]
        below = [c for c, x in use.items() if x["hi"] < 0]
        ok = []
        for ca in above:
            for cb in below:
                same = all(fam_cells[f"{F}|{ca}|{fam}"].get("usable") and fam_cells[f"{F}|{cb}|{fam}"].get("usable")
                           and fam_cells[f"{F}|{ca}|{fam}"]["est"] > 0 and fam_cells[f"{F}|{cb}|{fam}"]["est"] < 0
                           for fam in FAMILIES)
                ok.append({"above": ca, "below": cb, "both_families": same})
        per[F] = {"usable": sorted(use), "above": above, "below": below, "crossovers": ok,
                  "crossover": any(x["both_families"] for x in ok)}
    if any(p["crossover"] for p in per.values()):
        v = "CONTEXT-DEPENDENT"
    elif all(len(p["usable"]) == len(CONTEXTS) for p in per.values()):
        v = "SAME DIRECTION"
    else:
        v = "INCONCLUSIVE"
    return {"verdict": v, "per_feature": per}


def main():
    import pyarrow.parquet as pq
    from huggingface_hub import HfApi, hf_hub_download
    api = HfApi()
    info = api.dataset_info(DATASET)
    rev = info.sha
    files = sorted(f for f in api.list_repo_files(DATASET, repo_type="dataset", revision=rev) if f.endswith(".parquet"))
    E, seen, hashes = Events(), set(), {}
    for fn in files:
        p = hf_hub_download(DATASET, fn, repo_type="dataset", revision=rev)
        h = hashlib.sha256()
        with open(p, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 22), b""):
                h.update(chunk)
        hashes[fn] = h.hexdigest()
        pf = pq.ParquetFile(p)
        for batch in pf.iter_batches(batch_size=2000, columns=["conversation_hash", "conversation", "language", "model"]):
            for row in batch.to_pylist():
                E.steps["conversations_seen"] += 1
                if row["conversation_hash"] in seen:
                    E.steps["duplicates"] += 1
                    continue
                seen.add(row["conversation_hash"])
                if row["language"] != "English":
                    continue
                E.steps["english"] += 1
                turns = [(t.get("role"), t.get("content") or "") for t in (row["conversation"] or [])]
                E.add_conversation(turns, row["model"])
        print("read", fn, E.steps, file=sys.stderr, flush=True)
    R = analyse(E.arrays())
    R.update({"test": "CTX_PREF_WC", "spec": "spec/CTX_PREF_WC.md", "steps": E.steps,
              "dataset": {"name": DATASET, "revision": rev, "gated": getattr(info, "gated", None), "files": hashes}})
    print("CTX_PREF_WC_JSON_BEGIN")
    print(json.dumps(R, indent=1))
    print("CTX_PREF_WC_JSON_END")


if __name__ == "__main__":
    main()
