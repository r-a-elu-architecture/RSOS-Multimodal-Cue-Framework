import copy
import json
import pathlib
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parents[1] / "rsx"), str(HERE)]
from rsso import contribution as C, memstack, nodes  # noqa: E402
from rsx import compile_rsx  # noqa: E402
from test_memstack import person_log  # noqa: E402

NODE = shutil.which("node")
ROOT = HERE.parents[1]


def inputs():
    runs, srbai = person_log(seed=3, weeks=3)
    for k, r in enumerate(runs):
        r.update(local_hour=8 + k % 12, weekday=k % 7, program_kind="builtin", program_hash="1a2b3c4d", outputs="voice+tone+vibration",
                 inhale_s=4, exhale_s=6, glyph="🦁", duration_s=52, planned_s=52, trigger_note="the boss called" if k == 3 else "")
        if k % 3 == 0:
            r.update(hr_before=88, hr_after=79.5, rmssd_before=24, rmssd_after=31.2, hr_source="strap")
    runs[5]["protocol"] = "node_my_secret_name"
    plan = nodes.plan(dict(concerns=["ptsd", "habits"], symptoms="Flashbacks", author="therapist", triggers=["Raised voices"],
                           physiology=dict(resting_hr=70, rmssd=30), devices=dict(V=True, K=True, hr=True),
                           nodes=[dict(archetype="LION", frames=["I breathe fully and completely"], O="Cedar", believability=7, contexts=["At work"]),
                                  dict(archetype="OBSERVER")]))
    plan.update(approved=True, intake=dict(concerns=["ptsd", "habits"], symptoms="Flashbacks", triggers=["Raised voices"], author="therapist",
                                           physiology=dict(resting_hr=70, rmssd=30), devices=dict(V=True, K=True, hr=True),
                                           nodes=[dict(archetype="LION", O="Cedar", believability=7), dict(archetype="OBSERVER")]))
    t0 = min(float(r["timestamp"]) for r in runs)
    base = dict(role="person", ids=dict(contribution_id="c-test", participant="p-test"), runs=runs, srbai=srbai, plan=plan, now=t0 + 30 * 86400,
                cues=[dict(id="a", tier="414", content="I am calm", author="therapist", created_ms=(t0 + 86400 * 2) * 1000, sound_hz=432)],
                ugcl=dict(tiers=dict(LION=dict(glyph="O001", candidates=["O001", "O002"], comparisons=[[0, 1, 0]], scores=[1.2, -1.2])), colour="#e8b04a"),
                recognition=[dict(code="..-", chosen="..-", correct=True, rt_ms=1830, options=["..-", "---", ".-.", "-"], modality="sound")],
                outcomes=[dict(scale="PHQ9", total=14, ts=t0, rater="self"), dict(scale="phq9", total=9, ts=t0 + 20 * 86400),
                          dict(scale="GAD7", total=99, ts=t0)],
                adverse=[dict(severity="mild", related="possible", resolved=True, ts=t0 + 86400, text="dizzy for a minute")],
                profile=dict(age_band="35-44", gender="woman", handedness="right", region="Europe", experience=dict(meditation="some", hypnosis="x"),
                             conditions=["ptsd", "made_up"], in_therapy=True),
                app=dict(player="1.11.0", secret="x"),
                consent=dict(agreed=True, sharing="open", scopes=["physiology", "plan", "calibration", "recognition", "outcomes", "safety", "profile"]))
    full = copy.deepcopy(base)
    full["consent"]["scopes"] = list(C.SCOPES)
    clin = copy.deepcopy(base)
    clin.update(role="clinician", clinical=dict(profession="psychologist", modalities=["EMDR", "CBT"], client_consent=True, diagnoses=["6b40"],
                                                sessions=[dict(ts=t0 + 86400 * 3, minutes=50, nodes_used=2, fidelity=8, engagement=9, cgi_s=5, cgi_i=3, therapist_led=True, notes="good")]))
    lab = copy.deepcopy(base)
    lab.update(role="lab", lab=dict(site_code="L01", ethics_ref="IRB-2026-14", device=dict(name="OpenBCI Cyton", kind="eeg", channels=8, fs_hz=250, montage="10-20"),
                                    recordings=[dict(file_sha256="ab" * 32, bids_path="sub-01/eeg/sub-01_task-override_eeg.edf", duration_s=60, clock_offset_ms=-12.5, artifact_pct=4.2, program="override")]))
    no_consent = copy.deepcopy(base)
    no_consent["consent"]["agreed"] = False
    clin_bad = copy.deepcopy(clin)
    clin_bad["clinical"]["client_consent"] = False
    lab_bad = copy.deepcopy(lab)
    lab_bad["lab"]["ethics_ref"] = " "
    minimal = dict(role="person", ids=dict(contribution_id="c2", participant="p2"), runs=[], consent=dict(agreed=True))
    return [base, full, clin, lab, no_consent, clin_bad, lab_bad, minimal]


