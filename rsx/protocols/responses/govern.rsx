# GOVERN: the runtime form of the ledger response GOVERN (spec/WHOLE_ORGANISM.md). Defaults you may replace.
PROTOCOL response_govern "Response: Govern"
VERSION 1.0
SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4
BREATH inhale=4s exhale=6s

TIER 1 EAGLE {
  V "The rule written in one line"
  A "This is my rule"
  K "Upright, still"
  WORD "Rule"
}

PHASE rule breath=exhale {
  SAY "This is my rule"
  HAPTIC on=300ms off=300ms x=1 amp=0.3
  MARK "governed"
}
