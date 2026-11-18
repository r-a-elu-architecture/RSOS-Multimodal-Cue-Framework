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
