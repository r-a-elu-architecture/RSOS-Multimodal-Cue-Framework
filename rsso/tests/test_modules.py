"""The RDP/1.1 module code (firmware/rsos_core/rsos_modules.*) in simulation, and the display image converter."""
import pathlib
import shutil
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path[:0] = [str(HERE.parent)]
from rsso import modules as MD  # noqa: E402

HAVE_CXX = shutil.which("g++") or shutil.which("c++") or shutil.which("clang++")


@unittest.skipUnless(HAVE_CXX, "no C++ compiler")
class Modules(unittest.TestCase):
    def test_every_module_check_passes(self):
        r = MD.checks()
        self.assertEqual(len(r), 15)
        self.assertTrue(all(x[2] for x in r), MD.report(r))

    def test_faults_turn_the_element_off(self):
        by = {d["name"]: d for d in MD.thermal()}
        for n in ("sensor_open", "sensor_stuck", "sensor_spike", "sink_overheats", "battery_low"):
            self.assertNotEqual(by[n]["fault"], "none", n)
            self.assertEqual(by[n]["end_duty"], 0, n)
        self.assertLessEqual(max(d["max_skin"] for d in by.values()), 40.0)


class Parts(unittest.TestCase):
    def test_parts_list_on_the_site_matches(self):
        import json
        self.assertEqual(json.loads((REPO / "docs" / "data" / "parts.json").read_text(encoding="utf-8")), json.loads(json.dumps(MD.parts_json())))

    def test_costs(self):
        thermal = next(k for k in MD.KITS if k["id"] == "thermal")
        sites = next(k for k in MD.KITS if k["id"] == "sites")
        full, added = MD.kit_cost(thermal), MD.kit_cost(thermal, have_band=True)
        self.assertGreater(full["total"], added["total"])
        self.assertFalse(any("ESP32" in r["part"] for r in added["rows"]))
        self.assertAlmostEqual(MD.kit_cost(sites, 6)["total"] - MD.kit_cost(sites, 2)["total"], 4 * (2.99 + 7.95), places=2)
        for k in MD.KITS:
            for r in MD.kit_cost(k, 3)["rows"]:
                self.assertEqual(r["shop"] is None, r["url"] is None)


class ImageTool(unittest.TestCase):
    def test_convert(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow not installed")
        sys.path.insert(0, str(REPO / "firmware" / "esp32"))
        import make_image
        with tempfile.TemporaryDirectory() as d:
            src = pathlib.Path(d) / "a.png"
            Image.new("RGB", (300, 200), (255, 0, 0)).save(src)
            out = make_image.convert(src, "lion", out_dir=d)
            b = out.read_bytes()
            self.assertEqual(len(b), 240 * 240 * 2)
            self.assertEqual(b[:2], bytes((0x00, 0xF8)))     # pure red in RGB565, little-endian
            with self.assertRaises(ValueError):
                make_image.convert(src, "../etc", out_dir=d)


if __name__ == "__main__":
    unittest.main()
