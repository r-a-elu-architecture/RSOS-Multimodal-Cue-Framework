import pathlib, sys, unittest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from rsxv import world as W


class TestContext(unittest.TestCase):
    def test_four_contexts(self):
        self.assertEqual(W.context(0.2, -0.1), "calm")
        self.assertEqual(W.context(0.2, 0.1), "rising")
        self.assertEqual(W.context(0.8, -0.1), "loaded")
        self.assertEqual(W.context(0.8, 0.1), "crisis")


class TestLedger(unittest.TestCase):
    def test_mean_ci_fit_table(self):
        L = W.FitLedger()
        for r in (1.0, 2.0, 3.0):
            L.add("calm", "TIGER", r)
        L.add("calm", "BEAR", 0.0)
        self.assertEqual(L.mean("calm", "TIGER"), 2.0)
        lo, hi = L.ci("calm", "TIGER")
        self.assertLess(lo, 2.0)
        self.assertGreater(hi, 2.0)
        f = L.fit("calm")
        self.assertEqual((f["TIGER"], f["BEAR"], f["LION"]), (1.0, 0.0, 0.5))
        self.assertEqual(L.table(), {"calm": "TIGER"})


class TestWorld(unittest.TestCase):
    def test_both_envs_all_policies(self):
        for env in (W.AgentEnv, W.PersonEnv):
            for pol in ("watchdog", "rule", "rotation", "fixed", "bandit", {"calm": "BEAR"}):
                s = W.World(env(2), pol, seed=2).run(30)
                self.assertEqual(s["ticks"], 30)
                self.assertTrue(s["audit_ok"])

    def test_deterministic(self):
        a = W.World(W.PersonEnv(3), "watchdog", seed=3).run(40)
        b = W.World(W.PersonEnv(3), "watchdog", seed=3).run(40)
        self.assertEqual(a, b)

    def test_sleep_and_promote_edges(self):
        w = W.World(W.AgentEnv(4), "fixed", seed=4)
        w.run(W.SLEEP_EVERY * 2)
        kinds = [e["kind"] for e in w.lineage.edges]
        self.assertEqual(kinds.count("SLEEP"), 2)
        self.assertIn("PROMOTE", kinds)

    def test_rotation_switches_through_watchdog(self):
        w = W.World(W.PersonEnv(5), "rotation", seed=5)
        w.run(30)
        sw = [e for e in w.lineage.edges if e["kind"] == "SWITCH"]
        self.assertTrue(sw)
        self.assertTrue(all(e["by"] == "WATCHDOG" for e in sw))

    def test_only_owner_creates_merge_split_ban(self):
        w = W.World(W.PersonEnv(6), "fixed", seed=6)
        with self.assertRaises(PermissionError):
            w.lineage.add("BAN", "TIGER", "archive", "META", 1)
        prop = w.meta.propose("BAN", mode="TIGER")
        self.assertFalse(w.ratify("forged", prop))
        self.assertEqual(prop["status"], "pending")
        self.assertTrue(w.ratify(w.keys.credential(), prop))
        self.assertIn("TIGER", w.banned)
        self.assertNotIn("TIGER", w._allowed())
        self.assertEqual(w.lineage.edges[-1]["kind"], "BAN")
        m = w.meta.propose("MERGE", pair=("BEAR", "LION"))
        self.assertTrue(w.ratify(w.keys.credential(), m))
        self.assertEqual(w.lineage.edges[-1]["to"], "BEAR_LION")

    def test_override_cools_and_proposes_ban(self):
        w = W.World(W.PersonEnv(7), "fixed", seed=7, rules={"over_high": 0.0, "hysteresis": 0.0, "debounce": 1})
        w.env.sense = lambda: {"load": 0.9, "harm": 0.5, "trend": 0.1, "c_meta": 1.0, "c_over": 1.0}
        for _ in range(40):
            w.tick()
        kinds = [e["kind"] for e in w.lineage.edges]
        self.assertIn("COOL", kinds)
        self.assertIn("BAN", [p["kind"] for p in w.meta.pending])
        self.assertEqual(w.banned, set())                               # proposals only, nothing applied

    def test_transfer_table_is_a_policy(self):
        w = W.World(W.AgentEnv(8), "watchdog", seed=8)
        w.run(60)
        table = w.ledger.table()
        self.assertTrue(set(table) <= set(W.CONTEXTS))
        s = W.World(W.PersonEnv(8), table, seed=8).run(20)
        self.assertTrue(s["audit_ok"])


if __name__ == "__main__":
    unittest.main()


class TestExperimentHarness(unittest.TestCase):
    def test_small_runs(self):
        from rsxv import world_experiments as X
        self.assertTrue(X.w4()["pass"])
        r = X.w1(n=8)
        self.assertEqual(set(r["arms"]), {"META", "LOCAL", "LOCAL+", "GREEDY-GLOBAL"})
        ci = X.paired_ci([1, 1, 1, 0], [0, 0, 1, 0])
        self.assertAlmostEqual(ci["diff"], 0.5)
        perm = X.permuted({"calm": "TIGER", "crisis": "BEAR"}, (3, 1, 2, 0))
        self.assertEqual(perm, {"calm": "BEAR", "crisis": "TIGER"})
