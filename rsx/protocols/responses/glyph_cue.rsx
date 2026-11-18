# GLYPH_CUE: the runtime form of the ledger response GLYPH_CUE (spec/WHOLE_ORGANISM.md). Defaults you may replace.
PROTOCOL response_glyph_cue "Response: Glyph cue"
VERSION 1.0
SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4
BREATH inhale=4s exhale=6s

TIER 1 TIGER {
  V "The glyph in front of the eyes"
  A "The glyph's word"
  K "The glyph's code on the wrist"
  WORD "Glyph"
}

PHASE glyph breath=inhale {
  SEE "The glyph in front of the eyes"
  HAPTIC on=100ms off=100ms x=2 amp=0.3
}
PHASE open breath=exhale {
  FEEL "Let the glyph open the whole state"
  MARK "cued"
}
