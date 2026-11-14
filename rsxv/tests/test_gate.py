import pathlib, sys, unittest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from rsxv import gate as G
from rsxv import world as W


class TestGate(unittest.TestCase):
    def pilot(self, good, bad):
        p = {}
        for c in W.CONTEXTS:
            p[(c, "LION")] = [0.0, 0.1, -0.1, 0.05, -0.05] * 6
            p[(c, "BEAR")] = [x + good for x in p[(c, "LION")]]
            p[(c, "LEOPARD")] = [x + bad for x in p[(c, "LION")]]
        return p

    def test_admits_clear_gain_blocks_harm(self):
        table = {"calm": "LION", "rising": "BEAR", "loaded": "LEOPARD", "crisis": "TIGER"}
        gated, vmap = G.gate(table, self.pilot(good=0.5, bad=-0.5))
        self.assertEqual(gated, {"calm": "LION", "rising": "BEAR", "loaded": "LION", "crisis": "LION"})
        d = {r["context"]: r["decision"] for r in vmap}
        self.assertEqual(d["calm"], "admit (already baseline)")
        self.assertEqual(d["rising"], "admit")
        self.assertEqual(d["loaded"], "reject")
        self.assertEqual(d["crisis"], "reject: too few data")

    def test_small_gain_not_admitted(self):
        gated, _ = G.gate({c: "BEAR" for c in W.CONTEXTS}, self.pilot(good=0.001, bad=0))
        self.assertEqual(set(gated.values()), {"LION"})

    def test_welch_and_truth(self):
        d, lb = G.welch_lower([1, 2, 3, 4], [0, 1, 2, 3], 0.05)
        self.assertAlmostEqual(d, 1.0)
        self.assertLess(lb, 1.0)
        self.assertEqual(G.welch_lower([1], [2, 3], 0.05), (None, None))
        t = G.truth_effects({("calm", "LION"): [0.0, 0.0], ("calm", "BEAR"): [1.0, 1.0]})
        self.assertEqual(t[("calm", "BEAR")], 1.0)

    def test_mission_score_and_random_policy(self):
        for env in (W.PersonEnv, W.AgentEnv, W.AgentEnvV2):
            w = W.World(env(3), "random", seed=3, score="mission")
            w.run(10)
            self.assertEqual(len(w.trace), 10)
            self.assertEqual([t[2] for t in w.trace], w.rewards)
            self.assertEqual(w.switches, 0)


if __name__ == "__main__":
    unittest.main()


class TestGateV2Roles(unittest.TestCase):
    def test_min_cells_and_variance_floor(self):
        p = {("calm", "LION"): [0.0] * 4, ("calm", "BEAR"): [0.1] * 4}
        g, v = G.gate_v2({"calm": "BEAR"}, p)
        self.assertEqual(g["calm"], "LION")
        self.assertEqual(v[0]["decision"], "reject: too few data")
        p = {("calm", "LION"): [0.0] * 6, ("calm", "BEAR"): [0.05] * 6}
        g, _ = G.gate_v2({"calm": "BEAR"}, p)
        self.assertEqual(g["calm"], "LION")            # zero variance no longer admits a small gain
        g0, _ = G.gate({"calm": "BEAR"}, p)
        self.assertEqual(g0["calm"], "BEAR")           # the v1 weakness, kept for the record

    def test_roles_and_mapping(self):
        comps = [("calm", "LION", 0.1, 0.0)] * 3 + [("calm", "BEAR", 0.0, -0.5)] * 3 + [("calm", "TIGER", 0.5, 0.1)] * 3
        r = G.roles(comps)
        self.assertEqual(r, {"RESTORE": "BEAR", "DRIVE": "TIGER"})
        rt = G.role_table({"calm": "LEOPARD", "rising": "EAGLE"}, {"RESTORE": "LEOPARD", "DRIVE": "EAGLE"})
        self.assertEqual(rt["calm"], "RESTORE")
        self.assertEqual(rt["loaded"], "BASELINE")
        self.assertEqual(G.from_roles(rt, r)["calm"], "BEAR")
        self.assertEqual(G.from_roles(rt, r)["rising"], "TIGER")
