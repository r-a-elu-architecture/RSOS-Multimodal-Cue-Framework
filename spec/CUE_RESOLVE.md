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

### Results (code 5749ddb; run once, 30 s; `rsxv/results/cue_resolve.json`)

**Disclosed:** a smoke run (`--quick`) on 10 unregistered persons (seeds 990000–990009, Part B only) ran before the
registered run, and its direction was seen. Nothing was changed between it and the registered run.

**Part A: FAIL by the registered rule.**

| 15 recorded configurations | stuck at end | blocked ticks | cues (per run) | mean per tick |
|---|---|---|---|---|
| v2, always Bear | 15 / 15 | 2,335 | 15 (1 each) | +0.0918 |
| v2, Watchdog | 0 / 15 | 1,660 | 134 (3–23) | +0.0410 |
| **v3, always Bear** | **0 / 15** | **1,311** | 224 (14–16) | +0.0131 |
| v3, Watchdog | 0 / 15 | 987 | 242 (14–20) | +0.0128 |

- The stuck-cue condition is met: 15 / 15 → 0 / 15.
- The blocked-ticks condition is not: 2,335 → 1,311 is 1.8× fewer, not 10×. An independent recount from each cue's start
  and end gives the same totals.
- **Why, stated after the run:** closing the loophole lets about 15× more cues arrive (15 → 224), and each new cue is
  legitimately open for up to 6 ticks. "Blocked ticks" counted those normal episodes as well as the stuck one, so a 10×
  reduction was not a sensible target for this measure. This is a fault of the registration (and of WORLD_10X row 2's
  wording), not of the mechanism; the verdict stands as registered.

**Part B: BEAR STILL WINS on v3.**

| 200 fresh persons, 120 ticks | Watchdog − Bear (99%) | Bear | Watchdog | Lion | cues per person (B / W) |
|---|---|---|---|---|---|
| v2 (reference) | −0.0406 [−0.0464, −0.0353] | +0.127 | +0.086 | +0.038 | 1.0 / 5.1 |
| **v3, R = 6** | **−0.0193 [−0.0266, −0.0115]** | +0.054 | +0.035 | −0.032 | 9.6 / 10.7 |
| v3, R = 3 (sensitivity) | −0.0147 [−0.0251, −0.0048] | +0.030 | +0.015 | — | 12.6 / 13.0 |
| v3, R = 12 (sensitivity) | −0.0221 [−0.0281, −0.0167] | +0.079 | +0.057 | — | 6.7 / 8.4 |

- **Loophole share:** Bear's margin over the Watchdog falls from 0.0406 to 0.0193 per tick. **About half (0.0214) of
  Bear's advantage on v2 was the loophole.** The other half remains with the loophole closed, at every R tested.
- Both still beat Lion on v3 (Watchdog − Lion +0.067 [+0.058, +0.075]; Bear − Lion +0.086 [+0.078, +0.094]). Final distress
  on v3: Bear 0.81, Watchdog 1.73, Lion 5.72.

**Sealed predictions:** P(Part A passes) = 0.90, not met. P(BEAR STILL WINS) = 0.55, the outcome that occurred.

**What follows (§4, as fixed).**
- Part A did not pass, so person model v3 does **not** replace v2 by this step. A follow-up must register a measure that
  separates a stuck cue from normal episodes (for example ticks with a cue open longer than R) before v3 is adopted.
- BEAR STILL WINS on v3: the stabilise-first default (STAB_DEFAULT D2) stands, and the loophole caveat becomes a measured
  size: half of Bear's v2 margin was the loophole, half remains.
- Stated models only. Nothing here is evidence about people (TURN_RATINGS found no action effect in people's own ratings).

## 8. Follow-up B, registered 2026-11-18 (before its code): is v3 adopted?

**Why not a stuck-cue measure.** Any measure of cues open longer than R is circular: in v3 no cue can stay open past R by
construction, so it would pass automatically. The loophole was something else: **in v2 the cues a person meets depended on
the policy** (Part B: 1.0 per person under always Bear, 5.1 under the Watchdog). A person model must expose every policy to
the same world. The adoption test is therefore whether v3 makes cue exposure policy-independent.

- **Disclosed:** Part B already printed cues per person on v3 (Bear 9.6, Watchdog 10.7, Lion 9.7, seeds 260000–260199). The
  threshold below is set after seeing those numbers, so this is a confirmation on fresh seeds, not a discovery.
- **Design.** 200 fresh simulated persons, seeds 270000–270199 (unused), `PersonEnvV2(seed, trig_rate=0.15)`, 120 ticks,
  `World(score="mission")`, arms BEAR, WATCHDOG, LION, on v3 (R = 6) and on v2 for contrast. Measure: mean cues per person.
- **Pass:** on v3, both ratios BEAR / WATCHDOG and BEAR / LION lie in [0.85, 1.15], each with a 99% bootstrap interval
  (2000 resamples over persons, seed 12345) inside [0.80, 1.25]. Reported: the same ratios on v2.
- **Sealed prediction:** P(pass) = 0.80.
- **What follows.** Pass: person model v3 (`self_resolve=6`) becomes the default for **new** person-side tests, named
  `person2.V3`; `PersonEnvV2`'s own default stays v2 so recorded runs reproduce; the World page's recorded runs move to v3
  only by a separate registered site step (owner's decision). Fail: v3 is not adopted, and the next attempt changes the
  mechanism, not the threshold.

### Follow-up B results (code 93a1cbf; run once, 24 s; `rsxv/results/cue_resolve_adopt.json`)

| 200 fresh persons, 120 ticks | cues per person: Bear / Watchdog / Lion | Bear ÷ Watchdog (99%) | Bear ÷ Lion (99%) |
|---|---|---|---|
| v2 | 1.0 / 5.5 / 1.0 | 0.18 [0.16, 0.20] | 1.00 [1.00, 1.00] |
| **v3** | **9.6 / 10.6 / 9.6** | **0.90 [0.87, 0.94]** | **0.99 [0.95, 1.04]** |

- **PASS** (§8): both v3 ratios lie in [0.85, 1.15] with intervals inside [0.80, 1.25]. A confirmation, as disclosed: the
  threshold was set after Part B's numbers on other seeds.
- Found in the contrast: on v2 Lion, like Bear, met exactly one cue per person. The loophole affected every policy that
  cannot interrupt a cue, not only Bear.
- The Watchdog still meets about 11% more cues on v3. That is the model working as written: a cue the module interrupts
  can end before R ticks, so the next one can arrive sooner.
- **Sealed prediction** P(pass) = 0.80: met.
- **Applied (§8):** `person2.V3 = {"self_resolve": 6}` is the default for new person-side tests (AGENTS.md §3.2);
  `PersonEnvV2` keeps v2 as its own default, and `world_runs.json` is unchanged. Moving the World page's recorded runs to v3
  is a separate site step for the owner to decide.
