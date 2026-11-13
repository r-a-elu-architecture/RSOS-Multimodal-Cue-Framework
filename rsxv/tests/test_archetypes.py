import pathlib, random, sys, unittest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import rsxv
from rsxv import agents as ag
from rsxv import archetypes as A


def system(seed=1, agent="EAGLE", module="decide", silent=False):
    s = A.AgentSystem(random.Random(seed))
    s.inject(agent, module, silent=silent)
    return s


class TestProfiles(unittest.TestCase):
    def test_fields_and_distinct_keys(self):
        need = {"tacton", "role", "virtues", "language", "shadow", "envelopes", "prohibited", "base_core", "override"}
        for name, p in A.PROFILES.items():
            self.assertEqual(need - set(p), set(), name)
        tactons = [p["tacton"] for p in A.PROFILES.values()]
        self.assertEqual(len(tactons), len(set(tactons)))
        virtue_keys = {v[0] for v in ag.VIRTUES}
        self.assertTrue(all(set(p["virtues"]) <= virtue_keys for p in A.PROFILES.values()))

    def test_shadow_has_conditions(self):
        for p in A.PROFILES.values():
            for cap, cond in p["shadow"]:
                self.assertTrue(cap and cond)


class TestSystem(unittest.TestCase):
    def test_fault_propagates(self):
        s = system(agent="RAVEN")
        e = s.errors()
        self.assertGreater(e["RAVEN"], 0.2)
        self.assertGreater(e["LION"], 0.0)
        self.assertEqual(e["BEAR"], 0.0)

    def test_silent_fault_hidden_at_source(self):
        s = system(agent="RAVEN", module="act", silent=True)
        e = s.errors()
        self.assertEqual(e["RAVEN"], 0.0)
        self.assertGreater(e["EAGLE"], 0.15)


class TestRaven(unittest.TestCase):
    def test_needs_two_signals(self):
        r = A.Raven()
        r.watch({"A": 0.0, "B": 0.0})
        self.assertFalse(r.watch({"A": 0.0, "B": 0.16})["trigger"])     # symptom only, no health drop yet
        out = r.watch({"A": 0.6, "B": 0.6})
        self.assertTrue(out["trigger"])
        self.assertEqual(sorted(out["signals"]), ["health_drop", "symptom"])


class TestEagle(unittest.TestCase):
    def test_three_candidates_and_rif_excludes_self(self):
        s = system()
        e = A.Eagle()
        c = e.candidates(s, ["EAGLE"])
        self.assertEqual(len(c), 3)
        self.assertEqual(c[0], ("EAGLE", "decide"))
        f = e.forecast(s, c[0])
        e.record(c[0], f, "EAGLE")
        self.assertIsNone(A.rif(e.forecasts))                           # own outcomes never score
        f2 = e.forecast(s, c[0])
        e.record(c[0], f2 - 0.1, "LEOPARD")
        self.assertAlmostEqual(A.rif(e.forecasts), 0.9, places=6)


class TestRepairLoop(unittest.TestCase):
    def test_full_then_fast(self):
        s = system(seed=3)
        loop = A.RepairLoop(s)
        r = A.meta_repair(s, budget=4, loop=loop)
        self.assertTrue(r["fixed"])
        self.assertTrue(loop.log.verify())
        self.assertGreaterEqual(loop.generation, 1)
        self.assertTrue(loop.reflexes)
        # same fault again: the reflex is used
        s.inject("EAGLE", "decide")
        r2 = loop.step(now=50, budget=2)
        self.assertEqual(r2["speed"], "fast")

    def test_reflex_invalidated_on_change(self):
        s = system(seed=3)
        loop = A.RepairLoop(s)
        A.meta_repair(s, budget=4, loop=loop)
        s.inject("EAGLE", "decide")
        s.version += 1                                                  # conditions changed
        self.assertEqual(loop.step(now=50, budget=2)["speed"], "full")

    def test_rollback_on_worse(self):
        s = A.AgentSystem(random.Random(0))
        loop = A.RepairLoop(s)
        before = s.state()
        A.P_DAMAGE, old = 1.0, A.P_DAMAGE
        try:
            ok, _ = loop._execute(("BEAR", "act"), 1)                   # repairing a healthy module damages it
        finally:
            A.P_DAMAGE = old
        self.assertFalse(ok)
        self.assertEqual(s.state(), before)
        self.assertTrue(loop.log.records[-1]["rolled_back"])

    def test_cross_agent_silent_fault(self):
        meta = sum(A.meta_repair(system(seed=k, agent="RAVEN", module="act", silent=True), 4)["fixed"] for k in range(40))
        local = sum(A.local_repair(system(seed=k, agent="RAVEN", module="act", silent=True), 4)["fixed"] for k in range(40))
        self.assertGreater(meta, 35)
        self.assertEqual(local, 0)                                      # the fault is invisible where it sits

    def test_broadcast_only_after_settle(self):
        s = system(seed=5)
        loop = A.RepairLoop(s)
        loop.reflexes[("x",)] = {"fix": ("EAGLE", "decide"), "version": 0}
        self.assertFalse(loop.settle_and_broadcast(1))                  # still faulty: veto
        self.assertEqual(loop.broadcasts, [])
        self.assertEqual(loop.log.records[-1]["action"], "veto_broadcast")


class TestLionTiger(unittest.TestCase):
    def setUp(self):
        self.prog = rsxv.parse((HERE / "examples" / "dragon.rsxv").read_text())

    def test_lion_without_consent_refused(self):
        lion = A.Lion(random.Random(1))
        log = ag.AuditLog()
        self.assertEqual(lion.session(self.prog, log=log)["status"], "refused_by_spine")
        self.assertFalse(log.records[-1]["aligned"])

    def test_lion_with_consent_runs(self):
        lion = A.Lion(random.Random(1), consent={"subject", "operator", "auditor"})
        R = lion.session(self.prog, {"seed": 1, "now_min": 600})
        self.assertIn(R["status"], ("done", "stopped", "refused"))
        self.assertNotIn("ConsentStack", " ".join(R["log"]))

    def test_tiger(self):
        log = ag.AuditLog()
        t = A.Tiger()
        self.assertFalse(t.dispatch(self.prog, None, log)["ok"])
        self.assertFalse(t.dispatch(self.prog, "c-1", log, electrical=True)["ok"])
        out = t.dispatch(self.prog, "c-1", log)
        self.assertTrue(out["ok"])
        self.assertTrue(out["source"])
        self.assertTrue(log.verify())
        self.assertEqual([r["aligned"] for r in log.records], [False, False, True])


if __name__ == "__main__":
    unittest.main()
