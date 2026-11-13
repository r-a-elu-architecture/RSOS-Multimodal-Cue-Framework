import json
import pathlib
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent)]
from rsso import trial as T  # noqa: E402

NODE = shutil.which("node")


def manual(design, changes, seed=3):
    t = T.new_trial(design, len(next(iter(changes.values()))), seed)
    for k, arm in enumerate(t["schedule"]):
        T.record(t, 5, 5 + changes[arm][sum(1 for a in t["schedule"][:k] if a == arm)], {"sleep_h": 6 + k % 3, "hour": 9 + k})
    return t


class Schedule(unittest.TestCase):
    def test_permuted_blocks(self):
        for d, spec in T.DESIGNS.items():
            s = T.schedule(d, 6, 11)
            arms = spec["arms"]
            self.assertEqual(len(s), 6 * len(arms))
            for b in range(6):
                self.assertEqual(sorted(s[b * len(arms):(b + 1) * len(arms)]), sorted(arms))
        self.assertEqual(T.schedule("ssit", 4, 1), T.schedule("ssit", 4, 1))
        self.assertNotEqual(T.schedule("ssit", 4, 1), T.schedule("ssit", 4, 2))

    def test_record_follows_schedule(self):
        t = T.new_trial("anchor_vs_sham", 1, 5)
        self.assertEqual(T.record(t, 4, 6)["arm"], t["schedule"][0])
        T.record(t, 4, 5)
        self.assertIsNone(T.record(t, 4, 5))


class Analysis(unittest.TestCase):
    def test_clear_and_unclear(self):
        better = T.analyze(manual("anchor_vs_sham", {"anchor": [3, 2.5, 3.5, 3, 2.8, 3.2], "sham": [0, 0.5, -0.5, 0.2, 0, 0.3]}))
        c = better["contrasts"][0]
        self.assertEqual(c["verdict"], "better")
        self.assertLess(c["p"], 0.01)
        self.assertGreater(c["lo"], 0)
        same = T.analyze(manual("anchor_vs_sham", {"anchor": [1, -1, 2, 0, 1, -0.5], "sham": [0.5, 0, 1, -1, 1.5, 0]}))
        self.assertEqual(same["contrasts"][0]["verdict"], "unclear")
        few = T.analyze(T.new_trial("cue_vs_none", 3, 1))
        self.assertEqual(few["contrasts"][0]["verdict"], "too_few")

    def test_three_arms_adjustment_and_balance(self):
        t = T.SimPerson({"higher": 2.0, "local": 1.0, "calm": 0.0}, seed=8, noise=0.8).run(T.new_trial("ssit", 10, 8))
        a = T.analyze(t)
        self.assertEqual([c["arm"] for c in a["contrasts"]], ["higher", "local"])
        self.assertEqual(a["contrasts"][0]["verdict"], "better")
        self.assertEqual(a["adjusted"]["for"], ["session order", "sleep_h"])
        self.assertIn("hour", a["balance"])

    def test_pool_and_consistency(self):
        res = [T.analyze(T.SimPerson({"anchor": 1.0, "sham": 0.0}, seed=p).run(T.new_trial("anchor_vs_sham", 8, p))) for p in range(20)]
        p = T.pool(res, "anchor")
        self.assertLess(p["lo"], 1.0)
        self.assertGreater(p["hi"], 1.0)
        c = T.consistency([{"scenario": "s1", "choice": "a"}, {"scenario": "s1", "choice": "a"}, {"scenario": "s1", "choice": "b"},
                           {"scenario": "s2", "choice": "x"}, {"scenario": "s2", "choice": "x"}, {"scenario": "s3", "choice": "y"}])
        self.assertEqual(c["consistency"], 80)
        self.assertEqual(c["scenarios"], 2)

    def test_simulation(self):
        ev = T.evaluate(n_people=60)
        self.assertGreater(ev["power"][12], ev["power"][4])
        self.assertLessEqual(ev["false"][8], 10)
        self.assertLessEqual(ev["drift"]["adjusted_error"], ev["drift"]["raw_error"] + 0.05)

    def test_results_file_is_current(self):
        path = HERE.parent / "results" / "trial.md"
        before = path.read_text(encoding="utf-8")
        T.main(["--evaluate"])
        self.assertEqual(path.read_text(encoding="utf-8"), before)


@unittest.skipUnless(NODE, "node not installed")
class Parity(unittest.TestCase):
    def test_python_and_javascript_identical(self):
        schedules = [[d, b, s] for d in T.DESIGNS for b, s in ((3, 1), (6, 77))]
        sims = [["anchor_vs_sham", 8, 100 + k, {"anchor": 1.5, "sham": 0}, {"seed": 200 + k, "trend": 0.05 * k}] for k in range(4)]
        sims += [["ssit", 6, 9, {"higher": 2, "local": 1, "calm": 0}, {"seed": 9}],
                 ["order_ct_identity", 4, 4, {"ct_first": 1, "identity_peak_first": 0.5, "hybrid": 0.8, "identity_first": 0}, {"seed": 4, "noise": 2}],
                 ["cue_vs_none", 2, 6, {"cue": 1, "none": 0}, {"seed": 6}]]
        given = [manual("anchor_vs_sham", {"anchor": [3, 2.5, 3.5, 3, 2.8, 3.2], "sham": [0, 0.5, -0.5, 0.2, 0, 0.3]}),
                 T.new_trial("auto_vs_manual", 3, 2)]
        decisions = [{"scenario": s, "choice": c} for s, c in (("b", "x"), ("a", "y"), ("a", "y"), ("a", "z"), ("b", "x"), ("c", "q"), ("b", "w"))]
        inp = {"schedules": schedules, "sims": sims, "given": given, "decisions": decisions}
        js = json.loads(subprocess.run([NODE, str(HERE / "js_trial.js")], input=json.dumps(inp), capture_output=True, text=True, check=True).stdout)
        py = {"schedules": [T.schedule(*x) for x in schedules]}
        py["sims"] = []
        for d, b, seed, eff, o in sims:
            t = T.SimPerson(eff, **o).run(T.new_trial(d, b, seed))
            py["sims"].append({"trial": t, "analysis": T.analyze(t)})
        py["given"] = [T.analyze(t) for t in given]
        py["pool"] = T.pool([x["analysis"] for x in py["sims"] if x["trial"]["design"] == "anchor_vs_sham"], "anchor")
        py["consistency"] = T.consistency(decisions)
        for k in py:
            self.assertEqual(json.loads(json.dumps(py[k])), js[k], k)


if __name__ == "__main__":
    unittest.main()
