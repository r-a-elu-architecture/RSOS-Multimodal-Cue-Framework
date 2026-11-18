"""spec/SUBSTANCES_NOW.md S1-S3."""
import json
import pathlib
import random
import re
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE)]
from rsso import linx_mcp as L, safety  # noqa: E402
import test_linx_mcp as T  # noqa: E402

NODE = shutil.which("node")
FIELDS = ("substances", "sedative_prescribed", "arrangements_for_after", "self_harm_signal", "job_loss", "housing_risk",
          "no_income", "intensity_mechanism", "history_reference")


def events(n=500, seed=4242):
    r = random.Random(seed)
    out = []
    for _ in range(n):
        ev = {f: r.random() < 0.3 for f in FIELDS}
        if r.random() < 0.7:
            ev["distress"] = r.randint(0, 10)
        if r.random() < 0.6:
            ev["sleep_h"] = r.choice([2, 3.5, 5, 8])
        if r.random() < 0.4:
            ev["clinical_result"] = r.choice(["none", "low", "moderate", "high"])
        out.append(ev)
    return out


class S1Rule(unittest.TestCase):
    def test_grid(self):
        for c in T.GRID2:
            a = T.chk2(c)
            out = L.propose_plan(T.INTAKES[0], a)
            if a["substances"] in ("yes", "unsure"):
                self.assertIsNone(out["plan"], a)
                if a["medication"] in ("sedative", "unsure"):
                    self.assertEqual(out["mode"], "Clinician-led protocol")
                else:
                    self.assertIn(out["mode"], ("Stabilisation", "Paused: practical", "Clinician-led protocol"))
                    if out["mode"] == "Stabilisation":
                        self.assertEqual(out["allowed_now"]["regulation_programs"], list(safety.REGULATING))
            else:   # substances no: the v2 result, which never involved the new screen
                self.assertNotIn("substances_now", out["screens"])


@unittest.skipUnless(NODE, "node not installed")
class S2Parity(unittest.TestCase):
    def test_python_equals_javascript(self):
        evs = events()
        js = (f"const S=require({json.dumps(str(HERE.parents[1] / 'docs' / 'js' / 'safety.js'))});"
              "let s='';process.stdin.on('data',d=>s+=d);process.stdin.on('end',()=>{const e=JSON.parse(s);"
              "process.stdout.write(JSON.stringify(e.map(x=>{const r=S.observe(S.newState(),x,0);"
              "return [S.screen(x),r[0].mode,r[1].messages];})));});")
        out = json.loads(subprocess.run([NODE, "-e", js], input=json.dumps(evs), capture_output=True, text=True,
                                        check=True).stdout)
        py = [[safety.screen(e), safety.observe(safety.new_state(), e)[0]["mode"],
               safety.observe(safety.new_state(), e)[1]["messages"]] for e in evs]
        self.assertEqual(py, out)
        self.assertTrue(any("substances_now" in p[0] for p in py))


class S3Wording(unittest.TestCase):
    def test_message(self):
        self.assertIsNone(T.CRISIS.search(safety.MESSAGES["substances_now"]))


if __name__ == "__main__":
    unittest.main()
