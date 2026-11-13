"""The roadmap and claims register: reproducible from one source, complete, and consistent with the site."""
import json
import pathlib
import re
import subprocess
import sys
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]
OUTPUTS = [REPO / "docs" / "data" / "roadmap.json", REPO / "spec" / "ROADMAP.md", REPO / "spec" / "CLAIMS.md"]
EXCLUDED = [r"48\s*laws", r"\bcunning\b", r"\btribit\b", r"\bFox\b"]


class Roadmap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((REPO / "docs" / "data" / "roadmap.json").read_text(encoding="utf-8"))

    def test_reproducible_from_source(self):
        before = {p: p.read_bytes() for p in OUTPUTS}
        subprocess.run([sys.executable, str(REPO / "architecture" / "roadmap.py")], check=True, capture_output=True)
        changed = [str(p.relative_to(REPO)) for p in OUTPUTS if p.read_bytes() != before[p]]
        self.assertEqual(changed, [], "roadmap outputs were stale; roadmap.py has now rewritten them")

    def test_items_complete(self):
        ids = [i["id"] for i in self.data["items"]]
        self.assertEqual(ids, list(range(1, 70)))
        steps = {s["id"] for s in self.data["steps"]}
        self.assertEqual(steps, set(range(0, 10)))
        for i in self.data["items"]:
            self.assertIn(i["step"], steps, i["id"])
            for k in ("title", "kind", "module", "status", "source", "summary"):
                self.assertTrue(i[k].strip(), (i["id"], k))
        for s in range(1, 10):
            self.assertTrue(any(i["step"] == s for i in self.data["items"]), f"step {s} has no items")
        for i in self.data["items"]:
            if i["status"].startswith("merged into"):
                for n in map(int, re.findall(r"\d+", i["status"])):
                    self.assertIn(n, ids)

    def test_every_claim_has_a_test(self):
        ids = {i["id"] for i in self.data["items"]}
        claims = self.data["claims"]
        self.assertEqual([c["id"] for c in claims], [f"C{n}" for n in range(1, 102)])
        for c in claims:
            self.assertTrue(c["claim"].strip() and c["test"].strip() and c["by"] and c["kind"], c["id"])
            self.assertTrue(set(c["items"]) <= ids, c["id"])

    def test_combinations_and_hypotheses(self):
        ids = {i["id"] for i in self.data["items"]}
        for c in self.data["combinations"]:
            self.assertTrue(set(c["items"]) <= ids, c["id"])
        self.assertEqual([h["id"] for h in self.data["hypotheses"]], ["H-a", "H-b", "H-c", "H-d", "H-e", "H-f"])
        self.assertTrue(all(h["status"] == "deferred" for h in self.data["hypotheses"]))


class Framing(unittest.TestCase):
    def test_public_roadmap_is_framework_only(self):
        """The roadmap speaks as a framework: no personal events or personal sources in public files."""
        files = OUTPUTS + [REPO / "docs" / "roadmap.html"] + [REPO / "spec" / n for n in ("GLOSSARY.md", "PROVENANCE.md", "PRIOR_ART.md", "FOUNDATIONS.md")]
        pats = [r"\bE1\b", r"author's", r"\bobserved event", r"conversation archive"]
        hits = [f"{p.name}: {pat}" for p in files for pat in pats if re.search(pat, p.read_text(encoding="utf-8"), re.I)]
        self.assertEqual(hits, [])
        self.assertNotIn("events", self.__class__.data())

    @staticmethod
    def data():
        return json.loads((REPO / "docs" / "data" / "roadmap.json").read_text(encoding="utf-8"))


class Site(unittest.TestCase):
    def test_every_page_has_the_full_menu(self):
        want = ["Protocol", "RSX", "Model", "Player", "Nodes", "Anchors", "Identity", "Atlas", "Night", "Trials", "Therapist", "Devices", "Contribute", "Safety",
                "Tier ledger", "Metrics", "System", "Glyphs", "Roadmap", "GitHub"]
        for f in sorted((REPO / "docs").glob("*.html")):
            m = re.search(r"<nav(?: class=\"site\"[^>]*)?>(.*?)</nav>", f.read_text(encoding="utf-8"), re.S)
            if not m:
                continue
            got = re.findall(r">([^<]+)</a>", m.group(1))
            self.assertEqual(got, want, f.name)

    def test_roadmap_is_offline_and_listed(self):
        sw = (REPO / "docs" / "sw.js").read_text(encoding="utf-8")
        self.assertIn('"roadmap.html"', sw)
        self.assertIn('"data/roadmap.json"', sw)
        self.assertIn("roadmap.html", (REPO / "docs" / "sitemap.xml").read_text(encoding="utf-8"))


class Excluded(unittest.TestCase):
    def test_excluded_terms_appear_nowhere(self):
        files = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True).stdout.split()
        if not files:
            files = [str(p.relative_to(REPO)) for p in REPO.rglob("*") if p.is_file() and ".git" not in p.parts]
        files += [str(p.relative_to(REPO)) for p in (REPO / "spec").glob("*.md")] + ["docs/roadmap.html", "architecture/roadmap.py"]
        hits = []
        for rel in sorted(set(files)):
            p = REPO / rel
            if not p.is_file() or p.suffix in (".png", ".jpg", ".pdf", ".zip", ".woff2", ".ico") or p.stat().st_size > 5_000_000:
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
            for pat in EXCLUDED:
                if re.search(pat, text, 0 if pat == r"\bFox\b" else re.I):
                    hits.append(f"{rel}: {pat}")
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
