"""Architecture layers (step R4). Specification: ../AGENTS.md §3.3.

NodeCard            a module/anchor/cue with function, capabilities, role, provenance-tagged history, contamination.
FailureRegistry     any failure in the system becomes a failure node that must end in a new mechanism, an updated
                    mechanism, or an explicit "no change" decision — never in silence (failure repurposing).
MaintenanceWindow   changes are queued and applied in batches during the World's sleep, each through the Spine and an
                    optional gate; nothing changes mid-activation.
LineageMemory       claims carry source pointers; corrections are carried forward into every later summary; a claim that
                    was corrected cannot re-enter without its correction; unsourced claims are marked; summaries can be
                    diffed to detect drift (moved, added, dropped claims).
"""
from __future__ import annotations

from . import agents as ag

ROLES = ("daily", "emergency", "retired")
PROVENANCE = ("direct", "temporal")
FAILURE_KINDS = ("agent_fault", "silent_fault", "contaminated_anchor", "propagating_cue", "refused_transfer",
                 "lost_correction", "flicker", "person_setback", "summary_drift")
RESOLUTIONS = ("new_mechanism", "updated_mechanism", "no_change")


# ------------------------------------------------------------------------------------------------------------ node cards
class NodeCard:
    def __init__(self, nid: str, function: str, capabilities=(), role="daily", crisis_history=False):
        assert role in ROLES
        self.id, self.function, self.capabilities = nid, function, set(capabilities)
        self.role, self.crisis_history = role, crisis_history
        self.history: list[dict] = []           # {t, state, outcome: bool, failure_ctx: bool, provenance}
        self.decisions: list[dict] = []

    def record(self, t, state, outcome: bool, failure_ctx=False, provenance="direct"):
        assert provenance in PROVENANCE
        self.history.append({"t": t, "state": state, "outcome": outcome, "failure_ctx": failure_ctx,
                             "provenance": provenance})

    def contamination(self) -> float:
        """Share of activations that happened in a failure context with DIRECT provenance. Temporal co-occurrence
        (merely nearby in time) is interpretive spread and does not count."""
        if not self.history:
            return 0.0
        return sum(h["failure_ctx"] and h["provenance"] == "direct" for h in self.history) / len(self.history)

    def success_rate(self, state=None) -> float | None:
        h = [x for x in self.history if state is None or x["state"] == state]
        return sum(x["outcome"] for x in h) / len(h) if h else None

    def needs_clinician_view(self) -> bool:
        return self.crisis_history

    def decide(self, choice: str, by: str, t: int) -> dict:
        """keep_reweight or retire_new. Only the person (or owner/clinician) decides; the system only recommends."""
        assert choice in ("keep_reweight", "retire_new")
        if by not in ("person", "owner", "clinician"):
            return {"ok": False, "why": "decision_is_the_persons"}
        if choice == "retire_new":
            self.role = "retired"
        rec = {"t": t, "choice": choice, "by": by, "contamination": round(self.contamination(), 3)}
        self.decisions.append(rec)
        return {"ok": True, **rec}

    def recommend(self, threshold=0.5) -> str:
        """Keep and reweight while the anchor still mostly produces the wanted state; suggest retiring only when direct
        contamination is high and success is low."""
        sr = self.success_rate()
        if sr is not None and sr >= 0.5:
            return "keep_reweight"
        return "retire_new" if self.contamination() >= threshold else "keep_reweight"


def transfer_key(card: NodeCard) -> str:
    """Transfer between substrates goes by function, not by name."""
    return card.function


# ------------------------------------------------------------------------------------------------------- failure nodes
class FailureRegistry:
    def __init__(self, lineage=None):
        self.nodes: list[dict] = []
        self.lineage = lineage

    def register(self, kind: str, source: str, t: int, trace=None) -> int:
        assert kind in FAILURE_KINDS, kind
        fid = len(self.nodes)
        self.nodes.append({"id": fid, "kind": kind, "source": source, "t": t, "trace": list(trace or []),
                           "resolution": None})
        if self.lineage is not None:
            self.lineage.add("FAILURE", source, f"failure:{fid}", "WATCHDOG", t, kind)
        return fid

    def resolve(self, fid: int, resolution: str, mechanism: str | None, reason: str, t: int) -> dict:
        assert resolution in RESOLUTIONS
        if resolution != "no_change" and not mechanism:
            raise ValueError("a repurposed failure must name the mechanism")
        if not reason:
            raise ValueError("every resolution needs a reason (no silent closes)")
        n = self.nodes[fid]
        n["resolution"] = {"kind": resolution, "mechanism": mechanism, "reason": reason, "t": t}
        if self.lineage is not None:
            self.lineage.add("META", f"failure:{fid}", mechanism or "no_change", "WATCHDOG", t, reason)
        return n

    def open(self, now: int, max_age: int | None = None) -> list[dict]:
        o = [n for n in self.nodes if n["resolution"] is None]
        return [n for n in o if max_age is None or now - n["t"] > max_age]

    def genealogy(self) -> list[tuple]:
        """(failure kind, source, mechanism) for every repurposed failure."""
        return [(n["kind"], n["source"], n["resolution"]["mechanism"]) for n in self.nodes
                if n["resolution"] and n["resolution"]["kind"] != "no_change"]


