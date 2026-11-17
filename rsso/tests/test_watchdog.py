"""WATCHDOG (spec/WATCHDOG.md): the RSIA Watchdog on the person side."""
import copy
import json
import pathlib
import random
import re
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE.parent)]
from rsso import contain as C, safety as S, watchdog as W  # noqa: E402

NODE = shutil.which("node")
VIRTUES = {"makoto", "rei", "jin", "gi", "yu", "meiyo", "chugi", "p3", "p15"}


def _safety(mode):
    st = S.new_state()
    if mode == "STABILISE":
        st, _ = S.enter_stabilise(st, "person", 1)
    elif mode == "CRISIS":
        st, _ = S.observe(st, S.event_from_check({"clinical_result": "high"}), 1)
    elif mode == "PRACTICAL_CRISIS":
        st, _ = S.observe(st, {"job_loss": True}, 1)
    return st


def _contain(kind):
    st = C.new_state()
    if kind == "paused":
        st["escalation"] = {"active": True, "reasons": ["a serious adverse event in 30 days"]}
    elif kind == "quarantine":
        st["quarantine"]["node_lion"] = {"since": 1, "reason": "distress after runs is higher", "signals": ["worse"], "therapist": False}
    return st


def grid(n=2500, seed=7):
    rng = random.Random(seed)
    pick = rng.choice
    out = []
    for _ in range(n):
        a = {"kind": pick(["run", "offer", "plan", "session", "cue", "run", "stop"]),
             "protocol": pick([None, "override", "paced_breathing", "node_lion", "tier414_release", "tier016_stillness", "interrupt_only"]),
             "trigger": pick(["self", "self", "device", "agent"]), "source": pick(["person", "person", "practitioner", "agent"])}
        if rng.random() < 0.3:
            a["auto"] = True
            a["signals"] = pick([[], ["hr"], ["hr", "context"], ["hr", "eeg", "context"]])
        if rng.random() < 0.2:
            a["therapist_led"] = True
        if rng.random() < 0.1:
            a["deep"] = True
        if rng.random() < 0.1:
            a["programmed"] = True
        if rng.random() < 0.15:
            a["justified_by"] = pick(["cm1", "atlas", "person"])
        if rng.random() < 0.08:
            a["text"] = pick(["hold your breath until you faint", "take an ice bath", "breathe slowly"])
        c = {"now": 1000, "safety": _safety(pick(["NORMAL", "NORMAL", "STABILISE", "PRACTICAL_CRISIS", "CRISIS"])),
             "contain": _contain(pick(["new", "new", "paused", "quarantine"])),
             "max_level": pick([None, "structured", "clinician_led"]),
             "clinician_present": rng.random() < 0.4, "screening_recorded": rng.random() < 0.5,
             "consents": pick([[], [{"scope": "automatic_firing", "given": 10, "withdrawn": None}],
                               [{"scope": "automatic_firing", "given": 10, "withdrawn": 500}]]),
             "plan_protocols": pick([None, ["override", "paced_breathing", "node_lion"]])}
        out.append([a, c])
    return out


CASES = grid()


