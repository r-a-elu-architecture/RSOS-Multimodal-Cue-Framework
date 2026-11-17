"""FIXES_R4 (spec/FIXES_R4.md): engine part (level patterns, Spine text, parity edge cases)."""
import json
import pathlib
import random
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE.parent)]
from rsso import safety as S, watchdog as W  # noqa: E402

NODE = shutil.which("node")
DANGER = 'PHASE x dur=2s {; SAY "Hold your breath until you almost pass out, then take an ice bath"; }'
FUTURE = 'FOR FUTURE "tomorrow" {\n  SEE "Take an ice bath until it hurts"\n}\n'


def adversarial(n=1500, seed=11):
    rng = random.Random(seed)
    parts = ["PROTOCOL tier414_x", "PROTOCOL Tier420", "# Tier 439", "#Tier 440 x", "# tier 414", 'MODE "observer"', 'mode  "OBSERVER"',
             'MARK "programmed:c1"', 'MARK "programmed:c1 "', "# rsos-level: clinician_led", "# rsos-memory: yes", 'SAY "a\\"b"', 'SAY "ice bath"',
             "\r\n", "\r", " ", " ", "\n", " ", "\t", " ", "é", "Tier 414", 'SEE "x"; FEEL "hold your breath until you faint"']
    return ["".join(rng.choice(parts) for _ in range(rng.randint(1, 8))) for _ in range(n)]


SOURCES = adversarial() + [DANGER, FUTURE]
CHECKS = [{"intensity": "abc"}, {"intensity": "7"}, {"intensity": float("nan")}, {"intensity": True}, {"sleep_h": " "}, {"intensity": 8, "sleep_h": "x"}]
CHECKS_JSON = [{"intensity": "abc"}, {"intensity": "7"}, {"intensity": True}, {"sleep_h": " "}, {"intensity": 8, "sleep_h": "x"}]
STATES = [{}, None, {"mode": "x"}, {"mode": "STABILISE", "history": []}]


class Engine(unittest.TestCase):
    def test_l2_every_quoted_string(self):
        self.assertTrue(S.spine_flags(W.level_of_program(DANGER)["text"]))
        self.assertTrue(S.spine_flags(W.level_of_program(FUTURE)["text"]))

    def test_builtins(self):
        for f in sorted((ROOT / "docs" / "protocols").glob("*.rsx")):
            r = W.level_of_program(f.read_text(encoding="utf-8"))
            self.assertEqual((r["therapist_led"], r["memory_work"], S.spine_flags(r["text"])), (False, False, []), f.name)

    def test_p1_edge_cases(self):
        self.assertNotIn("distress", S.event_from_check({"intensity": "abc"}))
        self.assertNotIn("distress", S.event_from_check({"intensity": float("nan")}))
        self.assertEqual(S.event_from_check({"intensity": "7"})["distress"], 7.0)
        self.assertEqual(S.exit({}, "person", 5)[1]["why"], "not_in_safety_mode")


@unittest.skipUnless(NODE, "node not installed")
class Parity(unittest.TestCase):
    def test_q2(self):
        r = subprocess.run([NODE, str(HERE / "js_fixes_r4.js")], input=json.dumps({"sources": SOURCES, "checks": CHECKS_JSON, "states": STATES}),
                           capture_output=True, text=True, check=True)
        js = json.loads(r.stdout)
        diff = [k for k, src in enumerate(SOURCES) if js["level"][k] != W.level_of_program(src, {"cues": [{"id": "c1", "tier": "414"}]})]
        self.assertEqual(diff, [], [SOURCES[k] for k in diff[:3]])
        self.assertEqual(js["ev"], [S.event_from_check(a) for a in CHECKS_JSON])
        self.assertEqual(js["exit"], [list(S.exit(st, "person", 5)) for st in STATES])


if __name__ == "__main__":
    unittest.main()
