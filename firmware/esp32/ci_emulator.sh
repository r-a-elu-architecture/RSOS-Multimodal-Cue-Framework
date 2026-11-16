#!/usr/bin/env bash
# The ESP32 emulator checks of spec/BOARD_PENDING.md K1 and K3 on Arduino-ESP32 3.3.12, in Espressif's QEMU.
# Usage: ci_emulator.sh <tools dir with core-3.3.12 and qemu/bin> <work dir>
# Each check runs on a fresh copy of the image. Exit 0 only if every check passes as registered.
set -uo pipefail
T=$(realpath -m "$1"); W=$(realpath -m "$2"); mkdir -p "$W"
HERE=$(cd "$(dirname "$0")" && pwd); REPO=$(cd "$HERE/../.." && pwd)
CLI="$T/bin/arduino-cli"; CFG="$T/core-3.3.12/cfg.yaml"; Q="$T/qemu/bin/qemu-system-xtensa"; RC="$HERE/real_check.py"
"$CLI" --config-file "$CFG" compile --fqbn esp32:esp32:esp32:FlashMode=dio --build-path "$W/build" \
  --build-property "compiler.cpp.extra_flags=-DRSOS_EMULATOR" "$HERE/rsos_esp32" || exit 1
IMG="$W/build/rsos_esp32.ino.merged.bin"
fail=0
start() {   # start <flash copy> <port> [extra qemu args]
  "$Q" -nographic -machine esp32 -drive file="$1",if=mtd,format=raw \
    -global driver=timer.esp32.timg,property=wdt_disable,value=true -serial tcp::"$2",server -monitor none "${@:3}" \
    > "$1.qemu.txt" 2>&1 &
  sleep 1
}
stop() { pkill -f "tcp::$1," || true; sleep 2; }
cp "$IMG" "$W/u.bin"; start "$W/u.bin" 5901
python3 "$RC" usb --port 5901 --boot-wait 12 --out "$W/usb.json" --expected-fail U3 || fail=1
stop 5901; start "$W/u.bin" 5901
python3 "$RC" passkey --port 5901 --boot-wait 12 --expect-from "$W/usb.json" > "$W/u9.txt" || fail=1
tail -1 "$W/u9.txt"
stop 5901
cp "$IMG" "$W/b.bin"; start "$W/b.bin" 5902
python3 - 5902 <<'PY'   # wait for the boot line, then hand the socket to the board check
import socket, sys, time
s = socket.create_connection(("localhost", int(sys.argv[1]))); s.settimeout(0.5); buf = b""; t = time.time()
while b"NOTE emulator build" not in buf and time.time() - t < 120:
    try: buf += s.recv(4096)
    except socket.timeout: pass
time.sleep(2); s.close()
PY
(cd "$REPO/rsso" && python3 -m rsso.board --port socket://localhost:5902 --out "$W/board.md") || fail=1
stop 5902
cp "$IMG" "$W/p.bin"; rm -f "$W/led.log"; start "$W/p.bin" 5903 -trace "led_*" -D "$W/led.log"
python3 "$RC" pwm --port 5903 --trace "$W/led.log" --out "$W/pwm.json" || fail=1
stop 5903
echo "emulator checks: $([ $fail = 0 ] && echo pass || echo FAIL)"
exit $fail
