"""FIXES_NIGHT E-1: row sources use the longest key, and stated-model rows can never count as recorded or public data."""
import json
import os
import sys

import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import evidence as E  # noqa: E402

with open(os.path.join(HERE, "evidence_map.json"), encoding="utf-8") as _f:
    SOURCES = json.load(_f)["row_sources"]


def test_longest_key_wins():
    assert E.row_source("Round 8e, supporter action", SOURCES) == "public"
    assert E.row_source("Round 8f, person model v3", SOURCES) == "sim"
    assert E.row_source("Round 8f-B, is person model v3 adopted", SOURCES) == "sim"
    assert E.row_source("W5-R2, failure repurposing", SOURCES) == "sim"
    assert E.row_source("H-CTX2, hh-rlhf", SOURCES) == "public"


def test_the_old_prefix_rule_would_have_filed_8f_as_public():
    hits = [src for src, keys in SOURCES.items() for k in keys if "Round 8f, person model".startswith(k)]
    assert sorted(hits) == ["public", "sim"]          # ambiguous under the old rule; only the "Round 8" key existed then


def test_stated_model_rows_are_never_recorded_or_public():
    row = {"test": "Round 8z", "result": "x", "meaning": "Stated models (results/x.json)"}
    for src in ("public", "record"):
        with unittest.TestCase().assertRaises(ValueError):
            E.check_stated(row, src)
    E.check_stated(row, "sim")


def test_every_register_row_obeys_L4():
    with open(os.path.join(HERE, "..", "docs", "data", "results_register.json"), encoding="utf-8") as f:
        reg = json.load(f)
    for r in reg["rows"]:
        E.check_stated(r, E.row_source(r["test"], SOURCES))


class EvidenceSources(unittest.TestCase):   # so that unittest discovery in check_all.sh runs the functions above
    def test_all(self):
        for f in (test_longest_key_wins, test_the_old_prefix_rule_would_have_filed_8f_as_public,
                  test_stated_model_rows_are_never_recorded_or_public, test_every_register_row_obeys_L4):
            f()
