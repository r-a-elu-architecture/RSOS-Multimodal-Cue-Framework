"""spec/PERSONLAB.md §7c: the validity check's rules."""
import unittest

import numpy as np

from rsxv.personlab import validity as V


class Validity(unittest.TestCase):
    def test_rho_and_boot(self):
        x = np.arange(100); y = x + np.random.default_rng(0).normal(0, 5, 100)
        r, lo, hi = V.boot(x, y, B=300)
        self.assertGreater(r, 0.9); self.assertGreater(lo, 0.8)
        self.assertEqual(V.rho([1, 1, 1], [1, 2, 3]), 0.0)          # no variation -> 0, not nan

    def test_verdict(self):
        self.assertEqual(V.verdict({"a": (0.5, 0.2, 0.7), "b": (0.4, 0.1, 0.6), "c": (0.35, 0.05, 0.6)}), "VALID")
        self.assertEqual(V.verdict({"a": (0.5, 0.2, 0.7), "b": (0.2, 0.01, 0.4), "c": (0.35, 0.05, 0.6)}), "PARTIAL")
        self.assertEqual(V.verdict({"a": (0.5, 0.2, 0.7), "b": (0.2, -0.1, 0.4), "c": (0.35, 0.05, 0.6)}), "NOT VALID")


if __name__ == "__main__":
    unittest.main()
