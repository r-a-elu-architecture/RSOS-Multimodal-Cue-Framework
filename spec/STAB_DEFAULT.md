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

## 5. Results
(recorded after the code, in a separate commit)
