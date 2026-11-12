# Releases and DOIs

Each GitHub release is archived by Zenodo as a new version with its own DOI, provided the repository is switched on in the Zenodo GitHub settings (it was for v1.0.0).

## Making a release

1. Make sure all tests pass: `cd rsx && python -m unittest discover -s tests` and `cd toolkit && python -m unittest discover -s tests`.
2. Update `version` and `date-released` in `CITATION.cff` and write `releases/vX.Y.Z.md`.
3. On GitHub: Releases → Draft a new release → create tag `vX.Y.Z` on `main`; paste the release notes; tick "Set as the latest release"; publish.
4. Within a few minutes Zenodo shows the new version. Add its DOI to `CITATION.cff`, the README and `docs/index.html`.

## Repository topics

Suggested topics for the GitHub "About" box: `state-regulation`, `counterconditioning`, `multisensory`, `anchoring`, `breathwork`, `domain-specific-language`, `haptics`, `olfaction`, `wearables`, `brain-computer-interface`, `eeg`, `jitai`, `mental-health-tech`, `open-protocol`, `rsos`.

Website for the About box: https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/

## Release history

- **Next release** — collected in [releases/NEXT.md](../releases/NEXT.md); planned once all RSSO subsystems are complete.
- **v2.0.0** — Override Protocol, RSX language, protocol player ([notes](../releases/v2.0.0.md), [doi:10.5281/zenodo.24151788](https://doi.org/10.5281/zenodo.24151788)).
- **v1.0.0-research-preview** — superseded ([notes](../releases/v1.0.0-research-preview.md), [doi:10.5281/zenodo.24143732](https://doi.org/10.5281/zenodo.24143732)).
