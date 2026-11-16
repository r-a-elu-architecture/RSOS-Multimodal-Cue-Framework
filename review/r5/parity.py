"""Review R5: Python/JS parity on adversarial inputs. python3 -I review/r5/parity.py <repo_root>"""
import json, os, subprocess, sys, random, tempfile
REPO = sys.argv[1]
sys.path.insert(0, REPO + "/rsso")
from rsso import watchdog as W, safety as S
JS = r'''
const path=require("path"), J=n=>require(path.join(process.argv[2],"docs","js",n));
const W=J("watchdog.js"), S=J("safety.js"); let s=""; process.stdin.on("data",d=>s+=d); process.stdin.on("end",()=>{const i=JSON.parse(s);
const safe=f=>{try{return f()}catch(e){return "ERR:"+e.name}};
process.stdout.write(JSON.stringify({level:i.sources.map(x=>W.levelOfProgram(x,{cues:[{id:"c1",tier:"414"},{id:"ид",tier:"414"}],edited:true})),
ev:i.checks.map(a=>safe(()=>S.eventFromCheck(a))), exit:i.states.map(st=>safe(()=>S.exit(st,"person",5))),
spine:i.texts.map(t=>S.spineFlags(t).map(f=>f.flag))}))});
'''
JSF = os.path.join(tempfile.mkdtemp(), "par.js"); open(JSF, "w").write(JS)
parts = ["PROTOCOL tier414", "PROTOCOL tıer414", "PROTOCOL TİER414", "# Tıer 414", "# Tier 414", "# ſomething Tier 420", "MODE \"obſerver\"", "MODE \"observer\"",
         "MODE\u000b\"observer\"", "MODE\f\"observer\"", "MODE \"observer\"", "PROTOCOL tier414", "PROTOCOL\ftier414", "MARK \"programmed:c1\"",
         "MARK \"programmed:ид\"", " ", " ", "\x85", "\x1c", "﻿", "\x0b", "\x0c", "\r", "\n", " ", "\t", "SAY \"ice bath\"", "\"a\\ b\"", "\"x\\\x85\"",
         "Tier 4١4", "PROTOCOL tier414٣", "PROTOCOL tier414٣", "# Tier 414٣", "# rsos-level: clinician_led", "# rsos-memory: yes", "KTier 414", "# KTier 414"]
rng = random.Random(5)
srcs = ["".join(rng.choice(parts) for _ in range(rng.randint(1, 6))) for _ in range(6000)] + parts
checks = [{"intensity": v} for v in ["7_0", "0x10", "0b111", "0o7", "1e1", " 8 ", " 8", "﻿8", "٨", "８", "Infinity", "inf", "nan", [8], [], {}, "  ", "8\n", "+8", "-0", ".5", "5.", "1_000"]]
states = [{"mode": "STABILISE", "history": None}, {"mode": "STABILISE", "history": "x"}, {"mode": "STABILISE", "history": {}}, {"mode": "CRISIS", "history": None},
          [], "NORMAL", 5, {"mode": "STABILISE"}, {"mode": "PRACTICAL_CRISIS", "history": 3}]
texts = ["ice bath", "ice bath", "ICE BATH", "ıce bath", "İce bath", "hold your breath until you faint", "hold your breath until you faint", "ſcalding", "freeẓing"]
r = subprocess.run(["node", JSF, os.path.abspath(REPO)], input=json.dumps({"sources": srcs, "checks": checks, "states": states, "texts": texts}), capture_output=True, text=True)
if r.returncode: print(r.stderr); sys.exit(1)
js = json.loads(r.stdout)
def safe(f):
    try: return f()
    except Exception as e: return "ERR:" + type(e).__name__
d = [(s, js["level"][k], W.level_of_program(s, {"cues": [{"id": "c1", "tier": "414"}, {"id": "ид", "tier": "414"}], "edited": True})) for k, s in enumerate(srcs)]
d = [x for x in d if x[1] != x[2]]
print("level diffs:", len(d), "of", len(srcs))
seen = set()
for s, a, b in d:
    key = (a["therapist_led"], b["therapist_led"], a["memory_work"], b["memory_work"], a["text"] == b["text"])
    if key in seen: continue
    seen.add(key); print(repr(s)[:140], "| JS", {k: a[k] for k in ("therapist_led", "memory_work")}, "| PY", {k: b[k] for k in ("therapist_led", "memory_work")}, "| text equal", a["text"] == b["text"])
for k, c in enumerate(checks):
    p = safe(lambda: S.event_from_check(c)); j = js["ev"][k]
    if p != j: print("eventFromCheck", repr(c), "JS", j.get("distress") if isinstance(j, dict) else j, "PY", p.get("distress") if isinstance(p, dict) else p)
for k, st in enumerate(states):
    p = safe(lambda: list(S.exit(st, "person", 5))); j = js["exit"][k]
    if p != j: print("exit", repr(st), "JS", json.dumps(j)[:120], "PY", str(p)[:120])
for k, t in enumerate(texts):
    p = [f["flag"] for f in S.spine_flags(t)]
    if p != js["spine"][k]: print("spine", repr(t), "JS", js["spine"][k], "PY", p)
