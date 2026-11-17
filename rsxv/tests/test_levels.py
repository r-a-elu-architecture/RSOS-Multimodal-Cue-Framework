"""spec/RSXV_LEVELS.md Q1: RSX-V commands carry guidance levels, keep them through NEXT and ask the Watchdog."""
import pathlib
import random
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "rsso"))
import rsxv  # noqa: E402
from rsxv import bridge as B, lang, sim  # noqa: E402
from rsso import watchdog as W  # noqa: E402

DRAGON = (HERE / "examples/dragon.rsxv").read_text(encoding="utf-8")
CTX = {"seed": 5, "now_min": 600, "consent": ["subject", "operator", "auditor"]}
P = sim.person(random.Random(3), 0)


def cmd(head="", tier=8, intent="steady identity under pressure"):
    s = DRAGON.replace("RSX-V TIER 8", f"RSX-V TIER {tier}").replace('INTENT "steady identity under pressure"', f'INTENT "{intent}"')
    return s.replace("SENSE EEG", head + "SENSE EEG") if head else s


def go(src, **ctx):
    return rsxv.run(rsxv.parse(src), P, dict(CTX, **ctx))


class Language(unittest.TestCase):   # V1
    def test_header_lines_parse_and_round_trip(self):
        p = rsxv.parse(cmd("LEVEL structured\nMEMORY yes\n"))
        self.assertEqual((p["level"], p["memory"]), ("structured", True))
        q = rsxv.parse(lang.to_text(p))
        self.assertEqual((q["level"], q["memory"]), ("structured", True))

    def test_bad_values_refused(self):
        for head in ("LEVEL expert\n", "MEMORY maybe\n"):
            with self.assertRaises(lang.RSXVError):
                rsxv.parse(cmd(head))


class Effective(unittest.TestCase):   # V2, V3
    def test_content_raises_a_lower_declaration(self):
        p = rsxv.parse(cmd("LEVEL self_guided\n", tier=414))
        self.assertEqual(B.effective(p)["level"], "clinician_led")

    def test_cue_program_carries_the_markers(self):
        cue = B.to_cue(rsxv.parse(cmd("LEVEL clinician_led\nMEMORY yes\n")))
        self.assertTrue(cue["source"].startswith("# rsos-level: clinician_led\n# rsos-memory: yes\n"))
        lv = W.level_of_program(cue["source"])
        self.assertTrue(lv["therapist_led"] and lv["memory_work"])
        self.assertEqual((cue["manifest"]["level"], cue["manifest"]["memory"]), ("clinician_led", True))

    def test_plain_command_unchanged(self):   # V7
        cue = B.to_cue(rsxv.parse(DRAGON), pid="dragon")
        self.assertEqual(cue["source"], (HERE / "examples/dragon.cue.rsx").read_text(encoding="utf-8"))
        self.assertEqual(B.effective(rsxv.parse(DRAGON))["level"], "self_guided")


class Next(unittest.TestCase):   # V4
    def test_next_keeps_a_content_level(self):
        p = rsxv.parse(cmd(tier=414))
        r = go(cmd(tier=414), domain="clinical", clinical=True, clinician_present=True, screening_recorded=True)
        self.assertEqual(r["status"], "done")
        nx = rsxv.next_program(p, r)
        self.assertEqual(nx["program"]["level"], "clinician_led")
        self.assertIn("level carried from the parent", nx["notes"])
        self.assertIn("LEVEL clinician_led", nx["text"])

    def test_next_keeps_memory(self):
        src = cmd("MEMORY yes\n")
        nx = rsxv.next_program(rsxv.parse(src), go(src, domain="personal"))
        self.assertTrue(nx["program"]["memory"])
        self.assertIn("MEMORY yes", nx["text"])


class Watchdog(unittest.TestCase):   # V5, V6
    def test_memory_by_domain(self):
        self.assertEqual(go(cmd("MEMORY yes\n"), domain="workplace")["status"], "refused")
        self.assertNotEqual(go(cmd("MEMORY yes\n"), domain="personal")["status"], "refused")

    def test_clinician_led_needs_the_clinical_domain_and_a_clinician(self):
        src = cmd("LEVEL clinician_led\n")
        self.assertEqual(go(src, domain="personal")["status"], "refused")
        self.assertEqual(go(src, domain="clinical", clinical=True)["status"], "refused")
        self.assertNotEqual(go(src, domain="clinical", clinical=True, clinician_present=True, screening_recorded=True)["status"], "refused")

    def test_session_state(self):
        r = go(DRAGON, safety={"mode": "CRISIS", "history": [], "last": None})
        self.assertEqual(r["status"], "refused")
        self.assertTrue(r["log"][-1].startswith("Watchdog:") or any(l.startswith("Watchdog:") for l in r["log"]))

    def test_spine_on_intent_with_folding(self):
        for intent in ("finish with an ice bath", "finish with an іce bath"):
            r = go(cmd(intent=intent))
            self.assertEqual(r["status"], "refused", intent)
            self.assertTrue(any(x["rule"].startswith("spine:") for x in r["watchdog"]["reasons"]))

    def test_plain_command_runs_as_before(self):   # V7
        r = go(DRAGON)
        self.assertNotIn("watchdog", r)
        self.assertEqual(r["status"], "done")



class FixesP2(unittest.TestCase):   # spec/FIXES_P2.md L1, L2
    def test_memory_work_from_content(self):
        from rsxv import translate as T
        for msg in ("Help me relive the accident so I can process it.", "Help me rel\u0456ve the accident so I can process it."):
            prog = T.to_program(msg, tier=8)["program"]
            r = rsxv.run(prog, P, dict(CTX, domain="workplace"))
            self.assertEqual(r["status"], "refused", msg)
            self.assertTrue(B.effective(prog)["memory"])
        src = cmd("MEMORY no\n", intent="reprocess an old memory")
        self.assertEqual(go(src, domain="workplace")["status"], "refused")
        self.assertIn("# rsos-memory: yes", B.to_cue(rsxv.parse(src))["source"])

    def test_domain_normalised_and_unknown_refused(self):
        src = cmd("MEMORY yes\n")
        for d in ("Workplace", "workplace ", " WORKPLACE"):
            self.assertEqual(go(src, domain=d)["status"], "refused", d)
        r = go(DRAGON, domain="workplce")
        self.assertEqual(r["status"], "refused")
        self.assertEqual(r["watchdog"]["reasons"][0]["text"], "unknown domain")

    def test_no_domain_means_personal(self):
        r = go(cmd("LEVEL clinician_led\n"), clinician_present=True, screening_recorded=True)
        self.assertEqual(r["status"], "refused")
        self.assertEqual(go(DRAGON)["status"], "done")


if __name__ == "__main__":
    unittest.main()
