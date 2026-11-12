import json
import pathlib
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parents[1] / "rsx"), str(HERE)]
from rsso import nodes, thera as T  # noqa: E402
from rsx import compile_rsx  # noqa: E402

NODE = shutil.which("node")
ROOT = HERE.parents[1]


def plan_of(nodes_list, triggers=("Raised voices",)):
    it = dict(concerns=["ptsd", "stress"], triggers=list(triggers), nodes=nodes_list)
    p = nodes.plan(it)
    p.update(intake=it, approved=True)
    return p


FULL = plan_of([dict(archetype="LION", contexts=["At work", "In meetings"]), dict(archetype="OBSERVER")])
LION = plan_of([dict(archetype="LION")], triggers=())
CASES = [["stress", FULL], ["boundaries", LION], ["habits", FULL], ["low_mood", LION], ["trauma_observer", FULL], ["trauma_observer", LION], ["stress", None]]
EVENTS = [
    [0, [["open", {"sud": 7, "agency": 3, "done": True}, 1000], ["breath", {"sud": 5, "done": True}, 1200], ["anchor", {"sud": 4, "agency": 6, "done": True}, 1600],
         ["close", {"sud": 3, "agency": 7, "cgi_s": 4, "cgi_i": 2, "engagement": 8, "adverse": "none", "done": True}, 3000]]],
    [3, [["open", {"sud": 6, "done": True}, 1000], ["screen", {"screen": "yes"}, 1060]]],
    [4, [["open", {"sud": 5, "done": True}, 1000], ["observe", {"sud": 8.5}, 1900]]],
    [1, [["close", {"adverse": "moderate", "done": True}, 2000]]],
]
RUNS = [dict(timestamp=1100, protocol="paced_breathing"), dict(timestamp=1500, protocol="node_lion"), dict(timestamp=1550, protocol="node_lion"),
        dict(timestamp=9000, protocol="node_lion")]


def run_events(k, evs):
    s = T.session_plan(*CASES[k])
    for step, vals, at in evs:
        s = T.record(s, step, vals, at)
    return s


class Thera(unittest.TestCase):
    def test_data_file_is_current(self):
        self.assertEqual(json.loads((ROOT / "docs" / "data" / "thera.json").read_text(encoding="utf-8")), json.loads(json.dumps(T.export())))

    def test_session_uses_the_clients_nodes(self):
        s = T.session_plan("trauma_observer", FULL)
        prog = {st["id"]: st.get("program") for st in s["steps"]}
        self.assertEqual((prog["breath"], prog["observe"], prog["return"]), ("paced_breathing", "plan:1", "plan:0"))
        self.assertTrue(s["therapist_led"])
        self.assertEqual(s["problems"], [])
        self.assertIn("observer node", T.session_plan("trauma_observer", LION)["problems"][0])
        self.assertIn("raised voices", next(st for st in T.session_plan("stress", FULL)["steps"] if st["id"] == "test")["say"])
        for pid in T.PROTOCOLS:    # every protocol opens with a check-in and closes with an adverse-event question
            ids = [st["id"] for st in T.PROTOCOLS[pid]["steps"]]
            self.assertEqual((ids[0], ids[-1]), ("open", "close"))
            if T.PROTOCOLS[pid].get("screen"):
                self.assertIn("screen", ids)
        for i, n in enumerate(FULL["nodes"]):
            compile_rsx(n["program"])

    def test_stop_rules_and_summary(self):
        s = run_events(*EVENTS[0])
        sm = T.summary(s, RUNS)
        self.assertEqual((sm["sud_start"], sm["sud_end"], sm["sud_change"], sm["agency_change"]), (7, 3, -4, 4))
        self.assertEqual(sm["runs"], 3)
        self.assertEqual(sm["nodes_used"], 1)
        self.assertEqual(sm["record"]["cgi_i"], 2)
        self.assertEqual(sm["fidelity"], 5.7)          # 4 of 7 required steps done
        self.assertEqual(T.check(run_events(*EVENTS[1]))[0]["level"], "stop")
        self.assertEqual(T.check(run_events(*EVENTS[2]))[0]["level"], "return")
        self.assertEqual(T.check(run_events(*EVENTS[0]))[0]["level"], "ok")

    def test_homework(self):
        hw = T.homework(FULL, T.session_plan("trauma_observer", FULL))
        self.assertIn("..-", hw[0])
        self.assertIn("therapist-led work stays in sessions", hw[1])

    @unittest.skipUnless(NODE, "node not installed")
    def test_python_and_javascript_identical(self):
        inp = dict(protocols=T.PROTOCOLS, cases=CASES, events=EVENTS, runs=RUNS, started=1000, ended=3000)
        js = json.loads(subprocess.run([NODE, str(HERE / "js_thera.js")], input=json.dumps(inp), capture_output=True, text=True, check=True).stdout)
        norm = lambda x: json.loads(json.dumps(x))
        self.assertEqual(js["plans"], norm([T.session_plan(*c) for c in CASES]))
        sessions = [run_events(*e) for e in EVENTS]
        self.assertEqual(js["checks"], norm([T.check(s) for s in sessions]))
        self.assertEqual(js["summaries"], norm([T.summary(s, RUNS, 1000, 3000) for s in sessions]))
        self.assertEqual(js["homework"], norm([T.homework(c[1], T.session_plan(*c)) for c in CASES]))


if __name__ == "__main__":
    unittest.main()
