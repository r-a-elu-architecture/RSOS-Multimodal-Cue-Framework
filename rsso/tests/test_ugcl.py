import json
import math
import pathlib
import random
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent)]
from rsso import calibration as cal, ugcl  # noqa: E402

ROOT = HERE.parents[1]
LIB = json.loads((ROOT / "docs" / "ugcl" / "library.json").read_text())
ORIG = json.loads((ROOT / "docs" / "ugcl" / "originals.json").read_text(encoding="utf-8"))
NODE = shutil.which("node")


def bt_cases():
    rng = random.Random(3); cases = []
    for n in (4, 6, 8):
        comps = [tuple(rng.sample(range(n), 2)) for _ in range(2 * n)]
        scores = cal.bt_fit(n, comps, iters=60)
        cases.append(dict(n=n, comps=comps, scores=scores))
    return cases


class Format(unittest.TestCase):
    def test_library_valid_and_complete(self):
        self.assertEqual(LIB["format"], ugcl.FORMAT)
        ids = [g["id"] for g in LIB["glyphs"]]
        self.assertEqual(len(ids), 48); self.assertEqual(len(set(ids)), 48)
        for g in LIB["glyphs"]:
            ugcl.validate(g)
            self.assertTrue(g["lineage"] and g["lineage"][0]["op"] == "seed")
        self.assertEqual(LIB["archetype_defaults"], {})   # archetype glyphs come from the ledger

    def test_haptic_and_tone_limits(self):
        for g in LIB["glyphs"]:
            h = ugcl.haptic_signature(g)
            self.assertLessEqual(sum(on + off for on, off in h), 2000)
            self.assertEqual(h[-1][1], 0)
            self.assertTrue(all(40 <= on <= 220 for on, _ in h))
            t = ugcl.tone_motif(g)
            self.assertTrue(1 <= len(t) <= 5)

    def test_validate_rejects_bad_glyphs(self):
        bad = [dict(id="", sym=1, strokes=[dict(k="L", p=[0, 0, 1, 1])]),
               dict(id="x", sym=9, strokes=[dict(k="L", p=[0, 0, 1, 1])]),
               dict(id="x", sym=1, strokes=[]),
               dict(id="x", sym=1, strokes=[dict(k="L", p=[0, 0, 2, 1])]),
               dict(id="x", sym=1, strokes=[dict(k="Q", p=[0, 0])])]
        for g in bad:
            with self.assertRaises(ValueError):
                ugcl.validate(g)

    def test_compact_code_round_trip(self):
        sizes = []
        for g in LIB["glyphs"]:
            code = ugcl.encode(g); sizes.append(len(code))
            back = ugcl.decode(code, g["id"])
            self.assertEqual(ugcl.svg(back), ugcl.svg(g))
            self.assertEqual(ugcl.haptic_signature(back), ugcl.haptic_signature(g))
        self.assertLessEqual(max(sizes), 100)   # fits one BLE packet at the default 244-byte MTU, and a URL

    def test_svg_deterministic(self):
        g = LIB["glyphs"][0]
        self.assertEqual(ugcl.svg(g), ugcl.svg(json.loads(json.dumps(g))))
        self.assertTrue(ugcl.svg(g).startswith("<svg"))