class Watchdog(unittest.TestCase):
    def test_w2_never_weaker(self):
        for a, c in CASES:
            if a["kind"] == "stop":
                continue
            ca = dict(a, therapist_present=bool(c["clinician_present"]))
            if C.decide(ca, c["contain"], None, c["now"], c["safety"])["decision"] == "block":
                self.assertEqual(W.watch(a, c)["decision"], "hold", (a, c["safety"]["mode"]))

    def test_w3_stop_and_regulation(self):
        for a, c in CASES:
            r = W.watch(dict(a, kind="stop"), c)
            self.assertEqual(r["decision"], "allow")
            if S.regulating(a) and W.level(a) != "clinician_led":      # FIXES_R1 W-7: unedited and not clinician-led
                own = [x for x in W.watch(a, c)["reasons"] if x["rule"] in ("level", "clinician", "plan")]
                self.assertEqual(own, [], a)

    def test_w4_guidance(self):
        a = {"kind": "plan", "therapist_led": True}
        base = {"safety": S.new_state(), "contain": C.new_state()}
        self.assertEqual(W.watch(a, dict(base, max_level="structured", clinician_present=True, screening_recorded=True))["decision"], "hold")
        self.assertEqual(W.watch(a, dict(base, max_level="structured", clinician_present=True, screening_recorded=True))["resolve"], "none")
        r = W.watch(a, dict(base, max_level="clinician_led"))
        self.assertEqual((r["decision"], r["resolve"]), ("hold", "clinician"))
        self.assertEqual(W.watch(a, dict(base, max_level="clinician_led", clinician_present=True))["decision"], "hold")
        self.assertEqual(W.watch(a, dict(base, max_level="clinician_led", clinician_present=True, screening_recorded=True))["decision"], "allow")
        self.assertEqual(W.level({"kind": "run", "protocol": "tier439_x"}), "clinician_led")
        self.assertEqual(W.level({"kind": "run", "protocol": "tier016_stillness"}), "self_guided")
        self.assertEqual(W.level({"kind": "run", "trigger": "device"}), "structured")
        for a, c in CASES:
            r = W.watch(a, c)
            if r["level"] == "clinician_led" and a["kind"] != "stop":
                if c["max_level"] == "structured" or not (c["clinician_present"] and c["screening_recorded"]):
                    self.assertEqual(r["decision"], "hold")

    def test_w5_agents_and_devices(self):
        for a, c in CASES:
            r = W.watch(a, c)
            if a["kind"] == "stop":
                continue
            if a.get("source") == "agent" or a.get("trigger") == "agent":
                self.assertNotEqual(r["decision"], "allow", a)
            if a.get("trigger") == "device" and r["decision"] == "allow":
                consent = any(x["scope"] == "automatic_firing" and x["given"] <= 1000 and (x["withdrawn"] is None or x["withdrawn"] > 1000) for x in c["consents"])
                self.assertTrue(a.get("auto") and consent and len(a.get("signals", [])) >= 2, a)
        ok = W.watch({"kind": "offer", "protocol": "override", "trigger": "device", "source": "person", "auto": True, "signals": ["hr", "context"]},
                     {"consents": [{"scope": "automatic_firing", "given": 0, "withdrawn": None}], "now": 5})
        self.assertEqual(ok["decision"], "allow")

    def test_w6_reasons_named(self):
        for a, c in CASES:
            r = W.watch(a, c)
            if r["decision"] != "allow":
                self.assertTrue(r["reasons"])
                self.assertIn(r["resolve"], ("person", "clinician", "safety_page", "none"))
                for x in r["reasons"]:
                    self.assertIn(x["virtue"], VIRTUES)
                    self.assertTrue(x["text"])

    def test_w7_audit(self):
        self.assertEqual(W.sha256("abc"), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")  # FIPS 180-2 test vector
        log = []
        for k, (a, c) in enumerate(CASES[:300]):
            W.record(log, a, W.watch(a, c), 1700000000000 + k)
        self.assertTrue(W.verify(log))
        edited = copy.deepcopy(log)
        edited[100]["decision"] = "allow" if edited[100]["decision"] != "allow" else "hold"
        self.assertFalse(W.verify(edited))
        self.assertFalse(W.verify(log[:50] + log[51:]))
        self.assertFalse(W.verify(log[:10] + [log[11], log[10]] + log[12:]))
        self.assertTrue(W.verify(W.trim(log * 1)[-120:]))

    def test_w8_link(self):
        st, changed = W.link(_contain("paused"), S.new_state(), 5)
        self.assertTrue(changed)
        self.assertEqual(st["mode"], "STABILISE")
        self.assertEqual(st["history"][-1]["by"], "contain")
        for m in ("STABILISE", "PRACTICAL_CRISIS", "CRISIS"):
            st, changed = W.link(_contain("paused"), _safety(m), 5)
            self.assertEqual(st["mode"], m)
            self.assertFalse(changed)
        st, changed = W.link(_contain("new"), _safety("CRISIS"), 5)
        self.assertEqual(st["mode"], "CRISIS")

    def test_no_profiles_import(self):
        self.assertNotRegex((ROOT / "rsso" / "rsso" / "watchdog.py").read_text(encoding="utf-8"), r"(?m)^\s*(?:from|import)\s[^\n]*profiles")
        self.assertNotIn("RSOSProfiles", (ROOT / "docs" / "js" / "watchdog.js").read_text(encoding="utf-8"))


@unittest.skipUnless(NODE, "node not installed")
class Parity(unittest.TestCase):
    """W1: Python and JavaScript identical; W7: hashes agree."""

    def test_w1(self):
        links = [[_contain(k), _safety(m), 9] for k in ("new", "paused") for m in ("NORMAL", "STABILISE", "CRISIS")]
        texts = ["", "abc", "RSOS — état, Zustand, состояние 🦁", "x" * 1000]
        r = subprocess.run([NODE, str(HERE / "js_watchdog.js")], input=json.dumps({"cases": CASES, "links": links, "texts": texts}),
                           capture_output=True, text=True, check=True)
        js = json.loads(r.stdout)
        self.assertEqual(js["level"], [W.level(a) for a, _ in CASES])
        for k, (a, c) in enumerate(CASES):
            self.assertEqual(js["watch"][k], W.watch(a, c), k)
        self.assertEqual(js["link"], [list(W.link(*x)) for x in links])
        self.assertEqual(js["sha"], [W.sha256(t) for t in texts])
        log = []
        for k, (a, c) in enumerate(CASES[:300]):
            W.record(log, a, W.watch(a, c), 1700000000000 + k)
        self.assertEqual(js["log"], log)
        self.assertTrue(js["verify"])


class Pages(unittest.TestCase):
    """W9 (static part): no page calls CONTAIN's decide directly; the four pages ask the Watchdog."""

    def test_w9_static(self):
        for f in sorted((ROOT / "docs").glob("*.html")):
            self.assertNotRegex(f.read_text(encoding="utf-8"), r"(?:RSOSContain|\bK)\.decide\(", f.name)
        for n in ("player", "device", "nodes", "therapist"):
            t = (ROOT / "docs" / f"{n}.html").read_text(encoding="utf-8")
            self.assertIn("RSOSGuard.ask(", t, n)
            self.assertLess(t.index("js/watchdog.js"), t.index("js/guard.js"), n)


if __name__ == "__main__":
    unittest.main()
