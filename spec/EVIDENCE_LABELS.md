# EVIDENCE_LABELS — Phase 3, step 13: every page says how far its evidence goes

Status: registered 2026-11-17, before any code. Results in §7, in a separate record commit.

## 0. Why

- The site uses several unrelated status words: "built in simulation" (59 roadmap items), "test built, untested in
  people", "specified", "partial", "built", and pass / mixed / fail in the results register. A reader cannot tell
  whether "built in simulation" means *the software runs*, *the measuring was checked on simulated people with known
  answers*, or *the method was shown to help a simulated person*. Those are different claims.
- The results register now has 42 rows and 1 pass; nothing has been tested with people using RSOS. Pages describe
  what a part *does*, not how far that is supported. This step adds one scale, one label per page, and checks that keep
  the labels true.
- Not in this step: the Agents page board (step 14), the home page redesign (step 15), changing roadmap statuses.

## 1. The scale

| Level | Name | Means | Basis required |
|---|---|---|---|
| E0 | Written | Specified in a document; no code. | a spec file |
| E1 | Built | The software exists and its own tests pass. Says nothing about whether the method helps. | a test file |
| E2 | Checked on simulated people | The measure, detector or rule recovers known answers planted in simulated people. Shows the *measuring* works as designed; not that the method helps. | an evaluation file in `rsso/results/` |
| E3 | Tested in simulation | A registered test of whether the method itself helps, on simulated people or agents. | results-register rows with source `sim` |
| E4 | Tested on recorded data | A registered test on real recorded data (public conversation or preference data, or one private record), not on people using RSOS. | results-register rows with source `public` or `record` |
| E5 | Tested with people using RSOS | A registered study with people using RSOS. | results-register rows with source `people` |

A page's level is the highest level whose basis it cites. For E3–E5 the label also gives the counts of the cited rows by
status (pass, mixed, fail, other), taken from `docs/data/results_register.json` at build time, so they cannot drift.
Every label below E5 ends with: **"Not yet tested with people using RSOS."**

Pages that show records or summaries rather than a part get kind `record` ("Shows records as written; makes no claim of
effect") or `summary` (the site-wide counts by level and by register status).

## 2. Data and generator

- `architecture/evidence_map.json` (hand-maintained): for each live page, its kind, level and basis (file paths, or
  register sources and families); and the **source of every results-register row** (`sim`, `public`, `record`,
  `people`), matched by the start of the row's test name.
- `architecture/evidence.py` builds:
  - `docs/data/evidence.json`: the scale, every page's label text, and the counts;
  - the label block in each live page, between `<!-- evidence:start -->` and `<!-- evidence:end -->`, directly under the
    page's lede: `<p class="evidence" data-level="E2">Evidence: …</p>`; static text, so it shows without scripts;
  - the "Evidence levels" section of `README.md` between the same markers: one row per part with its level.
- `check_all.sh` runs the generator and adds `docs/*.html` and `README.md` to its "generated files unchanged" diff.

## 3. Rules (each a test)

- **L1** Every live page (not retired, not the offline cache) has exactly one label block, equal to the generated text.
- **L2** Basis exists: every cited file exists; E3–E5 pages cite at least one register row of the matching source.
- **L3** Every results-register row has exactly one source. An unclassified row fails the build, so a new row cannot
  appear without being placed on the scale.
- **L4** No E5 label while no row has source `people`. (Today: none.)
- **L5** Overclaim words. On any page or README text below E5, none of: proven, validated, evidence-based, clinically,
  scientifically, shown to work, guaranteed, effective, efficacy, cures, heals, rewires, reprograms. One exemption:
  "validated instrument" (a third-party questionnaire the practitioner chooses). Matched as whole words, case-insensitive,
  in visible text (not scripts or styles).
- **L6** Profile wording: labels pass `scripts/check_profiles.py` (no clinical words in non-clinical profiles).
- **L7** Python and the browser agree: the browser check reads each label as rendered on the development site and
  compares it with `evidence.json`.

## 4. Levels at registration (author's assignment; the generator enforces the basis, not the judgement)

| Page | Kind / level | Basis |
|---|---|---|
| player | E1 | RSX compilers' tests (Python and JS parity) |
| anchors | E2 | `rsso/results/peak.md` |
| trials | E2 | `rsso/results/trial.md` |
| identity | E2 | `rsso/results/identity.md` |
| atlas | E2 | `rsso/results/atlas.md` |
| night | E2 | `rsso/results/night.md` |
| therapist | E2 | `rsso/results/copilot.md` |
| nodes | E1 | NODES / LINX tests |
| device | E1 | conformance suite, firmware compile and emulator checks; no board run yet |
| glyphs | E1 | glyph format tests |
| safety | E1 | safety engine and Watchdog tests |
| contribute | E1 | contribution tests |
| agents, world, rsxv | E3 and E4 | register rows of families agents, transfer, repurposing, lineage |
| results, system | summary | all rows; all pages |
| roadmap, tiers, metrics | record | — |

## 5. Tests

- `rsso/tests/test_evidence.py`: L1–L6 statically, and that the generator is reproducible.
- `scripts/check_evidence.py docs`: L7 in Chrome on every live page, and no page errors.
- All suites, `check_all.sh` and the existing browser checks pass.

## 6. Limits

- The level is the author's assignment within what the basis allows; a reviewer should check §4.
- The word list in L5 catches plain overclaims, not every misleading sentence.

## 7. Results (recorded after code 88c0eae)

- **21 live pages labelled** (the 4 retired pages are excluded): 6 at E1 Built (player, nodes, device, glyphs, safety,
  contribute), 6 at E2 Checked on simulated people (anchors, trials, identity, atlas, night, therapist), 3 at E4 Tested
  on recorded data (agents, world, rsxv), 3 summary (index, system, results) and 3 record (roadmap, tiers, metrics).
  No page reaches E5.
- **Clarification of §4:** the home page is a live page, so L1 requires a label there too. It carries the summary label;
  the home page redesign stays step 15.
- **All 42 register rows placed (L3):** simulation 27 (1 pass, 7 mixed, 18 fail, 1 analysis); one private record 5
  (3 mixed, 2 fail); public data 10 (1 mixed, 5 fail, 4 other); people 0.
- The agents, World and RSX-V pages now read: in simulation 27 tests, 1 pass, 7 mixed, 18 fail, 1 analysis; on recorded
  data 7 tests, 0 pass, 2 mixed, 2 fail, 3 other.
- **L5 found one overclaim word:** README's autonomy-gate row said "proven strength against sham". It now reads
  "strength measured against sham and above it". No page text tripped the rule; the safety page's "validated instrument"
  is the registered exemption.
- **Checks:** `rsso/tests/test_evidence.py` 7 passed (L1–L6, each failure path exercised); `scripts/check_evidence.py`
  168 of 168 page views (21 pages × 4 domain profiles × desktop and phone) show the generated label, 0 page errors;
  `check_all.sh` passed (rsso 301, RSX-V 205 under unittest, toolkit 10, conformance 15/15 twice, board 7/7, generated
  files unchanged); the 12 existing browser checks and `check_release.py` (75 of 75 views) exit 0.
- Offline cache bumped to v50 so the labels reach installed copies.
- **Open for review:** the level assignments in §4 are the author's judgement within the basis rules; in particular,
  whether the World page (simulation replays) should sit at E3 rather than E4.
