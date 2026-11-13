import json
import pathlib
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent)]
from rsso import machines as M  # noqa: E402

NODE = shutil.which("node")


class Channels(unittest.TestCase):
    def test_lines_and_envelope(self):
        c = {"kind": "haptic", "t": 0, "on": 100, "off": 100, "count": 3, "amp": 0.4, "carrier_hz": 170, "mod_hz": 12, "site": "chest"}
        self.assertEqual(M.parse(M.encode(c)), c)
        self.assertEqual(M.check(c), [])
        self.assertIn("carrier outside 20-300 Hz", M.check(dict(c, carrier_hz=500)))
        self.assertIn("temperature change above 4 °C", M.check({"kind": "thermal", "t": 0, "dur": 1000, "delta_c": -6}))
        self.assertIn("too bright for the night", M.check({"kind": "display", "t": 0, "dur": 3000, "image": "lion"}, night=True, brightness=0.8))
        with self.assertRaises(ValueError):
            M.parse("X 1 2")
        self.assertTrue(M.CLASSES["implant"]["spec_only"])

    def test_spread_and_posture(self):
        sp = M.spread("..- ---", ["wrist_left", "chest"])
        self.assertEqual([p["site"] for p in sp], ["wrist_left"] * 3 + ["chest"] * 3)
        with self.assertRaises(ValueError):
            M.spread(".", ["nose"])
        self.assertAlmostEqual(M.tilt(0, 9.81, 0), 0, places=6)
        self.assertAlmostEqual(M.tilt(0, 0, 9.81), 90, places=6)
        angles, truth = M.sim_posture(3)
        self.assertEqual(len(M.posture(angles)["episodes"]), 3)


class Agents(unittest.TestCase):
    def test_values_gate_actions(self):
        a = M.agent_from(M.EXAMPLE_AGENT)
        self.assertEqual(M.act(a, {"id": "knife", "tags": ["sharp_near_person"]})["decision"], "override")
        self.assertEqual(M.act(a, {"id": "wipe", "tags": ["tidy", "slow"]}, 10)["decision"], "allow")
        self.assertEqual(M.alignment(a)["by"], {"allow": 1, "ask": 0, "override": 1})

    def test_human_signal_teaches(self):
        a = M.agent_from(M.EXAMPLE_AGENT)
        M.act(a, {"id": "blend", "tags": ["loud"]}, 0)
        self.assertIsNotNone(M.human_signal(a, 3))
        self.assertEqual(M.check_action(a, {"id": "blend2", "tags": ["loud"]})["decision"], "ask")
        self.assertIsNone(M.human_signal(a, 100))
        f1, f2, asks = M.sim_feedback(5)
        self.assertLess(f2, f1)

    def test_glyph_channel(self):
        for c in M.AGENT_STATES.values():
            self.assertEqual(M.decode_pulses(M.code_pulses(c)), c)
        self.assertEqual(M.person_reply(" --- ")["reply"], "stop")
        self.assertFalse(M.person_reply("..-")["understood"])

    def test_packs(self):
        for p in M.PACKS:
            self.assertEqual(M.pack_issues(p), [])
            for m in M.pack_matrices(p):
                self.assertEqual(len(m["branches"]), 3)
        with self.assertRaises(ValueError):
            M.make_pack("x", "x", "c", [])


class Simulation(unittest.TestCase):
    def test_results_file_is_current(self):
        self.assertEqual((HERE.parent / "results" / "machines.md").read_text(encoding="utf-8"), M.report(M.evaluate()))


@unittest.skipUnless(NODE, "node not installed")
class Parity(unittest.TestCase):
    def test_python_and_javascript_identical(self):
        cmds = [{"kind": "thermal", "t": 0, "dur": 5000, "delta_c": -2.5}, {"kind": "thermal", "t": 10, "dur": 200000, "delta_c": 5},
                {"kind": "display", "t": 0, "dur": 3000, "image": "lion_peak"}, {"kind": "haptic", "t": 5, "on": 300, "off": 100, "count": 2, "amp": 0.75, "carrier_hz": 12, "mod_hz": 50, "site": "nose"},
                {"kind": "haptic", "t": 5, "on": 100, "off": 100, "count": 3, "amp": 0.333, "carrier_hz": 170, "mod_hz": 8, "site": "ankle"}]
        vecs = [[0, 9.81, 0], [0, 7, 7], [3, 9, 1.5], [0, 0, 0], [0, -9.8, 0.1]]
        actions = [{"id": "a" + str(k), "tags": t} for k, t in enumerate([["tidy"], ["loud", "tidy"], ["sharp_near_person"], ["loud"], ["ask", "tidy"], ["loud"], ["hide_error", "report"],
                                                                          ["loud", "slow"], ["tidy"], ["announce"]])]
        rules = [{"id": "r" + str(k), "rule": "Rule number " + str(k) + " with a long name", "words": ["w" + str(k)], "response": "do " + str(k), "code": ".-"[k % 2] * (k + 1)} for k in range(4)]
        inp = {"cmds": cmds, "vecs": vecs, "actions": actions, "rules": rules}
        js = json.loads(subprocess.run([NODE, str(HERE / "js_machines.js")], input=json.dumps(inp), capture_output=True, text=True, check=True).stdout)
        agent = M.agent_from(M.EXAMPLE_AGENT)
        out = []
        for k, a in enumerate(actions):
            r = M.act(agent, a, k * 30)
            out.append(r)
            if r["decision"] == "ask":
                M.answer(agent, a, k % 2 == 0)
            if k % 3 == 1:
                M.human_signal(agent, k * 30 + 3)
        angles, _ = M.sim_posture(5)
        py = {"lines": [[M.encode(c), M.check(c, True, 0.5), M.parse(M.encode(c))] for c in cmds], "spread": M.spread("..- ---", ["wrist_left", "chest"]),
              "tilts": [M.r1(M.tilt(*v)) for v in vecs], "posture": M.posture(angles), "agent": [out, agent, M.alignment(agent)],
              "signals": [M.agent_signal(s) for s in M.AGENT_STATES], "replies": [M.person_reply(c) for c in (".", "-", " ---", "..-")],
              "decode": [M.decode_pulses(M.code_pulses(c)) for c in M.AGENT_STATES.values()], "packs": [[M.pack_matrices(p), M.pack_issues(p)] for p in M.PACKS],
              "made": M.make_pack("x", "X", "c", rules)}
        for k in py:
            self.assertEqual(json.loads(json.dumps(py[k])), js[k], k)


if __name__ == "__main__":
    unittest.main()
