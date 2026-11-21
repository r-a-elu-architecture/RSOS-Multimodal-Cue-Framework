"""spec/STACK1.md: the recorded results are reproduced exactly by a fresh run of the harness (about 5 s).
The test checks reproduction, not that every prediction passed: failed predictions stay on record (section 8)."""
import importlib.util
import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _harness():
    spec = importlib.util.spec_from_file_location("stack1", REPO / "scripts" / "stack1.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class TestStack1(unittest.TestCase):
    def test_results_reproduce(self):
        rec = json.loads((REPO / "spec" / "stack1" / "results.json").read_text(encoding="utf-8"))
        fresh = json.loads(json.dumps(_harness().main(None), ensure_ascii=False))
        self.assertEqual(fresh, rec)

    def test_verdict_as_reported(self):
        v = json.loads((REPO / "spec" / "stack1" / "results.json").read_text(encoding="utf-8"))["verdict"]
        self.assertEqual({k: v[k] for k in ("P1", "P2", "P3", "P4", "P5")},
                         {"P1": True, "P2": False, "P3": True, "P4": True, "P5": False})
        self.assertIn("results reproduce", (REPO / "spec" / "STACK1.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
