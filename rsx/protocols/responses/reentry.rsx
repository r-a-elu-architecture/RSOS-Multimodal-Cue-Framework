# REENTRY: the runtime form of the ledger response REENTRY (spec/WHOLE_ORGANISM.md). Defaults you may replace.
PROTOCOL response_reentry "Response: Re-entry"
VERSION 1.0
SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4
BREATH inhale=4s exhale=6s

TIER 1 BEAR {
  V "Golden light coming back into the belly"
  A "I return"
  K "Warmth in the belly"
  WORD "Return"
}

PHASE interrupt {
  SAY "I move, I act"
  GESTURE "Move: spine straight, head up, clench your fist"
  HAPTIC on=300ms off=300ms x=3 amp=0.4
  MARK "origin"
}
PHASE return breath=inhale {
  ACTIVATE BEAR
  SEE "Golden light coming back into the belly"
}
PHASE breathe_seal breath=inhale {
  FEEL "Breathe in"
}
PHASE seal breath=exhale {
  SAY "I own"
  MARK "sealed"
}
