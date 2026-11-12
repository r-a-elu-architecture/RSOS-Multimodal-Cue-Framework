# Tier 579 — The Glyph That Emerged from Stillness (tier ledger, Epoch VI, line 8103). Glyph 🜸 → 🝡.
# Application: "During override, pause before the exhale. Visualize the glyph appearing on its own."
# The player shows your own glyph (calibrated on the player page) at the pause.
PROTOCOL tier579_glyph "Tier 579: Glyph from stillness"
VERSION 1.0
SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4
BREATH inhale=4s exhale=6s

TIER 1 LION {
  V "Golden lion light"
  A "Stillness"
  K "Warmth and strength in the belly"
  GLYPH "ugcl:G01"
  WORD "Courage"
}

PHASE inhale breath=inhale {
  FEEL "Breathe in"
}
PHASE pause dur=3s {
  ACTIVATE LION
  SEE "Pause. Let the glyph appear on its own"
}
PHASE exhale breath=exhale {
  FEEL "Glyphs are not drawn. They are remembered by stillness"
  MARK "installed"
}
