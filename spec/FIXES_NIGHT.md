# FIXES_NIGHT — fixes for the night review of 18 November 2026 (pull request #11, `review/night-18nov`, bb00427)

Status: registered 2026-11-18, before any fix. Results in §3. Builder lane (`dev`); the review's own record stays on its
branch for the owner to merge. No recorded number and no registered verdict changes; statuses and wording do.

## 1. Fixes, one per finding

| Finding | Fix |
|---|---|
| **E-1** blocker | `architecture/evidence.py`: a row's source is the **longest** key that starts its name (so "Round 8f" beats "Round 8"); still exactly one source of that length, or an error. `evidence_map.json`: "Round 8f" → `sim` (covers 8f and 8f-B). New guard L4: a row whose result or meaning says "Stated model" can never be `public` or `record`; the build stops if it is. A test covers both. |
| **CR-1** | CUE_RESOLVE §9 records the reviewer's decomposition as information (verdict BEAR STILL WINS stands). The readings that called the remaining half of Bear's lead real are corrected: on v3 the lead comes entirely from the Watchdog meeting about 11% more cues; on all other ticks the Watchdog is ahead. Register 8f, the World page's cue sentence (generated), HANDOFF §4 and STAB_DEFAULT (the caveat stays, with this measured reason). A test with cue arrival times drawn in advance, independent of the policy, is named as the next step, not run here. |
| **FB-1** | Register 8f-B status → `analysis` (FIXES_P2 C1–C3 precedent): the criterion was set after its answer, and Bear ÷ Lion ≈ 1 holds by construction. `person2.V3` stays available but is **not** declared the default for new tests; adopting a v3 is the owner's decision, with policy-independent arrival times as the suggested form (CR-1). CUE_RESOLVE §8 and AGENTS.md §3.2 say so. |
| **TR-1** | The TURN_RATINGS sentences (generator, register 8e, HANDOFF §4) state the outcome as the seeker's rating of the support just given, the crowdworker seekers, the association, and the band: "did not measurably improve the prediction of the seeker's next rating of the support (within ±0.01 squared error)". The reviewer's sensitivity result (per-action effects above about 0.1–0.2 points would have shown) is cited as the reviewer's, unregistered. |
| **TR-2** | Effect option: "Equal (placeholder; consistent with ESConv ratings)". Lab note: equal ratings are consistent with equal effects, but do not show them; the NULL is an equivalence band. SITE_NIGHT §0.5 wording noted as superseded. |
| **SN-1** | All page wording through `rsxv/rsxv/site_findings.py`, so check C2 keeps the numbers tied to the data. |
| **TR-3** | TURN_RATINGS §0's "roughly 10× more outcome events than conversations" is corrected in a dated note: 7,681 ratings over 1,300 conversations is 5.9×; against step 5's 100 test conversations, 6,352 usable events is 63×. |
| **CR-3** | CUE_RESOLVE §4's "no setting of this model can be fitted from that data" is corrected in a dated note: TURN_RATINGS measured ratings of the support, this model's outcome is distress. |
| **W-2** | WORLD_10X stays sealed; a dated pointer line under it points row 2 to CUE_RESOLVE §7. |
| **TR-4** | Noted for future steps: register before writing code, or put the code's tree hash in the registration. |

## 2. Checks (fixed now)

- The register counts after the fixes: on recorded data 16 tests with **0 pass**; overall **1 pass** (W4).
- `check_all.sh`, RSX-V, `check_site_night` (C2 must hold with the new sentences), `check_evidence`,
  `check_site_catchup`, `check_profiles`, `check_personlab` pass.
- The new evidence test fails on the old prefix rule and passes on the new one.

## 3. Results

(recorded after the fix commit)
