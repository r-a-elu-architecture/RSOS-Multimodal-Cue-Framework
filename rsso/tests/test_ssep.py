import pathlib
import sys
import unittest

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent)]
from rsso import ssep as S  # noqa: E402


def person(rng, f, brain, pickup, phase=2.0):
    return [S.sim_eeg(rng, c, f, brain, pickup, phase=phase) for c in ("vibration", "sham", "rest")]


class Ssep(unittest.TestCase):
    def test_pickup_alone_is_not_a_response(self):
        rng = np.random.default_rng(1)
        r = S.analyze(*person(rng, 12.0, 0.0, 0.8), 12.0, rng)
        self.assertTrue(r["pickup_present"])
        self.assertTrue(r["naive_claims"])
        self.assertFalse(r["found"])
        self.assertEqual(r["verdict"], "no response beyond the electrical pickup")

    def test_a_real_response_is_found_through_the_pickup(self):
        rng = np.random.default_rng(2)
        r = S.analyze(*person(rng, 7.8, 0.8, 0.6), 7.8, rng)
        self.assertTrue(r["found"])
        self.assertEqual(r["verdict"], "a response at the rhythm beyond the electrical pickup")

    def test_bins(self):
        self.assertEqual(int(round(7.8 * S.TRIAL_S)), 39)
        self.assertEqual(int(round(12 * S.TRIAL_S)), 60)


if __name__ == "__main__":
    unittest.main()
