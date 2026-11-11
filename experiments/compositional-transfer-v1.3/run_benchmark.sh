#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python -m pip install -r requirements.txt
python src/transfer_benchmark.py --seed 63011 63012 63013 --people 48 --calibration 24 --tests 16 --threshold 0.23 --output results/reproduced_holdout
python src/transfer_benchmark.py --seed 64011 64012 64013 --people 48 --calibration 24 --tests 16 --threshold 0.23 --hard-ood --output results/reproduced_ood
