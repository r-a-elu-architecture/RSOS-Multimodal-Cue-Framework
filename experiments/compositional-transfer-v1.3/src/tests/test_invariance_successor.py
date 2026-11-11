"""Run with python -m unittest discover -s src/tests -p test_invariance_successor.py -v"""
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import transfer_benchmark as original
import invariance_successor as candidate

class InvarianceSuccessorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.new=candidate.run(63011,people=3,tests=2)
        cls.old=original.run(63011,people=3,tests=2)

    def test_all_original_policies_included(self):
        self.assertEqual(self.new.model.nunique(), len(original.MODELS)+6)

    def test_identical_generic_controls(self):
        self.assertTrue(candidate.exact_tie(self.new,"invariance_guard","generic_same_invariance"))
        self.assertTrue(candidate.exact_tie(self.new,"invariance_blend","generic_same_blend"))
        self.assertTrue(candidate.exact_tie(self.new,"rsia_evidence_gate","generic_same_gate"))

    def test_original_v13_policy_parity(self):
        for policy in original.MODELS:
            a=self.new[self.new.model==policy].sort_values(["world","person","trial"])
            b=self.old[self.old.model==policy].sort_values(["world","person","trial"])
            np.testing.assert_array_equal(a.selected_program.to_numpy(),b.selected_program.to_numpy())
            np.testing.assert_allclose(a.regret.to_numpy(),b.regret.to_numpy(),rtol=0,atol=1e-14)

    def test_zero_penalty_is_generic_threeway_cv(self):
        x=candidate.run(63011,people=2,tests=3,weight=0.)
        self.assertTrue(candidate.exact_tie(x,"invariance_guard","generic_threeway_cv"))

    def test_novel_context_is_excluded_from_ood_calibration(self):
        for person in range(3):
            _,_,_,contexts,_,_,test_contexts=candidate.synthetic_person(67011,6,person,24,16,True)
            self.assertFalse((contexts==3).any())
            self.assertTrue((test_contexts[::2]==3).all())

    def test_no_hidden_world_parameter_in_selector(self):
        import inspect
        self.assertNotIn("world",inspect.signature(candidate.scores).parameters)

    def test_regret_and_oracle(self):
        self.assertTrue(np.isfinite(self.new.regret.to_numpy()).all())
        self.assertTrue((self.new.regret.to_numpy() >= -1e-12).all())
        self.assertEqual(float(self.new[self.new.model=="oracle"].regret.sum()),0.)

    def test_repeatability(self):
        duplicate=candidate.run(63011,people=3,tests=2)
        np.testing.assert_array_equal(self.new.selected_program.to_numpy(),duplicate.selected_program.to_numpy())

    def test_bad_inputs_rejected(self):
        for args in (dict(people=0),dict(calibration=3),dict(weight=-1),dict(temperature=0)):
            with self.assertRaises(ValueError): candidate.run(63011,**args)

if __name__=="__main__":unittest.main()
