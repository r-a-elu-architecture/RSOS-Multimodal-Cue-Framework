"""spec/AGENTS_ANCHOR.md: the anchored policy (unit level; the experiment is rsxv/anchor.py)."""
import unittest

from rsxv.world import ANCHORED, FitLedger, World, AgentEnvV2


class Anchored(unittest.TestCase):
    def test_starts_in_bear_and_needs_the_interval(self):
        w = World(AgentEnvV2(1), seed=1, **ANCHORED)
        self.assertEqual(w.active, "BEAR")
        led = FitLedger()
        for r in (0.10, 0.12, 0.11, 0.09):
            led.add("calm", "BEAR", r)
        for r in (0.13, 0.15, 0.14, 0.16):      # better on average, intervals overlap: stay with Bear
            led.add("calm", "LION", r - 0.025)
        w.ledger = led
        self.assertEqual(w._anchored("calm"), "BEAR")
        for r in (0.9, 0.91, 0.92, 0.9, 0.91):   # interval clearly above Bear's: switch
            led.add("calm", "TIGER", r)
        self.assertEqual(w._anchored("calm"), "TIGER")
        self.assertEqual(w._anchored("rising"), "BEAR")     # no Bear interval in this context yet

    def test_other_policies_unchanged(self):
        self.assertEqual(World(AgentEnvV2(1), seed=1).active, "LION")


if __name__ == "__main__":
    unittest.main()
