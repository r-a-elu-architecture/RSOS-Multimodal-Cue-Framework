"""spec/PERSONLAB.md §6: the profile-driven simulated person."""
import copy
import unittest

from rsxv.personlab import person as PP
from rsxv.personlab import schema as S


def prof():
    p = S.example()
    p["initial_intensity"] = 4
    return p


class Person(unittest.TestCase):
    def test_deterministic(self):
        a = PP.ProfilePerson(prof(), seed=7); b = PP.ProfilePerson(prof(), seed=7)
        ra = [a.step("SUGGEST")["I"] for _ in range(30)]; rb = [b.step("SUGGEST")["I"] for _ in range(30)]
        self.assertEqual(ra, rb)

    def test_cues_never_block(self):
        P = copy.deepcopy(PP.DEFAULTS); P["rho"] = 0.5; P["act"]["NONE"]["r"] = 0.0
        x = PP.ProfilePerson(prof(), P, seed=1)
        for _ in range(200):
            x.step("NONE")
        self.assertGreater(x.cues, 60)            # roughly rho * (1 + 0.25 * signals) * 200; never stuck at 1

    def test_action_directions(self):
        P = copy.deepcopy(PP.DEFAULTS); P["rho"] = 0.0
        P["act"]["STABILISE"].update({"r": 0.4, "m": 0.1}); P["act"]["EXPLORE"].update({"e": 0.3})
        x = PP.ProfilePerson(prof(), P, initial_intensity=4)
        I0, u0 = x.I, x.u
        x.step("STABILISE")
        self.assertLess(x.I, I0); self.assertLess(x.u, u0)
        x.step("EXPLORE"); self.assertGreater(x.k, 0)
        calm = PP.ProfilePerson(prof(), P, initial_intensity=1)
        calm.step("SUGGEST"); self.assertGreater(calm.g, 0)               # calm enough: progress
        hot = PP.ProfilePerson(prof(), P, initial_intensity=5)
        u_hot = hot.u; hot.step("SUGGEST")
        self.assertEqual(hot.g, 0); self.assertGreaterEqual(hot.u, min(1.0, u_hot))   # too aroused: no progress

    def test_targets_rule(self):
        p = prof()
        self.assertEqual(PP.targets(p), (["skills", "mission"], "desired_any"))
        p["desired"]["mission"][0]["agreed"] = True
        self.assertEqual(PP.targets(p), (["mission"], "desired_agreed"))
        p["desired"] = {}
        self.assertEqual(PP.targets(p)[1], "current")
        p["current"] = {}
        self.assertEqual(PP.targets(p), (["behaviour"], "default"))

    def test_strategies_map_to_actions(self):
        self.assertEqual(len(PP.STRATEGY_TO_ACTION), 8)
        self.assertEqual(PP.STRATEGY_TO_ACTION["Providing Suggestions"], "SUGGEST")


if __name__ == "__main__":
    unittest.main()
