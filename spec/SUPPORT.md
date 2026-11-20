# SUPPORT: a way to fund RSOS research (registered 20 November 2026, before any change)

Author's request (20 November 2026): a donations button for the Cue Framework, chosen the way established open-source
projects do it. Decision: GitHub Sponsors on the author's personal account (0% fees for personal sponsors; payouts
through Stripe Connect to the author's bank). The Sponsors profile was submitted on 20 November 2026 and is waiting for
GitHub's approval.

## What this step adds
- `.github/FUNDING.yml`: the Sponsor button on the repository page, pointing only to `github: [r-a-elu-architecture]`.
- `docs/support.html`: one page in the family design that says what support pays for, what it does not buy, the tiers,
  and one plain link to the Sponsors page.
- A "Support RSOS" link in the home page footer and a short "Support" section in the README.
- The page listed in `docs/sw.js` (offline shell) and `docs/sitemap.xml`.

## Wording, fixed before the change
- What it funds, in the same words as the Sponsors profile: research and development, first of all the first registered
  study of RSOS in people (heart-rate sensors, participant payments and a university research partner), then devices and
  hosting.
- What it does not buy: "Your support buys no product, treatment or access. RSOS is a research and development
  framework, not a medical device."
- The positioning sentence (spec/POSITIONING.md) appears on the page as `<p data-raw>`.
- No claim of effect; the page carries an evidence label of kind `record` and none of the overclaim words in
  `architecture/evidence.py`.
- No details of the study protocol beyond the sentence above; the protocol is published when it is registered.

## Privacy and integrity
- No payment form, no third-party script, no iframe, no tracking pixel, no external image on the page. The only
  outbound payment link is `https://github.com/sponsors/r-a-elu-architecture`.
- Support never changes what is published: every registered result, including null results, is published whatever
  the funding (stated on the page).

## Release rule
Built on `dev` only. Not merged to `main` until GitHub approves the Sponsors profile (author's decision). GitHub reads
`FUNDING.yml` from the default branch, so the button cannot appear before the merge.

## Checks, fixed before the change
- U1: `.github/FUNDING.yml` parses and names exactly `github: [r-a-elu-architecture]`.
- U2: `docs/support.html` has the family bar, the ribbon header, the site nav (including `rsxv.html`), one evidence
  label, the positioning sentence, the "buys no product, treatment or access" sentence and the Sponsors link.
- U3: `docs/support.html` has no `<form>`, no `<iframe>`, no `<img>` or `<script src>` from another origin, and no
  payment link other than the Sponsors page.
- U4: the home page footer links `support.html`; the README links the Sponsors page; `sw.js` and `sitemap.xml` list
  `support.html`.
- U5: `scripts/check_all.sh` passes and the browser checks in `scripts/check_family.py` pass for every page, including
  `support.html` (no horizontal overflow at 1280 and 375 px, text contrast AA).
