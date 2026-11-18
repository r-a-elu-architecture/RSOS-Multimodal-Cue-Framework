# SITE_NIGHT — the World page shows the Person Lab and tonight's results (18 November 2026)

Status: registered 2026-11-18, before any code. Results in §4, in a separate record commit. Context: TURN_RATINGS and
CUE_RESOLVE are recorded on `dev` (register rows Round 8e and 8f); the register and evidence labels already show 44 tests,
but no page text says what they found.

## 0. What a check of the development site found (local render of `docs/` at 2e6c334 + 371b159)

1. The World page's title, lede and run notes name only "software agents and a simulated person". The Person Lab (100 lab
   persons and agents) is on the page, but it starts after "What you are looking at", about 2,600 px down, with no link from
   the top. Visitors who arrive from the System page's Person Lab box do not find it.
2. The System page's Person Lab box lists `docs/world.html#lab` only as a file name; there is no link that opens the lab.
3. The simulated-person note still ends "In this model an uninterrupted cue blocks later cues; see STAB_DEFAULT §5", with no
   word that the loophole has now been closed and measured (CUE_RESOLVE).
4. "What you are looking at" names T-AP as the most relevant result; TURN_RATINGS and CUE_RESOLVE are not mentioned.
5. The Person Lab's "Read this first" note and its effect choice ("Equal (registered placeholder)") do not say that
   people's own ratings in ESConv show no difference between supporter actions (TURN_RATINGS), which is what the equal
   effects now agree with.
6. The System page's Person Lab evidence line lacks TURN_RATINGS.
7. Bug: the World page marks two navigation items as the current page (World and Agents).

## 1. Changes

- **N1, title and lede.** Title: "Software agents, a simulated person and 100 lab persons, run by one architecture." The lede
  names the three parts. Under it, a line of in-page links: Agent system and simulated person · Person Lab · What the results
  say.
- **N2, findings from data, never typed.** `rsxv/rsxv/site_findings.py` reads `rsxv/results/turn_ratings.json` and
  `rsxv/results/cue_resolve.json` and writes `docs/data/world_findings.json` with the sentences and the numbers they
  contain. The page shows them in a short section "What the latest results say" under the evidence label (id `findings`),
  in the simulated-person note (the CUE_RESOLVE line replaces the STAB_DEFAULT §5 sentence, which it extends), in "What you
  are looking at" and in the Person Lab note (the TURN_RATINGS line).
- **N3, Person Lab effect choice.** The option text becomes "Equal (placeholder; ESConv ratings show no difference)". The
  value `placeholder` and every computation stay the same; `personlab_lab.json` is unchanged.
- **N4, System page.** The Person Lab box gains an "Open the Person Lab" link to `world.html#lab` (an optional `open` field
  any box may carry), and its evidence part adds TURN_RATINGS.
- **N5, navigation.** Only World is the current page on the World page.
- **N6, regeneration.** `check_all.sh` regenerates `world_findings.json` with the other generated files and checks it is
  unchanged.

Nothing in the World runs, the Person Lab data or any result changes. The World runs stay on person model v2
(CUE_RESOLVE §4: v3 is not adopted by that step).

## 2. Checks (fixed now)

`scripts/check_site_night.py docs` (Playwright, Chrome, desktop 1280×800 and phone 390×844):
- C1: the World h1 contains "Person Lab"; the in-page link to `#lab` exists and the target is in the page.
- C2: every number shown in the findings section, the simulated-person note, "What you are looking at" and the Person Lab
  note equals the number in `world_findings.json`, and those equal the result files (checked in Python).
- C3: the System page's Person Lab box shows a link whose href ends `world.html#lab`.
- C4: exactly one navigation item has `aria-current="page"` on the World page.
- C5: no page errors; the effect choice still offers `placeholder` and `illustrative`.
- C6: `check_profiles.py` (no crisis wording), `check_personlab.py`, `check_evidence.py`, `check_site_catchup.py` and
  `check_all.sh` pass.

## 3. Not in this step
Switching the World runs to person model v3; any new result.

## 4. Results

(recorded after the code commit)

### Results (code 083d18a)

- N1–N6 applied. **Disclosed deviation:** N1's title wording ("…and 100 lab persons…") did not contain "Person Lab",
  which C1 requires; C1 was kept and the title became "Software agents, a simulated person and a Person Lab of 100, run by
  one architecture." Found by the check's first run (18/20), before the code commit.
- `scripts/check_site_night.py docs`: **20/20** (desktop and phone): C1 title and #lab link; C2 every number shown equals
  `world_findings.json`, which equals the result files; C3 the System box links to `world.html#lab`; C4 one current
  navigation item; C5 effect values kept, 0 page errors.
- `check_profiles`, `check_personlab` 31/31, `check_evidence` 168/168, `check_site_catchup`, `check_release` and
  `check_all.sh` pass.