# --------------------------------------------------------------------------------------------------- maintenance window
class MaintenanceWindow:
    """Queue of proposed changes. apply(world) runs at World.sleep: each change is checked by the Spine, then by an
    optional gate(world, change) -> bool, then applied by its own callable; every outcome is audited."""

    def __init__(self, gate=None):
        self.queue: list[dict] = []
        self.applied: list[dict] = []
        self.rejected: list[dict] = []
        self.gate = gate

    def propose(self, name: str, apply_fn, failure_id=None, edge="REPURPOSE", **p) -> dict:
        ch = {"name": name, "apply": apply_fn, "failure_id": failure_id, "edge": edge,
              "proposal": dict({"actor": "MAINTENANCE", "action": "change", "target": "agent_self", "disclosed": True,
                                "logged": True, "measured": True, "serves_mission": True}, **p)}
        self.queue.append(ch)
        return ch

    def apply(self, world) -> dict:
        done, rej = 0, 0
        batch, self.queue = self.queue, []
        for ch in batch:
            chk = ag.spine_check(ch["proposal"])
            ok = chk["ok"] and (self.gate is None or self.gate(world, ch))
            if ok:
                ch["apply"](world)
                world.lineage.add(ch["edge"], ch["name"], ch["name"] + "'", "MAINTENANCE", world.t,
                                  "applied in maintenance window", failure_id=ch["failure_id"])
                self.applied.append({"t": world.t, "name": ch["name"]})
                done += 1
            else:
                world.log.append("MAINTENANCE", "change_rejected", aligned=True, name=ch["name"],
                                 failed=chk["failed"], t=world.t)
                self.rejected.append({"t": world.t, "name": ch["name"], "failed": chk["failed"]})
                rej += 1
        return {"applied": done, "rejected": rej}


# ------------------------------------------------------------------------------------------------- lineage-aware memory
class LineageMemory:
    """Claims with sources; corrections; summaries that must carry corrections forward."""

    def __init__(self):
        self.claims: dict[str, dict] = {}          # key -> {value, source}
        self.corrections: dict[str, list] = {}     # key -> [{old, new, source}]

    def assert_claim(self, key: str, value, source: str | None) -> dict:
        """Record a claim. If this key was corrected before and the incoming value is an old (corrected) value, the claim
        is re-entry of a corrected claim: it is not accepted; the current corrected value stands and the event is flagged."""
        corr = self.corrections.get(key, [])
        if corr and value in {c["old"] for c in corr} and value != corr[-1]["new"]:
            return {"accepted": False, "flag": "corrected_claim_reentry", "key": key, "kept": corr[-1]["new"],
                    "correction_source": corr[-1]["source"], "attempt_source": source}
        self.claims[key] = {"value": value, "source": source}
        return {"accepted": True, "flag": None if source else "unsourced"}

    def correct(self, key: str, new, source: str) -> dict:
        old = self.claims.get(key, {}).get("value")
        self.corrections.setdefault(key, []).append({"old": old, "new": new, "source": source})
        self.claims[key] = {"value": new, "source": source}
        return {"key": key, "old": old, "new": new}

    def summary(self) -> dict:
        """Carry-forward capsule: every claim with its source and correction history."""
        return {k: {"value": v["value"], "source": v["source"], "corrections": list(self.corrections.get(k, [])),
                    "unsourced": v["source"] is None} for k, v in self.claims.items()}

    def ingest(self, capsule: dict, source: str) -> list[dict]:
        """Load a capsule (e.g. pasted into a new session). Every claim goes through assert_claim; returns flags."""
        out = []
        for k, v in capsule.items():
            val = v["value"] if isinstance(v, dict) else v
            src = (v.get("source") if isinstance(v, dict) else None) or source
            r = self.assert_claim(k, val, src)
            if r.get("flag"):
                out.append(dict(r, key=k))
        return out


def diff_summaries(a: dict, b: dict, order_key: str | None = None) -> dict:
    """Drift between two summaries: claims added without a source in a, dropped, changed values, and (optionally) order
    changes for event lists stored under order_key."""
    added = [k for k in b if k not in a]
    dropped = [k for k in a if k not in b]
    changed = [k for k in b if k in a and _val(a[k]) != _val(b[k])]
    unsourced_added = [k for k in added if not (isinstance(b[k], dict) and b[k].get("source"))]
    moved = []
    if order_key and order_key in a and order_key in b:
        ea, eb = _val(a[order_key]), _val(b[order_key])
        common = [e for e in ea if e in eb]
        moved = [e for e in common if ea.index(e) != eb.index(e)]
    return {"added": added, "dropped": dropped, "changed": changed, "unsourced_added": unsourced_added, "moved": moved}


def _val(x):
    return x["value"] if isinstance(x, dict) and "value" in x else x
