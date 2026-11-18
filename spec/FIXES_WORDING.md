# FIXES_WORDING: no clinical wording outside its places (18 Nov 2026)

Author's request: remove "relapse" and check that the site carries no clinical wording.

- **"Relapse" removed** from the results register row Round 8l and from `spec/GUARD_GAIN.md` and
  `spec/ROLE_ORGANISM.md`; the function is named "keeping the gain (fault prevention)". Meaning and results unchanged.
- **Gap found and closed:** `docs/rsxv.html` was outside the profile check's page list and showed "distress" in plain
  text under every profile. The sentence now says "intensity"; the three code panes (RSX-V command, RSX cue program,
  device lines) are marked `data-raw`, because they show the language's own field names; `scripts/check_profiles.py`
  now includes the page.
- **Full scan, rendered in Chrome under the six non-clinical profiles, every page,** with the site's clinical word list
  plus relapse, psychiatr*, psychotherap*, disorder, pathology, medication, sedative, crisis, self-harm, addiction,
  withdrawal, clinical, clinician. Today's register rows (8g–8l) contain none. What remains is by design:
  - "Clinical" once per page: the name of the Clinical profile in the profile chooser (its description names
    psychotherapists and psychiatrists as its users);
  - "clinician-led protocol": kept in every profile on purpose (spec/PROFILES.md §2, invariant 4);
  - the safety page's self-check and guidance levels (medication question; clinician-led work);
  - "Disorder" on the metrics page: original ledger wording ("Integrity Through Disorder"), kept word for word;
  - "withdrawn" on the therapist page: a consent that was withdrawn, not a clinical term;
  - the research-record pages (results, roadmap, system, tiers, glyphs) keep their original wording by the existing
    rule (`rsso/rsso/profiles.py` EXEMPT_PAGES).
