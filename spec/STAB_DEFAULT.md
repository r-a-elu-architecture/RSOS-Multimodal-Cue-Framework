# STAB_DEFAULT — Phase 3, step 12: the agents' defaults follow the evidence

Status: registered 2026-11-17, before any code. Results in §5, in a separate record commit.

## 0. What was found before planning the code

- **No person-facing page switches archetypes.** Ledger-based switching exists only in the RSX-V simulation (`World`,
  default policy "watchdog") and in the World page, which replays recorded runs of that simulation. The person-facing pages
  (copilot, identity, night) never choose an archetype adaptively. The roadmap's "person-facing agents default to
  switching" was the author's assumption, and it was wrong. This step is therefore smaller than planned.
- **The asking-back finding is not applied** (CTX_PREF_HH, CTX_PREF_WC). It holds for everyday requests only, and the
  personal context was never testable. The copilot's questions are deliberate personal prompts, and nothing in the project
  generates replies to everyday requests. Applying it would go beyond the evidence. It is recorded in AGENTS.md as guidance
  for any future generator of everyday replies.

## 1. D1: the World page shows the audit's baseline beside the Watchdog

- `rsxv.site_traces` runs, for every recorded run, a second person World on the same simulated person. It has the same
  seed, the same events and the same timing, under the fixed Bear policy.
- It records the per-tick reward and the mean as `summary.person_mean_bear`, and Bear's per-tick reward as `p.rb` in each
  tick.
- The page shows both means beside the person panel, labelled "Watchdog switching" and "Always Bear (the simple baseline
  that beat switching in BASELINE_AUDIT)", with a link to the audit.
- The page does not claim which is better on a single recorded run. It shows the numbers.
- **Every existing field of `world_runs.json` must be unchanged** (checked by a diff of the earlier fields). The added World
  has its own random streams.

### 1a. Amendment, 17 November 2026 (before the page code; after the data generator was first run)
- Running the generator showed a property of person model v2. A cue that is never interrupted stays open, and while a cue
  is open no new cue can start (`PersonEnvV2.step`). Bear cannot interrupt with an untrained module, because only Tiger
  trains it. So under always-Bear the first cue stays open and blocks every later cue, including the page's storm.
- That makes the Bear number on the World page partly a loophole of the model. D1 therefore also records, per run, the
  number of cues and whether one is still open at the end, for both the Watchdog and the Bear person (`summary.cues`).
  The page shows that count beside the two means, with one line: "In this model an uninterrupted cue blocks later cues;
  see STAB_DEFAULT §5".
- Scope for BASELINE_AUDIT: person model v1 (`world.PersonEnv`) has no cue mechanism, so A3, A4 and T-AP's primary run are
  not affected. T-AP's confirmation run used person model v2 and may be affected. This is recorded in §5 and in the
  audit's spec, and left as an open note: a person model v3 where cues can resolve without the module.

## 2. D2: a stabilise-first default for new person-facing uses

- `rsxv.world.STABILISE_FIRST = {"policy": "fixed", "fixed_mode": "BEAR"}` and `rsxv.world.person_world(env, seed, **kw)`,
  which builds a World with that policy. Anything new that runs on a person starts there.
- `World`'s own default stays "watchdog", so every recorded experiment reproduces.
- AGENTS.md §4 gains a "Default" paragraph saying this and citing BASELINE_AUDIT. Switching is described as an experiment.

## 3. Tests

- T1: `person_world` returns a World whose policy is fixed Bear, and its modes are Bear on every tick unless the safety
  fallback applies.
- T2: `site_traces` adds `person_mean_bear` and `rb` without changing any earlier field (a fixture run: seed 11, no event).
- T3: `scripts/check_site_catchup.py` checks that the World page shows both means, read from the data.
- T4: all suites, `check_all.sh` and the browser checks pass.

## 4. Not in this step
Evidence labels (step 13), the Agents page board (step 14), the home page (step 15).

## 5. Results (recorded after code c4f3bd0)

- D1: all 15 recorded runs gained the Bear run. Every earlier field of `world_runs.json` is unchanged (checked by diff).
- **The §1a loophole holds in every run.** Under always Bear the simulated person received exactly 1 cue in all 15 runs,
  and it was still open at the end of each. Under the Watchdog it received 3 to 23 cues. Bear's mean per tick
  (0.087–0.093) is therefore not evidence of good care in person model v2. The page shows the counts beside the means.
- D2: `world.person_world` and `world.STABILISE_FIRST` are in place. `World` still defaults to "watchdog". AGENTS.md §4
  states the default and the asking-back guidance.
- Found while doing D1: the World page still called T-AP "the confirmed result most relevant here … helps the simulated
  person". It now says T-AP passed its registered test but fails the baseline audit.
- Checks: RSX-V 174 passed; `rsso` 291 passed, 2 skipped, 1 xfailed; `check_all.sh` passed; `check_site_catchup.py`
  (with step 12), `check_trial_loop.py` and `check_watchdog.py` exit 0.
- **Open:** person model v3, where a cue can resolve without the module (or where an open cue does not block later cues).
  Until then, any stabilise-first result on person model v2 carries this caveat.

## 7. Note, 18 November 2026 (FIXES_NIGHT CR-1): the caveat stays, with a measured reason

CUE_RESOLVE closed the §1a loophole in a person model v3. Always Bear still scores above the Watchdog there (−0.0193
[−0.0266, −0.0115] per tick), but the review's decomposition, reproduced in `rsxv/results/cue_resolve_decomp.json`, shows
that the whole lead comes from the Watchdog meeting about 11% more cues (10.69 against 9.60 per person; a cue costs the same
under both, −3.66 per trigger tick). On all other ticks the Watchdog is ahead (+0.0143 [+0.0042, +0.0241]). So D2
(stabilise-first as the default for anything new that runs on a person) rests on caution, not on evidence that stabilising
helps, in these models or in people. The next fair comparison draws cue arrival times in advance, independent of the policy.
