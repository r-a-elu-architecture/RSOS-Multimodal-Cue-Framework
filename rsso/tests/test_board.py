import json
import pathlib
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parents[1] / "rsx")]
from rsso import board, ugcl  # noqa: E402
from rsso.protocol import build_host_sim, encode  # noqa: E402
from rsx import compile_rsx  # noqa: E402

NODE = shutil.which("node")
ROOT = HERE.parents[1]


class DeadPort:
    """A port with nothing on the other end."""
    def write(self, data):
        pass

    def readline(self):
        return b""

    def close(self):
        pass


class Board(unittest.TestCase):
    def test_quick_check_passes_on_the_firmware_core_in_real_time(self):
        port = board.SimSerialPort()
        tx = board.SerialTransport(port)
        res = board.quick_check(tx)
        tx.shutdown()
        self.assertEqual([r[0] for r in res], [f"B{k}" for k in range(1, 8)])
        self.assertTrue(all(r[2] for r in res), [r for r in res if not r[2]])

    def test_quick_check_fails_without_a_device(self):
        res = board.quick_check(board.SerialTransport(DeadPort()))
        self.assertFalse(any(r[2] for r in res))

    @unittest.skipUnless(NODE, "node not installed")
    def test_browser_matches_python(self):
        tls = [compile_rsx(f.read_text(encoding="utf-8")) for f in sorted((ROOT / "rsx" / "protocols").glob("*.rsx"))]
        codes = [[ugcl.tacton_pulses(c), 0.4] for c in ("..-", "---", "..- ---", "-")]
        inp = dict(timelines=tls, codes=codes, host_sim=str(build_host_sim()))
        js = json.loads(subprocess.run([NODE, str(HERE / "js_board.js")], input=json.dumps(inp), capture_output=True, text=True, check=True, timeout=60).stdout)
        self.assertEqual(js["encoded"], [encode(t) for t in tls])
        self.assertEqual(js["codes"][0], ["LOAD 3 0.40", "H 0 100 100 1 0.40", "H 200 100 100 1 0.40", "H 400 300 100 1 0.40"])
        self.assertEqual([r[0] for r in js["check"]], [f"B{k}" for k in range(1, 8)])
        self.assertTrue(all(r[2] for r in js["check"]), [r for r in js["check"] if not r[2]])


if __name__ == "__main__":
    unittest.main()
