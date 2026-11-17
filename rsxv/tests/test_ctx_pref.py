"""spec/CTX_PREF.md: the fixed rules, on made-up rows (no dataset needed)."""
import unittest

from rsxv import ctx_pref as C


def row(prompt, ra, rb, winner="model_a", code=False, lang="en", order=1):
    u = {"role": "user", "content": [{"type": "text", "text": prompt}]}
    return {"winner": winner, "language": lang, "evaluation_order": order, "is_code": code,
            "conversation_a": [u, {"role": "assistant", "content": ra}],
            "conversation_b": [u, {"role": "assistant", "content": rb}]}


class Rules(unittest.TestCase):
    def test_context(self):
        self.assertEqual(C.context("I'm so stressed about my exams", False), "PERSONAL")
        self.assertEqual(C.context("I feel stuck at work", False), "PERSONAL")
        self.assertEqual(C.context("I'm stressed, fix this function", True), "CODE")
        self.assertEqual(C.context("Explain photosynthesis", False), "OTHER")

    def test_features(self):
        self.assertTrue(C.feat_s("I'm sorry you're dealing with this."))
        self.assertTrue(C.feat_s("That sounds really hard. Here is a plan."))
        self.assertFalse(C.feat_s("Here is the answer: 42."))
        self.assertTrue(C.feat_q("Here is a plan.\n\nWhat would you like to start with?"))
        self.assertFalse(C.feat_q("Is it hard?\n\nHere is the plan."))

    def test_length_match(self):
        self.assertTrue(C.length_matched("a" * 100, "b" * 125))
        self.assertFalse(C.length_matched("a" * 100, "b" * 126))

    def test_wilson_and_z(self):
        self.assertAlmostEqual(C.z_of(0.95), 1.959964, places=4)
        lo, hi = C.wilson(50, 100, 0.95)
        self.assertLess(lo, 0.5)
        self.assertGreater(hi, 0.5)

    def test_inclusion_and_cells(self):
        s, plain = "I'm sorry, that sounds hard. " + "x" * 80, "y" * 100
        rows = [row("I feel overwhelmed", s, plain, "model_a"),           # S wins, PERSONAL, matched
                row("I feel overwhelmed", s, plain, "tie"),               # excluded: tie
                row("I feel overwhelmed", s, plain, "model_a", lang="ru"),  # excluded: language
                row("I feel overwhelmed", s, plain, "model_a", order=2),  # excluded: not the first vote
                row("Write a sort", plain, s, "model_a", code=True)]      # S loses, CODE
        R = C.analyse(rows)
        self.assertEqual(R["steps"]["non_empty"], 2)
        self.assertEqual(R["matched"]["S|PERSONAL"]["k"], 1)
        self.assertEqual(R["matched"]["S|CODE"]["k"], 0)
        self.assertEqual(R["matched"]["S|CODE"]["n"], 1)

    def test_verdict(self):
        cells = {(f, c): {"k": 50, "n": 100} for f in C.FEATURES for c in C.CONTEXTS}
        self.assertEqual(C.verdict(cells)["verdict"], "SAME DIRECTION")
        cells[("S", "PERSONAL")] = {"k": 400, "n": 500}
        cells[("S", "CODE")] = {"k": 100, "n": 500}
        self.assertEqual(C.verdict(cells)["verdict"], "CONTEXT-DEPENDENT")
        few = {(f, c): {"k": 5, "n": 10} for f in C.FEATURES for c in C.CONTEXTS}
        self.assertEqual(C.verdict(few)["verdict"], "INCONCLUSIVE")


if __name__ == "__main__":
    unittest.main()
