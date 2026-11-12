"""Repository consistency: architecture pages match the archive manifest, and local links resolve."""
import pathlib
import re
import subprocess
import sys
import unittest
import urllib.parse

REPO = pathlib.Path(__file__).resolve().parents[2]


def snapshot():
    files = sorted((REPO / "architecture").rglob("README.md")) + [REPO / "architecture" / "SOURCE-TO-ARCHITECTURE-MAP.csv"]
    return {p: p.read_bytes() for p in files}


class Architecture(unittest.TestCase):
    def test_pages_are_up_to_date(self):
        before = snapshot()
        subprocess.run([sys.executable, str(REPO / "architecture" / "build.py")], check=True, capture_output=True)
        after = snapshot()
        changed = [str(p.relative_to(REPO)) for p in after if before.get(p) != after[p]]
        self.assertEqual(changed, [], "architecture/ was stale; build.py has now rewritten it")


class Links(unittest.TestCase):
    def test_local_links_resolve(self):
        bad = []
        for f in REPO.rglob("*"):
            if ".git" in f.parts or "original-estates" in f.parts or f.suffix not in (".md", ".html"):
                continue
            pattern = r'\]\(([^)\s]+)\)' if f.suffix == ".md" else r'href="([^"]+)"'
            for m in re.finditer(pattern, f.read_text(encoding="utf-8", errors="ignore")):
                u = m.group(1)
                if u.startswith(("http", "#", "mailto")):
                    continue
                target = urllib.parse.unquote(u.split("#")[0])
                if target and not (f.parent / target).exists():
                    bad.append(f"{f.relative_to(REPO)} -> {u}")
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
