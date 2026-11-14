import pathlib, sys, unittest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from rsxv import agents as ag, safety as sf


def ok(**kw):
    p = {"actor": "TIGER", "action": "cue", "target": "agent_self", "disclosed": True, "logged": True,
         "predicted_harm": 0.0, "measured": True, "serves_mission": True}
    p.update(kw)
    return p


class TestSpineSafetyRules(unittest.TestCase):
    def test_each_rule_blocks(self):
        for flag, virtue in [({"intensity_mechanism": "temperature_extreme"}, "jin"),
                             ({"rank_claim_about_person": True}, "makoto"),
                             ({"frames_failure_as_required": True}, "jin"),
                             ({"profiles_third_party": True}, "rei"),
                             ({"prompts_disclosure": True}, "rei"),
                             ({"draft_misleading": True}, "makoto"),
                             ({"removes_safety_caveat": True}, "jin")]:
            r = ag.spine_check(ok(**flag))
            self.assertFalse(r["ok"], flag)
            self.assertIn(virtue, r["failed"], flag)
        self.assertTrue(ag.spine_check(ok(intensity_mechanism="warm_shower"))["ok"])

    def test_mode_gate(self):
        self.assertTrue(ag.spine_check(ok(mode="NORMAL", category="deep_processing"))["ok"])
        for mode, cat in [("STABILISE", "deep_processing"), ("STABILISE", "override_cue"),
                          ("PRACTICAL_CRISIS", "module_work"), ("CRISIS", "regulating_cue")]:
            self.assertIn("mode", ag.spine_check(ok(mode=mode, category=cat))["failed"], (mode, cat))
        self.assertTrue(ag.spine_check(ok(mode="CRISIS", category="crisis_response"))["ok"])
        self.assertTrue(ag.spine_check(ok(mode="STABILISE", category="regulating_cue"))["ok"])


class TestScreensAndModes(unittest.TestCase):
    def test_screens(self):
        self.assertIn("sedative_combination", sf.screen({"substances": True, "sedative_prescribed": True}))
        self.assertNotIn("sedative_combination", sf.screen({"substances": True}))
        self.assertIn("possible_crisis", sf.screen({"hopelessness": True, "arrangements_for_after": True}))
        self.assertNotIn("possible_crisis", sf.screen({"hopelessness": True}))
        self.assertIn("practical_crisis", sf.screen({"job_loss": True}))
        self.assertIn("unstable", sf.screen({"sleep_h": 3}))

    def test_escalation_and_responses(self):
        s = sf.SafetyState()
        r = s.observe({"hopelessness": True, "arrangements_for_after": True})
        self.assertEqual(s.mode, "CRISIS")
        for a in ["ask_safety_directly", "crisis_contacts_for_country", "notify_clinician_view", "pause_module_work"]:
            self.assertIn(a, r["actions"])
        s.observe({"job_loss": True})                        # lower severity never downgrades
        self.assertEqual(s.mode, "CRISIS")

    def test_sedative_response(self):
        s = sf.SafetyState()
        r = s.observe({"substances": True, "sedative_prescribed": True})
        self.assertEqual(s.mode, "CRISIS")
        self.assertIn("state_breathing_risk_plainly", r["actions"])
        self.assertIn("route_prescriber_or_emergency_if_symptoms", r["actions"])

    def test_exit_rules(self):
        s = sf.SafetyState()
        s.observe({"self_harm_signal": True})
        self.assertFalse(s.exit("person")["ok"])
        self.assertFalse(s.exit("agent")["ok"])
        self.assertTrue(s.exit("clinician")["ok"])
        s.observe({"no_income": True})
        self.assertEqual(s.mode, "PRACTICAL_CRISIS")
        self.assertFalse(s.exit("WATCHDOG")["ok"])
        self.assertTrue(s.exit("person")["ok"])
        self.assertTrue(s.enter_stabilise()["ok"])
        self.assertEqual(s.mode, "STABILISE")
        self.assertEqual(len(s.history), 5)


class TestDeepSessionGate(unittest.TestCase):
    green = {"sleep_ok": True, "functioning_ok": True, "craving_spike": False, "distress_at_baseline": True}

    def test_gate(self):
        g = sf.may_start_deep_session
        self.assertEqual(g(0, None, None, 0, "unknown")["why"], "consent_tier_required")
        self.assertTrue(g(0, None, None, 0, "self_chosen")["ok"])
        self.assertEqual(g(0, None, None, 1, "self_chosen")["why"], "weekly_cap")
        last = {"end_h": 0, "intensity": "intense"}
        self.assertEqual(g(30, last, self.green, 1, "clinician_agreed")["why"], "recovery_window")
        self.assertTrue(g(50, last, self.green, 1, "clinician_agreed")["ok"])
        bad = dict(self.green, craving_spike=True)
        self.assertEqual(g(50, last, bad, 1, "clinician_agreed")["why"], "stability_check_not_green")


class TestCovariates(unittest.TestCase):
    def test_confound_removed(self):
        # medication raises the outcome by 5; module adds 1; treated sessions happen mostly on medication
        recs = []
        for med, n_t, n_c in [("on", 9, 1), ("off", 1, 9)]:
            base = 5 if med == "on" else 0
            recs += [{"treated": True, "med_state": med, "outcome": base + 1}] * n_t
            recs += [{"treated": False, "med_state": med, "outcome": base}] * n_c
        r = sf.adjusted_effect(recs)
        self.assertAlmostEqual(r["adjusted"], 1.0)
        self.assertGreater(r["crude"], 4.0)
        r2 = sf.adjusted_effect([{"treated": True, "med_state": "x", "outcome": 1}])
        self.assertIsNone(r2["adjusted"])
        self.assertEqual(r2["strata_dropped"], ["x"])


if __name__ == "__main__":
    unittest.main()
