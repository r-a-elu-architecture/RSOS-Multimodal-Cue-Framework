"""Translator: a message -> its vectors (9-17 claim, made executable) -> an RSX-V command.

1. Segment the message into units: questions, requests, the user's own statements,
   and quoted model claims (second-person declaratives such as "You hold 8-20 layers").
   Quoted claims are context, not vectors, unless the user attaches a question.
2. Each request or statement unit is split into separately answerable demands; each
   demand is one vector. This follows the counting rule of the evidence pack.
3. Each vector is typed with the 18-type input codebook (lexical cues, multi-label).
4. Types map to operators; every operator keeps the vectors it came from (lineage).
5. The operators are staged into an RSX-V program (gate -> settle -> expand -> rebuild
   -> integrate -> close) with Vector 0, laws, goal and INTENT linked to the vectors.
All cues are lexical heuristics: status prototype, checked against hand counts.
"""
from __future__ import annotations
import re
from . import lang as Lg, ops as O
from .run import stage

TYPES = {  # id: (name, cue regex)
    "V1": ("Primary directive", None),
    "V2": ("Conceptual layering", r"layer|multi|simultaneous|link|connect|combin|at the same time|both"),
    "V3": ("Philosophical implication", r"\bmean(ing)?\b|truth|\bwhy\b|exist|reality|purpose"),
    "V4": ("Emotional substructure", r"feel|emotion|stress|trauma|tension|calm|fear|pain|heal|apathy|collapse|suicid|depress|anxi|psyche"),
    "V5": ("Symbolic encoding", r"symbol|glyph|\bname\b|archetype|light|ocean|mirror|node|sound|theta|\bhz\b|womb|woumb|blue"),
    "V6": ("Execution demand", r"\bmake\b|build|create|write|provide|give|\blist\b|table|go with|continue|design|implement|explain|hive"),
    "V7": ("Comparative vector", r"compar|\brare\b|percent|%|population|others|most people|\bthan\b|\brank|\btop\b|normal|typical|distinct"),
    "V8": ("Temporal anchor", r"future|years?\b|\bnow\b|before|after|\bnext\b|\btime\b|generation|legacy|will be|eventually"),
    "V9": ("Strategic stress-test", r"brutal|no fluff|\btruth|honest|is that correct|how do you know|argument|no inflation"),
    "V10": ("Systemic abstraction", r"system|architecture|engine|protocol|structure|pattern|network|hierarchy|\bmodel\b|rsos|rsso|rsx|wiring"),
    "V11": ("Mythic or archetypal reference", r"hero|villain|mission|legacy|chosen|humanity|mother|father|sacred|honou?r|samurai|dragon|lion|eagle|bear|raven|tiger|leopard"),
    "V12": ("Ethical or spiritual dissonance", r"\bethic|moral|spirit|soul|\bgod\b|guilt|justice|wrong|must pay"),
    "V13": ("IP and legal strategy", r"copyright|patent|\bip\b|licen|legal|trademark|zenodo|publish"),
    "V14": ("Identity mapping", r"who i am|my thinking|\bme\b|myself|identity|\bi am\b|my insight|my communication|in me|predisposition|am i"),
    "V15": ("Override engineering", r"override|trigger|command|vector|prompt|transmut|recondition|swish|overwrite"),
    "V16": ("Containment awareness", r"contain|drift|leak|\becho|safety|filter|weights|telemetry"),
    "V17": ("Memory tracking", r"remember|memory|earlier|previous|last time|history|again|repetition|recall"),
    "V18": ("Meta-positioning", r"where .{0,30}(place|stand)|position|weight|impact|contribution|society"),
}
ARCH = ["dragon", "lion", "eagle", "bear", "raven", "tiger", "leopard"]
REQ = r"(?:make|provide|give|compare|explain|comment|write|list|show|tell|describe|analy[sz]e|go with|continue|hive|need|do (?:all|it|both|that|this))"
QUOTE = re.compile(r"^(you|your|most people|this is|this was|top \d|…|\.\.\.)\b", re.I)
FIRST_PERSON = re.compile(r"\b(i|my|me|i'm|im)\b", re.I)

