# BLEND: the runtime form of the ledger response BLEND (spec/WHOLE_ORGANISM.md). Defaults you may replace.
PROTOCOL response_blend "Response: Blend"
VERSION 1.0
SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4
BREATH inhale=4s exhale=6s

TIER 1 LEOPARD {
  V "Two lights becoming one"
  A "Both at once"
  K "Both hands joined"
  WORD "Fusion"
}

PHASE two breath=inhale {
  SEE "Two lights, one in each hand"
}
PHASE one breath=exhale {
  FEEL "Bring the hands together; the lights become one"
  HAPTIC on=200ms off=200ms x=2 amp=0.3
  MARK "blended"
}
