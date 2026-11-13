import json
import pathlib
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parent.parent / "rsx")]
from rsso import copilot as C  # noqa: E402
from rsso import peak as P  # noqa: E402
from rsx import compile_rsx  # noqa: E402

NODE = shutil.which("node")


class Matrix(unittest.TestCase):
    def test_copilot_and_agreement(self):
        m = C.EXAMPLE_MATRIX
        self.assertEqual(C.copilot_match(m, "It was all my fault, I should have known")["branch"], "blame")
        self.assertEqual(C.copilot_match(m, "Everything is too much, I'm overwhelmed")["branch"], "flood")
        self.assertIsNone(C.copilot_match(m, "We went for a walk")["branch"])
        self.assertTrue(C.copilot_match(m, "I hate myself")["unsafe"])
        log = []
        C.add_utterance(log, 0, "it's my fault", m)
        C.add_utterance(log, 10, "we had dinner", m)
        C.mark(log, 0, "blame", 2)
        C.mark(log, 1, "none", 12)
        a = C.agreement(log)
        self.assertEqual((a["agree"], a["kappa"], a["median_s"]), (100, 1, 2))
        with self.assertRaises(ValueError):
            C.make_matrix("x", "c", [])

    def test_kappa(self):
        self.assertEqual(C.kappa([("a", "a"), ("b", "b"), ("a", "b"), ("b", "a")])["kappa"], 0)


class Levels(unittest.TestCase):
    def test_levels_and_chain(self):
        self.assertEqual(C.level_of("I am a failure")["level"], "identity")
        self.assertEqual(C.level_of("My purpose is to help others")["level"], "mission")
        c = C.chain("I can't speak in meetings")
        self.assertEqual([s["step"] for s in c["steps"]], ["detect", "analyse", "modify", "output", "future"])
        self.assertTrue(C.chain("I want to die")["held"])
        self.assertGreaterEqual(C.level_accuracy()["accuracy"], 80)


