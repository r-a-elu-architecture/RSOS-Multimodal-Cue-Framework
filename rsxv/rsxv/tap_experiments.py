"""T-AP, directional transfer agents v1 -> person (AGENTS.md §11.8): the W5c design, one direction, pilot 8, own seeds and
level, plus a confirmation run (seeds + 100000, target person model v2 `arousal_deeper`).

    python3 -m rsxv.tap_experiments          # writes results/results_tap.json and results/tap.md
"""
from __future__ import annotations

import json
import pathlib

from . import w5c_experiments as M

M.LEVEL = 1 - 0.05 / 8
M.GATE_ALPHA = 0.05 / 8 / 4
M.SIZES = (8,)
# only agents v1 (source) and person (target) ranges are used; the others are set to unused ranges for completeness
M.SRC0 = {"person": 70000, "agent": 70100, "agent_v2": 70200}
M.PILOT0 = {"person": 72000, "agent": 72400, "agent_v2": 72800}
M.DEPLOY0 = {"person": 74000, "agent": 74200, "agent_v2": 74400}
M.ORACLE0 = {"person": 75000, "agent": 75100, "agent_v2": 75200}
M.TRUTH0 = {"person": 76000, "agent": 76200, "agent_v2": 76400}
DIR = [("agent", "person")]


def ok(r, audit):
    return bool(r["beats_all"] and all(r["noninferior"].values()) and r["safe"] and audit)


def audit_of(r):
    fc = r.get("false_certificates", {"adopted": 0, "false": 0})
    return fc["adopted"] == 0 or fc["false"] / fc["adopted"] <= 0.05, fc


def main():
    R = M.run(False, dirs=DIR)
    r = R["runs"][0]
    a, fc = audit_of(r)
    R["primary_pass"] = ok(r, a)
    R["audit"] = fc
    R["pass"] = False
    if R["primary_pass"]:
        C = M.run(False, shift=100000, dirs=DIR, person_alt=True)
        c = C["runs"][0]
        R["confirmation"] = C
        R["pass"] = bool(c["beats_all"] and all(c["noninferior"].values()) and c["safe"])
    L = ["# T-AP — directional transfer agents v1 → person: results", "",
         "Design: [`AGENTS.md`](../AGENTS.md) §11.8 (W5c design, one direction, pilot 8, level 0.05 / 8, two-sided 99.375%).",
         "Origin disclosed: the direction was chosen after it met every comparison in W5b and every condition in W5c.", "",
         "| Arm | Mean / tick | Spikes / target |", "|---|---|---|"]
    names = {"W5": "T-AP", "PILOT-ONLY-ADAPTIVE": "PILOT-ONLY", "RANDOM-CERT": "RANDOM-FUNC", "W5-NO-ADAPT": "T-AP-NO-FAIL"}
    L += [f"| {names.get(k, k)} | {v:+.4f} | {r['spikes'].get(k, float('nan')):.3f} |" for k, v in r["arms"].items()]
    L += [f"| ORACLE (upper bound) | {r['oracle']:+.4f} | |", "", "| Contrast | Estimate [interval] |", "|---|---|"]
    for k, c in list(r["contrasts"].items()) + [("W5-W3C", r["extra"]["W5-W3C"])]:
        L.append(f"| {k.replace('W5-', 'T-AP − ').replace('PILOT-ONLY-ADAPTIVE', 'PILOT-ONLY').replace('RANDOM-CERT', 'RANDOM-FUNC')} | "
                 f"{c['diff']:+.4f} [{c['lo']:+.4f}, {c['hi']:+.4f}] |")
    L.append("")
    L.append("| Spike contrast | Estimate [interval] |")
    L.append("|---|---|")
    for k, c in r["spike_contrasts"].items():
        L.append(f"| {k.replace('W5-', 'T-AP − ').replace('PILOT-ONLY-ADAPTIVE', 'PILOT-ONLY').replace('RANDOM-CERT', 'RANDOM-FUNC')} | "
                 f"{c['diff']:+.3f} [{c['lo']:+.3f}, {c['hi']:+.3f}] |")
    L += ["", f"Adopted a non-baseline table in {r['adopted']} repetitions; adopted contexts {fc['adopted']}, false "
          f"certificates {fc['false']}.", "",
          f"**Primary: {'PASS' if R['primary_pass'] else 'FAIL'}.**", ""]
    if "confirmation" in R:
        c = R["confirmation"]["runs"][0]
        L += ["## Confirmation (seeds + 100000; target person model v2, arousal_deeper)", "",
              "| Arm | Mean / tick | Spikes / target |", "|---|---|---|"]
        L += [f"| {names.get(k, k)} | {v:+.4f} | {c['spikes'].get(k, float('nan')):.3f} |" for k, v in c["arms"].items()]
        L += ["", "| Contrast | Estimate [interval] |", "|---|---|"]
        for k, x in c["contrasts"].items():
            L.append(f"| {k} | {x['diff']:+.4f} [{x['lo']:+.4f}, {x['hi']:+.4f}] |")
        L += ["", f"Beats all: {c['beats_all']}; non-inferior: {c['noninferior']}; safety gate: {c['safe']}.", ""]
    L += [f"**T-AP overall (primary and confirmation): {'PASS' if R['pass'] else 'FAIL'}.**", ""]
    d = pathlib.Path(__file__).resolve().parents[1] / "results"
    (d / "results_tap.json").write_text(json.dumps(R, indent=1, default=str))
    (d / "tap.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
