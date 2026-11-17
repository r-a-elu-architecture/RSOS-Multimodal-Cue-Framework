"""spec/FIXES_R5.md Q2: Python and JavaScript identical on the fifth reviewer's adversarial inputs (review/r5/parity.py):
levels, fold, Spine, eventFromCheck and exit; and the built-in list in docs/js/lineage.js matches docs/protocols."""
import json
import pathlib
import random
import re
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
from rsso import safety as S  # noqa: E402
from rsso import watchdog as W  # noqa: E402

PARTS = ["PROTOCOL tier414", "PROTOCOL tıer414", "PROTOCOL TİER414", "# Tıer 414", "# Tier 414", "# ſomething Tier 420", "MODE \"obſerver\"",
         "MODE \"observer\"", "MODE\u000b\"observer\"", "MODE\f\"observer\"", "MODE \"observer\"", "MODE　\"observer\"", "PROTOCOL tier414",
         "PROTOCOL\ftier414", "MARK \"programmed:c1\"", "MARK \"programmed:ид\"", "MARK \"programmed:C1\"", " ", " ", "\x85", "\x1c", "﻿",
         "\x0b", "\x0c", "\r", "\n", " ", "\t", "​", "SAY \"ice bath\"", "SAY \"іce bath\"", "\"a\\ b\"", "\"x\\\x85\"", "Tier 4١4",
         "PROTOCOL tier414٣", "# Tier 414٣", "# rsos-level: clinician_led", "# RSOS-LEVEL: clinician_led", "# rsos-memory: yes", "KTier 414",
         "# KTier 414", "ＰＲＯＴＯＣＯＬ tier414", "# Tier 420"]
CHECKS = [{"intensity": v} for v in ["7_0", "0x10", "0b111", "0o7", "1e1", " 8 ", " 8", "﻿8", "٨", "８", "Infinity", "inf", "nan", [8], [], {},
                                     "  ", "8\n", "+8", ".5", "5.", "1_000", 8, 8.5, True, None, "7", "-1"]]
STATES = [{"mode": "STABILISE", "history": None}, {"mode": "STABILISE", "history": "x"}, {"mode": "STABILISE", "history": {}},
          {"mode": "CRISIS", "history": None}, [], "NORMAL", 5, {"mode": "STABILISE"}, {"mode": "PRACTICAL_CRISIS", "history": 3}]
TEXTS = ["ice bath", "ice bath", "ICE BATH", "ıce bath", "İce bath", "іce bath", "ice  bath", "ice\tbath", "ice\\tbath", "ice​bath",
         "hold your breath until you faint", "ſcalding", "freeẓing", "top ١٠%", "top 10%", "fine"]


def sources():
    rng = random.Random(5)
    return ["".join(rng.choice(PARTS) for _ in range(rng.randint(1, 6))) for _ in range(6000)] + PARTS


def js(payload):
    r = subprocess.run(["node", str(HERE / "js_fixes_r5.js")], input=json.dumps(payload), capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def safe(f):
    try:
        return f()
    except Exception as e:  # noqa: BLE001
        return "ERR:" + type(e).__name__


@unittest.skipUnless(shutil.which("node"), "no node")
class Parity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = sources()
        cls.js = js({"sources": cls.src, "checks": CHECKS, "states": STATES, "texts": TEXTS})

    def test_levels_identical(self):
        cues = [{"id": "c1", "tier": "414"}, {"id": "ид", "tier": "414"}]
        diff = [s for k, s in enumerate(self.src) if W.level_of_program(s, {"cues": cues, "edited": True}) != self.js["level"][k]]
        self.assertEqual(diff[:5], [], f"{len(diff)} of {len(self.src)} differ")

    def test_fold_identical(self):
        diff = [s for k, s in enumerate(self.src) if S.fold(s) != self.js["fold"][k]]
        self.assertEqual(diff[:5], [])

    def test_check_answers_identical(self):
        for k, c in enumerate(CHECKS):
            self.assertEqual(safe(lambda: S.event_from_check(c)), self.js["ev"][k], repr(c))

    def test_exit_identical(self):
        for k, st in enumerate(STATES):
            self.assertEqual(json.loads(json.dumps(safe(lambda: list(S.exit(st, "person", 5))))), self.js["exit"][k], repr(st))

    def test_spine_identical_and_folded(self):
        for k, t in enumerate(TEXTS):
            self.assertEqual([f["flag"] for f in S.spine_flags(t)], self.js["spine"][k], repr(t))
        for t in TEXTS[:10]:
            self.assertTrue(S.spine_flags(t), repr(t))

    def test_look_alikes_and_spaces_raise_the_level(self):
        for s in ("PROTOCOL tıer414", "PROTOCOL tier414", "ＰＲＯＴＯＣＯＬ tier414", "# Tier 420"):
            self.assertTrue(W.level_of_program(s)["therapist_led"], repr(s))
        for s in ("MODE \"observer\"", "MODE　\"observer\"", "MODE \"obſerver\""):
            self.assertTrue(W.level_of_program(s, {"edited": True})["memory_work"], repr(s))
        self.assertTrue(W.level_of_program('MARK "programmed:C1"', {"cues": [{"id": "c1", "tier": "414"}]})["therapist_led"])


class Builtins(unittest.TestCase):
    def test_lineage_builtin_list_matches_protocols(self):
        src = (REPO / "docs/js/lineage.js").read_text(encoding="utf-8")
        listed = re.findall(r'"([a-z0-9_]+)"', src[src.index("const BUILTINS"):src.index("];", src.index("const BUILTINS"))])
        self.assertEqual(sorted(listed), sorted(p.stem for p in (REPO / "docs/protocols").glob("*.rsx")))


if __name__ == "__main__":
    unittest.main()
