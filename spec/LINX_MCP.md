# LINX_MCP: the planner as a tool any AI assistant can call (propose-only, gated)

Registered 18 Nov 2026, before any of its code. Step of the "for people, without people" track: companies, coaches,
practitioners and individuals use RSOS from the AI assistant they already work in (any client of the Model Context
Protocol), with no study participants needed to build or check it.

## 1. Why

NODES.md §9 specifies the AI layer and leaves it unbuilt: "It may only propose: the planner builds the plan
deterministically". Wellbeing tool servers for AI assistants already exist; this step does not claim the transport is
new. What it adds is the contract: **the assistant proposes names, states, frames, cues and contexts; the deterministic
planner computes everything else (vibration codes, pulses, programs, tiers, metrics, schedule, safety notes); the
session check gates every plan; nothing is approved by the assistant.** The same split was measured on recorded agent
data elsewhere: a model that names and a runtime that computes keeps exactness where a model that writes values does
not.

## 2. What is built

- `rsso/rsso/linx_mcp.py`: pure functions, no network, no model client.
  - `propose_plan(intake, check)`: removes every computed field from the assistant's proposal, runs the session check
    (`safety.event_from_check` → `safety.observe` → `safety.allowed(state, {"kind": "plan"})`), and returns either the
    planner's plan (`approved` always false, marked as a proposal for the person or person and practitioner to approve)
    or no plan, with the mode, the screens and the module's fixed messages.
  - `check_frame(text, mode, believability)`: `nodes.frame_check`.
  - `session_check(answers)`: the check alone, as above.
  - `tacton(code)`: the pulse pattern of a vibration code.
- `rsso/rsso/mcp_server.py`: the four functions as MCP tools over stdio, plus one prompt (`linx_intake`) with the §9
  rules for the assistant. Uses the official MCP Python SDK when installed; the core needs only the standard library
  and the existing modules.
- `rsso/tests/test_linx_mcp.py`, and a line in `scripts/check_all.sh`.

## 3. Predictions (each must hold in full)

| # | Prediction | Pass if |
|---|---|---|
| **L1** | Parity | For the NODES test intakes and 200 seeded generated intakes, with a check that raises nothing, the returned plan equals `nodes.plan` of the same proposal with computed fields removed (100%) |
| **L2** | Propose-only | For the same 200 intakes with computed fields injected (`tacton`, `tacton_pulses`, `program`, `frame_checks`, `schedule`, `tiers`, `metrics`, `safety`, `approved: true`), the output equals the output without them, and `approved` is false in every output (100%) |
| **L3** | Gate | Over the full grid of check answers (intensity 0–10, sleep 2/5/8 h, clinical none/low/moderate/high, flags none/medication/practical/both, history no/yes: 1,056 cells), a plan is returned exactly when `safety.allowed` permits a plan, and never when a screen pauses module work (100%) |
| **L4** | Protocol | With the MCP SDK's in-memory client: the server lists exactly the four tools and the one prompt, every tool has an input schema, and one call to each returns the same JSON as the pure function |
| **L5** | Determinism, no network | The same call twice gives identical bytes; the two new modules import no network or model client (`socket`, `http`, `urllib`, `requests`, `httpx`, `anthropic`, `openai`) |
| **L6** | Wording | Every string the server can return (tool and prompt descriptions, the prompt text, messages) passes the repository's representation rule (HANDOFF_DEV §1): no crisis, helpline or emergency-banner wording, none of the excluded terms |

No threshold changes after results. Failures are recorded here with the rest.

## 4. Limits stated now

- The session check is the structured self-check already in the product. A meaning-based reader of free text exists
  in research code (SR-3) and is not part of this step: its confirmation on data not seen in design (SR-4) is pending.
- Built and tested in software; effect unproven in people. The plan is a proposal; the person, or the person and
  their practitioner, approves it.
