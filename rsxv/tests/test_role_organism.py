"""spec/ROLE_ORGANISM.md R1-R6."""
import json
import pathlib
import re
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path[:0] = [str(REPO / "architecture")]
import bindings as B  # noqa: E402
import organism as O  # noqa: E402
from rsxv import roles  # noqa: E402
from rsxv.personlab import organism_plan as P  # noqa: E402

PERSONS = json.loads((REPO / "docs/data/personlab_persons.json").read_text(encoding="utf-8"))["persons"]
TMAP = json.loads((REPO / "docs/data/tier_map.json").read_text(encoding="utf-8"))
ORG = json.loads((REPO / "docs/data/organism.json").read_text(encoding="utf-8"))
_R1 = {}


def r1():
    if not _R1:
        _R1.update(roles.experiment())
    return _R1


class R1Sensors(unittest.TestCase):
    def test_five_roles_have_their_own_sensor(self):
        d = r1()["diagonal"]
        self.assertEqual([r for r, v in d.items() if not v["ok"]], ["Baseline"])   # observed; recorded in §4

    @unittest.expectedFailure
    def test_r1_registered(self):
        """Registered: 6 of 6. Observed 5 of 6 (Baseline: Drive scores higher). Recorded in spec/ROLE_ORGANISM.md §4."""
        self.assertTrue(r1()["R1"])


class R2Bindings(unittest.TestCase):
    def test_proposals(self):
        d = B.build()
        c = d["counts"]
        self.assertEqual(c["unbound"], 186)
        self.assertGreaterEqual(c["rule"] / c["unbound"], 0.80)
        for t, v in d["tiers"].items():
            self.assertFalse(v["confirmed"])
            self.assertEqual(bool(v["matched"]), v["method"] == "rule", t)
        self.assertEqual(sum(1 for v in TMAP["tiers"].values() if not v.get("response")), 186)   # tier_map unchanged

    def test_file_reproducible(self):
        on_disk = json.loads((REPO / "docs/data/bindings_proposed.json").read_text(encoding="utf-8"))
        self.assertEqual(on_disk, json.loads(json.dumps(B.build(), ensure_ascii=False, sort_keys=True)))


class R3RoleProfiles(unittest.TestCase):
    def test_six_complete(self):
        rp = ORG["role_profiles"]
        self.assertEqual(sorted(rp), sorted(O.ROLES))
        for r, v in rp.items():
            for k in ("archetype", "tacton", "sensor", "responses", "built_tiers", "proposed_tiers", "top_metrics"):
                self.assertIn(k, v, r)
        self.assertGreaterEqual(len(rp["Baseline"]["proposed_tiers"]), 1)


class R4R5Plans(unittest.TestCase):
    def test_every_person(self):
        plans = [P.plan(p, ORG, TMAP) for p in PERSONS]
        self.assertEqual(len(plans), 100)
        self.assertEqual([b for pl in plans for b in P.validate(pl, TMAP)], [])
        for p, pl in zip(PERSONS, plans):
            missing = [l for l in P.LEVELS if l not in p["levels"]]
            self.assertEqual([q["level"] for q in pl["intake_questions"] if q["level"] != "desired"], missing)
            self.assertEqual(any(q["level"] == "desired" for q in pl["intake_questions"]), not p["desired"])
            self.assertEqual(pl, P.plan(p, ORG, TMAP))
        c = [x for pl in plans for x in pl["candidates_per_step"]]
        self.assertLessEqual(sum(c) / len(c), 29.3)


class R6Wording(unittest.TestCase):
    def test_new_texts(self):
        import ast
        crisis = re.compile(r"\b(?:crisis|suicid\w*|self-harm|harming yourself|helpline|emergency services|not wanting to live|"
                            r"at risk of harm|emergency)\b", re.I)          # as rsso/tests/test_linx_mcp.py L6
        src = (REPO / "rsx" / "tests" / "test_roadmap.py").read_text(encoding="utf-8")
        line = next(x for x in src.splitlines() if x.startswith("EXCLUDED = "))
        excluded = [re.compile(p, 0 if any(c.isupper() for c in p) else re.I)
                    for p in ast.literal_eval(line.split("=", 1)[1].strip())]
        texts = list(P.QUESTION.values()) + list(P.STEP_WHY.values())
        for t in texts:
            self.assertIsNone(crisis.search(t), t)
            self.assertFalse(any(x.search(t) for x in excluded), t)


if __name__ == "__main__":
    unittest.main()
