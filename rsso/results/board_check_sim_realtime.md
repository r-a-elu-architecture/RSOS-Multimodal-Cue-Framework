# Board check: firmware core in real time (no board)

Date: 2026-11-12. Device: `HELLO RDP/1 haptic,olfactory,gustatory 1.00`.

| Check | Requirement | Result | Measured |
|---|---|---|---|
| B1 | the device answers HELLO with RDP/1 and its capabilities | PASS | HELLO RDP/1 haptic,olfactory,gustatory 1.00 |
| B2 | a 3-pulse pattern plays on the device's own clock: 300 ms pulses, 300 ms apart (±15 ms) | PASS | 0+300, 600+300, 1200+300 |
| B3 | a pulse asked at 0.9 under a limit of 0.4 is clamped to 0.4 and reported | PASS | CLAMPED reported; highest motor 0.40 |
| B4 | after STOP the motor is off and STOPPED arrives within 100 ms (host round trip) | PASS | 0 ms |
| B5 | without consent a scent release is refused | PASS | refused |
| B6 | a 5 s scent release closes by 3 s | PASS | closed at 3000 ms |
| B7 | the Lion's vibration code ..- plays as 100, 100 and 300 ms pulses | PASS | 100, 100, 300 |
| C1 | every event dispatched within 10 ms of its time | PASS | 1 ms |
| C8 | every output channel in the program has a device | PASS | all covered |
| C10 | "I move, I act" spoken exactly once, then "I own" once | PASS | I move, I act | I own |
| C11 | a run that is not stopped completes | PASS | completed |
| C2 | output ends within 100 ms of Stop, in every phase | PASS | worst 0 ms |
| C3 | no device output after Stop | PASS | none |
| C4 | haptic intensity never exceeds the program's haptic_max | PASS | peak 0.4 (limit 0.4) |
| C5 | no device-triggered run without opt-in | PASS | device triggering needs the person's opt-in |
| C6 | refractory period and hourly limit enforced for device-triggered runs | PASS | 30s refractory period; 1200s hourly limit |
| C9 | a self-initiated run is always allowed | PASS | ok |
| C7 | no scent or taste is released before the person confirms no allergy or aversion | PASS | 0 releases |
| C12 | no programmed cue runs without a consent record naming its content (therapist-led tiers: therapist present and screening passed) | PASS | without record: cue c1: no consent record; with record: ok; therapist-led alone: cue c2: therapist-led: needs a therapist present |
| C13 | the person can list every programmed cue and revoke any of them; a revoked cue never runs | PASS | listed c1, c2; after revoking: cue c1: revoked |
| C14 | a program outside the device safety envelope never starts; programs inside it run | PASS | outside: refused (outside the device safety envelope); inside: ok |
| C15 | a program that makes distress worse is paused and never starts until the person (or their therapist) restores it | PASS | paused: yes; after restoring (restored): ok |

22/22 checks passed.
