"""RELEASE_1 A2 F5: public documents carry no crisis, helpline or emergency wording (owner's decision)."""
import pathlib
import re
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]
DOCS = ["README.md", "SECURITY.md", "CONTRIBUTING.md", "REVIEW.md", "releases/NEXT.md", "releases/v2.1.0.md", "spec/OVERRIDE_PROTOCOL.md"]
EMERGENCY = "not for use in an emergency: if you are at risk of harm, contact your local emergency services."   # spec/PUBLIC_EDITION_2.md C
EMERGENCY_DOCS = ("README.md",)
BANNED = re.compile(r"crisis line|crisis help|helpline|hotline|emergency services|\b(?:112|911|999)\b", re.I)


class PublicWording(unittest.TestCase):
    def test_no_crisis_helpline_or_emergency_wording(self):
        for f in DOCS:
            text = (REPO / f).read_text(encoding="utf-8")
            if f in EMERGENCY_DOCS:              # the one allowed sentence, required there
                self.assertIn(EMERGENCY, text, f)
                text = text.replace(EMERGENCY, "")
            hits = [m.group(0) for m in BANNED.finditer(text)]
            self.assertEqual(hits, [], f)


if __name__ == "__main__":
    unittest.main()
