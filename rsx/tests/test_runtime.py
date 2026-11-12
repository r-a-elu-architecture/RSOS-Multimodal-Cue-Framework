import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from rsx import SafetyGovernor, RunRecord, write_log, LOG_FIELDS  # noqa: E402
from rsx import conditioning as cm  # noqa: E402

MIN = 60_000


class Governor(unittest.TestCase):
    def test_self_runs_always_allowed(self):
        g = SafetyGovernor()
        self.assertTrue(all(g.start(t * 1000, "self")[0] for t in range(100)))

    def test_device_needs_opt_in(self):
        self.assertEqual(SafetyGovernor().check(0, "device"), (False, "device triggering needs the person's opt-in"))

    def test_refractory_hourly_daily(self):
        g = SafetyGovernor(opted_in=True)
        self.assertTrue(g.start(0, "device")[0])
        self.assertEqual(g.check(60_000, "device")[1], "refractory period")
        t = 0
        for _ in range(5):
            t += 2 * MIN; self.assertTrue(g.start(t, "device")[0])
        self.assertEqual(g.check(t + 2 * MIN, "device")[1], "hourly limit")
        t = 0; g = SafetyGovernor(opted_in=True)
        for k in range(20):
            self.assertTrue(g.start(k * 15 * MIN, "device")[0])
        self.assertEqual(g.check(20 * 15 * MIN, "device")[1], "daily limit")
        self.assertTrue(g.check(24 * 60 * MIN + 1, "device")[0])


class Log(unittest.TestCase):
    def test_csv_schema(self):
        text = write_log([RunRecord("p01", "override", sud_before=7, sud_after=3, agency_before=2, agency_after=7,
                                    trigger_channel="memory", timestamp=1.0)])
        self.assertEqual(text.splitlines()[0].split(","), LOG_FIELDS)

    def test_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            write_log([RunRecord("p01", "override", sud_before=11)])


class Conditioning(unittest.TestCase):
    def test_compound_learns_faster_with_more_channels(self):
        n = [cm.trials_to(cm.acquisition(list(ch), 60), "compound", 0.9) for ch in ("V", "VAK", "VAKO")]
        self.assertTrue(n[0] > n[1] > n[2])

    def test_overshadowing_single_cue_weaker_in_bundle(self):
        alone = cm.acquisition(["V"], 60)[-1]["V_V"]
        bundled = cm.acquisition(["V", "A", "K"], 60)[-1]["V_V"]
        self.assertLess(bundled, alone)

    def test_blocking_after_pretraining(self):
        fresh = cm.counterconditioning(["V", "A", "K"], pretrain=0, pairings=30)[-1]["V_trigger"]
        blocked = cm.counterconditioning(["V", "A", "K"], pretrain=60, pairings=30)[-1]["V_trigger"]
        self.assertGreater(fresh, blocked)

    def test_habit_monotone(self):
        h = cm.habit(100)
        self.assertTrue(all(a["automaticity"] < b["automaticity"] for a, b in zip(h, h[1:])))
        self.assertLess(h[-1]["latency_s"], h[0]["latency_s"])


if __name__ == "__main__":
    unittest.main()
