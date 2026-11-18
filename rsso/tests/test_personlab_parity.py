"""spec/PERSONLAB.md §7d C: the browser's Person Lab engine (docs/js/personlab.js) equals Python (rsxv.personlab.lab)
for all 100 lab persons, three policies and two effect sets; and the published population summary matches."""
import json
import pathlib
import shutil
import subprocess
import sys
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "rsxv"))
from rsxv.personlab import lab as LB  # noqa: E402

NODE = shutil.which("node")
MIRRORS = json.loads((REPO / "docs/data/personlab_persons.json").read_text(encoding="utf-8"))
LAB = json.loads((REPO / "docs/data/personlab_lab.json").read_text(encoding="utf-8"))
JS = """
const L = require(process.argv[1]); const fs = require('fs');
const lab = JSON.parse(fs.readFileSync(process.argv[2], 'utf8')); const M = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const out = {sessions: [], population: L.population(lab, M.persons)};
M.persons.forEach((p, n) => { for (const eff of Object.keys(lab.effects)) for (const pol of L.POLICIES)
  out.sessions.push(L.session(lab, p, n + 1, pol, eff)); });
process.stdout.write(JSON.stringify(out));
"""


@unittest.skipUnless(NODE, "Node.js not installed")
class Parity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        r = subprocess.run([NODE, "-e", JS, str(REPO / "docs/js/personlab.js"), str(REPO / "docs/data/personlab_lab.json"),
                            str(REPO / "docs/data/personlab_persons.json")], capture_output=True, text=True, check=True)
        cls.js = json.loads(r.stdout)

    def test_every_session_tick_equal(self):
        i = 0
        for n, p in enumerate(MIRRORS["persons"]):
            for eff in LB.EFFECTS:
                for pol in LB.POLICIES:
                    py, js = LB.session(p, n + 1, pol, eff), self.js["sessions"][i]
                    i += 1
                    self.assertEqual(len(py["ticks"]), len(js["ticks"]))
                    for a, b in zip(py["ticks"], js["ticks"]):
                        for k in ("t", "action", "archetype", "target", "cue", "feedback", "spike"):
                            self.assertEqual(a[k], b[k], (p["id"], pol, eff, a["t"], k))
                        for k in ("I", "u", "k", "g", "score"):
                            self.assertAlmostEqual(a[k], b[k], delta=1e-6, msg=(p["id"], pol, eff, a["t"], k))
        self.assertEqual(i, 600)

    def test_population_equal_to_published(self):
        for eff, s in LAB["population"].items():
            self.assertEqual(s["agents_vs_bear"], self.js["population"][eff]["agents_vs_bear"])
            for pol in LB.POLICIES:
                for k, v in s[pol].items():
                    self.assertAlmostEqual(v, self.js["population"][eff][pol][k], delta=1e-4, msg=(eff, pol, k))

    def test_published_data_reproduces(self):
        self.assertEqual(LB.build(MIRRORS), LAB)


if __name__ == "__main__":
    unittest.main()
