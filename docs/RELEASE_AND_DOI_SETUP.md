# Publication controls — account steps and verification

Repository: https://github.com/r-a-elu-architecture/RSOS-Multimodal-Cue-Framework

## 1. Repository topics

Go to the repository homepage → **About** → gear icon → Topics. Paste up to 20 relevant topics (GitHub accepts individually entered topics):

`rsos`, `multimodal`, `human-ai-interaction`, `human-computer-interaction`, `personalization`, `adaptive-learning`, `mnemonics`, `context-aware-computing`, `brain-computer-interface`, `eeg`, `neurofeedback`, `symbolic-ai`, `open-science`, `provenance`, `cognitive-science`, `virtual-reality`, `trustworthy-ai`, `software-verification`.

Set the About website to https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/ **only after the website actually resolves**.

## 2. Zenodo connection BEFORE first tagged release

1. Open https://zenodo.org/ and sign in; link your GitHub account.
2. Open the Zenodo profile GitHub integration panel, click **Sync now**, and enable `r-a-elu-architecture/RSOS-Multimodal-Cue-Framework`.
3. If the repository does not appear, check permissions and refresh synchronization; the linked GitHub account must be allowed to enable the public repository.
4. Confirm preferred creator/organization name in `CITATION.cff` before assigning a scholarly DOI.

Zenodo official instructions: https://help.zenodo.org/docs/github/enable-repository/ and https://help.zenodo.org/docs/github/archive-software/github-upload/

## 3. First GitHub tagged research preview

1. Open https://github.com/r-a-elu-architecture/RSOS-Multimodal-Cue-Framework/releases/new.
2. Choose **Create new tag** `v1.0.0-research-preview` from the reviewed `main` branch.
3. Title: **RSOS Research Framework — v1.0.0 Research Preview**.
4. Release notes: use `releases/v1.0.0-research-preview.md`.
5. Mark as **pre-release**, then publish.
6. Confirm the release on https://github.com/r-a-elu-architecture/RSOS-Multimodal-Cue-Framework/releases and inspect its source snapshot.
7. Return to Zenodo integration and confirm successful archiving and a real DOI. Do not invent or preprint the DOI.

## 4. GitHub Pages research website

1. Open https://github.com/r-a-elu-architecture/RSOS-Multimodal-Cue-Framework/settings/pages.
2. Set **Source: Deploy from a branch**; **Branch: main**; **Folder: /docs**; Save.
3. Once deployed, open https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/ and inspect the page, source links and mobile layout.
4. Add this verified site URL to the repository About homepage field.
5. The site is static and uses the `docs/index.html` entry page with JSON-LD metadata and a sitemap.
6. GitHub Pages deployment uses GitHub's build infrastructure. Public repository standard runners are free under GitHub's published rules, but check account-specific restrictions before enabling.

GitHub official guide: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site

## 5. Verify discoverability and citation

- Verify the tag and release point at the intended snapshot.
- Verify all archive hashes against `archive/provenance/SHA256SUMS.txt`.
- After Zenodo returns a DOI, update `CITATION.cff` and README with **the actual DOI**, not a placeholder.
- Test branded and nonbranded searches documented in `research/discovery-query-matrix.csv`. Indexing is not guaranteed.
- Submit sitemap to Google Search Console only if you have verified site ownership. For a GitHub project subpath, sitemap submission may depend on property scope.
