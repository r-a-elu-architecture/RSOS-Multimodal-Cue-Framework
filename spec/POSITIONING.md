# Positioning: intended use and claims (registered 20 November 2026, before any page is changed)

Author's decision (20 November 2026): regulatory and clinical positioning is crucial. RSOS is correctly labelled "not a medical device".
Any therapeutic claim without data is a liability. The path is a **research operating system** or a **supervised practitioner tool**, not a
consumer wellness app, until evidence exists.

This step changes wording only. No program, gate, profile, protocol, data file or test threshold changes function.

## 1. The positioning statement (one sentence, used everywhere it is shown)
> Intended use: a research platform, and a tool for qualified practitioners working under their own professional protocol. Not a consumer
> wellness app. RSOS makes no therapeutic claim; claims about effects in people wait for registered human outcome data.

## 2. Intended use
- **Research operating system:** researchers run, change and test RSOS, and share results in its log format.
- **Supervised practitioner tool:** qualified practitioners use it within their own professional protocol (THERA, the copilot, the clinical
  module, which stays off by default).
- Individuals can still open the public pages and the player: they are research demonstrations of the method, not a consumer product.

## 3. Not intended
- A consumer wellness app or self-help product.
- Diagnosis, treatment, cure, mitigation or prevention of any condition.
- Use in an emergency (the registered sentence of PUBLIC_EDITION_2 C, unchanged).

## 4. Claims rule
- No therapeutic, diagnostic or health-benefit claim anywhere in the project's own voice without registered human outcome data supporting
  that exact claim.
- Every claim from the design records stays in `spec/CLAIMS.md` as a hypothesis with the test it becomes; none is presented as established.
- Software results keep their evidence labels (built, checked on simulated people, and so on); none is worded as an effect in people.
- The label used for work built without people but for people becomes: "built and tested in software, for research and for supervised
  practitioner use; effect in people not yet measured." (It replaces "ready for people and companies to use" in new texts; registered
  records keep their wording.)
- This positioning changes only by the author's decision, and only for the claim that registered evidence supports.

## 5. Where it is shown
README status block; `docs/index.html` ("Where it stands"); `docs/safety.html`; `docs/therapist.html`; `docs/player.html` (status line);
`LICENSING.md`; `SECURITY.md` stays as is; `REVIEW.md` finding F5 records the decision; `HANDOFF_DEV.md` Representation rule names this spec.
The README and the index stop inviting "individuals" as users; they name researchers and practitioners.

## 6. Checks, fixed before any change (`rsso/tests/test_positioning.py`)
- P1: the positioning sentence (§1, whitespace-normalised) appears in the README and in the visible text of `index.html`, `safety.html`,
  `therapist.html` and `player.html`.
- P2: neither the README nor `index.html` invites individuals as users ("researchers, clinics and individuals" no longer appears).
- P3: the registered emergency sentence is unchanged on the README, `safety.html` and `therapist.html`, and A7 still finds no other crisis
  wording on any page (existing test, unchanged).
- P4: `scripts/check_all.sh` passes with no other change: no data file or generated JSON differs.
