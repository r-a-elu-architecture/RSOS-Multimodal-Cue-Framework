import json, pathlib, random, sys, unittest
HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import rsxv
from rsxv import translate as T, sim

M = {m["id"]: m for m in json.load(open(HERE / "tests" / "fixtures" / "messages.json"))["messages"]}
CTX = {"now_min": 600, "hour": 14, "consent": ["subject", "operator", "auditor"], "ghost_runs": 8, "seed": 3}


class Translator(unittest.TestCase):
    def test_counts_close_to_hand(self):
        for m in M.values():
            self.assertLessEqual(abs(T.vectors(m["text"])["count"] - m["hand"]), 1, m["id"])

    def test_dense_and_short(self):
        self.assertGreaterEqual(T.vectors(M["dense"]["text"])["count"], 9)
        self.assertEqual(T.vectors(M["short"]["text"])["count"], 1)

    def test_pasted_material_is_context(self):
        V = T.vectors(M["pasted"]["text"])
        self.assertEqual(V["count"], 1); self.assertEqual(len(V["quoted_claims"]), 5)

    def test_program_valid_complete_and_traced(self):
        for m in M.values():
            t = T.to_program(m["text"], msg_id="m1")
            ck = t["program"]["check"]
            self.assertEqual(ck["layers_missing"], [], m["id"]); self.assertGreaterEqual(ck["vectors"], 9)
            self.assertEqual(t["unmapped"], [])
            self.assertIn("# from m1.v", t["source"])

    def test_archetypes_from_text(self):
        t = T.to_program(M["archetypes"]["text"])
        self.assertEqual(t["program"]["archetype"], "DRAGON")
        self.assertIn("ArchetypeMerge(DRAGON+LION)", t["source"])

    def test_runs_end_to_end(self):
        t = T.to_program(M["dense"]["text"])
        r = rsxv.run(t["program"], sim.person(random.Random(3), 3), CTX)
        self.assertIn(r["status"], ("done", "stopped"))
        self.assertEqual(rsxv.firmware_check(r["device_lines"])["errors"], [])


if __name__ == "__main__":
    unittest.main()
