"""T-AP-R, how far the confirmed transfer reaches (AGENTS.md §11.9): T-AP-4 (agents v1 -> person, pilot 4) and T-AP-V2
(agents v2 -> person, pilot 8). Each is the T-AP design with its own seeds and level, confirmation on + 100000 seeds and the
person model v2 with W3C included.

    python3 -m rsxv.tapr_experiments [T-AP-4|T-AP-V2]     # writes results/results_tapr.json and results/tapr.md
"""
from __future__ import annotations

import inspect
import json
import pathlib
import sys

from . import w5c_experiments as M

M.LEVEL = 1 - 0.05 / 11
M.GATE_ALPHA = 0.05 / 11 / 4
M.C.ENV["person_v2"] = M.ENV["person_v2"]
M.C.BASE_OF["person_v2"] = "person"
_d = inspect.getsource(M.direction)
_old = '''        p3, i3 = C.decide_transfer(tgt if tgt != "person_v2" else "person", seeds, w3c_label) \\
            if tgt != "person_v2" else (None, None)'''
assert _old in _d
exec(_d.replace(_old, '''        p3, i3 = C.decide_transfer(tgt, seeds, w3c_label)'''), M.__dict__)
_r = inspect.getsource(M.run)
_o2 = "for n in ((8,) if quick or shift else SIZES):"
assert _o2 in _r
exec(_r.replace(_o2, "for n in SIZES:"), M.__dict__)

CLAIMS = {
    "T-AP-4": {"src": "agent", "size": 4, "SRC0": 201100, "PILOT0": 202000, "DEPLOY0": 204000, "ORACLE0": 205000,
               "TRUTH0": 206000},
    "T-AP-V2": {"src": "agent_v2", "size": 8, "SRC0": 211200, "PILOT0": 212000, "DEPLOY0": 214000, "ORACLE0": 215000,
                "TRUTH0": 216000},
}


def setup(c):
    M.SIZES = (c["size"],)
    M.SRC0 = {"person": c["SRC0"] - 1000, "agent": c["SRC0"], "agent_v2": c["SRC0"]}
    M.PILOT0 = {"person": c["PILOT0"], "agent": c["PILOT0"] + 400, "agent_v2": c["PILOT0"] + 800}
    M.DEPLOY0 = {"person": c["DEPLOY0"], "agent": c["DEPLOY0"] + 200, "agent_v2": c["DEPLOY0"] + 400}
    M.ORACLE0 = {"person": c["ORACLE0"], "agent": c["ORACLE0"] + 100, "agent_v2": c["ORACLE0"] + 200}
    M.TRUTH0 = {"person": c["TRUTH0"], "agent": c["TRUTH0"] + 200, "agent_v2": c["TRUTH0"] + 400}


def verdict(r, need_audit=True):
    fc = r.get("false_certificates", {"adopted": 0, "false": 0})
    audit = fc["adopted"] == 0 or fc["false"] / fc["adopted"] <= 0.05
    return bool(r["beats_all"] and all(r["noninferior"].values()) and r["safe"] and (audit or not need_audit)), fc


def fmt(c):
    return f"{c['diff']:+.4f} [{c['lo']:+.4f}, {c['hi']:+.4f}]"


def section(name, r, title):
    nm = {"W5": name, "PILOT-ONLY-ADAPTIVE": "PILOT-ONLY", "RANDOM-CERT": "RANDOM-FUNC", "W5-NO-ADAPT": f"{name}-NO-FAIL"}
    L = [f"### {title}", "", "| Arm | Mean / tick | Spikes / target |", "|---|---|---|"]
    L += [f"| {nm.get(k, k)} | {v:+.4f} | {r['spikes'].get(k, float('nan')):.3f} |" for k, v in r["arms"].items()]
    L += ["", "| Contrast | Score | Spikes |", "|---|---|---|"]
    for o in ("PILOT-ONLY-ADAPTIVE", "NONE", "RANDOM-CERT", "W3C"):
        sc = r["contrasts"].get(f"W5-{o}") or (r["extra"]["W5-W3C"] if o == "W3C" else None)
        sp = r["spike_contrasts"].get(f"W5-{o}")
        if sc:
            L.append(f"| {name} − {nm.get(o, o)} | {fmt(sc)} | {fmt(sp) if sp else '—'} |")
    L += ["", f"Beats PILOT-ONLY, NONE, RANDOM-FUNC: {r['beats_all']}; non-inferior: {r['noninferior']}; safety gate: "
          f"{r['safe']}; adopted in {r['adopted']} repetitions.", ""]
    return L


def run_claim(name):
    c = CLAIMS[name]
    setup(c)
    d = [(c["src"], "person")]
    R = M.run(False, dirs=d)
    r = R["runs"][0]
    ok, fc = verdict(r)
    out = {"claim": name, "primary": r, "primary_pass": ok, "audit": fc, "pass": False}
    if ok:
        C_ = M.run(False, shift=100000, dirs=d, person_alt=True)
        cr = C_["runs"][0]
        out["confirmation"] = cr
        out["pass"] = verdict(cr, need_audit=False)[0]
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    names = argv or list(CLAIMS)
    res = {n: run_claim(n) for n in names}
    L = ["# T-AP-R — how far the confirmed transfer reaches: results", "",
         "Design: [`AGENTS.md`](../AGENTS.md) §11.9 (T-AP design; level 0.05 / 11, two-sided 99.55%).", ""]
    for n, X in res.items():
        L += [f"## {n}: {'PASS' if X['pass'] else 'FAIL'}", ""]
        L += section(n, X["primary"], f"Primary (pilot {CLAIMS[n]['size']}, source {CLAIMS[n]['src']})")
        L += [f"False certificates: {X['audit']['false']} of {X['audit']['adopted']} adopted contexts. "
              f"Primary: {'PASS' if X['primary_pass'] else 'FAIL'}.", ""]
        if "confirmation" in X:
            L += section(n, X["confirmation"], "Confirmation (seeds + 100000; person model v2 arousal_deeper; W3C included)")
    d = pathlib.Path(__file__).resolve().parents[1] / "results"
    (d / "results_tapr.json").write_text(json.dumps(res, indent=1, default=str))
    (d / "tapr.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
