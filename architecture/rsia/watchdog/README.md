# RSIA Watchdog

The observer layer: it notices which mode is active, flags drift away from the Spine and calls for correction. **Built on the person side** (`spec/WATCHDOG.md`, `rsso/rsso/watchdog.py`, identically `docs/js/watchdog.js`): one decision, allow, ask or hold, for every action that acts on a person (a run, a cue, a device offer, an agent's output), with the Spine virtue that decided it, written to a hash-chained audit log the person can verify on the Safety page. It applies the session state, the guidance level each program carries (self-guided, structured, clinician-led), the domain profile's highest level, consent, and the Spine wording checks. A program's level comes from where it came from and from its compiled content wherever it is copied (`spec/FIXES_R4.md` to `spec/FIXES_R6.md`). Its first form is the cue engine's `watchdog()`, which estimates a person's current response mode; in RSX-V the same Watchdog and Spine govern the archetype agents (`rsxv/AGENTS.md`).

## Sources in the archive

| Source file | What it is | SHA-256 (first 16) |
|---|---|---|
| [RSIA_Watchdog_Overview.txt](../../../archive/original-estates/RSIA_COPYRIGHT_ESTATE/RSIA_Watchdog_Overview.txt) | RSIA Watchdog | `4ac1c98606b8ccec` |