- Typed, not generated (disclosed): the System box's evidence part repeats "6,352 ratings" from TURN_RATINGS by hand, like
  the other parts of that box.

## 5. Amendment A1, 18 November 2026 (owner's report, before its code): "Run session" seems to do nothing

Reproduced in Chrome on 47544cc: the button runs, with no page error. But a change to any choice already reruns the session,
sessions are deterministic, and under equal effects the agents and always Bear are identical, so a click redraws the same
table with no visible sign. Also found: the summary lowercases the effect label ("esconv ratings").

- **A1.1** A status line under the controls (`#labStatus`, `aria-live="polite"`), updated on every run: run number, person,
  policy and effects, and one sentence: "Sessions are deterministic: the same choices give the same session; changing a
  choice runs it at once."
- **A1.2** The session pane is highlighted briefly on every run; on a phone a click on Run session scrolls it into view.
- **A1.3** The summary keeps the effect label's capitals ("ESConv").
- Checks added to `check_site_night.py`: C6 a click on Run session increases the run number shown; C7 the summary contains
  "ESConv" when the equal effects are chosen. No computation changes; check_personlab must still pass.

### A1 results (code a539772)
`check_site_night` 24/24 (C6 run number, C7 "ESConv" added), `check_personlab` 31/31.

## 6. Amendment A2, 18 November 2026 (owner's request, before its code): the Person Lab plays like the World run

The owner: the Person Lab should be watched the way the World run is, so people see the same autonomous system working on a
lab profile, decision by decision. A1's static status line does not do that.

- **A2.1 Controls** as the World run: Lab person, Effects, Policy, Speed (slow, normal, fast), **Play** (pause while
  playing) and **Restart**. Changing a choice computes the session and shows tick 1, as the World run does.
- **A2.2 Live person panel:** bars for intensity (1–5), arousal, openness and progress toward the desired state at the
  current tick; chips for the archetype now running, calm or aroused (arousal against the threshold τ), and the TARGET node.
  Always Bear's intensity at the same tick is shown beside it.
- **A2.3 Profile tree:** the node in the current TARGET is marked as the session plays.
- **A2.4 Timeline:** the existing chart gains a cursor at the current tick; a click on the chart jumps to that tick.
- **A2.5 "Why, at tick N"**, built from the session's own values, never typed per tick: (1) what the agents sensed (arousal
  before the step against τ, openness, and whether a cue arrived), (2) which rule chose the archetype (aroused: Bear
  steadies; calm: every sixth calm tick Lion shares, otherwise Raven clarifies while openness < 0.5, Tiger takes a step
  from 0.5), or the fixed policy, (3) the RSX-V program run, with its TARGET, (4) the result: intensity before and after,
  progress, the person's feedback.
- **A2.6** The RSX-V program of the current tick is shown; the full tick log stays below, complete at once, and a click on a
  row jumps there.
- **No change to the engine** (`docs/js/personlab.js`) or any data; Python–browser parity untouched.

Checks replacing A1's C6 (`check_site_night.py`):
- **C6′** Play advances the tick shown; Restart returns to tick 1.
- **C8** For every lab person, policy and effect set, the archetype the "Why" chain derives from the sensed values equals the
  archetype the engine chose, on every tick (600 sessions, 12,000 ticks): the explanation is the engine's rule, not a story.
- **C9** A click on the chart moves the current tick; the TARGET chip and the marked tree node match that tick's row.
- C5, C7 and `check_personlab` 31/31 must still pass.

### A2 results (code c61b885)
- A2.1–A2.6 applied; `docs/js/personlab.js` and every data file unchanged.
- `check_site_night` **35/35** on desktop and phone. **C8: the "Why" chain derives the engine's archetype on all 12,000
  ticks (600 sessions), 0 mismatches.** C6′ Play advances and Restart returns to tick 1; C9 a chart click moves the tick and
  the TARGET chip and marked tree node match that tick's row.
- **Check fix, disclosed:** C9 first failed because the check clicked the chart while it was outside the viewport; the
  page worked (a scrolled click jumped to tick 17). The check now scrolls the chart into view before clicking.
- The lede's "run a session" became "press Play to watch the session tick by tick".
- `check_personlab` 31/31, `check_profiles`, `check_evidence`, `check_release` and `check_all.sh` pass.

## 7. Note, 18 November 2026 (FIXES_NIGHT TR-1, TR-2, CR-1, SN-1)
§0.5's "which is what the equal effects now agree with" and N3's option text "show no difference" overstated TURN_RATINGS;
the page's cue sentence overstated CUE_RESOLVE. All three are corrected through `rsxv/rsxv/site_findings.py` (now also
reading `cue_resolve_decomp.json`) and the option text; check C2 still ties every number to the data.
