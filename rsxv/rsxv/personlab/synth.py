"""PERSONLAB §7d-B′: lab persons generated from published summary statistics only.

    python -m rsxv.personlab.synth aggregate PRIVATE_DIR OUT_AGG.json    # privately: counts over the private profiles
    python -m rsxv.personlab.synth generate AGG.json OUT_PERSONS.json     # publicly: 100 lab persons from the counts

No lab person corresponds to any profile: every feature is drawn independently from the aggregate counts, and every text
comes from the invented bank (mirror_bank.py).
"""
from __future__ import annotations

import json
import os
import random
import re
import sys
from collections import Counter

from . import schema as S
from .mirror_bank import BANK, DETAILS, SIGNALS, TYPES

PREFIX = {"environment": "e", "behaviour": "b", "skills": "k", "beliefs": "v", "identity": "i", "mission": "m"}
SEED = 2041
N = 100
LICENCE = ("CC BY 4.0 (RSOS). Generated from summary statistics of 100 profiles built from ESConv (Liu et al., 2021, "
           "thu-coai); no profile, conversation or per-person record is reproduced; every statement invented.")
CITATION = ("Liu, S., Zheng, C., Demasi, O., Sabour, S., Li, Y., Yu, Z., Jiang, Y., Huang, M. (2021). Towards Emotional "
            "Support Dialog Systems. ACL 2021.")


class _Doc:
    """The lab person's own invented text, so every item has a real source span, as the schema requires."""

    def __init__(self, doc_id):
        self.id, self.parts, self.n = doc_id, [], 0

    def add(self, text):
        start = self.n + (2 if self.parts else 0)
        self.parts.append(text)
        self.n = start + len(text)
        return {"doc": self.id, "span": [start, start + len(text)]}

    def text(self):
        return ". ".join(self.parts) + "."


def _c(counter) -> dict:
    return {str(k): v for k, v in sorted(counter.items(), key=lambda kv: str(kv[0]))}


def aggregate(profiles: list, types: list, intensities: list) -> dict:
    """Counts only; nothing per person (§7d-B′)."""
    agg = {"n": len(profiles), "problem_types": _c(Counter(types)),
           "initial_intensity": _c(Counter(int(x) for x in intensities)),
           "statements_per_level": {}, "details_per_statement": Counter(), "detail_kinds": Counter(),
           "items": {"current": {}, "desired": {}}, "signals_per_profile": Counter(), "signal_kinds": Counter()}
    for lv in S.LEVEL_IDS:
        agg["statements_per_level"][lv] = _c(Counter(len((p.get("levels") or {}).get(lv, {}).get("statements", [])) for p in profiles))
        for part in ("current", "desired"):
            items = [it for p in profiles for it in (p.get(part) or {}).get(lv, [])]
            agg["items"][part][lv] = {"per_profile": _c(Counter(len((p.get(part) or {}).get(lv, [])) for p in profiles)),
                                      "pointing": [sum(1 for it in items if it.get("node")), len(items)],
                                      "agreed": [sum(1 for it in items if it.get("agreed")), len(items)]}
    for p in profiles:
        for n in (p.get("levels") or {}).values():
            for st in n.get("statements", []):
                agg["details_per_statement"][len(st.get("details", []))] += 1
                for d in st.get("details", []):
                    agg["detail_kinds"][d["kind"]] += 1
        agg["signals_per_profile"][len(p.get("signals", []))] += 1
        for g in p.get("signals", []):
            agg["signal_kinds"][g["kind"]] += 1
    for k in ("details_per_statement", "detail_kinds", "signals_per_profile", "signal_kinds"):
        agg[k] = _c(agg[k])
    return {"spec": "spec/PERSONLAB.md §7d-B′", "note": "Counts over the 100 private Person Lab profiles (ESConv). Nothing per person.",
            "aggregates": agg}


def _draw(rng, counts: dict):
    keys = list(counts)
    return rng.choices(keys, weights=[counts[k] for k in keys])[0]


def _bern(rng, kn) -> bool:
    k, n = kn
    return n > 0 and rng.random() < k / n


