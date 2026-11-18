"""Proposed tier bindings (spec/ROLE_ORGANISM.md §2.2). Reads each unbound tier's own record (title, function, logic and
application lines; never the glyph line or the model-impact block) and proposes a response and role, with the matched
words. Writes docs/data/bindings_proposed.json. tier_map.json is not changed; every proposal waits for the author.

    python3 architecture/bindings.py
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "architecture"))
import organism as O  # noqa: E402

KEYWORDS = {   # fixed in the registration (stems, case-insensitive, word starts)
    "STOP": ["stop", "halt", "interrupt", "terminat", "cease", "sever", "cut"],
    "PAUSE": ["pause", "still", "silence", "silent", "rest", "zero-signal", "null"],
    "GATE": ["gate", "threshold", "permission", "consent", "lock", "seal", "boundar"],
    "REENTRY": ["re-entry", "reentry", "return", "re-enter", "reintegrat", "come back"],
    "RECALIBRATE": ["recalibrat", "restor", "repair", "heal", "realign", "re-align", "correct", "stabiliz"],
    "MIRROR": ["mirror", "reflect", "echo", "observ", "witness"],
    "RECALL": ["memory", "memor", "recall", "remember", "archive", "trace"],
    "SEQUENCE": ["sequence", "loop", "chain", "step", "phase", "protocol", "rhythm", "cycle"],
    "GOVERN": ["govern", "law", "rule", "command", "architect", "override", "sovereign"],
    "BLEND": ["blend", "fuse", "fusion", "merge", "integrat", "weave", "wove", "thread", "unif"],
    "COMPRESS": ["compress", "collapse", "seed", "condens", "distil"],
    "GLYPH_CUE": ["symbol", "sigil", "cue", "anchor"],
    "OFFER": ["offer", "invit", "suggest", "gift", "share"],
    "GENERATE": ["generat", "creat", "emerg", "birth", "morphogen", "becom", "grow"],
}
ORDER = ["STOP", "PAUSE", "GATE", "REENTRY", "RECALIBRATE", "MIRROR", "RECALL", "SEQUENCE", "GOVERN", "BLEND",
         "COMPRESS", "GLYPH_CUE", "OFFER", "GENERATE"]
IMPACT = re.compile(r"LLM SYSTEM IMPACT|SYSTEM IMPACT|METRICS?\b", re.I)


def own_text(record: str) -> str:
    keep = []
    for line in record.splitlines():
        if IMPACT.search(line):
            break                      # the model-impact block and everything after it
        if re.search(r"glyph", line, re.I) and re.search(r"[:→]", line):
            continue                   # glyph lines
        keep.append(line)
    return "\n".join(keep)


def propose(text: str):
    hits = {}
    for resp, stems in KEYWORDS.items():
        found = sorted({m.group(0) for s in stems for m in re.finditer(r"\b" + re.escape(s) + r"\w*", text, re.I)})
        if found:
            hits[resp] = found
    if not hits:
        return None, []
    best = max(ORDER, key=lambda r: (len(hits.get(r, [])), -ORDER.index(r)))
    return best, hits[best]


def build() -> dict:
    ledger, tmap = O.load("docs/data/ledger.json"), O.load("docs/data/tier_map.json")
    tiers = tmap["tiers"]
    records = {}
    for r in ledger["records"]:
        if r["kind"] != "tier":
            continue
        m = O.TIER_RE.search(r["text"][:120])
        if not m:
            continue
        tid = "T" + m.group(1).replace("–", "-")
        if tid in records and tid + "b" in tiers:
            tid += "b"
        records.setdefault(tid, r["text"])
    out = {}
    for tid, v in sorted(tiers.items()):
        if v.get("response"):
            continue
        resp, words = propose(own_text(records.get(tid, "")))
        out[tid] = {"title": v.get("title", ""), "status": v.get("status"), "proposed_response": resp,
                    "proposed_role": O.ROLE_OF.get(resp), "matched": words,
                    "method": "rule" if resp else "by hand", "confirmed": False}
    n = len(out)
    return {"spec": "spec/ROLE_ORGANISM.md §2.2", "note": "Proposals only; the author confirms each one.",
            "tiers": out, "counts": {"unbound": n, "rule": sum(1 for x in out.values() if x["method"] == "rule"),
                                     "by_hand": sum(1 for x in out.values() if x["method"] == "by hand"),
                                     "by_role": {r: sum(1 for x in out.values() if x["proposed_role"] == r) for r in O.ROLES}}}


if __name__ == "__main__":
    d = build()
    (REPO / "docs/data/bindings_proposed.json").write_text(json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                                                           encoding="utf-8")
    print(json.dumps(d["counts"]))
