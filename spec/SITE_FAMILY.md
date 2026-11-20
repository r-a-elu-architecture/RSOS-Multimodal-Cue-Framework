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

## F1 results (20 November 2026), added after the change; nothing above was changed
- S1 PASS: all 25 pages carry the family bar once, linking the Language site and this site, this site marked.
- S2 PASS: the home page keeps the evidence markers, the positioning sentence, `profiles.js`, `outlet.js`, `devmode.js`,
  the domain cards and the service worker, and all 31 links it had before (two in-page anchors, #rsx and #model, were
  first dropped with the old menu; the test caught it and they are now in "Every part").
- S3 PASS: `scripts/check_all.sh` (RSX 43, RSX-V 229, RSSO 332, evidence 23, toolkit 10 tests; conformance 15/15 ×2; board
  7/7; generated files reproducible) and the browser checks `check_profiles`, `check_site_catchup`, `check_evidence`,
  `check_outlet`, `check_fixes_r1`, with 0 page errors. `check_site_catchup` first failed: SITE_CATCHUP S7.1 and S7.4
  require RSX-V in every page's menu and the words "RSX-V, above RSX" on the home page; both were restored.
- S4 PASS: home page at 1280 px and 375 px reviewed by screenshot; overflow 0 px at both (a first 133 px overflow at
  375 px came from long link rows in "Every part"; they now wrap).
- S5 PASS after one change: green text on the pale green tag was 4.25:1 with the Language palette's #12805c. This site uses
  #0f7553 (4.92:1 there, 5.24:1 on the page). The Language site has the same 4.25:1 pair; that repository is not changed
  from this account.
- S6 PASS: home and README figures trace to `rsx compile` (43 events, 52.0 s, the refused 0.6 vibration),
  `check_all.sh` (637 tests) and `rsxv/RESULTS.md` (51 registered tests).
- Deliberate difference from the Language site: no external fonts are loaded here (privacy: a font request to Google would
  disclose every visitor's address on a site that promises nothing leaves the device).
- F2 remains: the tool pages keep their own dark styles under the family bar until each is moved onto the shared design.

## F1 amendment (20 November 2026, author's decision): the Cue Framework's ribbon
Both sites stay white (the shared family design). The Cue Framework's own header becomes a ribbon in its original colours:
navy #151b2f with a 3 px gold #e8b04a edge, a gold dot, light menu text (10.3:1 contrast) and a gold underline on primary
buttons. The family bar above it stays the shared light grey. Checks re-run after the change: unit tests, `check_profiles`,
`check_site_catchup`, `check_fixes_r1`, `check_evidence` pass; overflow 0 px at 1280 and 375 px. F2 carries the ribbon to every page.

## F2 (registered 20 November 2026, before any tool page changes): every page on the family design, with the ribbon
**Method.** One shared stylesheet, `docs/light.css`, loaded after each page's own styles: it remaps the pages' common
colour variables (`--ink`, `--ink-2`, `--ink-3`, `--line`, `--text`, `--muted`, `--gold`, `--glow`, `--ok`, `--warn`, `--stop`) to the
family design, sets the shared type, and turns each page's `header.top` into the navy and gold ribbon. Colours a page hard-codes
are fixed in that page's own styles, from screenshots. No script, element id, text or link changes; wording only where a colour
name is part of a label.
**Checks, fixed now:**
- T1: every page has a white ground (`body` background luminance ≥ 0.85) and the ribbon (navy header band with the gold edge),
  except where a page has no `header.top`; those are listed with the reason.
- T2: on every page, at 1280 px, every visible text element has computed contrast ≥ 4.5:1 against its effective background
  (≥ 3:1 for text ≥ 24 px or ≥ 18.66 px bold), measured in Chrome; exceptions are listed.
- T3: overflow 0 px at 1280 and 375 px on every page.
- T4: `scripts/check_all.sh` and every browser check in `scripts/` that ran before pass, with 0 page errors.
- T5: a screenshot of each page's first screen at 1280 px is reviewed, and the set is kept with the results.
Out of scope: the symbol and emoji fonts nine pages load from Google (they render the glyphs); flagged for a separate decision.
