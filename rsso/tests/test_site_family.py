"""spec/SITE_FAMILY.md F1: S1 (family bar on every page), S2 (the home page keeps its machinery and links), S5 (contrast)."""
import re
import unittest
from pathlib import Path

DOCS = Path(__file__).resolve().parents[2] / "docs"
LANG = "https://r-a-elu-architecture.github.io/RSOS-Language/"
# every in-site and outbound link the home page had before F1 (spec/SITE_FAMILY.md S2)
BEFORE = ["world.html", "results.html", "#protocol", "#rsx", "rsxv.html", "#model", "player.html", "nodes.html", "anchors.html",
          "identity.html", "atlas.html", "night.html", "trials.html", "therapist.html", "device.html", "agents.html",
          "contribute.html", "safety.html", "tiers.html", "metrics.html", "system.html", "glyphs.html", "roadmap.html",
          "https://github.com/r-a-elu-architecture/RSOS-Multimodal-Cue-Framework",
          "https://github.com/r-a-elu-architecture/RSOS-Multimodal-Cue-Framework/blob/main/spec/OVERRIDE_PROTOCOL.md",
          "https://github.com/r-a-elu-architecture/RSOS-Multimodal-Cue-Framework#readme",
          "https://github.com/r-a-elu-architecture/RSOS-Multimodal-Cue-Framework/blob/main/rsx/model/PREDICTIONS.md",
          "https://github.com/r-a-elu-architecture/RSOS-Multimodal-Cue-Framework/blob/main/RELATED_WORK.md",
          "https://github.com/r-a-elu-architecture/RSOS-Multimodal-Cue-Framework/tree/main/archive",
          "https://github.com/r-a-elu-architecture/RSOS-Multimodal-Cue-Framework/tree/main/toolkit",
          "https://doi.org/10.5281/zenodo.24143731"]


def lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


class TestSiteFamily(unittest.TestCase):
    def test_s1_family_bar_everywhere(self):
        for f in sorted(DOCS.glob("*.html")):
            t = f.read_text(encoding="utf-8")
            self.assertEqual(t.count('class="family"'), 1, f.name)
            bar = t[t.index('class="family"'):t.index('class="family"') + 600]
            self.assertIn(LANG, bar, f.name)
            self.assertIn('class="here"', bar, f.name)

    def test_s2_home_keeps_machinery_and_links(self):
        t = (DOCS / "index.html").read_text(encoding="utf-8")
        for s in ("<!-- evidence:start -->", "<!-- evidence:end -->", "js/profiles.js", "js/outlet.js", "js/devmode.js",
                  'id="profileCards"', "sw.js", "<p data-raw>Intended use: a research platform"):
            self.assertIn(s, t, s)
        hrefs = set(re.findall(r'href="([^"]+)"', t))
        self.assertEqual([h for h in BEFORE if h not in hrefs], [])

    def test_s5_text_contrast(self):
        css = (DOCS / "site.css").read_text(encoding="utf-8")
        tok = dict(re.findall(r"--([\w-]+):(#[0-9a-fA-F]{6})", css))
        pairs = [("ink", "ground"), ("ink", "surface"), ("ink-2", "ground"), ("ink-2", "surface"), ("slate", "ground"),
                 ("slate", "surface"), ("green", "ground"), ("green", "surface"), ("amber", "amber-2"), ("red", "red-2"),
                 ("green", "green-2")]
        low = {f"{a} on {b}": round(ratio(tok[a], tok[b]), 2) for a, b in pairs if ratio(tok[a], tok[b]) < 4.5}
        self.assertEqual(low, {})


if __name__ == "__main__":
    unittest.main()
