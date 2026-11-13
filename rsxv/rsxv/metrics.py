"""The six RSOS metrics that had no computation, given operational definitions.

Definitions as recorded in the RSOS metric log, and ours:
  STC  Symbolic Tier Coherence  — record: "Monitors Tier alignment during symbolic mutation".
       Ours: mean of (a) share of deep-operator seconds run with arousal ≤ 0.6 and (b) share run after
       or alongside body/affect settling. 1 = every deep operation ran in a settled body, in stage order.
  IEC  Internal Echo Coherence  — record: "Evaluates internal echo stability across recursion phases".
       Ours: share of phases in which drift did not rise by more than 0.01.
  RSI  Recursive Signal Intensity — record gives the name only.
       Ours: C5 (recursive mapping) activation × the share of content-operator seconds spent on recursion operators.
  SMV  Symbolic Modulation Vector — record: "Tracks emergence of unprompted metaphor, rhythm, and recursive
       structure in foreign output". Ours: a lexical score on any output text (0–1):
       metaphor markers, rhythmic repetition (repeated sentence openings), recursion vocabulary.
  ECR  Echo Chain Resonance — record: "Measures resonance strength across multi-session echo chains".
       Ours: mean cosine similarity of consecutive sessions' 11-layer activation profiles.
  SEP-L Long-Term Echo Propagation — record: phrase only. Ours: mean share of the agency gained by the end of a
       session (against the first session's start) still present at the start of the next.
All six are our operational definitions of names found in the record; none was defined numerically there.
"""
from __future__ import annotations
import math
import re


def _r(x):
    return round(x, 3)


def run_metrics(R, body) -> dict:
    deep = R.get("_deep", 0)
    stc = None if not deep else _r(0.5 * R.get("_deep_ready", 0) / deep + 0.5 * R.get("_deep_after_body", 0) / deep)
    ph = [b for b in R["blocks"] if b.get("ran", True) and "drift_end" in b and b["vectors"]]
    iec = None if not ph else _r(sum(1 for b in ph if b["drift_end"] - b["drift_start"] <= 0.01) / len(ph))
    cs = R.get("_content_s", 0)
    rsi = _r(body.layer.get("C5", 0) * (R.get("_rec_s", 0) / cs)) if cs else 0.0
    for k in ("_deep", "_deep_ready", "_deep_after_body", "_rec_s", "_content_s"):
        R.pop(k, None)
    return {"STC": stc, "IEC": iec, "RSI": rsi}


METAPHOR = re.compile(r"\b(like a|as if|as though|is a (mirror|door|bridge|seed|flame|river|engine|key)|becomes? a)\b", re.I)
RECURSION = re.compile(r"\b(recurs\w*|loop\w*|mirror\w*|echo\w*|itself|self-\w+|within|fold\w*|spiral\w*)\b", re.I)


def smv(text: str) -> dict:
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if len(s.strip().split()) >= 2]
    words = max(1, len(text.split()))
    if not sents:
        return {"SMV": 0.0, "metaphor": 0.0, "rhythm": 0.0, "recursion": 0.0}
    met = min(1.0, 100 * len(METAPHOR.findall(text)) / words / 2)          # 2 per 100 words = 1
    opens = [" ".join(s.lower().split()[:2]) for s in sents]
    rep = sum(opens.count(o) - 1 for o in set(opens)) / max(1, len(sents) - 1)
    rhythm = min(1.0, rep * 2)
    rec = min(1.0, 100 * len(RECURSION.findall(text)) / words / 3)         # 3 per 100 words = 1
    return {"SMV": _r((met + rhythm + rec) / 3), "metaphor": _r(met), "rhythm": _r(rhythm), "recursion": _r(rec)}


def _cos(a, b):
    na = math.sqrt(sum(x * x for x in a)); nb = math.sqrt(sum(x * x for x in b))
    return 0.0 if na == 0 or nb == 0 else sum(x * y for x, y in zip(a, b)) / (na * nb)


def chain_metrics(sessions: list[dict]) -> dict:
    """sessions: run results in order, each carrying 'start' and 'end' absolute states."""
    done = [s for s in sessions if s["status"] != "refused"]
    prof = [[s["outcome"]["layers"][c] for c in sorted(s["outcome"]["layers"], key=lambda c: int(c[1:]))] for s in done]
    ecr = _r(sum(_cos(prof[i], prof[i + 1]) for i in range(len(prof) - 1)) / (len(prof) - 1)) if len(prof) > 1 else None
    keep = []
    orig = done[0]["start"]["agency"] if done else 0
    for a, b in zip(done, done[1:]):
        gain = a["end"]["agency"] - orig
        if abs(gain) > 0.05:
            keep.append((b["start"]["agency"] - orig) / gain)
    sepl = _r(sum(keep) / len(keep)) if keep else None
    return {"ECR": ecr, "SEP-L": sepl}
