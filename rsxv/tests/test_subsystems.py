import pathlib, random, sys, unittest
HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import rsxv
from rsxv import sim, chain, bridge as B, subsystems as SS

FULL = open(HERE / "examples" / "dragon_full.rsxv").read()
CTX = {"seed": 3, "now_min": 600, "consent": ["subject", "operator", "auditor"], "ghost_runs": 8}


class RealSubsystems(unittest.TestCase):
    def test_full_dose_inside_contain_envelope(self):
        p = rsxv.parse(FULL)
        c = B.to_cue(p)
        self.assertLessEqual(c["manifest"]["haptic_budget"]["final_ms"], 18000)
        self.assertEqual(SS.contain_gate(p, SS.new_world(), 0)["decision"], "allow")

    def test_contain_blocks_outside_envelope(self):
        p = rsxv.parse(FULL)
        tl = SS.full_dose_timeline(p)
        tl["safety"]["haptic_max"] = 0.9            # as if a program asked for more than the envelope allows
        d = SS.C.decide({"kind": "run", "protocol": SS.protocol_id(p)}, SS.new_world()["contain"], tl, 0)
        self.assertEqual(d["decision"], "block")

    def test_sessions_feed_memstack_contain_and_cm1(self):
        w = SS.new_world()
        res = chain.run_chain(rsxv.parse(FULL), sim.person(random.Random(4), 4), [8] * 5, CTX, world=w)
        self.assertEqual(len(w["runs"]), 5)
        self.assertEqual(w["runs"][0]["protocol"], "rsxv_8_dragon")
        self.assertTrue(all(R.get("contain", {}).get("decision") == "allow" for R in res["sessions"]))
        runs, _ = SS.MS.restore(w["memstack"])           # checksummed snapshot
        self.assertEqual(len(runs), 5)
        self.assertGreater(SS.recall(w, "DRAGON")["bundle_strength"], 0.5)
        self.assertTrue(w["cm1"]["recommendations"])

    def test_contain_quarantines_a_program_that_stops_helping(self):
        p = rsxv.parse(FULL)
        w = SS.new_world()
        pid = SS.protocol_id(p)
        w["runs"] = [{"timestamp": 1_800_000_000 + k * 86400, "participant": "P1", "protocol": pid, "sud_before": 4, "sud_after": 6,
                      "agency_before": 5, "agency_after": 4, "completed": 1, "tier": "DRAGON"} for k in range(5)]
        w["contain"], ch = SS.C.review(w["contain"], w["runs"], now=1_800_500_000)
        self.assertTrue(any(c["kind"] == "quarantine" for c in ch))
        R = rsxv.run(p, sim.person(random.Random(4), 4), {**CTX, "world": w, "now": 1_800_500_000})
        self.assertEqual(R["status"], "stopped"); self.assertIn("CONTAIN", R["stopped"]["why"])


if __name__ == "__main__":
    unittest.main()