class Contribution(unittest.TestCase):
    def test_deidentified_by_default(self):
        c = C.build(inputs()[0])
        text = json.dumps(c, ensure_ascii=False)
        for secret in ("the boss called", "Flashbacks", "Raised voices", "I am calm", "dizzy", "Cedar", "my_secret_name", "I breathe fully", "secret"):
            self.assertNotIn(secret, text)
        self.assertNotIn("timestamp", text)
        self.assertEqual(c["runs"][0]["day"], 0)
        self.assertIn("custom", [r["protocol"] for r in c["runs"]])
        self.assertNotIn("concerns", c["plan"])            # health information only with the health scope
        self.assertNotIn("conditions", c["profile"])
        self.assertEqual(c["profile"]["experience"], {"meditation": "some"})
        self.assertEqual([o["total"] for o in c["outcomes"]], [14, 9])   # out-of-range totals are dropped
        self.assertEqual(c["outcomes"][1]["day"], 20)
        self.assertTrue(c["cues"][0]["therapist_led"])
        self.assertEqual(c["plan"]["nodes"][0]["senses"]["O"], True)
        self.assertTrue(any("hr_before" in r for r in c["runs"]))
        self.assertEqual(c["app"], {"player": "1.11.0"})

    def test_texts_and_health_only_when_shared(self):
        c = C.build(inputs()[1])
        self.assertEqual(c["plan"]["concerns"], ["ptsd", "habits"])
        self.assertEqual(c["profile"]["conditions"], ["ptsd"])
        self.assertIn("the boss called", json.dumps(c))
        self.assertEqual(c["cues"][0]["content"], "I am calm")

    def test_consent_is_required(self):
        bad = inputs()
        for i in (4, 5, 6):
            with self.assertRaises(ValueError):
                C.build(bad[i])

    def test_checksum_and_runlog(self):
        c = C.seal(C.build(inputs()[2]))
        self.assertEqual(C.check(c), [])
        self.assertEqual(c["clinical"]["sessions"][0]["day"], 3)
        self.assertNotIn("diagnoses", c["clinical"])
        c2 = dict(c, role="lab")
        self.assertTrue(C.check(c2))
        rows = C.to_runlog(c)
        self.assertEqual(len(rows), len(c["runs"]))
        s = memstack.summarize(rows)                    # the analysis kit reads contributions unchanged
        self.assertIn("LION", s["tiers"])
        table = C.pool([c, C.seal(C.build(inputs()[3]))])
        self.assertEqual(table.count("\n"), 1 + 2 * len(c["runs"]))

    def test_bids_events(self):
        tl = compile_rsx((ROOT / "rsx" / "protocols" / "override.rsx").read_text(encoding="utf-8"))
        tsv = C.bids_events(tl)
        self.assertTrue(tsv.startswith("onset\tduration\ttrial_type\tphase\tvalue\n"))
        self.assertEqual(tsv.count("\n"), len(tl["events"]) + 1)

    @unittest.skipUnless(NODE, "node not installed")
    def test_python_and_javascript_identical(self):
        ins = inputs()
        tl = compile_rsx((ROOT / "rsx" / "protocols" / "node_lion.rsx").read_text(encoding="utf-8"))
        res = subprocess.run([NODE, str(HERE / "js_contribution.js")], input=json.dumps(dict(inputs=ins, timeline=tl, text="PROTOCOL override ✨")),
                             capture_output=True, text=True, check=True)
        js = json.loads(res.stdout)
        for k, inp in enumerate(ins):
            try:
                py = C.seal(C.build(inp))
            except ValueError as e:
                self.assertIsNone(js["built"][k], k)
                self.assertEqual(str(e), js["errors"][k])
                continue
            self.assertEqual(py["sha256"], js["built"][k]["sha256"], k)
            self.assertEqual(py, js["built"][k])
        self.assertEqual(js["check"], [])
        self.assertEqual(js["bids"], C.bids_events(tl))
        self.assertEqual(js["fnv"], C.fnv1a("PROTOCOL override ✨"))


if __name__ == "__main__":
    unittest.main()
