# AGENTS_ANCHOR: a Bear-anchored Watchdog for the World agents

Registered 18 Nov 2026, before its code and before any run. Follows LINX_MCP and SUBSTANCES_NOW in the same
analysis → fix → efficiency chain, now on the World's agent system.

## 1. Analysis (from the code and the register)

On the person side the Watchdog loses to "always Bear" in every stated model; on person model v3 (CUE_RESOLVE Part B,
R = 6) by **−0.0193 per tick** [99% CI −0.0266, −0.0115]. `rsxv/world.py` shows three causes:

1. **Exploration cost:** on 20% of ticks the Watchdog runs a random allowed mode to feed its ledger.
2. **Switching on point estimates:** it switches by min-max scaled ledger means, ignoring the ledger's own intervals.
3. **Wrong anchor:** it starts in Lion and treats every mode alike, although Bear is the measured safe default
   (STAB_DEFAULT D2).

## 2. Fix: policy `anchored` (new; the existing policies and recorded runs are unchanged)

- Starts in **Bear** and returns to Bear by default.
- Switches away from Bear in a context only when the ledger's interval **rules Bear out**: the best other mode's lower
  95% bound is above Bear's upper bound in that context (`FitLedger.ci`, unchanged). Switches back when that stops
  holding.
- Explores on **5%** of ticks (not 20%), with the same disclosed micro-randomisation.
- The Watchdog's safety actions (override, re-entry), the Spine check and the safety modes are untouched.

## 3. Design (fixed now)

Person model v3 (`PersonEnvV2`, trig_rate 0.15, self_resolve R = 6), 120 ticks, mission score, **200 fresh persons,
seeds 270000–270199** (not used before). Arms: ANCHORED, BEAR (`person_world`), WATCHDOG. Paired bootstrap 99% CIs
(2,000 resamples, seed 12345), as CUE_RESOLVE. Secondary, reported without a threshold: the same three arms on the
agent environment `AgentEnvV2` (same seeds).

## 4. Predictions

| # | Prediction | Pass if |
|---|---|---|
| **A1** | Never worse than the safe default (non-inferiority) | ANCHORED − BEAR: 99% CI lower bound ≥ −0.00193 (one tenth of the Watchdog's v3 loss) |
| **A2** | The Watchdog's gap closed 10× | \|ANCHORED − BEAR\| point estimate ≤ 0.00193 |
| **A3** | Better than the old Watchdog | ANCHORED − WATCHDOG: 99% CI lower bound > 0 |
| **A4** | 10× fewer handovers | switches per person: ANCHORED ≤ 0.1 × WATCHDOG |
| **A5** | Safety unchanged | 0 Spine violations in every run; `world_runs.json` and every recorded result unchanged; `check_all.sh` passes |

Sealed expectation (written now): A1, A3, A4 likely; A2 uncertain (exploration at 5% may cost more than 0.00193 per
tick).

## 5. Not in this step

The World page keeps showing the recorded runs; showing ANCHORED there is a separate step once these results are in.
Stated models only: nothing here is evidence about people.
