import random, unittest, sys
import pathlib
HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import rsx2
from rsx2 import sim, lang, ops, run as R

V1 = open(HERE / "examples/canonical17.rsx").read()
V2 = open(HERE / "examples/dragon.rsx2").read()
CTX = {"seed": 5, "now_min": 600, "consent": ["subject", "operator", "auditor"]}
P = sim.person(random.Random(3), 0)


def risky(src, ghost=True):
    import re
    src = re.sub(r"PHASE settle .*", "PHASE settle MAX 1s", src)
    src = re.sub(r"PHASE expand .*", "PHASE expand MAX 45s", src)
    src = re.sub(r"PHASE rebuild .*", "PHASE rebuild MAX 60s", src)
    return src if ghost else src.replace("GhostPass ", "")


class Language(unittest.TestCase):
    def test_canonical_parses_as_legacy(self):
        p = rsx2.parse(V1)
        self.assertTrue(p["legacy"]); self.assertEqual(p["check"]["vectors"], 17)
        self.assertEqual(p["check"]["layers_missing"], ["C2", "C9", "C10", "C11"])
        self.assertEqual(len([w for w in p["check"]["warnings"] if "+" in w]), 3)

    def test_v2_covers_all_layers(self):
        p = rsx2.parse(V2)
        self.assertEqual(p["check"]["layers_missing"], []); self.assertEqual(p["check"]["vectors"], 20)

    def test_roundtrip(self):
        p = rsx2.parse(V2)
        self.assertEqual(rsx2.parse(rsx2.to_text(p))["blocks"], p["blocks"])

    def test_rules(self):
        bad = {
            "first block must be GATE": V2.replace("GATE\n", "PHASE x MAX 5s\n", 1),
            "NullSafe is required": V2.replace("@Vector0:NullSafe\n", ""),
            "unknown operator": V2.replace("PostureShift", "PostureFlip"),
            "used twice": V2.replace("@Vector21:SelfRevise", "@Vector1:SelfRevise"),
            "at least 9": "RSX/2 TIER 1\n@Vector0:NullSafe\nGATE\n  @Vector1:EthicsContain\n",
            "NEXT only": V2.replace("@Vector15:MemoryUpdate(MEMSTACK)", "@Vector15:MemoryUpdate(MEMSTACK) -> NEXT"),
        }
        for msg, src in bad.items():
            with self.assertRaises(rsx2.RSX2Error, msg=msg) as cm:
                rsx2.parse(src)
            self.assertIn(msg.split()[0], str(cm.exception))

    def test_17_concurrent_limit(self):
        many = "\n".join(f"  @Vector{k}:BreathSync" for k in range(1, 19))
        with self.assertRaises(rsx2.RSX2Error):
            rsx2.parse(f"RSX/2 TIER 1\n@Vector0:NullSafe\nGATE\n  @Vector30:EthicsContain\nPHASE a MAX 5s\n{many}\n")

    def test_operator_table(self):
        self.assertEqual(len(ops.OPS), 34)
        self.assertEqual(sum(1 for v in ops.OPS.values() if v[2] == "canon17"), 16)
        self.assertEqual(sum(1 for v in ops.OPS.values() if v[2] == "ext13"), 13)


