import json
import pathlib
import shutil
import subprocess
import sys
import unittest

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from rsso.hrs import parse_hrm, encode_hrm, HrsStream  # noqa: E402
from rsso.sensors import Event, HeartProfile, VirtualHeartRateStrap, StressDetector  # noqa: E402

NODE = shutil.which("node")
PACKETS = [
    bytes([0x00, 72]),                                  # uint8 HR only
    bytes([0x16, 75, 0x00, 0x04, 0x33, 0x03]),          # contact supported+detected, RR 1024 (1000 ms), 819 (~800 ms)
    bytes([0x19, 0x2C, 0x01, 0x10, 0x00, 0x00, 0x03]),  # uint16 HR 300, energy 16 kJ, RR 768 (750 ms)
    encode_hrm(64, [937.5, 950.2], contact=False),
]


class Parser(unittest.TestCase):
    def test_spec_examples(self):
        self.assertEqual(parse_hrm(PACKETS[0]), {"hr": 72, "contact": None, "energy_kj": None, "rr_ms": []})
        p = parse_hrm(PACKETS[1])
        self.assertEqual((p["hr"], p["contact"]), (75, True)); self.assertEqual(p["rr_ms"], [1000.0, 819 * 1000 / 1024])
        p = parse_hrm(PACKETS[2])
        self.assertEqual((p["hr"], p["energy_kj"], p["rr_ms"]), (300, 16, [750.0]))

    def test_roundtrip_and_stream(self):
        s = HrsStream()
        s.push(encode_hrm(70, [850, 2500, 860]))         # 2500 ms is an artefact and is dropped
        rec = s.recording()
        self.assertEqual(len(rec["rr"]), 2)
        self.assertAlmostEqual(rec["t"][-1], (round(850 * 1.024) + round(860 * 1.024)) / 1024, places=6)


@unittest.skipUnless(NODE, "node not installed")
class PythonJsAgree(unittest.TestCase):
    def test_parser_and_detector_identical(self):
        rng = np.random.default_rng(11); dur = 3 * 3600
        ev = [Event(1500.0, "stress", 1.0), Event(5200.0, "stress", 0.8), Event(3300.0, "activity", 0.9, 400), Event(8000.0, "stress", 1.1)]
        rec = VirtualHeartRateStrap(HeartProfile.sample(rng), ev, seed=4).record(dur)
        payload = {"packets": [list(p) for p in PACKETS],
                   "rec": {"t": rec["t"].tolist(), "rr": rec["rr"].tolist(), "motion": rec["motion"].tolist()}}
        out = json.loads(subprocess.run([NODE, str(HERE / "js_hrs.js")], input=json.dumps(payload),
                                        capture_output=True, text=True, check=True).stdout)
        py = [parse_hrm(p) for p in PACKETS]
        for a, b in zip(py, out["parsed"]):
            self.assertEqual(a["hr"], b["hr"]); self.assertEqual(a["contact"], b["contact"])
            self.assertEqual(a["energy_kj"], b["energy_kj"]); self.assertEqual(a["rr_ms"], b["rr_ms"])
        pyd = StressDetector().detect(rec)
        self.assertGreaterEqual(len(pyd), 2)
        self.assertEqual(pyd, out["det"])


if __name__ == "__main__":
    unittest.main()
