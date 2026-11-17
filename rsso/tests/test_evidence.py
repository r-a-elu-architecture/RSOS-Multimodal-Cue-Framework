"""spec/EVIDENCE_LABELS.md: repository checks L1-L6 and reproducibility (L7 is scripts/check_evidence.py)."""
import copy
import importlib.util
import json
import pathlib
import re
import sys
import unittest
from unittest import mock

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "rsso"))
from rsso import profiles  # noqa: E402

spec = importlib.util.spec_from_file_location("evidence", REPO / "architecture/evidence.py")
EV = importlib.util.module_from_spec(spec)
spec.loader.exec_module(EV)
DATA = json.loads((REPO / "docs/data/evidence.json").read_text(encoding="utf-8"))
MAP = json.loads((REPO / "architecture/evidence_map.json").read_text(encoding="utf-8"))


def live_pages():
    out = []
    for f in sorted((REPO / "docs").glob("*.html")):
        s = f.read_text(encoding="utf-8")
        if "This page has been retired" not in s:
            out.append((f.stem, s))
    return out


class Labels(unittest.TestCase):
    def test_L1_every_live_page_has_one_generated_label(self):
        pages = live_pages()
        self.assertEqual({p for p, _ in pages}, set(DATA["pages"]))
        for p, s in pages:
            self.assertEqual(s.count(EV.START), 1, p)
            self.assertEqual(s.count(EV.END), 1, p)
            block = re.search(re.escape(EV.START) + "(.*?)" + re.escape(EV.END), s, re.S).group(0)
            self.assertEqual(block, EV.label_html(DATA["pages"][p]), p)
            self.assertLess(s.index("<h1"), s.index(EV.START), p)

    def test_L1_generator_is_reproducible(self):
        self.assertEqual(EV.build(), DATA)
        for rel, content in EV.outputs(EV.build()).items():
            self.assertEqual((REPO / rel).read_text(encoding="utf-8"), content, rel)

    def test_L2_basis_files_exist_and_E3_E4_cite_rows(self):
        for p, v in MAP["pages"].items():
            for b in v.get("basis", []):
                self.assertTrue((REPO / b).exists(), f"{p}: {b}")
            if v.get("level") in ("E3", "E4"):
                self.assertTrue(v.get("families"), p)
        bad = copy.deepcopy(MAP)
        bad["pages"]["anchors"]["basis"] = ["rsso/results/no_such_file.md"]
        with mock.patch.object(EV, "load", side_effect=lambda rel: bad if "evidence_map" in rel else json.loads((REPO / rel).read_text(encoding="utf-8"))):
            with self.assertRaises(ValueError):
                EV.build()

    def test_L3_every_register_row_has_exactly_one_source(self):
        reg = json.loads((REPO / "docs/data/results_register.json").read_text(encoding="utf-8"))
        for r in reg["rows"]:
            self.assertIn(EV.row_source(r["test"], MAP["row_sources"]), MAP["row_sources"])
        self.assertEqual(sum(sum(c.values()) for c in DATA["register_by_source"].values()), len(reg["rows"]))
        with self.assertRaises(ValueError):
            EV.row_source("Z9, a new row nobody placed", MAP["row_sources"])

    def test_L4_no_E5_without_people_rows(self):
        self.assertEqual(MAP["row_sources"]["people"], [])
        self.assertFalse(any(v.get("level") == "E5" for v in DATA["pages"].values()))
        bad = copy.deepcopy(MAP)
        bad["pages"]["anchors"]["level"] = "E5"
        with mock.patch.object(EV, "load", side_effect=lambda rel: bad if "evidence_map" in rel else json.loads((REPO / rel).read_text(encoding="utf-8"))):
            with self.assertRaises(ValueError):
                EV.build()
        for v in DATA["pages"].values():
            self.assertTrue(v["text"].endswith(EV.TAIL))

    def test_L5_no_overclaim_words(self):
        for p, s in live_pages():
            self.assertEqual(EV.overclaims(EV.visible_text(s)), [], p)
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertEqual(EV.overclaims(readme), [])
        self.assertEqual(EV.overclaims("a validated instrument of their choice"), [])
        self.assertEqual(EV.overclaims("This is proven to work."), ["proven"])

    def test_L6_labels_carry_no_clinical_words(self):
        rx = re.compile(profiles.CLINICAL_WORDS, re.I)
        for p, v in DATA["pages"].items():
            self.assertIsNone(rx.search(v["text"]), p)


if __name__ == "__main__":
    unittest.main()
