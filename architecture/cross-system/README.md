# How the systems work together

1. **Trigger.** A negative state appears (a sound, a smell, something seen, a memory), or a device detects it (AUG; EEG or HRV, specified).
2. **Safety check.** CONTAIN and the runtime decide whether a run may start (opt-in, refractory period, hourly and daily limits).
3. **Program.** An RSX program (RSX) is selected; the cue engine can choose the variant that works best for this person (CM1, Watchdog).
4. **Execution.** The runtime plays the timeline: breath, words, imagery, gestures and haptic anchors (THERA), activating tiers (RSOS) in the mode of an archetype (RSIA), on a phone, a watch or another device (AUG, MICRO).
5. **Memory.** The run is logged (MEMSTACK): distress and agency before and after, trigger, completion.
6. **Learning.** Over many runs the bundle becomes a reflex, and the logs show which programs and tiers work for whom.

| Step | Built now |
|---|---|
| Trigger, self-initiated | Player |
| Safety check | `rsx/rsx/runtime.py` (`SafetyGovernor`); RSX compile-time limits |
| Program | [rsx/protocols/](../../rsx/protocols) |
| Execution | [docs/player.html](../../docs/player.html) |
| Memory | Run log (`RunRecord`, player CSV export) |
| Learning | [toolkit/](../../toolkit) and [learning model](../../rsx/model/PREDICTIONS.md) |
