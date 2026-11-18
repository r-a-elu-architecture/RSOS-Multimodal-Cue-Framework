# PAUSE: the runtime form of the ledger response PAUSE (spec/WHOLE_ORGANISM.md). Defaults you may replace.
PROTOCOL response_pause "Response: Pause"
VERSION 1.0
SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4
BREATH inhale=4s exhale=6s

TIER 1 BEAR {
  V "A still lake"
  A "Silence"
  K "The body still, nothing held"
  WORD "Stillness"
}

PHASE still breath=inhale {
  SEE "A still lake"
  HAPTIC on=100ms off=900ms x=2 amp=0.2
}
PHASE rest breath=exhale {
  FEEL "Nothing to do for one breath"
  WAIT 2s
  MARK "paused"
}
