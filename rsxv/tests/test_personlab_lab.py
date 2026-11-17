"""spec/PERSONLAB.md §7d: RSX-V TARGET, the public lab persons (generated from summary statistics, §7d-B′) and the session engine."""
import json
import pathlib
import random
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "rsso"))
import rsxv  # noqa: E402
from rsxv import lang, sim  # noqa: E402
from rsxv.personlab import lab as LB, schema as S, synth as SY  # noqa: E402
from rsxv.personlab.mirror_bank import BANK, DETAILS, SIGNALS, TYPES  # noqa: E402

DRAGON = (HERE / "examples/dragon.rsxv").read_text(encoding="utf-8")
MIRRORS = json.loads((HERE.parent / "docs/data/personlab_persons.json").read_text(encoding="utf-8"))
AGG = json.loads((HERE / "results/personlab_aggregates.json").read_text(encoding="utf-8"))
PERSONS = MIRRORS["persons"]


def with_target(t="skills:k1"):
    return DRAGON.replace("SENSE EEG", f"TARGET {t}\nSENSE EEG")


class Target(unittest.TestCase):   # §7d A
    def test_parse_and_round_trip(self):
        p = rsxv.parse(with_target())
        self.assertEqual(p["target"], {"level": "skills", "node": "k1"})
        t = lang.to_text(p)
        self.assertIn("TARGET skills:k1", t)
        self.assertEqual(rsxv.parse(t)["target"], p["target"])

    def test_without_target_unchanged(self):
        p = rsxv.parse(DRAGON)
        self.assertIsNone(p["target"])
        self.assertNotIn("TARGET", lang.to_text(p))

    def test_malformed_rejected(self):
        for bad in ("k1", "mood:k1", "skills:k 1", "skills:", "skills k1"):
            with self.assertRaises(lang.RSXVError, msg=bad):
                rsxv.parse(with_target(bad))

    def test_next_keeps_target(self):
        src = with_target("beliefs:v2")
        r = rsxv.run(rsxv.parse(src), sim.person(random.Random(3), 0),
                     {"seed": 5, "now_min": 600, "consent": ["subject", "operator", "auditor"], "domain": "personal"})
        nx = rsxv.next_program(rsxv.parse(src), r)
        self.assertEqual(nx["program"]["target"], {"level": "beliefs", "node": "v2"})
        self.assertIn("TARGET beliefs:v2", nx["text"])


class LabPersons(unittest.TestCase):   # §7d-B′ (the overlap check runs privately; its result is published in the file)
    def test_one_hundred_valid_invented_persons(self):
        self.assertEqual(len(PERSONS), 100)
        self.assertEqual([p["id"] for p in PERSONS], [f"lab-{i:03d}" for i in range(1, 101)])
        self.assertEqual({t: sum(p["problem_type"] == t for p in PERSONS) for t in TYPES}, {t: 25 for t in TYPES})
        for p in PERSONS:
            self.assertEqual(S.validate(p), [], p["id"])
            self.assertTrue(p["invented"])
            self.assertNotRegex(json.dumps(p).lower(), r"esconv-\d")   # no private document id
            self.assertIn(p["initial_intensity"], (1.0, 2.0, 3.0, 4.0, 5.0))

    def test_open_licence_and_citation(self):
        self.assertTrue(MIRRORS["licence"].startswith("CC BY 4.0"))
        self.assertNotIn("NC", MIRRORS["licence"].replace("ESConv", ""))
        self.assertIn("Liu", MIRRORS["citation"])

    def test_generated_from_the_published_aggregates_alone(self):
        self.assertEqual(SY.build(AGG, MIRRORS["check"]), MIRRORS)

    def test_aggregates_are_counts_only(self):
        A = AGG["aggregates"]
        self.assertEqual(A["n"], 100)
        def leaves(x):
            if isinstance(x, dict):
                for v in x.values():
                    yield from leaves(v)
            elif isinstance(x, list):
                for v in x:
                    yield from leaves(v)
            else:
                yield x
        self.assertTrue(all(isinstance(v, int) for v in leaves(A)))
        self.assertEqual(sum(A["initial_intensity"].values()), 100)
        for lv in S.LEVEL_IDS:
            self.assertEqual(sum(A["statements_per_level"][lv].values()), 100)

    def test_every_text_comes_from_the_invented_bank(self):
        bank = {x for ty in BANK.values() for lv in ty.values() for e in lv for x in e}
        bank |= {x for ty in DETAILS.values() for k in ty.values() for x in k} | set(SIGNALS.values())
        for p in PERSONS:
            for t in SY.texts(p):
                self.assertIn(t, bank, p["id"])

    def test_check_published(self):
        c = MIRRORS["check"]
        self.assertEqual((c["persons"], c["schema_valid"]), (100, 100))
        self.assertEqual((c["shared_4gram_with_profiles"], c["shared_4gram_with_input_text"]), (0, 0))


class Engine(unittest.TestCase):   # §7d C
    def test_every_program_parses_for_every_node(self):
        n = 0
        for p in PERSONS:
            for lv, node in LB.target_nodes(p):
                for a in LB.PROGRAMS:
                    prog = rsxv.parse(LB.program(a, f"{lv}:{node}"))
                    self.assertEqual(prog["target"], {"level": lv, "node": node})
                    self.assertEqual(prog["archetype"], LB.ARCH[a])
                    n += 1
        self.assertGreater(n, 400)

    def test_same_seed_same_run(self):
        a = LB.session(PERSONS[3], 4, "agents", "illustrative")
        b = LB.session(PERSONS[3], 4, "agents", "illustrative")
        self.assertEqual(a, b)
        self.assertNotEqual(a, LB.session(PERSONS[3], 5, "agents", "illustrative"))

    def test_placeholder_tie_and_illustrative_difference(self):   # expected by construction (§7d C)
        pop = LB.population(PERSONS)
        self.assertEqual(pop["placeholder"]["agents_vs_bear"], {"more_progress": 0, "same": 100, "less_progress": 0})
        self.assertEqual(pop["placeholder"]["agents"], pop["placeholder"]["always_bear"])
        self.assertGreater(pop["illustrative"]["agents"]["mean_final_g"], pop["illustrative"]["always_bear"]["mean_final_g"])

    def test_bear_while_aroused(self):
        p = dict(PERSONS[0], initial_intensity=5.0)
        rows = LB.session(p, 1, "agents", "illustrative")["ticks"]
        self.assertEqual(rows[0]["archetype"], "BEAR")
        for r in rows:
            self.assertIsNotNone(r["target"])

    def test_targets_are_nodes_of_the_person(self):
        for p in PERSONS:
            ids = {st["id"] for n in p["levels"].values() for st in n["statements"]} | {"all"}
            for lv, node in LB.target_nodes(p):
                self.assertIn(lv, S.LEVEL_IDS)
                self.assertIn(node, ids)


if __name__ == "__main__":
    unittest.main()
