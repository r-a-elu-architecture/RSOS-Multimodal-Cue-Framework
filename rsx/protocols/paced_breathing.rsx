# Control condition for H1: the same length and breath pacing as the Override Protocol,
# with neutral instructions only (no words, fist, light imagery, anchors or futures).
PROTOCOL paced_breathing "Paced breathing (control)"
VERSION 1.0
BREATH inhale=4s exhale=6s
PHASE settle dur=1800ms {
  FEEL "Sit comfortably"
}
REPEAT 5 {
  PHASE inhale breath=inhale {
    FEEL "Breathe in"
  }
  PHASE exhale breath=exhale {
    FEEL "Breathe out"
  }
}
