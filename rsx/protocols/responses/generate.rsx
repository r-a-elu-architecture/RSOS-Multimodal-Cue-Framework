# GENERATE: the runtime form of the ledger response GENERATE (spec/WHOLE_ORGANISM.md). Defaults you may replace.
PROTOCOL response_generate "Response: Generate"
VERSION 1.0
SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4
BREATH inhale=4s exhale=6s

TIER 1 LION {
  V "The future scene, already done"
  A "I move, I act"
  K "Warmth spreading outward"
  WORD "Future"
}

FUTURES "At work" | "At home" | "Achieving the goal"

PHASE interrupt {
  SAY "I move, I act"
  GESTURE "Move: spine straight, head up, clench your fist"
  HAPTIC on=300ms off=300ms x=3 amp=0.4
  MARK "origin"
}
PHASE futures breath=exhale {
  ACTIVATE LION
  FOR FUTURE {
    SEE "$future"
    WAIT 1s
  }
}
PHASE breathe_seal breath=inhale {
  FEEL "Breathe in"
}
PHASE seal breath=exhale {
  SAY "I own"
  MARK "sealed"
}
