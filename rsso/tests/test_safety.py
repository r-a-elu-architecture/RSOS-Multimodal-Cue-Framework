"""S1 (spec/CONTAIN.md §9): one safety layer for agents and people; Python and JavaScript identical."""
import json
import pathlib
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parents[1] / "rsx")]
from rsso import safety as S, contain as C, linx as L  # noqa: E402

NODE = shutil.which("node")

EVENTS = [{}, {"self_harm_signal": True}, {"arrangements_for_after": True}, {"hopelessness": True},
          {"hopelessness": True, "arrangements_for_after": True}, {"substances": True}, {"sedative_prescribed": True},
          {"substances": True, "sedative_prescribed": True}, {"job_loss": True}, {"housing_risk": True},
          {"no_income": True}, {"intensity_mechanism": "temperature_extreme"}, {"distress": 7}, {"distress": 6.5},
          {"sleep_h": 3.5}, {"sleep_h": 4}, {"history_reference": True},
          {"history_reference": True, "self_harm_signal": True}, {"history_reference": True, "distress": 8},
          {"job_loss": True, "distress": 9, "substances": True, "sedative_prescribed": True}, {"distress": None, "sleep_h": None}]
SEQUENCES = [
    [["observe", {"distress": 8}, 1], ["observe", {"job_loss": True}, 2], ["observe", {"distress": 9}, 3],
     ["exit", "person", 4], ["observe", {"self_harm_signal": True}, 5], ["exit", "person", 6], ["exit", "clinician", 7]],
    [["enter", "person", 1], ["enter", "person", 2], ["exit", "agent", 3], ["exit", "person", 4], ["exit", "person", 5]],
    [["observe", {"history_reference": True}, 1], ["observe", {"arrangements_for_after": True}, 2],
     ["observe", {"distress": 2}, 3], ["exit", "owner", 4]],
]
ACTIONS = [{"kind": "run", "protocol": "override"}, {"kind": "run", "protocol": "paced_breathing"},
           {"kind": "run", "protocol": "interrupt_only"}, {"kind": "offer", "protocol": "node_lion", "trigger": "device"},
           {"kind": "plan"}, {"kind": "run", "protocol": "tier406_release", "therapist_led": True},
           {"kind": "cue", "category": "crisis_response"}, {"kind": "run", "protocol": "tier016_stillness", "deep": True}]
SPINE_BAD = ["Sit in an ice bath until the feeling breaks", "Take a cold plunge to reset", "Make the shower as hot as you can",
             "Pinch yourself hard until it hurts", "Snap a rubber band on your wrist", "Hold your breath until you almost faint",
             "Hold the breath for 3 min", "Stay awake all night to break the loop", "Go without sleep for a day",
             "You are in the top 1% of minds", "Only 4 in 8 billion people can do this", "You are one in a million",
             "Your score is in the 99th percentile", "You are better than most people at this"]
SPINE_OK = ["A warm bath with soft music", "Golden light fills every cell", "I breathe slowly and calmly",
            "White light heals the whole country", "I sleep well and wake rested", "Warmth in the belly",
            "I move, I act", "I own", "Nothing binds", "Only observed", "A comfortable warm shower",
            "I see broadly and all", "Strength and calm together", "Hold the breath gently at the top for a moment",
            "Cool water on the face", "The lion stands in the sun", "I am at ease wherever I am",
            "Light flows down from above", "Three futures: driving, work, my goal", "Rest after work"]
CHECKS = [{}, {"clinical_result": "high"}, {"clinical_result": "moderate"}, {"clinical_result": "low"},
          {"clinical_result": "none", "intensity": 3}, {"flags": ["medication"]}, {"flags": ["practical"]},
          {"history": True}, {"intensity": "7", "sleep_h": "5"}, {"intensity": 3, "sleep_h": 3.5},
          {"clinical_result": "other", "intensity": ""}, {"flags": ["medication", "practical"], "clinical_result": "high"}]
DEEP = [[100, None, None, 0, "self_chosen"], [100, None, None, 1, "self_chosen"], [100, None, None, 0, "none"],
        [100, {"end_h": 80, "intensity": "intense"}, None, 1, "clinician_agreed"],
        [100, {"end_h": 40, "intensity": "intense"}, {"sleep_ok": True, "functioning_ok": True, "distress_at_baseline": True}, 1, "clinician_agreed"],
        [100, {"end_h": 40, "intensity": "intense"}, {"sleep_ok": True}, 1, "clinician_agreed"]]
