# RSXV_LEVELS — RSX-V commands carry guidance levels, keep them through NEXT and ask the Watchdog (phase 2, Step 9)

Status: registered 2026-11-16, before code.

## 0. Problem

On the person side, every program carries a guidance level (self-guided, structured, clinician-led) and possibly memory
work. The level follows the program wherever its content goes, and the Watchdog holds it when the session state, the
domain or consent does not allow it (spec/WATCHDOG.md, spec/FIXES_R4.md to spec/FIXES_R6.md). RSX-V has none of this:
- a command cannot declare a level;
- the RSX program the bridge writes carries no level marker;
- NEXT can write a successor that drops whatever level the parent had;
- `run()` asks ChronoGate, ConsentStack, GhostPass and CONTAIN, but not the Watchdog or the domain.

## 1. Rules

| ID | Rule |
|---|---|
| V1 | Two optional header lines: `LEVEL self_guided` \| `structured` \| `clinician_led`, and `MEMORY yes` \| `no`. Any other value is a parse error. `to_text` writes them when they are set, so a command survives a round trip. |
| V2 | **Effective level** of a command is the higher of the declared level and the content's level. The content's level is `rsso.watchdog.level_of_program` on the RSX program the bridge writes (clinician tiers, markers, programmed cues), plus memory work when `MEMORY yes`. A declaration can raise the level, never lower it. |
| V3 | **The bridge carries the level.** When the effective level is clinician-led, `to_cue` writes `# rsos-level: clinician_led` as the cue program's first comment line, and `# rsos-memory: yes` when there is memory work. These are the markers the person side already reads (FIXES_R3 §2), so the player, the device page and level lineage see the level. The manifest records `level` and `memory`. |
| V4 | **NEXT keeps the level.** `next_program` copies `LEVEL` and `MEMORY`. When the parent's effective level is clinician-led, the successor declares `LEVEL clinician_led` (and `MEMORY yes` if the parent had memory work), with the note "level carried from the parent". A successor's effective level is never lower than its parent's. |
| V5 | **The Watchdog decides first.** `run()` asks `rsso.watchdog.watch` before ChronoGate, with the action `{kind: "run", protocol: "rsxv:tier<n>", therapist_led, memory_work, text, trigger: "self", source}` (`source` from `ctx`, default `"person"`). The context is: the session state from `ctx["safety"]` if given; the domain cap `rsso.profiles.max_level(ctx["domain"], ctx.get("clinical", False))` and its `memory_work` when `ctx["domain"]` is given, otherwise `ctx.get("max_level")`; and `clinician_present` and `screening_recorded` from `ctx`. A hold, or an ask without `ctx["confirmed"]`, makes the run `refused`, with the log line `Watchdog: <reasons>` and `R["watchdog"]` set to the decision. |
| V6 | **Shared wording check.** The action's `text` is the command's INTENT, its vector arguments and the quoted words of the bridged program. The Watchdog checks it with the shared Spine word lists on folded text (`rsso.safety.fold`, the pinned table of FIXES_R6 §3), the same check the site runs. |
| V7 | **No change to existing behaviour without a level.** A command with no `LEVEL`, no `MEMORY`, no clinician content and no Spine flags, run without `domain` in `ctx`, gives the same result as before. The existing RSX-V tests and the committed examples stay unchanged. The effective level is computed once per command text. |
| V8 | `rsxv/SPEC.md` §2 (grammar) documents `LEVEL` and `MEMORY`. The RSX-V page (`docs/rsxv.html`) adds one line saying that commands carry guidance levels. |

## 2. Acceptance

- Q1 `rsxv/tests/test_levels.py`:
  - **Parsing:** the two header lines parse, round-trip through `to_text`, and refuse other values.
  - **V2:** clinician-tier content makes a `LEVEL self_guided` command clinician-led.
  - **V3:** a clinician-led command's cue program carries both markers, and `level_of_program` on it agrees.
  - **V4:** NEXT keeps the level, including when the parent's level came only from its content.
  - **V5:**
    - a `MEMORY yes` command is refused in `workplace` and allowed in `personal`;
    - a clinician-led command is refused in `personal` and refused in `clinical` without a clinician present;
    - it is allowed in `clinical` with the clinical module on, a clinician present and screening recorded;
    - a run in `CRISIS` is refused.
  - **V6:** an INTENT with "ice bath", and with "іce bath" written with a Cyrillic letter, is refused.
  - **V7:** `examples/dragon.rsxv` runs exactly as before.
- Q2 All 130 existing RSX-V tests pass unchanged. `scripts/check_all.sh` passes, including the regenerated
  `docs/data/rsxv_example.json`. All `rsso` suites and the browser checks pass.
