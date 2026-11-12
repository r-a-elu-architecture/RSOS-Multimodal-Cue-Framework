import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from rsx import compile_rsx, RSXError  # noqa: E402

PROTOCOLS = pathlib.Path(__file__).resolve().parents[1] / "protocols"


class OverrideProtocol(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = compile_rsx((PROTOCOLS / "override.rsx").read_text(encoding="utf-8"))

    def test_phase_order_matches_spec(self):
        names = [p["name"] for p in self.t["phases"]]
        self.assertEqual(names, ["interrupt", "ignite", "radiate", "anchor", "future", "future", "future",
                                 "extend", "fill", "return", "install"])

    def test_breath_alternates_after_interrupt(self):
        breaths = [p["breath"] for p in self.t["phases"][1:]]
        self.assertEqual(breaths, ["inhale", "exhale", "inhale", "exhale", "exhale", "exhale",
                                   "inhale", "exhale", "inhale", "exhale"])

    def test_three_futures_in_order(self):
        sees = [e["text"] for e in self.t["events"] if e["phase"] == "future" and e["kind"] == "see"]
        self.assertEqual(sees, ["Talking with people", "Walking with confidence", "Working at the computer"])

    def test_first_and_last_words(self):
        says = [e["text"] for e in self.t["events"] if e["kind"] == "say"]
        self.assertEqual(says, ["I move, I act", "I own"])

    def test_vib_and_fp_anchors(self):
        h = [e for e in self.t["events"] if e["channel"] == "haptic"]
        self.assertEqual((h[0]["on"], h[0]["off"], h[0]["count"]), (300, 300, 6))
        fp = [e for e in h if e["phase"] == "future"]
        self.assertEqual(len(fp), 3)
        self.assertTrue(all((e["on"], e["count"]) == (150, 8) for e in fp))
        self.assertTrue(all(e["amp"] <= self.t["safety"]["haptic_max"] for e in h))

    def test_lion_tier_fires_all_channels_together(self):
        cues = [e for e in self.t["events"] if e["kind"] == "cue"]
        self.assertEqual({e["channel"] for e in cues}, {"visual", "auditory", "kinesthetic"})
        self.assertEqual(len({e["t"] for e in cues}), 1)

    def test_timeline_is_contiguous(self):
        end = 0
        for p in self.t["phases"]:
            self.assertEqual(p["t"], end); end = p["t"] + p["dur"]
        self.assertEqual(end, self.t["duration_ms"])
        self.assertTrue(all(0 <= e["t"] <= self.t["duration_ms"] for e in self.t["events"]))


class LanguageRules(unittest.TestCase):
    def err(self, src):
        with self.assertRaises(RSXError) as cm:
            compile_rsx(src)
        return str(cm.exception)

    def test_requires_protocol(self):
        self.assertIn("missing PROTOCOL", self.err('PHASE a {\nSAY "x"\n}'))

    def test_haptic_cannot_exceed_safety(self):
        self.assertIn("exceeds SAFETY haptic_max", self.err('PROTOCOL p\nPHASE a {\nHAPTIC amp=0.9\n}'))

    def test_tier_needs_vak(self):
        self.assertIn("missing K", self.err('PROTOCOL p\nTIER 1 X {\nV "a"\nA "b"\n}'))

    def test_unknown_tier(self):
        self.assertIn("unknown tier NOPE", self.err('PROTOCOL p\nPHASE a {\nACTIVATE NOPE\n}'))

    def test_future_outside_loop(self):
        self.assertIn("$future used outside", self.err('PROTOCOL p\nPHASE a {\nSEE "$future"\n}'))

    def test_unclosed_block_reports_opener_line(self):
        self.assertEqual(self.err('PROTOCOL p\n\nPHASE a {\nSAY "x"'), "line 3: missing closing }")

    def test_comments_and_semicolons(self):
        t = compile_rsx('PROTOCOL p # id\nPHASE a { \n SAY "a # not a comment"; SAY "b"\n}')
        self.assertEqual([e["text"] for e in t["events"]], ["a # not a comment", "b"])

    def test_wait_offsets_later_steps(self):
        t = compile_rsx('PROTOCOL p\nPHASE a {\nSEE "x"\nWAIT 600ms\nSEE "y"\n}')
        self.assertEqual([e["t"] for e in t["events"]], [0, 600])

    def test_repeat(self):
        t = compile_rsx('PROTOCOL p\nREPEAT 3 {\nPHASE a dur=1s {\nMARK "m"\n}\n}')
        self.assertEqual([p["t"] for p in t["phases"]], [0, 1000, 2000])

    def test_legacy_vector_command(self):
        t = compile_rsx((PROTOCOLS / "legacy_vector.rsx").read_text(encoding="utf-8"))
        kinds = {(e["channel"], e["kind"]) for e in t["events"]}
        self.assertIn(("breath", "inhale"), kinds)
        self.assertIn(("device", "output"), kinds)
        self.assertEqual(len(t["warnings"]), 10)   # 17 vectors, 7 with a runtime effect


if __name__ == "__main__":
    unittest.main()
