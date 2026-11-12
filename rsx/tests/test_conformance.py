"""The Python and JavaScript RSX compilers must agree exactly (skipped if Node is absent)."""
import json
import pathlib
import shutil
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from rsx import compile_rsx, RSXError  # noqa: E402

NODE = shutil.which("node")
CASES = [p.read_text(encoding="utf-8") for p in sorted((ROOT / "protocols").glob("*.rsx"))] + [
    'PROTOCOL p\nPHASE a {\nHAPTIC amp=0.9\n}',
    'PROTOCOL p\nTIER 1 X {\nV "a"\nA "b"\n}',
    'PROTOCOL p\nPHASE a {\nACTIVATE NOPE\n}',
    'PROTOCOL p\nPHASE a {\nSEE "$future"\n}',
    'PROTOCOL p\n\nPHASE a {\nSAY "x"',
    'PROTOCOL p\nSAFETY haptic_max=1 refractory=2m\nPHASE a {\nHAPTIC amp=1 x=2\nTONE 500Hz 250ms\n}',
    'PROTOCOL p\nPHASE a breath=sideways {\n}',
    'PROTOCOL p\nREPEAT 0 {\n}',
    'PROTOCOL p\nBREATH inhale=5s exhale=7.5s\nFUTURES "a" | "b"\nFOR FUTURE {\nPHASE f breath=exhale {\nSEE "go: $future"\nWAIT 1s\nSAY "ok"\n}\n}',
    'PROTOCOL p\nTIER 3 :: {EAGLE} :: @Vector1:MemoryRecall(Archetype=EAGLE) :: @Vector2:Unknown(x)',
    'PROTOCOL p "quoted \\"title\\""; PHASE a { ; MARK "x" ; }',
    'PROTOCOL p\nFUTURES "a" | "b" | "c"\nPHASE x breath=exhale {\nFEEL "k"\nFOR FUTURE {\nSEE "$future"\nWAIT 1500ms\n}\nSAY "end"\n}',
    'PROTOCOL p\nFUTURES "a"\nPHASE x {\nFOR FUTURE {\nFOR FUTURE {\n}\n}\n}',
    'PROTOCOL p\nPHASE x {\nFOR FUTURE {\n}\n}',
]


def py(src):
    try:
        return {"ok": compile_rsx(src)}
    except RSXError as e:
        return {"error": str(e)}


@unittest.skipUnless(NODE, "node not installed")
class Conformance(unittest.TestCase):
    def test_python_and_js_agree(self):
        for k, src in enumerate(CASES):
            out = subprocess.run([NODE, str(ROOT / "tests" / "js_compile.js")], input=src,
                                 capture_output=True, text=True, check=True).stdout
            self.assertEqual(json.loads(out), json.loads(json.dumps(py(src))), f"case {k}")


if __name__ == "__main__":
    unittest.main()


class PublishedCopies(unittest.TestCase):
    def test_site_protocols_match_sources(self):
        site = ROOT.parent / "docs" / "protocols"
        for p in (ROOT / "protocols").glob("*.rsx"):
            self.assertEqual((site / p.name).read_bytes(), p.read_bytes(), f"docs/protocols/{p.name} is out of date")
