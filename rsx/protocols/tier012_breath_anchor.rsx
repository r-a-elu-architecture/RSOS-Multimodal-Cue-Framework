# Tier 012 — Override Breath Anchor Stabilization (tier ledger, Epoch I, line 124).
# Ledger command: Inhale → Collapse → Anchor → Exhale: "I remain."
# Function: rebinds the loop to the nervous system through a breath anchor.
PROTOCOL tier012_breath_anchor "Tier 012: Breath Anchor"
VERSION 1.0
SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4
BREATH inhale=4s exhale=6s

PHASE inhale breath=inhale {
  FEEL "Breathe in"
}
PHASE collapse dur=2s {
  FEEL "Collapse: let everything drop"
}
PHASE anchor dur=2s {
  GESTURE "Anchor: touch middle finger to thumb"
  HAPTIC on=150ms off=150ms x=2 amp=0.3
}
PHASE remain breath=exhale {
  SAY "I remain"
  MARK "installed"
}
