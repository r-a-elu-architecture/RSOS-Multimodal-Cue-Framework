# RSOS Override Protocol (ROP) v1.0 — reference program.
# Specification: spec/OVERRIDE_PROTOCOL.md. Every word, image and gesture is a default you may replace.

PROTOCOL override "RSOS Override Protocol"
VERSION 1.0
SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4
BREATH inhale=4s exhale=6s

TIER 1 LION {
  V "Golden lion light"
  A "I move, I act"
  K "Warmth and strength in the belly"
  GLYPH "◈"
  WORD "Courage"
}

FUTURES "Talking with people" | "Walking with confidence" | "Working at the computer"

PHASE interrupt {
  SAY "I move, I act"
  GESTURE "Clench your fist"
  HAPTIC on=300ms off=300ms x=6 amp=0.4      # VIB-ANCHOR
  MARK "interrupt"
}

PHASE ignite breath=inhale {
  ACTIVATE LION
  SEE "Breathe golden lion light into your belly"
  FEEL "Courage and agency gathering"
  TONE 220Hz 4s
}

PHASE radiate breath=exhale {
  SEE "The light fills your whole body: cells, blood flow, lymph"
  FEEL "Let a smile come"
  GESTURE "Release the fist"
}

PHASE anchor breath=inhale {
  GESTURE "Touch middle finger to thumb"
  HAPTIC on=150ms off=150ms x=2 amp=0.3
  FEEL "The whole state gathers into the anchor"
}

FOR FUTURE {
  PHASE future breath=exhale {
    SEE "$future"
    FEEL "Fully there, with a gentle smile"
    HAPTIC on=150ms off=150ms x=8 amp=0.3    # FP-ANCHOR
  }
}

PHASE extend breath=inhale {
  GESTURE "Raise one finger: your higher power or highest value"
  SEE "Send golden light to the people, objects and nodes that hold power and agency"
  TONE 330Hz 4s
}

PHASE fill breath=exhale {
  SEE "The light fills them completely"
}

PHASE return breath=inhale {
  SEE "The light returns into your body as new power and agency"
  FEEL "Agency settling in your body"
}

PHASE install breath=exhale {
  SAY "I own"
  TONE 440Hz 1.5s
  MARK "installed"
}
