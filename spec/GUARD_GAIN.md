# GUARD_GAIN: the author's glyph choice, and Baseline as keeping the gain (fault prevention)

Registered 18 Nov 2026, before its code. Author's decisions of the same day: accept the five glyph proposals; proceed
with the next Baseline test, then merge.

## 1. Glyphs (author's choice, recorded as an extension)

Raven 🝳, Bear ⟁, Eagle 🜵, Leopard 🜇, Tiger 🝢 (`docs/data/EXTENSION_glyph_proposals_2026-11-18.json`,
`chosen_by_author`). The nodes module and the ledger stay unchanged; the role profiles and the plans read the choice as
an overlay.

## 2. Baseline as keeping the gain (fault prevention) (`AgentEnvV4`, a new subclass; every recorded environment unchanged)

WHOLE_ORGANISM showed that rolling back to the best state does Repair's work and costs the whole. Blocking a bad change
within a tick is already Bear's snapshot. Baseline therefore gets the one function no role has: **prevention**. LION
keeps progress 0.5 and hardens the system for the next 3 ticks: new faults arrive at half the rate. Baseline sensor =
hardened ticks granted. Nothing is repaired or rolled back by Lion.

| # | Prediction | Pass if |
|---|---|---|
| **H1** | Six roles, six signatures | ROLE_ORGANISM's sensor design on AgentEnvV4 (same seeds): 6 of 6 |
| **H2** | Prevention helps the whole | on AgentEnvV4, seeds 295000–295199: ORGANISM (Watchdog on agents) − always Bear: 99% CI lower bound > 0 **and** estimate ≥ the V2 estimate on the same seeds (+0.0146) |
| **H3** | 10× (reported against the registered stretch) | the same margin ≥ +0.146 |
| **H4** | No regression | ledger files unchanged; recorded results unchanged; `check_all.sh` passes |

Sealed: H1 0.85, H2 0.5, H3 0.05, H4 0.9.

## 3. Results (18 Nov 2026; `rsxv/results/guard_gain.json`; tests `architecture/tests/test_guard_gain.py`)

| # | Result | Verdict |
|---|---|---|
| H1 | 6 of 6 roles have their own signature on AgentEnvV4: Monitor 0.33 vs 0; Stabilise 0.29 vs 0; Plan 1.0 vs 0.50; **Repair 0.20 vs 0.04 (kept)**; Drive 1.0 vs 0.50; **Baseline 2.54 vs 0** | **pass** |
| H2 | ORGANISM − always Bear on V4: **+0.0531** [+0.0414, +0.0634], against +0.0146 on V2 (same seeds): **3.6× larger**. The organism's own score rises from −0.0925 to −0.0437 per tick | **pass** |
| H3 | +0.0531 < +0.146 | **fail** (10× not reached) |
| H4 | Ledger files unchanged; recorded results unchanged; `check_all.sh` passes | **pass** |

The glyph choice is recorded in the extension file and read by the role profiles: Monitor 🝳, Stabilise ⟁, Plan 🜵,
Repair 🜇, Drive 🝢, Baseline 🦁. Baseline's function on the agent side is now prevention (keep the gain by making
the next fault less likely); on the person side it is the override's return to agency (WHOLE_ORGANISM's programs).
AgentEnvV4 is a separate variant: the World's recorded runs and defaults are unchanged; adopting it as the agent-side
default is a separate decision.
