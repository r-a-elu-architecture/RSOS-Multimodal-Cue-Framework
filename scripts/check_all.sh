#!/usr/bin/env bash
# Run every check in the repository, as a reviewer would (REVIEW.md §3).
# Needs: Python 3.10+ with requirements.txt, Node.js 18+ (Python/JavaScript parity tests), a C++ compiler (firmware).
set -euo pipefail
cd "$(dirname "$0")/.."
step() { printf '\n== %s\n' "$1"; }

step "RSX: language, compilers (Python and JavaScript), repository and link checks"
(cd rsx && python3 -m unittest discover -s tests)
step "RSX/2: command layer, laws, translator and bridge into RSX"
(cd rsx2 && python3 -m unittest discover -s tests)
step "RSSO: runtime, devices, firmware, safety, nodes, LINX, CONTAIN, THERA, CM1, PEAK, camera heart rate, TRIAL, CHECKS, contribution, board"
(cd rsso && python3 -m unittest discover -s tests)
step "Toolkit: cue engine and study kit"
(cd toolkit && python3 -m unittest discover -s tests)
step "Conformance suite: virtual rig and the firmware core"
(cd rsso && python3 -m rsso.conformance | tail -1 && python3 -m rsso.conformance --firmware | tail -1)
step "Board check against the firmware core in real time (no board)"
(cd rsso && python3 -m rsso.board --sim | grep "checks passed")
step "Generated files are reproducible"
python3 architecture/build.py >/dev/null
python3 architecture/roadmap.py >/dev/null
(cd rsso && python3 -m rsso.thera >/dev/null && python3 -m rsso.cm1 >/dev/null && python3 -m rsso.peak --evaluate >/dev/null && python3 -m rsso.trial --evaluate >/dev/null && python3 -m rsso.gate --evaluate >/dev/null && python3 -m rsso.identity --evaluate >/dev/null && python3 -m rsso.atlas --evaluate >/dev/null && python3 -m rsso.night --evaluate >/dev/null && python3 -m rsso.copilot --evaluate >/dev/null && python3 -m rsso.machines --evaluate >/dev/null && python3 -m rsso.machines --channels >/dev/null && python3 -m rsso.pron --evaluate >/dev/null && python3 -m rsso.ssep --evaluate >/dev/null && python3 -m rsso.modules --evaluate >/dev/null)
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git diff --exit-code --stat -- architecture docs/data rsso/results spec/ROADMAP.md spec/CLAIMS.md && echo "unchanged"
fi
printf '\nAll checks passed.\n'
