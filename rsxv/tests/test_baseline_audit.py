"""spec/BASELINE_AUDIT.md Q2: the audit's pure rules."""
import unittest

from rsxv import baseline_audit as B
from rsxv import world as W


class Rules(unittest.TestCase):
    def test_outcome_rule(self):
        self.assertEqual(B.outcome(0.01, 0.05), "HOLDS")
        self.assertEqual(B.outcome(-0.01, 0.05), "TIES")
        self.assertEqual(B.outcome(-0.05, -0.01), "LOSES")
        self.assertEqual(B.outcome(0.5, 0.9, identical=True), "TIES")

    def test_stab_only_table(self):
        t = B.stab_only_table({"STABILISE": "BEAR", "DRIVE": "TIGER"})
        self.assertEqual(t, {c: "BEAR" for c in W.CONTEXTS})
        self.assertEqual(B.stab_only_table({"DRIVE": "TIGER"}), {c: "LION" for c in W.CONTEXTS})

    def test_fixed_best_by_pilot_mean(self):
        means = {m: 0.0 for m in W.MODES}
        means["BEAR"] = 0.3
        self.assertEqual(B.fixed_best(means), "BEAR")
        self.assertEqual(B.fixed_best({m: 0.0 for m in W.MODES}), W.MODES[0])

    def test_mcnemar_known_case(self):
        self.assertAlmostEqual(B.mcnemar_one_sided(5, 0), 1 / 32)
        self.assertAlmostEqual(B.mcnemar_one_sided(0, 0), 1.0)
        self.assertAlmostEqual(B.mcnemar_one_sided(1, 1), 0.75)


if __name__ == "__main__":
    unittest.main()
