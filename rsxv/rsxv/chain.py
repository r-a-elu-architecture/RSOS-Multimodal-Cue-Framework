"""Sessions over time: the subject store, the Resonance Audit Log, the
Multi-Session Continuity and Temporal Symmetry laws, Emergency Purge, and the
chain metrics ECR and SEP-L.

Audit log design: every entry is hashed as H(prev_hash + content_hash). The
content can later be erased (purge) while the chain still verifies, because
the content hash stays in place of the content. A purge appends a Purge Proof
entry: subject, number of entries erased, and the hash of everything erased.
"""
from __future__ import annotations
import copy
import hashlib
import json
from . import lang as Lg, ops as O, sim as S, metrics as Mx
from .run import run, next_program

CSI_WINDOW = 3
CSI_FLOOR = 0.9


def _h(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _canon(x) -> str:
    return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


class Store:
    def __init__(self):
        self.subjects = {}        # subject -> {"history": [...], "memstack": [...]}
        self.audit = []           # hash chain

    def _append(self, kind, subject, content):
        prev = self.audit[-1]["hash"] if self.audit else "0" * 64
        ch = _h(_canon(content))
        e = {"n": len(self.audit), "kind": kind, "subject": subject, "content": content, "content_hash": ch,
             "prev": prev, "hash": _h(prev + ch)}
        self.audit.append(e)
        return e

    def record(self, subject, R, prog_text, hour):
        s = self.subjects.setdefault(subject, {"history": [], "memstack": []})
        summ = {"status": R["status"], "goal_met": R["goal_met"], "hour": hour, "outcome": R["outcome"],
                "metrics": R.get("metrics", {}), "rescues": R.get("rescues", []), "csi": R.get("csi")}
        s["history"].append(summ)
        s["memstack"].append({"layers": R["outcome"]["layers"], "end": R.get("end")})
        spill = [{"op": x["op"], "distress": x["distress"]} for x in R["audit"]["per_vector"]
                 if x["distress"] > 0.05 and O.OPS[x["op"]][0] not in ("safety",)]
        return self._append("session", subject, {**copy.deepcopy(summ), "program_hash": _h(prog_text), "spillover": spill,
                                                 "conflicts": copy.deepcopy(R["audit"]["conflicts"]), "interventions": list(R.get("interventions", []))})

    def verify(self) -> bool:
        prev = "0" * 64
        for e in self.audit:
            if e["content"] is not None and _h(_canon(e["content"])) != e["content_hash"]:
                return False
            if e["prev"] != prev or _h(prev + e["content_hash"]) != e["hash"]:
                return False
            prev = e["hash"]
        return True

    def purge(self, subject, now="") -> dict:
        """Emergency Purge: erase the subject's history, memory states and audit contents; return the Purge Proof."""
        erased = [e for e in self.audit if e["subject"] == subject and e["content"] is not None]
        digest = _h("".join(e["content_hash"] for e in erased) + _canon(self.subjects.get(subject, {})))
        for e in erased:
            e["content"] = None
        self.subjects.pop(subject, None)
        proof = {"subject": subject, "entries_erased": len(erased), "erased_digest": digest, "time": now}
        e = self._append("purge-proof", subject, proof)
        return {**proof, "proof_hash": e["hash"]}


def _end_state(R):
    return {k: R["base"][k] + R["outcome"][k] for k in ("agency", "distress", "arousal", "drift")}


def _csi(R):
    """Continuity Stability Index for one session: agency gained minus distress added, 0 if not completed."""
    if R["status"] != "done":
        return 0.0
    return round(R["outcome"]["agency"] - R["outcome"]["distress"], 3)


def _boost(prog):
    """Booster after a continuity breach: repeat the settle phase right after the gate, with a longer minimum."""
    q = copy.deepcopy(prog)
    settle = next((b for b in q["blocks"] if b["kind"] == "PHASE" and b["name"].startswith("settle")), None)
    if settle and not any(b["name"] == "settle_boost" for b in q["blocks"]):
        boost = {**copy.deepcopy(settle), "name": "settle_boost", "min_s": int(settle.get("min_s", 0) * 1.5) or 30, "if": None, "else": None}
        ks = {v["k"] for b in q["blocks"] for v in b["vectors"]}; nk = max(ks) + 1
        for v in boost["vectors"]:
            v["k"] = nk; nk += 1
        q["blocks"].insert(1, boost)
    return Lg.parse(Lg.to_text(q))


def run_chain(prog, person, hours, ctx=None, store=None, adaptive=True, subject=None, reschedule=True, world=None,
              start_ts=1_800_000_000, gap_s=86400):
    """world: the person's subsystem state (rsxv.subsystems.new_world()); when given, CONTAIN gates every
    session, MEMSTACK keeps the run log and CM1 compresses it."""
    """Run one session per entry in `hours`, carrying state over and applying the session laws."""
    ctx = dict(ctx or {})
    store = store or Store()
    subject = subject or f"P{person['id']}"
    laws = set(prog["laws"])
    p = dict(person)
    cur = prog
    out = []
    for i, h in enumerate(hours):
        hist = store.subjects.get(subject, {}).get("history", [])
        ts = start_ts + i * gap_s
        if world is not None:
            ctx = {**ctx, "world": world, "now": ts}
        R = run(cur, p, {**ctx, "seed": ctx.get("seed", 1) * 100 + i, "hour": h, "history": hist})
        if reschedule and R["status"] == "refused" and R.get("reschedule_to") is not None:
            moved = R["reschedule_to"]
            R = run(cur, p, {**ctx, "seed": ctx.get("seed", 1) * 100 + i, "hour": moved, "history": hist})
            R["log"].insert(0, f"TemporalSymmetry: moved from {h}:00 to {moved}:00")
            h = moved
        R["session"] = i + 1; R["hour"] = h
        R["start"] = {k: p["base"][k] for k in ("agency", "distress", "arousal", "drift")}
        R["end"] = _end_state(R)
        R["csi"] = _csi(R)
        if world is not None:
            from . import subsystems as SS
            if cur["archetype"] and any(v["op"] == "MemoryRecall" for b in cur["blocks"] for v in b["vectors"]):
                R["memstack_recall"] = SS.recall(world, cur["archetype"])
            R["subsystems"] = SS.after_session(cur, R, world, subject, ts)
        R["interventions"] = []
        prev = [x["csi"] for x in hist if x.get("csi") is not None and x["status"] != "refused"][-CSI_WINDOW:]
        breach = "MultiSessionContinuity" in laws and R["status"] != "refused" and prev and R["csi"] < CSI_FLOOR * max(prev)
        if breach:
            R["interventions"].append(f"continuity breach: CSI {R['csi']} < {CSI_FLOOR} × best of last {len(prev)} ({max(prev)}); settle booster added")
        if "ResonanceAudit" in laws:
            store.record(subject, R, Lg.to_text(cur), h)
        else:
            store.subjects.setdefault(subject, {"history": [], "memstack": []})["history"].append(
                {"status": R["status"], "goal_met": R["goal_met"], "hour": h, "csi": R["csi"]})
        out.append(R)
        if R["status"] != "refused":
            p = S.carry(p, R["end"])
        nxt = cur
        if adaptive and R["status"] != "refused":
            nxt = next_program(cur, R)["program"]
        if breach:
            nxt = _boost(nxt)
        cur = nxt
    cm = Mx.chain_metrics(out)
    return {"sessions": out, "metrics": cm, "store": store, "final_program": Lg.to_text(cur)}
