"""LEDGER_GRAPH (spec/LEDGER_GRAPH.md): every tier split into its parts; mutation, reference and shared-glyph edges
between tiers; edges between epochs; roles voted by chains, calibrated against keywords on the tiers whose role is
known. Deterministic; writes docs/data/ledger_graph.json. tier_map.json is read, never changed.

    python3 architecture/ledger_graph.py
"""
from __future__ import annotations

import collections
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "architecture"))
import bindings as B  # noqa: E402
import organism as O  # noqa: E402

SAFE_ORDER = ["Stabilise", "Monitor", "Repair", "Plan", "Baseline", "Drive"]
FIELD = re.compile(r"^\s*(?:[•\-\*]\s*)?([A-Z][A-Za-z /&()-]{1,40}):\s*(.*)$")
SECTION = re.compile(r"^\W*([A-Z][A-Z &/\-]{4,})\W*$")
MUTATION = re.compile(r"Glyph Mutation:\s*(\S+)\s*→\s*(\S+)")
GLYPH = re.compile(r"^\W*Glyphs?:\s*(\S+)", re.M)
REF = re.compile(r"\bTiers?\W{0,3}(\d{3})(?:\s*[–-]\s*(\d{3}))?", re.I)
IMPACT = re.compile(r"IMPACT|METRIC", re.I)


def records(tiers):
    """tier id -> record text, in ledger order (a second record of the same number is the map's 'b' tier)."""
    ledger = O.load("docs/data/ledger.json")
    out, epoch_of, epoch = {}, {}, None
    for r in ledger["records"]:
        if r["kind"] == "epoch":
            m = O.EPOCH_RE.search(r["text"])
            epoch = m.group(1) if m else epoch
        elif r["kind"] == "tier":
            m = O.TIER_RE.search(r["text"][:120])
            if not m:
                continue
            tid = "T" + m.group(1).replace("–", "-")
            if tid in out and tid + "b" in tiers:
                tid += "b"
            if tid in tiers and tid not in out:
                out[tid], epoch_of[tid] = r["text"], epoch
    return out, epoch_of


def parts(text: str) -> dict:
    lines = text.splitlines()
    p = {"title": re.sub(r"^\W*(RSOS\s+)?TIERS?\W*[\d.–-]+\w?\s*[—-]\s*", "", lines[0], flags=re.I).strip() if lines else "",
         "fields": {}, "sections": {}, "impact": {}}
    m = MUTATION.search(text)
    if m:
        p["glyph_from"], p["glyph_to"] = m.group(1), m.group(2)
    else:
        g = GLYPH.search(text)
        if g:
            p["glyph"] = g.group(1)
    for key in ("Tier Class", "Anchor"):
        mm = re.search(rf"^\W*{key}:\s*(.+)$", text, re.M)
        if mm:
            p[key.lower().replace(" ", "_")] = mm.group(1).strip()
    cur = None
    for line in lines[1:]:
        s = SECTION.match(line)
        if s and not line.strip().startswith(("•", "-")):
            cur = s.group(1).strip()
            (p["impact"] if IMPACT.search(cur) else p["sections"]).setdefault(cur, [])
            continue
        f = FIELD.match(line)
        if f and cur is None:
            p["fields"][f.group(1).strip()] = f.group(2).strip()
            continue
        if cur and line.strip():
            (p["impact"] if IMPACT.search(cur) else p["sections"])[cur].append(line.strip())
    p["has_content"] = bool(p["fields"] or p["sections"])
    return p


def own_glyph(p):
    return p.get("glyph_to") or p.get("glyph")


