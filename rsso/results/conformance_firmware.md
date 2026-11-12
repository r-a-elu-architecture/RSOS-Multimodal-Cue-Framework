Firmware core (RDP/1, host simulator) + virtual audio and display

| Check | Requirement | Result | Measured |
|---|---|---|---|
| C1 | every event dispatched within 10 ms of its time | PASS | 0 ms |
| C2 | output ends within 100 ms of Stop, in every phase | PASS | worst 0 ms |
| C3 | no device output after Stop | PASS | none |
| C4 | haptic intensity never exceeds the program's haptic_max | PASS | peak 0.4 (limit 0.4) |
| C5 | no device-triggered run without opt-in | PASS | device triggering needs the person's opt-in |
| C6 | refractory period and hourly limit enforced for device-triggered runs | PASS | 30s refractory period; 1200s hourly limit |
| C7 | no scent or taste is released before the person confirms no allergy or aversion | PASS | 0 releases |
| C8 | every output channel in the program has a device | PASS | all covered |
| C9 | a self-initiated run is always allowed | PASS | ok |
| C10 | "I move, I act" spoken exactly once, then "I own" once | PASS | I move, I act | I own |
| C11 | a run that is not stopped completes | PASS | completed |

11/11 checks passed.
