# SSIT: general calming imagery (spec/TRIAL_LOOP.md §5; SSIT design in spec/TRIAL.md, claims C97 and C101).
# Arm 'calm' (reference): general calming imagery with no task content.
# The three SSIT programs share breath, phases and length (300 s); only the imagery differs.
PROTOCOL ssit_calm "SSIT: general calming imagery"
VERSION 1.0
SAFETY max_per_hour=2 max_per_day=4 refractory=600s haptic_max=0.3
BREATH inhale=4s exhale=6s

PHASE settle dur=20s {
  FEEL "Sit comfortably. Let your body settle"
}
REPEAT 14 {
  PHASE inhale breath=inhale {
    SEE "A calm, quiet place"
  }
  PHASE exhale breath=exhale {
    SAY "I am calm"
  }
}
REPEAT 13 {
  PHASE inhale breath=inhale {
    SEE "The calm spreading through your body"
  }
  PHASE exhale breath=exhale {
    FEEL "Let the calm spread"
  }
}
PHASE close dur=10s {
  SAY "I am calm"
  MARK "imagery_done"
}
