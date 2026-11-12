# RSOS Override Protocol (ROP) v1.1 — reference program.
# Specification: spec/OVERRIDE_PROTOCOL.md. Every word, image and gesture is a default you may replace.
# Start it the moment a negative state appears: a sound, a smell, something seen, a memory.

PROTOCOL override "RSOS Override Protocol"
VERSION 1.1
SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4
BREATH inhale=4s exhale=6s

TIER 1 LION {
  V "Golden lion light"
  A "I move, I act"
  K "Warmth and strength in the belly"
  GLYPH "◈"
  WORD "Courage"
}

FUTURES "Driving the car" | "At work" | "Achieving your goal"

# 1. Interrupt: move, straighten, clench the fist and say "I move, I act" once, all at the same moment. Then inhale.
PHASE interrupt {
  SAY "I move, I act"
  GESTURE "Move: spine straight, head up, clench your fist"
  HAPTIC on=300ms off=300ms x=3 amp=0.4      # VIB-ANCHOR (short, so the inhale follows at once)
  MARK "interrupt"
}

# 2. Inhale the lion light into the belly.
PHASE ignite breath=inhale {
  ACTIVATE LION
  SEE "Breathe golden lion light into your belly"
  TONE 220Hz 4s
}

# 3. Exhale: the light expands inside.
PHASE radiate breath=exhale {
  SEE "The light expands inside you: blood flow, lymph, every part and every cell"
}

# 4. At the top of the inhale, touch middle finger to thumb.
PHASE anchor breath=inhale {
  FEEL "Breathe in"
  WAIT 2s
  GESTURE "At the top: touch middle finger to thumb"
  HAPTIC on=150ms off=150ms x=2 amp=0.3
}

# 5. One exhale through all three futures. Associated, as your future self: everything is connected
#    by golden light (beams, flows) to you and to each other; you see it and feel it inside you.
#    Over many runs the people, objects and places in these futures come to carry power and agency.
#    A gentle smile is held through the whole exhale.
PHASE futures breath=exhale {
  FEEL "You, the people, objects and places: all connected by golden beams and flows. See it and feel it inside you"
  GESTURE "Hold a gentle smile"
  HAPTIC on=150ms off=150ms x=8 amp=0.3    # FP-ANCHOR
  FOR FUTURE {
    SEE "$future"
    WAIT 2s
  }
}

# 6. At the top of the inhale, a golden hologram finger appears in front of the eyes, pointing up.
PHASE hologram breath=inhale {
  FEEL "Breathe in"
  WAIT 2s
  SEE "A golden hologram finger in front of your eyes, pointing upward"
}

# 7. Exhale: light flows from the finger in every direction and fills what holds agency and power.
PHASE extend breath=exhale {
  SEE "Golden light flows from the finger: up, around, above, below, to the sides, into the sky"
  TONE 330Hz 6s
  WAIT 3s
  SEE "It fills the people, objects and places that hold agency and power"
}

# 8. Inhale: the light returns into the belly, carrying their resources.
PHASE return breath=inhale {
  SEE "The golden light returns into your belly, carrying every source of agency and power"
}

# 9. Exhale: it fills the body with golden light of power and agency.
PHASE fill breath=exhale {
  SEE "It fills your lymph, blood flow, every part of your body and every cell"
  FEEL "Golden light of power and agency"
}

# 10. A simple inhale.
PHASE gather breath=inhale {
  FEEL "Breathe in"
}

# 11. Exhale while saying "I own": the override is sealed and confirmed.
PHASE install breath=exhale {
  SAY "I own"
  FEEL "Sealed and confirmed"
  TONE 440Hz 2s
  MARK "installed"
}
