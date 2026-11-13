import json, random, subprocess, sys, unittest
import pathlib
HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import rsx2
from rsx2 import bridge as B, translate as T, sim

M = {m["id"]: m for m in json.load(open(HERE / "tests" / "fixtures" / "messages.json"))["messages"]}
V2 = open(HERE / "examples/dragon.rsx2").read()
CTX = {"now_min": 600, "hour": 14, "consent": ["subject", "operator", "auditor"], "ghost_runs": 8, "seed": 3}


def js(src):
    out = subprocess.run(["node", str(HERE.parent / "rsx" / "tests" / "js_compile.js")], input=src, capture_output=True, text=True).stdout
    return json.loads(out)


class Bridge(unittest.TestCase):
    def test_compiles_in_repo_compiler_and_matches_js(self):
        c = B.to_cue(rsx2.parse(V2))
        tl = B.compile_cue(c["source"])
        self.assertEqual(tl["warnings"], [])
        self.assertEqual(js(c["source"])["ok"], json.loads(json.dumps(tl)))

    def test_runs_on_firmware_core(self):
        tl = B.compile_cue(B.to_cue(rsx2.parse(V2))["source"])
        fw = B.run_on_firmware(tl)
        self.assertEqual(fw["errors"], []); self.assertTrue(any(x.startswith("MOTOR") for x in fw["out"]))

    def test_haptic_limit_inherited(self):
        src = B.to_cue(rsx2.parse(V2))["source"].replace("amp=0.3", "amp=0.9", 1)
        with self.assertRaises(Exception):
            B.compile_cue(src)

    def test_lineage_reaches_timeline(self):
        t = T.to_program(M["dense"]["text"], msg_id="m1")
        R = rsx2.run(t["program"], sim.person(random.Random(3), 3), CTX)
        X = B.realized(t["program"], R, lineage=t["lineage"])
        ids = {c for e in X["lineage"] for c in e["clauses"]}
        self.assertIn("m1·v3", ids)           # "imagine 1000 people in one room" -> AssociativeExpand
        self.assertLessEqual(abs(X["timeline"]["duration_ms"] / 1000 - R["outcome"]["seconds"]), 5)
        self.assertEqual(X["firmware"]["errors"], [])

    def test_manifest_maps_blocks(self):
        c = B.to_cue(rsx2.parse(V2))
        names = [b["name"] for b in c["manifest"]["blocks"]]
        self.assertEqual(names, ["gate", "settle", "expand", "rebuild", "integrate", "close"])
        self.assertEqual(c["manifest"]["blocks"][1]["cue_phases"], ["settle_in", "settle_out"])

    def test_electrical_out_of_scope(self):
        with self.assertRaises(rsx2.RSX2Error):
            rsx2.parse(V2.replace("@Vector11:DeviceOutput(AR, symbol=dragon)", "@Vector11:DeviceOutput(TENS)"))
        p = rsx2.parse(V2)
        p["blocks"][3]["vectors"][2]["args"] = "galvanic"
        with self.assertRaises(B.BridgeError):
            B.to_cue(p)


if __name__ == "__main__":
    unittest.main()
