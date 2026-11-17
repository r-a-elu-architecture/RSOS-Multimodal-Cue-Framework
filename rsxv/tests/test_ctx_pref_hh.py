"""spec/CTX_PREF_HH.md: pair splitting and the verdict, on made-up transcripts."""
import unittest

from rsxv import ctx_pref_hh as H


def tr(prompt, reply, earlier=""):
    return f"{earlier}\n\nHuman: {prompt}\n\nAssistant: {reply}"


class Rules(unittest.TestCase):
    def test_split(self):
        self.assertEqual(H.split_pair(tr("I feel stuck", "A"), tr("I feel stuck", "B")), ("I feel stuck", "A", "B"))
        self.assertIsNone(H.split_pair(tr("x", "A"), tr("y", "B")))          # different prefixes
        self.assertIsNone(H.split_pair(tr("x", "A"), tr("x", "A")))          # identical replies
        self.assertIsNone(H.split_pair(tr("x", " "), tr("x", "B")))          # empty reply

    def test_last_human_turn_is_the_prompt(self):
        e = "\n\nHuman: hello\n\nAssistant: hi"
        self.assertEqual(H.split_pair(tr("I'm so stressed", "A", e), tr("I'm so stressed", "B", e))[0], "I'm so stressed")

    def test_analyse_counts_chosen_with_feature(self):
        s = "I'm sorry, that sounds hard. " + "x" * 70
        rows = [("f", tr("I feel overwhelmed", s), tr("I feel overwhelmed", "y" * 100)),   # S chosen, PERSONAL
                ("f", tr("Name a fruit", "y" * 100), tr("Name a fruit", s))]               # S rejected, OTHER
        R = H.analyse(rows)
        self.assertEqual(R["matched"]["S|PERSONAL"]["k"], 1)
        self.assertEqual(R["matched"]["S|OTHER"], {**R["matched"]["S|OTHER"], "k": 0, "n": 1})

    def test_verdict(self):
        cells = {(f, c): {"k": 500, "n": 1000} for f in ("S", "Q") for c in H.CONTEXTS}
        self.assertEqual(H.verdict(cells)["verdict"], "SAME DIRECTION")
        cells[("S", "PERSONAL")] = {"k": 800, "n": 1000}
        cells[("S", "OTHER")] = {"k": 300, "n": 1000}
        self.assertEqual(H.verdict(cells)["verdict"], "CONTEXT-DEPENDENT")
        cells = {(f, c): {"k": 5, "n": 10} for f in ("S", "Q") for c in H.CONTEXTS}
        self.assertEqual(H.verdict(cells)["verdict"], "INCONCLUSIVE")


if __name__ == "__main__":
    unittest.main()
