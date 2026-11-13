import json
import math
import pathlib
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent)]
from rsso import ppg  # noqa: E402

NODE = shutil.which("node")


synth = ppg.synthetic


class Camera(unittest.TestCase):
    def test_recovers_heart_rate_and_rmssd(self):
        for bpm, swing in ((60, 25), (72, 30), (95, 15), (120, 10)):
            sig, hr, rm = synth(bpm, swing)
            r = ppg.analyze(sig)
            self.assertTrue(r["ok"], (bpm, r))
            self.assertLess(abs(r["hr"] - hr), 2, (bpm, r["hr"], hr))
            self.assertLess(abs(r["rmssd"] - rm), 15, (bpm, r["rmssd"], rm))

    def test_refuses_bad_signals(self):
        self.assertFalse(ppg.analyze([])["ok"])
        self.assertIn("short", ppg.analyze(synth(seconds=5)[0])["say"])
        flat = [[i * 33.3, 100.0] for i in range(900)]
        self.assertFalse(ppg.analyze(flat)["ok"])
        noisy, _, _ = synth(noise=6.0)
        self.assertFalse(ppg.analyze(noisy)["ok"])

    @unittest.skipUnless(NODE, "node not installed")
    def test_python_and_javascript_identical(self):
        sigs = [synth(b, w, seed=s)[0] for b, w, s in ((60, 25, 1), (72, 30, 2), (95, 15, 3), (120, 10, 4))]
        sigs += [synth(noise=6.0)[0], synth(seconds=5)[0], [[i * 33.3, 100.0] for i in range(900)], []]
        js = json.loads(subprocess.run([NODE, str(HERE / "js_ppg.js")], input=json.dumps(sigs), capture_output=True, text=True, check=True).stdout)
        py = [ppg.analyze(s) for s in sigs]
        self.assertEqual(json.loads(json.dumps(py)), js)


if __name__ == "__main__":
    unittest.main()
