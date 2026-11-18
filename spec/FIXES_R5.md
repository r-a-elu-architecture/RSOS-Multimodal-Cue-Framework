# FIXES_R5 — fixes from the fifth independent review

Status: registered 2026-11-16 (d633b5a), before code; code 9ab5f78; results in §6. Review: branch `review/r5`, commit c21e634 (reviewed dev at 2dacc02;
0 blockers, 10 should fix, 8 notes). Author's decision on R5-8: restore the registered escalation count.

Two design choices of FIXES_R4 are replaced:
- The level of a run was matched to known origins by exact text, so any no-op edit lowered it. It is now matched on
  the compiled content (§2).
- The gate held one session; a refused request replaced it, and a run's saved domain overrode the live one. It now
  keeps every session apart (§1).

## 1. Output gate (`docs/js/outlet.js`)

| ID | Rule |
|---|---|
| O1 (R5-1) | The domain used for every check is the stricter of the session's own extra and the live `RSOSDomain`: the lower `max_level` (unknown → structured) and `memory_work_allowed` false if either is false. |
| O2 (R5-2) | The gate keeps a list of sessions. `open` and `adopt` return a handle; `close(handle)` removes that session, `close()` removes all. A refused `open` changes no existing session. Output passes only if no session is held and at least one live session (or, with no session, the page's declared one) allows it. The 1-second and storage re-checks cover every live session; when any turns to hold, everything stops and `rsos-outlet-hold` is dispatched. |
| O3 | A session that expires is removed (it is not a hold); a held session stays until its page closes it. |
| O4 (R5-16) | The player opens the run's session after the check-in dialog, and asks the Watchdog again at that moment. |
| O5 (R5-17) | `RSOSOutlet.session()` and `sessions()` return frozen copies. |
| O6 (R5-12) | The direct sound paths of the device carrier, glyphs and trials pages play nothing when `RSOSOutlet` is missing. |
| O7 (R5-13) | Recorded as intended: device- and agent-triggered vibration (posture cue, heart-rate offer, agent status codes) carries one signal, so the Watchdog asks and nothing vibrates on its own; the on-screen offer stays. |

## 2. Level from content, wherever it goes (`docs/js/lineage.js`, new; player and device page)

- **Origins**: every saved program with a level above self-guided: plan nodes (rules of FIXES_R4 LM1 and LOW_MOOD),
  saved therapist programs (`level`, `memory`), programmed cues (their tier). Each origin is compiled with RSX.
- **Elements** of a compiled program: the folded text (§3) of every SAY, SEE, cue, FEEL and GESTURE event and every
  future; each tier's name and mode; each pulse (on/off/count). Breath, tones, timing, marks and comments are not
  elements.
- **Distinctive elements** of an origin: its elements that no built-in program has.
- A run **inherits** an origin's flags when either:
  - it has one of the origin's distinctive elements. A distinctive text of 8 or more characters also counts when it
    appears as whole words inside a longer text.
  - its element set is at least 80% the same as the origin's (shared / all).
- The run's elements come from the source actually compiled for the run, futures fields included (R5-6).
- The player (R5-3, R5-4, R5-5) and the device page's "Play on the band" (R5-7) use the same function. An edited
  program whose compiled tier is in observer mode is clinician-led memory work, as before, now read from the compiled
  program as well as the source.
- **Codes** (R5-11): on the device page, a typed or button sequence is held when any of its codes is the code of a
  held plan node.
- **Limit, recorded:** a program in which the person removes every distinctive element and most of the rest is the
  person's own program. Its content rules (tiers, markers, observer mode, Spine) still apply.

## 3. Text folding and parity (`safety.py` / `safety.js`, `watchdog.py` / `watchdog.js`; R5-5, R5-9, R5-14)

- `fold(text)`, identical in both languages, in this order:
  1. Line ends normalised.
  2. NFKC applied.
  3. Zero-width characters and the soft hyphen removed.
  4. Listed look-alike letters mapped to ASCII: Cyrillic and Greek capitals and small letters, Turkish ı and İ.
  5. Every whitespace character JavaScript's `\s` accepts, and every C0 control except the newline, mapped to a
     space.
  6. Runs of spaces collapsed.
  7. A–Z lowercased.
- The level patterns and the Spine word lists match folded text with ASCII-only patterns:
  - Python compiles them with `re.ASCII`, and `\d` becomes `[0-9]`.
  - Programmed-cue ids are compared folded.
  - Whitespace between keyword and value is optional where RSX allows it.
- `level_of_program.text` is the folded text.
- `event_from_check` accepts a finite number (not a bool), or a string of ASCII digits with an optional sign and one
  decimal point. Anything else is omitted, in both languages.
- `exit` repairs a history that is not a list, in both languages (JavaScript already does).
- The parity test uses the reviewer's generator (`review/r5/parity.py` inputs) and must show 0 differences.

## 4. Other

| ID | Rule |
|---|---|
| R5-8 | **Author's decision:** restore the registered count: 3 or more self-checks of intensity 7 or more within the last 7 days, on any days. The message says "several times this week". FIXES_R4 §5's "No threshold changed" is corrected in the record, and LOW_MOOD §2, L4 and HANDOFF are brought back in line. |
| R5-15 | The night summary's nightmare clause and the therapist page's "re-living" link are memory-work text (hidden where memory work is not allowed). |
| R5-18 | Code commit messages carry no results. |

## 5. Acceptance

- Q1 `scripts/check_fixes_r5.py` drives the real page paths: Start and Begin in the player, the cue's "Load into the
  player" button, the program menu's change event, the device page's Play button, the code buttons and typed codes,
  and a domain switch in a second tab. It covers every R5-1 to R5-7 and R5-11 to R5-16 reproduction in
  `review/r5/attacks.py`, each with its expected outcome. It fails on 4f4b6d8 and passes after the fix.
- Q2 The parity script reports 0 differences on the reviewer's inputs: levels, Spine, eventFromCheck, exit.
- Q3 All suites and browser checks pass. Built-in programs run as before with no plan saved. No threshold changes
  besides the R5-8 restoration.

## 6. Results (recorded after the code commit 9ab5f78)

- Q1 met. `scripts/check_fixes_r5.py` (real page paths, expected outcome per scenario) on 4f4b6d8: 16 failures (R5-1 ×2,
  R5-2 ×2, R5-3 ×2, R5-4, R5-5, R5-6, R5-7 ×2, R5-11, R5-12, R5-15, R5-8, R5-16/17). Two of them (the second R5-2
  check and R5-16/17) fail on 4f4b6d8 only because they read the new `RSOSOutlet.sessions()`. On 9ab5f78: 0 failures,
  0 page errors. The controls pass: with no plan saved the built-in Observer plays on the band, every built-in program
  is allowed in Personal, and a code that belongs to no held node plays.
- The reviewer's own `review/r5/attacks.py` on 9ab5f78: A1, A1b, A2, A4–A8, A10–A14 show the expected holds. A3 and A9
  end with a script error only because the run is now stopped (A3: no session left after the switch) or never starts
  (A9).
- Q2 met. `rsso/tests/test_fixes_r5.py`: 7 passed (6 043 generated programs: level and fold identical; check answers,
  exit and Spine identical; look-alike letters and Unicode spaces raise the level; built-in list matches
  `docs/protocols`). `review/r5/parity.py`: 0 differences.
- Q3 met. `rsso` suite 263 passed, 1 expected failure (TRIAL_LOOP T4, unchanged); `rsxv` 130 passed;
  `scripts/check_all.sh` all passed; the 9 browser checks exit 0. The only threshold change is the R5-8 restoration.
- Implementation detail beyond §3, recorded: Spine also tests the folded text with backslash escapes and punctuation
  (other than `% . -`) read as spaces, because RSX keeps `\t` in a string as two characters (A10 "tab"). Both
  languages do the same.
- Limits that stand: a program from which the person removes every distinctive element is their own (§2); folding
  does not remove accents (NFKC keeps "ẓ"), so a Spine word with an accented letter is not matched; page code is
  trusted; a static site cannot authenticate.
