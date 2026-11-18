"""spec/LEDGER_GRAPH.md G1-G7."""
import json
import pathlib
import sys
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "architecture"))
import ledger_graph as G  # noqa: E402

D = G.build()


class Graph(unittest.TestCase):
    def test_g1_parts(self):
        c = D["counts"]
        self.assertGreaterEqual(c["with_title_and_content"] / c["tiers"], 0.95)

    @unittest.expectedFailure
    def test_g2_registered(self):
        """Registered: >= 80% of tiers with an edge. Observed 225 of 293 (76.8%). Recorded in spec/LEDGER_GRAPH.md §3."""
        self.assertGreaterEqual(D["counts"]["tiers_with_edge"] / D["counts"]["tiers"], 0.80)

    @unittest.expectedFailure
    def test_g3_registered(self):
        """Registered: chain accuracy >= 2 x chance. Observed 0.286 vs chance 0.211."""
        self.assertGreaterEqual(D["calibration"]["chain"]["accuracy"], 2 * D["calibration"]["chance"])

    @unittest.expectedFailure
    def test_g4_registered(self):
        """Registered: keyword accuracy >= 2 x chance. Observed 0.355 vs chance 0.211."""
        self.assertGreaterEqual(D["calibration"]["keyword"]["accuracy"], 2 * D["calibration"]["chance"])

    def test_g5_coverage(self):
        a = D["agreement"]
        self.assertGreaterEqual(a["chain_covered"] / a["unbound"], 0.5)

    def test_observed_numbers_pinned(self):
        self.assertEqual(D["counts"]["tiers_with_edge"], 225)
        self.assertAlmostEqual(D["calibration"]["chain"]["accuracy"], 22 / 77)
        self.assertAlmostEqual(D["calibration"]["keyword"]["accuracy"], 38 / 107)
        self.assertEqual((D["agreement"]["agree"], D["agreement"]["both"]), (34, 138))

    def test_g7_unchanged_and_reproducible(self):
        tmap = json.loads((REPO / "docs/data/tier_map.json").read_text(encoding="utf-8"))["tiers"]
        self.assertEqual(sum(1 for v in tmap.values() if v.get("response")), 107)
        on_disk = json.loads((REPO / "docs/data/ledger_graph.json").read_text(encoding="utf-8"))
        self.assertEqual(on_disk, json.loads(json.dumps(D, ensure_ascii=False, sort_keys=True)))


if __name__ == "__main__":
    unittest.main()
