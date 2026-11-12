import pathlib
import sys
import unittest

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parents[1] / "rsx")]
from rsso.devices import standard_rig, VirtualHaptic, Device, Action  # noqa: E402
from rsso.runtime import play  # noqa: E402
from rsso import conformance, study, analysis  # noqa: E402
from rsso.sensors import Event, HeartProfile, VirtualHeartRateStrap, StressDetector, score_detections  # noqa: E402
from rsx import compile_rsx  # noqa: E402

OVERRIDE = compile_rsx((HERE.parents[1] / "rsx" / "protocols" / "override.rsx").read_text(encoding="utf-8"))


class Runtime(unittest.TestCase):
    def test_full_run_dispatches_every_event(self):
        tr = play(OVERRIDE, standard_rig())
        self.assertTrue(tr.completed)
        self.assertEqual(tr.dispatched, len(OVERRIDE["events"]))

    def test_stop_truncates_vibration(self):
        devs = standard_rig()
        tr = play(OVERRIDE, devs, stop_at_ms=500)          # inside the first VIB-ANCHOR pattern
        hap = next(d for d in devs if d.name == "haptic")
        self.assertEqual(tr.stopped_at_phase, "interrupt")
        self.assertEqual(hap.actions[0].t_ms + hap.actions[0].dur_ms, 500)
        self.assertEqual(hap.output_after(500), [])


class Conformance(unittest.TestCase):
    def test_virtual_rig_passes(self):
        res = conformance.run_suite()
        self.assertTrue(all(r[2] for r in res), conformance.report(res))

    def test_suite_catches_a_device_that_ignores_stop(self):
        class Stubborn(VirtualHaptic):
            def stop(self, t_ms):
                self.armed = False
                return t_ms + 400                       # keeps vibrating for 400 ms
        res = {r[0]: r[2] for r in conformance.run_suite(lambda: [Stubborn()] + standard_rig()[1:])}
        self.assertFalse(res["C2"])

    def test_suite_catches_an_overdriving_device(self):
        class Loud(Device):
            name, channels = "loud", ("haptic",)
            def _act(self, e, t):
                return Action(t, self.name, "pattern", 10, {"amp": 1.0})
        res = {r[0]: r[2] for r in conformance.run_suite(lambda: [Loud()] + standard_rig()[1:])}
        self.assertFalse(res["C4"])


class Sensors(unittest.TestCase):
    def test_detector_on_virtual_strap(self):
        rng = np.random.default_rng(7); dur = 3 * 3600; scores = []
        for s in range(3):
            ev = [Event(float(t), "stress", 1.0) for t in (1200, 4200, 7800)]
            ev += [Event(5800.0, "activity", 0.8, 300)]
            rec = VirtualHeartRateStrap(HeartProfile.sample(rng), ev, seed=s).record(dur)
            scores.append(score_detections(StressDetector().detect(rec), ev, dur))
        self.assertGreaterEqual(np.mean([x["sensitivity"] for x in scores]), 0.8)
        self.assertLessEqual(np.mean([x["false_alarms_per_hour"] for x in scores]), 1.0)

    def test_paced_breathing_raises_rr_variability(self):
        p = HeartProfile()
        calm = VirtualHeartRateStrap(p, [], seed=1).record(300)
        paced = VirtualHeartRateStrap(p, [Event(0, "override", 1, 300)], seed=1).record(300)
        self.assertGreater(np.std(paced["rr"]), np.std(calm["rr"]))


class Study(unittest.TestCase):
    def test_h1_pipeline_recovers_assumed_direction(self):
        runs = study.h1(people=20, seed=1)["runs"]
        self.assertEqual(list(runs[study.COLUMNS].columns), study.COLUMNS)
        r = analysis.h1(runs)["relief"]
        self.assertGreater(r["mean"], 0)
        self.assertLess(r["p"], 0.05)

    def test_null_effect_is_not_found(self):
        cfg = study.StudyConfig(override_relief=1.0, control_relief=1.0)
        r = analysis.h1(study.h1(people=40, seed=2, cfg=cfg)["runs"])["relief"]
        self.assertLess(abs(r["mean"]), 0.35)

    def test_longitudinal_report(self):
        out = study.longitudinal(people=6, weeks=2, seed=3)
        text = analysis.report(out["runs"], out["triggers"], out["srbai"])
        self.assertIn("H2", text); self.assertIn("H5", text)


if __name__ == "__main__":
    unittest.main()
