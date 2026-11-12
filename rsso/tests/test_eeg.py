import pathlib
import sys
import unittest

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from rsso.eeg import ArousalDetector, ArousalEvent, ReplayStream, band_powers, synthetic_eeg  # noqa: E402


def run(x, sr):
    s, d = ReplayStream(x, sr), ArousalDetector()
    while not s.done:
        d.push(s.pull(0.5), sr)
    return d.detections


class EEG(unittest.TestCase):
    def test_band_power_of_alpha_sine(self):
        t = np.arange(1024) / 256
        bp = band_powers(10 * np.sin(2 * np.pi * 10 * t)[:, None], 256)
        self.assertGreater(bp["alpha"], bp["beta"] + 5)

    def test_detects_arousal_events_and_nothing_else(self):
        x, sr, _ = synthetic_eeg(900, events=[ArousalEvent(400, 60), ArousalEvent(700, 60)], seed=1)
        det = run(x, sr)
        self.assertEqual(len(det), 2)
        self.assertTrue(400 <= det[0] <= 430 and 700 <= det[1] <= 730)
        self.assertEqual(run(synthetic_eeg(900, seed=2)[0], 256.0), [])

    def test_replay_chunks_cover_the_recording(self):
        x = np.arange(1000.0)
        s = ReplayStream(x, 100)
        parts = [s.pull(0.3) for _ in range(40)]
        self.assertEqual(np.concatenate(parts).ravel().tolist(), x.tolist())


if __name__ == "__main__":
    unittest.main()
