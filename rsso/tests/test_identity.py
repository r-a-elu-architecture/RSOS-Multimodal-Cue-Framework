import copy
import json
import pathlib
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parent.parent / "rsx")]
from rsso import identity as I  # noqa: E402
from rsx import compile_rsx  # noqa: E402

NODE = shutil.which("node")


def practised(seed=1, growth=1.0, pull=1.5, weeks=12, tid="steady"):
    """A library profile with ratings, contexts, walks, rehearsals and versions from the simulation."""
    p = I.from_template(tid, "p" + str(seed), 0)
    sim = I.SimIdentity(seed, growth, pull)
    for w in range(weeks):
        I.rate(p, w * 7 * 86400, sim.rate(w * 7))
        if w % 2:
            I.rate(p, w * 7 * 86400 + 3600, sim.rate(w * 7, True), "after_mirroring")
    rng = I.P.Rng(seed)
    for k in range(12):
        I.add_context(p, k * 86400, ["desk", "meeting", "call", "home"][k % 4], k % 3 == 0, rng.u() < 0.7, 2 + rng.u() * 9 if k % 5 else None)
    I.set_tree(p, "A lion at the door", [{"part": "mane", "context": "Before a meeting", "code": ".-"}, {"part": "paws", "context": "On the phone", "code": "-."},
                                          {"part": "eyes", "context": "Saying no", "code": ".."}])
    for c in range(5):
        for kind in ("tree", "single"):
            I.add_walk(p, c * 86400 + (kind == "single"), kind, [{"part": x, "ok": rng.u() < (0.8 if kind == "tree" else 0.6), "ms": int(1500 + rng.u() * 2000)}
                                                                  for x in ("mane", "paws", "eyes")])
    for k in range(6):
        b = 45 + rng.u() * 20
        I.add_rehearsal(p, k * 86400, ["honesty", "fairness"][k % 2], "violation", b, b * (0.8 + rng.u() * 0.15), b * 0.98, 6)
        I.add_rehearsal(p, k * 86400 + 60, "", "neutral", b, b * (0.95 + rng.u() * 0.1), b)
    I.save_version(p, 0, "first")
    p["levels"]["values"]["text"] = "Clarity, courage, care, rest."
    p["environment"]["music"] = "Silence"
    p["symbol"] = "🦁🐉"
    I.save_version(p, 86400, "after a month")
    return p


class Profile(unittest.TestCase):
    def test_issues_and_completeness(self):
        p = I.make_profile("a", "A", "", "x")
        self.assertEqual({i["field"] for i in I.issues(p)}, {"symbol", "code", *I.LEVELS})
        q = I.from_template("steady")
        self.assertEqual(I.issues(q), [])
        self.assertTrue(I.completeness(q)["ready"])
        q["levels"]["values"]["code"] = "..-"
        q["levels"]["beliefs"]["code"] = ".-"
        q["levels"]["skills"]["code"] = ".-.."
        says = [i["say"] for i in I.issues(q)]
        self.assertIn("Values: the same code as the login code; the body cannot tell them apart.", says)
        self.assertTrue(any(s.startswith("Skills: the code starts like beliefs") for s in says))
        q["code"] = "   "
        self.assertIn("code", [i["field"] for i in I.issues(q)])

    def test_versions_diff(self):
        p = practised()
        d = I.diff(p["versions"][0], p["versions"][1])
        self.assertEqual([x["field"] for x in d], ["symbol", "values", "environment.music"])

    def test_coherence(self):
        self.assertEqual(I.coherence({l: 8 for l in I.LEVELS})["score"], 8)
        c = I.coherence({"mission": 10, "identity": 10, "values": 10, "beliefs": 4})
        self.assertLess(c["score"], c["mean"])
        self.assertEqual(c["weakest"], "beliefs")
        self.assertIsNone(I.coherence({"mission": 5}))

    def test_trend_and_drift_known_answers(self):
        self.assertEqual(I.trend(practised(3, 1.0, 0.0, 26))["verdict"], "rising")
        self.assertEqual(I.drift(practised(3, 0.0, 2.0, 26))["verdict"], "drifts")
        self.assertEqual(I.trend(I.from_template("learner"))["verdict"], "too_few")

    def test_generalisation_walks_rehearsals(self):
        p = practised()
        g = I.generalisation(p)
        self.assertEqual(g["trained"] + g["new"], 12)
        w = I.walks_report(p)
        self.assertEqual(w["tree"]["walks"], 5)
        self.assertIsNotNone(w["compare"])
        r = I.rehearsals_report(p)
        self.assertEqual([v["value"] for v in r["values"]], ["fairness", "honesty"])
        self.assertEqual(r["neutral"], 6)
        self.assertTrue(I.reaction({"before": 50, "during": 40, "after": 48})["reacted"])
        self.assertFalse(I.reaction({"before": 50, "during": 47, "after": 48})["reacted"])

    def test_switching(self):
        log = []
        I.switch(log, 0, "learner", "login")
        I.settle(log, 40)
        I.switch(log, 100, "maker", "schedule")
        I.interrupt(log, 130, "steady")
        I.settle(log, 140)
        self.assertEqual(I.current(log, "steady"), "steady")
        self.assertEqual(I.switch_report(log)["median_settle_s"], 25)
        sch = [{"from": "08:00", "to": "12:00", "profile": "learner"}, {"from": "22:00", "to": "06:00", "profile": "rest"}]
        self.assertEqual([I.profile_at(sch, m) for m in (480, 719, 720, 1380, 200)], ["learner", "learner", None, "rest", "rest"])


