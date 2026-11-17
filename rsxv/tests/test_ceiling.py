"""spec/CEILING.md §3: W5-CEILING's mapping and decision rule on constructed cases, and a deterministic quick run."""
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from rsxv import ceiling_experiments as CE  # noqa: E402


class Mapping(unittest.TestCase):
    def test_best_table_positive_only(self):
        eff = {("calm", "BEAR"): 0.2, ("calm", "TIGER"): 0.5, ("rising", "BEAR"): -0.1, ("loaded", "LION"): 0.0}
        self.assertEqual(CE.best_table(eff), {"calm": "TIGER", "rising": "LION", "loaded": "LION", "crisis": "LION"})

    def test_first_matching_function_and_unmatched_stays_lion(self):
        src = {"calm": "BEAR", "rising": "RAVEN", "loaded": "LION", "crisis": "TIGER"}
        sroles = {"STABILISE": "BEAR", "RESTORE": "BEAR", "DRIVE": "TIGER"}
        troles = {"STABILISE": "LEOPARD", "RESTORE": "EAGLE", "DRIVE": "TIGER"}
        self.assertEqual(CE.map_table(src, sroles, troles), {"calm": "LEOPARD", "rising": "LION", "loaded": "LION", "crisis": "TIGER"})


class Decision(unittest.TestCase):
    def test_verdict_and_line(self):
        pos, neg = {"diff": 0.1, "lo": 0.01, "hi": 0.2}, {"diff": 0.0, "lo": -0.01, "hi": 0.02}
        self.assertEqual(CE.verdict(pos, neg), {"value": True, "room": False})
        dirs = [{"source": "a", "target": "b", "verdict": {"value": True, "room": False}}]
        self.assertFalse(CE.line_verdict(dirs)["pass"])
        self.assertIn("no W5f", CE.line_verdict(dirs)["decision"])
        dirs.append({"source": "c", "target": "d", "verdict": {"value": True, "room": True}})
        lv = CE.line_verdict(dirs)
        self.assertTrue(lv["pass"]); self.assertEqual(lv["room_in"], ["c → d"])


class Quick(unittest.TestCase):
    def test_quick_run_is_deterministic(self):
        a = CE.run(quick=True); b = CE.run(quick=True)
        self.assertEqual(a, b)
        self.assertEqual(len(a["directions"]), 4)


if __name__ == "__main__":
    unittest.main()
