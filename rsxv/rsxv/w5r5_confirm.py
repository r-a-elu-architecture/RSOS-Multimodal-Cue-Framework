"""W5-R5 confirmation (AGENTS.md §11.9, as §11.6): every seed + 100000 for each substrate that passed the primary run
(persons additionally with install hypothesis calm_better where the regime sets none).

    python3 -m rsxv.w5r5_confirm agent [person]   # writes results/results_w5r5_confirmation.json and w5r5_confirmation.md
"""
from __future__ import annotations

import json
import pathlib
import sys

from . import w5r3_experiments as M3
from . import w5r5_experiments as M


def main(argv=None):
    subs = tuple((sys.argv[1:] if argv is None else argv) or ["agent"])
    M.SHIFT = 100000
    M3.CONFIRM = True
    R = M.run(False, subs=subs)
    rep = M.report(R).replace("# W5-R5 — the snapshot forge: results",
                              "# W5-R5 confirmation: every seed + 100000 (persons: calm_better where the regime sets none)")
    d = pathlib.Path(__file__).resolve().parents[1] / "results"
    (d / "results_w5r5_confirmation.json").write_text(json.dumps(R, indent=1, default=str))
    (d / "w5r5_confirmation.md").write_text(rep)
    print(rep)


if __name__ == "__main__":
    main()
