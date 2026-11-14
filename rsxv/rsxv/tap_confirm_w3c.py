"""T-AP confirmation, completing the W3C comparator for the person model v2 (AGENTS.md §11.8 requires the confirmation to
meet the same conditions, which include non-inferiority to W3C; the shared transfer code had skipped W3C for person v2).
Reruns the registered confirmation (same seeds, same procedure, deterministic) with W3C's own pilot and decision run on the
person model v2.

    python3 -m rsxv.tap_confirm_w3c        # writes results/results_tap_confirm_w3c.json and appends to results/tap.md
"""
from __future__ import annotations

import inspect
import json
import pathlib

from . import tap_experiments as T

M = T.M
M.C.ENV["person_v2"] = M.ENV["person_v2"]
M.C.BASE_OF["person_v2"] = "person"
src = inspect.getsource(M.direction)
old = '''        p3, i3 = C.decide_transfer(tgt if tgt != "person_v2" else "person", seeds, w3c_label) \\
            if tgt != "person_v2" else (None, None)'''
assert old in src
exec(src.replace(old, '''        p3, i3 = C.decide_transfer(tgt, seeds, w3c_label)'''), M.__dict__)


def main():
    C = M.run(False, shift=100000, dirs=T.DIR, person_alt=True)
    c = C["runs"][0]
    ok = bool(c["beats_all"] and all(c["noninferior"].values()) and c["safe"])
    out = {"arms": c["arms"], "spikes": c["spikes"], "contrasts": c["contrasts"], "w5_w3c": c["extra"]["W5-W3C"],
           "noninferior": c["noninferior"], "safe": c["safe"], "spike_contrasts": c["spike_contrasts"], "pass": ok}
    d = pathlib.Path(__file__).resolve().parents[1] / "results"
    (d / "results_tap_confirm_w3c.json").write_text(json.dumps(out, indent=1, default=str))
    x = c["extra"]["W5-W3C"]
    s = c["spike_contrasts"].get("W5-W3C")
    add = ["", "## Confirmation completed with the W3C comparator on person model v2", "",
           f"W3C mean {c['arms'].get('W3C', float('nan')):+.4f}; T-AP − W3C {x['diff']:+.4f} [{x['lo']:+.4f}, {x['hi']:+.4f}]; "
           f"spikes T-AP − W3C {s['diff']:+.3f} [{s['lo']:+.3f}, {s['hi']:+.3f}]. Non-inferior: {c['noninferior']}; "
           f"safety gate against every comparator: {c['safe']}; beats PILOT-ONLY, NONE, RANDOM-FUNC: {c['beats_all']}.", "",
           f"**T-AP confirmation with every registered comparator: {'PASS' if ok else 'FAIL'}.**", ""]
    md = d / "tap.md"
    md.write_text(md.read_text() + "\n".join(add))
    print("\n".join(add))


if __name__ == "__main__":
    main()
