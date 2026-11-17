"""spec/ARCH_REFRESH.md B2: the architecture map covers RSX-V and what Steps 1 to 4 built, in neutral wording."""
import pathlib
import importlib.util
import re
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]
ARCH = REPO / "architecture"
_spec = importlib.util.spec_from_file_location("test_roadmap", REPO / "rsx/tests/test_roadmap.py")
_rm = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_rm)
read = lambda p: (ARCH / p / "README.md").read_text(encoding="utf-8")


class ArchRefresh(unittest.TestCase):
    def test_rsxv_page_links_its_documents(self):
        page = read("rsx/rsx-v")
        for doc in ("rsxv/README.md", "rsxv/SPEC.md", "rsxv/AGENTS.md", "rsxv/RESULTS.md"):
            self.assertIn(doc, page)
        self.assertIn("rsx-v/", read(""))
        self.assertIn("rsx-v/", read("rsx"))

    def test_watchdog_contain_micro_current(self):
        self.assertIn("spec/WATCHDOG.md", read("rsia/watchdog"))
        contain = read("rsso/subsystems/CONTAIN")
        for s in ("Standard", "Stabilisation", "Paused: practical", "Clinician-led protocol", "outlet.js"):
            self.assertIn(s, contain)
        self.assertIn("spec/BLE_PAIRING.md", read("rsso/subsystems/MICRO"))

    def test_neutral_wording(self):
        bad = re.compile(r"crisis help|hotline|\b112\b", re.I)   # plus the repository's excluded terms
        hits = [str(p.relative_to(ARCH)) for p in ARCH.rglob("README.md")
                if bad.search(p.read_text(encoding="utf-8")) or any(re.search(t, p.read_text(encoding="utf-8"), 0 if t == r"\bFox\b" else re.I) for t in _rm.EXCLUDED)]
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
