"""Software-in-the-loop tests of the RDP/1 firmware core (firmware/rsos_core) through the host simulator."""
import pathlib
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path[:0] = [str(HERE.parent), str(REPO / "rsx")]
from rsso.devices import VirtualHaptic  # noqa: E402
from rsso.protocol import ProtocolDevice, build_host_sim, encode  # noqa: E402
from rsso.runtime import play  # noqa: E402
from rsso import conformance  # noqa: E402
from rsx import compile_rsx  # noqa: E402

HAVE_CXX = shutil.which("g++") or shutil.which("c++") or shutil.which("clang++")
OVERRIDE = compile_rsx((REPO / "rsx" / "protocols" / "override.rsx").read_text(encoding="utf-8"))


def sim(lines):
    out = subprocess.run([str(build_host_sim())], input="\n".join(lines + ["QUIT"]) + "\n",
                         capture_output=True, text=True, check=True).stdout
    return [x for x in out.splitlines() if not x.startswith("TOCK")]


@unittest.skipUnless(HAVE_CXX, "no C++ compiler")
class Firmware(unittest.TestCase):
    def test_conformance_on_firmware_core(self):
        res = conformance.run_suite(conformance.firmware_rig)
        self.assertTrue(all(r[2] for r in res), conformance.report(res))

    def test_pulses_match_the_timeline_exactly(self):
        fw = ProtocolDevice(); ref = VirtualHaptic()
        play(OVERRIDE, [fw]); play(OVERRIDE, [ref])
        expected = [(t, t + on) for a in ref.actions for t, on in a.detail["pulses"]]
        got = [(a.t_ms, a.t_ms + a.dur_ms) for a in fw.actions if a.kind == "pulse"]
        self.assertEqual(got, expected)
        fw.close()

    def test_scent_with_consent_is_capped_at_3s(self):
        tl = compile_rsx('PROTOCOL s\nPHASE p {\nSMELL "cedar"\nWAIT 500ms\n}')
        tl["events"][0]["dur"] = 9000; tl["duration_ms"] = 10000
        fw = ProtocolDevice(consent=True); play(tl, [fw])
        rel = [a for a in fw.actions if a.kind == "release"]
        self.assertEqual(len(rel), 1); self.assertEqual(rel[0].dur_ms, 3000)
        fw.close()

    def test_protocol_errors(self):
        out = sim(["START", "LOAD 65 0.4", "LOAD 1 1.5", "X 1", "H 0 300 300 3 0.4"])
        self.assertEqual(out, ["ERR START not-loaded", "ERR LOAD too-many-events", "ERR LOAD syntax", "ERR X unknown", "ERR H not-loading"])

    def test_link_loss_stops_output(self):
        out = sim(["LOAD 1 0.4", "H 0 1000 0 5 0.4", "START", "TICK 1500", "LINK_LOST", "TICK 6000"])
        self.assertIn("STOPPED 1500", out)
        self.assertNotIn("DONE 5000", out)
        self.assertEqual(out[-2:], ["MOTOR 1500 0.00", "STOPPED 1500"])

    def test_encode_selects_device_channels(self):
        lines = encode(OVERRIDE)
        self.assertEqual(lines[0], "LOAD 3 0.40")
        self.assertTrue(all(x.startswith("H ") for x in lines[1:]))


class SketchInSync(unittest.TestCase):
    def test_esp32_copy_of_core_is_identical(self):
        for f in ("rsos_core.h", "rsos_core.cpp"):
            self.assertEqual((REPO / "firmware/rsos_core" / f).read_bytes(), (REPO / "firmware/esp32/rsos_esp32" / f).read_bytes(), f)

    @unittest.skipUnless(shutil.which("g++"), "no g++")
    def test_esp32_sketch_compiles_against_stubs(self):
        st = REPO / "firmware/esp32/stubs"
        r = subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-Wno-unused-parameter", f"-I{st}",
                            f"-I{REPO / 'firmware/esp32/rsos_esp32'}", "-fsyntax-only", "-x", "c++", str(st / "check.cpp")],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
