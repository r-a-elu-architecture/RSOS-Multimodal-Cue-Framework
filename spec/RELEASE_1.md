# RELEASE_1 — review the dev work and prepare one release to main (owner approves)

Status: registered 2026-11-17, before any review fix, the merge preparation or a change to pages. Results in §6, in
separate "Record results" commits. No threshold, limit or pass criterion of any earlier spec changes in this step.

## 0. What and why

`dev` holds 92 commits since `main` (Steps 1–5, fix passes R1–R6 and P2, Phase 2, BASELINE_AUDIT, ESP32_TOOLS,
BOARD_PENDING), all "awaiting review". The owner's decision (2026-11-17): one consolidated step. This account reviews
everything itself, fixes what blocks a professional release, makes the site usable without us, and ends with **one
pull request from `dev` to `main` that the owner approves**. This account does not merge to `main`.

**Freeze.** From this registration until the pull request is opened, `dev` takes only this step's commits and fixes.
The parallel session adds no new spec (HANDOFF_DEV §1 notice).

## 1. R-MERGE — the release must carry everything on dev

`main` holds 059a58f, a revert of 6394a70 (S1) and 5227a26. `dev` descends from 6394a70. A plain merge of `dev` into
`main` would keep that revert: git treats 6394a70 as merged already, so S1's files (`docs/js/safety.js`,
`docs/safety.html` and others) would stay in their reverted state wherever `dev` did not touch the same lines.

- **M1** Before the pull request, `dev` records `main` as merged with no change to its files:
  `git merge -s ours origin/main` (message names 059a58f and this section).
- **M2** Check, before opening the pull request: a trial merge of the new `dev` into `origin/main`, in a scratch
  clone, gives a tree identical to `dev` (`git diff --stat <trial> dev` is empty).
- **M3** The backup branch `backup/pre-claude-2026-11-16` stays untouched.

## 2. R-CHECK — every automated check

- **A1** `scripts/check_all.sh`, `(cd rsxv && pytest)`, and every suite in HANDOFF_DEV §2 "How to verify" pass.
- **A2** Every browser acceptance script in HANDOFF_DEV §2 (`scripts/check_*.py docs`, Playwright with Chrome) passes.
- **A3** Page check (new, `scripts/check_release.py`): every `docs/*.html` page, opened from a local server at the site
  root in Chrome (desktop 1280×800 and phone 390×844):
  - no uncaught page error;
  - no `console.error`;
  - no failed same-origin request;
  - every same-origin link (`href`, and `src` of scripts, styles and images) resolves to a file;
  - the "DEVELOPMENT VERSION" banner is absent at the root and present under `/dev/` (the page served under `/dev/`).

  External links are listed, not fetched.
- **A4** The `firmware` workflow passes on the release commit (both jobs).

## 3. R-REVIEW — review by risk, findings recorded

Order: (1) wristband security (BLE_PAIRING, FIXES_R6C, FIXES_P2); (2) safety engine and wording (Step 1, CONTAIN,
LOW_MOOD, R1–R6 output gate); (3) claims against evidence (RSX-V levels, W5-CEILING, BASELINE_AUDIT); (4) site
(SITE_CATCHUP, ARCH_REFRESH); (5) firmware and CI (ESP32_TOOLS, BOARD_PENDING).

Each area is checked against the HANDOFF_DEV §3 checklist. Findings are recorded in HANDOFF_DEV §5 as one block per
area: the commit reviewed, pass/fail per item with evidence, and the findings with severity.

- **blocker:** wrong behaviour, a safety rule not enforced, a claim the evidence does not support, broken page, or a
  rule of HANDOFF_DEV §1 broken.
- **should fix** and **note:** recorded; fixed in this step when small, otherwise listed as open in the release notes.

Every fix is registered in §5 (an amendment) before its code, as in earlier steps.

This is a review by the same model family that built the work: the release notes say so. They do not call the work
"independently reviewed".

## 4. R-USE — usable without us

- **U1 Start here.** `docs/index.html` opens with a short "Start here" block: five paths, each one sentence and one
  link to a working page.

  | Path | Link |
  |---|---|
  | Try the core routine | the player |
  | Researchers | REVIEW.md and the results page |
  | Clinicians | the therapist page |
  | Developers | the repository README and RSX |
  | Hardware | the Devices page |

- **U2 Status in plain words.** Each of those five destination pages states what it is and its evidence status, in the
  site's own status vocabulary (complete in simulation / built and tested / specification only / measured), with no
  claim beyond HANDOFF_DEV and the evidence register.
- **U3 Nothing development-only** appears at the site root (A3) or in the README.
- **U4 Wording.** The representation rule of HANDOFF_DEV §1 holds on every page changed in this step
  (`scripts/check_profiles.py` and the existing wording tests).

## 5. Amendments (fixes registered before code)

(none yet)

## 6. Results

(recorded after the runs, in separate commits)

## 7. Release notes and pull request

- **N1** `releases/NEXT.md` becomes the release notes. Contents: what is new by area; what each part's evidence is;
  what remains open (from HANDOFF_DEV §6 and this review); how to verify.
- **N2** One pull request `dev` → `main`, titled "Release: dev work of 16–17 November 2026 (RELEASE_1)". The body holds
  the release notes summary, the review verdicts and the checks with their run links, and states that merging
  publishes the live site. The owner merges; this account does not.
- **N3** Version number and CITATION.cff `version` / `date-released` are set by the owner at merge (the pull request
  proposes `v2.1.0`). This step does not tag.
