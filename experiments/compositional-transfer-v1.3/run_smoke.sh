#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python -m pip install -r requirements.txt
python src/transfer_benchmark.py --seed 63011 --people 3 --calibration 24 --tests 2 --output results/smoke
