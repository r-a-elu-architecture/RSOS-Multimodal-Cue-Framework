"""PERSONLAB step 1 (spec/PERSONLAB.md §2): the identity profile.

A profile is plain JSON-ready data:

    {
      "id": "...", "source_dataset": "...", "licence": "...", "document_id": "...", "builder": "...", "created": "...",
      "levels": {level_id: {"statements": [statement, ...]}},
      "current": {level_id: [state item, ...]}, "desired": {level_id: [state item, ...]},
      "signals": [{"kind": "...", "text": "...", "source": src}]
    }
    statement  = {"id": "...", "text": "I am ...", "source": src, "details": [{"kind": "where"|"when"|"detail", "text": "...", "source": src}]}
    state item = {"text": "...", "node": statement id or None, "source": src}
    src        = {"doc": "...", "span": [start, end]}
"""
from __future__ import annotations

LEVELS = [
    {"id": "environment", "name": "Environment", "question": "Where and when?",
     "definition": "The external conditions, surroundings, context and physical setting in which you operate "
                   "(for example your office, home, geography or time constraints)."},
    {"id": "behaviour", "name": "Behaviour", "question": "What do I do?",
     "definition": "The specific actions, habits, choices and reactions you physically perform."},
    {"id": "skills", "name": "Capabilities and skills", "question": "How do I do it?",
     "definition": "The internal strategies, competencies, knowledge and skills you deploy to carry out your behaviours."},
    {"id": "beliefs", "name": "Beliefs and values", "question": "Why do I do it? What matters to me?",
     "definition": "The underlying drivers, permissions, criteria and convictions that either empower or limit your "
                   "capabilities and actions."},
    {"id": "identity", "name": "Identity", "question": "Who am I?",
     "definition": "Your core sense of self, self-concept, and the roles or titles you embrace."},
    {"id": "mission", "name": "Purpose and mission", "question": "For what purpose? Who else?",
     "definition": "The transpersonal layer: your connection to a larger system, community, organisation or purpose "
                   "beyond yourself."},
]
LEVEL_IDS = [lv["id"] for lv in LEVELS]
DETAIL_KINDS = ("where", "when", "detail")
REQUIRED = ("id", "source_dataset", "licence", "document_id", "builder", "created", "levels")


def _src_ok(src) -> bool:
    return (isinstance(src, dict) and isinstance(src.get("doc"), str) and src["doc"]
            and isinstance(src.get("span"), (list, tuple)) and len(src["span"]) == 2
            and all(isinstance(x, int) for x in src["span"]) and 0 <= src["span"][0] <= src["span"][1])


def validate(p: dict) -> list:
    """Every problem with a profile, as readable strings. An empty list means valid."""
    probs = []
    for k in REQUIRED:
        if not p.get(k):
            probs.append(f"missing {k}")
    ids = set()
    for lv, node in (p.get("levels") or {}).items():
        if lv not in LEVEL_IDS:
            probs.append(f"unknown level {lv}")
            continue
        for st in node.get("statements", []):
            sid = st.get("id")
            if not sid:
                probs.append(f"{lv}: statement without id")
            elif sid in ids:
                probs.append(f"{lv}: duplicate statement id {sid}")
            ids.add(sid)
            if not (st.get("text") or "").strip():
                probs.append(f"{lv}/{sid}: empty statement")
            if not _src_ok(st.get("source")):
                probs.append(f"{lv}/{sid}: missing source")
            for d in st.get("details", []):
                if d.get("kind") not in DETAIL_KINDS:
                    probs.append(f"{lv}/{sid}: unknown detail kind {d.get('kind')}")
                if not (d.get("text") or "").strip():
                    probs.append(f"{lv}/{sid}: empty detail")
                if not _src_ok(d.get("source")):
                    probs.append(f"{lv}/{sid}: detail missing source")
    for part in ("current", "desired"):
        for lv, items in (p.get(part) or {}).items():
            if lv not in LEVEL_IDS:
                probs.append(f"{part}: unknown level {lv}")
                continue
            for it in items:
                if not (it.get("text") or "").strip():
                    probs.append(f"{part}/{lv}: empty item")
                if it.get("node") is not None and it["node"] not in ids:
                    probs.append(f"{part}/{lv}: points at missing node {it['node']}")
                if not _src_ok(it.get("source")):
                    probs.append(f"{part}/{lv}: missing source")
    for s in p.get("signals", []):
        if not (s.get("text") or "").strip() or not _src_ok(s.get("source")):
            probs.append("signal without text or source")
    return probs


