# STOP: the runtime form of the ledger response STOP (spec/WHOLE_ORGANISM.md). Defaults you may replace.
PROTOCOL response_stop "Response: Stop"
VERSION 1.0
SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4
BREATH inhale=4s exhale=6s

TIER 1 BEAR {
  V "A clear red line in front of you"
  A "Stop"
  K "Feet planted, hands still"
  WORD "Stop"
}

PHASE halt {
  SAY "Stop"
  GESTURE "Open hand forward, feet planted"
  HAPTIC on=300ms off=200ms x=2 amp=0.4
  MARK "stopped"
}
PHASE settle breath=exhale {
  FEEL "Let the breath out slowly"
}
