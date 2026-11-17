"""spec/SITE_CATCHUP.md: repository checks for Steps 6 to 8 (S6.4, S6.5, S7.3, S8.6)."""
import pathlib
import re
import sys
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]
SYSTEM = (REPO / "docs/system.html").read_text(encoding="utf-8")
BUILD = (REPO / "architecture/build.py").read_text(encoding="utf-8")
NODE_RX = re.compile(r'^  (\w+): \{ x: (\d+), y: (\d+), w: (\d+), h: (\d+), t: "([^"]+)", s: "[^"]*", status: "(\w+)", layer: (null|"[^"]+")', re.M)


def nodes():
    return {m[0]: {"x": int(m[1]), "y": int(m[2]), "w": int(m[3]), "h": int(m[4]), "t": m[5], "status": m[6], "layer": m[7].strip('"')}
            for m in NODE_RX.findall(SYSTEM)}


class Step6(unittest.TestCase):
    def test_statuses_match_the_architecture_map(self):   # S6.4
        arch = dict(re.findall(r'^    \("([A-Z0-9]+)", "[^"]+", "(\w+)",', BUILD, re.M))
        arch.update({"RSX": "built", "RSX-V": "built"})
        n = nodes()
        self.assertIn("rsxv", n)
        for k, v in n.items():
            if v["layer"] != "null" and v["layer"] in arch:
                self.assertEqual(v["status"], arch[v["layer"]], k)
        self.assertEqual({v["layer"] for v in n.values()} - {"null"} - set(arch), set())

    def test_boxes_inside_the_map_and_not_overlapping(self):   # S6.5
        n = list(nodes().items())
        for k, b in n:
            self.assertTrue(0 <= b["x"] and b["x"] + b["w"] <= 900 and 0 <= b["y"] and b["y"] + b["h"] <= 640, k)
        for i, (a, A) in enumerate(n):
            for b, B in n[i + 1:]:
                apart = A["x"] + A["w"] <= B["x"] or B["x"] + B["w"] <= A["x"] or A["y"] + A["h"] <= B["y"] or B["y"] + B["h"] <= A["y"]
                self.assertTrue(apart, (a, b))

    def test_safety_box_names_the_new_parts(self):   # S6.1-S6.3
        for s in ("Watchdog and CONTAIN", "Paused: practical", "Clinician-led protocol", "docs/js/outlet.js", "docs/js/lineage.js",
                  '["ai", "rsxv"], ["rsxv", "program"]', "spec/BLE_PAIRING.md"):
            self.assertIn(s, SYSTEM)



class Step7(unittest.TestCase):
    def test_example_is_the_real_bridge_output(self):   # S7.3
        import json
        import subprocess
        d = json.loads((REPO / "docs/data/rsxv_example.json").read_text(encoding="utf-8"))
        self.assertEqual(d["command"], (REPO / "rsxv/examples/dragon.rsxv").read_text(encoding="utf-8").rstrip("\n"))
        self.assertEqual(d["cue"], (REPO / "rsxv/examples/dragon.cue.rsx").read_text(encoding="utf-8").rstrip("\n"))
        r = subprocess.run([sys.executable, "-c", "import json; from rsxv.site_example import build; print(json.dumps(build()))"],
                           cwd=REPO / "rsxv", capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(r.stdout), d)

    def test_page_listed_everywhere(self):   # S7.1, S7.4
        self.assertIn('"rsxv.html"', (REPO / "docs/sw.js").read_text(encoding="utf-8"))
        self.assertIn("rsxv.html", (REPO / "docs/sitemap.xml").read_text(encoding="utf-8"))
        for p in (REPO / "docs").glob("*.html"):
            s = p.read_text(encoding="utf-8")
            if "<nav" in s:
                self.assertIn('href="rsxv.html"', s, p.name)
        page = (REPO / "docs/rsxv.html").read_text(encoding="utf-8")
        for s in ("js/outlet.js", "not a medical device", "none comes from people"):
            self.assertIn(s, page)



class Step8(unittest.TestCase):
    def test_families_parents_counts(self):   # S8.6
        import json
        d = json.loads((REPO / "docs/data/results_register.json").read_text(encoding="utf-8"))
        rows = d["rows"]
        plain = lambda t: re.sub(r"<[^>]+>", "", t).strip()
        index = {plain(r["test"]): i for i, r in enumerate(rows)}
        for i, r in enumerate(rows):
            self.assertIn(r["family"], d["families"], r["test"])
            self.assertNotEqual(r["family"], "other", r["test"])
            if r["parent"] is not None:
                j = index[r["parent"]]
                self.assertLess(j, i)
                self.assertEqual((rows[j]["family"], rows[j]["series"]), (r["family"], r["series"]))
        for f in d["families"]:
            for s in ("pass", "mixed", "fail", "analysis", "other"):
                self.assertEqual(d["family_counts"][f][s], sum(r["family"] == f and r["status"] == s for r in rows), (f, s))

    def test_display_wording(self):   # S8.5
        for p in ("docs/data/results_register.json", "docs/results.html"):
            self.assertNotIn("past-crisis", (REPO / p).read_text(encoding="utf-8"), p)


if __name__ == "__main__":
    unittest.main()
