# How the systems work together

1. **Trigger.** A negative state appears (a sound, a smell, something seen, a memory), or a device detects it (AUG; EEG or HRV, specified).
2. **Safety check.** The domain profile sets the highest guidance level (personal, coaching, performance, learning, research, workplace or clinical). The Watchdog (RSIA) asks CONTAIN, the session state and consent, and allows, asks or holds with a Spine reason; the runtime keeps its limits (opt-in, refractory period, hourly and daily limits). The output gate on every page lets output through only while that decision stands.
3. **Program.** An RSX program (RSX) is selected, or an RSX-V command is compiled into one; the cue engine can choose the variant that works best for this person (CM1, Watchdog). The program carries the level of where it came from.
4. **Execution.** The runtime plays the timeline: breath, words, imagery, gestures and haptic anchors (THERA), activating tiers (RSOS) in the mode of an archetype (RSIA), on a phone, a watch or another device (AUG, MICRO).
5. **Memory.** The run is logged (MEMSTACK): distress and agency before and after, trigger, completion.
6. **Learning.** Over many runs the bundle becomes a reflex, and the logs show which programs and tiers work for whom. A trial (anchor against sham, automatic against manual) feeds its results into the evidence chain (PEAK, GATE).

| Step | Built now |
|---|---|
| Trigger, self-initiated | Player |
| Trigger, device-detected | Virtual heart-rate strap and stress detector (`rsso/rsso/sensors.py`) |
| Domain profile | [spec/PROFILES.md](../../spec/PROFILES.md); `docs/js/profiles.js` |
| Safety check | Watchdog [spec/WATCHDOG.md](../../spec/WATCHDOG.md); session states [spec/CONTAIN.md](../../spec/CONTAIN.md) §9–§10; output gate `docs/js/outlet.js`; `rsx/rsx/runtime.py` (`SafetyGovernor`); RSX compile-time limits; conformance suite (`rsso/rsso/conformance.py`) |
| Command layer | [rsxv/](../../rsxv) (RSX-V compiles into RSX) |
| Program | [rsx/protocols/](../../rsx/protocols) |
| Execution | [docs/player.html](../../docs/player.html); device runtime `rsso/rsso/runtime.py` |
| Memory | Run log (`RunRecord`, player CSV export) |
| Learning | [toolkit/](../../toolkit) and [learning model](../../rsx/model/PREDICTIONS.md) |
| Studies | Virtual participants, synthetic studies and analysis kit: [rsso/](../../rsso); trial loop [spec/TRIAL_LOOP.md](../../spec/TRIAL_LOOP.md) |
