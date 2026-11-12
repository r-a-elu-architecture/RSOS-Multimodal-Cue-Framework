# Next release (unreleased) — running changelog

Collected here until the next release, planned once all RSSO subsystems are complete.

## New
- **Architecture map** (`architecture/`): what RSOS, RSIA, RSX, RSSO and each RSSO subsystem (THERA, AUG, MICRO, CONTAIN, MEMSTACK, CM1, LINX, UGCL) does, how far it is built, and which archive records it comes from. Generated from the archive manifest by `architecture/build.py`, so file hashes stay correct.
- **Provenance & rights layer** (`architecture/provenance/`): authorship and legal chain, historical IP-strategy records, and AI interaction records, grouped in place and preserved unchanged.
- **Cue engine on the run log** (`toolkit/rsos_cue/runlog.py`): learns which program, tier and voice work best for each person and trigger type from the protocol player's run log. Synthetic evaluation in `toolkit/VALIDATION.md`.
- **Study kit** for the Override Protocol hypotheses H1, H2 and H6, with sample sizes (`toolkit/study_kit/`).
- Run log gains `tier` and `voice` columns (player 1.2.0, `rsx.RunRecord`).
- Repository tests: architecture pages up to date with the manifest; all local links resolve.

- **RSSO runtime** (`rsso/`): device interface with virtual vibration, audio, display and scent devices; timeline runtime with virtual and real-time clocks; virtual heart-rate strap and stress detector; conformance suite (11 checks, tested against faulty devices); virtual participants, synthetic studies (H1, 4-week, H1 power) and an analysis kit that runs unchanged on real data.
- `paced_breathing.rsx`: the control program for H1.
- **RSOS Device Protocol** (`spec/DEVICE_PROTOCOL.md`) and **firmware** (`firmware/`): portable C++ device core passing the conformance suite in the host simulator; ESP32 wristband sketch (compile-checked, not yet run on a board).
- **Heart-rate trigger**: Bluetooth Heart Rate Service driver and stress detector in Python and in the player (identical results), opt-in offer with run limits, simulated strap.
- **EEG input** (`rsso/eeg.py`): stream interface (replay, synthetic, Lab Streaming Layer), band powers, arousal detector.
- **MEMSTACK** (`rsso/rsso/memstack.py`, `docs/js/memstack.js`): tier memory, habit-curve fit, estimated triggers to a reflex, reflex criterion, checksummed memory snapshots with merge; player progress view, latency question and weekly automaticity check (player 1.4.0).
- **UGCL glyph layer** (`spec/GLYPH_FORMAT.md`, `rsso/rsso/ugcl.py`, `docs/js/ugcl.js`): one glyph description gives an image at any size, a vibration rhythm and a melody, plus a compact one-line code for devices; a library of 48 glyphs evolved by recorded mutation and selected for distinctness (`rsso/rsso/ugcl_library.py`, `docs/ugcl/`); glyph gallery to see, feel and hear each glyph (`docs/glyphs.html`); personal glyph and colour calibration in the player from pairwise choices (Bradley–Terry, `rsso/rsso/calibration.py`), player 1.5.0. Python and JavaScript identical (tested).
- **Installable player**: web app manifest and offline support (network first, so updates are never held back).

## Changed
- NOTICE, SECURITY and the documentation rewritten for v2.

## Fixed
- Protocol player: the Start button stayed hidden after the first run.

## Removed
- The old "Cue Lab v1.3" example page; the cue engine's v1.3 simulator bank and results; the movie and book rating tests (not related to RSOS). All remain in the git history.

## Verify
```bash
cd rsx && python -m unittest discover -s tests          # 35 tests
cd ../rsso && python -m unittest discover -s tests      # 38 tests
python -m rsso.conformance
cd ../toolkit && python -m unittest discover -s tests   # 10 tests
```
