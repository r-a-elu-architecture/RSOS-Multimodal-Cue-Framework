"""Read-only overlay of the author's tier role bindings (spec/TIER_BINDINGS_EXTENSION.md).

The extension file is kept apart from the ledger on purpose: docs/data/tier_map.json and docs/data/ledger.json are never
written here. roles() gives every tier's role: the original response's role where the tier map has one, else the
author's binding from the extension.
"""
from __future__ import annotations

import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "architecture"))
import organism as O  # noqa: E402

EXTENSION = "docs/data/EXTENSION_tier_role_bindings_author_2026-11-18.json"


def load():
    return json.loads((REPO / EXTENSION).read_text(encoding="utf-8"))


def roles() -> dict:
    tiers = O.load("docs/data/tier_map.json")["tiers"]
    ext = load()["bindings"]
    out = {}
    for t, v in tiers.items():
        if v.get("response") in O.ROLE_OF:
            out[t] = {"role": O.ROLE_OF[v["response"]], "source": "ledger"}
        elif t in ext:
            out[t] = {"role": ext[t]["role"], "source": "extension"}
    return out
