"""FIXES_R3 (spec/FIXES_R3.md): structural fixes after the third review (review/r3, 15256fa)."""
import json
import pathlib
import re
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE.parent), str(ROOT / "rsx")]
from rsso import safety as S, watchdog as W  # noqa: E402

NODE = shutil.which("node")
OBS = (ROOT / "docs" / "protocols" / "node_observer.rsx").read_text(encoding="utf-8")
CUE = '# Programmed cue c1\nPROTOCOL cue_c1 "Programmed cue"\nPHASE cue dur=2s {\n  SAY "I am calm"\n  MARK "programmed:c1"\n}\n'
LEVEL = [[OBS, {}], [OBS, {"edited": True}], [CUE, {"cues": [{"id": "c1", "tier": "414"}]}], [CUE, {"cues": [{"id": "c1", "tier": "012"}]}],
         ["# Tier 439 release\nPROTOCOL x\n", {}], ["PROTOCOL tier420_y\n", {}], ["# rsos-level: clinician_led\n# rsos-memory: yes\nPROTOCOL z\n", {}],
         ['PROTOCOL o\nPHASE p dur=1s {\n  SAY "hold your breath until you almost pass out"\n}\n', {"edited": True}]]
STATES = [{}, {"mode": "nonsense"}, None, {"mode": "NORMAL", "history": []}]
OUTPUT = re.compile(r"UGCL\.feel\(|navigator\.vibrate\(|RSOSVoice\.speak\(|speechSynthesis\.speak\(|new Audio\(|createOscillator\(|send\(\"START\"\)")


class Engine(unittest.TestCase):
    def test_level_of_program(self):
        r = [W.level_of_program(src, o) for src, o in LEVEL]
        self.assertEqual([x["therapist_led"] for x in r], [False, True, True, False, True, True, True, False])
        self.assertEqual([x["memory_work"] for x in r], [False, True, False, False, False, False, True, False])
        self.assertTrue(S.spine_flags(r[7]["text"]))                      # dangerous wording reaches the Spine check

    def test_builtins_unchanged(self):
        for f in sorted((ROOT / "docs" / "protocols").glob("*.rsx")):
            r = W.level_of_program(f.read_text(encoding="utf-8"))
            self.assertEqual((r["therapist_led"], r["memory_work"], S.spine_flags(r["text"])), (False, False, []), f.name)

    def test_r3a_lion_dragon_codes_apart(self):
        from rsx import compiler
        ev = compiler.compile_rsx((ROOT / "docs" / "protocols" / "tier013_lion_dragon.rsx").read_text(encoding="utf-8"))["events"]
        pulses = [e for e in ev if e.get("kind") == "pulse"]
        lion = [e for e in pulses if e.get("tacton") == "..-"]
        dragon = [e for e in pulses if e.get("tacton") == "---"]
        self.assertTrue(lion and dragon)
        gap = min(d["t"] for d in dragon) - max(l["t"] + l["dur"] for l in lion)
        self.assertGreaterEqual(gap, 600)

    def test_r3c_malformed_states(self):
        self.assertEqual([S.observe(st, {"clinical_result": "high"}, 5)[0]["mode"] for st in STATES], ["CRISIS"] * 4)
        self.assertEqual([W.link({"escalation": {"active": True, "reasons": ["x"]}}, st, 5)[0]["mode"] for st in STATES], ["STABILISE"] * 4)

    def test_g2_every_output_page_is_covered(self):
        missing = []
        for f in sorted((ROOT / "docs").glob("*.html")):
            t = f.read_text(encoding="utf-8")
            if OUTPUT.search(re.sub(r"<script src[^>]*></script>", "", t)):
                if "js/outlet.js" not in t or not ("data-outlet-kind" in t or "RSOSOutlet.open(" in t or "RSOSOutlet.adopt(" in t):
                    missing.append(f.name)
        self.assertEqual(missing, [])

    def test_no_pin_path_in_protocol(self):
        t = (ROOT / "docs" / "safety.html").read_text(encoding="utf-8")
        self.assertNotIn("pin_set_older_state", t)
        self.assertNotIn("viaRecord", t.split("function ensurePin")[1].split("}")[0] if "function ensurePin" in t else "")


@unittest.skipUnless(NODE, "node not installed")
class Parity(unittest.TestCase):
    def test_g3(self):
        r = subprocess.run([NODE, str(HERE / "js_fixes_r3.js")], input=json.dumps({"level": LEVEL, "states": STATES}), capture_output=True, text=True, check=True)
        js = json.loads(r.stdout)
        self.assertEqual(js["level"], [W.level_of_program(src, o) for src, o in LEVEL])
        self.assertEqual(js["observe"], [S.observe(st, {"clinical_result": "high"}, 5)[0]["mode"] for st in STATES])
        self.assertEqual(js["link"], [W.link({"escalation": {"active": True, "reasons": ["x"]}}, st, 5)[0]["mode"] for st in STATES])


if __name__ == "__main__":
    unittest.main()
