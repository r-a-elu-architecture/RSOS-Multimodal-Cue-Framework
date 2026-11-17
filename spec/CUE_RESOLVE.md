# CUE_RESOLVE — person model v3: a cue resolves on its own after a window (WORLD_10X planet 2)

Status: registered 2026-11-18, before any code. Results go in §7, in separate record commits. Context:
spec/STAB_DEFAULT.md §1a and §5 (the loophole), spec/world10x/WORLD_10X.md row 2, spec/BASELINE_AUDIT.md.

All environments are stated models. Nothing here is data about people.

## 0. Why

In person model v2 (`rsxv/rsxv/person2.py`, `PersonEnvV2.step`) a cue stays open until a module interrupts it, and no new
cue can start while one is open. Only Tiger trains the module. Under always-Bear the module is never trained, so the first
cue stays open for the rest of the run and blocks every later cue: exactly 1 cue in 15 of 15 recorded runs, still open at the
end of each (STAB_DEFAULT §5). Bear's mean per tick on person model v2 is therefore partly the absence of new cues.

Particle (WORLD_10X row 2): the refractory period. A cue that is not resolved by the module ends on its own after a window,
as an episode ends without help, with no relief from the module. New cues can then arrive.

## 1. Mechanism (person model v3 = v2 + one parameter)

- `PersonEnvV2(..., self_resolve=None)`. With `None`, behaviour is exactly v2, so every recorded result reproduces.
- With an integer R: at the end of a tick, a cue open for R or more ticks since its trigger closes. It is marked
  `self_resolved` if it was never interrupted, `resolved_late` otherwise. No change to distress, arousal or the module at
  that moment; the chain's distress already added stays. The cue counts as resolved in `outcomes()`; the counts of
  self-resolved and late cues are reported separately.
- **R = 6 ticks** (two minutes at 20 s per tick) is the registered value. R = 3 and R = 12 are reported for sensitivity only.

## 2. Part A: the loophole (the WORLD_10X row 2 target)

The 15 recorded configurations of `rsxv.site_traces` (seeds 11–13; no event, storm at 40 and 90, shift at 40 and 90;
160 ticks), each person under always Bear (`person_world`) and under the Watchdog, on v2 and on v3 (R = 6).

Measures per run:
- **stuck at end:** a cue open at the last tick that has been open for 20 ticks or more. (A cue that has just started is
  not stuck; the WORLD_10X wording "open at the end" is refined here, before any run, for that reason.)
- **blocked ticks:** ticks at whose start a cue was open, so no new cue could begin.
- cues per run.

**Part A passes** when, under always Bear on v3, at most 1 of 15 runs has a stuck cue (v2: 15 of 15 open), **and** the total
blocked ticks under always Bear are at most one tenth of v2's.

## 3. Part B: does always-Bear still beat the Watchdog once the loophole is closed?

- 200 fresh simulated persons, seeds 260000–260199 (not used by any earlier test), `PersonEnvV2(seed, trig_rate=0.15)`,
  120 ticks, `World(score="mission")`.
- Arms: WATCHDOG (`policy="watchdog"`), BEAR (`person_world`), LION (`policy="fixed"`, Lion). Each arm on v3 (R = 6) and,
  for reference, on v2 (same seeds).
- Outcome: mean mission score per tick per person. Contrast WATCHDOG − BEAR, paired bootstrap over persons (2000
  resamples, seed 12345), two-sided 99%.
- **Verdict on v3:** BEAR STILL WINS if the upper bound is below 0; WATCHDOG WINS if the lower bound is above 0; TIE
  otherwise.
- Reported beside it: the same contrast on v2; the loophole share = (BEAR − WATCHDOG on v2) − (BEAR − WATCHDOG on v3); cues
  per person per arm; final distress; WATCHDOG − LION and BEAR − LION on v3; R = 3 and R = 12 for the v3 contrast.

**Sealed predictions:** P(Part A passes) = 0.90. P(BEAR STILL WINS on v3) = 0.55; P(TIE) = 0.30; P(WATCHDOG WINS) = 0.15.

## 4. What follows (fixed now)

- **Part A passes:** person model v3 replaces v2 for every new person-side test; v2 stays for reproducing recorded runs.
  The World page's "always Bear" figure gains the v3 number beside the v2 one.
- **BEAR STILL WINS on v3:** the stabilise-first default (STAB_DEFAULT D2) stands without the loophole caveat.
- **TIE or WATCHDOG WINS on v3:** Bear's earlier advantage on v2 was the loophole; STAB_DEFAULT's caveat becomes a
  correction, and BASELINE_AUDIT's T-AP confirmation note (person model v2) is updated.
- Nothing here says anything about people. ESConv showed no measurable effect of supporter actions on people's own ratings
  (TURN_RATINGS), so no setting of this model can be fitted from that data.

## 5. Tests (before any run)

- T1: with `self_resolve=None`, a run is identical tick by tick to v2 (rewards and events).
- T2: with R, a cue never interrupted closes after exactly R ticks and is marked `self_resolved`; a new cue can start after it.
- T3: the measures of Part A on a fixed small run.
- T4: all suites and `check_all.sh` pass; `docs/data/world_runs.json` is unchanged by this step.

## 6. Not in this step
The World page and site_traces stay on v2 until Part A is recorded (then a separate registered step).

## 7. Results

(recorded in separate commits)
