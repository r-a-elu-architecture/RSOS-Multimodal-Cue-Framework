import json
import pathlib
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent)]
from rsso import pron as R, peak as P  # noqa: E402

NODE = shutil.which("node")


class Pron(unittest.TestCase):
    def test_pitch_and_syllables_of_a_drill(self):
        d = R.DRILLS[0]
        F = R.features(R.synth(d["syllables"]))
        self.assertEqual(len(R.syllables_of(F)), 4)
        f0 = [f["f0"] for f in F if f["f0"]]
        self.assertTrue(110 < min(f0) and max(f0) < 195, (min(f0), max(f0)))

    def test_feedback_finds_the_planted_error(self):
        d = R.DRILLS[0]
        m = R.synth(d["syllables"])
        rng = P.Rng(3)
        x, k = R.learner(d, "vowels", rng)
        c = R.compare(x, m, [s["v"] for s in d["syllables"]])
        self.assertEqual((c["worst"], c["at"]["vowels"]), ("vowels", k))
        x, _ = R.learner(d, "correct", rng)
        self.assertIsNone(R.compare(x, m)["worst"])

    def test_mouth(self):
        vs, spans = ["i", "e", "i"], [[0.1, 0.34], [0.39, 0.63], [0.68, 0.92]]
        r = R.mouth_feedback(R.sim_mouth(P.Rng(4), vs, spans, wrong=(1, "o")), spans, vs)
        self.assertTrue(r["say"].startswith("On 'e' (syllable 2)"), r["say"])
        self.assertEqual(R.mouth_feedback([], spans, vs)["say"], "No face seen; check the light and the camera.")

    @unittest.skipUnless(NODE, "node not installed")
    def test_js_matches_python(self):
        js = json.loads(subprocess.run([NODE, str(HERE / "js_pron.js")], input="{}", capture_output=True, text=True, check=True).stdout)
        rng = P.Rng(21)
        k = 0
        for i, d in enumerate(R.DRILLS[:3]):
            m = R.synth(d["syllables"])
            F = R.features(m)
            jm = js["model"][i]
            self.assertEqual(jm[0], len(m))
            for a, b in zip(jm[1], m[1000:1010]):
                self.assertAlmostEqual(a, b, places=9)
            for (db, f0), f in zip(jm[2], F):
                self.assertAlmostEqual(db, f["db"], places=6)
                self.assertEqual(f0 is None, f["f0"] is None)
                if f0 is not None:
                    self.assertAlmostEqual(f0, f["f0"], places=6)
            self.assertEqual(jm[3], R.syllables_of(F))
            for kind in ("correct", "melody", "vowels", "rhythm"):
                x, kk = R.learner(d, kind, rng)
                c = R.compare(x, m, [s["v"] for s in d["syllables"]])
                self.assertEqual(js["compare"][k], [kk, c])
                k += 1
        mr = P.Rng(4)
        d = R.DRILLS[3]
        vs, spans = [s["v"] for s in d["syllables"]], [[0.1, 0.34], [0.39, 0.63], [0.68, 0.92]]
        self.assertEqual(js["mouth"][0], R.mouth_feedback(R.sim_mouth(mr, vs, spans, 30, (1, "o")), spans, vs))
        self.assertEqual(js["mouth"][1], R.mouth_feedback(R.sim_mouth(mr, vs, spans), spans, vs))
        self.assertEqual(js["resampled"], [1, 4, 7, 10])
        src = (HERE.parents[1] / "docs" / "js" / "pron.js").read_text(encoding="utf-8")
        self.assertIn(json.dumps(R.DRILLS, ensure_ascii=False, indent=2).replace("\n", "\n  "), src)


if __name__ == "__main__":
    unittest.main()
