import json
import pathlib
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parents[1] / "rsx"), str(HERE)]
from rsso import linx as L, nodes  # noqa: E402
from rsx import compile_rsx  # noqa: E402

NODE = shutil.which("node")
TEXTS = [
    """I have chronic stress and burnout. When my boss raises his voice I freeze. I want to feel calm confidence at work.
My symbol is the lion. My frame is "I breathe fully and completely, my memory is exceptional". The smell of cedar and the taste of mint.
For old memories I want the observer, nothing binds. I scroll social media 3 hours. 50 times a day for 4 days. My resting heart rate is 72.""",
    "My client has PTSD and flashbacks at night. She wants to feel safe. Her symbol is like a phoenix, with the sound of rain and a feeling of warmth.",
    "I want to be focused at the office. My statement: I see the whole field clearly and choose my moment",
    "Stress at work when my boss shouts. I want calm confidence, like a lion, with the smell of cedar.",
    "",
]
CONVERSATIONS = [
    ["Stress at work when my boss shouts", "the lion", "\"I hold my ground and breathe fully\"", "golden light, the sound of waves, cedar", "at work, in meetings", "skip"],
    ["I keep scrolling instead of working", "a raven", "I am good at seeing things", "skip", "before sleep and at home", "opening instagram"],
    ["no", "an owl", "calm and wise", "I see everything from above", "lavender", "no", "no"],
    ["Stress when my boss shouts. I want calm confidence, like a lion.", "I hold my ground", "the smell of cedar", "in meetings and at work", "more: the sound of rain at work"],
]
FRAMES = [["I will not be afraid", "associated"], ["I am good at seeing things", "associated"], ["I am intelligent", "associated"],
          ["I just try to focus", "associated"], ["I will be strong", "associated"], ["Nothing binds. Only observed", "observer"],
          ["I see", "associated"], ["I don't get stressed at work", "associated"], ["I am good at holding my ground", "associated"]]
PROPOSALS = [
    {"schema": L.SCHEMA, "nodes": [{"ref": 0, "frames": ["I breathe fully and see the whole room", "I will never fail"], "A": "Low drum", "start": True},
                                   {"archetype": "RAVEN", "state": "Wide view", "frames": ["I see broadly, from above"], "contexts": ["At work"]},
                                   {"ref": 7, "state": "x"}, {"archetype": "UNICORN", "frames": ["I want to die"]}],
     "concerns": ["stress", "made_up"], "triggers": ["Raised voices", "x" * 200], "notes_for_therapist": ["Check the trauma history before observer work"], "run_now": 1},
    {"schema": "other"}, [1, 2], {"schema": L.SCHEMA},
]


def fixtures():
    intake = dict(concerns=["stress", "ptsd"], triggers=["Raised voices at work"],
                  nodes=[dict(archetype="LION", frames=["I hold my ground"], O="Cedar", contexts=["At work", "In meetings"]),
                         dict(archetype="OBSERVER", contexts=["Old memories at night"])])
    plan = nodes.plan(intake)
    plan.update(approved=True, intake=intake)
    runs = [dict(protocol="node_lion", sud_before=7, sud_after=k % 3 + 2) for k in range(5)] + \
           [dict(protocol="node_observer", sud_before=6, sud_after=6.5) for _ in range(3)] + [dict(protocol="override", sud_before="", sud_after=3)]
    ctx = dict(intake=intake, plan=plan, runs=runs)
    events = [dict(source="hr"), dict(source="context", text="a meeting at work"), dict(source="memory", text="a memory at night"), dict(source="eeg")]
    return ctx, plan, runs, events


