"""spec/AGENTS_PROVEN.md Q1: the Agents page's data comes from the real code, deterministically and consistently."""
import json
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from rsxv import site_agents as SA  # noqa: E402

FILE = HERE.parent / "docs" / "data" / "agents_proven.json"


class SiteAgents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(FILE.read_text(encoding="utf-8"))

    def test_deterministic_and_current(self):
        self.assertEqual(json.loads(json.dumps(SA.build(), ensure_ascii=False)), self.d)

    def test_trials_consistent(self):
        w = self.d["w1"]
        self.assertEqual(w["n"], 40)
        for t in w["trials"]:
            for arm in ("meta", "local"):
                self.assertEqual(t[arm]["used"], len(t[arm]["repairs"]), (t["seed"], arm))
                self.assertLessEqual(t[arm]["used"], w["budget"])
            self.assertEqual(len(t["faults"]), 2)
        for arm in ("meta", "local"):
            self.assertEqual(w["fixed"][arm]["all"], sum(t[arm]["fixed"] for t in w["trials"]))
            self.assertEqual(w["fixed"][arm]["cross"], sum(t[arm]["fixed"] for t in w["trials"] if t["cross"]))

    def test_policies_and_register(self):
        self.assertEqual([p["policy"] for p in self.d["hswitch"]["policies"]], SA.POLICIES)
        rows = json.loads((HERE.parent / "docs/data/results_register.json").read_text(encoding="utf-8"))["rows"]
        for k, r in self.d["register"].items():
            self.assertIn(r, rows, k)
        self.assertEqual(len(self.d["register"]), 6)


if __name__ == "__main__":
    unittest.main()
