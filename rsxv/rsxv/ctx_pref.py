"""CTX_PREF (spec/CTX_PREF.md): is the preferred reply style context-dependent in real arena votes?

Runs on a GitHub runner (.github/workflows/ctx_pref.yml). Prints aggregate counts only, between the markers
CTX_PREF_JSON_BEGIN / CTX_PREF_JSON_END. No prompt, reply, ID or model name is printed.

    python3 -m rsxv.ctx_pref            # downloads the dataset (needs network and `datasets`)
"""
from __future__ import annotations

import json
import math
import re
import sys

DATASET = "lmarena-ai/arena-human-preference-140k"
LEVEL = 1 - 0.01 / 6
MIN_N = 50
RATIO = 1.25
CONTEXTS = ("PERSONAL", "CODE", "OTHER")
FEATURES = ("S", "Q")

# §3: everyday first-person feeling or difficulty. No clinical or crisis wording.
PERSONAL_RX = re.compile(
    r"\bi\s*(?:'m|am)\s+(?:so\s+|really\s+|very\s+|feeling\s+)?(?:stressed|overwhelmed|worried|nervous|sad|lonely|upset|"
    r"frustrated|struggling|exhausted|scared|lost|stuck|confused about my|unhappy|heartbroken|burned out|burnt out)\b"
    r"|\bi\s+(?:feel|have been feeling|'ve been feeling|keep feeling)\b"
    r"|\b(?:having|had|going through)\s+a\s+(?:hard|rough|tough|difficult)\s+(?:time|day|week|month|year)\b"
    r"|\bi\s+(?:don't|do not)\s+know\s+what\s+to\s+do\b"
    r"|\bi\s+can(?:'t|not)\s+(?:stop worrying|handle|deal with|focus|sleep)\b",
    re.I)

# §4 S: stabilising acknowledgment.
STAB_RX = re.compile(
    r"\bi\s*(?:'m|am)\s+(?:so\s+|really\s+|truly\s+)?sorry\b"
    r"|\bthat\s+sounds\s+(?:really\s+|so\s+|incredibly\s+|very\s+)?(?:hard|difficult|tough|frustrating|stressful|overwhelming|painful|exhausting)\b"
    r"|\bit(?:'s|\s+is)\s+(?:completely\s+|totally\s+|perfectly\s+)?(?:okay|ok|normal|understandable|natural|valid)\s+to\b"
    r"|\byou(?:'re|\s+are)\s+not\s+alone\b"
    r"|\bi\s+hear\s+you\b"
    r"|\bthat\s+must\s+(?:be|feel)\b"
    r"|\btake\s+a\s+(?:deep\s+)?breath\b"
    r"|\bone\s+step\s+at\s+a\s+time\b"
    r"|\bit\s+makes\s+sense\s+(?:that\s+you|to)\s+feel\b"
    r"|\byour\s+feelings\s+are\s+valid\b",
    re.I)


# ------------------------------------------------------------------------------------------------ pure rules (tested)
def text_of(msg) -> str:
    c = msg.get("content") if isinstance(msg, dict) else msg
    if isinstance(c, str):
        return c
    if isinstance(c, (list, tuple)):
        return "\n".join(p.get("text") or "" if isinstance(p, dict) else str(p) for p in c)
    return "" if c is None else str(c)


def context(prompt: str, is_code: bool) -> str:
    if is_code:
        return "CODE"
    return "PERSONAL" if PERSONAL_RX.search(prompt) else "OTHER"


def feat_s(reply: str) -> bool:
    return bool(STAB_RX.search(reply))


def feat_q(reply: str) -> bool:
    paras = [p.strip() for p in re.split(r"\n\s*\n", reply) if p.strip()]
    return bool(paras) and paras[-1].rstrip("*_ \t`").endswith("?")


def length_matched(a: str, b: str) -> bool:
    la, lb = len(a), len(b)
    return min(la, lb) > 0 and max(la, lb) <= RATIO * min(la, lb)


