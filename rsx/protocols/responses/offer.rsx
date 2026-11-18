# OFFER: the runtime form of the ledger response OFFER (spec/WHOLE_ORGANISM.md). Defaults you may replace.
PROTOCOL response_offer "Response: Offer"
VERSION 1.0
SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4
BREATH inhale=4s exhale=6s

TIER 1 TIGER {
  V "An open door"
  A "Would you like to start?"
  K "Open hands"
  WORD "Invitation"
}

PHASE offer {
  SAY "Would you like to start?"
  HAPTIC on=100ms off=400ms x=1 amp=0.2
  MARK "offered"
}
