import pathlib, sys, unittest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from rsxv import layers as L, person2 as P, world as W


class TestNodeCard(unittest.TestCase):
    def test_provenance_and_recommendation(self):
        c = L.NodeCard("anchor_a", "emergency_override", {"interrupt"}, role="emergency", crisis_history=True)
        for i in range(6):
            c.record(i, "activated", outcome=True)
        for i in range(4):
            c.record(10 + i, "activated", outcome=False, failure_ctx=True, provenance="temporal")
        self.assertEqual(c.contamination(), 0.0)              # temporal co-occurrence is not contamination
        self.assertEqual(c.recommend(), "keep_reweight")
        self.assertTrue(c.needs_clinician_view())
        d = L.NodeCard("x", "f")
        for i in range(8):
            d.record(i, "calm", outcome=False, failure_ctx=True, provenance="direct")
        self.assertEqual(d.recommend(), "retire_new")
        self.assertFalse(d.decide("retire_new", by="WATCHDOG", t=1)["ok"])
        self.assertTrue(d.decide("retire_new", by="person", t=1)["ok"])
        self.assertEqual(d.role, "retired")
        self.assertEqual(L.transfer_key(c), "emergency_override")


class TestFailureRepurposing(unittest.TestCase):
    def test_never_silent(self):
        w = W.World(P.PersonEnvV2(seed=1), policy="rule", seed=1)
        reg = L.FailureRegistry(w.lineage)
        f = reg.register("contaminated_anchor", "anchor_a", t=3)
        with self.assertRaises(ValueError):
            reg.resolve(f, "new_mechanism", None, "x", t=4)     # must name the mechanism
        with self.assertRaises(ValueError):
            reg.resolve(f, "no_change", None, "", t=4)          # must give a reason
        self.assertEqual(len(reg.open(now=100, max_age=10)), 1)
        reg.resolve(f, "new_mechanism", "anchor_b", "simple motor anchor without crisis history", t=5)
        self.assertEqual(reg.open(now=100), [])
        self.assertEqual(reg.genealogy(), [("contaminated_anchor", "anchor_a", "anchor_b")])
        kinds = [e["kind"] for e in w.lineage.edges]
        self.assertIn("FAILURE", kinds)
        self.assertIn("META", kinds)


class TestMaintenanceWindow(unittest.TestCase):
    def test_applies_only_at_sleep_and_through_spine(self):
        w = W.World(P.PersonEnvV2(seed=2), policy="rule", seed=2)
        w.maint = L.MaintenanceWindow()
        box = {"n": 0}
        w.maint.propose("tune", lambda world: box.__setitem__("n", box["n"] + 1))
        w.maint.propose("bad", lambda world: box.__setitem__("n", 99), intensity_mechanism="pain")
        for _ in range(W.SLEEP_EVERY - 1):
            w.tick()
        self.assertEqual(box["n"], 0)                         # nothing changes before the window
        w.tick()                                              # sleep happens at this tick
        self.assertEqual(box["n"], 1)
        self.assertEqual(len(w.maint.rejected), 1)
        self.assertIn("REPURPOSE", [e["kind"] for e in w.lineage.edges])
        self.assertTrue(w.log.verify())

    def test_gate_can_refuse(self):
        w = W.World(P.PersonEnvV2(seed=2), policy="rule", seed=2)
        w.maint = L.MaintenanceWindow(gate=lambda world, ch: False)
        w.maint.propose("x", lambda world: None)
        r = w.maint.apply(w)
        self.assertEqual(r, {"applied": 0, "rejected": 1})

    def test_lineage_permissions(self):
        w = W.World(P.PersonEnvV2(seed=2), policy="rule", seed=2)
        with self.assertRaises(PermissionError):
            w.lineage.add("REPURPOSE", "a", "b", "TIGER", 1)


class TestLineageMemory(unittest.TestCase):
    def test_corrected_claim_cannot_reenter(self):
        # structure of a documented case: claim, correction, then the old capsule pasted again
        m = L.LineageMemory()
        m.assert_claim("estimate", "value_A", "capsule@t5")
        m.correct("estimate", "value_B", "review@t6")
        flags = m.ingest({"estimate": "value_A"}, "capsule@t151")
        self.assertEqual(flags[0]["flag"], "corrected_claim_reentry")
        self.assertEqual(m.claims["estimate"]["value"], "value_B")
        cap = m.summary()
        self.assertEqual(cap["estimate"]["corrections"][0]["source"], "review@t6")

    def test_unsourced_and_drift(self):
        m = L.LineageMemory()
        self.assertEqual(m.assert_claim("x", 1, None)["flag"], "unsourced")
        a = {"events": ["e1", "e2", "e3"]}
        b = {"events": ["e2", "e1", "e3"], "new_section": "added"}
        d = L.diff_summaries(a, b, order_key="events")
        self.assertIn("new_section", d["unsourced_added"])
        self.assertEqual(set(d["moved"]), {"e1", "e2"})


if __name__ == "__main__":
    unittest.main()
