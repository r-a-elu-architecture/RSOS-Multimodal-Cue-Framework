"""Population check of the five session laws and six metrics (simulation, stated model)."""
import json, random, re, sys
from . import lang as Lg, sim as S
from .run import run
from .chain import run_chain

CTX = {"now_min": 600, "consent": ["subject", "operator", "auditor"], "ghost_runs": 12}


def main(full_src, out):
    full = Lg.parse(open(full_src).read())
    base_laws = "LAWS InteractionMatrix ChronoGate GhostPass ConsentStack"
    plain = Lg.parse(re.sub(r"LAWS .*", base_laws, open(full_src).read()).replace("RESCUE {SHIELD} {ANCHOR_MAX} {MIRROR_RESET}\n", ""))
    rng = random.Random(77)
    people = [S.person(rng, i) for i in range(120)]
    hours = [8, 20, 14, 20, 8, 11, 20, 17]
    res = {}
    for name, prog in (("five session laws on", full), ("session laws off", plain)):
        csi, refused, moved, boosts, ecr, sepl, stc, iec, rsi, goals, n = [], 0, 0, 0, [], [], [], [], [], 0, 0
        for p in people:
            ch = run_chain(prog, p, hours, {**CTX, "seed": p["id"] + 1})
            for R in ch["sessions"]:
                n += 1; csi.append(R["csi"]); refused += R["status"] == "refused"; goals += bool(R["goal_met"])
                moved += any("moved from" in l for l in R["log"]); boosts += bool(R["interventions"])
                m = R["metrics"]
                stc += [m["STC"]] if m["STC"] is not None else []; iec += [m["IEC"]] if m["IEC"] is not None else []; rsi.append(m["RSI"])
            if ch["metrics"]["ECR"] is not None: ecr.append(ch["metrics"]["ECR"])
            if ch["metrics"]["SEP-L"] is not None: sepl.append(ch["metrics"]["SEP-L"])
            assert ch["store"].verify()
        mean = lambda xs: round(sum(xs) / len(xs), 3) if xs else None
        res[name] = {"sessions": n, "mean_CSI": mean(csi), "goal_rate": round(goals / n, 3), "refused": refused, "moved_by_TemporalSymmetry": moved,
                     "continuity_boosters": boosts, "ECR": mean(ecr), "SEP-L": mean(sepl), "true_retain": mean([p["retain"] for p in people]),
                     "STC": mean(stc), "IEC": mean(iec), "RSI": mean(rsi)}
    # Contingency on a risky program
    src = open(full_src).read()
    src = re.sub(r"PHASE settle .*", "PHASE settle MAX 1s", src); src = re.sub(r"PHASE expand .*", "PHASE expand MAX 45s", src)
    src = re.sub(r"PHASE rebuild .*", "PHASE rebuild MAX 60s", src).replace("GhostPass ", "")
    risky = Lg.parse(src); risky_off = Lg.parse(src.replace(" Contingency", ""))
    hot = [{**p, "base": {**p["base"], "arousal": min(0.95, p["base"]["arousal"] + 0.3), "distress": min(9, p["base"]["distress"] + 1.5)}} for p in people]
    def stops(prog):
        rs = [run(prog, p, {**CTX, "seed": p["id"] + 5}) for p in hot]
        return {"stopped": sum(r["status"] == "stopped" for r in rs), "completed": sum(r["status"] == "done" for r in rs),
                "rescues": sum(len(r.get("rescues", [])) for r in rs), "mean_STC": round(sum(r["metrics"]["STC"] or 0 for r in rs) / len(rs), 3)}
    res["risky program, Contingency on"] = stops(risky); res["risky program, Contingency off"] = stops(risky_off)
    json.dump(res, open(out, "w"), indent=1)
    for k, v in res.items():
        print(k, v)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