def generate(agg_doc: dict, n: int = N, seed: int = SEED) -> list:
    A = agg_doc["aggregates"]
    rng = random.Random(seed)
    types = [t for t in TYPES for _ in range(n // len(TYPES))]
    rng.shuffle(types)
    persons = []
    for i, ptype in enumerate(types):
        pid = f"lab-{i + 1:03d}"
        doc = _Doc(pid)
        levels, entries = {}, {}
        for lv in S.LEVEL_IDS:
            bank = BANK[ptype][lv]
            k = int(_draw(rng, A["statements_per_level"][lv]))
            picks = rng.sample(range(len(bank)), k)
            entries[lv] = {}
            sts = []
            for j, b in enumerate(picks):
                sid = f"{PREFIX[lv]}{j + 1}"
                entries[lv][sid] = bank[b]
                st = {"id": sid, "text": bank[b][0], "source": doc.add(bank[b][0])}
                dets, used = [], set()
                for _ in range(int(_draw(rng, A["details_per_statement"]))):
                    kind = _draw(rng, A["detail_kinds"])
                    pool = [x for x in DETAILS[ptype][kind] if x not in used] or DETAILS[ptype][kind]
                    t = rng.choice(pool); used.add(t)
                    dets.append({"kind": kind, "text": t, "source": doc.add(t)})
                if dets:
                    st["details"] = dets
                sts.append(st)
            if sts:
                levels[lv] = {"statements": sts}
            entries[lv]["_"] = bank[rng.randrange(len(bank))]
        states = {"current": {}, "desired": {}}
        for part, col in (("current", 1), ("desired", 2)):
            for lv in S.LEVEL_IDS:
                spec = A["items"][part][lv]
                out = []
                for _ in range(int(_draw(rng, spec["per_profile"]))):
                    sids = [s for s in entries[lv] if s != "_"]
                    node = rng.choice(sids) if sids and _bern(rng, spec["pointing"]) else None
                    e = entries[lv][node] if node else entries[lv]["_"]
                    out.append({"text": e[col], "node": node, "source": doc.add(e[col]), "agreed": _bern(rng, spec["agreed"])})
                if out:
                    states[part][lv] = out
        signals = []
        for _ in range(int(_draw(rng, A["signals_per_profile"]))):
            kind = _draw(rng, A["signal_kinds"])
            signals.append({"kind": kind, "text": SIGNALS[kind], "source": doc.add(SIGNALS[kind])})
        persons.append({"id": pid, "source_dataset": "generated from summary statistics (§7d-B′)", "licence": LICENCE,
                        "document_id": pid, "builder": "personlab.synth v1 (§7d-B′)", "created": "2026-11-17", "invented": True,
                        "problem_type": ptype, "initial_intensity": float(_draw(rng, A["initial_intensity"])),
                        "levels": levels, "current": states["current"], "desired": states["desired"], "signals": signals,
                        "story": doc.text()})
    return persons


def texts(p: dict) -> list:
    out = [st["text"] for n in (p.get("levels") or {}).values() for st in n.get("statements", [])]
    out += [d["text"] for n in (p.get("levels") or {}).values() for st in n.get("statements", []) for d in st.get("details", [])]
    out += [it["text"] for part in ("current", "desired") for items in (p.get(part) or {}).values() for it in items]
    out += [g["text"] for g in p.get("signals", [])]
    return out


def grams(t: str, n=4) -> set:
    w = re.findall(r"[a-z']+", t.lower())
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


def build(agg_doc: dict, check: dict | None = None) -> dict:
    persons = generate(agg_doc)
    return {"spec": "spec/PERSONLAB.md §7d-B′", "licence": LICENCE, "citation": CITATION,
            "aggregates": "rsxv/results/personlab_aggregates.json", "seed": SEED,
            "note": "Lab persons for the architecture, drawn at random from summary statistics; every statement invented. "
                    "Not real people, not their words, and no lab person corresponds to any profile.",
            "check": check or {}, "persons": persons}


def main(argv):
    if argv[0] == "aggregate":
        priv, out = argv[1], argv[2]
        sample = json.load(open(os.path.join(priv, "sample.json")))["main"]
        profiles, types, ints = [], [], []
        for pos, idx in enumerate(sample):
            profiles.append(json.load(open(os.path.join(priv, "profiles", f"esconv-{idx}.json"))))
            types.append(TYPES[pos // 25])
            ints.append(float(json.load(open(os.path.join(priv, "held", f"esconv-{idx}.json")))["initial_intensity"]))
        agg = aggregate(profiles, types, ints)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(agg, f, indent=1); f.write("\n")
        # private check, aggregates only: no generated text shares a 4-word run with the private profiles or inputs
        persons = generate(agg)
        pg = set().union(*(grams(t) for p in profiles for t in texts(p)))
        ig = set().union(*(grams(open(os.path.join(priv, "inputs", f"esconv-{i}.txt")).read()) for i in sample))
        mg = set().union(*(grams(t) for p in persons for t in texts(p)))
        print(json.dumps({"persons": len(persons), "schema_valid": sum(not S.validate(p) for p in persons),
                          "shared_4gram_with_profiles": len(mg & pg), "shared_4gram_with_input_text": len(mg & ig)}))
    elif argv[0] == "generate":
        agg = json.load(open(argv[1], encoding="utf-8"))
        check = json.loads(argv[3]) if len(argv) > 3 else None
        data = build(agg, check)
        with open(argv[2], "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1); f.write("\n")
        print(len(data["persons"]), "lab persons")


if __name__ == "__main__":
    main(sys.argv[1:])
