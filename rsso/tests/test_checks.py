import json
import pathlib
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent)]
from rsso import checks as C  # noqa: E402

NODE = shutil.which("node")


class Tasks(unittest.TestCase):
    def test_nback(self):
        seq = C.gen_nback(5)
        self.assertEqual(len(seq), 24)
        self.assertEqual(sum(s["target"] for s in seq), 8)
        perfect = C.score_nback(seq, [{"i": s["i"], "rt": 600} for s in seq if s["target"]])
        self.assertEqual(perfect["hits"], 8)
        self.assertEqual(perfect["false_alarms"], 0)
        self.assertGreater(perfect["d_prime"], 2.5)
        chance = C.score_nback(seq, [{"i": s["i"]} for s in seq])
        self.assertLess(abs(chance["d_prime"]), 0.6)
        self.assertAlmostEqual(C.zq(0.975), 1.96, places=2)

    def test_span(self):
        tr = []
        for L, ok in ((3, 1), (3, 1), (4, 1), (4, 0), (5, 0), (5, 0)):
            self.assertEqual(C.next_span(tr), L)
            tr.append({"length": L, "correct": ok})
        self.assertIsNone(C.next_span(tr))
        self.assertEqual(C.score_span(tr)["span"], 4)
        d = C.gen_digits(3, 9)
        self.assertEqual(len(d), 9)
        self.assertTrue(all(d[k] != d[k + 1] for k in range(8)))

    def test_reaction_recall_reading_dotprobe(self):
        r = C.score_reaction([120, 250, 260, 300, 700, 280, None])
        self.assertEqual((r["anticipations"], r["lapses"], r["median"]), (1, 1, 280))
        w = C.gen_words(1)
        rec = C.score_recall(w, ", ".join(w[:5]) + " banana " + w[0])
        self.assertEqual((rec["correct"], rec["intrusions"], rec["repeats"]), (5, 1, 1))
        rd = C.score_reading("bees", 60000, [0, 1, 0])
        self.assertEqual(rd["correct"], 2)
        self.assertEqual(rd["wpm"], C.word_count(C.passage("bees")["text"]))
        t = C.gen_dotprobe(4)
        self.assertEqual(sum(x["congruent"] for x in t), 16)
        resp = [{"k": x["k"], "side": x["probe_side"], "rt": 450 if x["congruent"] else 490} for x in t]
        self.assertEqual(C.score_dotprobe(t, resp)["bias"], 40)
        self.assertTrue(all(len(p["questions"]) == 3 for p in C.PASSAGES))


@unittest.skipUnless(NODE, "node not installed")
class Parity(unittest.TestCase):
    def test_python_and_javascript_identical(self):
        nb = []
        for seed in (1, 5, 99):
            q = C.gen_nback(seed)
            nb.append([seed, [{"i": s["i"], "rt": 500 + s["i"] * 7} for s in q if s["target"] or s["i"] % 5 == 0]])
        span = [[{"length": 3, "correct": 1}, {"length": 3, "correct": 0}], [{"length": 5, "correct": 0}, {"length": 5, "correct": 0}], []]
        reaction = [[[120, 250.5, 260, 300, 700, 280], 1], [[310, 290], 0], [[], 0], [[401], 2]]
        w = C.gen_words(7)
        recall = [[w, " ".join(w[:4]) + " zebra " + w[1].upper()], [w, ""], [w, "anchor-basket; candle!"]]
        reading = [["bees", 48000, [0, 1, 1]], ["tides", 0, [1, 0, None]], ["lighthouse", 93500, [1, 1, 0]]]
        dot = []
        for seed in (2, 8):
            t = C.gen_dotprobe(seed)
            dot.append([seed, [{"k": x["k"], "side": x["probe_side"] if x["k"] % 7 else "up", "rt": 300 + (x["k"] * 37) % 900} for x in t]])
        z = [0.001, 0.02, 0.3, 0.5, 0.77, 0.99, 0.9995]
        inp = {"nback": nb, "digits": [[1, 5], [2, 9]], "span": span, "reaction": reaction, "words": [1, 7], "recall": recall,
               "reading": reading, "dot": dot, "z": z}
        js = json.loads(subprocess.run([NODE, str(HERE / "js_checks.js")], input=json.dumps(inp), capture_output=True, text=True, check=True).stdout)
        py = {"nback": [{"seq": C.gen_nback(s), "score": C.score_nback(C.gen_nback(s), p)} for s, p in nb],
              "digits": [C.gen_digits(s, n) for s, n in [[1, 5], [2, 9]]],
              "span": [[C.score_span(t), C.next_span(t)] for t in span],
              "reaction": [C.score_reaction(r, m) for r, m in reaction], "delays": C.gen_delays(9),
              "words": [C.gen_words(s) for s in (1, 7)], "recall": [C.score_recall(a, b) for a, b in recall],
              "reading": [C.score_reading(*x) for x in reading],
              "dot": [{"trials": C.gen_dotprobe(s), "score": C.score_dotprobe(C.gen_dotprobe(s), r)} for s, r in dot],
              "z": [round(C.zq(p), 12) for p in z]}
        js["z"] = [round(v, 12) for v in js["z"]]
        for k in py:
            self.assertEqual(json.loads(json.dumps(py[k])), js[k], k)


if __name__ == "__main__":
    unittest.main()