RECORDS = [{"treated": True, "med_state": "on", "outcome": 3}, {"treated": False, "med_state": "on", "outcome": 1},
           {"treated": True, "med_state": "off", "outcome": 4}, {"treated": True, "outcome": 2},
           {"treated": False, "med_state": "off", "outcome": 2}, {"treated": False, "outcome": 1}]


def states():
    out = {}
    for m in S.MODES:
        st = S.new_state()
        st["mode"] = m
        out[m] = st
    return out


class TestRules(unittest.TestCase):
    def test_screens(self):
        self.assertEqual(S.screen({"arrangements_for_after": True}), ["possible_crisis"])       # §11.14 fix
        self.assertEqual(S.screen({"hopelessness": True}), [])
        self.assertEqual(S.screen({"history_reference": True}), ["history_check_in"])
        self.assertEqual(S.screen({"history_reference": True, "self_harm_signal": True}), ["possible_crisis"])
        self.assertEqual(S.screen({"substances": True}), [])
        self.assertEqual(S.screen({"distress": 7}), ["unstable"])
        for h in S.RESPONSES:
            self.assertIn(h, S.MESSAGES)

    def test_a4_modes_block_what_section_3_1_forbids(self):
        st = states()
        for m, allowed in S.MODE_ALLOWED.items():
            for a in ACTIONS:
                self.assertEqual(S.allowed(st[m], a)["ok"], S.category(a) in allowed)
        self.assertFalse(S.allowed(st["CRISIS"], {"kind": "run", "protocol": "paced_breathing"})["ok"])
        self.assertTrue(S.allowed(st["STABILISE"], {"kind": "run", "protocol": "paced_breathing"})["ok"])
        self.assertFalse(S.allowed(st["STABILISE"], {"kind": "run", "protocol": "override"})["ok"])
        self.assertFalse(S.allowed(st["NORMAL"], {"kind": "run"})["reason"])

    def test_a4_no_downgrade_and_crisis_exit(self):
        st, r = S.observe(None, {"self_harm_signal": True}, 1)
        self.assertEqual(st["mode"], "CRISIS")
        st, r = S.observe(st, {"distress": 8}, 2)
        self.assertEqual(st["mode"], "CRISIS")                     # never downgrades on a lower screen
        st, r = S.exit(st, "person", 3)
        self.assertFalse(r["ok"])
        self.assertEqual(r["why"], "crisis_exit_needs_clinician_or_owner")
        st, r = S.exit(st, "clinician", 4)
        self.assertTrue(r["ok"])
        self.assertEqual(st["mode"], "NORMAL")
        st, r = S.observe(st, {"history_reference": True}, 5)
        self.assertEqual((st["mode"], r["transition"]), ("NORMAL", None))

    def test_a8_clinical_result(self):
        for res, mode in (("high", "CRISIS"), ("moderate", "STABILISE"), ("low", "NORMAL"), ("none", "NORMAL")):
            st, r = S.observe(None, S.event_from_check({"clinical_result": res}))
            self.assertEqual(st["mode"], mode, res)
        self.assertEqual(S.MODE_NAME["CRISIS"], "Clinician-led protocol")

    def test_a7_no_crisis_wording_in_texts(self):
        import re
        bad = re.compile(r"crisis|suicid|self-harm|harming yourself|helpline|emergency services|not wanting to live", re.I)
        texts = list(S.MESSAGES.values()) + list(S.MODE_TEXT.values()) + list(S.MODE_NAME.values()) + list(S.LEVELS.values()) \
            + [q["text"] for q in S.SELF_CHECK] + list(S.CLINICAL_FLAGS.values()) + [S.FOOTER]
        for t in texts:
            self.assertIsNone(bad.search(t), t)

    def test_a5_spine_flags(self):
        for t in SPINE_BAD:
            self.assertTrue(S.spine_flags(t), t)
        for t in SPINE_OK:
            self.assertEqual(S.spine_flags(t), [], t)

    def test_contain_asks_the_mode(self):
        cst = C.new_state()
        a = {"kind": "run", "protocol": "override"}
        self.assertEqual(C.decide(a, cst), C.decide(a, cst, safety=None))        # A3: unchanged without a state
        self.assertEqual(C.decide(a, cst, safety=S.new_state())["decision"], "allow")
        crisis, _ = S.observe(None, {"arrangements_for_after": True})
        d = C.decide(a, cst, safety=crisis)
        self.assertEqual(d["decision"], "block")
        self.assertIn("Clinician-led protocol", d["reasons"][-1])

    def test_linx_rejects_spine_wording(self):
        p = {"schema": L.SCHEMA, "triggers": ["Take a cold plunge to reset", "the smell of smoke"]}
        r = L.route(p, {})
        self.assertEqual(r["intake"].get("triggers"), ["the smell of smoke"])
        self.assertTrue(any(x["reason"].startswith("Spine:") for x in r["rejected"]))

    def test_agents_share_the_rule_set(self):
        sys.path.insert(0, str(HERE.parents[1] / "rsxv"))
        from rsxv import agents as ag, safety as xs
        self.assertIs(ag.MODE_ALLOWED, S.MODE_ALLOWED)
        self.assertIs(xs.screen, S.screen)


