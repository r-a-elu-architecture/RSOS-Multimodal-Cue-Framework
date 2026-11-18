# RECALL: the runtime form of the ledger response RECALL (spec/WHOLE_ORGANISM.md). Defaults you may replace.
PROTOCOL response_recall "Response: Recall"
VERSION 1.0
SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4
BREATH inhale=4s exhale=6s

TIER 1 RAVEN {
  V "A moment when the resource was present"
  A "I remember this strength"
  K "The posture of that moment"
  WORD "Resource"
}

PHASE find breath=inhale {
  SEE "A moment when the resource was present"
}
PHASE bring breath=exhale {
  FEEL "Take the posture of that moment now"
  HAPTIC on=200ms off=200ms x=2 amp=0.3
  MARK "recalled"
}
