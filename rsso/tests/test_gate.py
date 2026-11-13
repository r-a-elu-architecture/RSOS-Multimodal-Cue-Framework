import copy
import json
import pathlib
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent)]
from rsso import gate as G  # noqa: E402
from rsso import peak as P  # noqa: E402

NODE = shutil.which("node")


def trained(kind="strong", seed=3, captures=8):
    a = P.scenario(kind, seed)["anchor"]
    a["captures"] = a["captures"][:captures]
    return a


def offers_for(aid, n, false_every=0, start=10**6):
    out = []
    for k in range(n):
        G.record_offer(out, aid, start + k * 3600, "not_needed" if false_every and k % false_every == 0 else "helped")
    return out


class Stages(unittest.TestCase):
    def test_climbs_with_evidence(self):
        a = trained()
        self.assertEqual(G.gate(a, [])["stage"], "suggest")          # trained and strong, but no confirmed offers yet
        self.assertIn("Enough confirmed offers", G.gate(a, [])["needs"])
        offs = offers_for(a["id"], 12, false_every=6)
        self.assertEqual(G.gate(a, offs)["stage"], "auto")
        self.assertEqual(G.gate(trained(captures=3), offs)["stage"], "manual")
        self.assertEqual(G.gate(trained("none"), offs)["stage"], "manual")

    def test_false_alarms_and_wear_close_it(self):
        a = trained()
        self.assertEqual(G.gate(a, offers_for(a["id"], 12, false_every=2))["stage"], "suggest")
        worn = copy.deepcopy(a)
        for k in range(30):
            P.add_use(worn, 2 * 10**6 + k, False)
        self.assertEqual(G.wear(worn)["level"], "high")
        self.assertEqual(G.gate(worn, offers_for(a["id"], 12, false_every=6))["stage"], "suggest")

    def test_contamination_and_pressure(self):
        bad = P.scenario("contaminated", 5)["anchor"]
        self.assertEqual(G.gate(bad, offers_for(bad["id"], 12))["stage"], "manual")
        a = trained()
        offs = offers_for(a["id"], 35, false_every=10)
        now = 10**7
        self.assertEqual(G.gate(a, offs, now, {"pressure": True}, {"auto_since": now - 31 * 86400})["stage"], "pressure")
        self.assertEqual(G.gate(a, offs, now, {}, {"auto_since": now - 31 * 86400})["stage"], "auto")

    def test_consent_flag_audit(self):
        a = trained()
        offs = offers_for(a["id"], 12, false_every=6)
        self.assertEqual(G.may_fire(a, "auto", offs, 10**7)["decision"], "deny")
        cons = []
        G.give_consent(cons, "automatic_firing", "person", 100)
        d = G.may_fire(a, "auto", offs, 10**7, consents=cons)
        self.assertEqual(d["decision"], "allow")
        self.assertEqual(d["flag"], "The device fires without asking")
        G.withdraw_consent(cons, "automatic_firing", 200)
        self.assertEqual(G.may_fire(a, "auto", offs, 10**7, consents=cons)["decision"], "deny")
        self.assertEqual(G.may_fire(a, "suggest", offs, 10**7)["decision"], "allow")
        with self.assertRaises(ValueError):
            G.give_consent(cons, "everything", "x", 0)
        log = []
        G.audit(log, 1, "device", "auto", "a", "allow", [], G.flag("automatic_firing"))
        G.audit(log, 2, "person", "suggest", "a", "deny", ["x"])
        s = G.audit_summary(log)
        self.assertEqual((s["entries"], s["automatic"], s["denied"], s["flagged"]), (2, 1, 1, 1))

    def test_simulation_and_results(self):
        ev = G.evaluate(n_each=12)
        self.assertEqual(ev["res"][(True, "none")]["reached_auto"], 0)
        self.assertLess(ev["res"][(True, "none")]["unhelpful_auto"], ev["res"][(False, "none")]["unhelpful_auto"])
        self.assertEqual(ev["res"][(True, "contaminated")]["final_auto"], 0)
        path = HERE.parent / "results" / "gate.md"
        before = path.read_text(encoding="utf-8")
        G.main(["--evaluate"])
        self.assertEqual(path.read_text(encoding="utf-8"), before)


@unittest.skipUnless(NODE, "node not installed")
class Parity(unittest.TestCase):
    def test_python_and_javascript_identical(self):
        cases = []
        for kind in ("strong", "weak", "none", "contaminated"):
            for caps, fe, n in ((8, 6, 12), (3, 0, 0), (10, 2, 25), (8, 10, 40)):
                a = trained(kind, 11, caps)
                offs = offers_for(a["id"], n, fe)
                offs.append({"anchor": a["id"], "ts": 5, "outcome": "ignored", "stage": "suggest"})
                cons = [{"scope": "automatic_firing", "by": "p", "given": 0, "withdrawn": None, "note": ""}] if n % 2 == 0 else []
                cases.append({"anchor": a, "offers": offs, "now": 10**7, "optins": {"pressure": fe == 10}, "history": {"auto_since": 10**7 - 40 * 86400}, "consents": cons})
        worn = trained()
        for k in range(18):
            P.add_use(worn, 2 * 10**6 + k, k % 2 == 0)
        cases.append({"anchor": worn, "offers": [], "now": 0, "optins": {}, "history": {}, "consents": []})
        log = [{"ts": t, "actor": a, "action": x, "anchor": "a", "decision": d, "reasons": [], "flag": f}
               for t, a, x, d, f in ((1, "device", "auto", "allow", "f"), (6, "device", "suggest", None, None), (9, "person", "auto", "deny", None))]
        cs = [{"scope": "night_cueing", "by": "p", "given": 10, "withdrawn": 20, "note": ""}]
        inp = {"cases": cases, "log": log, "consents": [[cs, "night_cueing", 15], [cs, "night_cueing", 25], [cs, "automatic_firing", 15]]}
        js = json.loads(subprocess.run([NODE, str(HERE / "js_gate.js")], input=json.dumps(inp), capture_output=True, text=True, check=True).stdout)
        py = {"cases": [{"gate": G.gate(c["anchor"], c["offers"], c["now"], c["optins"], c["history"]), "wear": G.wear(c["anchor"]),
                         "fa": G.false_alarms(c["offers"], c["anchor"]["id"]),
                         "fire": [G.may_fire(c["anchor"], m, c["offers"], c["now"], c["optins"], c["history"], c["consents"]) for m in ("suggest", "auto", "pressure")]}
                        for c in cases],
              "summary": G.audit_summary(log, 5), "has": [G.has_consent(*x) for x in inp["consents"]]}
        for k in py:
            self.assertEqual(json.loads(json.dumps(py[k])), js[k], k)


if __name__ == "__main__":
    unittest.main()
