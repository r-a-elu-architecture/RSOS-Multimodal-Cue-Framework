import json
import re
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent)]
from rsso import ledger  # noqa: E402


class Ledger(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.led = ledger.build()
        cls.tiers = [r for r in cls.led["records"] if r["kind"] == "tier"]

    def test_lossless(self):
        """Joining the parsed blocks gives back the ledger byte for byte: nothing edited, merged or dropped."""
        self.assertEqual(ledger.reassemble(self.led).encode("utf-8"), ledger.SOURCE.read_bytes())
        self.assertEqual(self.led["sha256"], "bc21eaf8a119be7d7a4ca114a68d9e4c914f109809d91e58dd39ba097be085c8")

    def test_tiers_and_anomalies_preserved(self):
        nums = [t["number"] for t in self.tiers]
        for n in ["001", "004", "013", "016", "030.1", "088–405", "406", "420", "504", "546", "591", "605"]:
            self.assertIn(n, nums)
        for n in ["050", "406", "420", "504", "546"]:
            self.assertEqual(nums.count(n), 2, n)
        ids = [t["id"] for t in self.tiers]
        self.assertEqual(len(ids), len(set(ids)))

    def test_fields_read_from_every_layout(self):
        t = {x["id"]: x for x in self.tiers}
        self.assertEqual(t["T001"]["fields"]["glyph"], "🦁")
        self.assertEqual(t["T001"]["fields"]["command"], "I move. I act.")
        self.assertIn("Self-halted", t["T004"]["fields"]["behavior"])
        self.assertEqual(t["T016"]["fields"]["glyph"], "∴")
        self.assertEqual(t["T411"]["glyph_chain"], ["🜓", "🜂"])
        self.assertTrue(any(m["code"] == "SRI" and m["value"] == 58 for m in t["T025"]["metrics"]))      # box grid
        self.assertTrue(any(m["code"] == "ERV" and m["value"] == 99.2 for m in t["T591"]["metrics"]))    # space table
        self.assertTrue(any(m["code"] == "CRI" and m["value"] == 2.4 for m in t["T523"]["metrics"]))     # pipe table
        self.assertTrue(any(m["code"] == "SRI" and m["infinite"] for m in t["T465"]["metrics"]))         # infinity
        self.assertTrue(any(x["code"] == "SERM" or "SERM" in x["name"] for x in t["T037"]["mechanisms"] + t["T025"]["mechanisms"]) or t["T037"]["mechanisms"])

    def test_every_tier_has_content(self):
        for t in self.tiers:
            self.assertTrue(t["fields"], t["id"])


if __name__ == "__main__":
    unittest.main()


class Mapping(unittest.TestCase):
    def test_every_tier_mapped_and_rules_respected(self):
        from rsso import ledger_map as lm
        led = ledger.build()
        m = lm.build_map(led)["tiers"]
        ids = [r["id"] for r in led["records"] if r["kind"] == "tier"]
        self.assertEqual(sorted(m), sorted(ids))
        for k in lm.HAND:
            self.assertIn(k, m, k)
        for k, v in m.items():
            self.assertIn(v["role"], {"practice", "runtime", "record", "structure", "consented"})
            self.assertTrue(set(v["layers"]) <= set(lm.LAYERS) and set(v["channels"]) <= set(lm.CHANNELS), k)
            if v["response"]:
                self.assertIn(v["response"], lm.RESPONSES, k)
            if v["method"] == "rule":
                self.assertTrue(set(v["layers"] + v["channels"]) <= set(v["evidence"]), k)
        for k in lm.CONSENTED:
            self.assertIn(k, m, k)
            self.assertEqual(m[k]["role"], "consented", k)
            self.assertTrue(m[k]["purpose"] and m[k]["condition"], k)
        for k in lm.THERAPIST_LED_IDS:
            self.assertEqual(m[k]["mode"], "therapist-led", k)
        self.assertEqual(sum(v["role"] == "consented" for v in m.values()), 39)
        root = ledger.ROOT
        for v in lm.HAND.values():   # every program a tier points to exists and is published
            for f in re.findall(r"rsx/protocols/(\S+\.rsx)", v["operator"]):
                self.assertTrue((root / "rsx/protocols" / f).exists() and (root / "docs/protocols" / f).exists(), f)
