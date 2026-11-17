"""spec/FIXES_R6.md Q2: fold() pinned to one Unicode table, identical in Python and JavaScript for every table entry and for
code points newer than the table (Unicode 16 outlined letters and digits); levels and Spine identical on them."""
import json
import pathlib
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from rsso import foldtable as FT  # noqa: E402
from rsso import safety as S  # noqa: E402
from rsso import watchdog as W  # noqa: E402

NEW = "".join(chr(c) for c in range(0x1CCD6, 0x1CCFA))   # Unicode 16: outlined Latin letters and digits


def samples():
    keys = sorted(FT.MAP)
    out = ["".join(chr(k) for k in keys[i:i + 40]) for i in range(0, len(keys), 40)]
    marks = [chr(a) for a, b in FT.MARKS] + [chr(b) for a, b in FT.MARKS]
    out += ["".join(marks[i:i + 40]) for i in range(0, len(marks), 40)]
    out += [NEW, "\U0001CCD8\U0001CCD2\U0001CCDB bath", "PROTOCOL tier\U0001CCF4\U0001CCF1\U0001CCF4", 'MODE "\U0001CCE4bserver"',
            "I am stéady", "I am stéady", "ɑɡɩȷօսցⅼ", "ﬁne", "\U0001D422ce bath"]
    return out


@unittest.skipUnless(shutil.which("node"), "no node")
class Pinned(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = samples()
        r = subprocess.run(["node", str(HERE / "js_fixes_r5.js")], input=json.dumps({"sources": cls.s, "checks": [], "states": [], "texts": cls.s}),
                           capture_output=True, text=True, check=True)
        cls.js = json.loads(r.stdout)

    def test_fold_identical_for_every_entry_and_newer_code_points(self):
        diff = [k for k, s in enumerate(self.s) if S.fold(s) != self.js["fold"][k]]
        self.assertEqual(diff, [])

    def test_levels_and_spine_identical(self):
        for k, s in enumerate(self.s):
            self.assertEqual(W.level_of_program(s, {"edited": True}), self.js["level"][k], repr(s))
            self.assertEqual([f["flag"] for f in S.spine_flags(s)], self.js["spine"][k], repr(s))

    def test_newer_code_points_are_kept_as_they_are(self):
        self.assertEqual(S.fold(NEW), NEW)

    def test_accents_and_added_look_alikes(self):
        self.assertEqual(S.fold("I am stéady"), "i am steady")
        self.assertEqual(S.fold("I am stéady"), "i am steady")
        self.assertEqual(S.fold("ɑɡɩȷօսցⅼ"), "agijougl")
        self.assertTrue(S.spine_flags("\U0001D422ce bath"))

    def test_table_is_pinned(self):
        self.assertEqual(FT.UNICODE, "15.1.0")


if __name__ == "__main__":
    unittest.main()
