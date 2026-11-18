"""spec/GUARD_GAIN.md H1-H4."""
import pathlib
import sys
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / "rsxv")]
from rsxv import organism_env as E  # noqa: E402

R = E.guard_gain()


class GuardGain(unittest.TestCase):
    def test_h1_six_signatures(self):
        self.assertTrue(R["H1"])

    def test_h2_prevention_helps_the_whole(self):
        self.assertTrue(R["H2"])
        self.assertAlmostEqual(R["margins"]["v4"]["ORGANISM_minus_BEAR"]["estimate"], 0.0530668111111111)

    @unittest.expectedFailure
    def test_h3_registered(self):
        """Registered stretch: >= +0.146 (10x). Observed +0.0531 (3.6x the V2 margin). Recorded in spec/GUARD_GAIN.md §3."""
        self.assertTrue(R["H3"])


if __name__ == "__main__":
    unittest.main()
