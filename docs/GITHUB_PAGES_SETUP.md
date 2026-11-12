# Website (GitHub Pages)

The project website is served from the `docs/` folder of the `main` branch:

- Home: `docs/index.html`
- Protocol player: `docs/player.html` (uses `docs/js/rsx.js` and the programs in `docs/protocols/`)
- Retired pages from v1 (`cue-lab.html`, `cue-lab-v13.html`, `invariance-v14.html`, `architecture-benchmark.html`) are short notices that link home, so old links do not break.

**Settings:** Repository → Settings → Pages → Deploy from a branch → `main`, folder `/docs`.

**Keeping the player in sync:** `docs/protocols/*.rsx` must be identical to `rsx/protocols/*.rsx`; the RSX tests fail otherwise. After changing the player, raise `BUILD` in `docs/player.html` so browsers load fresh program files.
