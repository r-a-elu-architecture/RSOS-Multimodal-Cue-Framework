# PUBLIC_EDITION_2 — the originals move to the private repository; subtitle, emergency line, evidence label, author, roadmap

Status: registered 2026-11-18, before any code. Results in §8. The owner's decisions of 18 November 2026. A verified
backup was made first: private repository RSOS-Multimodal-World, `corpus/backups/cue-framework-2026-11-18/` (commit
c86b556): the whole public repository at c4b89b4, the original archive unpacked, the pre-edit files and a SHA-256
manifest, all checked byte for byte. Git history is not rewritten (owner's decision).

## 1. The originals move (M)

- **Removed from the public repository:** `archive/original-estates/` (65 files, the archive's public edition of the
  original records) and `archive/original-package/` (the source ZIP). They are kept in the private repository, in the
  backup above.
- **Kept public:** `archive/README.md` (updated: the originals are kept privately and are available to researchers on
  request), `archive/provenance/` (every file's SHA-256, original path, size, the edit list and duplicate map),
  `archive/ARCHIVE-INTEGRITY.json`, `archive/SOURCE_ARCHIVE_SHA256.csv`.
- **Generators** (`rsso/rsso/ledger.py`, `rsso/rsso/metrics.py`): when the original files are present (the private
  repository), they rebuild, check and publish as now; when absent (the public repository), they leave the published
  edition (`docs/data/ledger.json`, `metrics.json`, `rsso/results/ledger_summary.md`) unchanged and say so.
- **Verification moves with the originals:** a new script `scripts/verify_edition.py ORIGINALS_DIR` checks, against a copy
  of the originals, that they match the SHA-256 manifest, that the ledger reassembles byte for byte, and that the
  published files equal the originals plus rule E1 (PUBLIC_EDITION). Tests that need the originals skip when they are
  absent; a public test checks the published ledger's recorded source hash against the manifest.
- **Links:** `architecture/build.py` lists each original by name, purpose and SHA-256 without a link (the file is private);
  `docs/metrics.html` points to the provenance manifest. `rsx/tests/test_repository.py` must still find every local link.

## 2. Subtitle (S)

Under the name, in the README and on the home page: "An open framework for practising state change with breath, words and
cues." The name stays.

## 3. Emergency line (C)

The disclaimer "Research and development framework; not a medical device." becomes "Research and development framework;
not a medical device, and not for use in an emergency: if you are at risk of harm, contact your local emergency services."
**Only** in the README's status box and on `docs/safety.html` and `docs/therapist.html`; no numbers, services, pages or
buttons. `scripts/check_profiles.py` (which bars crisis wording from every page, RELEASE_1 A2) allows exactly this sentence
on those two pages and nowhere else; everything else it checks is unchanged.

## 4. Evidence label (L)

`architecture/evidence.py`: a part at level E4 is shown as "Tested on recorded data: no positive result yet" while the
register holds no pass on recorded or public data, and as "Tested on recorded data" once it does. Computed from the
register, never typed.

## 5. Author (A)

In prose that refers to the author's own decisions, "the owner" becomes "the author": the phrases "owner's decision(s)",
"owner's direction", "owner's request", "by the owner", "from the owner" in public Markdown files. **Not changed:** "owner"
as a system role (owner keys, owner ratification, leaving CRISIS by a clinician or the owner) in specifications and code,
where it names a role in the architecture, not a person.

## 6. Roadmap (R)

As C50 in PUBLIC_EDITION, marked as edited 18 November 2026:
- C27 "The combination is historically unprecedented, 10-20 years ahead, and edits memory faster than therapy." → "The
  combination is new, and edits memory faster than therapy." (the comparison stays: it is the testable part)
- C71 "The robot insight scores 9.7 of 10, a breakthrough 2-5 years ahead." → "The robot insight is new." (tracked against
  public evidence, as before)

## 7. Checks (fixed now)

- V1 `scripts/verify_edition.py` passes on the private backup's originals.
- V2 the public repository holds no file under `archive/original-estates/` or `archive/original-package/`; every other
  published file is unchanged by the move (generators leave them as they are).
- V3 `check_all.sh`, RSX-V, `check_evidence`, `check_site_catchup`, `check_profiles` (with the one allowed sentence),
  `check_site_night`, `check_personlab` pass; `rsx/tests/test_repository.py` finds every local link.
- V4 the emergency sentence appears on exactly the README, `safety.html` and `therapist.html`; the subtitle on the README
  and home page; no E4 label reads "Tested on recorded data" alone while recorded data holds no pass.

## 8. Results

(recorded after the code commit)

### Results (code 4a17218)

- **V1:** `scripts/verify_edition.py` on the private backup's originals: 65/65 files match the manifest; the ledger
  reassembles byte for byte; the published ledger and metrics equal the originals plus E1.
- **V2:** no file under `archive/original-estates/` or `archive/original-package/` is tracked in the public repository (0);
  with the originals absent, `ledger.build()` falls back to the published edition and the tier map and glyph originals
  rebuild **byte-identical**; `ledger.py` and `metrics.py` leave the published files unchanged.
- **V3:** `check_all.sh`, RSX-V 234, `check_profiles`, `check_evidence` 168/168, `check_site_catchup`,
  `check_site_night` 35/35, `check_personlab` 31/31 pass; `rsx/tests/test_repository.py` resolves every local link.
- **V4:** the emergency sentence is in the README, `safety.html` and `therapist.html` only (required there by
  `check_profiles`, `test_release` and `test_safety`, barred elsewhere); the subtitle is on the README and home page; E4
  reads "Tested on recorded data: no positive result yet" on every page and in the README.
- **Disclosed:** (1) `docs/metrics.html` first broke (a `//` comment cut off the rest of a line); `check_profiles` and
  `check_evidence` caught it (8 page errors) before the commit; fixed with an inline comment. (2) The README's "Acute risk
  is outside self-guided use and belongs under a qualified clinician's protocol." was replaced by the emergency sentence.
  (3) A: "owner's brief" and "owner's design images" were also changed (named in the audit, F5, though not in §5's list);
  ADOPT_WC's "the owner's private record" became "a private record". "Ratified by the owner" (a system role) is kept.
  (4) Roadmap C68 ("Within 2-5 years: invitations from labs, a movement…") still carries a forecast; not in scope.

## 9. Amendment R2, 18 November 2026 (owner's decision, before its code): roadmap C68

C68 is a tracked prediction, so it is made checkable rather than removed, and marked as edited:
"Within 2-5 years: invitations from labs, a movement, thousands helped." → "Milestones to track by November 2028: an
invitation or collaboration from a research lab; a first registered study with people; the number of people who have used
RSOS. (Edited 18 November 2026.)" Kind (prediction), test ("Tracked as a dated prediction."), author label and status stay.
Files: `architecture/roadmap.py`, `spec/CLAIMS.md`, regenerated `docs/data/roadmap.json`. Checks: `check_all.sh`; the roadmap
page renders with no page error and shows the new text; no public file outside `archive/` and this spec keeps "thousands
helped" or "a movement".

### R2 results (code 47df4ef)
C68 edited in `architecture/roadmap.py`, `spec/CLAIMS.md` and `docs/data/roadmap.json`; the roadmap page shows the new
text with 0 page errors; `check_all.sh` passes. "thousands helped" appears nowhere outside this spec. **Disclosed:** the
registered phrase check also listed "a movement", which still appears in unrelated senses (a body movement in the Identity
exercise; the ledger's recorded text, kept as recorded); the claim itself is gone.
