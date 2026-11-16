# Tier 013: the lion and the dragon held as one composite anchor (spec/TRIAL_LOOP.md §5; PEAK composite()).
# Two TIER blocks; glyphs joined with +, vibration codes played one after the other with a pause (FIXES_R3 R3-a),
# so each code stays readable on one motor.
# The archive v1 command ran this as ArchetypeMerge (legacy_vector.rsx); this is the RSX v2 program.
PROTOCOL tier013_lion_dragon "Tier 013: Lion and Dragon"
VERSION 1.0
SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4
BREATH inhale=4s exhale=6s

TIER 1 LION {
  V "Golden lion light"
  A "I move, I act"
  K "Warmth and strength in the belly"
  GLYPH "🦁"
  WORD "Courage"
  TACTON "..-"
}
TIER 2 DRAGON {
  V "A clear, cool light around the whole body"
  A "I hold my strength and my shadow in one breath"
  K "Shoulders wide, breath deep and slow"
  GLYPH "🐉"
  WORD "Strength and shadow held together"
  TACTON "---"
}

PHASE interrupt dur=2s {
  SAY "I move, I act"
  GESTURE "Spine straight, clench your fist"
}
PHASE lion breath=inhale {
  ACTIVATE LION
  SEE "🦁 The lion"
}
PHASE pause dur=1s {
  FEEL "Hold"
}
PHASE dragon breath=exhale {
  ACTIVATE DRAGON
  SEE "🐉 The dragon, held with the lion as one"
}
PHASE seal breath=exhale {
  SAY "I hold my strength and my shadow in one breath"
}
REPEAT 3 {
  PHASE breathe_in breath=inhale {
    FEEL "Breathe in, both held as one"
  }
  PHASE breathe_out breath=exhale {
    FEEL "Breathe out, steady"
  }
}
PHASE remain dur=3s {
  SAY "I remain"
  MARK "installed"
}
