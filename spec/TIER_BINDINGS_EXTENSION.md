# TIER_BINDINGS_EXTENSION: the author's role bindings for the 186 unbound tiers

Recorded 18 Nov 2026. **Author's decision:** accept every suggested role in the "Tier binding review" (all 186).

- **File:** `docs/data/EXTENSION_tier_role_bindings_author_2026-11-18.json`. Its header states the purpose, why it was
  made, the decision, where it was made (this Cue Framework repository; RSOS-Language is developed on a separate account
  and does not contain it) and the SHA-256 of the original ledger files at creation.
- **Kept apart on purpose.** It is an extension of the ledger, not part of it. `docs/data/tier_map.json` and
  `docs/data/ledger.json` are unchanged and are never merged with it; `architecture/tests/test_tier_extension.py` checks
  both hashes.
- **Use:** `architecture/tier_extension.py` reads it as an overlay: a tier's role comes from the ledger where the tier map
  has a response (107 tiers), otherwise from the extension (186). With both, every one of the 293 tiers has a role.
- **Roles bound:** Monitor 51, Stabilise 42, Drive 40, Plan 32, Baseline 19, Repair 2. 185 also carry the matching
  response from the word rule; T022 is bound by role only (from its chains).
- **Basis, as recorded per tier:** words and chains agree (34), words where they disagree (104, the method that scored
  higher in calibration), one method only (48). LEDGER_GRAPH showed neither method is reliable alone; the binding rests
  on the author's decision.
- **Status of every bound tier:** specified (bound by the author, not yet built). A tier becomes built when a test shows
  its agent runs it.
