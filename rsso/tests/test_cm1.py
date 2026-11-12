import json
import pathlib
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE)]
from rsso import cm1 as C, nodes  # noqa: E402

NODE = shutil.which("node")
ROOT = HERE.parents[1]
GLYPHS = [g["char"] for g in json.loads((ROOT / "docs" / "ugcl" / "originals.json").read_text(encoding="utf-8"))["glyphs"]]


def plans():
    it = dict(concerns=["stress"], nodes=[dict(archetype="LION"), dict(archetype="OBSERVER"), dict(name="Wolf mother of the north", glyph="🔥", tacton="..- ---")])
    p = nodes.plan(it)
    return [[p, None], [p, {"quarantine": {"node_observer": {}}, "escalation": {"active": True}}], [{"nodes": []}, None]]


class CM1(unittest.TestCase):
    def test_recovers_known_profiles(self):
        ev = C.evaluate(C.synthetic_population())
        self.assertEqual(ev["assigned_right_first"], ev["test"])          # clear profiles: all from 10 runs
        hard = C.evaluate(C.synthetic_population(hard=True))
        self.assertGreaterEqual(hard["assigned_right_first"] / hard["test"], 0.85)
        self.assertGreaterEqual(hard["best_kind_right_first"] / hard["with_clear_best"], 0.85)
        self.assertEqual(sorted(ev["labels"].values()), sorted(C.TRUE_PROFILES))

    def test_signature_shrinks_small_samples(self):
        one = C.signature([dict(protocol="node_lion", sud_before=8, sud_after=2, completed=1)])
        self.assertEqual(one["v"][0], 1.5)      # a drop of 6 from one run counts as 6 / (1 + 3)
        self.assertEqual(one["n"][0], 1)
        self.assertEqual(C.signature([])["v"][-1], 0.9)

    def test_patterns_find_the_strong_ones(self):
        rows = [r for p in C.synthetic_population() for r in p["runs"]]
        pats = C.patterns(rows)
        top = {(p["feature"], p["value"]) for p in pats[:6]}
        self.assertIn(("kind", "associated"), top)
        self.assertTrue(all(p["low"] <= p["mean_drop"] <= p["high"] for p in pats))

    def test_bundle_round_trip(self):
        for p, st in plans():
            b = C.pack(p, GLYPHS, st)
            u = C.unpack(b, GLYPHS)
            self.assertEqual([n["tacton"] for n in u["nodes"]], [n["tacton"] for n in p["nodes"]][:8])
            self.assertLess(u["bytes"], 80)
        u = C.unpack(C.pack(*plans()[1][:1], GLYPHS, plans()[1][1]), GLYPHS)
        self.assertEqual([n["paused"] for n in u["nodes"]], [False, True, False])
        self.assertEqual(u["nodes"][0]["glyph"], "🦁")
        self.assertTrue(u["escalation"])
        bad = bytearray(__import__("base64").b64decode(C.pack(plans()[0][0], GLYPHS)))
        bad[5] ^= 1
        with self.assertRaises(ValueError):
            C.unpack(__import__("base64").b64encode(bytes(bad)).decode(), GLYPHS)

    def test_data_file_is_current(self):
        d = json.loads((ROOT / "docs" / "data" / "cm1.json").read_text(encoding="utf-8"))
        ev = C.evaluate(C.synthetic_population())
        self.assertEqual(d["profiles"], json.loads(json.dumps(ev["profiles"])))

    @unittest.skipUnless(NODE, "node not installed")
    def test_python_and_javascript_identical(self):
        pop = C.synthetic_population(people=12, hard=True)
        people = [p["runs"][:k] for p, k in zip(pop, [0, 1, 3, 5, 8, 10, 12, 15, 20, 25, 30, 30])]
        people.append([dict(protocol="x", completed=True), dict(protocol="tier014_seal", sud_before="7", sud_after="", completed="1")])
        profiles = C.evaluate(C.synthetic_population())["profiles"]
        pl = plans()
        bundles = [C.pack(p, GLYPHS, st) for p, st in pl]
        inp = dict(people=people, profiles=profiles, glyphs=GLYPHS, plans=pl, bundles=bundles)
        js = json.loads(subprocess.run([NODE, str(HERE / "js_cm1.js")], input=json.dumps(inp), capture_output=True, text=True, check=True).stdout)
        norm = lambda x: json.loads(json.dumps(x))
        sigs = [C.signature(p) for p in people]
        self.assertEqual(js["sigs"], norm(sigs))
        self.assertEqual(js["assign"], norm([C.assign(s, profiles) for s in sigs]))
        self.assertEqual(js["suggest"], norm([C.suggest(s, profiles) for s in sigs]))
        self.assertEqual(js["describe"], [C.describe(p["centroid"]) for p in profiles])
        self.assertEqual(js["packs"], bundles)
        self.assertEqual(js["unpacked"], norm([C.unpack(b, GLYPHS) for b in bundles]))


if __name__ == "__main__":
    unittest.main()
