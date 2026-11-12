# Interrupt-only: phase 1 of the override, for very high distress or very little time.
PROTOCOL interrupt_only "Interrupt only"
VERSION 1.0
PHASE interrupt {
  SAY "I move, I act"
  GESTURE "Clench your fist"
  HAPTIC on=300ms off=300ms x=6 amp=0.4
}
PHASE breathe breath=exhale {
  FEEL "Feet on the floor; long exhale"
}
