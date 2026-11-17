"""FIXES_R1 (spec/FIXES_R1.md): each test reproduces a finding of the first independent review (review/interim, 2b2cc3c)."""
import json
import pathlib
import re
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE.parent), str(HERE)]
from rsso import contain as C, profiles as P, safety as S, watchdog as W  # noqa: E402
from test_profiles import CORPUS  # noqa: E402

NODE = shutil.which("node")


def mode(m):
    st = S.new_state()
    if m == "STABILISE":
        st, _ = S.enter_stabilise(st, "person", 1)
    elif m == "CRISIS":
        st, _ = S.observe(st, S.event_from_check({"clinical_result": "high"}), 1)
    return st


ALLOWED = [
    [mode("CRISIS"), {"kind": "run", "protocol": "override", "category": "logging"}],                 # S-4a person
    [mode("CRISIS"), {"kind": "log", "category": "logging", "source": "agent"}],                      # S-4a agent keeps it
    [mode("STABILISE"), {"kind": "run", "protocol": "paced_breathing", "edited": True}],             # S-4b renamed override
    [mode("STABILISE"), {"kind": "run", "protocol": "paced_breathing"}],
    [mode("STABILISE"), {"kind": "run", "protocol": "tier012_breath_anchor"}],                        # S-3
    [{}, {"kind": "run", "protocol": "override"}],                                                    # W-10
    [{"mode": "nonsense"}, {"kind": "run", "protocol": "override"}],
]
WATCH = [
    [{"kind": "run", "protocol": "paced_breathing", "therapist_led": True, "source": "person"}, {"max_level": "structured"}],     # W-7
    [{"kind": "run", "protocol": "tier414_x", "source": "person"}, {"max_level": "bogus", "clinician_present": True, "screening_recorded": True}],  # W-8
    [{"kind": "session", "protocol": "session_low_mood", "source": "practitioner"}, {"max_level": "structured", "clinician_present": True, "screening_recorded": True}],  # W-9
    [{"kind": "run", "protocol": "override", "source": "person"}, {"safety": {}, "contain": {}}],                                # W-10
    [{"kind": "offer", "protocol": "override", "trigger": "device", "source": "person", "auto": True, "signals": ["hr", "hr"]},
     {"consents": [{"scope": "automatic_firing", "given": None, "withdrawn": None}], "now": 5}],                                  # W-10, W-11
    [{"kind": "plan", "protocol": "plan", "memory_work": True, "source": "person"}, {"memory_work_allowed": False}],            # P-2
    [{"kind": "plan", "protocol": "plan", "memory_work": True, "source": "person"}, {}],
]
TEXT = [[t, p] for t in ("Observer work with trauma memories is therapist-led", "therapist-led tiers need a therapist present",
                         "A memory, observed (therapist-led)", "Distress (SUD)", "Book two therapy sessions", "an anxiety disorder",
                         "Symptoms and what they feel like", "It supports clinical judgement; it does not diagnose or treat.")
        for p in P.IDS]
MAX = [[p, on] for p in P.IDS for on in (False, True)]


