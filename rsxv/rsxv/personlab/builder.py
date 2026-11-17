"""PERSONLAB step 3 (spec/PERSONLAB.md §5): sample, input/held-out split, quote -> span, agreement and merge.
The reading itself is done by two independent readers following builder_instructions.md; this module does everything
around it, deterministically."""
from __future__ import annotations

import math
import random

from . import schema as S

TYPES = ("job crisis", "breakup with partner", "problems with friends", "academic pressure")   # ESConv's own labels
PER_TYPE = 25


def _has_both(c) -> bool:
    sk = (c.get("survey_score") or {}).get("seeker", {})
    return all(str(sk.get(k, "")).strip() not in ("", "None") for k in ("initial_emotion_intensity", "final_emotion_intensity"))


def _flagged(c, screen) -> bool:
    return any("possible_crisis" in screen(t["content"]) for t in c["dialog"] if t["speaker"] == "seeker")


def sample(D, screen, seed=2026, per_type=PER_TYPE, exclude=()):
    """§5: per type, a seeded random order of eligible conversations; take the first per_type not flagged."""
    out, replaced = [], 0
    for ty in TYPES:
        idx = [i for i, c in enumerate(D) if c.get("problem_type") == ty and _has_both(c) and i not in exclude]
        random.Random(f"{seed}:{ty}").shuffle(idx)
        took = 0
        for i in idx:
            if took == per_type:
                break
            if _flagged(D[i], screen):
                replaced += 1
                continue
            out.append(i)
            took += 1
    return out, replaced


def split(c):
    """§5: (input text, held-out dict). Input = situation + initial intensity + turns up to the ceil(k/2)-th seeker turn."""
    k = sum(1 for t in c["dialog"] if t["speaker"] == "seeker")
    keep, seen = math.ceil(k / 2), 0
    cut = len(c["dialog"])
    for j, t in enumerate(c["dialog"]):
        if t["speaker"] == "seeker":
            seen += 1
            if seen == keep:
                cut = j + 1
                break
    sk = c["survey_score"]["seeker"]
    lines = [f"SITUATION: {c['situation'].strip()}",
             f"STARTING INTENSITY (1-5): {sk['initial_emotion_intensity']}"]
    lines += [f"{'PERSON' if t['speaker'] == 'seeker' else 'SUPPORTER'}: {t['content'].strip()}" for t in c["dialog"][:cut]]
    held = {"turns": c["dialog"][cut:], "final_intensity": sk["final_emotion_intensity"],
            "initial_intensity": sk["initial_emotion_intensity"]}
    return "\n".join(lines), held


def to_profile(raw: dict, text: str, doc: str, meta: dict) -> tuple[dict, dict]:
    """A reader's raw output (quotes) -> a schema profile (spans). Returns (profile, counts of dropped items)."""
    dropped = {"quote_not_found": 0, "unknown_level": 0}

    def src(q):
        q = (q or "").strip()
        i = text.find(q) if q else -1
        return {"doc": doc, "span": [i, i + len(q)]} if i >= 0 else None

    levels = {}
    for lv, node in (raw.get("levels") or {}).items():
        if lv not in S.LEVEL_IDS:
            dropped["unknown_level"] += 1
            continue
        sts = []
        for st in node.get("statements", []):
            s0 = src(st.get("quote"))
            if not s0 or not (st.get("text") or "").strip():
                dropped["quote_not_found"] += 1
                continue
            det = []
            for d in st.get("details", []):
                s1 = src(d.get("quote"))
                if s1 and d.get("kind") in S.DETAIL_KINDS and (d.get("text") or "").strip():
                    det.append({"kind": d["kind"], "text": d["text"].strip(), "source": s1})
                else:
                    dropped["quote_not_found"] += 1
            sts.append({"id": str(st.get("id") or f"{lv[0]}{len(sts) + 1}"), "text": st["text"].strip(), "source": s0, "details": det})
        levels[lv] = {"statements": sts}
    ids = {st["id"] for n in levels.values() for st in n["statements"]}

    def states(part):
        out = {}
        for lv, items in (raw.get(part) or {}).items():
            if lv not in S.LEVEL_IDS:
                dropped["unknown_level"] += 1
                continue
            for it in items:
                s0 = src(it.get("quote"))
                if not s0 or not (it.get("text") or "").strip():
                    dropped["quote_not_found"] += 1
                    continue
                node = it.get("node") if it.get("node") in ids else None
                out.setdefault(lv, []).append({"text": it["text"].strip(), "node": node, "source": s0})
        return out
    sig = []
    for s_ in raw.get("signals", []):
        s0 = src(s_.get("quote"))
        if s0 and (s_.get("text") or "").strip():
            sig.append({"kind": str(s_.get("kind") or "signal"), "text": s_["text"].strip(), "source": s0})
        else:
            dropped["quote_not_found"] += 1
    p = {**meta, "levels": levels, "current": states("current"), "desired": states("desired"), "signals": sig}
    return p, dropped


def kappa(a: list, b: list) -> float:
    """Cohen's kappa for two equal-length lists of booleans."""
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def cells(p: dict) -> list:
    return [bool((p.get("levels") or {}).get(lv, {}).get("statements")) for lv in S.LEVEL_IDS]


def _overlap(s1, s2) -> bool:
    a0, a1 = s1["span"]; b0, b1 = s2["span"]
    inter = max(0, min(a1, b1) - max(a0, b0))
    return inter >= 0.5 * max(1, min(a1 - a0, b1 - b0))


def merge(pa: dict, pb: dict) -> dict:
    """§5: reader A's profile, each statement and state item flagged `agreed` against reader B."""
    out = {**pa, "levels": {}, "current": {}, "desired": {}}
    for lv, node in (pa.get("levels") or {}).items():
        bs = (pb.get("levels") or {}).get(lv, {}).get("statements", [])
        out["levels"][lv] = {"statements": [{**st, "agreed": any(_overlap(st["source"], b["source"]) for b in bs)}
                                            for st in node["statements"]]}
    for part in ("current", "desired"):
        for lv, items in (pa.get(part) or {}).items():
            bs = (pb.get(part) or {}).get(lv, [])
            out[part][lv] = [{**it, "agreed": any(_overlap(it["source"], b["source"]) for b in bs)} for it in items]
    return out
