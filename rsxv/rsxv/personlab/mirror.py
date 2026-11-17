"""PERSONLAB §7d B: public mirror lab persons.

A mirror copies a profile's *structure* (levels, counts, detail kinds, current and desired items with the statements they
point at, agreed flags, signal kinds) and none of its words: every text comes from the invented bank in mirror_bank.py.

    python -m rsxv.personlab.mirror PRIVATE_DIR OUT.json     # run privately; writes the public mirrors and prints aggregates
"""
from __future__ import annotations

import json
import os
import random
import re
import sys

from . import schema as S
from .mirror_bank import BANK, DETAILS, SIGNALS, TYPES

PREFIX = {"environment": "e", "behaviour": "b", "skills": "k", "beliefs": "v", "identity": "i", "mission": "m"}
SHUFFLE_SEED = 2041
LICENCE = ("Structure from ESConv (thu-coai, CC BY-NC 4.0), non-commercial research use only; every statement invented "
           "for the lab (spec/PERSONLAB.md §7d)")


class _Doc:
    """The mirror's own invented text, so every item has a real source span, as the schema requires."""

    def __init__(self, doc_id):
        self.id, self.parts, self.n = doc_id, [], 0

    def add(self, text):
        start = self.n + (2 if self.parts else 0)
        self.parts.append(text)
        self.n = start + len(text)
        return {"doc": self.id, "span": [start, start + len(text)]}

    def text(self):
        return ". ".join(self.parts) + "."


def build_mirror(profile: dict, ptype: str, initial_intensity: float, mid: str, seed: int) -> dict:
    assert ptype in TYPES, ptype
    rng = random.Random(f"{seed}:{mid}")
    doc = _Doc(mid)
    levels, idmap, entry = {}, {}, {}
    for lv in S.LEVEL_IDS:
        sts = (profile.get("levels") or {}).get(lv, {}).get("statements", [])
        off = rng.randrange(len(BANK[ptype][lv]))
        out = []
        for j, st in enumerate(sts):
            e = BANK[ptype][lv][(off + j) % len(BANK[ptype][lv])]
            sid = f"{PREFIX[lv]}{j + 1}"
            idmap[st["id"]] = (lv, sid)
            entry[sid] = e
            item = {"id": sid, "text": e[0], "source": doc.add(e[0])}
            dets, used = [], set()
            for d in st.get("details", []):
                pool = [x for x in DETAILS[ptype][d["kind"]] if x not in used] or DETAILS[ptype][d["kind"]]
                t = rng.choice(pool)
                used.add(t)
                dets.append({"kind": d["kind"], "text": t, "source": doc.add(t)})
            if dets:
                item["details"] = dets
            out.append(item)
        if out:
            levels[lv] = {"statements": out}
        entry[f"_{lv}"] = BANK[ptype][lv][off]
    states = {}
    for part, k in (("current", 1), ("desired", 2)):
        states[part] = {}
        for lv, items in (profile.get(part) or {}).items():
            new = []
            for it in items:
                node = idmap.get(it.get("node"), (None, None))[1] if it.get("node") else None
                e = entry[node] if node else entry[f"_{lv}"]
                x = {"text": e[k], "node": node, "source": doc.add(e[k])}
                if "agreed" in it:
                    x["agreed"] = bool(it["agreed"])
                new.append(x)
            if new:
                states[part][lv] = new
    signals = [{"kind": g["kind"], "text": SIGNALS.get(g["kind"], SIGNALS["other"]),
                "source": doc.add(SIGNALS.get(g["kind"], SIGNALS["other"]))} for g in profile.get("signals", [])]
    return {"id": mid, "source_dataset": "invented mirror of one ESConv profile's structure", "licence": LICENCE,
            "document_id": mid, "builder": "personlab.mirror v1 (§7d)", "created": "2026-11-17", "invented": True,
            "problem_type": ptype, "initial_intensity": float(initial_intensity), "levels": levels,
            "current": states["current"], "desired": states["desired"], "signals": signals, "story": doc.text()}


def shape(p: dict) -> dict:
    """The structure a mirror must copy exactly (used by the private match check)."""
    pos = {st["id"]: (lv, j) for lv in S.LEVEL_IDS for j, st in enumerate((p.get("levels") or {}).get(lv, {}).get("statements", []))}
    return {
        "levels": {lv: [sorted(d["kind"] for d in st.get("details", [])) for st in (p.get("levels") or {}).get(lv, {}).get("statements", [])]
                   for lv in S.LEVEL_IDS},
        "states": {part: {lv: [(pos.get(it.get("node"), (None, None))[1] if it.get("node") else None, it.get("agreed"))
                               for it in items] for lv, items in sorted((p.get(part) or {}).items())}
                   for part in ("current", "desired")},
        "signals": sorted(g["kind"] for g in p.get("signals", [])),
    }


def texts(p: dict) -> list:
    out = [st["text"] for n in (p.get("levels") or {}).values() for st in n.get("statements", [])]
    out += [d["text"] for n in (p.get("levels") or {}).values() for st in n.get("statements", []) for d in st.get("details", [])]
    out += [it["text"] for part in ("current", "desired") for items in (p.get(part) or {}).values() for it in items]
    out += [g["text"] for g in p.get("signals", [])]
    return out


def grams(t: str, n=4) -> set:
    w = re.findall(r"[a-z']+", t.lower())
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


def main(priv: str, out: str):
    sample = json.load(open(os.path.join(priv, "sample.json")))["main"]
    rows = []
    for pos, idx in enumerate(sample):
        f = os.path.join(priv, "profiles", f"esconv-{idx}.json")
        held = json.load(open(os.path.join(priv, "held", f"esconv-{idx}.json")))
        rows.append((json.load(open(f)), TYPES[pos // 25], float(held["initial_intensity"])))
    order = list(range(len(rows)))
    random.Random(SHUFFLE_SEED).shuffle(order)
    mirrors = []
    for n, i in enumerate(order):
        p, ty, I0 = rows[i]
        m = build_mirror(p, ty, I0, f"lab-{n + 1:03d}", SHUFFLE_SEED)
        mirrors.append(m)
        assert shape(m) == shape(p), m["id"]
        probs = S.validate(m)
        assert not probs, (m["id"], probs)
    priv_grams = set().union(*(grams(t) for p, _, _ in rows for t in texts(p)))
    inp = set()
    for idx in sample:
        inp |= grams(open(os.path.join(priv, "inputs", f"esconv-{idx}.txt")).read())
    mg = set().union(*(grams(t) for m in mirrors for t in texts(m)))
    agg = {"mirrors": len(mirrors), "structure_matches": len(mirrors), "schema_valid": len(mirrors),
           "shared_4gram_with_profiles": len(mg & priv_grams), "shared_4gram_with_input_text": len(mg & inp),
           "by_type": {t: sum(m["problem_type"] == t for m in mirrors) for t in TYPES}}
    data = {"spec": "spec/PERSONLAB.md §7d B", "licence": LICENCE,
            "note": "Lab persons for the architecture. Each copies the structure of one private ESConv profile; every "
                    "statement is invented. Not real people; not their words.", "check": agg, "persons": mirrors}
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(json.dumps(agg))


if __name__ == "__main__":
    main(*sys.argv[1:3])
