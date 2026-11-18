"""spec/ORGANISM.md O1: the atlas is complete and reproducible."""
import json
import pathlib
import sys
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "architecture"))
import organism as O  # noqa: E402


class Atlas(unittest.TestCase):
    def test_o1_complete(self):
        c = O.build()["checks"]
        self.assertEqual(c["tiers_placed"], c["tiers"])
        self.assertGreaterEqual(c["metric_values_attached"] / c["metric_values"], 0.99)
        self.assertEqual(c["tiers_with_response_bound"], c["tiers_with_response"])

    def test_every_response_has_one_role(self):
        rs = [r for v in O.ROLES.values() for r in v["responses"]]
        self.assertEqual(len(rs), len(set(rs)))
        self.assertEqual(set(rs), set(json.loads((REPO / "docs/data/tier_map.json").read_text(encoding="utf-8"))["responses"]))

    def test_file_is_reproducible(self):
        on_disk = json.loads((REPO / "docs/data/organism.json").read_text(encoding="utf-8"))
        self.assertEqual(on_disk, json.loads(json.dumps(O.build(), ensure_ascii=False, sort_keys=True)))


if __name__ == "__main__":
    unittest.main()
