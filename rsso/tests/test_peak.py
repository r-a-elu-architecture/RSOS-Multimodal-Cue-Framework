import json
import pathlib
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parents[1] / "rsx"), str(HERE)]
from rsso import peak as P  # noqa: E402
from rsx import compile_rsx  # noqa: E402

NODE = shutil.which("node")


def probes(anchor, cue, sham=(), start=0, metric="rmssd"):
    t = start
    for kind, effs in (("cue", cue), ("sham", sham)):
        for e in effs:
            t += 600
            if metric == "rmssd":
                P.add_probe(anchor, {"ts": t, "kind": kind, "rmssd_before": 40, "rmssd_after": 40 * (1 + e / 100)})
            else:
                P.add_probe(anchor, {"ts": t, "kind": kind, "calm_before": 4, "calm_after": 4 + e})
    return anchor


def lion():
    return P.make_anchor("lion", "Lion", "🦁", "..-", "redirection", "cedar", "gold", "I move. I act.")


def cases():
    strong = probes(lion(), [18, 22, 20, 19, 24], [1, -1, 2])
    none = probes(lion(), [2, -3, 1, 0, -1], [1, -2, 0])
    falling = probes(lion(), [20, 18, 16, 8, 4, 1], [])
    bad = probes(lion(), [-8, -12, -10, -9], [1, 0, 1])
    calm = probes(lion(), [2, 3, 2], metric="calm")
    stressed = probes(lion(), [10, 6, 3, 1], [])
    for k in range(6):
        P.add_use(stressed, 9000 + k, k % 3 != 0)
    return {"strong": strong, "none": none, "falling": falling, "bad": bad, "calm": calm, "stressed": stressed}


class Anchor(unittest.TestCase):
    def test_make_and_composite(self):
        d = P.make_anchor("dragon", "Dragon", "🐉", "---", "healing", phrase="I am whole.")
        c = P.composite(lion(), d)
        self.assertEqual(c["code"], "..- ---")
        self.assertEqual(c["glyph"], "🦁 + 🐉")
        self.assertEqual(c["parts"], ["lion", "dragon"])
        self.assertEqual(c["channels"]["phrase"], "I move. I act. I am whole.")
        with self.assertRaises(ValueError):
            P.make_anchor("x", "X", "x", "abc")
        with self.assertRaises(ValueError):
            P.make_anchor("x", "X", "x", "..", "boss")

    def test_capture(self):
        self.assertTrue(P.capture_check({"source": "self_tap"})["ok"])
        self.assertTrue(P.capture_check({"source": "hrv", "rmssd": 52, "hr": 70}, {"rmssd": 40, "hr": 68})["ok"])
        self.assertFalse(P.capture_check({"source": "hrv", "rmssd": 44}, {"rmssd": 40})["ok"])
        moving = P.capture_check({"source": "hrv", "rmssd": 60, "hr": 95}, {"rmssd": 40, "hr": 70})
        self.assertFalse(moving["ok"])
        self.assertIn("10 bpm", moving["reason"])
        self.assertTrue(P.capture_check({"source": "eeg", "alpha_theta": 1.3}, {"alpha_theta": 1.0})["ok"])
        a = lion()
        P.add_capture(a, {"source": "hrv", "rmssd": 44}, {"rmssd": 40})
        P.add_capture(a, {"source": "self_tap", "intensity": 8})
        self.assertEqual(len(a["captures"]), 1)


class Strength(unittest.TestCase):
    def test_statuses(self):
        c = cases()
        self.assertEqual(P.strength(c["strong"])["status"], "strong")
        self.assertEqual(P.strength(c["strong"])["against"], "sham")
        self.assertEqual(P.strength(c["none"])["status"], "unclear")
        self.assertEqual(P.strength(c["falling"])["status"], "weakening")
        self.assertEqual(P.strength(c["bad"])["status"], "contaminated")
        self.assertEqual(P.strength(c["calm"])["metric"], "calm")
        self.assertEqual(P.strength(lion())["status"], "building")
        s = P.strength(c["strong"])
        self.assertLess(s["lo"], s["estimate"])
        self.assertLess(s["estimate"], s["hi"])

    def test_contamination_and_restoration(self):
        c = cases()
        self.assertTrue(P.contamination(c["bad"])["contaminated"])
        self.assertEqual(P.contamination(c["strong"])["risk"], "low")
        st = P.contamination(c["stressed"])
        self.assertEqual(st["risk"], "medium")
        self.assertTrue(any("during stress" in r for r in st["reasons"]))
        dragon = P.make_anchor("dragon", "White dragon", "🐉", "---", "healing")
        plan = P.restoration_plan(c["bad"], dragon)
        self.assertTrue(plan["needed"])
        self.assertTrue(any("🦁 + 🐉" in s for s in plan["steps"]))
        self.assertFalse(P.restoration_plan(c["strong"])["needed"])


