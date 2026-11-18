"""spec/ADOPT_WC.md: words, event sets, the placebo and the verdict, on made-up conversations."""
import unittest

import numpy as np

from rsxv import adopt_wc as A


def conv(user, assistant, ts, vocab):
    a, u, f = A.conv_sets([("user", user), ("assistant", assistant)], vocab)
    return {"A": a, "U": u, "F": f, "ts": ts}


class Rules(unittest.TestCase):
    def test_words(self):
        self.assertEqual(A.words("The Gardening schedule, about Tomatoes!"), ["gardening", "schedule", "tomatoes"])
        self.assertEqual(A.words("short tiny"), [])

    def test_sets_and_first_turn(self):
        v = {}
        a, u, f = A.conv_sets([("user", "gardening tomatoes"), ("assistant", "compost compost mulching"),
                               ("user", "watering")], v)
        self.assertEqual(f, {v["gardening"], v["tomatoes"]})
        self.assertEqual(u, {v["gardening"], v["tomatoes"], v["watering"]})
        self.assertEqual(a[v["compost"]], 2)

    def test_event_and_placebo(self):
        v = {}
        prev_words = "compost mulching seedling pruning trellis fertiliser"
        next_words = "quantum electron photon neutron proton muonic"
        c = [conv("gardening", "starter words here", 0, v),
             conv("gardening tomatoes", prev_words, 1, v),
             conv("compost mulching question", "anything elsewise", 2, v),      # F uses two AI words from c1
             conv("physics", next_words, 3, v)]
        ev = A.person_events(c)
        k2 = [e for e in ev if abs(e["gap"] - 1) < 1e-9][0]                    # the event with k = 2
        self.assertAlmostEqual(k2["p_prev"], 2 / 6)
        self.assertEqual(k2["p_next"], 0.0)

    def test_words_typed_before_are_excluded(self):
        v = {}
        c = [conv("compost mulching seedling pruning trellis fertiliser", "hello friends", 0, v),
             conv("gardening", "compost mulching seedling pruning trellis fertiliser", 1, v),
             conv("compost", "nothing", 2, v),
             conv("x", "quantum electron photon neutron proton muonic", 3, v)]
        self.assertEqual(A.person_events(c), [])                                  # X_prev empty: all typed in c0

    def test_bootstrap_and_verdict(self):
        est, lo, hi = A.bootstrap(np.full(600, 0.02) + np.linspace(-0.001, 0.001, 600))
        self.assertGreater(lo, 0)
        self.assertEqual(A.analyse([])["verdict"], "NOT TESTABLE")


if __name__ == "__main__":
    unittest.main()
