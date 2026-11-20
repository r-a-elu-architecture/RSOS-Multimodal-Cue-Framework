# SITE_FAMILY: one professional RSOS family (registered 20 November 2026, before any page changes)

Author's request (20 November 2026): make the Cue Framework as professional as the RSOS Language site
(https://r-a-elu-architecture.github.io/RSOS-Language/), and the same in look and structure. The Language repository is
read-only from this account; it is only read, never changed.

## What the Language site does, and this step adopts
- One design system in one stylesheet: light slate ground, deep ink, Atkinson Hyperlegible, green reserved for
  verified results, amber for predictions, red for failures; type scale, spacing and focus styles shared.
- A family bar on every page linking the two public RSOS sites, with the current one marked.
- A short header (the mark and five or six destinations) and the same footer on every page (author, ORCID, licences,
  "not a medical device", source, DOI, responsible use, security).
- A home page that leads with one plain claim and shows it working, then measured numbers, then evidence, then where to
  start by audience, then how the parts fit, then how to run it.
- A README with the same order: claim, measured table, limits, where to start.

## Phases
- **F1 (this step):** `docs/site.css` (the family design system, adapted from the Language site by the same author under
  Apache 2.0); the home page rebuilt in that structure and style; the family bar on all other pages; the README top
  rebuilt (claim, measured table, limits, where to start) and its stale test counts corrected (RSX 35 → 43, RSSO 30 → 328).
- **F2 (next step, registered separately):** the tool pages move onto the same tokens, one at a time, each with a
  screenshot check, because their interfaces carry their own colours.

## Function does not change
Wording, structure and style only. The home page keeps every script, every element id the tests use (the profile
selector, the domain cards), the generated evidence block between its markers, the positioning sentence (`data-raw`),
and every link destination it had (moved, not removed).

## Checks, fixed before the change
- S1: every page in `docs/*.html` carries the family bar, with links to the Language site and to this site, this site marked.
- S2: the home page keeps `<!-- evidence:start -->` … `<!-- evidence:end -->`, the positioning sentence, `profiles.js` and
  the guard scripts it loaded, and every in-site link it had before.
- S3: `scripts/check_all.sh` passes, and the browser checks `check_profiles`, `check_site_catchup`, `check_evidence`,
  `check_outlet` and `check_fixes_r1` pass with 0 page errors.
- S4: home page screenshots at 1280 px and 375 px wide are reviewed; no horizontal overflow at 375 px.
- S5: the text colour tokens meet WCAG AA contrast (≥ 4.5:1) on their backgrounds, computed.
- S6: every number on the new home page and README traces to a generated file or a command shown beside it
  (results register, test counts from `check_all.sh`, the compiled protocol).