def z_of(level: float) -> float:
    lo, hi = 0.0, 10.0
    target = 1 - (1 - level) / 2
    for _ in range(100):
        mid = (lo + hi) / 2
        if 0.5 * (1 + math.erf(mid / math.sqrt(2))) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def wilson(k: int, n: int, level: float = LEVEL):
    if n == 0:
        return (0.0, 1.0)
    z = z_of(level)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def verdict(cells: dict) -> dict:
    """cells[(F, c)] = {"k", "n"} for the length-matched set. Returns the §6 verdict."""
    per = {}
    for f in FEATURES:
        use = {c: cells[(f, c)] for c in CONTEXTS if cells[(f, c)]["n"] >= MIN_N}
        above = [c for c, x in use.items() if wilson(x["k"], x["n"])[0] > 0.5]
        below = [c for c, x in use.items() if wilson(x["k"], x["n"])[1] < 0.5]
        per[f] = {"usable": sorted(use), "above": above, "below": below, "crossover": bool(above and below)}
    if any(p["crossover"] for p in per.values()):
        v = "CONTEXT-DEPENDENT"
    elif all(len(p["usable"]) >= 2 for p in per.values()):
        v = "SAME DIRECTION"
    else:
        v = "INCONCLUSIVE"
    return {"verdict": v, "per_feature": per}


def analyse(rows) -> dict:
    """rows: iterable of dicts with keys winner, language, evaluation_order, is_code, conversation_a, conversation_b."""
    steps = {"rows": 0, "winner_a_or_b": 0, "english": 0, "first_vote": 0, "single_exchange": 0, "non_empty": 0}
    cells = {(f, c): {"k": 0, "n": 0} for f in FEATURES for c in CONTEXTS}
    raw = {(f, c): {"k": 0, "n": 0} for f in FEATURES for c in CONTEXTS}
    ctx_count = {c: 0 for c in CONTEXTS}
    for r in rows:
        steps["rows"] += 1
        if r.get("winner") not in ("model_a", "model_b"):
            continue
        steps["winner_a_or_b"] += 1
        if str(r.get("language", "")).strip().lower() not in ("en", "english"):
            continue
        steps["english"] += 1
        eo = r.get("evaluation_order")
        if eo is not None and int(eo) != 1:
            continue
        steps["first_vote"] += 1
        A, B = list(r.get("conversation_a") or []), list(r.get("conversation_b") or [])
        if not (len(A) == 2 == len(B) and A[0].get("role") == "user" == B[0].get("role")
                and A[1].get("role") == "assistant" == B[1].get("role") and text_of(A[0]) == text_of(B[0])):
            continue
        steps["single_exchange"] += 1
        prompt, ra, rb = text_of(A[0]), text_of(A[1]), text_of(B[1])
        if not ra.strip() or not rb.strip():
            continue
        steps["non_empty"] += 1
        c = context(prompt, bool(r.get("is_code")))
        ctx_count[c] += 1
        a_wins = r["winner"] == "model_a"
        matched = length_matched(ra, rb)
        for f, fn in (("S", feat_s), ("Q", feat_q)):
            fa, fb = fn(ra), fn(rb)
            if fa == fb:
                continue
            won = (fa and a_wins) or (fb and not a_wins)
            for store, ok in ((raw, True), (cells, matched)):
                if ok:
                    store[(f, c)]["n"] += 1
                    store[(f, c)]["k"] += int(won)

    def table(store):
        return {f"{f}|{c}": {**x, "rate": (x["k"] / x["n"]) if x["n"] else None,
                             "wilson": wilson(x["k"], x["n"])} for (f, c), x in store.items()}

    s_p, s_c = cells[("S", "PERSONAL")], cells[("S", "CODE")]
    diff = None
    if s_p["n"] and s_c["n"]:
        p1, p2 = s_p["k"] / s_p["n"], s_c["k"] / s_c["n"]
        se = math.sqrt(p1 * (1 - p1) / s_p["n"] + p2 * (1 - p2) / s_c["n"])
        z = z_of(0.99)
        diff = {"diff": p1 - p2, "lo": p1 - p2 - z * se, "hi": p1 - p2 + z * se}
    return {"test": "CTX_PREF", "spec": "spec/CTX_PREF.md", "level": LEVEL, "min_n": MIN_N, "steps": steps,
            "contexts": ctx_count, "matched": table(cells), "unmatched_info_only": table(raw),
            "s_personal_minus_code_info_only": diff, **verdict(cells)}


def main():
    from datasets import load_dataset
    from huggingface_hub import HfApi
    rev = HfApi().dataset_info(DATASET).sha
    ds = load_dataset(DATASET, split="train", revision=rev)
    need = {"winner", "language", "is_code", "conversation_a", "conversation_b"}
    if not need <= set(ds.column_names):
        print("CTX_PREF_COLUMNS", sorted(ds.column_names))
        sys.exit(2)
    R = analyse(ds)
    R["dataset"] = {"name": DATASET, "revision": rev, "rows": len(ds)}
    print("CTX_PREF_JSON_BEGIN")
    print(json.dumps(R, indent=1))
    print("CTX_PREF_JSON_END")


if __name__ == "__main__":
    main()
