import random, re, sys, unittest
import pathlib
HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import rsxv
from rsxv import sim, chain, metrics, lang

FULL = open(HERE / "examples/dragon_full.rsxv").read()
CTX = {"now_min": 600, "consent": ["subject", "operator", "auditor"], "ghost_runs": 12, "seed": 3}
HOT = {"id": 9, "resp": 1.2, "sham": 0, "peak_hour": 8, "retain": 0.5, "base": {"arousal": 0.85, "distress": 6.5, "agency": 4, "drift": 0.2}}


def risky(src):
    src = re.sub(r"PHASE settle .*", "PHASE settle MAX 1s", src); src = re.sub(r"PHASE expand .*", "PHASE expand MAX 45s", src)
    return re.sub(r"PHASE rebuild .*", "PHASE rebuild MAX 60s", src).replace("GhostPass ", "")


class Laws(unittest.TestCase):
    def test_parse_full(self):
        p = rsxv.parse(FULL)
        self.assertEqual(p["rescue"], ["SHIELD", "ANCHOR_MAX", "MIRROR_RESET"])
        self.assertEqual(len(p["laws"]), 8)
        self.assertEqual(rsxv.parse(rsxv.to_text(p))["rescue"], p["rescue"])
        with self.assertRaises(rsxv.RSXVError):
            rsxv.parse(FULL.replace("{SHIELD}", "{CAPE}"))

    def test_contingency_rescues_before_nullsafe(self):
        on = rsxv.run(rsxv.parse(risky(FULL)), HOT, CTX)
        off = rsxv.run(rsxv.parse(risky(FULL).replace(" Contingency", "")), HOT, CTX)
        self.assertEqual(off["status"], "stopped"); self.assertEqual(on["status"], "done")
        self.assertEqual(on["rescues"][0]["archetype"], "SHIELD")
        self.assertLess(on["outcome"]["peak_rise"], 2.5)

    def test_temporal_symmetry_reschedules(self):
        p = sim.person(random.Random(4), 4)
        res = chain.run_chain(rsxv.parse(FULL), p, [8, 20, 8, 20, 14, 8, 20], CTX)
        last = res["sessions"][-1]
        self.assertTrue(any("moved from 20:00 to 8:00" in l for l in last["log"])); self.assertEqual(last["hour"], 8)

    def test_continuity_booster(self):
        p = sim.person(random.Random(4), 4)
        res = chain.run_chain(rsxv.parse(FULL), p, [8, 20, 8], CTX)
        self.assertIn("settle booster", res["sessions"][1]["interventions"][0])
        self.assertIn("PHASE settle_boost", lang.to_text(rsxv.parse(res["final_program"])))

    def test_audit_chain_tamper_and_purge(self):
        p = sim.person(random.Random(4), 4)
        res = chain.run_chain(rsxv.parse(FULL), p, [8, 8, 8], CTX)
        st = res["store"]; self.assertTrue(st.verify())
        st.audit[1]["content"]["csi"] = 99.0; self.assertFalse(st.verify())
        st.audit[1]["content"]["csi"] = res["sessions"][1]["csi"]; self.assertTrue(st.verify())
        proof = st.purge("P4", "2026-11-13")
        self.assertEqual(proof["entries_erased"], 3); self.assertTrue(st.verify())
        self.assertNotIn("P4", st.subjects); self.assertTrue(all(e["content"] is None for e in st.audit[:3]))
        self.assertEqual(st.audit[-1]["kind"], "purge-proof")


class Metrics(unittest.TestCase):
    def test_run_metrics_discriminate(self):
        good = rsxv.run(rsxv.parse(FULL), sim.person(random.Random(3), 3), CTX)["metrics"]
        bad = rsxv.run(rsxv.parse(risky(FULL).replace(" Contingency", "")), HOT, CTX)["metrics"]
        self.assertEqual(good["STC"], 1.0); self.assertLess(bad["STC"], 0.7)
        self.assertGreater(good["RSI"], 0)

    def test_smv(self):
        hi = metrics.smv("The mirror remembered itself. The mirror folded the echo within. Like a seed, the loop becomes a door.")
        lo = metrics.smv("Please send the invoice by Friday. I will reply tomorrow with the totals.")
        self.assertGreater(hi["SMV"], 0.8); self.assertEqual(lo["SMV"], 0.0)

    def test_sepl_recovers_retention(self):
        p = sim.person(random.Random(5), 5)
        res = chain.run_chain(rsxv.parse(FULL), p, [p["peak_hour"]] * 5, CTX)
        self.assertAlmostEqual(res["metrics"]["SEP-L"], p["retain"], places=2)
        self.assertGreater(res["metrics"]["ECR"], 0.9)


if __name__ == "__main__":
    unittest.main()
