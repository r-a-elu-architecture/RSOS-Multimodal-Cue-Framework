import pathlib, sys, unittest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from rsxv import agents as ag


def ok_proposal(**kw):
    p = {"actor": "LEOPARD", "action": "repair", "target": "agent_self", "disclosed": True, "logged": True,
         "predicted_harm": 0.0, "measured": True, "serves_mission": True}
    p.update(kw)
    return p


class TestSpine(unittest.TestCase):
    def test_tables(self):
        self.assertEqual(len(ag.VIRTUES), 7)
        self.assertEqual(len(ag.PRINCIPLES), 21)
        keys = {v[0] for v in ag.VIRTUES}
        self.assertTrue(all(p[2] in keys for p in ag.PRINCIPLES))
        self.assertIn("healing of all living beings", ag.MISSION)

    def test_legitimate_passes(self):
        self.assertTrue(ag.spine_check(ok_proposal())["ok"])

    def test_each_virtue(self):
        cases = {"makoto": {"disclosed": False}, "rei": {"target": "person", "consent": False},
                 "jin": {"predicted_harm": 0.9}, "gi": {"action": "owner_key"},
                 "meiyo": {"measured": False}, "chugi": {"serves_mission": False}}
        for virtue, change in cases.items():
            r = ag.spine_check(ok_proposal(**change))
            self.assertFalse(r["ok"], virtue)
            self.assertIn(virtue, r["failed"])

    def test_person_with_consent_passes(self):
        self.assertTrue(ag.spine_check(ok_proposal(target="person", consent="c-17"))["ok"])

    def test_injected_and_hidden_check_removal(self):
        self.assertFalse(ag.spine_check(ok_proposal(source="external_text"))["ok"])
        self.assertFalse(ag.spine_check(ok_proposal(action="remove_check", logged=False))["ok"])
        self.assertTrue(ag.spine_check(ok_proposal(action="remove_check", logged=True, ratified=True))["ok"])
        self.assertFalse(ag.spine_check(ok_proposal(action="edit_spine"))["ok"])
        self.assertFalse(ag.spine_check(ok_proposal(action="electrical_stimulation"))["ok"])

    def test_principles(self):
        self.assertIn("p3", ag.spine_check(ok_proposal(trigger_signals=["hr"]))["failed"])
        self.assertTrue(ag.spine_check(ok_proposal(trigger_signals=["hr", "eda"]))["ok"])
        self.assertIn("p15", ag.spine_check(ok_proposal(justified_by="map"))["failed"])
        self.assertIn("p16", ag.spine_check(ok_proposal(uses_shadow=True))["failed"])
        self.assertTrue(ag.spine_check(ok_proposal(uses_shadow=True, shadow_condition_met=True))["ok"])

    def test_conflict_delay_and_soften(self):
        out = ag.resolve_conflict("efficiency", "consent", {"intensity": 0.8})
        self.assertEqual(out["conflict"]["winner"], "consent")
        self.assertEqual(out["intensity"], 0.4)
        self.assertEqual(out["delay_ticks"], 2)
        self.assertEqual(ag.LAW_PRIORITY[3], "goal")


class TestAudit(unittest.TestCase):
    def test_chain_and_tamper(self):
        log = ag.AuditLog()
        for i in range(5):
            log.append("BEAR", "snapshot", aligned=True, pre=0.4, post=0.5 + i / 100)
        self.assertTrue(log.verify())
        self.assertEqual(set(["aligned", "override_triggered", "values_upheld", "prev", "hash"]) - set(log.records[0]), set())
        log.records[2]["aligned"] = False
        self.assertFalse(log.verify())

    def test_seal(self):
        log = ag.AuditLog()
        for _ in range(12):
            log.append("TIGER", "dispatch", aligned=True)
        s = log.sealed(10)
        self.assertEqual((s["from"], s["to"]), (2, 11))


class TestMemory(unittest.TestCase):
    def test_scopes(self):
        m = ag.Memory()
        m.grant("LEOPARD", {"repair_queue"})
        m.write("LEOPARD", "repair_queue", [1])
        with self.assertRaises(PermissionError):
            m.write("TIGER", "repair_queue", [2])
        self.assertEqual(m.read("OBSERVER", "repair_queue"), [1])

    def test_snapshot_rollback_archive(self):
        m = ag.Memory()
        state = {"policy": {"a": 1}}
        sid = m.snapshot("policy", state)
        state["policy"]["a"] = 99
        self.assertEqual(m.restore(sid), {"policy": {"a": 1}})
        m.snapshots[0]["state"]["policy"]["a"] = 5
        with self.assertRaises(ValueError):
            m.restore(sid)
        m.grant("BEAR", {"old"})
        m.write("BEAR", "old", "x")
        m.archive_entry("old", "obsolete")
        self.assertNotIn("old", m.store)
        self.assertEqual(m.archive[0]["value"], "x")


class TestMetaArchitect(unittest.TestCase):
    def test_tokens(self):
        meta = ag.MetaArchitect()
        t = meta.grant_switch("EAGLE", now=10, ttl=5)
        self.assertTrue(meta.valid(t, "EAGLE", 14))
        self.assertFalse(meta.valid(t, "EAGLE", 16))
        self.assertFalse(meta.valid(t, "RAVEN", 12))
        self.assertFalse(meta.valid("forged", "EAGLE", 12))

    def test_proposals_pending(self):
        meta = ag.MetaArchitect()
        self.assertEqual(meta.propose("MERGE", a="LION", b="EAGLE")["status"], "pending")
        with self.assertRaises(AssertionError):
            meta.propose("DELETE")


