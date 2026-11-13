import copy
import json
import pathlib
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent)]
from rsso import atlas as A  # noqa: E402
from rsso import gate as G  # noqa: E402
from rsso import peak as P  # noqa: E402

NODE = shutil.which("node")


def world(seed=1, days=14, phases=True, spread=0.5):
    s = A.SimWorld(seed)
    a = s.atlas()
    s.sample(a, days)
    if phases:
        s.sample(a, days, phase="map2", t0=20 * 86400, scale=[0.85] * s.n)
        k = int(A.choose_node(a)[1:])
        s.sample(a, days, phase="after", t0=40 * 86400, scale=[0.72 * (0.2 if i == k else (1 - 0.8 * spread) if s.w[i] > 0 else 1) for i in range(s.n)])
    rng = P.Rng(seed)
    for h in A.HIGHER:
        for _ in range(3):
            A.add_sweep(a, 0, h["id"], -(2 - 0.6 * abs(h["rank"] - 3) + rng.gauss() * 0.5))
    for w in range(4):
        A.add_route_walk(a, w * 86400, 0, 6, [{"pos": k, "ok": rng.u() < 0.4 + 0.15 * w, "ms": int(900 + rng.u() * 900)} for k in range(6)])
    return a


class Map(unittest.TestCase):
    def test_finds_known_triggers(self):
        d = A.sim_demo(3, 21)
        W = A.weights(d["atlas"])
        for i, w in enumerate(d["truth"]):
            if w > 2.5:
                self.assertEqual(W["n" + str(i)]["verdict"], "trigger", i)
        self.assertEqual(A.combos(d["atlas"])[0]["verdict"], "only_together")
        self.assertEqual(A.predict(d["atlas"])["verdict"], "predicts")

    def test_inputs_checked(self):
        a = A.make_atlas("x")
        A.add_node(a, "door", "The door slam", "sound")
        with self.assertRaises(ValueError):
            A.add_node(a, "door", "Again", "sound")
        with self.assertRaises(ValueError):
            A.add_node(a, "y", "Y", "colour")
        with self.assertRaises(ValueError):
            A.add_combo(a, "c", ["door"])
        with self.assertRaises(ValueError):
            A.expose(a, 0, [], 1, 2, "later")
        self.assertEqual(A.weights(a)["door"]["verdict"], "too_few")
        self.assertEqual(A.predict(a)["verdict"], "too_few")

    def test_readiness(self):
        a = A.sim_demo(4, 2)["atlas"]
        r = A.readiness(a)
        self.assertEqual(r["nodes"], 12)
        self.assertLessEqual(len(r["next"]), 5)


class Engine(unittest.TestCase):
    def test_transfer_controlled(self):
        a = world(2, 14)
        t = A.transfer(a, A.choose_node(a))
        self.assertTrue(t["controlled"])
        self.assertIn(t["verdict"], ("spreads", "unclear", "stays", "no_change"))
        self.assertLess(t["treated_change"], 0)

    def test_uncontrolled_is_marked(self):
        a = world(2, 14)
        a["exposures"] = [e for e in a["exposures"] if e["phase"] != "map2"]
        self.assertIn("habituation", A.transfer(a, A.choose_node(a))["say"])

    def test_sweep_and_route(self):
        a = world(5, 7, phases=False)
        rep = A.sweep_report(a)
        self.assertEqual(rep["dims"]["abstraction"]["top"], "identity")
        self.assertIsNotNone(rep["abstraction_minus_scope"])
        self.assertEqual(len(A.route_report(a)["walks"]), 4)
        self.assertEqual(A.glyph_route(list("abcdefgh"), 2, 3), ["c", "d", "e"])

    def test_reroute_through_gate(self):
        a = A.sim_demo(3, 21)["atlas"]
        top = A.choose_node(a)
        an = P.scenario("strong", 3)["anchor"]
        self.assertEqual(A.reroute(a, [top], [], threshold=0)["action"], "none")
        r = A.reroute(a, [top], [an], threshold=0)
        self.assertIn(r["action"], ("suggest", "none"))
        offs = []
        for k in range(14):
            G.record_offer(offs, an["id"], 10**6 + k, "helped")
        cons = []
        G.give_consent(cons, "automatic_firing", "p", 0)
        self.assertEqual(A.reroute(a, [top], [an], offs, 10**7, {}, {}, cons, threshold=0)["action"], "fire")
        self.assertEqual(A.reroute(a, ["n11"], [an], offs, 10**7, {}, {}, cons, threshold=99)["action"], "none")


class Simulation(unittest.TestCase):
    def test_results_file_is_current(self):
        self.assertEqual((HERE.parent / "results" / "atlas.md").read_text(encoding="utf-8"), A.report(A.evaluate()))


@unittest.skipUnless(NODE, "node not installed")
class Parity(unittest.TestCase):
    def test_python_and_javascript_identical(self):
        atl = [world(1, 7), world(6, 14, spread=0.0), world(9, 3, phases=False), A.make_atlas("empty")]
        an = P.scenario("strong", 3)["anchor"]
        offs = []
        for k in range(14):
            G.record_offer(offs, an["id"], 10**6 + k, "helped" if k % 5 else "not_needed")
        cons = []
        G.give_consent(cons, "automatic_firing", "p", 0)
        present = ["n0", "n1", "n2", "n3"]
        glyphs = [str(i) for i in range(20)]
        inp = {"atlases": copy.deepcopy(atl), "present": present, "anchors": [an], "offers": offs, "now": 10**7, "history": {}, "consents": cons, "glyphs": glyphs}
        js = json.loads(subprocess.run([NODE, str(HERE / "js_atlas.js")], input=json.dumps(inp), capture_output=True, text=True, check=True).stdout)
        py = {"atlases": [{"weights": A.weights(a), "w2": A.weights(a, "map2"), "combos": A.combos(a), "edges": A.edges(a), "readiness": A.readiness(a),
                           "predict": A.predict(a), "choose": A.choose_node(a), "transfer": A.transfer(a, A.choose_node(a) or "n0"),
                           "sweep": A.sweep_report(a), "route": A.route_report(a),
                           "reroute": A.reroute(a, present, [an], offs, 10**7, {}, {}, cons)} for a in atl],
              "demo": A.sim_demo(11, 5), "route": A.glyph_route(glyphs, 3, 5)}
        for k in py:
            self.assertEqual(json.loads(json.dumps(py[k])), js[k], k)


if __name__ == "__main__":
    unittest.main()
