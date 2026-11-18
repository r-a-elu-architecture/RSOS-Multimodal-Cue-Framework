"""spec/PERSONLAB.md §5: the builder's deterministic parts, on made-up conversations."""
import unittest

from rsxv.personlab import builder as B
from rsxv.personlab import schema as S


def conv(ty, seeker_turns, initial="4", final="2"):
    d = []
    for i, t in enumerate(seeker_turns):
        d.append({"speaker": "seeker", "content": t, "annotation": {}})
        d.append({"speaker": "supporter", "content": f"reply {i}", "annotation": {}})
    return {"problem_type": ty, "situation": "I lost my job at the factory.", "dialog": d,
            "survey_score": {"seeker": {"initial_emotion_intensity": initial, "final_emotion_intensity": final}}}


class Builder(unittest.TestCase):
    def test_split_holds_out_the_second_half(self):
        text, held = B.split(conv("job crisis", ["a1", "a2", "a3", "a4", "a5"]))
        self.assertIn("PERSON: a3", text)
        self.assertNotIn("a4", text)
        self.assertEqual(held["final_intensity"], "2")
        self.assertEqual([t["content"] for t in held["turns"] if t["speaker"] == "seeker"], ["a4", "a5"])

    def test_sample_skips_flagged_and_missing(self):
        D = [conv("job crisis", ["fine"]) for _ in range(30)] + [conv("job crisis", ["flag"], final="")]
        screen = lambda t: ["possible_crisis"] if t == "flag" else []
        D[0] = conv("job crisis", ["flag"])
        idx, replaced = B.sample(D, screen, per_type=5)
        self.assertEqual(len([i for i in idx if D[i]["problem_type"] == "job crisis"]), 5)
        self.assertNotIn(0, idx)
        self.assertNotIn(30, idx)
        self.assertEqual(B.sample(D, screen, per_type=5), (idx, replaced))      # deterministic

    def test_quotes_become_spans_and_misses_are_dropped(self):
        text = "SITUATION: I lost my job at the factory.\nPERSON: I am the one who pays the rent"
        raw = {"levels": {"identity": {"statements": [{"id": "i1", "text": "I am the provider", "quote": "I am the one who pays the rent"},
                                                       {"id": "i2", "text": "invented", "quote": "not in the text"}]},
                          "environment": {"statements": [{"id": "e1", "text": "I worked at a factory", "quote": "at the factory",
                                                          "details": [{"kind": "where", "text": "factory", "quote": "factory"}]}]},
                          "dreams": {"statements": []}},
               "desired": {"identity": [{"text": "x", "node": "i1", "quote": "nowhere"}]}}
        meta = {"id": "t1", "source_dataset": "test", "licence": "CC BY-NC 4.0", "document_id": "t1", "builder": "test", "created": "2026-11-17"}
        p, dropped = B.to_profile(raw, text, "t1", meta)
        self.assertEqual(S.validate(p), [])
        self.assertEqual(dropped, {"quote_not_found": 2, "unknown_level": 1})
        a, b = p["levels"]["identity"]["statements"][0]["source"]["span"]
        self.assertEqual(text[a:b], "I am the one who pays the rent")

    def test_kappa_and_merge(self):
        self.assertAlmostEqual(B.kappa([True, False, True, False], [True, False, True, False]), 1.0)
        self.assertAlmostEqual(B.kappa([True, True, False, False], [True, False, True, False]), 0.0)
        pa = {"levels": {"identity": {"statements": [{"id": "a", "text": "x", "source": {"doc": "d", "span": [0, 10]}}]}}}
        pb = {"levels": {"identity": {"statements": [{"id": "b", "text": "y", "source": {"doc": "d", "span": [4, 12]}}]}}}
        self.assertTrue(B.merge(pa, pb)["levels"]["identity"]["statements"][0]["agreed"])
        pb["levels"]["identity"]["statements"][0]["source"]["span"] = [9, 20]
        self.assertFalse(B.merge(pa, pb)["levels"]["identity"]["statements"][0]["agreed"])


if __name__ == "__main__":
    unittest.main()
