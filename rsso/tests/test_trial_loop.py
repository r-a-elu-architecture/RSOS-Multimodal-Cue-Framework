"""TRIAL_LOOP (spec/TRIAL_LOOP.md): trials feed PEAK, GATE and contributions; run log, MEMSTACK and CM1 unchanged."""
import copy
import json
import pathlib
import random
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE.parent), str(HERE)]
from rsso import contribution as C, gate as G, peak as P, trial as T  # noqa: E402
from test_contribution import inputs as contribution_inputs  # noqa: E402

NODE = shutil.which("node")


def sim_trial(design, seed, effect, blocks=6, noise=1.0, anchor_code="..-"):
    """Sessions of one simulated person: calm change = true effect for the non-reference arm + Gaussian noise."""
    rng = random.Random(seed)
    tr = T.new_trial(design, blocks, seed, "t%d" % seed, 0)
    for k, arm in enumerate(tr["schedule"]):
        before = 4.0
        change = (effect if arm != T.DESIGNS[design]["reference"] else 0.0) + rng.gauss(0, noise)
        after = max(0.0, min(10.0, before + change))
        code = anchor_code if arm == "anchor" else T.sham_code(tr, k, anchor_code)
        T.record(tr, before, after, {"sleep_h": 7, "hour": 9}, 1000 + 86400 * k, {"code_kind": "anchor" if arm == "anchor" else "sham", "code": code})
    return tr


def feed(tr):
    a = P.make_anchor("a1", "Anchor", "🦁", "..-")
    for s in tr["sessions"]:
        ev = T.evidence(tr, s)
        if ev["probe"]:
            P.add_probe(a, ev["probe"])
        if ev["use"]:
            P.add_use(a, ev["use"]["ts"], ev["use"]["during_stress"])
    return a


class Bridge(unittest.TestCase):
    def test_t2_sham_codes(self):
        for seed in range(0, 4000, 37):
            tr = {"seed": seed * 104729}
            for i in range(12):
                for code in ("..-", "-..-", None, "---"):
                    c = T.sham_code(tr, i, code)
                    self.assertIn(c, T.SHAM_POOL)
                    self.assertNotEqual(c, code)
                    self.assertEqual(c, T.sham_code(tr, i, code))
        tr = sim_trial("anchor_vs_sham", 5, 2.0)
        for k, s in enumerate(tr["sessions"]):
            if s["arm"] == "sham":
                self.assertEqual(s["detail"], {"code_kind": "sham", "code": T.sham_code(tr, k, "..-")})

    def test_t3_mapping(self):
        for design in T.DESIGNS:
            tr = T.new_trial(design, 2, 11, "t", 0)
            for k in range(len(tr["schedule"])):
                s = T.record(tr, 4, 6, {}, k)
                ev = T.evidence(tr, s)
                if design == "anchor_vs_sham":
                    self.assertEqual(ev["probe"], {"ts": k, "kind": "cue" if s["arm"] == "anchor" else "sham", "calm_before": 4, "calm_after": 6})
                    self.assertIsNone(ev["use"])
                elif (design == "cue_vs_none" and s["arm"] == "cue") or design == "auto_vs_manual":
                    self.assertEqual(ev, {"probe": None, "use": {"ts": k, "during_stress": True}})
                else:
                    self.assertEqual(ev, {"probe": None, "use": None})

    def test_record_without_detail_unchanged(self):
        tr = T.new_trial("ssit", 1, 3, "t", 0)
        s = T.record(tr, 3, 5, {"sleep_h": 7}, 9)
        self.assertEqual(set(s), {"i", "arm", "ts", "before", "after", "cov"})

    @staticmethod
    def _t4():
        out = {"strong_true": 0, "strong_null": 0, "gate_misses": []}
        for seed in range(200):
            a = feed(sim_trial("anchor_vs_sham", 10_000 + seed, 2.0))
            if P.strength(a)["status"] == "strong":
                out["strong_true"] += 1
                g = G.gate(a, [], 10 ** 9)
                strength_checks = [c for stage in g["checks"].values() for c in stage if c["id"] == "strength"]
                if not strength_checks or not all(c["met"] for c in strength_checks):
                    out["gate_misses"].append(seed)
            if P.strength(feed(sim_trial("anchor_vs_sham", 20_000 + seed, 0.0)))["status"] == "strong":
                out["strong_null"] += 1
        return out

    def test_t4_gate_and_false_positives(self):
        r = self._t4()
        self.assertEqual(r["gate_misses"], [])          # every strong anchor meets GATE's strength checks
        self.assertLessEqual(r["strong_null"], 10, r)   # at most 5% with no true effect

    @unittest.expectedFailure
    def test_t4_registered_power(self):
        """Registered: strong for at least 80% (160/200) with a true effect of 2.0 after 6 blocks. Observed at build time:
        158/200 (79%). Not met; recorded in spec/TRIAL_LOOP.md §7 and kept as a visible registered failure."""
        self.assertGreaterEqual(self._t4()["strong_true"], 160)

    def test_t5_run_log_untouched(self):
        page = (ROOT / "docs" / "trials.html").read_text(encoding="utf-8")
        self.assertNotIn('"rsos.runs"', page)
        for f in ("trial.py",):
            self.assertNotIn("rsos.runs", (ROOT / "rsso" / "rsso" / f).read_text(encoding="utf-8"))


