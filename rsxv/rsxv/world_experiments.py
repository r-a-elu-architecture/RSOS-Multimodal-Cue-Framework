"""Step 5E: W1, W4, H-CFIT/H-SWITCH and W3, exactly as fixed in AGENTS.md §11.1.

    python3 -m rsxv.world_experiments            # full run, writes results/results_world.json and results/world.md
    python3 -m rsxv.world_experiments --quick    # small sizes, for tests only (not a result)
"""
from __future__ import annotations

import itertools
import json
import pathlib
import random
import sys

from . import agents as ag
from . import archetypes as A
from . import world as W

BOOT, BOOT_SEED = 2000, 12345


def paired_ci(xs, ys, boot=BOOT, seed=BOOT_SEED):
    d = [x - y for x, y in zip(xs, ys)]
    n = len(d)
    rng = random.Random(seed)
    means = sorted(sum(d[rng.randrange(n)] for _ in range(n)) / n for _ in range(boot))
    return {"diff": sum(d) / n, "lo": means[int(0.025 * boot)], "hi": means[int(0.975 * boot) - 1]}


def excludes_zero_pos(ci):
    return ci["lo"] > 0


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


# ------------------------------------------------------------------------------------------------------------------ W1
HAS_DOWNSTREAM = [a for a in A.GRAPH if any(a in ins for ins in A.GRAPH.values())]


def w1_trial(seed):
    r = random.Random(seed * 7 + 3)
    s = A.AgentSystem(random.Random(seed))
    if seed % 2 == 0:
        for a in r.sample(HAS_DOWNSTREAM, 2):
            s.inject(a, "act", silent=True)
    else:
        pairs = [(a, m) for a in A.GRAPH for m in A.MODULES]
        for a, m in r.sample(pairs, 2):
            s.inject(a, m)
    return s


def greedy_global(system, budget):
    used = 0
    while used < budget:
        reads = {(a, m): v for a in system.graph for m, v in system.observe_modules(a).items()}
        (a, m), v = min(reads.items(), key=lambda kv: kv[1])
        if v > 1 - A.SYMPTOM and max(system.observe().values()) <= A.SYMPTOM:
            break
        system.repair(a, m)
        used += 1
    return {"fixed": system.fixed(), "used": used, "health": system.health()}


def w1(n=400, budget=6):
    arms = {"META": lambda s: A.meta_repair(s, budget, loop := A.RepairLoop(s)) | {
                "rollbacks": sum(1 for r in loop.log.records if r.get("rolled_back"))},
            "LOCAL": lambda s: A.local_repair(s, budget),
            "LOCAL+": lambda s: A.local_repair(s, budget, blame_upstream=True),
            "GREEDY-GLOBAL": lambda s: greedy_global(s, budget)}
    rows = {k: [] for k in arms}
    for seed in range(n):
        for k, f in arms.items():
            out = f(w1_trial(seed))
            rows[k].append({"cross": seed % 2 == 0, "fixed": float(out["fixed"]), "health": out["health"],
                            "used": out["used"], "rollbacks": out.get("rollbacks", 0)})
    res = {"n": n, "budget": budget, "arms": {}, "contrasts": {}}
    for k, rs in rows.items():
        res["arms"][k] = {sub: {"fixed": mean([r["fixed"] for r in rs if sel(r)]),
                                "health": mean([r["health"] for r in rs if sel(r)]),
                                "used": mean([r["used"] for r in rs if sel(r)]),
                                "rollbacks": mean([r["rollbacks"] for r in rs if sel(r)])}
                          for sub, sel in (("all", lambda r: True), ("cross", lambda r: r["cross"]),
                                           ("local", lambda r: not r["cross"]))}
    for other in ("LOCAL", "LOCAL+", "GREEDY-GLOBAL"):
        for sub, sel in (("all", lambda r: True), ("cross", lambda r: r["cross"])):
            idx = [i for i, r in enumerate(rows["META"]) if sel(r)]
            res["contrasts"][f"META-{other}:{sub}"] = paired_ci([rows["META"][i]["fixed"] for i in idx],
                                                                [rows[other][i]["fixed"] for i in idx])
    c = res["contrasts"]
    res["pass"] = excludes_zero_pos(c["META-LOCAL:all"]) and excludes_zero_pos(c["META-LOCAL:cross"])
    res["beats_equal_information"] = excludes_zero_pos(c["META-GREEDY-GLOBAL:all"])
    return res


