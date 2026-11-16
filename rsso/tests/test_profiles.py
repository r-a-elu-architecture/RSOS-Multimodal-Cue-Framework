"""PROFILES (spec/PROFILES.md): domain profiles change what people see, never what the engine does."""
import html
import json
import pathlib
import re
import shutil
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE.parent)]
from rsso import profiles as P  # noqa: E402

NODE = shutil.which("node")
IN_SCOPE = ["index", "player", "nodes", "therapist", "contribute", "night", "safety", "world", "metrics", "anchors",
            "identity", "atlas", "trials", "device", "agents"]
EXTRA = ["PTSD or trauma", "Depression", "Anxiety", "Chronic stress", "Symptoms and what they feel like",
         "A therapist, with the client", "Distress (0 none – 10 worst)", "Distress drop per run: 2.1",
         "it lowered your distress by 1.5 on average", "Rate distress before and after in the player.",
         "An open protocol for interrupting a negative state.", "SUD 7", "a distressing memory", "panic attacks",
         "the client's plan", "Clients and therapists", "patient", "I am in therapy while practising",
         "Whether practice changes depression, anxiety, trauma symptoms, stress and wellbeing over weeks.",
         "How RSOS works inside therapy: sessions, fidelity, clinician ratings.", "Observer work with trauma memories is therapist-led"]


def _strings(o, out):
    if isinstance(o, str):
        out.append(o)
    elif isinstance(o, dict):
        for v in o.values():
            _strings(v, out)
    elif isinstance(o, list):
        for v in o:
            _strings(v, out)
    return out


def _visible(name):
    t = (ROOT / "docs" / f"{name}.html").read_text(encoding="utf-8")
    t = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>|<nav[\s\S]*?</nav>|<pre[\s\S]*?</pre>|<textarea[\s\S]*?</textarea>", " ", t)
    t = re.sub(r"<[^>]*data-show=\"clinical\"[\s\S]*?<!-- /clinical -->", " ", t)
    return [s.strip() for s in html.unescape(re.sub(r"<[^>]+>", "\n", t)).split("\n") if s.strip()]


def corpus():
    c = _strings(json.loads((ROOT / "docs" / "data" / "thera.json").read_text(encoding="utf-8")), [])
    for n in IN_SCOPE:
        c += _visible(n)
    return sorted(set(c + EXTRA))


CORPUS = corpus()


class Profiles(unittest.TestCase):
    def test_shape(self):
        self.assertEqual(P.IDS, ["personal", "coaching", "performance", "learning", "research", "workplace", "clinical"])
        for k, row in P.TERMS.items():
            self.assertEqual(sorted(row), sorted(P.IDS), k)

    def test_p2_no_clinical_words(self):
        bad = []
        for p in P.IDS:
            for on in (False, True):
                if P.clinical_vocab(p, on):
                    continue
                bad += [f"{p}: {P.text(s, p, on)!r}" for s in CORPUS if P.has_clinical_words(P.text(s, p, on))]
                bad += [f"{p} term {k}" for k in P.TERMS if P.has_clinical_words(P.term(k, p, on))]
        self.assertEqual(bad, [])

    def test_p3_clinical_identity(self):
        for s in CORPUS:
            self.assertEqual(P.text(s, "clinical"), s)
            self.assertEqual(P.text(s, "research", True), s)
        self.assertTrue(P.clinical_vocab("research", True))
        self.assertFalse(P.clinical_vocab("research", False))

    def test_p4_engine_untouched(self):
        for f in (ROOT / "rsso" / "rsso").glob("*.py"):
            if f.name != "profiles.py":
                self.assertNotRegex(f.read_text(encoding="utf-8"), r"import\s+profiles|from\s+\.?\s*profiles|profiles\s+as\s|import[^\n]*\bprofiles\b", f.name)
        for f in (ROOT / "docs" / "js").glob("*.js"):
            if f.name != "profiles.js":
                self.assertNotIn("RSOSProfiles", f.read_text(encoding="utf-8"), f.name)
        js = (ROOT / "docs" / "js" / "profiles.js").read_text(encoding="utf-8")
        self.assertEqual(set(re.findall(r"localStorage\.setItem\((\w+)", js)), {"KEY"})
        self.assertIn('const KEY = "rsos.profile"', js)

    def test_p5_idempotent(self):
        for p in P.IDS:
            for s in CORPUS:
                once = P.text(s, p)
                self.assertEqual(P.text(once, p), once, (p, s))

    def test_examples(self):
        self.assertEqual(P.text("PTSD or trauma", "performance"), "Past setbacks")
        self.assertEqual(P.text("A therapist, with the client", "research"), "An investigator, with the participant")
        self.assertEqual(P.text("Clients and therapists", "learning"), "Learners and teachers")
        self.assertEqual(P.text("Distress drop per run", "workplace"), "Pressure drop per run")
        self.assertEqual(P.text("from 0 (calm) to 10 (the most distress)", "performance"), "from 0 (calm) to 10 (the highest tension)")
        self.assertEqual(P.text("x", "nonsense"), "x")


@unittest.skipUnless(NODE, "node not installed")
class Parity(unittest.TestCase):
    """P1: Python and JavaScript identical."""

    def test_p1(self):
        r = subprocess.run([NODE, str(HERE / "js_profiles.js")], input=json.dumps({"corpus": CORPUS}),
                           capture_output=True, text=True, check=True)
        js = json.loads(r.stdout)
        self.assertEqual(js["profiles"], P.PROFILES)
        self.assertEqual(js["terms"], P.TERMS)
        self.assertEqual(js["exempt"], P.EXEMPT_PAGES)
        self.assertEqual(js["flags"], [P.has_clinical_words(c) for c in CORPUS])
        for p in P.IDS:
            for on in (False, True):
                k = f"{p}:{'true' if on else 'false'}"
                self.assertEqual(js["vocab"][k], P.clinical_vocab(p, on), k)
                self.assertEqual(js["term"][k], [P.term(t, p, on) for t in P.TERMS], k)
                self.assertEqual(js["text"][k], [P.text(c, p, on) for c in CORPUS], k)


if __name__ == "__main__":
    unittest.main()
