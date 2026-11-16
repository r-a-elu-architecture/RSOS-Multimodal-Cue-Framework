# WATCHDOG — the RSIA Watchdog on the person side

Status: registered 2026-11-16, before code (1dc4ea6); built and tested. W1–W8 and the static part of W9:
`rsso/tests/test_watchdog.py` (parity over 2,500 generated cases); W9 in Chrome: `scripts/check_watchdog.py`. Code: `rsso/rsso/watchdog.py` and `docs/js/watchdog.js` (identical
results, tested).

## 1. Purpose

In RSX-V the Watchdog and the Spine (7 virtues, 21 precepts) govern the agents. On the person side, CONTAIN, the
session states, GATE and consent each answer one question, and pages ask them separately. This step gives the
person side the same constitution as the agents: **one decision for every action that acts on a person, with the
Spine virtue that decided it, written to a hash-chained audit log.**

The Watchdog adds rules; it never loosens one. It does not import the profiles module: the page passes the
profile's highest guidance level.

## 2. The decision

`watch(action, ctx) -> {decision, level, reasons[], resolve, contain}`

- `decision`: **allow** (may start), **ask** (the person confirms first), **hold** (does not start).
- `reasons`: `[{rule, virtue, text}]`, every reason names a Spine virtue or precept.
- `resolve`: who can lift it: `person` (ask), `clinician` (clinician-led holds), `safety_page` (CONTAIN or session
  state holds), or `none` (the action is not allowed in this domain).

`action`: `{kind: run | offer | cue | plan | session | stop, protocol, trigger: self | device | agent,
source: person | practitioner | agent, auto, therapist_led, deep, signals[], justified_by}`.

`ctx`: `{contain, safety, timeline, now, max_level, clinician_present, screening_recorded, consents, plan_protocols}`.

Checks, in Spine order. Any hold gives **hold**; otherwise any ask gives **ask**; otherwise **allow**.

| Rule | Virtue | Outcome |
|---|---|---|
| `stop` is always allowed, before every other rule | Yū (necessary actions are not blocked) | allow |
| Text in the action carries a Spine wording flag | the flag's virtue | hold |
| CONTAIN `decide` blocks (envelope, quarantine, practice paused, session state) | Jin | hold, resolve safety_page |
| Guidance level above the domain's highest level | Gi | hold, resolve none |
| Clinician-led level without a clinician present and a recorded screening result | Gi | hold, resolve clinician |
| Automatic firing without `automatic_firing` consent | Rei | downgraded to ask |
| Automatic firing on fewer than two independent signals | precept 3 | downgraded to ask |
| A device or agent offers a program that is not in the person's plan | Chūgi | hold |
| Proposed by an agent, or by a device without automatic firing | Rei (the person starts every run) | ask |
| Justified only by a population map (CM1, ATLAS) | precept 15 | ask |
| Everything else | — | allow |

Guidance level of an action: **clinician_led** if `therapist_led`, `deep`, or a release-of-identity tier
(414, 420, 439, 440); **structured** if it is a plan, a practitioner session, a programmed cue, or triggered by a
device or an agent; otherwise **self_guided**.

The Watchdog's own rules never hold a regulating program (paced breathing, interrupt, stillness, breath anchor) or
a stop; only CONTAIN and the session state can (they are unchanged).

## 3. Link between CONTAIN and the session state

`link(contain, safety, now)`: while CONTAIN's practice pause (escalation) is active, the session state is at least
Stabilisation (entered "by contain" with the pause reasons). It never lowers a state. Pages call it after CONTAIN's
review.

## 4. Audit

Every decision is appended to a hash-chained log (SHA-256 over canonical JSON, the previous hash in each record),
kept in `rsos.watchdog.log` (last 500). `verify(log)` detects any edited, removed or reordered record. The JS
SHA-256 is synchronous and equal to Python's.

## 5. Pages

Player, device, nodes and therapist ask the Watchdog instead of CONTAIN directly; the safety page shows the recent
decisions and whether the log verifies. The world simulation is not part of this step.

## 6. Interpretation recorded at build time

On the therapist page a clinician-led THERA session counts as having its screening recorded, because the session
itself contains a required screening step before any processing, and a "yes" there stops the session (THERA `check`).
On the node studio the screening answer given before saving counts. Where the person confirms by pressing start or
accepting an offer, an "ask" proceeds; a "hold" never does.

## 7. Acceptance

- W1 Parity: Python and JS identical over a generated grid of actions, states and contexts (decisions, reasons,
  levels, link results, hashes).
- W2 Never weaker: whenever CONTAIN `decide` blocks, the Watchdog holds.
- W3 Stop is always allowed; the Watchdog's own rules never hold a regulating program.
- W4 Guidance: clinician-led actions hold where the highest level is structured; where it is clinician-led they
  hold unless a clinician is present and a screening result is recorded.
- W5 Agents and devices never start a run alone: agent-proposed actions are at most ask; automatic firing is
  allow only with `automatic_firing` consent and two or more signals.
- W6 Every ask or hold names a virtue or precept, a plain reason and who can resolve it.
- W7 Audit: every decision is logged; `verify` is true for an untouched log and false after any edit, removal or
  reordering; JS and Python hashes agree.
- W8 Link: with CONTAIN's pause active the state is at least Stabilisation after `link`; `link` never lowers it.
- W9 Pages: no page calls CONTAIN `decide` directly; in the browser a clinician-led plan holds in Workplace and is
  allowed in Clinical with a clinician present and a screening result recorded.
