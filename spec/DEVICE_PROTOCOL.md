# RSOS Device Protocol (RDP) — Specification v1.0

**Status:** open specification, CC BY 4.0. Reference implementations: host side `rsso/rsso/protocol.py`; device side `firmware/rsos_core/` (portable C++, with an ESP32 wrapper).

RDP is how a phone, computer or hub (the **host**) drives an RSOS output device (the **device**): a wristband or ring with a vibration motor, a scent or taste dispenser, or any combination. The host compiles an RSX program, sends the device only the events it can render, and starts it. The device then plays the timeline **on its own clock**, so timing does not depend on the radio link, and it must stop at once when told to.

## 1. Transport

Any byte stream that carries text lines works:

| Transport | Framing |
|---|---|
| USB / UART serial | 115200 baud, 8N1 |
| Bluetooth LE | Nordic UART Service: service `6E400001-B5A3-F393-E0A9-E50E24DCCA9E`, host writes to RX `6E400002-…`, device notifies on TX `6E400003-…` |

Messages are ASCII lines ending in `\n`, at most 96 bytes. Fields are separated by single spaces. Times are integers in milliseconds from the start of the run; amplitudes are decimals in 0–1.

## 2. Host → device

| Message | Meaning |
|---|---|
| `HELLO` | Ask the device to identify itself |
| `CONSENT <0\|1>` | The person has (1) or has not (0) confirmed no allergy or aversion to the scent and taste cartridges. Default after power-on: 0 |
| `LOAD <n> <haptic_max>` | Begin a timeline of `n` events; the device must never drive the motor above `haptic_max` |
| `H <t> <on> <off> <count> <amp>` | Haptic pattern: `count` pulses of `on` ms with `off` ms between, at amplitude `amp`, starting at `t` |
| `S <t> <dur> <O\|G>` | Release scent (`O`) or taste (`G`) for `dur` ms at `t` |
| `START` | Start the loaded timeline now (time 0) |
| `STOP` | Stop all output immediately |
| `STATUS` | Ask for the current state |

`TICK <t>` is accepted only by the host simulator (`firmware/rsos_core/host_sim`): it advances simulated time, so that a device's behaviour can be tested exactly without hardware.

## 3. Device → host

| Message | Meaning |
|---|---|
| `HELLO RDP/1 <capabilities> <motor_max>` | Capabilities: comma-separated subset of `haptic,olfactory,gustatory` |
| `OK <command>` | Command accepted |
| `ERR <command> <reason>` | Command rejected (bad syntax, too many events, not loaded, …) |
| `MOTOR <t> <amp>` | Motor amplitude changed at `t` (0 = off) |
| `SCENT <t> <O\|G> <0\|1>` | Valve opened (1) or closed (0) at `t` |
| `REFUSED <t> <O\|G> consent` | A release was skipped because consent was not given |
| `CLAMPED <t> <requested> <limit>` | A pulse was limited to `haptic_max` |
| `STOPPED <t>` | All output ended at `t` after `STOP` |
| `DONE <t>` | The timeline finished at `t` |
| `STATE <idle\|loaded\|playing> <t>` | Reply to `STATUS` |

`MOTOR` and `SCENT` reports are what make a device testable: they let the host (and the conformance suite) see exactly what the hardware did.

## 4. Required device behaviour

1. **Own clock.** After `START`, events play from the device's clock; radio delays must not shift them.
2. **Stop.** On `STOP`, the motor and all valves are off within 100 ms, and nothing restarts until a new `LOAD` and `START`.
3. **Intensity limit.** Motor amplitude never exceeds the `haptic_max` of the current `LOAD` (and never the hardware maximum).
4. **Consent.** No scent or taste is released unless `CONSENT 1` was received since power-on.
5. **Release limit.** A single release lasts at most 3000 ms, whatever `dur` says.
6. **Link loss.** If the host connection drops while playing, the device stops all output within 1 s.
7. **Bounded memory.** A device may refuse a `LOAD` larger than it can hold (`ERR LOAD too-many-events`); it must hold at least 64 events.

A device that meets these rules and passes the conformance suite (`python -m rsso.conformance`, run through the host adapter) is **RDP/1 compatible**.

## 5. Example

Produced by the host simulator running the reference firmware core:

```
host:   HELLO
device: HELLO RDP/1 haptic,olfactory 1.00
host:   CONSENT 0
device: OK CONSENT
host:   LOAD 2 0.40
device: OK LOAD
host:   H 0 300 300 3 0.40
host:   S 1800 2000 O
host:   START
device: OK START
device: MOTOR 0 0.40
device: MOTOR 300 0.00
device: MOTOR 600 0.40
device: MOTOR 900 0.00
device: MOTOR 1200 0.40
device: MOTOR 1500 0.00
device: REFUSED 1800 O consent
host:   STOP   (at 1900 ms)
device: STOPPED 1900
```