class Engine(unittest.TestCase):
    def test_s3_regulating_list(self):
        self.assertEqual(S.REGULATING, ("paced_breathing", "interrupt_only", "tier016_stillness"))
        self.assertFalse(S.allowed(mode("STABILISE"), {"kind": "run", "protocol": "tier012_breath_anchor"})["ok"])

    def test_s4_category_and_edited(self):
        self.assertFalse(S.allowed(*ALLOWED[0])["ok"])            # a person cannot claim "logging"
        self.assertTrue(S.allowed(*ALLOWED[1])["ok"])             # an agent's own category still counts
        self.assertFalse(S.allowed(*ALLOWED[2])["ok"])            # an edited program named paced_breathing is not regulating
        self.assertTrue(S.allowed(*ALLOWED[3])["ok"])
        self.assertFalse(W.watch({"kind": "run", "protocol": "paced_breathing", "edited": True, "source": "person"},
                                 {"safety": mode("STABILISE")})["decision"] == "allow")

    def test_w1_trimmed_log_verifies(self):
        log = []
        for k in range(1200):
            W.record(log, {"kind": "run"}, {"decision": "allow", "level": "self_guided", "reasons": []}, 1000 + k)
            log = W.trim(log)
        self.assertTrue(W.verify(log))
        self.assertEqual((log[0]["n"], len(log)), (700, 500))

    def test_w7_w8_w9_p2(self):
        r = [W.watch(a, c) for a, c in WATCH]
        self.assertEqual(r[0]["decision"], "hold")                 # clinician-led "paced_breathing" not exempt
        self.assertEqual(r[1]["decision"], "hold")                 # unknown max_level -> structured
        self.assertEqual(W.level(WATCH[2][0]), "clinician_led")
        self.assertEqual(r[2]["decision"], "hold")
        self.assertEqual(r[3]["decision"], "allow")                # empty saved states count as none
        self.assertEqual(r[4]["decision"], "ask")                  # one distinct signal
        self.assertEqual([x["rule"] for x in r[4]["reasons"]], ["p3"])
        self.assertEqual((r[5]["decision"], r[5]["reasons"][0]["rule"]), ("hold", "memory"))
        self.assertNotEqual(r[6]["decision"], "hold")

    def test_p1_clinician_led_wording(self):
        led = re.compile(r"\b(?:coach|teacher|facilitator|investigator|practitioner|guide)s?-led\b", re.I)
        bad = [(p, P.text(s, p)) for p in P.IDS for s in CORPUS + [t for t, _ in TEXT] if led.search(P.text(s, p))]
        self.assertEqual(bad, [])
        self.assertEqual(P.text("therapist-led tiers need a therapist present", "performance"), "clinician-led tiers need a clinician present")

    def test_p4_grammar(self):
        words = ("an? [a-z]+", )
        bad = []
        for p in P.IDS:
            for s in CORPUS + [t for t, _ in TEXT]:
                t = P.text(s, p)
                if t == s:
                    continue
                if re.search(r"\b(\w+) \1\b", t, re.I) and not re.search(r"\b(\w+) \1\b", s, re.I):
                    bad.append((p, "doubled", t))
                for m in re.finditer(r"\b(a|an) ([a-z])", t, re.I):
                    vowel = m.group(2).lower() in "aeiou"
                    if (m.group(1).lower() == "a") == vowel and not re.search(re.escape(m.group(0)), s, re.I):
                        bad.append((p, "article", t))
                for term in {P.term(k, p) for k in P.TERMS}:
                    if term and re.search(re.escape(term) + r"\W+\(?" + re.escape(term), t, re.I):
                        bad.append((p, "repeated term", t))
        self.assertEqual(bad, [])

    def test_w2_research_level(self):
        self.assertEqual(P.max_level("research"), "structured")
        self.assertEqual(P.max_level("research", True), "clinician_led")
        self.assertEqual(P.max_level("clinical"), "clinician_led")
        self.assertEqual(P.max_level("workplace", True), "structured")


@unittest.skipUnless(NODE, "node not installed")
class Parity(unittest.TestCase):
    """R2: Python and JavaScript identical for every changed function."""

    def test_r2(self):
        r = subprocess.run([NODE, str(HERE / "js_fixes_r1.js")], input=json.dumps({"allowed": ALLOWED, "watch": WATCH, "text": TEXT, "max": MAX}),
                           capture_output=True, text=True, check=True)
        js = json.loads(r.stdout)
        self.assertEqual(js["allowed"], [S.allowed(st, a) for st, a in ALLOWED])
        self.assertEqual(js["watch"], [W.watch(a, c) for a, c in WATCH])
        self.assertEqual(js["text"], [P.text(t, p) for t, p in TEXT])
        self.assertEqual(js["max"], [P.max_level(p, on) for p, on in MAX])
        self.assertEqual(js["trimmed"], {"verify": True, "n0": 700, "len": 500})


if __name__ == "__main__":
    unittest.main()
