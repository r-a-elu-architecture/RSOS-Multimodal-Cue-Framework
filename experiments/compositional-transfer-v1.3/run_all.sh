#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONPATH="$PWD/src"
python -m unittest discover -s src/tests -v
python src/compiler_stress.py
python src/stress_test.py
python src/scoped_stress.py --output results/scoped_stress_reproduced.json
python src/transfer_benchmark.py --seed 62001 --people 24 --calibration 24 --tests 16 --threshold 0.23 --output results/reproduce_development
python src/transfer_benchmark.py --seed 63011 63012 63013 --people 48 --calibration 24 --tests 16 --threshold 0.23 --output results/reproduce_holdout
python src/transfer_benchmark.py --seed 64011 64012 64013 --people 48 --calibration 24 --tests 16 --threshold 0.23 --hard-ood --output results/reproduce_ood
python src/transfer_benchmark.py --seed 63011 63012 63013 --people 48 --calibration 24 --tests 16 --threshold 0.23 --design balanced --output results/reproduce_balanced
