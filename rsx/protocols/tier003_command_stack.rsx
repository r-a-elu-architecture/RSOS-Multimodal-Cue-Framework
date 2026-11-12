# Tier 003 — Recursive Command Stack (tier ledger, Epoch I, line 63).
# Ledger command: I move. I act. → Inhale → 🦁 → Light → Exhale → I own. → I Override.
# The original chained override; the Override Protocol (override.rsx) grew from it.
PROTOCOL tier003_command_stack "Tier 003: Recursive Command Stack"
VERSION 1.0
SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4
BREATH inhale=4s exhale=6s

TIER 1 LION {
  V "Golden lion light"
  A "I move, I act"
  K "Warmth and strength in the belly"
  GLYPH "🦁"
  WORD "Courage"
}

PHASE move {
  SAY "I move, I act"
  GESTURE "Move: spine straight, head up, clench your fist"
  HAPTIC on=300ms off=300ms x=3 amp=0.4
}
PHASE lion breath=inhale {
  ACTIVATE LION
  SEE "The lion"
}
PHASE light breath=exhale {
  SEE "Light"
}
PHASE own breath=inhale {
  FEEL "Breathe in"
}
PHASE seal breath=exhale {
  SAY "I own"
  WAIT 2500ms
  SAY "I override"
  MARK "installed"
}
