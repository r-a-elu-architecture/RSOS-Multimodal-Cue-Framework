"""spec/POSITIONING.md P1-P2: the intended-use sentence is shown, and the README and index no longer invite individuals as users.
P3 is the existing A7 test (test_safety.py); P4 is scripts/check_all.sh."""
import html
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SENTENCE = ("Intended use: a research platform, and a tool for qualified practitioners working under their own professional protocol. "
            "Not a consumer wellness app. RSOS makes no therapeutic claim; claims about effects in people wait for registered human outcome data.")


def visible(p: Path) -> str:
    t = p.read_text(encoding="utf-8")
    if p.suffix == ".html":
        t = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", t)
        t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    else:
        t = re.sub(r"[*_>`]", "", t)
    return " ".join(t.split())


class TestPositioning(unittest.TestCase):
    def test_p1_sentence_shown(self):
        for rel in ("README.md", "docs/index.html", "docs/safety.html", "docs/therapist.html", "docs/player.html"):
            self.assertIn(SENTENCE, visible(ROOT / rel), rel)

    def test_p1b_identical_in_every_profile(self):
        # profile translation would turn "therapeutic" into "supportive"; the sentence is marked data-raw so it never changes
        for rel in ("docs/index.html", "docs/safety.html", "docs/therapist.html", "docs/player.html"):
            t = (ROOT / rel).read_text(encoding="utf-8")
            line = next(l for l in t.splitlines() if "Intended use: a research platform" in l)
            self.assertIn("<p data-raw", line, rel)

    def test_p2_no_invitation_to_individuals(self):
        for rel in ("README.md", "docs/index.html"):
            self.assertNotIn("researchers, clinics and individuals", visible(ROOT / rel), rel)


if __name__ == "__main__":
    unittest.main()
