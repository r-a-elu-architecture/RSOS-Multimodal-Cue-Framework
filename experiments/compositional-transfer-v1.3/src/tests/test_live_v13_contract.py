"""Regression checks for the public v1.3 interactive benchmark contract.

Run: python -m unittest discover -s src/tests -p 'test_live_v13_contract.py' -v
All outcomes are synthetic. No human effect is inferred.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import transfer_benchmark as v13  # noqa: E402


class LiveV13ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = v13.run(seed=63011, people=3, calibration=24, tests=16, threshold=.23)

    def test_policy_count_and_sample_size(self):
        self.assertEqual(len(v13.MODELS), 11)
        self.assertEqual(len(self.df), 8 * 3 * 16 * 11)
        self.assertEqual(len(v13.ARMS), 180)
        self.assertEqual(v13.N_C, 4)

    def test_generic_same_gate_exact_negative_control(self):
        p = self.df.pivot(index=['seed', 'world', 'person', 'trial'], columns='model', values='regret')
        self.assertTrue((p['generic_same_gate'] == p['rsia_evidence_gate']).all())
        choices = self.df.pivot(index=['seed', 'world', 'person', 'trial'], columns='model', values='selected_program')
        self.assertTrue((choices['generic_same_gate'] == choices['rsia_evidence_gate']).all())

    def test_generic_same_relations_exact_negative_control(self):
        p = self.df.pivot(index=['seed', 'world', 'person', 'trial'], columns='model', values='regret')
        self.assertTrue((p['generic_same_relations'] == p['rsos_relational']).all())

    def test_oracle_zero_regret(self):
        self.assertTrue((self.df[self.df.model=='oracle'].regret.abs() < 1e-12).all())

    def test_model_outputs_finite_nonnegative_regret(self):
        import numpy as np
        self.assertTrue(np.isfinite(self.df.regret.to_numpy()).all())
        self.assertTrue((self.df.regret.to_numpy() >= -1e-12).all())

    def test_threshold_uses_evidence_gate(self):
        gated = self.df[self.df.model=='rsia_evidence_gate']
        self.assertTrue((gated.uses_relation == (gated.eta >= .23)).all())


if __name__ == '__main__':
    unittest.main()
