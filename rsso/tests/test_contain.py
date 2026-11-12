import copy
import json
import pathlib
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parents[1] / "rsx"), str(HERE)]
from rsso import contain as C  # noqa: E402
from rsso.devices import standard_rig  # noqa: E402
from rsso.runtime import VirtualClock, play  # noqa: E402
from rsx import compile_rsx  # noqa: E402

NODE = shutil.which("node")
ROOT = HERE.parents[1]
DAY = 86400
NOW = 1_800_000_000


def prog(name):
    return compile_rsx((ROOT / "rsx" / "protocols" / name).read_text(encoding="utf-8"))


def loud():
    return compile_rsx("""PROTOCOL loud
SAFETY max_per_hour=12 max_per_day=40 refractory=30s haptic_max=0.9
PHASE p {
  HAPTIC on=1500ms off=500ms x=5 amp=0.9
  TONE 3000Hz 12s
}
""")


def runs_of(protocol, pairs, start=NOW - 10 * DAY, step=3600, completed=1, agency=None):
    out = []
    for k, (b, a) in enumerate(pairs):
        r = dict(timestamp=start + k * step, protocol=protocol, sud_before=b, sud_after=a, completed=completed)
        if agency:
            r.update(agency_before=agency[k][0], agency_after=agency[k][1])
        out.append(r)
    return out


def cases():
    helping = runs_of("override", [(7, 4)] * 6)
    worsening = runs_of("node_lion", [(5, 4), (5, 4), (4, 6), (4, 5), (5, 6), (4, 5)])
    stopped = [dict(timestamp=NOW - DAY + k * 600, protocol="swish", completed=0 if k < 4 else 1) for k in range(6)]
    falling = runs_of("tier014_seal", [(5, 5)] * 5, agency=[(6, 4)] * 5)
    rising = runs_of("node_observer", [(6, 3)] * 5 + [(6, 5)] * 5)
    high = runs_of("override", [(9, 9), (9, 8), (8, 9), (9, 9), (7, 6)], start=NOW - 2 * DAY)
    adverse = [dict(ts=(NOW - 3 * DAY) * 1000, severity="moderate", related="possible", protocol="tier406_release"),
               dict(ts=(NOW - 2 * DAY) * 1000, severity="moderate", related="likely")]
    serious = [dict(ts=(NOW - 40 * DAY) * 1000, severity="serious", related="unlikely")]
    screens = [dict(ts=(NOW - DAY) * 1000, answer="yes")]
    allruns = helping + worsening + stopped + falling + rising
    return dict(helping=helping, worsening=worsening, stopped=stopped, falling=falling, rising=rising, high=high,
                adverse=adverse, serious=serious, screens=screens, allruns=allruns)


