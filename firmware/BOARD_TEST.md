# RSOS wristband — first board test sheet

This is the first run of the wristband firmware on real hardware. Every step lists what you do, what you should see,
and what to write down. Record what actually happens, including anything unexpected. A failed step is useful data,
not a problem.

Allow about 1.5 hours. Tests T6 and T7 need waiting time.

**What this test settles.** The pairing rules (spec/BLE_PAIRING.md, spec/FIXES_R6.md §5, spec/FIXES_R6C.md) were
checked by reading the ESP32 library and stack sources, never on a board. Two questions only hardware can answer:
- **T5:** a phone that is not paired cannot pair outside the 2-minute window.
- **T7:** a paired phone still reconnects after its private Bluetooth address changes (review finding R6c-2).

## What you need

| Item | Notes |
|---|---|
| ESP32 board, coin vibration motor, MOSFET, diode, resistors | `BOARD_KIT.md` §1 and §2 (wiring) |
| USB cable and a computer | Arduino IDE 2.x, or arduino-cli, or PlatformIO |
| Android phone with Chrome | For Bluetooth tests |
| Optional: a second phone, or a laptop with Chrome | For T5 (a device that was never paired) |
| A notebook or this file | To record results |

Use the **development site** for the browser steps, because it has the newest wristband code:
https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/dev/device.html

## T0 — Flash

1. Wire the board as in `BOARD_KIT.md` §2. Motor pin: GPIO 25 on ESP32-DevKitC, GPIO 5 on ESP32-C3, GPIO 4 on
   ESP32-S3.
2. Get the firmware from the `dev` branch: `firmware/esp32/rsos_esp32/`. Include all files in that folder:
   `rsos_esp32.ino`, `rsos_core.*`, `rsos_link.*` and the module files.
3. Flash with Arduino IDE ("esp32 by Espressif Systems") or PlatformIO (`BOARD_KIT.md` §3). Versions that compile:
   2.0.17 or 3.3.12 for the ESP32; 2.0.17 or 3.2.1 for the ESP32-C3 and -S3 (3.3 and later stop with a message on
   those two, because they use a different Bluetooth stack).

**Expect:** the upload finishes without errors.

**Record:**
- the board model;
- the Arduino-ESP32 version (Boards Manager shows it);
- any compiler error, copied exactly. The firmware has been compiled with the real toolchains for these versions
  (spec/ESP32_TOOLS.md), so an error here points to a different version or setting: record both.

## T1 — Signs of life over USB

Open the serial monitor: 115200 baud, line ending "Newline". Type each line and press Enter.

| Type | Expect |
|---|---|
| `HELLO` | `HELLO RDP/1 haptic,olfactory,gustatory 0.60` |
| `LOAD 1 0.40` then `H 0 300 300 3 0.40` then `START` | Three pulses of the motor, with `MOTOR` lines |
| `STOP` | `STOPPED …` while the pattern plays, or `OK STOP` once it has finished; motor off |
| `PASSKEY` | `PASSKEY` followed by six digits. **Write the number down.** |

**Record:** each reply as shown, and whether the motor pulsed three times.

## T2 — Board check (B1–B7)

From a computer, with the band on USB:

```
pip install pyserial
cd rsso
python -m rsso.board --port <your port> --out results/board_<your-board>.md
```

The port is `COM3`/`COM5` on Windows, `/dev/cu.usbserial-…` on a Mac, `/dev/ttyUSB0` on Linux.

**Expect:** 7/7 checks pass.

**Record:** the result line. If any check fails, record its name and the message (`BOARD_KIT.md` §7 explains common
causes).

## T3 — Pair a phone inside the window

1. Restart the band (press reset, or unplug and plug in). The 2-minute pairing window starts now.
2. On the Android phone, open the dev device page in Chrome and choose **Bluetooth**. Pick `RSOS-band`.
3. Android asks for a passkey. Type the six digits from T1.
4. Choose "Run the check" on the page.

**Expect:**
- Android asks for the passkey.
- Pairing succeeds.
- The page connects and the check runs.

**Record:**
- whether the passkey prompt appeared;
- the result of the check;
- the time from restart to pairing (it must be under 2 minutes).

## T4 — USB-only commands are refused over Bluetooth