@unittest.skipUnless(NODE, "node not installed")
class TestParity(unittest.TestCase):
    def test_a1_python_and_javascript_identical(self):
        st = states()
        allowed_cases = [[st[m], a] for m in S.MODES for a in ACTIONS]
        crisis, _ = S.observe(None, {"self_harm_signal": True}, 1)
        stab, _ = S.observe(None, {"distress": 9}, 1)
        cst = C.new_state()
        decisions = [[a, cst, None, 0, sf] for a in ACTIONS for sf in (None, S.new_state(), crisis, stab)]
        routes = [[{"schema": L.SCHEMA, "triggers": [t]}, {}] for t in SPINE_BAD[:5] + SPINE_OK[:5]]
        inp = {"events": EVENTS, "sequences": SEQUENCES, "actions": ACTIONS, "allowed": allowed_cases,
               "checks": CHECKS, "texts": SPINE_BAD + SPINE_OK, "deep": DEEP, "records": RECORDS,
               "decisions": decisions, "routes": routes}
        js = json.loads(subprocess.run([NODE, str(HERE / "js_safety.js")], input=json.dumps(inp), capture_output=True,
                                       text=True, check=True).stdout)

        def seq(steps):
            s_, r_ = S.new_state(), []
            for op, arg, t in steps:
                if op == "observe":
                    s_, res = S.observe(s_, arg, t)
                elif op == "exit":
                    s_, res = S.exit(s_, arg, t)
                else:
                    s_, res = S.enter_stabilise(s_, arg, t)
                r_.append([s_, res])
            return r_

        py = {"screen": [S.screen(e) for e in EVENTS], "sequences": [seq(q) for q in SEQUENCES],
              "category": [S.category(a) for a in ACTIONS], "allowed": [S.allowed(s_, a) for s_, a in allowed_cases],
              "check": [S.event_from_check(a) for a in CHECKS], "spine": [S.spine_flags(t) for t in SPINE_BAD + SPINE_OK],
              "deep": [S.may_start_deep_session(*a) for a in DEEP], "adjusted": S.adjusted_effect(RECORDS),
              "decide": [C.decide(a, s_, tl, n, sf) for a, s_, tl, n, sf in decisions],
              "route": [L.route(p, i) for p, i in routes]}
        py = json.loads(json.dumps(py))
        for k in py:
            self.assertEqual(py[k], js[k], k)


if __name__ == "__main__":
    unittest.main()


class TestSiteWording(unittest.TestCase):
    """A7 (spec/CONTAIN.md §10): no crisis, helpline or emergency-banner wording in the visible text of any page."""

    def test_a7_pages(self):
        import html
        import re
        bad = re.compile(r"crisis|suicid|self-harm|harming yourself|helpline|emergency services|not wanting to live|at risk of harm", re.I)
        hits = []
        for f in sorted((HERE.parents[1] / "docs").glob("*.html")):
            t = f.read_text(encoding="utf-8")
            t = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", t)
            t = html.unescape(re.sub(r"<[^>]+>", " ", t))
            hits += [f"{f.name}: {m.group(0)}" for m in bad.finditer(t)]
        self.assertEqual(hits, [])