def to_tree(p: dict) -> dict:
    """The nested view the site draws: profile -> level -> statement -> details, levels bottom to top."""
    return {"id": p.get("id"), "children": [
        {"level": lv["id"], "name": lv["name"], "question": lv["question"], "definition": lv["definition"],
         "children": [{"id": st["id"], "text": st["text"],
                       "children": [{"kind": d["kind"], "text": d["text"]} for d in st.get("details", [])]}
                      for st in (p.get("levels", {}).get(lv["id"], {}).get("statements", []))],
         "current": [it["text"] for it in (p.get("current") or {}).get(lv["id"], [])],
         "desired": [it["text"] for it in (p.get("desired") or {}).get(lv["id"], [])]}
        for lv in LEVELS]}


def example() -> dict:
    """An invented, illustrative profile (spec/PERSONLAB.md §4): not from any dataset or person."""
    text = ("I work long shifts at a small bakery in the city. I start at five in the morning. I keep saying yes to "
            "extra hours. I know how to plan a week, but I never plan rest. I believe resting is lazy. I am the one "
            "my family relies on. I want my children to see that work can be calm.")

    def s(fragment):
        i = text.index(fragment)
        return {"doc": "illustrative-1", "span": [i, i + len(fragment)]}
    return {
        "id": "illustrative-1", "source_dataset": "invented for illustration", "licence": "CC BY 4.0",
        "document_id": "illustrative-1", "builder": "hand-written example", "created": "2026-11-17",
        "levels": {
            "environment": {"statements": [{"id": "e1", "text": "I work long shifts at a small bakery",
                                            "source": s("I work long shifts at a small bakery"),
                                            "details": [{"kind": "where", "text": "in the city", "source": s("in the city")},
                                                        {"kind": "when", "text": "from five in the morning",
                                                         "source": s("I start at five in the morning")}]}]},
            "behaviour": {"statements": [{"id": "b1", "text": "I keep saying yes to extra hours",
                                          "source": s("I keep saying yes to extra hours")}]},
            "skills": {"statements": [{"id": "k1", "text": "I know how to plan a week",
                                       "source": s("I know how to plan a week")}]},
            "beliefs": {"statements": [{"id": "v1", "text": "Resting is lazy", "source": s("I believe resting is lazy")}]},
            "identity": {"statements": [{"id": "i1", "text": "I am the one my family relies on",
                                         "source": s("I am the one my family relies on")}]},
            "mission": {"statements": [{"id": "m1", "text": "My children see that work can be calm",
                                        "source": s("I want my children to see that work can be calm")}]},
        },
        "current": {"behaviour": [{"text": "Says yes to every extra hour", "node": "b1",
                                   "source": s("I keep saying yes to extra hours")}],
                    "skills": [{"text": "Never plans rest", "node": "k1", "source": s("but I never plan rest")}]},
        "desired": {"skills": [{"text": "Plans rest into the week", "node": "k1", "source": s("I know how to plan a week")}],
                    "mission": [{"text": "Shows the children calm work", "node": "m1",
                                 "source": s("I want my children to see that work can be calm")}]},
        "signals": [{"kind": "load", "text": "long shifts and extra hours",
                     "source": s("I keep saying yes to extra hours")}],
    }
