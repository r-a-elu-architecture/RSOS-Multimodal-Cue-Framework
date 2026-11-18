"""spec/WHOLE_ORGANISM.md W1-W5."""
import json
import pathlib
import sys
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / "architecture"), str(REPO / "rsx"), str(REPO / "rsso"), str(REPO / "rsxv")]
import glyph_proposals as GP  # noqa: E402
import organism as O  # noqa: E402
import tier_extension as X  # noqa: E402
from rsx import compile_rsx  # noqa: E402
from rsso.devices import standard_rig  # noqa: E402
from rsso.runtime import play  # noqa: E402
from rsxv import organism_env as E  # noqa: E402

PROGRAMS = REPO / "rsx" / "protocols" / "responses"
_W = {}


def w(k):
    if k not in _W:
        _W[k] = E.w1() if k == "w1" else E.w4()
    return _W[k]


def program_for(tier, tmap, ext):
    resp = tmap[tier].get("response") or ext.get(tier, {}).get("response")
    if not resp:
        resp = O.ROLES[ext[tier]["role"]]["responses"][0]      # bound by role only: the role's first response
    return PROGRAMS / f"{resp.lower()}.rsx"


class Whole(unittest.TestCase):
    def test_w1_baseline_now_has_a_sensor(self):
        d = w("w1")["diagonal"]
        self.assertTrue(d["Baseline"]["ok"])
        self.assertEqual([r for r, v in d.items() if not v["ok"]], ["Repair"])      # observed; spec §4

    @unittest.expectedFailure
    def test_w1_registered(self):
        """Registered: 6 of 6. Observed 5 of 6: the return to the origin also fixes modules, so Repair loses its signature."""
        self.assertTrue(w("w1")["W1"])

    def test_w2_every_response_runs(self):
        files = sorted(PROGRAMS.glob("*.rsx"))
        self.assertEqual(len(files), 14)
        self.assertEqual({f.stem.upper() for f in files}, set(O.ROLE_OF))
        for f in files:
            t = compile_rsx(f.read_text(encoding="utf-8"))
            rig = standard_rig()
            tr = play(t, rig)
            self.assertTrue(tr.started and tr.completed, f.name)
            amps = [a.detail.get("amp", 0) for d in rig for a in d.actions if d.name == "haptic"]
            self.assertTrue(amps and max(amps) <= 0.4, f.name)

    def test_w3_every_tier_runs(self):
        tmap = O.load("docs/data/tier_map.json")["tiers"]
        ext = X.load()["bindings"]
        self.assertEqual(sum(1 for t in tmap if program_for(t, tmap, ext).exists()), 293)

    def test_w4_measured(self):
        r = w("w4")
        self.assertAlmostEqual(r["v3"]["ORGANISM_minus_BEAR"]["estimate"], -0.020061825925925928)
        self.assertAlmostEqual(r["v2"]["ORGANISM_minus_BEAR"]["estimate"], 0.014594214814814807)

    @unittest.expectedFailure
    def test_w4_registered(self):
        """Registered: >= +0.088 on V3. Observed -0.0201 (V2 +0.0146): the return to the origin did not help the whole."""
        self.assertTrue(w("w4")["W4"])

    def test_glyph_proposals_file(self):
        on_disk = json.loads((REPO / GP.OUT).read_text(encoding="utf-8"))
        self.assertEqual(on_disk, json.loads(json.dumps(GP.build(), ensure_ascii=False, sort_keys=True)))
        self.assertEqual({a: v["chosen_by_author"] for a, v in on_disk["proposals"].items()}, GP.CHOSEN)


if __name__ == "__main__":
    unittest.main()
