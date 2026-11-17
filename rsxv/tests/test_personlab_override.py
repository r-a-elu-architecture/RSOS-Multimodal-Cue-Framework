"""spec/PERSONLAB.md §7b: the override test's machinery, on made-up conversations."""
import unittest

from rsxv.personlab import override as O


def dlg(*turns):
    return [{"speaker": s, "content": c, "annotation": ({"strategy": st} if st else {})} for s, c, st in turns]


class Override(unittest.TestCase):
    def test_content_and_targets(self):
        self.assertEqual(O.content("I believe resting is LAZY, really"), {"believe", "resting", "lazy"})
        stmts = [O.content("resting is lazy and weak")]
        self.assertTrue(O.targets(["Is resting really lazy?"], stmts))
        self.assertFalse(O.targets(["Resting helps."], stmts))      # one shared word is not enough

    def test_blocks_and_held_out_only(self):
        d = dlg(("seeker", "s1", None), ("supporter", "a", "Question"), ("seeker", "s2", None),
                ("supporter", "resting lazy", "Providing Suggestions"), ("supporter", "more", None), ("seeker", "s3", None))
        bl = list(O.blocks(d, 0))
        self.assertEqual([(i, j, st) for i, j, _, st, _ in bl], [(1, 2, "Question"), (2, 3, "Providing Suggestions")])
        ev = O.events("c", d, cut=3, stress={1: 4, 2: 4, 3: 2}, own=[O.content("resting is lazy")], placebo=[O.content("money rent")])
        self.assertEqual(len(ev), 1)                                   # only the block after the cut
        self.assertEqual((ev[0]["d"], ev[0]["action"], ev[0]["band"], ev[0]["t"], ev[0]["p"]), (-2, "SUGGEST", "high", True, False))

    def test_stratified_and_bootstrap(self):
        ev = []
        for c in range(40):
            for k in range(4):
                t = k % 2 == 0
                ev.append({"conv": c, "d": -1.0 if t else 0.0, "action": "SUGGEST", "band": "mid", "t": t, "p": k < 2})
        self.assertAlmostEqual(O.stratified(ev, "t"), -1.0)
        r = O.bootstrap(ev, B=200)
        self.assertLess(r["target"][2], 0)

    def test_weighted_kappa(self):
        self.assertAlmostEqual(O.weighted_kappa([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]), 1.0)
        self.assertLess(O.weighted_kappa([1, 2, 3, 4, 5], [5, 4, 3, 2, 1]), 0)


if __name__ == "__main__":
    unittest.main()
