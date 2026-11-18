# GATE: the runtime form of the ledger response GATE (spec/WHOLE_ORGANISM.md). Defaults you may replace.
PROTOCOL response_gate "Response: Gate"
VERSION 1.0
SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4
BREATH inhale=4s exhale=6s

TIER 1 BEAR {
  V "A gate that opens only from inside"
  A "Do I choose this now?"
  K "Hand on the chest"
  WORD "Choice"
}

PHASE check {
  SAY "Do I choose this now?"
  HAPTIC on=100ms off=200ms x=2 amp=0.3
}
PHASE answer breath=exhale {
  FEEL "Wait for a clear yes; without it, stop here"
  MARK "gate"
}
