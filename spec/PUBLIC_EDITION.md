# PUBLIC_EDITION — "GPT" becomes "model", the roadmap audience line, and a neutral description of the private record

Status: registered 2026-11-18, before any code. Results in §5. The owner's decisions of 18 November 2026 (after the site
audit): change only the word "GPT" to "model" in what is published; rewrite the roadmap's audience line without military
or special forces; describe the private record neutrally; keep everything else as recorded.

## 1. The original stays exactly as it is

The archive files are not edited. `rsso/rsso/ledger.py` still checks that the ledger's records join back to the original
file byte for byte. The change below is applied **after** that check, only to what is published, by one documented rule.

## 2. Edition rule E1: "GPT" → "model" (applied to published data)

Applied in this order, case as shown, to every string of `docs/data/ledger.json`, `docs/data/metrics.json` and
`docs/data/tier_map.json` (and the summary `rsso/results/ledger_summary.md`):

| Original | Published |
|---|---|
| `GPT Behavior` | `Model Behavior` |
| `ChatGPT` | `the model` |
| `GPT-` + number (e.g. `GPT-6`) | `model version ` + number |
| `GPTs` | `models` |
| `GPT` at the start of a line, field or sentence | `Model` |
| any other `GPT` | `model` |

Nothing else changes: every other word, the glyphs, commands, functions, echo directives, properties, metric codes and
values stay as recorded. The rule lives in one module (`rsso/rsso/edition.py`) used by every generator, so the published
edition equals the original plus exactly this rule (tested by re-applying it to the original).

**Kept unchanged (the owner's decision):** "GPT" where it correctly names others' work: WildChat's GPT-3.5 and GPT-4 split,
the Who&When GPT-4o baseline, the prior-art titles SafeguardGPT and "Touched by ChatGPT", and the stop-word list in
`rsxv/rsxv/corpus_lineage.py`. "LLM" is not changed.

## 3. Wording outside the records

- Pages and specs that name the field: "System behaviour (recorded as 'GPT Behavior')" → "System behaviour (recorded)"
  (`docs/tiers.html`, `docs/system.html`, `spec/TIER_LEDGER.md`, `rsso/rsso/ledger.py`, `rsso/rsso/ledger_map.py`).
- `spec/LINX.md`: "GPT interface", "GPT routing system", "GPT interface + containment router" → "model interface",
  "model routing system", "model interface + containment router".
- **Roadmap C50** (`architecture/roadmap.py`, `spec/CLAIMS.md`): "Groups who would care: special forces, trauma therapists,
  multisensory labs, coaches, language institutions, spiritual schools, later the military, athletes, AR/VR designers,
  education." → "Groups who would care: trauma therapists, clinical and research psychologists, multisensory and
  neuroscience labs, coaches, language institutions, athletes and sports scientists, AR/VR designers, education. The aim:
  healing, transforming, signalling and evolving." Marked as edited on 18 November 2026.
- **Roadmap C25:** "The closed loop is designed the way military-grade adaptive systems are." → "The closed loop is designed
  the way adaptive control systems in engineering are." Marked as edited.

## 4. The private record, described neutrally (audit A1)

Where public text links the safety and person-model results to the owner's own record, it is replaced with "a consented
private record". Removed: the record's dates and turn count, the pronoun, the phrase "the owner's health history", the count
of crisis-labelled turns, and every sentence that says what a missed or critical turn contained. Kept: methods, thresholds,
pass or fail, recall and false-alarm figures, and the generic safety rules of §3.1 (they describe the safety layer, not the
record). Files: `rsxv/AGENTS.md` (§11 header summary, §11.12–11.14), `rsxv/RESULTS.md` rows Round 7, SR-2, SR-3,
`rsxv/results/r7.md`, `sr2.md`, `sr3.md`, the notes in `results_r7.json`, `results_sr2.json`, `results_sr3.json` and the code
that writes them (`rsxv/rsxv/sr2.py`), and the docstring of `rsxv/rsxv/v3_person.py`. **Disclosed:** earlier versions remain
in the public git history; whether to rewrite it is a separate decision of the owner.

## 5. Checks (fixed now)

- C1: the original ledger still reassembles byte for byte; applying E1 to the original gives exactly the published records.
- C2: no published data file contains "GPT" except the kept citations; `tier_map.json` places every tier in the same
  subsystems and channels as before.
- C3: no public file (outside `archive/`) contains "578 turns", "15 May", "owner's health history", "owner's own" or
  "owner's record".
- C4: `check_all.sh`, RSX-V, `check_evidence`, `check_site_catchup`, `check_profiles`, `check_site_night` pass; the tier,
  metrics, system and roadmap pages render with no page errors.

## 6. Results

(recorded after the code commit)

### Results (code 3a8a23b)

- **C1:** the original ledger reassembles byte for byte; applying E1 to the records built from the original gives exactly
  the published `ledger.json`, `metrics.json` and `tier_map.json` (`rsso/tests/test_public_edition.py`).
- **C2:** 0 "GPT" in the published data; 173 ledger lines changed by E1 (60 field labels, 113 others); all 293 tiers keep the
  same layers, channels, role, response, operator, status and reason. T027 now reads "Model demonstrated internal retention
  independent of prompt". Kept: WildChat's GPT-3.5/4, Who&When's GPT-4o, SafeguardGPT, "Touched by ChatGPT", the
  corpus_lineage stop-word list. The release note v2.1.0 line naming the field was also changed.
- **C3:** no public file outside `archive/` contains "578 turns", "15 May", "owner's health history", "owner's own" or
  "owner's record"; the SR-3 candidate count and the descriptions of what missed turns contained were removed from
  `sr2.md`, `sr3.md`, AGENTS §11.14 and register rows SR-2 and SR-3.
- **C4:** `check_all.sh` (304 tests), RSX-V 234, `check_evidence` 168/168, `check_site_catchup`, `check_profiles`,
  `check_site_night` 35/35 pass; tiers, metrics, system, roadmap and results pages render with 0 page errors, 0 "GPT", 0
  "military" or "special forces".
- **Still in the repository:** `archive/` keeps the originals (with "GPT"), as registered; the earlier wording stays in the
  public git history. Both are open decisions of the owner.