class Chain(unittest.TestCase):
    def test_order_and_rsx(self):
        a = [P.make_anchor("lock", "Seal", "🔒", "-.-", "lockin", phrase="I own."),
             lion(),
             P.make_anchor("heal", "Dragon", "🐉", "---", "healing", "lavender", "white", "I am safe.")]
        ph = P.chain(a)
        self.assertEqual([p["role"] for p in ph], ["healing", "redirection", "lockin"])
        prog = compile_rsx(P.chain_rsx(a))
        tactons = [e.get("tacton") for e in prog["events"] if e["channel"] == "haptic"]
        self.assertEqual(sorted(set(tactons)), ["---", "-.-", "..-"])
        self.assertEqual([e["text"] for e in prog["events"] if e.get("kind") == "mark"], ["check healing", "check redirection", "check lockin"])
        rep = P.chain_report([{"role": "healing", "calm_before": 3, "calm_after": 6}, {"role": "redirection", "calm_before": 6, "calm_after": 6}])
        self.assertEqual(rep["worked"], 1)
        self.assertEqual(rep["weakest"], "redirection")


class Simulation(unittest.TestCase):
    def test_known_answers(self):
        ev = P.evaluate(n_each=20, probes=8, shams=4)
        self.assertGreaterEqual(ev["strong_found"], 90)
        self.assertLessEqual(ev["none_called_effect"], 10)
        self.assertGreaterEqual(ev["contamination_sensitivity"], 90)
        self.assertGreaterEqual(ev["contamination_specificity"], 90)

    def test_results_file_is_current(self):
        path = HERE.parent / "results" / "peak.md"
        before = path.read_text(encoding="utf-8")
        P.main(["--evaluate"])
        self.assertEqual(path.read_text(encoding="utf-8"), before)


@unittest.skipUnless(NODE, "node not installed")
class Parity(unittest.TestCase):
    def test_python_and_javascript_identical(self):
        c = cases()
        caps = [[{"source": "self_tap", "intensity": 7}, None], [{"source": "hrv", "rmssd": 52, "hr": 70}, {"rmssd": 40, "hr": 68}],
                [{"source": "hrv", "rmssd": 44.3}, {"rmssd": 40}], [{"source": "hrv", "rmssd": 60, "hr": 95}, {"rmssd": 40, "hr": 70}],
                [{"source": "eeg", "alpha_theta": 1.37}, {"alpha_theta": 1.0}], [{"source": "eeg"}, {}]]
        scen = [[k, s, n, sh] for k in ("strong", "weak", "none", "contaminated") for s in (3, 17, 401) for n, sh in ((8, 4), (5, 2))]
        resource = P.make_anchor("dragon", "White dragon", "🐉", "---", "healing")
        make = [["heal", "Dragon", "🐉", "---", "healing", "lavender", "white", "I am safe.", 0],
                ["lion", "Lion", "🦁", "..-", "redirection", "cedar", "gold", "I move. I act.", 0],
                ["lock", "Seal", "🔒", "-.-", "lockin", None, None, "I own.", 0]]
        rep = [{"role": "healing", "calm_before": 3, "calm_after": 6}, {"role": "redirection", "calm_before": 6, "calm_after": 5.5}, {"role": "lockin"}]
        inp = {"captures": caps, "scenarios": scen, "anchors": list(c.values()), "resource": resource, "make": make, "report": rep}
        js = json.loads(subprocess.run([NODE, str(HERE / "js_peak.js")], input=json.dumps(inp), capture_output=True, text=True, check=True).stdout)
        py = {"captures": [P.capture_check(a, b) for a, b in caps]}
        py["scenarios"] = []
        for k, s, n, sh in scen:
            sc = P.scenario(k, s, n, sh)
            py["scenarios"].append({"anchor": sc["anchor"], "true_strength": sc["true_strength"],
                                    "strength": P.strength(sc["anchor"]), "contamination": P.contamination(sc["anchor"])})
        py["anchors"] = [{"strength": P.strength(a), "contamination": P.contamination(a), "plan": P.restoration_plan(a, resource)} for a in c.values()]
        mk = [P.make_anchor(*m) for m in make]
        py["composite"] = P.composite(mk[0], mk[1])
        py["chain"] = P.chain(mk)
        py["rsx"] = P.chain_rsx(mk)
        py["report"] = P.chain_report(rep)
        for key in py:
            self.assertEqual(json.loads(json.dumps(py[key])), js[key], key)


if __name__ == "__main__":
    unittest.main()
