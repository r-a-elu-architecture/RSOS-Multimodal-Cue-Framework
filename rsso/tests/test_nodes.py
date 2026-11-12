import json
import pathlib
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parents[1] / "rsx"), str(HERE)]
from rsso import nodes  # noqa: E402
from rsx import compile_rsx  # noqa: E402
from test_memstack import person_log  # noqa: E402

NODE = shutil.which("node")
INTAKES = [
    dict(concerns=["ptsd", "chronic_stress", "habits"], symptoms="Flashbacks, tension in the chest", author="therapist",
         physiology=dict(resting_hr=72, rmssd=28), triggers=["Loud voices"], dose=dict(per_day=50, days=4), devices=dict(hr=True, eeg=True),
         nodes=[dict(archetype="LION", frames=["I breathe fully and completely, my memory is exceptional"], O="Cedar",
                     K="Spine straight, saying no with calm confidence", contexts=["At work", "Saying no to scrolling"], believability=7),
                dict(archetype="RAVEN", frames=["I am good at seeing things", "I am intelligent and see broadly and all"]),
                dict(archetype="OBSERVER"), dict(name="Rabbit", frames=["I will not be afraid"], G="Mint")]),
    dict(concerns=["focus"], nodes=[dict(archetype="LION"), dict(archetype="LION", name="Lion at work")], dose=dict(per_day=10, days=7)),
    dict(nodes=[]),
]
FRAMES = [["I am intelligent and see broadly and all", "associated", None], ["I am good at seeing things", "associated", 4],
          ["Nothing binds. Only observed", "observer", None], ["I will never be perfect", "associated", 9],
          ["I breathe fully and completely, my memory is exceptional", "associated", None]]


class Nodes(unittest.TestCase):
    def test_programs_compile_with_node_fields(self):
        for intake in INTAKES:
            for n in nodes.plan(intake)["nodes"]:
                tl = compile_rsx(n["program"])
                tier = next(e for e in tl["events"] if e["kind"] == "tier")
                self.assertEqual(tier["frames"], n["frames"])
                self.assertEqual(tier["tacton"], n["tacton"])
                pulses = [[e["on"], e["off"]] for e in tl["events"] if e["channel"] == "haptic" and e.get("tacton")]
                expect = [[on, 100] for on, _ in nodes.tacton_pulses(n["tacton"])]
                self.assertEqual(pulses, expect)

    def test_codes_unique_and_archetypes_kept(self):
        p = nodes.plan(INTAKES[0])
        codes = [n["tacton"] for n in p["nodes"]]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertEqual(codes[:3], ["..-", ".-.", "-"])
        self.assertEqual(p["nodes"][0]["glyph"], "🦁")
        self.assertTrue(p["therapist_led"])
        self.assertIn("T444", p["tiers"])
        two = nodes.plan(INTAKES[1])["nodes"]
        self.assertNotEqual(two[0]["tacton"], two[1]["tacton"])

    def test_frame_check_examples(self):
        wide = nodes.frame_check("I am intelligent and see broadly and all")
        narrow = nodes.frame_check("I am good at seeing things")
        self.assertEqual(wide["scope"], "broad")
        self.assertEqual(narrow["scope"], "narrow")
        self.assertGreater(wide["score"], narrow["score"])
        self.assertIn("negation", nodes.frame_check("I will not be afraid")["flags"])
        self.assertEqual(nodes.frame_check("Nothing binds. Only observed", "observer")["flags"], [])

    def test_channel_opening(self):
        runs, _ = person_log(seed=5, weeks=4)
        op = nodes.channel_opening(runs)
        self.assertTrue(op)
        for v in op.values():
            self.assertLessEqual(v["completed"], v["runs"])


@unittest.skipUnless(NODE, "node not installed")
class Parity(unittest.TestCase):
    def test_python_and_js_identical(self):
        runs, _ = person_log(seed=5, weeks=4)
        out = json.loads(subprocess.run([NODE, str(HERE / "js_nodes.js")], capture_output=True, text=True, check=True,
                                        input=json.dumps(dict(intakes=INTAKES, frames=FRAMES, runs=runs))).stdout)
        self.assertEqual([nodes.plan(i) for i in INTAKES], out["plans"])
        self.assertEqual([nodes.frame_check(*f) for f in FRAMES], out["frames"])
        self.assertEqual(nodes.channel_opening(runs), out["opening"])


if __name__ == "__main__":
    unittest.main()
