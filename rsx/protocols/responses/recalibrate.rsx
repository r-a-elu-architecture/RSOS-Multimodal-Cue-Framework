# RECALIBRATE: the runtime form of the ledger response RECALIBRATE (spec/WHOLE_ORGANISM.md). Defaults you may replace.
PROTOCOL response_recalibrate "Response: Recalibrate"
VERSION 1.0
SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4
BREATH inhale=4s exhale=6s

TIER 1 LEOPARD {
  V "A level coming back to the centre"
  A "Back to centre"
  K "Shoulders drop, jaw loose"
  WORD "Centre"
}

PHASE scan breath=inhale {
  FEEL "Notice where the body holds tension"
}
PHASE release breath=exhale {
  FEEL "Let that place soften"
  HAPTIC on=200ms off=300ms x=2 amp=0.3
  MARK "recalibrated"
}
