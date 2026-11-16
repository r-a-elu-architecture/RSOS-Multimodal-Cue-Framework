# CEILING — is perfect source knowledge worth anything to the target? (phase 2, Step 11)

Status: registered 2026-11-16 (a45ff0d), before any code or run; code 3a055c7; run and results in §5. Test ID in the register: **W5-CEILING** (transfer family, W5
series).

## 0. Question

The transfer line has failed five times (W5, W5b–W5e), with only T-AP (agents v1 → person) confirmed. Its records
already hold one ceiling: W5's ORACLE, the best target policy chosen with full knowledge of the target.
- For agent → person, ORACLE is +0.240 per tick, against −0.093 for no change. The person model can therefore
  express a large gain.
- The methods never found it.

That ceiling does not separate the two possible reasons:
- the methods estimate badly, or
- the source's knowledge is not worth much to the target, even when it is perfect.

This test removes all estimation on the source side. The target receives the source's **true** best table, mapped
by roles read with full information. If even that does not beat learning from a small target pilot, no transfer
method can do so in these models.

## 1. Design (fixed before any run)

The four W5 directions (`w5_experiments.DIRECTIONS`) use W5's environments, mission score, smoothed context, seeds and
deployment, unchanged.

| Arm | Definition |
|---|---|
| **SRC-TRUE** | The source's true effects: `w5_experiments.truth(src)`, 200 source seeds × 60 ticks. In each context, the archetype with the largest positive effect over LION; LION if none is positive. That archetype becomes a function through the source's roles, read with full information (`w3c_experiments.read_roles(src, ORACLE seeds, 60)`): the first of STABILISE, RESTORE, DRIVE whose role it is. If no role matches, the context stays LION. The function becomes a target archetype through the target's roles, read the same way on the target's ORACLE seeds. Deployed as a `TablePolicy` with no gate. |
| **TGT-TRUE** | The target's own true best table, read the same way from `truth(tgt)`, as a `TablePolicy`. This is the table-class ceiling, comparable with SRC-TRUE. |
| **PILOT-8** | `w5_experiments.decide_pilot_only` on an 8-target pilot, 20 repetitions, with W5's pilot seeds. The per-seed mean over the repetitions is deployed. |
| **NONE** | `TablePolicy({})` (LION everywhere). |

- **Deployment:** W5's 200 deployment seeds of the target, 60 ticks each; the score is the mean mission reward per tick.
- **Contrasts:** paired 99% bootstrap intervals (`w5_experiments.ci`).

## 2. Decision rule (fixed before any run)

For each direction:
- **VALUE:** the lower bound of SRC-TRUE − NONE is above 0. Perfect source knowledge helps at all.
- **ROOM:** the lower bound of SRC-TRUE − PILOT-8 is above 0. Perfect source knowledge beats a cheap target-only
  pilot.
- **Share**, reported only: (SRC-TRUE − NONE) / (TGT-TRUE − NONE).

For the line:
- If **no direction has ROOM**, W5-CEILING fails. In these models even perfect source knowledge is no better than an
  8-target pilot. **The W5 transfer line stops: no W5f.** T-AP stays as recorded.
- If **any direction has ROOM**, W5-CEILING passes for those directions. The bottleneck there is the method, not the
  models. Only those directions may get one new registered method; the others stop.

No threshold is changed after the run. The result is recorded as it is.

## 3. Outputs

- `rsxv/rsxv/ceiling_experiments.py` writes `rsxv/results/results_ceiling.json` and `rsxv/results/ceiling.md`. These
  hold the four tables, the arms, the contrasts and the verdict per direction and for the line.
- Record commit:
  - a W5-CEILING row in `rsxv/RESULTS.md` §8;
  - the regenerated `docs/data/results_register.json`, where the row joins the W5 chain on the results page;
  - the verdict in HANDOFF.
- A test, `rsxv/tests/test_ceiling.py`:
  - a quick run is deterministic;
  - the table mapping follows §1 on a constructed case (an archetype with no role stays LION; the first matching
    function wins);
  - the verdict follows §2 on constructed intervals.

## 4. Not in this step

The repurposing family (W5-R) has no ceiling in its records. A ceiling for it needs its own design around the
mechanism library, so it will be registered separately rather than improvised here.

## 5. Results (full run after the code commit 3a055c7; `rsxv/results/ceiling.md`)

The run took 44 s. Deployment: 200 seeds per direction; PILOT-8: 20 repetitions; intervals at 99%.

| Direction | SRC-TRUE − NONE | SRC-TRUE − PILOT-8 | Share | VALUE | ROOM |
|---|---|---|---|---|---|
| agent → person | +0.333 [+0.326, +0.341] | +0.213 [+0.199, +0.228] | 1.00 | yes | **yes** |
| person → agent | +0.072 [+0.060, +0.083] | −0.003 [−0.008, +0.001] | 1.00 | yes | no |
| agent v2 → person | +0.030 [−0.001, +0.063] | −0.090 [−0.115, −0.062] | 0.09 | no | no |
| person → agent v2 | −0.050 [−0.053, −0.046] | −0.053 [−0.056, −0.049] | −0.56 | no | no |

**Verdict, as registered (§2):** W5-CEILING passes for agent → person only.
- agent → person may get one new registered method.
- person → agent, agent v2 → person and person → agent v2 stop.
- The register records it as "mixed".

**Caveat, recorded with the result and not part of the rule:**
- In agent → person, the source's true table says only "the stabilising function in every context". It reaches the
  target's own optimum (Bear everywhere) because the target's roles were read with full information: 50 target seeds ×
  60 ticks, about 3,000 ticks, against the pilot's 8 × 30.
- The room is real, but a method reaches it only if it reads the target's roles well. That is the design question for
  the one permitted successor. The source contributes the function ("stabilise"); the target data contributes which
  archetype carries it.
- In person → agent v2, perfect source knowledge is harmful: the person's optimum (Bear) is not the v2 agent's
  (Leopard, Tiger).

**Checks after the run:**
- RSX-V suite: 149 passed (including `tests/test_ceiling.py`, 4).
- `rsso/tests/test_site_catchup.py`: 7 passed. W5-CEILING is in the transfer family with parent W5e.
- `scripts/check_all.sh`: all passed.
- `scripts/check_site_catchup.py`: exits 0. The results page shows 34 tests and the chain W5 → … → W5e → W5-CEILING.
