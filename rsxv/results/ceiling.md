# W5-CEILING — is perfect source knowledge worth anything to the target? (results)

Design and decision rule: [`spec/CEILING.md`](../../spec/CEILING.md), registered before any code or run. W5's environments,
mission score, smoothed context, seeds and deployment, unchanged. 99% paired bootstrap intervals over 200 deployment
seeds. All environments are stated models; no number here comes from people or production agents.

## agent → person

- Source true table {'calm': 'LEOPARD', 'rising': 'LEOPARD', 'loaded': 'LEOPARD', 'crisis': 'LEOPARD'}; source roles {'RESTORE': 'LEOPARD', 'DRIVE': 'TIGER', 'STABILISE': 'LEOPARD'}; target roles {'RESTORE': 'BEAR', 'DRIVE': 'LEOPARD', 'STABILISE': 'BEAR'}.
- SRC-TRUE (mapped) {'calm': 'BEAR', 'rising': 'BEAR', 'loaded': 'BEAR', 'crisis': 'BEAR'}; TGT-TRUE {'calm': 'BEAR', 'rising': 'BEAR', 'loaded': 'BEAR', 'crisis': 'BEAR'}.

| Arm | Mean / tick |
|---|---|
| SRC-TRUE | +0.2402 |
| TGT-TRUE | +0.2402 |
| NONE | -0.0931 |
| PILOT-8 | +0.0270 |

| Contrast (99%) | Estimate |
|---|---|
| SRC-TRUE − NONE | +0.3333 [+0.3261, +0.3405] |
| SRC-TRUE − PILOT-8 | +0.2132 [+0.1988, +0.2275] |
| TGT-TRUE − NONE | +0.3333 [+0.3261, +0.3405] |
| PILOT-8 − NONE | +0.1201 [+0.1047, +0.1358] |

Share of the reachable gain: +1.00.
VALUE: **yes**. ROOM: **yes**.

## person → agent

- Source true table {'calm': 'BEAR', 'rising': 'BEAR', 'loaded': 'BEAR', 'crisis': 'BEAR'}; source roles {'RESTORE': 'BEAR', 'DRIVE': 'LEOPARD', 'STABILISE': 'BEAR'}; target roles {'RESTORE': 'LEOPARD', 'DRIVE': 'TIGER', 'STABILISE': 'LEOPARD'}.
- SRC-TRUE (mapped) {'calm': 'LEOPARD', 'rising': 'LEOPARD', 'loaded': 'LEOPARD', 'crisis': 'LEOPARD'}; TGT-TRUE {'calm': 'LEOPARD', 'rising': 'LEOPARD', 'loaded': 'LEOPARD', 'crisis': 'LEOPARD'}.

| Arm | Mean / tick |
|---|---|
| SRC-TRUE | -0.0049 |
| TGT-TRUE | -0.0049 |
| NONE | -0.0764 |
| PILOT-8 | -0.0017 |

| Contrast (99%) | Estimate |
|---|---|
| SRC-TRUE − NONE | +0.0716 [+0.0597, +0.0829] |
| SRC-TRUE − PILOT-8 | -0.0031 [-0.0075, +0.0012] |
| TGT-TRUE − NONE | +0.0716 [+0.0597, +0.0829] |
| PILOT-8 − NONE | +0.0747 [+0.0628, +0.0869] |

Share of the reachable gain: +1.00.
VALUE: **yes**. ROOM: **no**.

## agent_v2 → person

- Source true table {'calm': 'LEOPARD', 'rising': 'LEOPARD', 'loaded': 'TIGER', 'crisis': 'TIGER'}; source roles {'RESTORE': 'LEOPARD', 'DRIVE': 'TIGER', 'STABILISE': 'BEAR'}; target roles {'RESTORE': 'BEAR', 'DRIVE': 'LEOPARD', 'STABILISE': 'BEAR'}.
- SRC-TRUE (mapped) {'calm': 'BEAR', 'rising': 'BEAR', 'loaded': 'LEOPARD', 'crisis': 'LEOPARD'}; TGT-TRUE {'calm': 'BEAR', 'rising': 'BEAR', 'loaded': 'BEAR', 'crisis': 'BEAR'}.

| Arm | Mean / tick |
|---|---|
| SRC-TRUE | -0.0632 |
| TGT-TRUE | +0.2402 |
| NONE | -0.0931 |
| PILOT-8 | +0.0270 |

| Contrast (99%) | Estimate |
|---|---|
| SRC-TRUE − NONE | +0.0299 [-0.0007, +0.0627] |
| SRC-TRUE − PILOT-8 | -0.0902 [-0.1149, -0.0619] |
| TGT-TRUE − NONE | +0.3333 [+0.3261, +0.3405] |
| PILOT-8 − NONE | +0.1201 [+0.1047, +0.1358] |

Share of the reachable gain: +0.09.
VALUE: **no**. ROOM: **no**.

## person → agent_v2

- Source true table {'calm': 'BEAR', 'rising': 'BEAR', 'loaded': 'BEAR', 'crisis': 'BEAR'}; source roles {'RESTORE': 'BEAR', 'DRIVE': 'LEOPARD', 'STABILISE': 'BEAR'}; target roles {'RESTORE': 'LEOPARD', 'DRIVE': 'TIGER', 'STABILISE': 'BEAR'}.
- SRC-TRUE (mapped) {'calm': 'BEAR', 'rising': 'BEAR', 'loaded': 'BEAR', 'crisis': 'BEAR'}; TGT-TRUE {'calm': 'LEOPARD', 'rising': 'LEOPARD', 'loaded': 'TIGER', 'crisis': 'TIGER'}.

| Arm | Mean / tick |
|---|---|
| SRC-TRUE | -0.1294 |
| TGT-TRUE | +0.0091 |
| NONE | -0.0797 |
| PILOT-8 | -0.0763 |

| Contrast (99%) | Estimate |
|---|---|
| SRC-TRUE − NONE | -0.0497 [-0.0527, -0.0461] |
| SRC-TRUE − PILOT-8 | -0.0531 [-0.0561, -0.0494] |
| TGT-TRUE − NONE | +0.0888 [+0.0828, +0.0956] |
| PILOT-8 − NONE | +0.0033 [+0.0032, +0.0035] |

Share of the reachable gain: -0.56.
VALUE: **no**. ROOM: **no**.

## Verdict

Pass for agent → person by the registered rule. The room cannot be credited to the source: a source-free rule (the target's stabilising archetype everywhere, read from the pilot's own role-reading ticks) reaches the same value (review P2-1; spec/FIXES_P2.md C1). The W5 transfer line stops in all four directions (C2).
