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

## 5. Results (18 Nov 2026)

Code: `rsso/rsso/linx_mcp.py`, `rsso/rsso/mcp_server.py`; tests `rsso/tests/test_linx_mcp.py` (7 tests); the whole
RSSO suite 317 tests, OK. MCP Python SDK 2.3.0.

| # | Result | Verdict |
|---|---|---|
| L1 | 203 intakes (3 NODES test intakes + 200 seeded), 411 nodes: every plan equals `nodes.plan` of the proposal with computed fields removed | **pass** |
| L2 | 200 intakes with computed fields injected (node and top level, `approved: true`): outputs identical to the clean ones; `approved` false in all | **pass** |
| L3 | 1,056 check cells: a plan exactly where `safety.allowed` permits one (56 cells, Standard); none in Stabilisation (142), Paused: practical (198) or Clinician-led protocol (660); none where a screen pauses module work | **pass** |
| L4 | In-memory MCP client: the four tools (each with an input schema) and the one prompt listed; each call returns the pure function's JSON. Also run as a real stdio server: tools listed, a proposed vibration code `------` replaced by the planner's `..-`, `approved` false; intensity 9 returns no plan and the Stabilisation message | **pass** |
| L5 | Identical bytes on repeated calls (50 intakes); no network or model client imported by either module | **pass** |
| L6 | Tool and prompt descriptions, the prompt, the proposal note, every module message and mode text, and outputs over the check grid: 0 hits for crisis, helpline or emergency wording or the excluded terms | **pass** |

**Observation (no threshold involved).** Through the existing self-check, the flag "medication is a concern" alone is
read as a sedative combination and moves the session to the clinician-led protocol, so no plan is built (all 528
cells with that flag). This is the safety module's fixed rule, unchanged here; for practitioners and coaches it is the
main limit on when the tool returns a plan. A finer medication question is a separate, registered step if wanted.

**CI fix (same day).** The first push failed the repository's excluded-terms scan: the L6 test spelled the terms
out to search for them. The test now reads the patterns from `rsx/tests/test_roadmap.py`; no threshold or result
changed. `scripts/check_all.sh`: all checks passed.

**Not covered here.** The L4 test is skipped where the MCP SDK is not installed (CI installs `requirements.txt`
only); the pure functions (L1-L3, L5, L6) run everywhere. No AI assistant was run against the server; how well an
assistant fills an intake is not measured.

## 6. Amendment v2 (registered 18 Nov 2026, before its code): fixes and efficiency

Analysis of v1 (§5): (a) one coarse medication flag withholds every plan (528 of 1,056 cells); (b) when no plan is
built the assistant gets a dead end, not what the session state still allows; (c) one intake costs the assistant about
5 calls (session check, about 3 frame checks, the plan) and about 6 KB returned, 83% of it programs and frame checks the
person approves in full later; (d) CI never runs L4 (SDK not installed).

Changes:
- **Finer medication questions** in the LINX check (the site's coarse flag is unchanged): `medication`:
  none | non_sedative | sedative | unsure, and `substances` (alcohol or other substances now): no | yes | unsure. They
  fill the safety module's own event fields: `sedative_prescribed` = sedative or unsure; `substances` = yes or unsure.
  The module's rule (both together raise the screen) is unchanged. The old `flags` input keeps its meaning.
- **`allowed_now`** in every reply: what the session state permits (from `safety.MODE_ALLOWED`), with the regulation
  programs named (`safety.REGULATING`) where they are allowed.
- **`detail`**: `summary` (default) returns, per node, the name, mode, vibration code, frames with the frame check's
  score and tips only where flagged, and contexts; the tiers, the schedule in one line per phase, and every safety line
  in full. `full` returns v1's plan. The intake prompt asks for **one** `propose_plan` call (frame checks come back in
  it); `check_frame` and `session_check` stay available.
- CI installs the MCP SDK so L4 runs there.

| # | Prediction | Pass if |
|---|---|---|
| **L7** | Finer medication | Over the v2 grid (v1 grid without `flags` × medication 4 × substances 3 = 3,168 cells): a plan is returned exactly where `safety.allowed` permits it for the event built from the answers; never where sedative-or-unsure meets yes-or-unsure substances; and plan-allowed cells with medication non_sedative and substances no equal those with medication none |
| **L8** | No dead end | In every v1 and v2 grid cell without a plan, `allowed_now` equals the categories `safety.MODE_ALLOWED` gives for that mode, and names the regulation programs exactly when `regulating_cue` is allowed |
| **L9** | Compact | Over the 203 L1 intakes, summary bytes ≤ 0.25 × full bytes (mean of ratios), with every node name, code and frame, and every safety line, present |
| **L10** | 10× (REACH, reported, and a pass threshold) | Bytes returned to the assistant per completed intake, v2 flow (one summary call) ÷ v1 flow (session check + one check per frame + full plan): pass if ≤ 0.10; calls per intake reported (v1: 2 + frames) |
| **L11** | CI | The checks job installs the SDK and L4 runs (not skipped) on dev |
| **L12** | No regression | L1–L6 still pass (L1, L2, L4 on `detail: full`); `scripts/check_all.sh` passes |

## 7. Results v2 (18 Nov 2026)

`rsso/tests/test_linx_mcp.py`: 12 tests, OK, with L9 and L10 kept as visible registered failures
(`expectedFailure`, as `test_trial_loop.py` T4) and their observed values pinned. `scripts/check_all.sh`: all
checks passed.

| # | Result | Verdict |
|---|---|---|
| L7 | 3,168 cells: plans exactly where `safety.allowed` permits; none where sedative-or-unsure meets yes-or-unsure substances; non_sedative + no equals none + no in every cell. Plan-allowed cells: 448 of 3,168 (each medication answer with substances "no": 56 of 264, the same as no medication); with the coarse flag every medication cell was withheld | **pass** |
| L8 | Every cell without a plan (v1 and v2 grids) carries `allowed_now` equal to the mode's categories; regulation programs named exactly where allowed | **pass** |
| L9 | Summary 0.288 × full (mean of ratios, 203 intakes); content condition met (every node name, code, frame and safety line) | **fail** (≤ 0.25) |
| L10 | Bytes returned per intake: v2 1,963 vs v1 6,720 = **0.292×** (3.4× less); calls per intake 1 vs 5.14 (**5.1× fewer**) | **fail** (≤ 0.10) |
| L11 | The checks job installs the SDK (mcp 2.3.0 in the dev run of 565d88c) and sets `RSOS_REQUIRE_MCP`, so a missing SDK fails CI instead of skipping L4; that run is green | **pass** |
| L12 | L1–L6 pass (L1, L2, L4 on `detail: full`); check_all passes | **pass** |

**Why 10× was not reached.** After the programs and full frame checks moved out, what remains is content the person
needs to see: every node's frames, the safety lines in full (about 0.6 KB per plan) and the session fields. Reaching
0.10 would mean sending safety lines by reference, which trades the person seeing them for bytes; not done. The larger
lever in practice is calls: each tool call is a model turn over the whole conversation, and the flow went from 5.14
calls to 1.

**Observation (module rule, unchanged).** Substances now without sedative medication raise no screen (56 plan-allowed
cells per substances answer with no medication). That is the safety module's rule (the screen needs both); whether
substances alone should move the session to Stabilisation is a question for a separate, registered safety step.
