"""RELEASE_1 A2 F5: public documents carry no crisis, helpline or emergency wording (owner's decision)."""
import pathlib
import re
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]
DOCS = ["README.md", "SECURITY.md", "CONTRIBUTING.md", "REVIEW.md", "releases/NEXT.md", "spec/OVERRIDE_PROTOCOL.md"]
BANNED = re.compile(r"crisis line|crisis help|helpline|hotline|emergency services|\b(?:112|911|999)\b", re.I)


class PublicWording(unittest.TestCase):
    def test_no_crisis_helpline_or_emergency_wording(self):
        for f in DOCS:
            text = (REPO / f).read_text(encoding="utf-8")
            hits = [m.group(0) for m in BANNED.finditer(text)]
            self.assertEqual(hits, [], f)


if __name__ == "__main__":
    unittest.main()
