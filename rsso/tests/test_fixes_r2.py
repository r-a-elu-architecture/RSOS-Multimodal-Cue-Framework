"""FIXES_R2 (spec/FIXES_R2.md): each test reproduces a finding of the repeat review (review/r2, 557c3fa)."""
import copy
import json
import pathlib
import re
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE.parent), str(HERE)]
from rsso import cm1 as CM, contribution as C, memstack as MS, trial as T  # noqa: E402
from test_contribution import inputs as contribution_inputs  # noqa: E402
from test_trial_loop import feed, sim_trial  # noqa: E402

NODE = shutil.which("node")


def session(design, arm, detail=None):
    tr = {"design": design, "seed": 1}
    s = {"i": 0, "arm": arm, "ts": 5, "before": 4, "after": 6, "cov": {}}
    if detail:
        s["detail"] = detail
    return tr, s


EVIDENCE = [session("anchor_vs_sham", "anchor"), session("anchor_vs_sham", "sham", {"code_kind": "sham", "code": "-..-"}),
            session("cue_vs_none", "cue"), session("cue_vs_none", "cue", {"code_kind": "anchor", "code": "..-"}),
            session("auto_vs_manual", "auto"), session("ssit", "higher", {"code": "x"})]
SHAM = [[seed, k, c] for seed in (-2 ** 40, -12345, -1, 0, 7, 2 ** 31) for k in range(4) for c in ("..-", None)]


class Fixes(unittest.TestCase):
    def test_r2_2_guard_passes_every_watchdog_key(self):
        wd = set(re.findall(r'x\.get\("(\w+)"', (ROOT / "rsso" / "rsso" / "watchdog.py").read_text(encoding="utf-8")))
        g = (ROOT / "docs" / "js" / "guard.js").read_text(encoding="utf-8")
        ctx = g[g.index("const ctx = {"):g.index("};", g.index("const ctx = {"))]
        keys = set(re.findall(r"(\w+):", ctx))
        self.assertEqual(sorted(wd - keys), [])

    def test_r2_6_evidence_needs_a_played_code(self):
        r = [T.evidence(tr, s) for tr, s in EVIDENCE]
        self.assertEqual(r[0], {"probe": None, "use": None})                 # saved without playing
        self.assertEqual(r[1]["probe"]["kind"], "sham")
        self.assertEqual(r[2], {"probe": None, "use": None})
        self.assertEqual(r[3]["use"], {"ts": 5, "during_stress": True})
        self.assertEqual(r[4]["use"], {"ts": 5, "during_stress": True})      # the person fires the anchor either way
        self.assertEqual(r[5], {"probe": None, "use": None})

    def test_r2_7_memstack_cm1_unchanged_by_trials(self):
        inp = contribution_inputs()[1]
        runs = copy.deepcopy(inp["runs"])
        before = (MS.summarize(copy.deepcopy(runs), inp["srbai"]), CM.signature(copy.deepcopy(runs)))
        trials = [sim_trial("anchor_vs_sham", 31, 2.0), sim_trial("cue_vs_none", 32, 1.0)]
        for tr in trials:
            feed(tr)
        inp["trials"] = trials
        C.build(inp)
        after = (MS.summarize(copy.deepcopy(inp["runs"]), inp["srbai"]), CM.signature(copy.deepcopy(inp["runs"])))
        self.assertEqual(inp["runs"], runs)
        self.assertEqual(after, before)

    def test_r2_8_trials_scope_opt_in(self):
        page = (ROOT / "docs" / "contribute.html").read_text(encoding="utf-8")
        default_on = re.search(r"const DEFAULT_ON = \[([^\]]*)\]", page).group(1)
        self.assertNotIn('"trials"', default_on)


@unittest.skipUnless(NODE, "node not installed")
class Parity(unittest.TestCase):
    def test_q2(self):
        r = subprocess.run([NODE, str(HERE / "js_fixes_r2.js")], input=json.dumps({"sham": SHAM, "evidence": EVIDENCE}),
                           capture_output=True, text=True, check=True)
        js = json.loads(r.stdout)
        self.assertEqual(js["sham"], [T.sham_code({"seed": s}, k, c) for s, k, c in SHAM])
        self.assertEqual(js["evidence"], [T.evidence(tr, s) for tr, s in EVIDENCE])


if __name__ == "__main__":
    unittest.main()
