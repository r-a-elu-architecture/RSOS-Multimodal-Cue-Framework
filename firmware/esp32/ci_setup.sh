#!/usr/bin/env bash
# Install arduino-cli 1.6.0 and Arduino-ESP32 cores, one data directory each (spec/ESP32_TOOLS.md §1,
# spec/BOARD_PENDING.md K1). Usage: ci_setup.sh <tools dir> <core version>...
# Writes <tools dir>/core-<version>/cfg.yaml for real_check.py (--cfg2, --cfg32, --cfg3).
set -euo pipefail
T=$(realpath -m "$1"); shift
mkdir -p "$T/bin"
if [ ! -x "$T/bin/arduino-cli" ]; then
  curl -fsSL https://downloads.arduino.cc/arduino-cli/arduino-cli_1.6.0_Linux_64bit.tar.gz | tar -xz -C "$T/bin" arduino-cli
fi
CLI="$T/bin/arduino-cli"
for v in "$@"; do
  d="$T/core-$v"; mkdir -p "$d/data" "$d/dl" "$d/user"
  cat > "$d/cfg.yaml" <<CFG
board_manager:
  additional_urls: [https://espressif.github.io/arduino-esp32/package_esp32_index.json]
directories:
  data: $d/data
  downloads: $d/dl
  user: $d/user
network:
  connection_timeout: 600s
CFG
  "$CLI" --config-file "$d/cfg.yaml" core update-index
  "$CLI" --config-file "$d/cfg.yaml" core install "esp32:esp32@$v"
  "$CLI" --config-file "$d/cfg.yaml" lib update-index
  case "$v" in
    2.*) "$CLI" --config-file "$d/cfg.yaml" lib install "GFX Library for Arduino@1.6.0" ;;   # ESP32_TOOLS §7.3
    *)   "$CLI" --config-file "$d/cfg.yaml" lib install "GFX Library for Arduino" ;;
  esac
done
