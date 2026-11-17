"""spec/CTX_PREF_WC.md: the fixed rules and the estimator, on made-up conversations."""
import unittest

import numpy as np

from rsxv import ctx_pref_wc as W


class Rules(unittest.TestCase):
    def test_context(self):
        self.assertEqual(W.context("def f():\n  return 1"), "CODE")
        self.assertEqual(W.context("```js\nx\n```"), "CODE")
        self.assertEqual(W.context("I'm so stressed about my exams"), "PERSONAL")
        self.assertEqual(W.context("What is the capital of Peru"), "OTHER")

    def test_score(self):
        self.assertEqual(W.score("Thanks, that helps!"), 1)
        self.assertEqual(W.score("No, that's not what I asked"), -1)
        self.assertEqual(W.score("thanks but it still doesn't work"), 0)
        self.assertEqual(W.score("Now write a poem"), 0)
        self.assertEqual(W.score("x" * 300 + " thanks"), 0)       # beyond the first 300 characters

    def test_family(self):
        self.assertEqual(W.family("gpt-4-0314"), "GPT-4")
        self.assertEqual(W.family("gpt-3.5-turbo-0613"), "GPT-3.5")

    def test_events(self):
        E = W.Events()
        E.add_conversation([("user", "I feel stuck"), ("assistant", "I'm sorry, that sounds hard."),
                            ("user", "thanks"), ("assistant", "Anything else?")], "gpt-4")
        self.assertEqual(E.steps["events"], 1)
        self.assertEqual(E.steps["turns_without_next"], 1)
        A = E.arrays()
        self.assertEqual((int(A["ctx"][0]), int(A["s"][0]), int(A["y"][0]), int(A["fam"][0])), (0, 1, 1, 1))

    def test_stratified_estimator(self):
        rng = np.random.default_rng(0)
        n = 4000
        f = rng.integers(0, 2, n)
        y = np.where(f == 1, rng.choice([1, 0], n, p=[0.6, 0.4]), rng.choice([1, 0], n, p=[0.4, 0.6]))
        st = rng.integers(0, 10, n)
        conv = np.arange(n)
        r = W.stratified(y, f, st, conv, 1.96)
        self.assertTrue(r["usable"])
        self.assertAlmostEqual(r["est"], 0.2, delta=0.05)
        self.assertGreater(r["lo"], 0)
        small = W.stratified(y[:100], f[:100], st[:100], conv[:100], 1.96)
        self.assertFalse(small["usable"])

    def test_verdict_needs_both_families(self):
        good = {"usable": True, "est": 0.1, "lo": 0.05, "hi": 0.15}
        bad = {"usable": True, "est": -0.1, "lo": -0.15, "hi": -0.05}
        mid = {"usable": True, "est": 0.0, "lo": -0.01, "hi": 0.01}
        cells = {"S|PERSONAL": good, "S|CODE": bad, "S|OTHER": mid, "Q|PERSONAL": mid, "Q|CODE": mid, "Q|OTHER": mid}
        fam = {f"{k}|{fm}": v for k, v in cells.items() for fm in W.FAMILIES}
        self.assertEqual(W.verdict(cells, fam)["verdict"], "CONTEXT-DEPENDENT")
        fam["S|CODE|GPT-4"] = good
        self.assertEqual(W.verdict(cells, fam)["verdict"], "SAME DIRECTION")


if __name__ == "__main__":
    unittest.main()
