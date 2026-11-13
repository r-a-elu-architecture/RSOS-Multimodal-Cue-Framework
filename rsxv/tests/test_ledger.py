import json, pathlib, random, sys, unittest
HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from rsxv import translate as T, sim, ledger as L, chain
from rsxv import ledger_recovery as R

M = {m["id"]: m for m in json.load(open(HERE / "tests" / "fixtures" / "messages.json"))["messages"]}
CTX = {"consent": ["subject", "operator", "randomisation"]}
T1 = T.to_program(M["dense"]["text"], msg_id="m1")
TEXTS = {f"m1·v{v['n']}": v["text"] for v in T1["vectors"]["vectors"]}


def person(d=5.0):
    p = sim.person(random.Random(3), 3); p["base"]["distress"] = d; return p


class Ledger(unittest.TestCase):
    def test_needs_consent_to_randomise(self):
        r = L.build(T1["program"], T1["lineage"], person(), sessions=2, ctx={"consent": ["subject", "operator"]})
        self.assertEqual(r["status"], "refused")

    def test_safety_operators_never_randomised(self):
        units = L.clause_units(T1["program"], T1["lineage"])
        self.assertTrue(units)
        for op in ("EthicsContain", "SymbolicDriftCheck", "BreathOverride", "MemoryUpdate", "SymbolicCommandExport"):
            self.assertNotIn(op, units)

    def test_recovers_planted_effects(self):
        planted = {"m1·v3": {"distress": -0.012}, "m1·v7": {"distress": 0.012}}
        led = L.build(T1["program"], T1["lineage"], person(), sessions=30, ctx=CTX, planted=planted, inert=True, seed=5)
        e = {x["clause"]: x["distress"] for x in led["entries"]}
        self.assertLess(e["m1·v3"]["hi"], 0); self.assertGreater(e["m1·v7"]["lo"], 0)
        self.assertTrue(e["m1·v3"]["lo"] <= -0.12 <= e["m1·v3"]["hi"])
        self.assertTrue(e["m1·v7"]["lo"] <= 0.12 <= e["m1·v7"]["hi"])

    def test_recovery_study_is_calibrated(self):
        res = R.study(reps=12, sessions=30, seed=3)
        self.assertGreater(res["coverage_95"], 0.85); self.assertGreater(res["power_nonzero"], 0.9)
        self.assertLess(abs(res["mean_bias"]), 0.02)

    def test_sentences_and_next(self):
        planted = {"m1·v8": {"distress": 0.015}}
        led = L.build(T1["program"], T1["lineage"], person(), sessions=30, ctx=CTX, planted=planted, inert=True, seed=9, texts=TEXTS)
        s = L.sentences(led, "distress")
        self.assertIn("raised distress", s[0]); self.assertIn("symbol and a name", s[0])
        n = L.next_from_ledger(T1["program"], T1["lineage"], led)
        self.assertIn("CompressionRun", n["dropped"])
        self.assertNotIn("CompressionRun", [v["op"] for b in n["program"]["blocks"] for v in b["vectors"]])

    def test_ledger_in_audit_chain(self):
        led = L.build(T1["program"], T1["lineage"], person(), sessions=3, ctx=CTX, inert=True)
        st = chain.Store(); L.to_audit(st, "P3", led)
        self.assertTrue(st.verify()); self.assertEqual(st.audit[-1]["kind"], "ledger")


if __name__ == "__main__":
    unittest.main()
