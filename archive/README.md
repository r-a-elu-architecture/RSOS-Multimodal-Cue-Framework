# RSOS / RSIA / RSX / RSSO — historical source archive

This directory preserves the **original dated source records** supplied for public disclosure. These are primary historical documents: descriptions and original claims **are not proof** that an underlying model, physiological effect, neural state, or claimed intellectual-property entitlement was independently established.

## Navigating the archive

**The original records are kept privately** (since 18 November 2026, spec/PUBLIC_EDITION_2.md). What stays public is
everything needed to identify and check them:

- [`provenance/SOURCE-MANIFEST.csv`](provenance/SOURCE-MANIFEST.csv) — every original file's SHA-256, original path, byte
  count and source category (65 files).
- [`provenance/SHA256SUMS.txt`](provenance/SHA256SUMS.txt) — independently checkable SHA-256s for the source ZIP and all files.
- [`provenance/DUPLICATE-MAP.csv`](provenance/DUPLICATE-MAP.csv) — nine exact duplicate file-content groups.
- [`provenance/PUBLIC-EDITION-EDITS.csv`](provenance/PUBLIC-EDITION-EDITS.csv) — the earlier targeted wording edits, with
  original and edited hashes.
- The **published edition** of the tier ledger and metric logs that the site uses: `docs/data/ledger.json` and
  `docs/data/metrics.json`. It equals the originals with one rule applied, "GPT" → "model" (spec/PUBLIC_EDITION.md).
  Anyone holding the originals can check this with `python3 scripts/verify_edition.py PATH/TO/archive`.
- [`../architecture/`](../architecture/) — modern, source-linked navigation and interpretations.

Researchers who need the originals can ask the author; they are checked against the hashes above.

## Archive integrity and interpretation

The original files were not sanitized, rewritten or deduplicated. Fifteen files carry targeted public-edition edits only: the fifth archetype is now Raven (insight and strategic perception), its mnemonic references now point to Stephen Covey's *7 Habits of Highly Effective People*, and comparison passages with an external system were removed. Line counts are unchanged and all other text is untouched. The original hashes of these files, and of the superseded source ZIP (`a2bcf263…c735e`), are listed beside the edited hashes in [`provenance/PUBLIC-EDITION-EDITS.csv`](provenance/PUBLIC-EDITION-EDITS.csv). All 65 original internal paths are preserved within `original-estates/`; the source ZIP keeps the same estate folders under a top-level `RSOS_RSIA_RSX_RSSO/` folder. Texts labeled `PASS31B` include later historical reconstructions and evidence excerpts; do not assign their assertions the same provenance as original specifications. Some original texts contain proprietary declarations, author contact details, psychological terminology and historical assistant claims. These reflect their authorship and source context, not verified extraordinary model capabilities.

## License boundary

The repository's Apache-2.0 software license **does not automatically grant an Apache-2.0 license to these separately identified original estate records**. They are publicly disclosed as historical archival sources, with their original notices preserved and copyright retained as stated in those records. For downstream reuse beyond rights granted by applicable law, check the applicable historical notice or seek permission. The present disclosure of trade-secret-labeled material does not preserve secrecy as a matter of law.

To cite an individual source, use its exact path and SHA-256 from the manifest, not an undated paraphrase.
