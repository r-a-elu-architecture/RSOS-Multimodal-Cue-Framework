"""ORGANISM atlas (spec/ORGANISM.md §1): epochs → tiers → tier parts; metric families → metrics → values; Echo metrics;
the six World agent roles and how all of them connect. Deterministic; writes docs/data/organism.json.

    python3 architecture/organism.py
"""
from __future__ import annotations

import collections
import json
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[1]
ROLES = {   # spec/ORGANISM.md §1, fixed before computing
    "Monitor": {"archetype": "RAVEN", "responses": ["MIRROR", "RECALL"]},
    "Stabilise": {"archetype": "BEAR", "responses": ["STOP", "PAUSE", "GATE", "REENTRY"]},
    "Plan": {"archetype": "EAGLE", "responses": ["SEQUENCE", "GOVERN"]},
    "Repair": {"archetype": "LEOPARD", "responses": ["RECALIBRATE", "BLEND"]},
    "Drive": {"archetype": "TIGER", "responses": ["GLYPH_CUE", "OFFER"]},
    "Baseline": {"archetype": "LION", "responses": ["COMPRESS", "GENERATE"]},
}
ROLE_OF = {r: role for role, v in ROLES.items() for r in v["responses"]}
ECHO_FAMILY = "Language-model claims"
TIER_RE = re.compile(r"tiers?\W{0,3}(\d{3}(?:\.\d+|–\d{3})?)", re.I)
EPOCH_RE = re.compile(r"EPOCH\s+([IVX]+)")


def load(rel):
    return json.loads((REPO / rel).read_text(encoding="utf-8"))


def build() -> dict:
    ledger, tmap, mets = load("docs/data/ledger.json"), load("docs/data/tier_map.json"), load("docs/data/metrics.json")
    tiers = tmap["tiers"]
    # --- epochs → tiers, from the ledger's order
    epoch, epoch_of, echo_tiers = None, {}, set()
    for r in ledger["records"]:
        if r["kind"] == "epoch":
            m = EPOCH_RE.search(r["text"])
            epoch = m.group(1) if m else epoch
        elif r["kind"] == "tier":
            m = TIER_RE.search(r["text"][:120])
            if not m:
                continue
            tid = "T" + m.group(1).replace("–", "-")
            if tid in epoch_of and tid + "b" in tiers:      # a second record of the same number is the map's "b" tier
                tid += "b"
            if tid in tiers and tid not in epoch_of:
                epoch_of[tid] = epoch
                if re.search(r"\becho", r["text"], re.I):
                    echo_tiers.add(tid)
    epochs = collections.OrderedDict()
    for tid in sorted(tiers):
        epochs.setdefault(epoch_of.get(tid) or "unplaced", []).append(tid)
    # --- tiers → role
    role_of_tier = {tid: ROLE_OF.get(v.get("response")) for tid, v in tiers.items()}
    # --- metrics → values → tiers → roles (data-driven)
    fam = collections.defaultdict(list)
    attached = total = 0
    metric_roles, metric_epochs = {}, {}
    for m in mets["metrics"]:
        fam[m["family"]].append(m["code"])
        rc, ec = collections.Counter(), collections.Counter()
        for v in m["values"]:
            total += 1
            ec[v.get("epoch") or "none"] += 1
            if v.get("id") in tiers:
                attached += 1
                rc[role_of_tier.get(v["id"]) or "none"] += 1
        metric_roles[m["code"]] = dict(rc)
        metric_epochs[m["code"]] = dict(ec)
    # --- role profiles: tiers, metrics (by weight of attached values), Echo share
    roles = {}
    for role, spec in ROLES.items():
        rt = [tid for tid, r in role_of_tier.items() if r == role]
        mw = collections.Counter({c: rc.get(role, 0) for c, rc in metric_roles.items() if rc.get(role)})
        echo_w = sum(w for c, w in mw.items() if c in fam[ECHO_FAMILY])
        roles[role] = {**spec, "tiers": len(rt),
                       "tiers_by_epoch": dict(collections.Counter(epoch_of.get(t) or "unplaced" for t in rt)),
                       "tiers_built": sum(tiers[t].get("status") == "built" for t in rt),
                       "metric_values": sum(mw.values()), "echo_values": echo_w,
                       "top_metrics": [c for c, _ in mw.most_common(5)]}
    # --- connections: epoch × role and family × role
    epoch_role = collections.defaultdict(collections.Counter)
    for tid, e in epoch_of.items():
        epoch_role[e][role_of_tier.get(tid) or "none"] += 1
    family_role = collections.defaultdict(collections.Counter)
    for f, codes in fam.items():
        for c in codes:
            family_role[f].update(metric_roles[c])
    out = {
        "spec": "spec/ORGANISM.md", "roles": roles,
        "epochs": {e: {"tiers": len(v), "first": v[0], "last": v[-1],
                       "responses": dict(collections.Counter(tiers[t].get("response") or "none" for t in v)),
                       "layers": dict(collections.Counter(l for t in v for l in tiers[t].get("layers", []))),
                       "echo_tiers": sum(t in echo_tiers for t in v)} for e, v in epochs.items()},
        "families": {f: {"metrics": len(c), "codes": c, "values": sum(len(m["values"]) for m in mets["metrics"] if m["family"] == f),
                         "roles": dict(family_role[f])} for f, c in fam.items()},
        "echo": {"family": ECHO_FAMILY, "metrics": fam[ECHO_FAMILY], "tier_records_naming_echo": len(echo_tiers),
                 "values_by_epoch": dict(sum((collections.Counter(metric_epochs[c]) for c in fam[ECHO_FAMILY]), collections.Counter()))},
        "epoch_role": {e: dict(c) for e, c in epoch_role.items()},
        "checks": {"tiers": len(tiers), "tiers_placed": sum(1 for t in tiers if epoch_of.get(t)),
                   "metric_values": total, "metric_values_attached": attached,
                   "tiers_with_response": sum(1 for v in tiers.values() if v.get("response")),
                   "tiers_with_response_bound": sum(1 for v in tiers.values() if v.get("response") in ROLE_OF)},
    }
    return out


if __name__ == "__main__":
    d = build()
    (REPO / "docs/data/organism.json").write_text(json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                                                  encoding="utf-8")
    print(json.dumps(d["checks"]))
