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
