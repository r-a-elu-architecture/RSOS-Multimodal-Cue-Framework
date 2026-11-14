import pathlib, sys, unittest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from rsxv import person2 as P, world as W


class TestModule(unittest.TestCase):
    def test_state_dependence_and_calm_transfer(self):
        calm, act = P.Module(), P.Module()
        for _ in range(30):
            calm.train("calm")
            act.train("activated")
        self.assertGreater(calm.p_work("calm"), act.p_work("calm"))
        self.assertTrue(calm.calm_transfer())
        self.assertFalse(act.calm_transfer())

    def test_hypotheses(self):
        a, n = P.Module("arousal_deeper"), P.Module("neutral")
        for _ in range(10):
            a.train("activated"); n.train("activated")
        self.assertGreater(a.strength, n.strength)
        with self.assertRaises(AssertionError):
            P.Module("unknown")


class TestEnv(unittest.TestCase):
    def run_env(self, policy="rule", **kw):
        env = P.PersonEnvV2(seed=3, **kw)
        w = W.World(env, policy=policy, seed=3)
        for _ in range(120):
            w.tick()
        return env, w

    def test_two_way_gain(self):
        lo = P.PersonEnvV2(seed=5, gain=0.5, safety_on=False)
        hi = P.PersonEnvV2(seed=5, gain=1.5, safety_on=False)
        d_lo, d_hi = lo.body.s["distress"], hi.body.s["distress"]
        lo._trigger(); hi._trigger()
        self.assertGreater(hi.body.s["distress"] - d_hi, lo.body.s["distress"] - d_lo)

    def test_medication_lowers_impact(self):
        off = P.PersonEnvV2(seed=5, gain=1.0, safety_on=False)
        on = P.PersonEnvV2(seed=5, gain=1.0, med_on=True, safety_on=False)
        d_off, d_on = off.body.s["distress"], on.body.s["distress"]
        off._trigger(); on._trigger()
        self.assertGreater(off.body.s["distress"] - d_off, on.body.s["distress"] - d_on)

    def test_outcomes_present(self):
        env, _ = self.run_env()
        o = env.outcomes()
        self.assertGreater(o["triggers"], 0)
        for k in ("return_latency", "chain_length", "coexistence_share", "rumination_s", "vividness"):
            self.assertIn(k, o)
        m = P.mission_v2(o)
        self.assertEqual(len(m), 3)

    def test_safety_modes_gate_world(self):
        env = P.PersonEnvV2(seed=11, gain=2.0, trig_rate=0.4)
        w = W.World(env, policy="fixed", fixed_mode="LEOPARD", seed=11)
        blocked_any = False
        for _ in range(150):
            before = env.safety.mode                          # the gate applies to the mode in force at tick start
            w.tick()
            if before != "NORMAL":
                self.assertEqual(w.trace[-1][1], "BEAR")      # no deep processing while not NORMAL
                blocked_any = True
        self.assertTrue(blocked_any)
        self.assertGreater(getattr(w, "safety_blocks", 0), 0)
        self.assertTrue(w.log.verify())

    def test_safety_off_unchanged_interface(self):
        env = P.PersonEnvV2(seed=2, safety_on=False)
        w = W.World(env, policy="rule", seed=2)
        for _ in range(30):
            w.tick()
        self.assertEqual(getattr(w, "safety_blocks", 0), 0)


class TestMissionV2(unittest.TestCase):
    def test_lexicographic(self):
        safe_shallow = (0.0, -10.0, 1.0)
        unsafe_deep = (-3.0, 10.0, 9.0)
        self.assertTrue(P.mission_better(safe_shallow, unsafe_deep))
        self.assertFalse(P.mission_better(unsafe_deep, safe_shallow))
        self.assertTrue(P.mission_better((0.0, 5.0, 0.0), (0.0, 1.0, 9.0)))
        self.assertFalse(P.mission_better((0.0, 1.0, 0.0), (0.2, 1.2, 0.0)))   # within tolerance: tie


if __name__ == "__main__":
    unittest.main()
