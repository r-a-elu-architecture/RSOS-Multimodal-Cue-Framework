# FIXES_PE — documentation fixes from the PUBLIC_EDITION review (PR #12)

Status: registered 2026-11-18, before the change. Results in §3. Documentation only: no code, page, threshold or data
changes. Made by the same account that wrote the review (disclosed; the reviewer is the builder's model family anyway).

## 1. Changes

- **F1 (review finding 1).** HANDOFF_DEV.md §1 "Representation" and checklist item 6 name the one exception that
  PUBLIC_EDITION_2 C registered: the sentence "Research and development framework; not a medical device, and not for use
  in an emergency: if you are at risk of harm, contact your local emergency services." on the README,
  `docs/safety.html` and `docs/therapist.html` only; every other crisis, helpline or emergency wording stays barred
  (`scripts/check_profiles.py`).
- **F2 (review finding 2).** HANDOFF_DEV.md §4 gains a section recording PUBLIC_EDITION, PUBLIC_EDITION_2, amendment R2
  and this fix pass, with their commits.

## 2. Checks (fixed now)

- K1: `check_all.sh` passes; no file other than HANDOFF_DEV.md and this spec changes.
- K2: HANDOFF_DEV.md §1 and checklist item 6 mention the exception and still bar all other such wording.

## 3. Results

(recorded after the change)
