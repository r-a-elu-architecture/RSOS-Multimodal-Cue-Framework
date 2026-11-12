# AUG — Device and augmentation layer

**Function:** Connects state control to devices: AR overlays, EEG, haptics, scent and vibration, wearables; EEG-triggered anchors.

**Status:** **Complete in simulation** — built and tested end to end with virtual and simulated hardware; awaiting a check on real devices

**Now:** Built: one device interface with virtual vibration, audio, display and scent devices; the RSOS Device Protocol for wristbands and scent modules; a Bluetooth heart-rate driver (standard Heart Rate Service) with a stress detector in Python and in the player, identical in both; an EEG stream interface (replay, synthetic, Lab Streaming Layer) with an arousal detector (`rsso/`, `docs/player.html`, `spec/DEVICE_PROTOCOL.md`). Awaiting: a check with real straps, scent hardware and EEG headsets.

## Sources in the archive

| Source file | What it is | SHA-256 (first 16) |
|---|---|---|
| [AUG_Historical_Reconstruction.txt](../../../../archive/original-estates/RSSO_PASS31B/AUG_Historical_Reconstruction.txt) | Reconstruction: role, inputs, outputs, operators | `06d83d85073b2a5e` |
| [AUG_Evidence_Excerpts.txt](../../../../archive/original-estates/RSSO_PASS31B/AUG_Evidence_Excerpts.txt) | Evidence excerpts (public edition) | `6ee179b8c7ee24ff` |