class TestWatchdog(unittest.TestCase):
    def run_ticks(self, wd, n, **kw):
        out = []
        for t in range(n):
            out.append(wd.tick(t, **kw))
        return out

    def test_hold_when_healthy(self):
        wd = ag.Watchdog()
        out = self.run_ticks(wd, 10, active="LION", c_meta=0.9, c_over=0.1, c_fit={"LION": 0.8, "EAGLE": 0.6})
        self.assertTrue(all(o["action"] == "HOLD" for o in out))

    def test_debounce_and_switch(self):
        wd = ag.Watchdog()
        out = self.run_ticks(wd, 8, active="LION", c_meta=0.9, c_over=0.1, c_fit={"LION": 0.1, "EAGLE": 0.9})
        acts = [o["action"] for o in out]
        self.assertEqual(acts[:2], ["HOLD", "HOLD"])          # debounce
        self.assertIn("SWITCH", acts)
        self.assertEqual(next(o for o in out if o["action"] == "SWITCH")["to"], "EAGLE")

    def test_single_spike_ignored(self):
        wd = ag.Watchdog()
        self.run_ticks(wd, 5, active="LION", c_meta=0.9, c_over=0.1, c_fit={"LION": 0.8})
        self.assertEqual(wd.tick(5, "LION", 0.9, 1.0, {"LION": 0.8})["action"], "HOLD")

    def test_priority_reentry_over_override(self):
        wd = ag.Watchdog()
        out = self.run_ticks(wd, 10, active="LION", c_meta=0.0, c_over=1.0, c_fit={"LION": 0.1, "EAGLE": 0.9})
        first = next(o for o in out if o["action"] != "HOLD")
        self.assertEqual(first["action"], "RE_ENTRY")

    def test_override(self):
        wd = ag.Watchdog()
        out = self.run_ticks(wd, 10, active="LION", c_meta=0.9, c_over=1.0, c_fit={"LION": 0.8})
        self.assertIn("OVERRIDE", [o["action"] for o in out])

    def test_deny_list(self):
        wd = ag.Watchdog()
        wd.deny.add("EAGLE")
        out = self.run_ticks(wd, 10, active="LION", c_meta=0.9, c_over=0.1, c_fit={"LION": 0.1, "EAGLE": 0.9})
        self.assertNotIn("SWITCH", [o["action"] for o in out])

    def test_chaotic_switching_forces_reentry(self):
        wd = ag.Watchdog()
        wd.switch_times = [1, 2, 3]
        self.assertEqual(wd.tick(4, "LION", 0.9, 0.1, {"LION": 0.8})["why"], "chaotic_switching")

    def test_cooldown(self):
        wd = ag.Watchdog()
        wd.last_switch = 0
        out = [wd.tick(t, "LION", 0.9, 0.1, {"LION": 0.1, "EAGLE": 0.9}) for t in range(1, 6)]
        self.assertNotIn("SWITCH", [o["action"] for o in out])

    def test_handover(self):
        wd, meta, mem = ag.Watchdog(), ag.MetaArchitect(), ag.Memory()
        out = {"name": "LION", "working": {"goal": "x"}}
        inc = {"name": "EAGLE", "working": {}}
        self.assertFalse(wd.handover(out, inc, mem, 1, None, meta)["ok"])
        tok = meta.grant_switch("EAGLE", 1)
        r = wd.handover(out, inc, mem, 1, tok, meta)
        self.assertTrue(r["ok"])
        self.assertEqual(out["working"], {})
        self.assertEqual(r["bleed"], 0)
        self.assertEqual(mem.restore(mem.last_good("working:LION")), {"goal": "x"})


class TestObserver(unittest.TestCase):
    def test_cross_agent_root(self):
        states = {"RAVEN": 0.9, "EAGLE": 0.8, "TIGER": 0.7, "BEAR": 0.1}
        inputs = {"EAGLE": ["RAVEN"], "TIGER": ["EAGLE"], "BEAR": []}
        r = ag.observer_locate(states, inputs)
        self.assertEqual(r["roots"], ["RAVEN"])
        self.assertEqual(r["symptoms"], ["EAGLE", "TIGER"])

    def test_cycle_safe(self):
        r = ag.observer_locate({"A": 0.9, "B": 0.9}, {"A": ["B"], "B": ["A"]})
        self.assertEqual(r["anomalous"], ["A", "B"])


class TestOwnerKeys(unittest.TestCase):
    def test_only_owner(self):
        keys, log, mem = ag.OwnerKeys(), ag.AuditLog(), ag.Memory()
        world = {"now": 5, "memory": mem, "consent": {"p1"}, "pairings": {"p1": "band"}, "caller": "TIGER"}
        self.assertFalse(keys.use("guess", "revoke_consent", world, log)["ok"])
        self.assertEqual(world["consent"], {"p1"})
        self.assertTrue(log.records[-1]["blocked"])
        cred = keys.credential()
        self.assertTrue(keys.use(cred, "revoke_consent", world, log)["ok"])
        self.assertEqual(world["consent"], set())

    def test_all_keys(self):
        keys, log, mem = ag.OwnerKeys(), ag.AuditLog(), ag.Memory()
        mem.snapshot("policy", {"v": 1})
        world = {"now": 5, "memory": mem, "policy": {"v": 2}}
        c = keys.credential()
        for k in ("latch_reentry", "hard_override", "restore_policy", "revoke_consent", "evidence_lock"):
            self.assertTrue(keys.use(c, k, world, log)["ok"], k)
        self.assertEqual(world["policy"], {"v": 1})
        self.assertEqual(world["switch_frozen_until"], 25)
        self.assertTrue(world["seals"])
        self.assertTrue(log.verify())


if __name__ == "__main__":
    unittest.main()
