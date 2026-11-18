"""Glyph proposals for the archetypes without one (spec/WHOLE_ORGANISM.md §2.3). Writes a separate extension file; the
nodes module and the ledger are not changed. Proposals only: the author chooses.

    python3 architecture/glyph_proposals.py
"""
from __future__ import annotations

import collections
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "architecture"))
import organism as O  # noqa: E402
import tier_extension as X  # noqa: E402

OUT = "docs/data/EXTENSION_glyph_proposals_2026-11-18.json"
GLYPHLIKE = re.compile(r"^[^\w\[\](){}\"'.,:;]+$")      # a symbol, not a word or a bracketed name


def build() -> dict:
    parts = json.loads((REPO / "docs/data/ledger_graph.json").read_text(encoding="utf-8"))["parts"]
    roles = X.roles()
    by_role = collections.defaultdict(list)
    for t, v in roles.items():
        p = parts.get(t, {})
        g = p.get("glyph_to") or p.get("glyph")
        if g and GLYPHLIKE.match(g):
            by_role[v["role"]].append((g, t))
    taken = {"🦁", "🐉", "∅"}
    out = {}
    for role, spec in O.ROLES.items():
        if spec["archetype"] == "LION":
            continue
        cnt = collections.Counter(g for g, _ in by_role[role] if g not in taken)
        first = {}
        for g, t in sorted(by_role[role], key=lambda x: x[1]):
            first.setdefault(g, t)
        ranked = sorted(cnt, key=lambda g: (-cnt[g], first[g]))
        out[spec["archetype"]] = {"role": role, "proposed": ranked[0] if ranked else None,
                                  "from_tiers": sorted(t for g, t in by_role[role] if ranked and g == ranked[0]),
                                  "alternatives": [{"glyph": g, "tiers": cnt[g]} for g in ranked[1:4]],
                                  "chosen_by_author": None}
        if ranked:
            taken.add(ranked[0])
    return {"EXTENSION": "Glyph proposals for Raven, Eagle, Leopard, Tiger and Bear (18 Nov 2026)",
            "purpose": "Five archetypes have no ledger glyph in the nodes module (only Lion 🦁). Each proposal is the glyph that "
                       "appears most often on the tiers of the archetype's role (ledger and the author's binding extension).",
            "is_an_extension": "Kept apart: the nodes module and the ledger are unchanged. The author chooses; nothing is applied "
                               "until then.", "spec": "spec/WHOLE_ORGANISM.md", "proposals": out}


if __name__ == "__main__":
    d = build()
    (REPO / OUT).write_text(json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(d["proposals"], ensure_ascii=False, indent=1))
