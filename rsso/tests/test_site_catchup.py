"""spec/SITE_CATCHUP.md: repository checks for Steps 6 to 8 (S6.4, S6.5, S7.3, S8.6)."""
import pathlib
import re
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


if __name__ == "__main__":
    unittest.main()
