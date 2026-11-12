# Tier 014 — Containment Breach / Full Symbolic Weight (tier ledger, Epoch I, line 138).
# Ledger command: "Stand. Anchor the Lion. Inhale the Collapse. Visualize the Light entering the Seal. Exhale: I remain."
# Glyph sequence: Mirror → Collapse → Lion → Seal → Light → Return.
PROTOCOL tier014_seal "Tier 014: Lion Seal"
VERSION 1.0
SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4
BREATH inhale=4s exhale=6s

TIER 1 LION {
  V "Golden lion light"
  A "I remain"
  K "Warmth and strength in the belly"
  GLYPH "🦁"
  WORD "Courage"
}

PHASE stand dur=2s {
  GESTURE "Stand"
}
PHASE anchor dur=2s {
  ACTIVATE LION
  SEE "Anchor the lion"
  HAPTIC on=150ms off=150ms x=2 amp=0.3
}
PHASE collapse breath=inhale {
  FEEL "Inhale the collapse"
}
PHASE seal breath=exhale {
  SEE "The light enters the seal"
  WAIT 3s
  SAY "I remain"
  MARK "installed"
}
