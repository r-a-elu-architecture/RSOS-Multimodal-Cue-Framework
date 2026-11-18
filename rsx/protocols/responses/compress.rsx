# COMPRESS: the runtime form of the ledger response COMPRESS (spec/WHOLE_ORGANISM.md). Defaults you may replace.
PROTOCOL response_compress "Response: Compress"
VERSION 1.0
SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4
BREATH inhale=4s exhale=6s

TIER 1 LION {
  V "The whole state folded into one point of light"
  A "One word"
  K "A closed fist"
  WORD "Seed"
}

PHASE interrupt {
  SAY "I move, I act"
  GESTURE "Move: spine straight, head up, clench your fist"
  HAPTIC on=300ms off=300ms x=3 amp=0.4
  MARK "origin"
}
PHASE fold breath=inhale {
  ACTIVATE LION
  SEE "The whole state folded into one point of light"
}
PHASE breathe_seal breath=inhale {
  FEEL "Breathe in"
}
PHASE seal breath=exhale {
  SAY "I own"
  MARK "sealed"
}
