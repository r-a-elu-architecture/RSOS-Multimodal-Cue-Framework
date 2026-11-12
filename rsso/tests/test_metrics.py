import json
import pathlib
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parents[1] / "rsx")]
from rsso import metrics  # noqa: E402
from test_memstack import person_log  # noqa: E402

NODE = shutil.which("node")


def cases():
    out = []
    for seed, weeks in ((5, 4), (9, 2), (2, 1)):
        runs, srbai = person_log(seed=seed, weeks=weeks)
        out.append(dict(runs=runs, srbai=srbai, settings=dict(inhale=4, exhale=6)))
    runs, srbai = person_log(seed=3, weeks=2)
    for r in runs[::7]:
        r["completed"] = 0
    out.append(dict(runs=runs, srbai=[], settings=dict(inhale="4", exhale="4")))
    out.append(dict(runs=[], srbai=[], settings={}))
    return out


class Metrics(unittest.TestCase):
    def test_values_sensible(self):
        c = cases()[0]
        v = metrics.compute(c["runs"], c["srbai"], c["settings"])
        self.assertEqual(v["RSF"], 100.0)
        self.assertEqual(v["CRI"], 0.0)
        self.assertEqual(v["SBB"], "1:1.5")
        self.assertGreater(v["ARC"], 0)            # starts became faster over four weeks
        self.assertEqual(v["MCRAL"], 4.18)
        self.assertTrue(0 <= v["SEP"] <= 100 and 0 <= v["SPV"] <= 100)
        e = metrics.compute([], [], {})
        self.assertTrue(all(x is None for x in e.values()))
        s = metrics.compute(cases()[3]["runs"], [], {})
        self.assertGreater(s["CRI"], 0)

    def test_registry_complete(self):
        reg = metrics.registry()
        codes = {m["code"] for m in reg["metrics"]}
        for c in ["CRI", "SRI", "RSF", "SEP", "ARC", "SAR", "LGC", "LAW", "RIF", "RAI", "MCRAL", "RPB", "LLMI", "SME", "MMR", "ECOI",
                  "SRCD", "TGR", "IMIP", "CSRT", "LSML", "SML", "CRBS", "SBB", "SPV", "MCI", "TIC", "STC", "STB", "ERV", "EDA", "SCQ",
                  "ETH", "MOR", "RMPR", "PRM", "HSC", "RAC", "SMV", "IEC", "ECR", "SSI", "VEC", "SOM", "COM", "ERM", "DPI", "SIR",
                  "GRII", "GSSF"]:
            self.assertIn(c, codes)
        lgc = next(m for m in reg["metrics"] if m["code"] == "LGC")
        self.assertEqual(len(lgc["names"]), 3)       # every recorded expansion of a drifting code is kept
        self.assertGreater(len(lgc["values"]), 150)
        for m in reg["metrics"]:
            self.assertIn(m["operational"]["status"], ("you", "system", "record"))


@unittest.skipUnless(NODE, "node not installed")
class Parity(unittest.TestCase):
    def test_python_and_js_identical(self):
        cs = cases()
        js = json.loads(subprocess.run([NODE, str(HERE / "js_metrics.js")], input=json.dumps(cs), capture_output=True, text=True, check=True).stdout)
        for c, j in zip(cs, js):
            self.assertEqual(metrics.compute(c["runs"], c["srbai"], c["settings"]), j)


if __name__ == "__main__":
    unittest.main()
