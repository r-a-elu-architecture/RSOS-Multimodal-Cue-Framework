# TRIAL_LOOP — trials feed the evidence chain

Status: registered 2026-11-16, before code. Code: `rsso/rsso/trial.py` and `docs/js/trial.js` (the bridge),
`rsso/rsso/contribution.py` and `docs/js/contribution.js` (the `trials` scope), `docs/trials.html`, four RSX
programs in `docs/protocols/`. Python and JavaScript identical, tested.

## 1. Problem

TRIAL (spec/TRIAL.md) runs a person's own randomised experiments, but its sessions stay in their own store: an
anchor-versus-sham session never reaches PEAK, so PEAK's strength and GATE's permission to automate ignore the
strongest evidence the person produces. The sham code is drawn with an unseeded random number at play time and not
recorded, so a blind session cannot be audited or reproduced. Trials cannot be contributed to research. The SSIT
design has no programs to practise, and Tier 013 (the lion and the dragon held as one) runs only through the archive
v1 command.

## 2. Where trial evidence goes, and where it does not

| Destination | Trial sessions feed it? | Why |
|---|---|---|
| PEAK (anchor strength) | **yes** | An anchor-versus-sham session is exactly PEAK's probe: the cue alone, or a sham, with calm rated before and after |
| GATE (permission to automate) | **yes, through PEAK** | GATE reads PEAK strength; no separate path |
| Anchor wear (GATE) | **yes** | Playing the anchor when stress starts (cue arm) and firing it in the automatic/manual design are uses outside training |
| Contribution file | **yes**, new optional scope `trials` | Trials pool across people (TRIAL §6) |
| Run log, MEMSTACK, CM1 | **no** | They model program practice; a trial session is a measurement. Writing trials there would change MEMSTACK's reflex curve, CM1's signature, CONTAIN's run review and every run count. They stay unchanged. |

## 3. The bridge (trial module)

- `SHAM_POOL` = `-..-`, `.-.-`, `--..`, `-.-.`, `..--` (the codes the page already used).
- `sham_code(trial, i, anchor_code)`: the sham code for session `i`, drawn with the module's seeded generator from
  `trial.seed` and `i`, from the pool without the anchor's code. Deterministic; identical in both languages.
- `record(trial, before, after, cov, ts, detail=None)`: unchanged, plus an optional `detail` stored on the session:
  `{code_kind: anchor | sham, code}` for sessions that play a code. Sessions without detail are as before.
- `evidence(trial, session)`: `{probe, use}` for the trial's anchor. anchor_vs_sham: one probe
  `{ts, kind: cue | sham, calm_before, calm_after}`; cue_vs_none, arm cue: one use during stress; auto_vs_manual,
  either arm: one use during stress; anything else: neither. The page applies it with PEAK's `add_probe` / `add_use`
  to the anchor in `rsos.anchors`.
- Trial sessions ask the Watchdog before starting (spec/WATCHDOG.md), as every action on a person does.

## 4. Contribution scope `trials`

Optional scope; the schema stays `rsos-contribution/1` (adding an optional scope is backward compatible). Per trial:
`{design, arms, reference, blocks, planned, sessions: [{day, hour, arm, before, after, change, sleep_h, caffeine,
exercise}], result: [{arm, against, diff, lo, hi, p, verdict}]}`. Days are counted from the first day, as for runs.
No anchor names, codes or free text. Ratings outside 0–10 are dropped. Only completed sessions are included.

## 5. Programs

- `ssit_higher.rsx`, `ssit_local.rsx`, `ssit_calm.rsx`: the three SSIT arms (higher-level imagery flowing down into
  the activity; imagery of the activity itself becoming easy; general calming imagery), five minutes each, same
  breath and length so only the content differs.
- `tier013_lion_dragon.rsx`: Lion and Dragon held as one composite (two TIER blocks activated together, glyph
  🦁+🐉, codes joined with a pause), RSX v2.
- All four compile identically in Python and JS within the safety limits, appear in the player's list and in the
  contribution's known protocols. An SSIT trial session links to its arm's program.

## 6. Acceptance

- T1 Parity: `sham_code`, `record` with detail, `evidence` and the `trials` scope identical in Python and JS.
- T2 Sham codes: deterministic for (seed, i); never the anchor's code; always from the pool; recorded in the session.
- T3 PEAK bridge: the mapping in §3 exactly (one probe per anchor_vs_sham session, one use per cue or
  automatic/manual session, nothing otherwise).
- T4 Evidence reaches GATE: 200 simulated people (seeded), 6 anchor_vs_sham blocks each, calm change per session
  = true effect + Gaussian noise (SD 1.0; sham true effect 0). With a true cue effect of 2.0, PEAK status is `strong`
  for at least 80% of people, and for every such anchor GATE's strength check is met. With a true effect of 0, status
  is `strong` for at most 5%.
- T5 Unchanged: MEMSTACK and CM1 results and the run log are identical with and without trials.
- T6 Contribution: `trials` appears only with the scope consented; no codes, names or text; out-of-range ratings
  dropped; contributions without the scope are byte-identical to before.
- T7 Programs: the four programs compile in both languages with identical output and pass the safety limits.
- T8 Browser: an anchor_vs_sham session on the trials page adds one probe to the anchor, shows the seeded sham code
  after saving, asks the Watchdog, and the page has no errors.