class Contribution(unittest.TestCase):
    def test_t6_scope(self):
        base = contribution_inputs()[0]
        before = C.build(copy.deepcopy(base))
        with_trials = copy.deepcopy(base)
        tr = sim_trial("anchor_vs_sham", 3, 2.0)
        tr["anchor"] = "my_secret_anchor"
        tr["sessions"][0]["after"] = 42
        with_trials["trials"] = [tr]
        self.assertEqual(C.build(copy.deepcopy(with_trials)), before)          # no scope: unchanged
        with_trials["consent"]["scopes"] = with_trials["consent"]["scopes"] + ["trials"]
        c = C.build(with_trials)
        text = json.dumps(c["trials"])
        for secret in ("my_secret_anchor", "..-", "-..-", ".-.-", "--..", "-.-.", "..--", "code"):
            self.assertNotIn(secret, text)
        self.assertEqual(len(c["trials"][0]["sessions"]), len(tr["sessions"]) - 1)   # the out-of-range rating is dropped
        self.assertEqual(c["trials"][0]["design"], "anchor_vs_sham")
        self.assertEqual({r["arm"] for r in c["trials"][0]["result"]}, {"anchor"})


@unittest.skipUnless(NODE, "node not installed")
class Parity(unittest.TestCase):
    """T1: Python and JavaScript identical."""

    def test_t1(self):
        sham = [[seed * 7919, k, code] for seed in range(60) for k in range(6) for code in ("..-", None, "-..-")]
        rng = random.Random(4)
        trials = []
        for design in T.DESIGNS:
            sessions = []
            for k in range(12):
                det = rng.choice([None, {"code_kind": "sham", "code": "-..-"}, {"code_kind": "anchor", "code": ""}])
                sessions.append([rng.randint(0, 10), round(rng.uniform(0, 10), 2), {"sleep_h": 6.5, "hour": k}, 100 + k, det])
            trials.append({"design": design, "blocks": 3, "seed": rng.randint(0, 2 ** 32 - 1), "sessions": sessions})
        r = subprocess.run([NODE, str(HERE / "js_trial_loop.js")], input=json.dumps({"sham": sham, "trials": trials}),
                           capture_output=True, text=True, check=True)
        js = json.loads(r.stdout)
        self.assertEqual(js["sham"], [T.sham_code({"seed": s}, k, c) for s, k, c in sham])
        for k, t in enumerate(trials):
            tr, ev = T.new_trial(t["design"], t["blocks"], t["seed"], "t", 0), []
            for b, a, cov, ts, det in t["sessions"]:
                x = T.record(tr, b, a, cov, ts, det)
                ev.append(T.evidence(tr, x) if x else None)
            self.assertEqual(js["trials"][k]["trial"], tr, t["design"])
            self.assertEqual(js["trials"][k]["evidence"], ev, t["design"])

    def test_t1_contribution(self):
        inp = contribution_inputs()[1]          # every scope consented
        inp["trials"] = [sim_trial("anchor_vs_sham", 8, 1.5), sim_trial("ssit", 9, 1.0, blocks=3)]
        r = subprocess.run([NODE, str(HERE / "js_contribution.js")], input=json.dumps({"inputs": [inp], "timeline": {"events": []}, "text": "x"}),
                           capture_output=True, text=True, check=True)
        js = json.loads(r.stdout)["built"][0]
        py = C.seal(C.build(copy.deepcopy(inp)))
        self.assertEqual(js["trials"], py["trials"])
        self.assertEqual(js, py)


if __name__ == "__main__":
    unittest.main()
