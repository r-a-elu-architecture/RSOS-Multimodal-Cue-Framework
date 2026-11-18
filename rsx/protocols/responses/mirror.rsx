# MIRROR: the runtime form of the ledger response MIRROR (spec/WHOLE_ORGANISM.md). Defaults you may replace.
PROTOCOL response_mirror "Response: Mirror"
VERSION 1.0
SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4
BREATH inhale=4s exhale=6s

TIER 1 RAVEN {
  V "The scene seen from above"
  A "Only observed"
  K "The body still"
  WORD "Observer"
}

PHASE above breath=inhale {
  SEE "The scene seen from above"
}
PHASE observe breath=exhale {
  SAY "Only observed"
  HAPTIC on=100ms off=300ms x=1 amp=0.2
  MARK "observed"
}
