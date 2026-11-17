---
name: Board report (RSOS wristband)
about: Report a run of firmware/BOARD_TEST.md on a real ESP32 board
title: "Board report: <board model>"
labels: ["board report"]
---

Test sheet: https://github.com/r-a-elu-architecture/RSOS-Multimodal-Cue-Framework/blob/dev/firmware/BOARD_TEST.md
(board kit: https://github.com/r-a-elu-architecture/RSOS-Multimodal-Cue-Framework/blob/dev/firmware/BOARD_KIT.md).
Record what actually happened, including anything unexpected. A failed step is useful data.

```
Board:                      (model)
Arduino-ESP32 version:
Motor / driver:
T0 flash:                   ok / error: …
T1 USB:                     HELLO … / pulses: yes/no / PASSKEY shown: yes/no
T2 board check:             …/7 (failed: …)
T3 pair in window:          prompt yes/no, paired yes/no, check …
T4 USB-only over BLE:       replies …
T5 window closed:           prompt yes/no, connected yes/no; after PAIR: …
T6 failure limit:           attempts 1–3 …, attempt 4 (correct key) …
T7 reconnect after address change:  ok / failed: error … serial …
T8 link loss:               motor stopped yes/no, after … s
T9 NEWKEY:                  old phone …
Anything unexpected:
```

Please do not include the passkey itself.
