"""python -m rsxv FILE [--person SEED] [--fw] [--next OUT]"""
import argparse, json, random, sys
from . import parse, run, next_program, firmware_check, sim

ap = argparse.ArgumentParser()
ap.add_argument("file"); ap.add_argument("--person", type=int, default=3); ap.add_argument("--fw", action="store_true")
ap.add_argument("--next"); ap.add_argument("--json")
a = ap.parse_args()
prog = parse(open(a.file).read())
print("check:", json.dumps(prog["check"], ensure_ascii=False))
p = sim.person(random.Random(a.person), a.person)
r = run(prog, p, {"seed": a.person, "now_min": 600, "consent": ["subject", "operator", "auditor"]})
print(f"\nstatus: {r['status']}" + (f" ({r['stopped']['why']})" if r["stopped"] else ""))
if r["ghost"]:
    print(f"ghost pass: {r['ghost']['runs']} runs, predicted stop {r['ghost']['p_stop']:.0%}, predicted goal {r['ghost']['p_goal']:.0%}")
print("\n".join("  " + l for l in r["log"]))
o = r["outcome"]
print(f"\noutcome: agency {o['agency']:+.2f}, distress {o['distress']:+.2f}, arousal {o['arousal']:+.2f}, drift {o['drift']:+.3f}, "
      f"{o['coverage']}/11 layers ≥0.3, {o['seconds']} s, goal met: {r['goal_met']}")
print(f"audit: MCI {r['audit']['MCI']}, VEC {r['audit']['VEC']}, conflicts {r['audit']['conflicts']}")
print("\n  k  operator               block      s   agency  distress  drift   layer")
for x in r["audit"]["per_vector"]:
    print(f"  {x['k']:<3}{x['op']:<23}{x['block']:<10}{x['seconds']:>4}  {x['agency']:+.2f}   {x['distress']:+.2f}   {x['drift']:+.3f}  {x['layer']:.2f}")
if a.fw:
    fw = firmware_check(r["device_lines"])
    print("\nfirmware lines:", *fw["lines"], sep="\n  "); print("firmware errors:", fw["errors"] or "none")
    print("firmware output:", *fw["out"], sep="\n  ")
n = next_program(prog, r)
print("\nNEXT:", *n["notes"], sep="\n  - ")
if a.next:
    open(a.next, "w").write(n["text"])
if a.json:
    json.dump(r, open(a.json, "w"), indent=1, ensure_ascii=False)
