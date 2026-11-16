# BASELINE_AUDIT — the passed RSX-V rows against their simplest baselines (results)

Design and rule: [`spec/BASELINE_AUDIT.md`](../../spec/BASELINE_AUDIT.md), registered before this code. Stated models;
no number here comes from people or production agents.

| Row | Baseline | Outcome |
|---|---|---|
| A1 W1 | GREEDY (equal information) | **TIES** |
| A2 W4 | none applies (§3) | **NOT APPLICABLE** |
| A3 H-SWITCH | FIXED-BEST (BEAR) | **LOSES** |
| A4 H-CFIT-M | FIXED-BEST (BEAR) | **LOSES** |
| A5 G1 | NONE (transfer nothing) | **TIES** |
| A6 J1 | NEVER-JAM | **TIES** |
| A7 T-AP | STAB-ONLY | **LOSES** |

## A1 W1

- Recorded: {"beats_equal_information": false}.

## A2 W4

- Recorded: {}.

## A3 H-SWITCH

- Pilot means (20 pilot persons): LION +0.0393, EAGLE -0.0003, BEAR +0.0546, LEOPARD +0.0006, RAVEN -0.0043, TIGER -0.0003
- Chosen: BEAR. Watchdog +0.0426; FIXED-BEST +0.0538.
- Watchdog − FIXED-BEST (95%): -0.0111 [-0.0123, -0.0100]. Reproduced: True.
- Information only, each fixed mode on the test persons: LION +0.0387, EAGLE +0.0038, BEAR +0.0538, LEOPARD +0.0057, RAVEN -0.0049, TIGER +0.0035

## A4 H-CFIT-M

- Pilot means (20 pilot persons): LION -0.0550, EAGLE -0.0852, BEAR +0.1269, LEOPARD -0.0765, RAVEN -0.0721, TIGER -0.0824
- Chosen: BEAR. Watchdog +0.0447; FIXED-BEST +0.1294.
- Watchdog − FIXED-BEST (95%): -0.0847 [-0.0954, -0.0741]. Reproduced: True.
- Information only, each fixed mode on the test persons: LION -0.0497, EAGLE -0.0822, BEAR +0.1294, LEOPARD -0.0752, RAVEN -0.0688, TIGER -0.0797

## A5 G1

- Recorded: {"g1_gated_tables_all_lion": true}.

## A6 J1

- n 260; J1 accuracy 0.754; never-jam 0.685; mean-only rule 0.746 (information only).
- Discordant pairs: J1 only right 65, never-jam only right 47; exact one-sided McNemar p = 5.39e-02. Reproduced: True.

## A7 T-AP

- primary (person): T-AP +0.1113; STAB-ONLY +0.2439; T-AP − STAB-ONLY -0.1325 [-0.1449, -0.1190]; reproduced True; **LOSES**.
  STAB-ONLY tables used: {"calm": "BEAR", "crisis": "BEAR", "loaded": "BEAR", "rising": "BEAR"}.
- confirmation (person_v2): T-AP +0.0872; STAB-ONLY +0.2271; T-AP − STAB-ONLY -0.1399 [-0.1470, -0.1335]; reproduced True; **LOSES**.
  STAB-ONLY tables used: {"calm": "BEAR", "crisis": "BEAR", "loaded": "BEAR", "rising": "BEAR"}.
