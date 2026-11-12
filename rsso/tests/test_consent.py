import json
import pathlib
import shutil
import subprocess
import sys
import unittest
from dataclasses import asdict

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parents[1] / "rsx")]
from rsso import consent as cs  # noqa: E402
from rsso.devices import standard_rig  # noqa: E402
from rsso.runtime import VirtualClock, play  # noqa: E402
from rsx import compile_rsx  # noqa: E402

NODE = shutil.which("node")


def cases():
    base = dict(id="c1", content="When doubt appears, I move", person="me", created_ms=0)
    out = [cs.Consent(**base), cs.Consent(**dict(base, revoked_ms=500)), cs.Consent(**dict(base, expires_ms=800)),
           cs.Consent(**dict(base, content=" ")), cs.Consent(**dict(base, tier="420")),
           cs.Consent(**dict(base, tier="420", therapist_present=True)),
           cs.Consent(**dict(base, tier="420", therapist_present=True, screened_ok=False)),
           cs.Consent(**dict(base, tier="439", therapist_present=True, screened_ok=True)),
           cs.Consent(**dict(base, sound_hz=432.5, content='Say "yes"\nnow', tier="422", author="therapist"))]
    return [(c, now) for c in out for now in (100, 1000)]


class Consent(unittest.TestCase):
    def test_rules(self):
        c = cs.Consent(id="a", content="I move", person="me")
        self.assertEqual(cs.check(c, 0), (True, "ok"))
        self.assertEqual(cs.check(None, 0)[0], False)
        led = cs.Consent(id="b", content="The old pattern ends", person="me", tier="414", therapist_present=True)
        self.assertEqual(cs.check(led, 0), (False, "therapist-led: screening not passed"))
        led.screened_ok = True
        self.assertTrue(cs.check(led, 0)[0])

    def test_program_compiles_and_is_gated(self):
        store = cs.ConsentStore()
        c = store.add(cs.Consent(id="x1", content="I choose calm", person="me", sound_hz=330))
        tl = compile_rsx(cs.cue_program(c))
        self.assertEqual(cs.programmed_ids(tl), ["x1"])
        devs = standard_rig()
        tr = play(tl, devs, VirtualClock(), consents=store)
        self.assertTrue(tr.completed)
        self.assertIn("I choose calm", [a.detail["text"] for d in devs for a in d.actions if a.kind == "speech"])
        store.revoke("x1", 0)
        self.assertFalse(play(tl, standard_rig(), VirtualClock(), consents=store, now_ms=1).started)
        self.assertIn('"cues"', store.to_json())

    def test_plain_programs_unaffected(self):
        tl = compile_rsx((HERE.parents[1] / "rsx/protocols/override.rsx").read_text(encoding="utf-8"))
        self.assertTrue(play(tl, standard_rig(), VirtualClock(), consents=None).completed)


@unittest.skipUnless(NODE, "node not installed")
class Parity(unittest.TestCase):
    def test_python_and_js_identical(self):
        cc = cases()
        progs = [c for c, _ in cc[::2]]
        out = json.loads(subprocess.run([NODE, str(HERE / "js_consent.js")], capture_output=True, text=True, check=True,
                                        input=json.dumps(dict(cases=[dict(c=asdict(c), now=n) for c, n in cc], progs=[asdict(c) for c in progs]))).stdout)
        for (c, n), j in zip(cc, out["checks"]):
            self.assertEqual(list(cs.check(c, n)), j, (c, n))
        for c, j in zip(progs, out["progs"]):
            self.assertEqual(cs.cue_program(c, 4, 6), j)


if __name__ == "__main__":
    unittest.main()
