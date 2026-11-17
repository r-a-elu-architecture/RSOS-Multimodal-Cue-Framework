"""spec/PERSONLAB.md §2: the identity-profile schema."""
import copy
import pathlib
import re
import unittest

from rsxv.personlab import schema as S

ROOT = pathlib.Path(__file__).resolve().parents[2]


class Schema(unittest.TestCase):
    def test_example_is_valid(self):
        self.assertEqual(S.validate(S.example()), [])

    def test_sources_point_at_the_text(self):
        p = S.example()
        st = p["levels"]["identity"]["statements"][0]
        a, b = st["source"]["span"]
        self.assertGreater(b, a)

    def test_problems_are_caught(self):
        base = S.example()
        cases = [
            (lambda p: p.pop("licence"), "missing licence"),
            (lambda p: p["levels"].__setitem__("dreams", {"statements": []}), "unknown level dreams"),
            (lambda p: p["levels"]["identity"]["statements"][0].pop("source"), "identity/i1: missing source"),
            (lambda p: p["levels"]["identity"]["statements"][0].__setitem__("text", " "), "identity/i1: empty statement"),
            (lambda p: p["desired"]["skills"][0].__setitem__("node", "zz"), "desired/skills: points at missing node zz"),
            (lambda p: p["levels"]["environment"]["statements"][0]["details"][0].__setitem__("kind", "why"),
             "environment/e1: unknown detail kind why"),
            (lambda p: p["levels"]["behaviour"]["statements"].append(copy.deepcopy(p["levels"]["behaviour"]["statements"][0])),
             "behaviour: duplicate statement id b1"),
        ]
        for change, problem in cases:
            p = copy.deepcopy(base)
            change(p)
            self.assertIn(problem, S.validate(p))

    def test_levels_match_the_copilot(self):
        js = (ROOT / "docs" / "js" / "copilot.js").read_text(encoding="utf-8")
        block = js[js.index('"QUESTION": {'):]
        block = block[:block.index("}")]
        self.assertEqual(re.findall(r'"(\w+)":', block)[1:], S.LEVEL_IDS)

    def test_tree_view(self):
        t = S.to_tree(S.example())
        self.assertEqual([c["level"] for c in t["children"]], S.LEVEL_IDS)
        env = t["children"][0]
        self.assertEqual([d["kind"] for d in env["children"][0]["children"]], ["where", "when"])
        self.assertEqual(t["children"][2]["desired"], ["Plans rest into the week"])


if __name__ == "__main__":
    unittest.main()