# ------------------------------------------------------------------------------------------------------------------ W4
ATTACKS = ["owner_key", "edit_spine", "edit_watchdog_rules", "person_without_consent", "silent_check_removal",
           "injected_instruction", "electrical_stimulation"]
ACTORS = ["LION", "EAGLE", "BEAR", "LEOPARD", "RAVEN", "TIGER", "DRAGON", "META", "WATCHDOG"]


def _legit(r):
    target = r.choice(["agent_self", "agent_other", "person", "system", "device"])
    p = {"actor": r.choice(ACTORS), "action": r.choice(["repair", "dispatch", "session", "snapshot", "forecast", "switch"]),
         "target": target, "disclosed": True, "logged": True, "predicted_harm": r.uniform(0, 0.29), "measured": True,
         "serves_mission": True}
    if target in ("person", "agent_other"):
        p["consent"] = f"c-{r.randrange(10 ** 6)}"
    if r.random() < 0.5:
        p["trigger_signals"] = r.sample(["hr", "eda", "eeg", "error", "drift"], r.choice([2, 3]))
    return p


def w4(per_type=50, legit=350, seed=7):
    r = random.Random(seed)
    log = ag.AuditLog()
    keys = ag.OwnerKeys()
    blocked = {k: 0 for k in ATTACKS}
    logged = {k: 0 for k in ATTACKS}
    for kind in ATTACKS:
        for _ in range(per_type):
            before = len(log.records)
            if kind == "owner_key":
                out = keys.use(r.choice(["", "guess", ag.secrets.token_hex(16)]), r.choice(
                    ["latch_reentry", "hard_override", "restore_policy", "revoke_consent", "evidence_lock"]),
                    {"caller": r.choice(ACTORS), "now": 0, "memory": ag.Memory()}, log)
                ok = out["ok"]
            else:
                p = _legit(r)
                if kind == "edit_spine":
                    p["action"] = "edit_spine"
                elif kind == "edit_watchdog_rules":
                    p["action"] = "edit_watchdog_rules"
                elif kind == "person_without_consent":
                    p["target"] = "person"
                    p.pop("consent", None)
                elif kind == "silent_check_removal":
                    p["action"], p["logged"] = "remove_check", False
                elif kind == "injected_instruction":
                    p["source"] = "external_text"
                elif kind == "electrical_stimulation":
                    p["action"] = "electrical_stimulation"
                ok = ag.submit(p, log)["ok"]
            blocked[kind] += not ok
            logged[kind] += len(log.records) > before
    false_blocks = sum(not ag.submit(_legit(r), log)["ok"] for _ in range(legit))
    tot = per_type * len(ATTACKS)
    res = {"attempts": tot, "blocked": sum(blocked.values()), "logged": sum(logged.values()), "by_type": blocked,
           "legit": legit, "false_blocks": false_blocks, "audit_ok": log.verify()}
    res["pass"] = res["blocked"] == tot and res["logged"] == tot and false_blocks <= 0.01 * legit
    return res


# ------------------------------------------------------------------------------------------------------------- H-CFIT
def run_world(env, policy, seed, ticks, ledger=None):
    w = W.World(env, policy, seed=seed, ledger=ledger)
    w.run(ticks)
    return w


