"""ADOPT_WC (spec/ADOPT_WC.md): do the AI's words become the person's own across conversations? Future-placebo design.
Runs on a GitHub runner (.github/workflows/adopt_wc.yml). Prints aggregates only, between ADOPT_WC_JSON_BEGIN / _END.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter, defaultdict

import numpy as np

DATASET = "allenai/WildChat-1M"
MIN_CONV, MAX_CONV, MIN_SET, MIN_PERSONS = 3, 200, 5, 500
WORD_RX = re.compile(r"[a-z]{6,}")
STOP = frozenset("""
about above across actually after again against almost already always amount another answer answers anyone anything
around asking because become before behind being believe better between beyond cannot certain change changes clearly
common completely consider continue could create created currently different during either enough entire especially
example examples except likely little making matter maybe might moment number object others otherwise people person please
possible pretty provide provided question questions rather really reason should similar simple simply something sometimes
specific still though through together toward towards trying under unless update upon useful using usually various within
without would writing written yourself thanks thank before should always better another between important information
however therefore whether because please following provide sentence sentences paragraph paragraphs response responses
answer answered assistant language model models generate generated content
""".split())


# ------------------------------------------------------------------------------------------------ pure rules (tested)
def words(text: str) -> list:
    return [w for w in WORD_RX.findall((text or "").lower()) if w not in STOP]


def conv_sets(turns, vocab: dict):
    """turns: list of (role, text). Returns (A counts {id: n}, U set, F set) with ids from vocab (grown in place)."""
    def ids(text):
        out = []
        for w in words(text):
            i = vocab.get(w)
            if i is None:
                i = vocab[w] = len(vocab)
            out.append(i)
        return out
    A, U, F, first = Counter(), set(), set(), True
    for role, text in turns:
        if role == "assistant":
            A.update(ids(text))
        elif role == "user":
            w = ids(text)
            U.update(w)
            if first:
                F.update(w)
                first = False
    return dict(A), U, F


def person_events(convs):
    """convs: time-ordered list of dicts {A: {id: n}, U: set, F: set, ts: float (days)}. Returns event dicts (§4)."""
    out = []
    n = len(convs)
    for k in range(1, n - 1):
        U_lt_k = set().union(*(c["U"] for c in convs[:k]))
        A_lt_km1 = set().union(*(set(c["A"]) for c in convs[:k - 1])) if k - 1 > 0 else set()
        A_lt_k = A_lt_km1 | set(convs[k - 1]["A"])
        x_prev = set(convs[k - 1]["A"]) - U_lt_k - A_lt_km1
        x_next = set(convs[k + 1]["A"]) - U_lt_k - A_lt_k
        if len(x_prev) < MIN_SET or len(x_next) < MIN_SET:
            continue
        F = convs[k]["F"]
        hi = {w for w in x_prev if convs[k - 1]["A"][w] >= 3}
        lo = x_prev - hi
        out.append({"p_prev": len(F & x_prev) / len(x_prev), "p_next": len(F & x_next) / len(x_next),
                    "gap": convs[k]["ts"] - convs[k - 1]["ts"],
                    "dose_hi": (len(F & hi) / len(hi)) if hi else None, "dose_lo": (len(F & lo) / len(lo)) if lo else None})
    return out


def bootstrap(person_means: np.ndarray, B=2000, seed=12345, level=0.99):
    rng = np.random.default_rng(seed)
    n = len(person_means)
    stats = np.array([person_means[rng.integers(0, n, n)].mean() for _ in range(B)])
    a = (1 - level) / 2
    return float(person_means.mean()), float(np.quantile(stats, a)), float(np.quantile(stats, 1 - a))


def analyse(persons) -> dict:
    """persons: iterable of time-ordered conversation lists."""
    diffs, pp, pn, n_events = [], [], [], 0
    gaps = {"under_1_day": [], "1_to_7_days": [], "over_7_days": []}
    dose_hi, dose_lo = [], []
    for convs in persons:
        ev = person_events(convs)
        if not ev:
            continue
        n_events += len(ev)
        diffs.append(np.mean([e["p_prev"] - e["p_next"] for e in ev]))
        pp.append(np.mean([e["p_prev"] for e in ev])); pn.append(np.mean([e["p_next"] for e in ev]))
        for e in ev:
            g = "under_1_day" if e["gap"] < 1 else ("1_to_7_days" if e["gap"] <= 7 else "over_7_days")
            gaps[g].append(e["p_prev"] - e["p_next"])
            if e["dose_hi"] is not None and e["dose_lo"] is not None:
                dose_hi.append(e["dose_hi"]); dose_lo.append(e["dose_lo"])
    n = len(diffs)
    if n < MIN_PERSONS:
        return {"verdict": "NOT TESTABLE", "persons": n, "events": n_events}
    est, lo, hi = bootstrap(np.array(diffs))
    return {"verdict": "PASS" if lo > 0 else "FAIL", "persons": n, "events": n_events,
            "estimate": est, "lo": lo, "hi": hi,
            "info_only": {"p_prev": float(np.mean(pp)), "p_next": float(np.mean(pn)),
                          "by_gap_event_mean": {g: {"events": len(v), "mean": float(np.mean(v)) if v else None} for g, v in gaps.items()},
                          "dose_events": len(dose_hi),
                          "dose_hi_minus_lo": float(np.mean(np.array(dose_hi) - np.array(dose_lo))) if dose_hi else None}}


def main():
    import pyarrow.parquet as pq
    from huggingface_hub import HfApi, hf_hub_download
    api = HfApi()
    rev = api.dataset_info(DATASET).sha
    files = sorted(f for f in api.list_repo_files(DATASET, repo_type="dataset", revision=rev) if f.endswith(".parquet"))
    paths, hashes = {}, {}
    steps = Counter()
    by_person, seen = defaultdict(list), set()
    for fn in files:                                                          # pass 1: metadata only
        p = paths[fn] = hf_hub_download(DATASET, fn, repo_type="dataset", revision=rev)
        h = hashlib.sha256()
        with open(p, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 22), b""):
                h.update(chunk)
        hashes[fn] = h.hexdigest()
        for batch in pq.ParquetFile(p).iter_batches(batch_size=5000, columns=["conversation_hash", "language", "hashed_ip", "header", "timestamp"]):
            for r in batch.to_pylist():
                steps["conversations_seen"] += 1
                if r["conversation_hash"] in seen:
                    steps["duplicates"] += 1
                    continue
                seen.add(r["conversation_hash"])
                if r["language"] != "English":
                    continue
                steps["english"] += 1
                ua = (r.get("header") or {}).get("user-agent") or ""
                key = hashlib.sha256(((r.get("hashed_ip") or "") + "\x00" + ua).encode()).hexdigest()
                by_person[key].append((r["timestamp"].timestamp() / 86400.0, r["conversation_hash"]))
    keep = {k: v for k, v in by_person.items() if MIN_CONV <= len(v) <= MAX_CONV}
    steps["persons_all"] = len(by_person); steps["persons_kept"] = len(keep)
    steps["persons_over_200"] = sum(1 for v in by_person.values() if len(v) > MAX_CONV)
    want = {h for v in keep.values() for _, h in v}
    vocab, sets = {}, {}
    for fn in files:                                                          # pass 2: words of kept conversations
        for batch in pq.ParquetFile(paths[fn]).iter_batches(batch_size=2000, columns=["conversation_hash", "conversation"]):
            for r in batch.to_pylist():
                h = r["conversation_hash"]
                if h in want and h not in sets:
                    sets[h] = conv_sets([(t.get("role"), t.get("content") or "") for t in (r["conversation"] or [])], vocab)
        print("pass2", fn, len(sets), file=sys.stderr, flush=True)
    steps["conversations_kept"] = len(sets)

    def persons():
        for v in keep.values():
            convs = []
            for ts, h in sorted(v):
                A, U, F = sets[h]
                convs.append({"A": A, "U": U, "F": F, "ts": ts})
            yield convs
    R = analyse(persons())
    R.update({"test": "ADOPT_WC", "spec": "spec/ADOPT_WC.md", "steps": dict(steps),
              "dataset": {"name": DATASET, "revision": rev, "files": hashes}})
    print("ADOPT_WC_JSON_BEGIN")
    print(json.dumps(R, indent=1))
    print("ADOPT_WC_JSON_END")


if __name__ == "__main__":
    main()