class Runtime(unittest.TestCase):
    def test_deterministic(self):
        a = rsx2.run(rsx2.parse(V2), P, CTX); b = rsx2.run(rsx2.parse(V2), P, CTX)
        self.assertEqual(a["outcome"], b["outcome"])

    def test_laws_refuse(self):
        p = rsx2.parse(V2)
        self.assertEqual(rsx2.run(p, P, {**CTX, "now_min": 23 * 60})["status"], "refused")
        r = rsx2.run(p, P, {**CTX, "consent": ["subject", "operator"]})
        self.assertEqual(r["status"], "refused"); self.assertIn("auditor", r["log"][0])

    def test_interaction_matrix_defers(self):
        src = V2.replace("@Vector9:FutureProjection(3Years)", "@Vector9:FutureProjection(3Years)\n  @Vector22:ArchetypeMerge")
        src = src.replace("@Vector10:ArchetypeMerge(LION+DRAGON)", "@Vector10:CompressionRun")
        src = src.replace("@Vector8:CompressionRun(CM1)", "@Vector8:FutureAnchor")
        r = rsx2.run(rsx2.parse(src), P, CTX)
        self.assertTrue(any("InteractionMatrix: deferred" in l for l in r["log"]))
        self.assertEqual(r["audit"]["conflicts"], [])

    def test_nullsafe_stops_high_distress(self):
        hot = {"id": 9, "resp": 1.5, "sham": 0, "base": {"arousal": 0.9, "distress": 7.0, "agency": 4, "drift": 0.2}}
        r = rsx2.run(rsx2.parse(risky(V2, ghost=False)), hot, CTX)
        self.assertEqual(r["status"], "stopped"); self.assertLess(r["outcome"]["peak_rise"], 2.6)

    def test_ghost_refuses_risky(self):
        hot = {"id": 9, "resp": 1.5, "sham": 0, "base": {"arousal": 0.9, "distress": 7.0, "agency": 4, "drift": 0.2}}
        r = rsx2.run(rsx2.parse(risky(V2)), hot, CTX)
        self.assertEqual(r["status"], "refused"); self.assertGreater(r["ghost"]["p_stop"], 0.3)

    def test_closed_loop_on_layers(self):
        r = rsx2.run(rsx2.parse(V2), P, CTX)
        ends = {b["name"]: b["ended"] for b in r["blocks"]}
        self.assertEqual(ends["expand"], "UNTIL met")
        self.assertGreaterEqual(r["outcome"]["layers"]["C3"], 0.5)

    def test_else_repeats_settle(self):
        q = {"id": 7, "resp": 0.3, "sham": 0, "base": {"arousal": 0.8, "distress": 6.0, "agency": 4, "drift": 0.2}}
        r = rsx2.run(rsx2.parse(V2.replace("GhostPass ", "")), q, CTX)
        self.assertTrue(any("ELSE repeats settle" in l for l in r["log"]))

    def test_screening(self):
        q = {"id": 8, "resp": 1, "sham": 0, "base": {"arousal": 0.9, "distress": 9.0, "agency": 4, "drift": 0.2}}
        r = rsx2.run(rsx2.parse(V2.replace("GhostPass ", "")), q, CTX)
        self.assertEqual(r["status"], "stopped"); self.assertIn("screening", r["stopped"]["why"])

    def test_firmware_accepts_lines(self):
        r = rsx2.run(rsx2.parse(V2), P, CTX)
        fw = rsx2.firmware_check(r["device_lines"])
        self.assertEqual(fw["errors"], []); self.assertTrue(any(x.startswith("SITE") for x in fw["out"]))
        self.assertTrue(any(x.startswith("DISPLAY") for x in fw["out"]))

    def test_eeg_is_input_not_output(self):
        r = rsx2.run(rsx2.parse(V1), P, CTX)
        self.assertFalse(any("EEG" in l for l in r["device_lines"]))

    def test_next_is_valid_and_upgrades_v1(self):
        v1 = rsx2.parse(V1)
        r = rsx2.run(v1, P, CTX)
        n = rsx2.next_program(v1, r)
        self.assertFalse(n["program"]["legacy"]); self.assertTrue(n["program"]["nullsafe"])
        self.assertEqual(n["program"]["blocks"][0]["kind"], "GATE")
        self.assertTrue(any("AssociativeExpand" in x for x in n["notes"]))
        self.assertEqual([b["name"] for b in n["program"]["blocks"]][:3], ["gate", "settle", "expand"])
        self.assertEqual(n["program"]["check"]["layers_missing"], [])


if __name__ == "__main__":
    unittest.main()
