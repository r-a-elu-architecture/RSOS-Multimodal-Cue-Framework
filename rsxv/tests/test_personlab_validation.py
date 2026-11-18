"""spec/PERSONLAB.md §7: the validation machinery, on made-up data."""
import unittest

import numpy as np

from rsxv.personlab import validation as V


class Validate(unittest.TestCase):
    def test_actions_from_strategies(self):
        conv = {"dialog": [{"speaker": "seeker", "content": "x"},
                           {"speaker": "supporter", "annotation": {"strategy": "Question"}},
                           {"speaker": "supporter", "annotation": {"strategy": "Providing Suggestions"}},
                           {"speaker": "supporter", "annotation": {}}]}
        self.assertEqual(V.actions(conv), ["EXPLORE", "SUGGEST", "NONE"])

    def test_predict_is_bounded_and_monotone(self):
        th = [0.3, 0, 0, 0, 0, 0, 0]
        self.assertAlmostEqual(V.predict_final(th, 4.0, ["STABILISE"] * 5), 2.5)
        self.assertEqual(V.predict_final(th, 4.0, ["STABILISE"] * 50), 1.0)
        up = [0, 0, 0, 0, 0, 0.1, 0]
        self.assertGreater(V.predict_final(up, 2.0, ["NONE"] * 3, signals=4), V.predict_final(up, 2.0, ["NONE"] * 3))

    def test_fit_recovers_a_simple_truth(self):
        truth = [0.2, 0.0, 0.1, 0.0, 0.0, 0.0, 0.0]
        rng = np.random.default_rng(0)
        dev = []
        for _ in range(60):
            acts = list(rng.choice(V.ACTS, 8))
            i0 = float(rng.integers(3, 6))
            dev.append((i0, acts, V.predict_final(truth, i0, acts)))
        th, L = V.fit(dev, starts=2)
        self.assertLess(L, 0.05)

    def test_linear_and_interval(self):
        rows = [(i0, ["STABILISE"] * k, i0 - 0.1 * k) for i0 in (3.0, 4.0, 5.0) for k in range(5)]
        c = V.linear_fit(rows)
        self.assertAlmostEqual(V.linear_predict(c, 4.0, ["STABILISE"] * 2), 3.8, places=6)
        m, lo, hi = V.paired_interval([0.1] * 50, [0.5] * 50, 0.95)
        self.assertLess(hi, 0)


if __name__ == "__main__":
    unittest.main()