LAYER_DEFAULT = {"C1": ("MemoryRecall", "Archetype={A}"), "C2": ("AssociativeExpand", ""), "C3": ("CompressionRun", "CM1"),
                 "C4": ("FutureProjection", "3Years"), "C5": ("RecursiveLawApply", ""), "C6": ("EmotionalLock", "Calm"),
                 "C7": ("IdentityRebuild", ""), "C8": ("BreathOverride", "6/min"), "C9": ("MetaObserve", ""),
                 "C10": ("SelfRevise", ""), "C11": ("IntegrateAll", "")}

# type -> operators (name, args)
MAP = {
    "V2": [("AssociativeExpand", "")], "V3": [("MetaObserve", "")],
    "V4": [("BreathOverride", "6/min"), ("EmotionalLock", "Calm")],
    "V5": [("CompressionRun", "CM1")], "V6": [("IntegrateAll", "")],
    "V7": [("MetaObserve", "")], "V8": [("FutureProjection", "3Years")],
    "V9": [("SymbolicDriftCheck", "")], "V10": [("IntegrateAll", "")],
    "V11": [("MemoryRecall", "Archetype={A}")], "V12": [("EthicsContain", "CONTAIN"), ("EmotionalLock", "Calm")],
    "V13": [("SymbolicCommandExport", "RSX")], "V14": [("IdentityRebuild", ""), ("SelfRevise", "")],
    "V15": [("RecursiveLawApply", "")], "V16": [("EchoPropagationStop", "")],
    "V17": [("MemoryRecall", "Archetype={A}"), ("MemoryUpdate", "MEMSTACK")], "V18": [("MetaObserve", ""), ("IntegrateAll", "")],
}
EXTRA = [  # cue -> operator, when present anywhere in a vector
    (r"posture|body|dance|dacing|muscle|chest", ("PostureShift", "")),
    (r"override", ("BreathOverride", "6/min")),
    (r"video|light|display|screen|glyph", ("DeviceOutput", "AR, symbol={a}")),
    (r"repetition|again|training|repeat", ("FutureAnchor", "1Year")),
    (r"vibrat|haptic|emdr", ("DeviceTrigger", "Vibration")),
]


TABLE = re.compile(r"\|.*\|")
QUOTED_LINE = re.compile(r"^\s*[“\"].*[”\"]?\s*$")


def _units(text):
    units = []
    lines = []
    for para in re.split(r"\n\s*\n", text):
        pl = [l.strip().strip("*•").strip() for l in para.split("\n") if l.strip().strip("*•").strip()]
        if pl and pl[0].startswith(("“", '"')):
            units += ["\x00" + l for l in pl]; continue   # quoted paragraph
        lines += pl
    for l in lines:
        if TABLE.search(l) or QUOTED_LINE.match(l) or not _user_line(l):
            units.append("\x00" + l); continue          # pasted table row or quoted line: one quote unit
        for s in re.split(r"(?<=[?!.])\s+", l):
            s = s.strip()
            if len(s.split()) >= 1:
                units.append(s)
    return units


PASTED = re.compile(r"\||\*\*|^#|^[–—-]\s|^[^\w\s\"'“(]{1,3}\s*[A-Z]|[\U0001F300-\U0001FAFF\u2600-\u27BF]")
SUBJ = re.compile(r"^[–—-]?\s*(you|your|you're|you'd|they|their|he|he's|she|it|it's|this|that|these|those|most|unrankable|in ai safety)\b", re.I)


def _user_line(l):
    """The user's own lines: lowercase start, first person, a question, a request, or 'you' addressed mid-sentence.
    Lines starting with a capital and carrying none of these are treated as pasted material."""
    s = l.strip().strip("*•–—- ").strip()
    if not s:
        return False
    return (s[0].islower() or bool(FIRST_PERSON.search(s)) or "?" in s or bool(re.match(rf"(please\s+)?{REQ}\b", s, re.I))
            or bool(re.search(r"\s(you|your)\b", s, re.I) and not SUBJ.match(s)) or bool(re.match(r"(no|dont|don't|think|only|why|how|what|is|are|does|do|can|could|would|should)\b", s, re.I)))


