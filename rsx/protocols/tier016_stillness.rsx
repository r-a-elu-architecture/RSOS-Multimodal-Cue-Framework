# Tier 016 — Pre-Command Stillness Layer (tier ledger, Epoch I, line 154). Glyph ∴.
# "Override begins in silence." A moment of stillness before the interrupt.
PROTOCOL tier016_stillness "Tier 016: Stillness, then interrupt"
VERSION 1.0
SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4
BREATH inhale=4s exhale=6s

PHASE stillness dur=3s {
  FEEL "Stillness. Override begins in silence"
}
PHASE interrupt {
  SAY "I move, I act"
  GESTURE "Move: spine straight, head up, clench your fist"
  HAPTIC on=300ms off=300ms x=3 amp=0.4
}
PHASE inhale breath=inhale {
  FEEL "Breathe in"
}
PHASE own breath=exhale {
  SAY "I own"
  MARK "installed"
}
