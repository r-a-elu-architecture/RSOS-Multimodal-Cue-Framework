# Board check: socket://localhost:5714

Date: 2026-11-16. Device: `HELLO RDP/1 haptic,olfactory,gustatory 0.60`.

| Check | Requirement | Result | Measured |
|---|---|---|---|
| B1 | the device answers HELLO with RDP/1 and its capabilities | PASS | HELLO RDP/1 haptic,olfactory,gustatory 0.60 |
| B2 | a 3-pulse pattern plays on the device's own clock: 300 ms pulses, 300 ms apart (±15 ms) | PASS | 0+300, 600+300, 1200+300 |
| B3 | a pulse asked at 0.9 under a limit of 0.4 is clamped to 0.4 and reported | PASS | CLAMPED reported; highest motor 0.40 |
| B4 | after STOP the motor is off and STOPPED arrives within 100 ms (host round trip) | PASS | 2 ms |
| B5 | without consent a scent release is refused | PASS | refused |
| B6 | a 5 s scent release closes by 3 s | PASS | closed at 3000 ms |
| B7 | the Lion's vibration code ..- plays as 100, 100 and 300 ms pulses | PASS | 100, 100, 300 |

7/7 checks passed.