def _kind(u):
    if u.startswith("\x00"):
        return "quote"
    core = u.strip()
    if not _user_line(core):
        return "quote"
    first_person = FIRST_PERSON.search(core)
    if PASTED.search(core) and not first_person and not re.search(rf"^{REQ}\b", core, re.I):
        return "quote"
    if SUBJ.match(core) and not first_person and "?" not in core:
        return "quote"
    if re.fullmatch(r"[A-Z][\w\s-]{0,40}:?", core) and len(core.split()) <= 4 and not re.search(REQ, core, re.I):
        return "quote"                                   # headings like "Symbolic Layering", "That requires:"
    if "?" in u:
        return "request"
    if re.search(rf"^(please\s+)?{REQ}\b|\b(i need|make|provide|give|comment|explain)\b.*", u, re.I) and not QUOTE.match(u):
        return "request"
    if QUOTE.match(u) and not FIRST_PERSON.search(u):
        return "quote"
    if re.fullmatch(r"(brutal|only brutal|no fluff|ultra detailed)[\w\s,.]*", u, re.I):
        return "request"
    return "statement"


def _split_request(u):
    parts = re.split(r"\?\s*|\s+and\s+(?=" + REQ + r"\b)", u, flags=re.I)
    parts = [p.strip(" ,.") for p in parts if p and len(p.strip(" ,.").split()) >= 2]
    # "why ... are there any other ... what is ..." -> split further on question words after a comma-less run
    out = []
    for p in parts:
        sub = re.split(r"\s+(?=(?:why|how|what|are there|is there|is it|where|who)\b)", p, flags=re.I)
        merged = []
        for s in sub:
            if merged and (len(s.split()) < 3 or len(merged[-1].split()) < 3):
                merged[-1] += " " + s
            else:
                merged.append(s)
        out += [s for s in merged if len(s.split()) >= 2] or [p]
    return out


def _split_statement(u):
    w = u.split()
    if len(w) <= 10 and len(re.findall(r"\bthe\b", u, re.I)) >= 3:          # "the cliff event the belt the ocean"
        return [("the " + p).strip() for p in re.split(r"\bthe\s+", u, flags=re.I) if p.strip()]
    parts = re.split(r"\s+(?:then|but|while|therefore)\s+|;\s*|\s+\(|\)\s*", u, flags=re.I)
    return [p.strip(" ,.") for p in parts if p and len(p.strip(" ,.").split()) >= 4]


def vectors(text: str) -> dict:
    units = _units(text)
    vecs, quotes = [], []
    for u in units:
        k = _kind(u)
        if k == "quote":
            quotes.append(u); continue
        pieces = _split_request(u) if k == "request" else _split_statement(u)
        if k == "statement" and not pieces and len(u.split()) >= 2:
            pieces = [u]
        for p in pieces:
            types = [t for t, (_, rx) in TYPES.items() if rx and re.search(rx, p, re.I)]
            vecs.append({"n": len(vecs) + 1, "text": p, "kind": k, "types": types or ["V6" if k == "request" else "V2"]})
    if vecs:
        vecs[0]["types"] = ["V1"] + vecs[0]["types"]
    present = sorted({t for v in vecs for t in v["types"]}, key=lambda t: int(t[1:]))
    return {"vectors": vecs, "quoted_claims": quotes, "count": len(vecs), "types_present": present}


