import json
import pathlib
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parents[1] / "rsx")]
from rsso import memstack as ms, study  # noqa: E402

NODE = shutil.which("node")


def person_log(seed=5, weeks=4):
    out = study.longitudinal(people=1, weeks=weeks, device_fraction=0.0, seed=seed)
    runs = json.loads(out["runs"].to_json(orient="records"))
    # add practice runs (no trigger) at the start, as the player records them
    t0 = min(r["timestamp"] for r in runs)
    practice = [dict(timestamp=t0 - 3600 * (k + 1), participant="s000", protocol="override", trigger="self", trigger_channel="",
                     trigger_note="", sud_before=3, sud_after=2, agency_before=5, agency_after=6, latency_s="", completed=1,
                     stopped_at_phase="", tier="LION", voice="own") for k in range(15)]
    srbai = json.loads(out["srbai"].to_json(orient="records"))
    return practice + runs, srbai


class Memstack(unittest.TestCase):
    def test_summary_tracks_learning(self):
        runs, srbai = person_log()
        t = ms.summarize(runs, srbai)["tiers"]["LION"]
        self.assertEqual(t["practice"], 15)
        self.assertGreater(t["trigger_runs"], 50)
        self.assertGreater(t["bundle_strength"], 0.95)
        h = t["habit"]
        self.assertIsNotNone(h)
        first = [r["latency_s"] for r in runs if r["trigger_channel"]][:5]
        self.assertLess(h["predicted_latency_now"], min(first))      # faster than at the start
        self.assertGreater(h["runs_to_reflex"], 0)                  # but not yet a reflex after 4 weeks

    def test_habit_fit_recovers_parameters(self):
        lat = [1 + 60 * (1 - 0.05) ** n for n in range(80)]
        h = ms.fit_habit(lat)
        self.assertAlmostEqual(h["eta"], 0.05, delta=0.006)
        self.assertEqual(h["runs_to_reflex"], max(0, __import__("math").ceil(__import__("math").log(2 / 60) / __import__("math").log(0.95) - 80)))

    def test_reflex_criterion(self):
        runs = [dict(timestamp=k, tier="LION", trigger_channel="V", completed=1, latency_s=2.0, sud_before=5, sud_after=3) for k in range(12)]
        self.assertTrue(ms.summarize(runs, [{"week": 3, "srbai": 4.2}, {"week": 4, "srbai": 4.5}])["tiers"]["LION"]["reflex"]["met"])
        self.assertFalse(ms.summarize(runs, [{"week": 3, "srbai": 4.2}, {"week": 5, "srbai": 4.5}])["tiers"]["LION"]["reflex"]["met"])
        self.assertFalse(ms.summarize(runs[:9], [{"week": 3, "srbai": 4.2}, {"week": 4, "srbai": 4.5}])["tiers"]["LION"]["reflex"]["met"])

    def test_snapshot_roundtrip_and_tamper(self):
        runs, srbai = person_log(weeks=1)
        snap = ms.snapshot(runs, srbai)
        self.assertEqual(ms.restore(json.loads(json.dumps(snap))), (runs, srbai))
        snap["runs"][0]["sud_after"] = 9
        with self.assertRaises(ValueError):
            ms.restore(snap)

    def test_merge_removes_duplicates(self):
        runs, _ = person_log(weeks=1)
        self.assertEqual(ms.merge(runs, runs[:10]), sorted(runs, key=lambda r: r["timestamp"]))


@unittest.skipUnless(NODE, "node not installed")
class PythonJsAgree(unittest.TestCase):
    def test_same_summary_and_cross_verified_snapshots(self):
        runs, srbai = person_log()
        py = ms.summarize(runs, srbai)
        pysnap = ms.snapshot(runs, srbai)
        out = json.loads(subprocess.run([NODE, str(HERE / "js_memstack.js")], input=json.dumps({"runs": runs, "srbai": srbai, "pysnap": pysnap}),
                                        capture_output=True, text=True, check=True).stdout)
        js = out["summary"]
        self.assertEqual(out["pysnap_ok"], True); self.assertEqual(out["tampered"], "rejected")
        self.assertEqual(ms.restore(out["jssnap"]), (runs, srbai))
        self.assertEqual(set(py["tiers"]), set(js["tiers"]))
        for k, a in py["tiers"].items():
            b = js["tiers"][k]
            for f, v in a.items():
                if isinstance(v, dict):
                    for g, w in v.items():
                        self.assertAlmostEqual(w, b[f][g], delta=1e-3, msg=f"{k}.{f}.{g}") if isinstance(w, float) else self.assertEqual(w, b[f][g], f"{k}.{f}.{g}")
                elif isinstance(v, float):
                    self.assertAlmostEqual(v, b[f], delta=1e-3, msg=f"{k}.{f}")
                else:
                    self.assertEqual(v, b[f], f"{k}.{f}")


if __name__ == "__main__":
    unittest.main()
