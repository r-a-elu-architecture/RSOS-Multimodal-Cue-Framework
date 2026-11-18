"""A plan per person from the organism (spec/ROLE_ORGANISM.md §2.4). Deterministic; reads docs/data/organism.json and
docs/data/tier_map.json. The plan is a proposal for the person, or the person and their practitioner, to approve.

    python3 -m rsxv.personlab.organism_plan ../docs/data/personlab_persons.json results/organism_plans.json
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
LEVELS = ("environment", "behaviour", "skills", "beliefs", "identity", "mission")
QUESTION = {
    "environment": "Where and when does this happen, and where do you want to be?",
    "behaviour": "What do you do now, and what do you want to do instead?",
    "skills": "Which capability would help, and how would you know you have it?",
    "beliefs": "What matters to you here, and which belief would serve you better?",
    "identity": "Who are you when this is going well?",
    "mission": "What is this for, and who else benefits when it works?",
}
STEP_WHY = {
    "Stabilise": "Steady the body and lower intensity before any change",
    "Monitor": "Map the current statements and what keeps them in place",
    "Plan": "Work at the level of beliefs, identity and mission",
    "Repair": "Change the behaviour that keeps the problem going",
    "Drive": "Build the skill and act in the real environment",
    "Baseline": "Keep the gain: maintenance and every real trigger",
}


def load(rel):
    return json.loads((REPO / rel).read_text(encoding="utf-8"))


def _words(t):
    return set(re.findall(r"[a-z]{4,}", t.lower()))


def plan(person: dict, org: dict | None = None, tmap: dict | None = None) -> dict:
    org = org or load("docs/data/organism.json")
    tiers = (tmap or load("docs/data/tier_map.json"))["tiers"]
    prof = org["role_profiles"]
    present = set(person.get("levels", {}))
    signals = {s["kind"] for s in person.get("signals", [])}
    roles = []
    if person.get("initial_intensity", 0) >= 4 or signals & {"load", "conflict"}:
        roles.append("Stabilise")
    roles.append("Monitor")
    if present & {"beliefs", "identity", "mission"}:
        roles.append("Plan")
    if "behaviour" in present:
        roles.append("Repair")
    if present & {"skills", "environment"}:
        roles.append("Drive")
    roles.append("Baseline")
    story = _words(person.get("story", ""))
    steps, candidates = [], []
    for role in roles:
        p = prof[role]
        cand = p["built_tiers"]
        candidates.append(len(cand))
        ranked = sorted(cand, key=lambda t: (-len(story & _words(tiers[t].get("title", "") + " " + tiers[t].get("operator", ""))), t))
        start = person.get("initial_intensity", 3)
        steps.append({
            "role": role, "archetype": p["archetype"], "glyph": p["glyph"], "tacton": p["tacton"], "why": STEP_WHY[role],
            "tiers": [{"id": t, "title": tiers[t]["title"], "response": tiers[t]["response"]} for t in ranked[:3]],
            "proposed_tiers_waiting": len(p["proposed_tiers"]) if not cand else 0,
            "agent_sensor": p["sensor"],
            "measures": [{"name": "intensity (1-5)", "target": f"<= {max(1, start - 1):g}"},
                         {"name": "progress toward the desired state", "target": ">= 50%"},
                         {"name": "feedback (1-5)", "target": ">= 4"}]})
    questions = [{"level": l, "question": QUESTION[l]} for l in LEVELS if l not in present]
    if not person.get("desired"):
        questions.insert(0, {"level": "desired", "question": "What do you want instead? Say it for each level that "
                                                            "matters to you."})
    return {"person": person["id"], "problem_type": person.get("problem_type"), "steps": steps,
            "intake_questions": questions, "waits_for_answers": [s["role"] for s in steps if s["role"] in ("Plan",)]
            if not person.get("desired") else [], "candidates_per_step": candidates, "approved": False}


def validate(pl: dict, tmap: dict) -> list:
    bad = []
    for s in pl["steps"]:
        for t in s["tiers"]:
            if t["id"] not in tmap["tiers"] or tmap["tiers"][t["id"]].get("status") != "built":
                bad.append(f"{pl['person']} {s['role']} {t['id']} not built")
        if not s["measures"] or not all(m.get("target") for m in s["measures"]):
            bad.append(f"{pl['person']} {s['role']} measure without target")
    return bad


if __name__ == "__main__":
    persons = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))["persons"]
    org, tmap = load("docs/data/organism.json"), load("docs/data/tier_map.json")
    plans = [plan(p, org, tmap) for p in persons]
    json.dump({"spec": "spec/ROLE_ORGANISM.md §2.4", "plans": plans}, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
    c = [x for p in plans for x in p["candidates_per_step"]]
    print(json.dumps({"plans": len(plans), "invalid": sum(len(validate(p, tmap)) for p in plans),
                      "mean_candidates_per_step": sum(c) / len(c), "steps_per_plan": sum(len(p["steps"]) for p in plans) / len(plans)}))