class Programs(unittest.TestCase):
    def test_every_program_compiles(self):
        p = practised()
        progs = [I.day_rsx(p), I.night_rsx(p), I.sequence_rsx(p, 'the "old" fear'), I.install_rsx(I.from_template("maker"))] + [d["rsx"] for d in I.week_plan(p)]
        for src in progs:
            out = compile_rsx(src)
            self.assertGreater(out["duration_ms"], 0)
        night = compile_rsx(I.night_rsx(p))
        self.assertEqual([ph["name"] for ph in night["phases"]], ["symbol", *I.LEVELS, "close"])
        self.assertEqual(len(I.week_plan(p)), 8)

    def test_dose(self):
        d = I.dose_plan()
        self.assertEqual((d["total"], d["times"][0], d["times"][-1], len(d["times"])), (360, "08:00", "21:00", 12))

    def test_library(self):
        self.assertEqual(len(I.LIBRARY), 6)
        codes = [t["code"] for t in I.LIBRARY]
        self.assertEqual(len(set(codes)), 6)
        for t in I.LIBRARY:
            self.assertEqual(I.issues(I.from_template(t["id"])), [], t["id"])


class Simulation(unittest.TestCase):
    def test_results_file_is_current(self):
        self.assertEqual((HERE.parent / "results" / "identity.md").read_text(encoding="utf-8"), I.report(I.evaluate()))


@unittest.skipUnless(NODE, "node not installed")
class Parity(unittest.TestCase):
    def test_python_and_javascript_identical(self):
        profiles = [practised(s, g, pl, w, t) for s, g, pl, w, t in ((1, 1.0, 1.5, 12, "steady"), (7, 0.0, 0.0, 20, "maker"), (9, 2.0, 0.5, 3, "speaker"))]
        bad = I.make_profile("b ad/Ω", 'A "quoted" name', "", ".-x")
        bad["levels"]["values"]["code"] = ".-x"
        profiles.append(bad)
        log = []
        for k, (to, by) in enumerate((("a", "login"), ("b", "schedule"), ("a", "interrupt"), ("c", "person"))):
            I.switch(log, k * 100, to, by)
            if k % 2 == 0:
                I.settle(log, k * 100 + 7 * (k + 1))
        sch = [{"from": "08:00", "to": "12:00", "profile": "a"}, {"from": "21:30", "to": "06:15", "profile": "n"}]
        mins = [0, 374, 375, 480, 719, 720, 1290, 1439]
        inp = {"profiles": copy.deepcopy(profiles), "log": log, "schedule": sch, "minutes": mins}
        js = json.loads(subprocess.run([NODE, str(HERE / "js_identity.js")], input=json.dumps(inp), capture_output=True, text=True, check=True).stdout)
        py = {"profiles": [{"issues": I.issues(p), "completeness": I.completeness(p), "coherence": [I.coherence(r["scores"]) for r in p["ratings"]],
                            "trend": I.trend(p), "drift": I.drift(p), "generalisation": I.generalisation(p), "walks": I.walks_report(p),
                            "rehearsals": I.rehearsals_report(p), "diff": I.diff(p["versions"][0], p["versions"][-1]) if len(p["versions"]) > 1 else [],
                            "day": I.day_rsx(p), "night": I.night_rsx(p), "seq": I.sequence_rsx(p, "the worry"), "week": I.week_plan(p)} for p in profiles],
              "library": I.LIBRARY, "templates": [I.from_template(t["id"], "x" + t["id"], 5) for t in I.LIBRARY],
              "switches": I.switch_report(log), "at": [I.profile_at(sch, m) for m in mins], "dose": [I.dose_plan(), I.dose_plan("07:30", "22:00", 9, 14)]}
        ev = I.evaluate(30)
        py["evaluate"] = {"n": 30, "res": {":".join(str(int(x) if isinstance(x, float) and x.is_integer() else x) for x in k): v for k, v in ev["res"].items()}}
        for k in py:
            self.assertEqual(json.loads(json.dumps(py[k])), js[k], k)


if __name__ == "__main__":
    unittest.main()
