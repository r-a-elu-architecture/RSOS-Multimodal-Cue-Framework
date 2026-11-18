# SUBSTANCES_NOW: substances now, without sedative medication, move the session to Stabilisation

Registered 18 Nov 2026, before its code. Author's decision of the same day, after LINX_MCP §7 recorded the gap:
substances now without sedative medication raised no screen, so a full plan was built.

## Change (one rule set: `rsso/rsso/safety.py` and `docs/js/safety.js`, identical results)

- New screen `substances_now`: raised when `substances` is true and `sedative_prescribed` is not (with both, the
  existing `sedative_combination` screen is raised as before and its pause is unchanged).
- Response: `offer_stabilise_mode`, `no_deep_processing_today`. Mode: Stabilisation (the same as `unstable`).
- Message: "Substances noted: the session moved to Stabilisation. Regulation programs only today; leave Stabilisation
  when you choose."
- This change only makes the layer more cautious (HANDOFF_DEV §1 and SR-3), so it is applied with this registration.

## Predictions

| # | Prediction | Pass if |
|---|---|---|
| **S1** | The rule | Over the LINX_MCP v2 grid (3,168 cells): every cell with substances yes or unsure gets no plan; with sedative or unsure medication the session is Clinician-led protocol (unchanged), otherwise at least Stabilisation with `allowed_now` naming the regulation programs; every other cell keeps its v2 result |
| **S2** | Parity | Python and JavaScript give identical screens, modes and messages on the safety parity tests and on 500 seeded events covering every field |
| **S3** | Wording | The new message passes the representation rule (no crisis, helpline or emergency wording) |
| **S4** | No other change | `scripts/check_all.sh` passes; any pinned research number that moves is reported here with old and new values, never silently re-pinned |

## Results (18 Nov 2026)

| # | Result | Verdict |
|---|---|---|
| S1 | 3,168 cells: every cell with substances yes or unsure has no plan; with sedative or unsure medication the mode stays Clinician-led protocol; otherwise Stabilisation (or a higher mode from another screen) with the regulation programs named; cells with substances no never raise the new screen. Plan-allowed cells: 224 (was 448: the 224 removed are exactly substances yes or unsure without sedative medication) | **pass** |
| S2 | Python and JavaScript identical on 500 seeded events (screens, mode, messages) and on the existing safety parity tests | **pass** |
| S3 | The new message has no crisis, helpline or emergency wording | **pass** |
| S4 | `scripts/check_all.sh` passes; no generated file and no pinned research number moved. One unit test encoded the old rule (`screen({"substances": True}) == []`); it now expects `["substances_now"]`, marked in the test | **pass** |

Tests: `rsso/tests/test_substances_now.py`.
