import json
import pathlib
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent)]
from rsso import night as N  # noqa: E402
from rsso import peak as P  # noqa: E402

NODE = shutil.which("node")
CODES = [{"code": "..-", "label": "Lion"}, {"code": "-.-", "label": "French words", "area": "french"}, {"code": "---", "label": "The crash", "trauma": True}]


class Sleep(unittest.TestCase):
    def test_plan_holds_trauma_back(self):
        p = N.make_plan(CODES)
        self.assertEqual([c["code"] for c in p["codes"]], ["..-", "-.-"])
        self.assertEqual(len(p["held"]), 1)
        with self.assertRaises(ValueError):
            N.make_plan(CODES, trauma="play")

    def test_closed_loop_cues_in_deep_sleep_and_respects_limits(self):
        p = N.make_plan(CODES, limit=40)
        out = N.Sleeper(5).run(N.Controller(p))
        self.assertLessEqual(len(out["cues"]), 40)
        self.assertGreater(out["report"]["in_n3"], 85)
        self.assertNotIn("---", {c["code"] for c in out["cues"]})
        self.assertTrue(all(c["intensity"] <= p["max_intensity"] for c in out["cues"]))
        rnd = N.Sleeper(5).run(N.Controller(p, "random"))
        self.assertGreater(rnd["report"]["arousals"], out["report"]["arousals"])
        self.assertEqual(N.Sleeper(5).run(None)["report"]["cues"], 0)

    def test_tmr_and_diary(self):
        rows = [{"cued_before": 20, "cued_after": 19, "uncued_before": 20, "uncued_after": 16 + k % 2} for k in range(5)]
        self.assertEqual(N.tmr_analyze(rows)["verdict"], "helps")
        self.assertEqual(N.tmr_analyze(rows[:2])["verdict"], "too_few")
        d = [{"night": k, "cueing": k % 2 == 0, "nightmares": (0 if k % 2 == 0 else 2) + (k % 3 == 0), "distress": 3} for k in range(10)]
        self.assertEqual(N.diary_compare(d)["verdict"], "lower")

    def test_nightmare_response(self):
        s = N.Sleeper(8, nightmares=2.0)
        r = N.nightmare_response(N.make_plan([], trauma="wake"), s)
        self.assertGreaterEqual(r["nightmares"], 1)
        self.assertEqual(r["safety_codes"], 0)


class Reward(unittest.TestCase):
    def test_family(self):
        f = N.family("-.", 4)
        self.assertEqual(f, ["-. .", "-. -", "-. ..", "-. .-"])
        self.assertEqual(len(N.families_ok({"hoops": "-.", "french": "-.", "tennis": "-.-"})), 3)
        with self.assertRaises(ValueError):
            N.family("x", 2)

    def test_events(self):
        st = N.reward_state("hoops", "-. .")
        self.assertTrue(N.on_event(st, {"t_ms": 0, "success": True, "detect_ms": 150})["play"])
        self.assertEqual(N.on_event(st, {"t_ms": 500, "success": True})["why"], "too soon after the last reward")
        self.assertFalse(N.on_event(st, {"t_ms": 3000, "success": False})["play"])
        rep = N.reward_report(st)
        self.assertEqual((rep["successes"], rep["rewarded"], rep["median_ms"]), (2, 1, 190))

    def test_moves(self):
        rng = P.Rng(3)
        good = sum(1 for _ in range(20) if any(e["success"] for e in N.detect_moves(N.sim_move(rng, True))))
        poor = sum(1 for _ in range(20) if any(e["success"] for e in N.detect_moves(N.sim_move(rng, False))))
        self.assertGreaterEqual(good, 16)
        self.assertLessEqual(poor, 2)

    def test_notice(self):
        t = [{"channel": "both" if k % 2 else "vibration", "noticed": True, "latency_ms": (500 if k % 2 else 900) + k * 7} for k in range(12)]
        self.assertIn("sooner", N.notice_report(t)["say"])


class Simulation(unittest.TestCase):
    def test_results_file_is_current(self):
        self.assertEqual((HERE.parent / "results" / "night.md").read_text(encoding="utf-8"), N.report(N.evaluate()))


@unittest.skipUnless(NODE, "node not installed")
class Parity(unittest.TestCase):
    def test_python_and_javascript_identical(self):
        seeds = [[1, "closed", False], [2, "random", False], [3, "closed", True], [4, "none", False], [5, "closed", False]]
        events = [{"t_ms": 0, "source": "rim", "success": True, "detect_ms": 120}, {"t_ms": 800, "success": True}, {"t_ms": 2500, "source": "answer", "success": False},
                  {"t_ms": 4000, "source": "motion", "success": True, "detect_ms": 150}] + [{"t_ms": 6000 + k * 1600, "success": True} for k in range(25)]
        tmr = [{"cued_before": 20, "cued_after": 18 - k % 3, "uncued_before": 19, "uncued_after": 15 + k % 2} for k in range(6)]
        diary = [{"night": k, "cueing": k % 2 == 0, "nightmares": k % 3, "distress": (k * 7) % 10} for k in range(12)]
        notice = [{"channel": "both" if k % 2 else "vibration", "noticed": k % 5 != 0, "latency_ms": 400 + (k * 37) % 300} for k in range(14)]
        areas = {"hoops": "-.", "french": ".-", "tennis": "-.-", "chess": ".-"}
        inp = {"seeds": seeds, "codes": CODES, "events": events, "tmr": tmr, "diary": diary, "notice": notice, "areas": areas}
        js = json.loads(subprocess.run([NODE, str(HERE / "js_night.js")], input=json.dumps(inp), capture_output=True, text=True, check=True).stdout)
        nights = []
        for seed, kind, poor in seeds:
            sl = N.Sleeper(seed, 8, 1, {"W": 0.8, "N1": 0.3, "N2": 0.65, "N3": 0.6, "REM": 0.6} if poor else None, 1)
            plan = N.make_plan(CODES, ["vibration", "light"], "wake" if seed % 2 else "safety")
            run = sl.run(None if kind == "none" else N.Controller(plan, kind))
            nights.append({"run": run, "nm": N.nightmare_response(plan, sl)})
        rng = P.Rng(77)
        moves = [N.detect_moves(N.sim_move(rng, k % 2 == 0)) for k in range(12)]
        st = N.reward_state("hoops", N.family("-.", 3)[0])
        for e in events:
            N.on_event(st, e)
        py = {"nights": nights, "plan": N.make_plan(CODES), "tmr": N.tmr_analyze(tmr), "diary": [N.diary_compare(diary), N.diary_compare(diary, "distress")],
              "fam": [N.family("-.", 5), N.families_ok(areas)], "reward": [st["log"], N.reward_report(st)], "moves": moves, "notice": N.notice_report(notice)}
        for k in py:
            self.assertEqual(json.loads(json.dumps(py[k])), js[k], k)
        for a, b in zip(N.template(), js["template"]):     # exp() may differ in the last bit between the two runtimes
            self.assertAlmostEqual(a, b, places=12)


if __name__ == "__main__":
    unittest.main()
