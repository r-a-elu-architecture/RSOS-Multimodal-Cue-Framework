# SSIT: higher-level imagery (spec/TRIAL_LOOP.md §5; SSIT design in spec/TRIAL.md, claims C97 and C101).
# Arm 'higher': imagery about a level above the problem (who you are at your best), flowing down into what you do.
# The three SSIT programs share breath, phases and length (300 s); only the imagery differs.
PROTOCOL ssit_higher "SSIT: higher-level imagery"
VERSION 1.0
SAFETY max_per_hour=2 max_per_day=4 refractory=600s haptic_max=0.3
BREATH inhale=4s exhale=6s

PHASE settle dur=20s {
  FEEL "Sit comfortably. Bring to mind who you are at your best, above any single task"
}
REPEAT 14 {
  PHASE inhale breath=inhale {
    SEE "The quality you have at your best: steady, clear, capable"
  }
  PHASE exhale breath=exhale {
    SAY "I am steady and clear"
  }
}
REPEAT 13 {
  PHASE inhale breath=inhale {
    SEE "That quality flowing down into everything you do today"
  }
  PHASE exhale breath=exhale {
    FEEL "Let it flow down into what you do"
  }
}
PHASE close dur=10s {
  SAY "It carries into everything I do"
  MARK "imagery_done"
}