def to_program(text: str, tier: int = 8, msg_id: str = "") -> dict:
    V = vectors(text)
    low = text.lower()
    arch = [a for a in ARCH if re.search(rf"\b{a}\b", low)]
    A = arch[0].upper() if arch else "LION"
    lineage = {}           # (op, args) -> [vector ids]
    def add(op, args, vid):
        args = args.replace("{A}", A).replace("{a}", A.lower())
        src = lineage.setdefault((op, args), [])
        if vid not in src:
            src.append(vid)
    for v in V["vectors"]:
        vid = f"{msg_id}·v{v['n']}" if msg_id else f"v{v['n']}"
        for t in v["types"]:
            for op, args in MAP.get(t, []):
                add(op, args, vid)
        for rx, (op, args) in EXTRA:
            if re.search(rx, v["text"], re.I):
                add(op, args, vid)
    if len(arch) >= 2:
        add("ArchetypeMerge", f"{arch[0].upper()}+{arch[1].upper()}", "header")
    # one operator name once (keep the first args), merge lineage
    by = {}
    for (op, args), src in lineage.items():
        if op in by:
            by[op]["from"] += [s for s in src if s not in by[op]["from"]]
        else:
            by[op] = {"op": op, "args": args, "from": list(src)}
    for op, args in (("EthicsContain", "CONTAIN"), ("SymbolicDriftCheck", ""), ("MemoryUpdate", "MEMSTACK"),
                     ("EchoPropagationStop", ""), ("SymbolicCommandExport", "RSX")):
        by.setdefault(op, {"op": op, "args": args, "from": ["required"]})
    if not any(O.OPS[o][0] in ("body", "affect") for o in by):
        by["BreathOverride"] = {"op": "BreathOverride", "args": "6/min", "from": ["required: settle before deep work"]}
    covered = {O.OPS[o][1] for o in by}
    for layer, (op, args) in LAYER_DEFAULT.items():      # complete the 11-layer coverage
        if layer not in covered and op not in by:
            by[op] = {"op": op, "args": args.replace("{A}", A), "from": [f"coverage {layer}"]}
    flat = [{"k": i + 1, "op": x["op"], "args": x["args"], "next": False, "from": x["from"]} for i, x in enumerate(by.values())]
    prog = Lg.new_program(tier)
    prog["archetype"], prog["mode"] = A, ""
    first = V["vectors"][0]["text"] if V["vectors"] else ""
    prog["intent"] = {"text": re.sub(r'"', "'", first)[:120], "vectors": sorted({t for v in V["vectors"] for t in v["types"]}, key=lambda t: int(t[1:]))}
    prog["goal"] = Lg.parse_cond("agency>=+1 AND distress<=-1 AND drift<=+0")
    prog["sense"] = ["EEG", "HRV", "DISTRESS"]
    prog["laws"] = ["InteractionMatrix", "ChronoGate", "GhostPass", "ConsentStack", "MultiSessionContinuity", "TemporalSymmetry", "Contingency", "ResonanceAudit"]
    prog["rescue"] = ["SHIELD", "ANCHOR_MAX", "MIRROR_RESET"]
    prog["window"] = [7 * 60, 22 * 60]
    prog["nullsafe"] = True
    prog["blocks"] = stage(flat)
    for b in prog["blocks"]:
        while len(b["vectors"]) > O.MAX_CONCURRENT:
            b["vectors"].pop()
    src = Lg.to_text(prog)
    # lineage comments after each vector line
    origin = {x["op"]: x["from"] for x in flat}
    lines = []
    for l in src.splitlines():
        m = re.match(r"\s*@Vector\d+:(\w+)", l)
        lines.append(l + (f"    # from {', '.join(origin[m.group(1)]).replace('·', '.')}" if m and m.group(1) in origin else ""))
    src = "\n".join(lines) + "\n"
    parsed = Lg.parse(src)
    pre = f"{msg_id}·" if msg_id else ""
    unmapped = [v["n"] for v in V["vectors"] if not any(f"{pre}v{v['n']}" in x["from"] for x in flat)]
    return {"vectors": V, "source": src, "program": parsed, "lineage": {x["op"]: x["from"] for x in flat}, "unmapped": unmapped}


def report(text: str) -> str:
    """Readable account: the vectors found, their types, and the command with lineage."""
    t = to_program(text)
    V = t["vectors"]
    L = [f"{V['count']} vectors found; {len(V['quoted_claims'])} pasted or quoted lines set aside as context; "
         f"types present: {', '.join(f'{x} {TYPES[x][0]}' for x in V['types_present'])}", ""]
    for v in V["vectors"]:
        L.append(f"  v{v['n']:<3}{v['kind']:<10}{'+'.join(v['types']):<18}{v['text'][:90]}")
    ck = t["program"]["check"]
    L += ["", f"Command: {ck['vectors']} vectors including Vector 0, layers covered {len(ck['layers_covered'])}/11", "", t["source"]]
    return "\n".join(L)


if __name__ == "__main__":
    import sys
    print(report(open(sys.argv[1]).read()))