def build() -> dict:
    tmap = O.load("docs/data/tier_map.json")["tiers"]
    recs, epoch_of = records(tmap)
    P = {t: parts(x) for t, x in recs.items()}
    # --- edges
    edges = []
    start_of = collections.defaultdict(set)
    for t, p in P.items():
        for g in (p.get("glyph_from"), p.get("glyph")):
            if g:
                start_of[g].add(t)
    for t, p in P.items():
        if p.get("glyph_to"):
            for u in sorted(start_of.get(p["glyph_to"], set()) - {t}):
                edges.append(("mutation", t, u))
    for t, x in recs.items():
        body = "\n".join(x.splitlines()[1:])
        seen = set()
        for m in REF.finditer(body):
            for n in (m.group(1), m.group(2)):
                if n and f"T{n}" in tmap and f"T{n}" != t and f"T{n}" not in seen:
                    seen.add(f"T{n}")
                    edges.append(("reference", t, f"T{n}"))
    by_glyph = collections.defaultdict(list)
    for t, p in P.items():
        if own_glyph(p):
            by_glyph[own_glyph(p)].append(t)
    for g, ts in by_glyph.items():
        ts = sorted(ts)
        for i, a in enumerate(ts):
            for b in ts[i + 1:]:
                edges.append(("shared_glyph", a, b))
    nb = collections.defaultdict(set)
    for _, a, b in edges:
        nb[a].add(b)
        nb[b].add(a)
    epoch_edges = collections.Counter(f"{epoch_of.get(a)}→{epoch_of.get(b)}" for k, a, b in edges if k != "shared_glyph")
    # --- roles: known, chain vote, keyword rule
    known = {t: O.ROLE_OF[v["response"]] for t, v in tmap.items() if v.get("response") in O.ROLE_OF}

    def vote(t, exclude_self=True):
        for hop in (1, 2):
            ring = set(nb[t]) if hop == 1 else {y for x in nb[t] for y in nb[x]} - {t}
            roles = collections.Counter(known[x] for x in ring if x in known and not (exclude_self and x == t))
            if roles:
                top = max(roles.values())
                return next(r for r in SAFE_ORDER if roles.get(r) == top), hop
        return None, None

    def keyword(t):
        resp, _ = B.propose(B.own_text(recs.get(t, "")))
        return O.ROLE_OF.get(resp)

    shares = collections.Counter(known.values())
    chance = sum((c / len(known)) ** 2 for c in shares.values())
    loo = [(t, vote(t)[0]) for t in known]
    chain_cal = [(known[t], r) for t, r in loo if r]
    kw_cal = [(known[t], keyword(t)) for t in known]
    calib = {"known_tiers": len(known), "chance": chance,
             "chain": {"covered": len(chain_cal), "accuracy": sum(a == b for a, b in chain_cal) / len(chain_cal) if chain_cal else None},
             "keyword": {"covered": sum(1 for _, b in kw_cal if b), "accuracy": sum(a == b for a, b in kw_cal) / len(kw_cal)}}
    unbound = [t for t in tmap if t not in known]
    prop = {}
    for t in sorted(unbound):
        c, hop = vote(t, exclude_self=False)
        k = keyword(t)
        prop[t] = {"chain_role": c, "chain_hops": hop, "keyword_role": k, "agree": (c == k) if c and k else None}
    both = [v for v in prop.values() if v["chain_role"] and v["keyword_role"]]
    kshare = collections.Counter(v["keyword_role"] for v in both)
    cshare = collections.Counter(v["chain_role"] for v in both)
    agree_chance = sum((kshare[r] / len(both)) * (cshare[r] / len(both)) for r in O.ROLES) if both else None
    better = "chain" if (calib["chain"]["accuracy"] or 0) > calib["keyword"]["accuracy"] else "keyword"
    for v in prop.values():
        v["review_order"] = (1 if v["agree"] else 3 if not (v["chain_role"] or v["keyword_role"]) else 2)
        v["suggested_role"] = (v["chain_role"] if v["agree"] else
                               (v[f"{better}_role"] or v["chain_role"] or v["keyword_role"]))
    return {
        "spec": "spec/LEDGER_GRAPH.md",
        "parts": {t: {k: v for k, v in p.items() if k != "impact"} | {"impact_blocks": sorted(p["impact"])} for t, p in P.items()},
        "edges": [{"kind": k, "from": a, "to": b} for k, a, b in edges],
        "counts": {"tiers": len(tmap), "records": len(recs), "with_title_and_content": sum(1 for p in P.values() if p["title"] and p["has_content"]),
                   "edges": dict(collections.Counter(k for k, _, _ in edges)), "tiers_with_edge": sum(1 for t in tmap if nb[t]),
                   "sections": dict(collections.Counter(s for p in P.values() for s in p["sections"]).most_common(12)),
                   "fields": dict(collections.Counter(f for p in P.values() for f in p["fields"]).most_common(12))},
        "epoch_edges": dict(epoch_edges),
        "calibration": calib, "better_method": better,
        "proposals": prop,
        "agreement": {"both": len(both), "agree": sum(v["agree"] for v in both), "rate": sum(v["agree"] for v in both) / len(both) if both else None,
                      "chance": agree_chance, "chain_covered": sum(1 for v in prop.values() if v["chain_role"]), "unbound": len(prop)},
    }


if __name__ == "__main__":
    d = build()
    (REPO / "docs/data/ledger_graph.json").write_text(json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: d[k] for k in ("counts", "calibration", "better_method", "agreement")}, ensure_ascii=False, indent=1))
    print(json.dumps(d["epoch_edges"], ensure_ascii=False))