The device page cannot send a raw line, so use a Bluetooth terminal app that speaks the Nordic UART Service, for
example "Serial Bluetooth Terminal" (Kai Morich) or "nRF Connect for Mobile" (Nordic). In nRF Connect, write text to
the RX characteristic `6E400002-B5A3-F393-E0A9-E50E24DCCA9E` and enable notifications on TX
`6E400003-B5A3-F393-E0A9-E50E24DCCA9E`. End each line with a newline. The phone is already paired from T3, so the app
uses that pairing. Send: `PASSKEY`, `PAIR`, `UNPAIR`, `NEWKEY`.

**Expect:**
- Each answers `ERR LINK usb-only`.
- No passkey appears on the phone.
- The phone stays paired.

Then send a line of 100 letters. **Expect:** `ERR LINE too-long`.

**Record:** each reply.

## T5 — A new device cannot pair outside the window (key test)

1. Restart the band and wait **more than 2 minutes** without pairing anything. The window is now closed.
2. On a device that was **never paired** with this band, try to connect: a second phone, or a laptop with Chrome
   (choose Bluetooth on the dev device page). If you only have one phone, use the phone's Bluetooth settings to
   "Forget" `RSOS-band` first.
3. Try to connect and pair.

**Expect:**
- No passkey prompt appears, or pairing fails at once.
- The page does not connect as an RSOS band.

Then send `PAIR` over USB (it replies `PAIR open 120`) and try again within 2 minutes. **Expect:** now the passkey
prompt appears and pairing works.

**Record:**
- what happened with the window closed: was there a prompt, an error message, or a connection?
- what happened after `PAIR`.

**Why this test matters (spec/FIXES_P2.md E1).** The band refuses pairing outside the window only if nothing asks the
phone for encryption at connect. An earlier version called `setEncryptionLevel`, which on Arduino-ESP32 2.0.17 and 3.2.1
makes the library request encryption on every connection and so invites any phone to pair. That call is removed. The
fix rests on reading the library at 2.0.17, 3.2.1 and 3.3.12, not on a run, so record the core version you flashed with.

## T6 — Failure limit

1. Send `UNPAIR` over USB, then `PAIR`. The window is open.
2. On the phone, connect and type a **wrong** passkey. Repeat until it has failed 3 times.
3. Now type the **correct** passkey on a fourth attempt, still within the 2 minutes.

**Expect:** the fourth attempt is refused even with the correct passkey. After `PAIR` over USB, the correct passkey
works again.

**Record:** each attempt's result.

## T7 — A paired phone reconnects after its address changes (key test, R6c-2)

Phones change their Bluetooth address every few minutes for privacy. The band must still recognise a paired phone.

1. Pair the phone inside a window (as in T3), then close the page.
2. Restart the band and wait **more than 2 minutes**, so the window is closed.
3. Change the phone's address: turn Bluetooth off for a minute and on again. If you can, also wait 15 minutes or
   restart the phone.
4. Open the dev device page, choose Bluetooth, pick `RSOS-band`, and run the check.

**Expect:** the phone reconnects with **no** passkey prompt, and the check runs.

**If it fails, record exactly:**
- the error on the page;
- whether Android shows `RSOS-band` as paired;
- what the serial monitor prints at the moment of connecting.

This is the result that decides the next code change.

## T8 — Link loss stops the motor

1. Connected over Bluetooth, start a long program on the dev device page ("Play on the band", for example
   Override).
2. While the motor is pulsing, turn off the phone's Bluetooth, or walk out of range.

**Expect:** the motor stops within about a second, and the serial monitor shows the stop.

**Record:** whether and how fast it stopped.

## T9 — New passkey forgets every phone

1. Send `NEWKEY` over USB, then `PASSKEY`.
2. Try to reconnect the old phone without the window open.

**Expect:**
- `NEWKEY done` is printed, and `PASSKEY` shows a different number.
- The old phone can no longer connect without pairing again, inside a window, with the new passkey.

**Record:** both passkeys (old and new), and what the phone does.

## Report

Copy this block, fill it in, and send it back: the easiest way is a GitHub issue with the **Board report** form
(Issues → New issue → Board report), which already holds this block. Leave the passkey itself out.

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

The first report from a real board moves MICRO and AUG from "complete in simulation" toward "checked on hardware"
on the system map (`BOARD_KIT.md` §6).
