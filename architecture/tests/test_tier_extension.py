"""spec/TIER_BINDINGS_EXTENSION.md: the extension stays apart and covers every unbound tier."""
import hashlib
import json
import pathlib
import sys
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "architecture"))
import organism as O  # noqa: E402
import tier_extension as X  # noqa: E402


class Extension(unittest.TestCase):
    def test_originals_unchanged(self):
        meta = X.load()["originals_sha256_at_creation"]
        for rel, h in meta.items():
            self.assertEqual(hashlib.sha256((REPO / rel).read_bytes()).hexdigest(), h, rel)

    def test_covers_every_unbound_tier(self):
        tiers = O.load("docs/data/tier_map.json")["tiers"]
        unbound = {t for t, v in tiers.items() if not v.get("response")}
        ext = X.load()["bindings"]
        self.assertEqual(set(ext), unbound)
        self.assertTrue(all(v["role"] in O.ROLES for v in ext.values()))
        r = X.roles()
        self.assertEqual(len(r), len(tiers))
        self.assertEqual(sum(1 for v in r.values() if v["source"] == "extension"), 186)


if __name__ == "__main__":
    unittest.main()