class Originals(unittest.TestCase):
    def test_every_ledger_glyph_is_an_original(self):
        from rsso import ugcl_originals as uo
        from rsso.ledger import build
        chars = {g["char"] for g in ORIG["glyphs"]}
        for r in build()["records"]:
            if r["kind"] == "tier":
                for t in uo.tokens(r["fields"].get("glyph", "")) + [x for g in r["glyph_chain"] for x in uo.tokens(g)[:1]]:
                    self.assertIn(t, chars, r["id"])
        self.assertEqual(len(chars), len(ORIG["glyphs"]))
        self.assertEqual(ORIG["glyphs"][0]["char"], "🦁")
        self.assertEqual(ORIG["glyphs"][0]["tiers"][0]["number"], "001")
        self.assertEqual(ORIG["archetype_defaults"]["LION"], "O001")

    def test_valid_with_rhythm_melody_and_ancestry(self):
        for g in ORIG["glyphs"]:
            ugcl.validate(g)
            h = ugcl.haptic_signature(g)
            self.assertLessEqual(sum(on + off for on, off in h), 2000)
            self.assertEqual(h[-1][1], 0)
            self.assertTrue(2 <= len(ugcl.tone_motif(g)) <= 5)
        pairs = {json.dumps([g["haptic"], g["tone"]]) for g in ORIG["glyphs"]}
        self.assertGreaterEqual(len(pairs), 130)
        fire = next(g for g in ORIG["glyphs"] if g["char"] == "🜑")
        self.assertIn("🜒", [c["char"] for c in fire["children"]])     # Tier 406: 🜑 → 🜒

    def test_programs_use_the_original_lion(self):
        for f in ("override.rsx", "tier003_command_stack.rsx", "tier014_seal.rsx", "tier579_glyph.rsx"):
            self.assertIn('GLYPH "🦁"', (ROOT / "rsx" / "protocols" / f).read_text(encoding="utf-8"), f)

    def test_build_is_reproducible(self):
        from rsso import ugcl_originals as uo
        again = uo.build_originals()
        self.assertEqual([(g["char"], g["haptic"], g["tone"]) for g in again["glyphs"]],
                         [(g["char"], g["haptic"], g["tone"]) for g in ORIG["glyphs"]])


class Calibration(unittest.TestCase):
    def test_recovers_true_ranking(self):
        """Simulated people with known preferences: after 2n adaptive choices the top glyph is usually found."""
        hits, taus = 0, []
        for seed in range(20):
            rng = random.Random(seed)
            true = [rng.gauss(0, 1.5) for _ in range(8)]
            scores, comps = cal.simulate_session(true, 16, noise=0.6, seed=seed)
            hits += max(range(8), key=scores.__getitem__) in sorted(range(8), key=true.__getitem__)[-2:]
            conc = sum(1 if (true[i] - true[j]) * (scores[i] - scores[j]) > 0 else -1 for i in range(8) for j in range(i + 1, 8))
            taus.append(conc / 28)
        self.assertGreaterEqual(hits, 16)              # best glyph lands in the true top two in >= 80% of people
        self.assertGreater(sum(taus) / len(taus), 0.5)  # Kendall tau

    def test_adaptive_pairs_do_not_repeat(self):
        _, comps = cal.simulate_session([0, 1, 2, 3, 4, 5], 12, seed=1)
        keys = [tuple(sorted(c)) for c in comps]
        self.assertEqual(len(keys), len(set(keys)))


@unittest.skipUnless(NODE, "node not installed")
class Parity(unittest.TestCase):
    def test_python_and_js_identical(self):
        cases = bt_cases()
        glyphs = LIB["glyphs"] + ORIG["glyphs"]
        out = json.loads(subprocess.run([NODE, str(HERE / "js_ugcl.js")], input=json.dumps(dict(glyphs=glyphs, bt=cases)),
                                        capture_output=True, text=True, check=True).stdout)
        for g, j in zip(glyphs, out["glyphs"]):
            self.assertEqual(ugcl.svg(g, 96), j["svg"], g["id"])
            self.assertEqual(ugcl.svg(g, 40, "#fff", "#000"), j["svg_bg"], g["id"])
            self.assertEqual(ugcl.haptic_signature(g), j["haptic"], g["id"])
            self.assertEqual(ugcl.tone_motif(g), j["tone"], g["id"])
            if g.get("kind") != "original":
                self.assertEqual(ugcl.encode(g), j["code"], g["id"])
                self.assertEqual(ugcl.svg(g, 96), j["back"], g["id"])
        for c, j in zip(cases, out["bt"]):
            for a, b in zip(cal.bt_fit(c["n"], c["comps"], iters=60), j["scores"]):
                self.assertTrue(math.isclose(a, b, abs_tol=1e-9))
            self.assertEqual(list(cal.next_pair(c["n"], c["comps"], c["scores"])), j["next"])


if __name__ == "__main__":
    unittest.main()
