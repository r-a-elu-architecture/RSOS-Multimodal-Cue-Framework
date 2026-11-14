"""LIA-WW (AGENTS.md §11.15): Who&When failure attribution — prep and scoring.

    python3 -m rsxv.lia_ww prep ALL.json OUT_DIR          # strip annotations, cap steps, write judge batches
    python3 -m rsxv.lia_ww score ALL.json OUT_DIR PUBLIC.json

Operational choices (fixed and committed before any judge output existed):
- Agent of a step = the history item's `name` if present (Algorithm-Generated), else its `role` (Hand-Crafted).
- Steps are 0-based indices into the history, as in the dataset. Each step's content is capped at 1000 characters (first
  700 + "[...]" + last 300) for both arms alike; agent names and step indices are never altered.
- Annotations (mistake agent, step, reason) are written only to a separate answers file that judges are told not to open.
- Agent match: case-insensitive, after stripping, equal or one contained in the other (20 annotated agent names differ in
  form from the log's speaker names, e.g. a role suffix). Step match: exact integer.
- 3 tasks whose annotated step lies beyond the log stay in (no method can hit them) and are reported.
- A missing or unparsable judge answer counts as wrong. RANDOM: uniform over the log's distinct agents and over its steps,
  seeds 0–999, mean accuracy.
- McNemar exact one-sided on step hits; agent-level paired bootstrap (2000 resamples, seed 12345) of the difference.
"""
from __future__ import annotations

import json
import math
import pathlib
import random
import sys


def cap(s, n=1000):
    return s if len(s) <= n else s[:700] + "\n[...]\n" + s[-300:]


def prep(all_p, out):
    d = json.loads(pathlib.Path(all_p).read_text())
    o = pathlib.Path(out); o.mkdir(parents=True, exist_ok=True)
    ans = {x["id"]: {"agent": x["ans_agent"], "step": x["ans_step"], "subset": x["subset"], "n": len(x["steps"]),
                     "agents": sorted({s["agent"] for s in x["steps"]})} for x in d}
    (o / "answers.json").write_text(json.dumps(ans))
    batches, cur, size = [], [], 0
    for x in d:
        item = {"id": x["id"], "task": x["question"], "correct_answer": x["gt"],
                "log": [{"step": s["i"], "agent": s["agent"], "content": cap(s["content"])} for s in x["steps"]]}
        n = len(json.dumps(item))
        if cur and size + n > 230000:
            batches.append(cur); cur, size = [], 0
        cur.append(item); size += n
    if cur:
        batches.append(cur)
    for k, b in enumerate(batches):
        with open(o / f"batch_{k:02d}.jsonl", "w") as f:
            for it in b:
                f.write(json.dumps(it) + "\n")
    print(len(batches), "batches", [len(b) for b in batches])


def agent_ok(pred, gold):
    p, g = str(pred or "").strip().lower(), str(gold or "").strip().lower()
    return bool(p) and bool(g) and (p == g or p in g or g in p)


def load(o, arm):
    R = {}
    for f in sorted(pathlib.Path(o).glob(f"out_{arm}_*.jsonl")):
        for l in open(f):
            l = l.strip()
            if not l:
                continue
            try:
                x = json.loads(l); R[x["id"]] = x
            except Exception:
                pass
    return R


def score(all_p, out, pub_p):
    ans = json.loads((pathlib.Path(out) / "answers.json").read_text())
    ids = sorted(ans)
    arms = {a: load(out, a) for a in ("lia", "aao")}
    hit = {}
    for a, R in arms.items():
        hit[a] = {}
        for i in ids:
            r = R.get(i, {})
            try:
                st = int(r.get("step"))
            except Exception:
                st = None
            hit[a][i] = (agent_ok(r.get("agent"), ans[i]["agent"]), st is not None and str(st) == str(ans[i]["step"]).strip())
    # random baseline
    rnd = {"agent": 0.0, "step": 0.0}
    by_sub_rnd = {}
    for s in range(1000):
        rng = random.Random(s)
        for i in ids:
            a = rng.choice(ans[i]["agents"]); st = rng.randrange(ans[i]["n"])
            ra, rs = agent_ok(a, ans[i]["agent"]) / 1000 / len(ids), (str(st) == str(ans[i]["step"]).strip()) / 1000 / len(ids)
            rnd["agent"] += ra; rnd["step"] += rs
    def acc(a, sub=None, k=0):
        xs = [hit[a][i][k] for i in ids if sub is None or ans[i]["subset"] == sub]
        return sum(xs) / len(xs)
    b = sum(hit["lia"][i][1] and not hit["aao"][i][1] for i in ids)
    c = sum(hit["aao"][i][1] and not hit["lia"][i][1] for i in ids)
    p_one = sum(math.comb(b + c, k) for k in range(b, b + c + 1)) / 2 ** (b + c) if b + c else 1.0
    d = [hit["lia"][i][0] - hit["aao"][i][0] for i in ids]
    rng = random.Random(12345); n = len(d)
    dist = sorted(sum(d[rng.randrange(n)] for _ in range(n)) / n for _ in range(2000))
    ci = [dist[50], dist[1949]]
    res = {"tasks": len(ids), "answered": {a: len(arms[a]) for a in arms},
           "pooled": {a: {"agent": acc(a), "step": acc(a, k=1)} for a in arms},
           "by_subset": {s: {a: {"agent": acc(a, s), "step": acc(a, s, 1)} for a in arms} for s in ("alg", "hand")},
           "random": rnd, "step_mcnemar": {"lia_only": b, "aao_only": c, "p_one_sided": p_one},
           "agent_diff": {"mean": sum(d) / n, "ci95": ci},
           "annotated_step_beyond_log": sum(1 for i in ids if int(ans[i]["step"]) >= ans[i]["n"]),
           "published_gpt4o_with_gt": {"all_at_once": {"alg": [54.33, 12.50], "hand": [55.17, 5.26]},
                                        "step_by_step": {"alg": [35.20, 25.51], "hand": [34.48, 7.02]},
                                        "binary_search": {"alg": [44.13, 23.98], "hand": [51.72, 6.90]},
                                        "random": {"alg": [29.10, 19.06], "hand": [12.00, 4.16]}}}
    res["status"] = "PASS" if (p_one < 0.025 and ci[0] > -0.05) else "FAIL"
    pathlib.Path(pub_p).write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    a = sys.argv[1:]
    prep(a[1], a[2]) if a[0] == "prep" else score(a[1], a[2], a[3])
