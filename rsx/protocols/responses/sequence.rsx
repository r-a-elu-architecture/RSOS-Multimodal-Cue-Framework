# SEQUENCE: the runtime form of the ledger response SEQUENCE (spec/WHOLE_ORGANISM.md). Defaults you may replace.
PROTOCOL response_sequence "Response: Sequence"
VERSION 1.0
SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4
BREATH inhale=4s exhale=6s

TIER 1 EAGLE {
  V "Three steps laid out in order"
  A "One step, then the next"
  K "Steady walking rhythm"
  WORD "Order"
}

PHASE step1 breath=inhale {
  SEE "The first step"
}
PHASE step2 breath=exhale {
  SEE "The second step"
}
PHASE step3 breath=inhale {
  SEE "The third step"
  HAPTIC on=200ms off=200ms x=3 amp=0.3
  MARK "sequenced"
}