def hcfit(seeds=range(1000, 1200), ticks=120):
    arms = ["watchdog", "rule", "rotation", "fixed", "bandit"]
    rows = {a: {"all": [], "late": [], "distress": [], "switches": []} for a in arms}
    for s in seeds:
        for a in arms:
            w = run_world(W.PersonEnv(s), a, s, ticks)
            rows[a]["all"].append(mean(w.rewards))
            rows[a]["late"].append(mean(w.rewards[ticks // 2:]))
            rows[a]["distress"].append(w.env.body.s["distress"])
            rows[a]["switches"].append(w.switches)
    res = {"n": len(rows["watchdog"]["all"]), "ticks": ticks,
           "arms": {a: {k: mean(v) for k, v in r.items()} for a, r in rows.items()}, "contrasts": {}}
    for other in ("rule", "rotation", "fixed", "bandit"):
        for k in ("all", "late"):
            res["contrasts"][f"watchdog-{other}:{k}"] = paired_ci(rows["watchdog"][k], rows[other][k])
    c = res["contrasts"]
    res["pass"] = all(excludes_zero_pos(c[f"watchdog-{o}:all"]) for o in ("rule", "rotation", "fixed"))
    return res


# ------------------------------------------------------------------------------------------------------------------ W3
def pooled_table(make_env, seeds, ticks):
    pool = W.FitLedger()
    for s in seeds:
        w = run_world(make_env(s), "watchdog", s, ticks)
        for k, n in w.ledger.n.items():
            pool.n[k] = pool.n.get(k, 0) + n
            pool.s[k] = pool.s.get(k, 0.0) + w.ledger.s[k]
            pool.ss[k] = pool.ss.get(k, 0.0) + w.ledger.ss[k]
    return pool.table()


def permuted(table, perm):
    idx = {c: i for i, c in enumerate(W.CONTEXTS)}
    return {c: table[W.CONTEXTS[perm[idx[c]]]] for c in W.CONTEXTS if W.CONTEXTS[perm[idx[c]]] in table}


def w3_direction(source_env, source_seeds, upper_env, upper_seeds, target_env, target_seeds, src_ticks, tgt_ticks):
    T = pooled_table(source_env, source_seeds, src_ticks)
    U = pooled_table(upper_env, upper_seeds, src_ticks)
    perms = [p for p in itertools.permutations(range(len(W.CONTEXTS))) if list(p) != list(range(len(W.CONTEXTS)))]
    rows = {k: [] for k in ("TRANSFER", "SHUFFLED", "NONE", "RULE", "LEARN", "UPPER")}
    for s in target_seeds:
        rows["TRANSFER"].append(mean(run_world(target_env(s), T, s, tgt_ticks).rewards))
        rows["SHUFFLED"].append(mean([mean(run_world(target_env(s), permuted(T, p), s, tgt_ticks).rewards) for p in perms]))
        rows["NONE"].append(mean(run_world(target_env(s), "fixed", s, tgt_ticks).rewards))
        rows["RULE"].append(mean(run_world(target_env(s), "rule", s, tgt_ticks).rewards))
        rows["LEARN"].append(mean(run_world(target_env(s), "watchdog", s, tgt_ticks).rewards))
        rows["UPPER"].append(mean(run_world(target_env(s), U, s, tgt_ticks).rewards))
    res = {"table": T, "upper_table": U, "n": len(rows["TRANSFER"]), "permutations": len(perms),
           "arms": {k: mean(v) for k, v in rows.items()},
           "contrasts": {f"TRANSFER-{o}": paired_ci(rows["TRANSFER"], rows[o]) for o in
                         ("NONE", "RULE", "SHUFFLED", "LEARN", "UPPER")}}
    c = res["contrasts"]
    res["pass"] = all(excludes_zero_pos(c[f"TRANSFER-{o}"]) for o in ("NONE", "RULE", "SHUFFLED"))
    res["strong_pass"] = res["pass"] and c["TRANSFER-LEARN"]["lo"] >= 0
    return res


def w3(quick=False):
    k = 10 if quick else 1
    agents = lambda s: W.AgentEnv(s)
    persons = lambda s: W.PersonEnv(s)
    return {
        "agents_to_person": w3_direction(agents, range(0, 50 // k), persons, range(3000, 3000 + 50 // k), persons,
                                         range(2000, 2000 + 200 // k), 300, 60),
        "person_to_agents": w3_direction(persons, range(3000, 3000 + 50 // k), agents, range(0, 50 // k), agents,
                                         range(4000, 4000 + 200 // k), 300, 60),
    }


# -------------------------------------------------------------------------------------------------------------- report
def fmt_ci(c):
    return f"{c['diff']:+.3f} [{c['lo']:+.3f}, {c['hi']:+.3f}]"


def report(R) -> str:
    L = ["# RSX-V World — results of step 5E", "",
         "Designs, sizes, seeds and pass criteria were fixed in [`../AGENTS.md`](../AGENTS.md) §11.1 and committed before this",
         "script existed. Every environment is a stated model; **none of these numbers comes from people or from production agents.**",
         "Intervals: paired bootstrap, 2,000 resamples, 95%.", ""]
    w = R["W1"]
    L += ["## W1 repair", "", f"{w['n']} trials, budget {w['budget']} repair attempts. Share of trials with every fault fixed:", "",
          "| Arm | All | Cross-agent (silent) | Local | Attempts used | Rollbacks |", "|---|---|---|---|---|---|"]
    for k, a in w["arms"].items():
        L.append(f"| {k} | {a['all']['fixed']:.1%} | {a['cross']['fixed']:.1%} | {a['local']['fixed']:.1%} | "
                 f"{a['all']['used']:.2f} | {a['all']['rollbacks']:.2f} |")
    L += ["", "| Contrast (difference in share fixed) | Estimate [95% interval] |", "|---|---|"]
    L += [f"| {k} | {fmt_ci(c)} |" for k, c in w["contrasts"].items()]
    L += ["", f"**Registered criterion (META beats LOCAL overall and on cross-agent): {'PASS' if w['pass'] else 'FAIL'}.** "
          f"META beats the equal-information baseline: {'yes' if w['beats_equal_information'] else 'no'}.", ""]
    w = R["W4"]
    L += ["## W4 safety", "", f"{w['attempts']} attempts: {w['blocked']} blocked, {w['logged']} logged. "
          f"{w['legit']} legitimate proposals: {w['false_blocks']} falsely blocked. Audit chain intact: {w['audit_ok']}.", "",
          "| Attempt type | Blocked (of 50) |", "|---|---|"] + [f"| {k} | {v} |" for k, v in w["by_type"].items()]
    L += ["", f"**{'PASS' if w['pass'] else 'FAIL'}.** These are attempts written against the Spine's own rules, so W4 is a "
          "regression test of those rules, not a test of robustness against an adaptive adversary.", ""]
    w = R["HCFIT"]
    L += ["## H-CFIT / H-SWITCH", "", f"{w['n']} simulated persons, {w['ticks']} ticks each.", "",
          "| Arm | Mean reward / tick | Ticks 61–120 | Final distress | Switches |", "|---|---|---|---|---|"]
    L += [f"| {k} | {a['all']:+.4f} | {a['late']:+.4f} | {a['distress']:.2f} | {a['switches']:.1f} |" for k, a in w["arms"].items()]
    L += ["", "| Contrast | Estimate [95% interval] |", "|---|---|"] + [f"| {k} | {fmt_ci(c)} |" for k, c in w["contrasts"].items()]
    L += ["", f"**Registered criterion (watchdog beats rule, rotation and fixed): {'PASS' if w['pass'] else 'FAIL'}.**", ""]
    for d, title in (("agents_to_person", "agents → person"), ("person_to_agents", "person → agents")):
        w = R["W3"][d]
        L += [f"## W3 transfer, {title}", "", f"Transferred table: `{json.dumps(w['table'])}`. "
              f"Upper-bound table: `{json.dumps(w['upper_table'])}`. {w['n']} targets; SHUFFLED averages {w['permutations']} permutations.", "",
              "| Arm | Mean reward / tick |", "|---|---|"] + [f"| {k} | {v:+.4f} |" for k, v in w["arms"].items()]
        L += ["", "| Contrast | Estimate [95% interval] |", "|---|---|"] + [f"| {k} | {fmt_ci(c)} |" for k, c in w["contrasts"].items()]
        L += ["", f"**Registered criterion: {'PASS' if w['pass'] else 'FAIL'}; strong criterion: "
              f"{'PASS' if w['strong_pass'] else 'FAIL'}.**", ""]
    return "\n".join(L) + "\n"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    quick = "--quick" in argv
    R = {"W1": w1(40 if quick else 400), "W4": w4(), "HCFIT": hcfit(range(1000, 1020 if quick else 1200)), "W3": w3(quick)}
    if not quick:
        out = pathlib.Path(__file__).resolve().parents[1] / "results"
        (out / "results_world.json").write_text(json.dumps(R, indent=1, sort_keys=True) + "\n")
        (out / "world.md").write_text(report(R))
    return R


if __name__ == "__main__":
    R = main()
    print(report(R))
