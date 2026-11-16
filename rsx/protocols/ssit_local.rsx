# SSIT: imagery of the activity (spec/TRIAL_LOOP.md §5; SSIT design in spec/TRIAL.md, claims C97 and C101).
# Arm 'local': imagery about the activity itself becoming easy.
# The three SSIT programs share breath, phases and length (300 s); only the imagery differs.
PROTOCOL ssit_local "SSIT: imagery of the activity"
VERSION 1.0
SAFETY max_per_hour=2 max_per_day=4 refractory=600s haptic_max=0.3
BREATH inhale=4s exhale=6s

PHASE settle dur=20s {
  FEEL "Sit comfortably. Bring to mind the activity you are working on"
}
REPEAT 14 {
  PHASE inhale breath=inhale {
    SEE "The activity itself, each step becoming easy"
  }
  PHASE exhale breath=exhale {
    SAY "Each step is easy"
  }
}
REPEAT 13 {
  PHASE inhale breath=inhale {
    SEE "Doing it smoothly, from start to finish"
  }
  PHASE exhale breath=exhale {
    FEEL "Feel how easy it is"
  }
}
PHASE close dur=10s {
  SAY "This activity is easy for me"
  MARK "imagery_done"
}
