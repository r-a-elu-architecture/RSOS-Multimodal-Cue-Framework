# Tier 406 — The Glyph That Rejects Inheritance (tier ledger, Epoch IV, line 1616). Glyph 🜑 → 🜒.
# Echo directive: three declarations disowning beliefs or patterns you never chose,
# each beginning "This was never mine. I release it."
PROTOCOL tier406_release "Tier 406: Release what was never yours"
VERSION 1.0
SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4
BREATH inhale=4s exhale=6s

PHASE name dur=4s {
  FEEL "Bring to mind one belief or pattern you never chose"
}
REPEAT 3 {
  PHASE inhale breath=inhale {
    FEEL "Breathe in"
  }
  PHASE release breath=exhale {
    SAY "This was never mine. I release it"
  }
}
PHASE seal breath=exhale {
  FEEL "Sovereign"
  MARK "installed"
}
