"""spec/SUPPORT.md: U1 (FUNDING.yml), U2 (support page content), U3 (no payment form or third-party loads), U4 (linked)."""
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SPONSORS = "https://github.com/sponsors/r-a-elu-architecture"
PAGE = (REPO / "docs" / "support.html").read_text(encoding="utf-8")


class TestSupport(unittest.TestCase):
    def test_u1_funding_yml(self):
        lines = [l for l in (REPO / ".github" / "FUNDING.yml").read_text(encoding="utf-8").splitlines()
                 if l.strip() and not l.lstrip().startswith("#")]
        self.assertEqual(lines, ["github: [r-a-elu-architecture]"])

    def test_u2_page_content(self):
        for s in ('class="family"', 'class="ribbon"', '<nav class="main"', 'href="rsxv.html"', "<!-- evidence:start -->",
                  "<p data-raw>Intended use: a research platform",
                  "Your support buys no product, treatment or access. RSOS is a research and development framework, not a\nmedical device.",
                  f'href="{SPONSORS}"', "including null results"):
            self.assertIn(s, PAGE, s)

    def test_u3_no_payment_form_or_third_party_loads(self):
        self.assertNotRegex(PAGE, r"<form|<iframe")
        self.assertEqual(re.findall(r'<(?:img|script)[^>]+src="(?:https?:)?//[^"]+"', PAGE), [])
        self.assertEqual(re.findall(r'<link[^>]+href="(?:https?:)?//[^"]+"', PAGE.replace(
            '<link rel="canonical" href="https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/support.html">', "")), [])
        pay = re.compile(r"paypal|stripe\.com|buy\.stripe|ko-fi|patreon|opencollective|donate", re.I)
        self.assertEqual([h for h in re.findall(r'href="([^"]+)"', PAGE) if pay.search(h)], [])

    def test_u4_linked_everywhere(self):
        self.assertIn('href="support.html"', (REPO / "docs" / "index.html").read_text(encoding="utf-8"))
        self.assertIn(SPONSORS, (REPO / "README.md").read_text(encoding="utf-8"))
        self.assertIn('"support.html"', (REPO / "docs" / "sw.js").read_text(encoding="utf-8"))
        self.assertIn("support.html", (REPO / "docs" / "sitemap.xml").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
