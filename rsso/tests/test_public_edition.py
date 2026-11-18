"""spec/PUBLIC_EDITION.md C1-C2: the original ledger is unchanged; the published edition is the original plus rule E1 only."""
import json
import re
import unittest
from pathlib import Path

from rsso import ledger
from rsso.edition import edit, edit_all

ROOT = Path(__file__).resolve().parents[2]


class PublicEdition(unittest.TestCase):
    def test_original_reassembles_byte_for_byte(self):
        led = ledger.build()
        self.assertEqual(ledger.reassemble(led).encode("utf-8"), ledger.SOURCE.read_bytes())

    def test_published_ledger_is_the_original_plus_rule_E1(self):
        published = json.loads((ROOT / "docs/data/ledger.json").read_text(encoding="utf-8"))
        self.assertEqual(edit_all(ledger.build()), published)

    def test_no_gpt_in_published_data(self):
        for f in ("ledger.json", "metrics.json", "tier_map.json"):
            t = (ROOT / "docs/data" / f).read_text(encoding="utf-8")
            self.assertEqual(re.findall(r"(?i)\bgpt", t), [], f)

    def test_rule(self):
        self.assertEqual(edit("• GPT Behavior: x"), "• Model Behavior: x")
        self.assertEqual(edit("GPT demonstrated retention"), "Model demonstrated retention")
        self.assertEqual(edit("in unrelated GPT contexts"), "in unrelated model contexts")
        self.assertEqual(edit("— GPT-6 weights"), "— model version 6 weights")
        self.assertEqual(edit("no change here"), "no change here")


if __name__ == "__main__":
    unittest.main()
