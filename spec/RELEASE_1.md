# RELEASE_1 — review the dev work and prepare one release to main (owner approves)

Status: registered 2026-11-17 (cfe9eff), before any review fix, the merge preparation or a change to pages. Results in §6, in
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

### A1 (after the first check run; before any fix)

Found (recorded in full in §6):
- **RF1 (blocker, a check).** `scripts/check_site_catchup.py` fails on `dev` at 3a3d4d8 / cfe9eff:
  `BASELINE_AUDIT Q3 H-SWITCH meaning shown: got False`. The Agents page is right: `profiles.js` shows clinical words
  in the default profile's vocabulary ("distress" becomes "intensity"), as the representation rule requires. The check
  compares the raw register text. BASELINE_AUDIT Q4 records that the browser checks pass, which is not true on `dev`.
- **RF2 (environment).** In the workspace, external hosts are blocked. Every page that loads Google Fonts logs
  `Failed to load resource: net::ERR_TUNNEL_CONNECTION_FAILED`. No same-origin request failed and no link was missing.
- **RF3 (note).** Pages load fonts from fonts.googleapis.com / fonts.gstatic.com: a third-party request on every visit,
  and no glyph fonts when offline. Recorded as open in the release notes; not changed in this step.

Fixes:
- **F1** In `check_site_catchup.py`, the two register-meaning checks (W1, H-SWITCH) compare the page with the
  register text after the page's own wording rule:
  `RSOSProfiles.text(stripped, RSOSProfiles.current(), RSOSProfiles.clinicalOn())`, evaluated in the page. Nothing on
  the page changes. HANDOFF_DEV §5 records that BASELINE_AUDIT Q4 was not met when recorded.
- **F2** `check_release.py` (A3): a `console.error` of the form `Failed to load resource: net::ERR_…` does not fail a
  view when, in that view, a request to an external host failed and no same-origin request failed. The failed external
  URLs are listed per view and in the summary. Same-origin failures, page errors and any other `console.error` still
  fail.
- **F3 (U1, U2)** — the texts:
  - `index.html`, before "Your domain": a section "Start here" with the five paths of §4 U1. Each path is one sentence
    plus one link.
  - A one-line status note under the first heading of `player.html`, `therapist.html`, `device.html` and
    `results.html`, in the site's status words. Each says what the page is, its evidence status, and "not a medical
    device".
  - Text that names no outcome claim: no human outcome data yet; the wristband compiled and emulated, not run on a
    board; clinical use under the practitioner's own protocol.

## 6. Results

Registered cfe9eff; amendment A1 ae091f8; code 475b9d2; review record 3e9eac2; release notes 6e848bb; M1 683c4a6.

| ID | Result |
|---|---|
| A1 | `check_all.sh` pass; rsso 292 passed, 1 expected failure; RSX-V 156 passed (475b9d2) |
| A2 | Before F1: 10 of 11 browser checks pass. `check_site_catchup.py` failed: `BASELINE_AUDIT Q3 H-SWITCH meaning shown: got False, expected True` (RF1). After F1: 11 of 11 |
| A3 | `check_release.py`: 25 pages, 75 views (desktop, phone, `/dev/`). First run: every page error was `Failed to load resource: net::ERR_TUNNEL_CONNECTION_FAILED` from Google Fonts (blocked in the workspace), with no same-origin failure, no missing link, and the banner right in every view. After F2: 75 of 75 pass; external loads that failed here: `https://fonts.googleapis.com/css2` |
| A4 | On 683c4a6: `checks` run 44026359262 success; `firmware` run 44026359253 success (compile `K1-P pass: 40 builds`; emulator pass); Pages success |
| R-REVIEW | Five areas, HANDOFF_DEV §5. One blocker (RF1, a check; fixed). One should-fix (no guided entry; fixed). Notes: FIXES_P2 E1 confirmed in the library sources; README crisis-line sentence (the owner's decision); third-party fonts (RF3, open). Verdict in every area: ready for the owner. A same-account review |
| U1–U4 | "Start here" with five paths on the home page; status lines on the player, practitioner, devices and results pages; the dev banner only under `/dev/` (A3); `check_profiles.py` pass |
| M1 | 683c4a6: `git merge -s ours origin/main`; tree identical to 6e848bb |
| M2 | Trial merge of 683c4a6 into `main` (059a58f) in a scratch clone: no conflict, `git diff` against `dev` 0 lines, S1's `docs/js/safety.js` present. Without M1 (the same trial with 6e848bb): conflicts in 8 files, among them `docs/js/safety.js` and `rsso/rsso/safety.py` (deleted on `main`, modified on `dev`) |
| M3 | `backup/pre-claude-2026-11-16` still at 32f49bb |
| N1 | `releases/NEXT.md`: release section for this work, evidence status, open items, verify commands |
| N2 | Pull request #6: https://github.com/r-a-elu-architecture/RSOS-Multimodal-Cue-Framework/pull/6 |

## 7. Release notes and pull request

- **N1** `releases/NEXT.md` becomes the release notes. Contents: what is new by area; what each part's evidence is;
  what remains open (from HANDOFF_DEV §6 and this review); how to verify.
- **N2** One pull request `dev` → `main`, titled "Release: dev work of 16–17 November 2026 (RELEASE_1)". The body holds
  the release notes summary, the review verdicts and the checks with their run links, and states that merging
  publishes the live site. The owner merges; this account does not.
- **N3** Version number and CITATION.cff `version` / `date-released` are set by the owner at merge (the pull request
  proposes `v2.1.0`). This step does not tag.