class Contain(unittest.TestCase):
    def test_every_program_inside_the_envelope(self):
        for f in sorted((ROOT / "rsx" / "protocols").glob("*.rsx")):
            self.assertEqual(C.check_envelope(compile_rsx(f.read_text(encoding="utf-8"))), [], f.name)
        rules = {v["rule"] for v in C.check_envelope(loud())}
        self.assertTrue({"max_per_hour", "max_per_day", "refractory_ms_min", "haptic_amp_max", "haptic_pulse_ms_max",
                         "haptic_burst_ms_max", "tone_hz", "tone_ms_max"} <= rules, rules)

    def test_drift_signals(self):
        c = cases()
        self.assertEqual(C.drift(c["helping"], "override")["status"], "ok")
        self.assertEqual(C.drift(c["worsening"], "node_lion")["status"], "drift")
        self.assertEqual(C.drift(c["stopped"], "swish")["status"], "watch")
        self.assertEqual(C.drift(c["falling"], "tier014_seal")["signals"][0]["signal"], "agency falls")
        self.assertEqual([s["signal"] for s in C.drift(c["rising"], "node_observer")["signals"]], ["rising distress"])
        self.assertEqual(C.drift(c["worsening"], "node_lion", since=NOW)["status"], "ok")    # nothing after a release

    def test_escalation(self):
        c = cases()
        self.assertFalse(C.escalation(c["helping"], [], [], NOW)["active"])
        self.assertFalse(C.escalation([], c["serious"], [], NOW)["active"])      # older than 30 days
        self.assertEqual(len(C.escalation(c["high"], c["adverse"], c["screens"], NOW)["reasons"]), 3)

    def test_review_quarantines_and_release_needs_the_right_person(self):
        c = cases()
        st, ch = C.review(None, c["allruns"], c["adverse"], [], NOW)
        self.assertEqual(sorted(st["quarantine"]), ["node_lion", "tier014_seal", "tier406_release"])
        self.assertTrue(st["quarantine"]["tier406_release"]["therapist"])
        self.assertTrue(st["escalation"]["active"])
        d = C.decide({"kind": "run", "protocol": "node_lion", "trigger": "self"}, st, prog("node_lion.rsx"), NOW)
        self.assertEqual(d["decision"], "block")
        self.assertEqual(C.decide({"kind": "run", "protocol": "override", "trigger": "self"}, st, prog("override.rsx"), NOW)["decision"], "allow")
        self.assertEqual(C.decide({"kind": "offer", "protocol": "override"}, st, None, NOW)["decision"], "block")    # escalation
        st2, msg = C.release(st, "node_lion", "person", NOW)
        self.assertIn("therapist", msg)                 # escalation active: the therapist restores
        st3, msg = C.release(st, "node_lion", "therapist", NOW)
        self.assertEqual(msg, "restored")
        st4, _ = C.review(st3, c["allruns"], c["adverse"], [], NOW + 60)
        self.assertNotIn("node_lion", st4["quarantine"])  # old evidence does not re-quarantine after a release
        self.assertEqual(C.decide({"kind": "run", "protocol": "loud"}, None, loud(), NOW)["decision"], "block")

    def test_runtime_refuses_what_contain_blocks(self):
        st, _ = C.review(None, cases()["worsening"], [], [], NOW)
        tr = play(prog("node_lion.rsx"), standard_rig(), VirtualClock(), contain=st)
        self.assertFalse(tr.started)
        self.assertIn("paused by CONTAIN", tr.reason)
        tr = play(loud(), standard_rig(), VirtualClock(), contain=C.new_state())
        self.assertFalse(tr.started)
        self.assertTrue(play(prog("override.rsx"), standard_rig(), VirtualClock(), contain=st).started)

    def test_rollback(self):
        h = [dict(approved=True, v=1), dict(approved=False, v=2), dict(approved=True, v=3)]
        self.assertEqual(C.rollback(h)["v"], 1)
        self.assertIsNone(C.rollback(h[:1]))

    @unittest.skipUnless(NODE, "node not installed")
    def test_python_and_javascript_identical(self):
        c = cases()
        st, _ = C.review(None, c["allruns"], c["adverse"], [], NOW)
        tls = [prog(f.name) for f in sorted((ROOT / "rsx" / "protocols").glob("*.rsx"))] + [loud()]
        drifts = [[c[k], p, None] for k, p in (("helping", "override"), ("worsening", "node_lion"), ("stopped", "swish"),
                                                ("falling", "tier014_seal"), ("rising", "node_observer"))] + [[c["worsening"], "node_lion", NOW]]
        escs = [[c["helping"], [], [], NOW], [c["high"], c["adverse"], c["screens"], NOW], [[], c["serious"], [], NOW]]
        reviews = [[None, c["allruns"], c["adverse"], [], NOW], [st, c["allruns"] + c["high"], c["adverse"], c["screens"], NOW + 5]]
        decs = [[{"kind": "run", "protocol": "node_lion", "trigger": "self"}, st, tls[2], NOW], [{"kind": "offer", "protocol": "override"}, st, None, NOW],
                [{"kind": "run", "protocol": "loud"}, None, loud(), NOW], [{"kind": "plan", "therapist_led": True}, st, None, NOW]]
        rels = [[st, "node_lion", "person", NOW], [st, "node_lion", "therapist", NOW], [st, "nothing", "person", NOW]]
        hist = [dict(approved=True, v=1), dict(approved=True, v=2)]
        inp = dict(timelines=tls, drifts=drifts, escalations=escs, reviews=reviews, decisions=decs, releases=rels, history=hist)
        js = json.loads(subprocess.run([NODE, str(HERE / "js_contain.js")], input=json.dumps(inp), capture_output=True, text=True, check=True).stdout)
        norm = lambda x: json.loads(json.dumps(x))
        self.assertEqual(js["envelope"], norm([C.check_envelope(t) for t in tls]))
        self.assertEqual(js["drift"], norm([C.drift(*d) for d in drifts]))
        self.assertEqual(js["escalation"], norm([C.escalation(*e) for e in escs]))
        self.assertEqual(js["review"], norm([C.review(*r) for r in reviews]))
        self.assertEqual(js["decide"], norm([C.decide(*d) for d in decs]))
        self.assertEqual(js["release"], norm([C.release(*r) for r in rels]))
        self.assertEqual(js["rollback"], norm(C.rollback(hist)))


if __name__ == "__main__":
    unittest.main()