class Linx(unittest.TestCase):
    def test_understand_reads_what_was_said(self):
        u = L.understand(TEXTS[0])
        self.assertEqual(u["concerns"], ["chronic_stress", "habits", "confidence"])
        lion = u["nodes"][0]
        self.assertEqual((lion["archetype"], lion["state"], lion["O"], lion["G"]), ("LION", "calm confidence", "Cedar", "Mint"))
        self.assertEqual(lion["frames"], ["I breathe fully and completely, my memory is exceptional"])
        self.assertEqual(u["nodes"][1]["mode"], "observer")
        self.assertEqual(u["triggers"], ["My boss raises his voice"])
        self.assertEqual((u["physiology"], u["dose"]), ({"resting_hr": 72}, {"per_day": 50, "days": 4}))
        u2 = L.understand(TEXTS[1])
        self.assertEqual(u2["author"], "therapist")
        self.assertEqual(u2["nodes"][0]["name"], "Phoenix")
        self.assertEqual(u2["nodes"][0]["state"], "safe")
        self.assertEqual(L.understand(TEXTS[3])["nodes"][0]["state"], "calm confidence")

    def test_conversation_fills_a_plan(self):
        st = None
        for m in CONVERSATIONS[0]:
            r = L.converse(st, m)
            st = r["state"]
        self.assertTrue(r["done"])
        n = st["intake"]["nodes"][0]
        self.assertEqual((n["archetype"], n["V"], n["A"], n["O"]), ("LION", "Golden light", "The sound of waves", "Cedar"))
        self.assertEqual(n["contexts"], ["At work", "In meetings"])
        p = nodes.plan(st["intake"])
        compile_rsx(p["nodes"][0]["program"])     # the conversation's plan compiles

    def test_frame_suggestions_score_higher(self):
        for t, m in FRAMES:
            base = nodes.frame_check(t, m)["score"]
            for s in L.suggest_frames(t, m):
                self.assertGreaterEqual(s["score"], base, t)
                self.assertNotIn("negation", nodes.frame_check(s["text"], m)["flags"])
        self.assertEqual(L.suggest_frames("I will not be afraid")[0]["text"], "I am calm and I breathe fully")
        self.assertEqual(L.suggest_frames("I am good at seeing things")[0]["text"], "I see broadly and clearly")

    def test_router_contains_model_output(self):
        ctx, *_ = fixtures()
        r = L.route(PROPOSALS[0], ctx["intake"])
        reasons = {x["path"]: x["reason"] for x in r["rejected"]}
        self.assertIn("LINX may only propose", reasons["run_now"])
        self.assertIn("nodes.0.start", reasons)
        self.assertIn("nodes.0.frames.1", reasons)        # "I will never fail": fails the frame check
        self.assertIn("nodes.2.ref", reasons)
        self.assertIn("nodes.3.archetype", reasons)
        self.assertIn("unsafe", reasons["nodes.3.frames.0"])
        self.assertIn("triggers.1", reasons)
        self.assertNotIn("triggers", reasons)
        lion = r["intake"]["nodes"][0]
        self.assertEqual(lion["A"], "Low drum")
        self.assertIn("I breathe fully and see the whole room", lion["frames"])
        self.assertEqual(r["intake"]["nodes"][2]["archetype"], "RAVEN")
        self.assertEqual(r["intake"]["notes_for_therapist"], ["Check the trauma history before observer work"])
        self.assertEqual(L.route(PROPOSALS[1], {})["applied"], [])

    def test_offer_picks_the_node_and_respects_limits(self):
        ctx, plan, runs, events = fixtures()
        self.assertEqual(L.offer(events[1], plan, runs, {}, 1000)["name"], "Lion")
        self.assertEqual(L.offer(events[2], plan, runs, {}, 1000)["name"], "Observer")
        self.assertIsNone(L.offer(events[0], plan, runs, {"last_start": 950}, 1000)["node"])
        self.assertIsNone(L.offer(events[0], plan, runs, {"starts": [1000 - 60 * k for k in range(6)]}, 1000)["node"])
        self.assertIsNone(L.offer(events[0], dict(plan, approved=False), runs, {}, 1000)["node"])
        self.assertIn("lowered your distress", L.offer(events[0], plan, runs, {}, 1000)["reason"])

    def test_prompt_injects_the_state(self):
        ctx, *_ = fixtures()
        p = L.model_prompt(ctx)
        self.assertIn("Node 0 Lion (associated)", p)
        self.assertIn("node_lion: 5 rated, mean change in distress -4.2", p)
        self.assertIn(L.SCHEMA, p)

    @unittest.skipUnless(NODE, "node not installed")
    def test_python_and_javascript_identical(self):
        ctx, plan, runs, events = fixtures()
        gov = {"starts": [10, 20]}
        lists = ["golden light, the sound of waves, cedar", "mint; a warm hand and blue sky", "x"]
        res = subprocess.run([NODE, str(HERE / "js_linx.js")], capture_output=True, text=True, check=True,
                             input=json.dumps(dict(texts=TEXTS, conversations=CONVERSATIONS, frames=FRAMES, ctx=ctx, proposals=PROPOSALS,
                                                   events=events, plan=plan, runs=runs, gov=gov, now=5000, senseLists=lists)))
        js = json.loads(res.stdout)
        self.assertEqual(js["understand"], [L.understand(t) for t in TEXTS])
        for k, msgs in enumerate(CONVERSATIONS):
            st = None
            for j, m in enumerate(msgs):
                r = L.converse(st, m)
                st = r["state"]
                self.assertEqual(r, js["conversations"][k][j], (k, j))
        self.assertEqual(js["frames"], [L.suggest_frames(t, m) for t, m in FRAMES])
        self.assertEqual(js["prompt"], L.model_prompt(ctx))
        self.assertEqual(js["routes"], [L.route(p, ctx["intake"]) for p in PROPOSALS])
        self.assertEqual(js["offers"], [L.offer(e, plan, runs, gov, 5000) for e in events])
        self.assertEqual(js["senses"], [L.senses_from_list(x) for x in lists])


if __name__ == "__main__":
    unittest.main()