class Tools(unittest.TestCase):
    def test_profile_needs_consent(self):
        self.assertTrue(C.profile("senses", "I see it", subject="other")["refused"])
        p = C.profile("senses", " ".join(["I feel it, I touch it, warm and solid"] * 5))
        self.assertEqual(p["top"], "kinesthetic")

    def test_craving(self):
        trig = [{"id": "app", "kind": "app", "match": "casino"}, {"id": "late", "kind": "time", "match": "22:00-23:59"}]
        self.assertEqual(C.context_trigger(trig, {"kind": "app", "value": "Lucky Casino"})["id"], "app")
        self.assertEqual(C.context_trigger(trig, {"kind": "time", "value": "22:30"})["id"], "late")
        self.assertIsNone(C.context_trigger(trig, {"kind": "place", "value": "casino"}))
        log = [{"ts": k * 86400 * 3, "craving": 8 - k // 4} for k in range(24)]
        self.assertEqual(C.cue_reactivity(log)["verdict"], "falling")

    def test_core_transformation(self):
        ct = C.ct_start("anger")
        for a in ("to be respected", "to feel safe", "peace"):
            C.ct_answer(ct, a)
        self.assertTrue(ct["done"])
        self.assertGreater(compile_rsx(C.ct_rsx(ct))["duration_ms"], 0)
        held = C.ct_answer(C.ct_start("x"), "I want to die")
        self.assertTrue(held["held"])

    def test_programs_compile(self):
        for src in (C.rescript_rsx("the crash", "🦁", "I brake calmly"), C.dol9_rsx()):
            self.assertGreater(compile_rsx(src)["duration_ms"], 0)
        d = compile_rsx(C.dol9_rsx())["duration_ms"]
        self.assertEqual(d, 90000)

    def test_overrides_and_routes(self):
        log = [{"ts": k * 3600, "kind": "fear", "overridden": k % 4 != 0, "latency_s": 1 + k % 5, "after_wake": k % 7 == 0} for k in range(40)]
        m = C.override_metrics(log, 2)
        self.assertEqual((m["overrides"], m["per_day"]), (30, 15))
        self.assertEqual(m["oxq"], C._v(C.r1(30 / 32 * 100)))
        self.assertEqual(C.route_event("perceptual")["route"], "escalate")
        with self.assertRaises(ValueError):
            C.route_event("other")

    def test_timeline_context_burst_setting(self):
        t = C.timeline_report([{"year": 2001, "title": "b", "specific": True}, {"year": 1995, "title": "a", "specific": False}])
        self.assertEqual([n["year"] for n in t["nodes"]], [1995, 2001])
        self.assertEqual(C.speech_context("the meeting starts now", [{"id": "meet", "phrases": ["meeting starts"]}])["id"], "meet")
        self.assertEqual(C.burst("..-")["ms"], (500 + 200) * 3 + 800)
        s = [{"change": 3 + (k % 2), "setting": {"music": k % 2 == 1}} for k in range(10)]
        self.assertEqual(C.setting_effect(s, "music")["verdict"], "helps")


class Simulation(unittest.TestCase):
    def test_results_file_is_current(self):
        self.assertEqual((HERE.parent / "results" / "copilot.md").read_text(encoding="utf-8"), C.report(C.evaluate()))


@unittest.skipUnless(NODE, "node not installed")
class Parity(unittest.TestCase):
    def test_python_and_javascript_identical(self):
        sentences = [t for t, _ in C.LEVEL_TEST[::5]] + ["I want to die", "", "When the meeting starts I freeze", "It's my fault and everything is too much"]
        speech = [["senses", C.sim_speech(3, "senses", "visual", 400), "self", False], ["time", C.sim_speech(4, "time", "past", 300), "other", True],
                  ["senses", "I hear you", "other", False]]
        triggers = [{"id": "app", "kind": "app", "match": "casino"}, {"id": "bar", "kind": "place", "match": "bar"}, {"id": "late", "kind": "time", "match": "22:00-23:59"}]
        events = [{"kind": "app", "value": "Casino Royale"}, {"kind": "place", "value": "Sports Bar"}, {"kind": "time", "value": "23:10"}, {"kind": "time", "value": "08:00"}]
        rng = P.Rng(9)
        cue = [{"ts": k * 86400 * 2.5, "craving": int(7 - k * 0.1 + rng.gauss())} for k in range(30)]
        over = [{"ts": k * 7200 * 9, "kind": C.OVERRIDE_KINDS[k % 4], "overridden": rng.u() < 0.7, "latency_s": round(1 + rng.u() * 6, 1), "after_wake": k % 6 == 0} for k in range(50)]
        timeline = [{"year": 1980 + (k * 7) % 40, "title": "event " + str(k), "glyph": "✦", "specific": k % 3 == 0} for k in range(9)]
        contexts = [{"id": "meet", "phrases": ["meeting starts", "agenda*"]}, {"id": "fault", "phrases": ["my fault"]}]
        setting = [{"change": round(rng.gauss() * 2, 1), "setting": {"warmth": k % 2 == 0, "music": k % 3 == 0, "imagery": True}} for k in range(12)]
        ct_answers = ["to relax", "to feel free of it"]
        inp = {"seeds": [[1, 0.9], [2, 0.6]], "sentences": sentences, "speech": speech, "triggers": triggers, "events": events, "cue": cue, "ct": ct_answers,
               "timeline": timeline, "over": over, "contexts": contexts, "setting": setting}
        js = json.loads(subprocess.run([NODE, str(HERE / "js_copilot.js")], input=json.dumps(inp), capture_output=True, text=True, check=True).stdout)
        sessions = []
        for seed, acc in inp["seeds"]:
            log = C.sim_session(seed, 30, acc)
            sessions.append({"log": log, "agree": C.agreement(log)})
        ct = C.ct_start("the urge to check the phone")
        for a in ct_answers:
            C.ct_answer(ct, a)
        py = {"sessions": sessions, "chains": [C.chain(t) for t in sentences], "levels": C.level_accuracy(),
              "profiles": [C.profile(*x) for x in speech], "trig": [C.context_trigger(triggers, e) for e in events], "cue": C.cue_reactivity(cue),
              "ct": [ct, C.ct_rsx(ct, "..--")], "rescript": C.rescript_rsx("the argument at the door", "🦁", "I breathe out and speak slowly"),
              "timeline": C.timeline_report(timeline), "over": [C.override_metrics(over, 14), C.monthly(over)], "dol9": C.dol9_rsx(),
              "route": [C.route_event(k) for k in ("fear", "perceptual")], "ctx": [C.speech_context(t, contexts) for t in sentences],
              "block": C.four_day_block("Speak slowly", 3), "burst": [C.burst(c) for c in ("..-", "-. .-", "---")],
              "setting": [C.setting_effect(setting, f) for f in C.SETTING_FACTORS],
              "data": {"m": C.EXAMPLE_MATRIX, "p": C.PLUGINS, "t": [list(x) for x in C.LEVEL_TEST]}}
        for k in py:
            self.assertEqual(json.loads(json.dumps(py[k])), js[k], k)


if __name__ == "__main__":
    unittest.main()
