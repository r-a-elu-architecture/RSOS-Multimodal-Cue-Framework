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

## 2. Research-record pages translated too (registered 18 Nov 2026, before the change)

Author's decision: the research-record pages (results, system, tiers, roadmap, glyphs and the archived benchmark pages)
also show profile wording; **only the wording changes, never the function.**

Change: the exemption list (`EXEMPT_PAGES`, `rsso/rsso/profiles.py` and `docs/js/profiles.js`, kept identical) becomes
empty; four display rules are added to the existing translation table (therapeutic, diagnosed, diagnostics,
pathology). Translation runs at display time only (PROFILES §2): stored data, module outputs, rules and the Clinical
profile are untouched.

| # | Prediction | Pass if |
|---|---|---|
| **F1** | Wording | Under the six non-clinical profiles, every page's rendered text has none of the site's clinical words (`CLINICAL_WORDS`) and no "pathology" |
| **F2** | Function unchanged, shown | The Clinical profile renders every page's text byte-identical before and after (snapshot of all pages taken before the change) |
| **F3** | Function unchanged, by construction | No file under `docs/data/`, no module outside the two profile files, and no test expectation other than the exemption list changes; `check_all.sh`, `check_profiles.py`, `check_site_catchup.py` pass |

### Results (18 Nov 2026)

| # | Result | Verdict |
|---|---|---|
| F1 | `check_profiles.py`, now checking every page under every non-clinical profile for the clinical word list and "pathology": 0 fails, 0 page errors | **pass** |
| F2 | Clinical profile, all 25 pages, rendered text before vs after: identical except the contribute page's participant code, which is random per device and new in each fresh browser (masked, identical) | **pass** |
| F3 | No file under `docs/data/` changed (hash check); changed files: the two profile files (exemption list emptied, 13 display rules added, identical in Python and JavaScript) and the check script; `check_all.sh`, `check_profiles.py`, `check_site_catchup.py`, `check_evidence.py` (168/168) pass | **pass** |
