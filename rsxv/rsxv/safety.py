"""Safety layer (step R2). Specification: ../AGENTS.md §3.1.

Since S1 (spec/CONTAIN.md §9) there is one rule set for agents and people: this module re-exports
rsso/rsso/safety.py, which the person-facing pages mirror in docs/js/safety.js (identical results, tested).
Rules are fixed; agents cannot edit them (they are part of the Spine).
"""
from __future__ import annotations

import pathlib
import sys

_RSSO = str(pathlib.Path(__file__).resolve().parents[2] / "rsso")
if _RSSO not in sys.path:
    sys.path.insert(0, _RSSO)

from rsso.safety import (MODES, SEVERITY, RECOVERY_H, WEEKLY_CAP, RESPONSES, MESSAGES, MODE_ALLOWED,  # noqa: E402,F401
                         screen, SafetyState, may_start_deep_session, adjusted_effect, spine_flags)
