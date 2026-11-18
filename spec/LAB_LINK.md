# LAB_LINK — play the Person Lab from the agent system pane

Status: registered 2026-11-18, before any code. Results in §3. The author's decision (18 November 2026): the Person Lab is
not added as a node of the agent graph (every circle there is one of the six agents and every arrow a dependency; the lab
is 100 invented lab persons with agents working toward each one's desired state). Instead the agent pane gets one link
that plays the lab.

## 1. Change

- `docs/world.html`, agent system pane, under the line `#aNow`: a link "Person Lab: 100 lab persons — play"
  (`#labJump`, `href="#lab"`). On click it scrolls to the Person Lab section and starts its run by the lab's own Play
  button, only if the lab is not already playing (button text "Play"). Without JavaScript the link still jumps to `#lab`.
- Nothing else changes: no engine, data, wording rule, threshold or storage key.

## 2. Checks (fixed now)

- K1: `check_all.sh` passes; `check_site_night` and `check_personlab` still pass.
- K2: a new browser check `scripts/check_lab_link.py docs`: the link is inside the agent pane; clicking it puts `#lab` in
  view and the lab button reads "Pause" (playing); a second click does not stop it; 0 page errors, on desktop and phone
  widths.

## 3. Results

(recorded after the code commit)

### Results (code in the commit before this one)
- **K1:** `check_all.sh` "All checks passed"; `check_site_night` 35/35; `check_personlab` 31/31, 0 page errors;
  `check_profiles` fails []; `check_evidence` 168/168.
- **K2:** `scripts/check_lab_link.py docs` 10/10 at 1280 px and 390 px: the link is in the agent pane; one click brings
  `#lab` into view and the lab button reads "Pause"; a second click leaves it playing; 0 page errors.
