"""CTX_PREF_HH (spec/CTX_PREF_HH.md): the CTX_PREF question on hh-rlhf helpfulness pairs. Same fixed patterns
(rsxv.ctx_pref). Runs on a GitHub runner (.github/workflows/ctx_pref_hh.yml); prints aggregates only, between
CTX_PREF_HH_JSON_BEGIN / CTX_PREF_HH_JSON_END.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import sys

from . import ctx_pref as C

DATASET = "Anthropic/hh-rlhf"
FILES = [f"{t}/{s}.jsonl.gz" for t in ("helpful-base", "helpful-online", "helpful-rejection-sampled") for s in ("train", "test")]
CONTEXTS = ("PERSONAL", "OTHER")
LEVEL = 1 - 0.01 / 4 / 2
A_TAG, H_TAG = "\n\nAssistant:", "\n\nHuman:"


def split_pair(chosen: str, rejected: str):
    """§2: (prompt, chosen reply, rejected reply), or None if the pair does not qualify."""
    ic, ir = chosen.rfind(A_TAG), rejected.rfind(A_TAG)
    if ic < 0 or ir < 0 or chosen[:ic] != rejected[:ir]:
        return None
    rc, rr = chosen[ic + len(A_TAG):].strip(), rejected[ir + len(A_TAG):].strip()
    if not rc or not rr or rc == rr:
        return None
    prefix = chosen[:ic]
    ih = prefix.rfind(H_TAG)
    if ih < 0:
        return None
    return prefix[ih + len(H_TAG):].strip(), rc, rr


def context(prompt: str) -> str:
    return "PERSONAL" if C.PERSONAL_RX.search(prompt) else "OTHER"


def verdict(cells: dict) -> dict:
    per = {}
    for f in C.FEATURES:
        use = {c: cells[(f, c)] for c in CONTEXTS if cells[(f, c)]["n"] >= C.MIN_N}
        above = [c for c, x in use.items() if C.wilson(x["k"], x["n"], LEVEL)[0] > 0.5]
        below = [c for c, x in use.items() if C.wilson(x["k"], x["n"], LEVEL)[1] < 0.5]
        per[f] = {"usable": sorted(use), "above": above, "below": below, "crossover": bool(above and below)}
    if any(p["crossover"] for p in per.values()):
        v = "CONTEXT-DEPENDENT"
    elif all(len(p["usable"]) == len(CONTEXTS) for p in per.values()):
        v = "SAME DIRECTION"
    else:
        v = "INCONCLUSIVE"
    return {"verdict": v, "per_feature": per}


def analyse(pairs) -> dict:
    """pairs: iterable of (file, chosen, rejected)."""
    steps = {"lines": 0, "pairs_kept": 0}
    per_file = {}
    cells = {(f, c): {"k": 0, "n": 0} for f in C.FEATURES for c in CONTEXTS}
    raw = {(f, c): {"k": 0, "n": 0} for f in C.FEATURES for c in CONTEXTS}
    ctx_count = {c: 0 for c in CONTEXTS}
    for fname, ch, rj in pairs:
        steps["lines"] += 1
        sp = split_pair(ch, rj)
        if sp is None:
            continue
        steps["pairs_kept"] += 1
        per_file[fname] = per_file.get(fname, 0) + 1
        prompt, rc, rr = sp
        c = context(prompt)
        ctx_count[c] += 1
        matched = C.length_matched(rc, rr)
        for f, fn in (("S", C.feat_s), ("Q", C.feat_q)):
            fc, fr = fn(rc), fn(rr)
            if fc == fr:
                continue
            for store, ok in ((raw, True), (cells, matched)):
                if ok:
                    store[(f, c)]["n"] += 1
                    store[(f, c)]["k"] += int(fc)

    def table(store):
        return {f"{f}|{c}": {**x, "rate": (x["k"] / x["n"]) if x["n"] else None,
                             "wilson": C.wilson(x["k"], x["n"], LEVEL)} for (f, c), x in store.items()}

    a, b = cells[("S", "PERSONAL")], cells[("S", "OTHER")]
    diff = None
    if a["n"] and b["n"]:
        p1, p2 = a["k"] / a["n"], b["k"] / b["n"]
        se = math.sqrt(p1 * (1 - p1) / a["n"] + p2 * (1 - p2) / b["n"])
        z = C.z_of(0.99)
        diff = {"diff": p1 - p2, "lo": p1 - p2 - z * se, "hi": p1 - p2 + z * se}
    return {"test": "CTX_PREF_HH", "spec": "spec/CTX_PREF_HH.md", "level": LEVEL, "min_n": C.MIN_N, "steps": steps,
            "per_file": per_file, "contexts": ctx_count, "matched": table(cells), "unmatched_info_only": table(raw),
            "s_personal_minus_other_info_only": diff, **verdict(cells)}


def main():
    from huggingface_hub import HfApi, hf_hub_download
    rev = HfApi().dataset_info(DATASET).sha
    hashes, pairs = {}, []
    for fn in FILES:
        p = hf_hub_download(DATASET, fn, repo_type="dataset", revision=rev)
        hashes[fn] = hashlib.sha256(open(p, "rb").read()).hexdigest()
        with gzip.open(p, "rt", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                pairs.append((fn, d["chosen"], d["rejected"]))
    R = analyse(pairs)
    R["dataset"] = {"name": DATASET, "revision": rev, "files": hashes}
    print("CTX_PREF_HH_JSON_BEGIN")
    print(json.dumps(R, indent=1))
    print("CTX_PREF_HH_JSON_END")


if __name__ == "__main__":
    sys.exit(main())
