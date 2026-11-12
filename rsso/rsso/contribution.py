"""Research data contribution: one de-identified, checksummed file per person, clinician or lab (spec/DATA_CONTRIBUTION.md).

A contribution gathers what RSOS records on a device — runs, weekly automaticity checks, node plans, glyph
calibration, programmed cues — with what only people can add: outcome scales, adverse events, a clinician's
sessions and ratings, a lab's EEG/BCI recordings. Everything is filtered by the consent scopes the contributor
chose, dates become day numbers counted from the first run, ids are random, and free text is left out unless
the contributor shares it. The same file feeds the analysis kit unchanged (`to_runlog`, `pool`).

docs/js/contribution.js builds identical files (tested). Command line:

  python -m rsso.contribution check  FILE...          # schema and checksum
  python -m rsso.contribution pool   FILE... > runs.csv   # all runs of all contributions, one table
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import sys

from . import metrics as _metrics
from .memstack import _canonical

SCHEMA = "rsos-contribution/1"
CONSENT_VERSION = "rsos-data-consent/1"
ROLES = ("person", "clinician", "lab")
SCOPES = {
    "runs": "Practice runs: program, tier, glyph, code, trigger, ratings before and after, start time, completion; weekly automaticity checks; computed metrics",
    "physiology": "Heart rate and heart-rate variability before and after each run",
    "plan": "The structure of node plans and programmed cues: archetypes, modes, which senses have cues, frame scores, dose",
    "texts": "Your own words: frames, cue texts, contexts, trigger notes, clinician and lab notes",
    "calibration": "Glyph and colour choices",
    "recognition": "Results of the vibration-code recognition check",
    "outcomes": "Standard questionnaire totals over time (PHQ-9, GAD-7, PCL-5, PSS-10, WEMWBS, global change)",
    "safety": "Adverse events and stopped runs",
    "profile": "Age band, gender, handedness, world region, prior practice",
    "health": "Health information: what the plan is for, self-reported conditions, diagnosis categories",
    "clinical": "Clinician sessions and ratings",
    "lab": "Lab, device and recording descriptions (EEG, BCI, heart rate)",
}
REQUIRED = {"runs"}
KNOWN_PROTOCOLS = ("override", "interrupt_only", "swish", "legacy_tier8", "paced_breathing", "tier003_command_stack",
                   "tier012_breath_anchor", "tier014_seal", "tier016_stillness", "tier406_release", "tier579_glyph",
                   "node_lion", "node_observer")
RUN_CORE = ("program_kind", "program_hash", "trigger", "trigger_channel", "sud_before", "sud_after", "agency_before",
            "agency_after", "latency_s", "completed", "stopped_at_phase", "tier", "voice", "outputs", "inhale_s",
            "exhale_s", "glyph", "tacton", "node_mode", "duration_s", "planned_s")
RUN_NUM = {"sud_before", "sud_after", "agency_before", "agency_after", "latency_s", "completed", "inhale_s",
           "exhale_s", "duration_s", "planned_s", "hr_before", "hr_after", "rmssd_before", "rmssd_after"}
RUN_PHYS = ("hr_before", "hr_after", "rmssd_before", "rmssd_after", "hr_source")
SCALES = {"PHQ9": (0, 27), "GAD7": (0, 21), "PCL5": (0, 80), "PSS10": (0, 40), "WEMWBS": (14, 70), "PGIC": (1, 7), "SUDS": (0, 10)}
SEVERITY = ("mild", "moderate", "serious")
RELATED = ("unrelated", "unlikely", "possible", "likely")
AGE_BANDS = ("18-24", "25-34", "35-44", "45-54", "55-64", "65+")
GENDERS = ("woman", "man", "non-binary", "another", "prefer not to say")
HANDS = ("right", "left", "both")
REGIONS = ("Africa", "Asia", "Europe", "Latin America and Caribbean", "Middle East", "North America", "Oceania")
PRACTICES = ("meditation", "breathwork", "hypnosis", "nlp", "psychotherapy", "neurofeedback", "martial arts", "music")
LEVELS = ("none", "some", "regular")
CONDITIONS = ("ptsd", "depression", "anxiety", "chronic_stress", "adhd", "insomnia", "chronic_pain", "addiction", "other")
DAY = 86400


def num(v):
    """'' and None -> None; numbers and numeric text -> number (whole numbers as int)."""
    if v is None or v == "" or isinstance(v, bool):
        return None if not isinstance(v, bool) else int(v)
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(x):
        return None
    return int(x) if x == int(x) else x


def pick(d: dict, keys, allowed=None):
    out = {}
    for k in keys:
        v = d.get(k)
        if v is None or v == "" or (allowed and k in allowed and v not in allowed[k]):
            continue
        out[k] = v
    return out


def fnv1a(text: str) -> str:
    """32-bit FNV-1a of UTF-8 text, 8 hex digits (identical in JavaScript): a short program fingerprint."""
    h = 0x811C9DC5
    for b in text.encode("utf-8"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return f"{h:08x}"


def _day(ts, t0):
    t = num(ts)
    return None if t is None or t0 is None else int(math.floor((t - t0) / DAY))


def _runs(raw: list[dict], scopes: set, t0):
    out = []
    for r in sorted(raw, key=lambda r: num(r.get("timestamp")) or 0):
        x = {"day": _day(r.get("timestamp"), t0)}
        for k in ("local_hour", "weekday"):
            if num(r.get(k)) is not None:
                x["hour" if k == "local_hour" else k] = num(r.get(k))
        proto = str(r.get("protocol") or "")
        x["protocol"] = proto if (proto in KNOWN_PROTOCOLS or "texts" in scopes) else "custom"
        for k in RUN_CORE + (RUN_PHYS if "physiology" in scopes else ()):
            v = r.get(k)
            v = num(v) if k in RUN_NUM else (None if v in (None, "") else str(v))
            if v is not None:
                x[k] = v
        if "texts" in scopes and r.get("trigger_note"):
            x["trigger_note"] = str(r["trigger_note"])
        if "sud_before" in x and "sud_after" in x:
            x["sud_change"] = num(x["sud_after"] - x["sud_before"])
        if "agency_before" in x and "agency_after" in x:
            x["agency_change"] = num(x["agency_after"] - x["agency_before"])
        out.append(x)
    return out


def _plan(plan: dict | None, scopes: set):
    if not plan or not plan.get("nodes"):
        return None
    texts, intake = "texts" in scopes, plan.get("intake") or {}
    raw_nodes = intake.get("nodes") or []
    nodes = []
    for i, n in enumerate(plan["nodes"]):
        ch = n.get("channels") or {}
        raw = raw_nodes[i] if i < len(raw_nodes) else {}
        x = {"archetype": n.get("archetype") or "own", "mode": n.get("mode"), "tacton": n.get("tacton"), "glyph": n.get("glyph") or None,
             "senses": {k: bool(raw.get(k)) for k in "VAKOG"}, "frames": len(n.get("frames") or []),
             "contexts": len(n.get("contexts") or []), "rules": len(n.get("rules") or []),
             "frame_checks": [{"score": f.get("score"), "scope": f.get("scope"), "kind": f.get("kind"), "flags": list(f.get("flags") or [])}
                              for f in n.get("frame_checks") or []]}
        if num(raw.get("believability")) is not None:
            x["believability"] = num(raw.get("believability"))
        if texts:
            x.update(name=n.get("name"), state=n.get("meaning"), cues={k: v for k, v in ch.items() if v}, frame_texts=list(n.get("frames") or []),
                     context_texts=list(n.get("contexts") or []), rule_texts=list(n.get("rules") or []))
        nodes.append({k: v for k, v in x.items() if v is not None})
    sched = plan.get("schedule") or []
    first = sched[0] if sched else {}
    out = {"planner": plan.get("planner"), "author": plan.get("author"), "nodes": nodes, "tiers": list(plan.get("tiers") or []),
           "dose": {"per_day": num(first.get("per_day")), "days": num(first.get("days"))}, "approved": bool(plan.get("approved")),
           "therapist_led": bool(plan.get("therapist_led")), "devices": sorted(k for k, v in (intake.get("devices") or {}).items() if v)}
    if "health" in scopes:
        out["concerns"] = list(intake.get("concerns") or [])
        phys = intake.get("physiology") or {}
        if "physiology" in scopes and phys:
            out["baseline"] = {k: num(v) for k, v in phys.items() if num(v) is not None}
    if texts:
        out.update(symptoms=intake.get("symptoms") or "", triggers=list(intake.get("triggers") or []))
    return {k: v for k, v in out.items() if v is not None}


def _cues(cues: list[dict], scopes: set, t0):
    out = []
    for c in cues or []:
        x = {"tier": str(c.get("tier") or ""), "therapist_led": str(c.get("tier") or "") in ("414", "420", "439", "440"),
             "author": c.get("author") or "self", "revoked": c.get("revoked_ms") is not None,
             "sound": bool(c.get("sound_hz"))}
        if t0 is not None and num(c.get("created_ms")) is not None:
            x["day"] = _day(num(c["created_ms"]) / 1000, t0)
        if "texts" in scopes:
            x["content"] = c.get("content") or ""
        out.append(x)
    return out


def _calibration(ugcl: dict | None):
    if not ugcl:
        return None
    tiers = {}
    for k, v in (ugcl.get("tiers") or {}).items():
        tiers[k] = {"glyph": v.get("glyph"), "candidates": list(v.get("candidates") or []), "comparisons": v.get("comparisons") or [],
                    "scores": list(v.get("scores") or [])}
    return {"tiers": tiers, "colour": ugcl.get("colour") or None}


def _outcomes(items, t0, texts):
    out = []
    for o in items or []:
        s, total = str(o.get("scale") or "").upper(), num(o.get("total"))
        if s not in SCALES or total is None or not SCALES[s][0] <= total <= SCALES[s][1]:
            continue
        x = {"scale": s, "total": total, "rater": o.get("rater") if o.get("rater") in ("self", "clinician") else "self"}
        x["day"] = _day(o.get("ts"), t0) if t0 is not None and o.get("ts") is not None else num(o.get("day"))
        out.append(x)
    return sorted(out, key=lambda x: (x["day"] if x["day"] is not None else -10**9, x["scale"]))


def _adverse(items, t0, texts):
    out = []
    for a in items or []:
        x = pick(a, ("severity", "related"), {"severity": SEVERITY, "related": RELATED})
        x["resolved"] = bool(a.get("resolved"))
        x["day"] = _day(a.get("ts"), t0) if t0 is not None and a.get("ts") is not None else num(a.get("day"))
        if texts and a.get("text"):
            x["text"] = str(a["text"])
        out.append(x)
    return out


def _profile(p: dict | None, scopes: set):
    p = p or {}
    out = {}
    if "profile" in scopes:
        out.update(pick(p, ("age_band", "gender", "handedness", "region"),
                        {"age_band": AGE_BANDS, "gender": GENDERS, "handedness": HANDS, "region": REGIONS}))
        exp = {k: v for k, v in (p.get("experience") or {}).items() if k in PRACTICES and v in LEVELS}
        if exp:
            out["experience"] = exp
    if "health" in scopes:
        cond = sorted(c for c in p.get("conditions") or [] if c in CONDITIONS)
        if cond:
            out["conditions"] = cond
        for k in ("in_therapy", "medication_change"):
            if isinstance(p.get(k), bool):
                out[k] = p[k]
    return out or None


def _clinical(c: dict | None, scopes: set, t0):
    if not c:
        return None
    texts = "texts" in scopes
    out = pick(c, ("profession", "years_band", "setting"))
    out["modalities"] = sorted(str(m) for m in c.get("modalities") or [])
    out["client_consent"] = bool(c.get("client_consent"))
    sess = []
    for s in c.get("sessions") or []:
        x = {"day": _day(s.get("ts"), t0) if t0 is not None and s.get("ts") is not None else num(s.get("day"))}
        for k in ("minutes", "nodes_used", "fidelity", "engagement", "cgi_s", "cgi_i"):
            if num(s.get(k)) is not None:
                x[k] = num(s.get(k))
        x["therapist_led"] = bool(s.get("therapist_led"))
        if texts and s.get("notes"):
            x["notes"] = str(s["notes"])
        sess.append(x)
    out["sessions"] = sess
    if "health" in scopes and c.get("diagnoses"):
        out["diagnoses"] = sorted(str(d).strip().upper() for d in c["diagnoses"] if str(d).strip())
    return out


def _lab(lab: dict | None, scopes: set):
    if not lab:
        return None
    out = pick(lab, ("site_code", "ethics_ref", "protocol_ref"))
    dev = lab.get("device") or {}
    d = pick(dev, ("name", "kind", "reference", "montage", "ground", "transport"))
    for k in ("channels", "fs_hz", "impedance_kohm_max"):
        if num(dev.get(k)) is not None:
            d[k] = num(dev.get(k))
    out["device"] = d
    recs = []
    for r in lab.get("recordings") or []:
        x = pick(r, ("file_sha256", "bids_path", "program", "task"))
        for k in ("day", "duration_s", "clock_offset_ms", "artifact_pct", "run_index"):
            if num(r.get(k)) is not None:
                x[k] = num(r.get(k))
        recs.append(x)
    out["recordings"] = recs
    if "texts" in scopes and lab.get("notes"):
        out["notes"] = str(lab["notes"])
    return out


def build(inp: dict) -> dict:
    """Build the contribution body (without checksum). Raises ValueError when consent is missing."""
    role = inp.get("role")
    if role not in ROLES:
        raise ValueError("role must be person, clinician or lab")
    consent = inp.get("consent") or {}
    if consent.get("agreed") is not True:
        raise ValueError("a contribution needs the contributor's consent")
    scopes = {s for s in consent.get("scopes") or [] if s in SCOPES} | REQUIRED
    if role == "clinician":
        scopes.add("clinical")
        if not (inp.get("clinical") or {}).get("client_consent"):
            raise ValueError("a clinician contribution needs the client's consent")
    if role == "lab":
        scopes.add("lab")
        if not str((inp.get("lab") or {}).get("ethics_ref") or "").strip():
            raise ValueError("a lab contribution needs its ethics approval reference")
    ids = inp.get("ids") or {}
    raw = inp.get("runs") or []
    stamps = [num(r.get("timestamp")) for r in raw if num(r.get("timestamp")) is not None]
    t0 = min(stamps) if stamps else (num(inp.get("t0")))
    texts = "texts" in scopes
    runs = _runs(raw, scopes, t0)
    srbai = sorted(({"week": num(s.get("week")), "srbai": num(s.get("srbai"))} for s in inp.get("srbai") or []), key=lambda s: s["week"] or 0)
    body = {
        "schema": SCHEMA,
        "contribution_id": ids.get("contribution_id"),
        "participant": ids.get("participant"),
        "role": role,
        "consent": {"version": CONSENT_VERSION, "scopes": sorted(scopes), "sharing": consent.get("sharing") if consent.get("sharing") in ("open", "research") else "research",
                    "contact": bool(consent.get("contact")), "agreed": True},
        "app": {k: v for k, v in (inp.get("app") or {}).items() if k in ("player", "planner", "ugcl", "platform", "vibration", "schema_runs")},
        "runs": runs,
        "weekly": srbai,
        "metrics": _metrics.compute(raw, inp.get("srbai") or [], inp.get("settings") or {}, num(inp.get("now"))) if raw else {},
    }
    if "plan" in scopes:
        body["plan"] = _plan(inp.get("plan"), scopes)
        body["cues"] = _cues(inp.get("cues"), scopes, t0)
    if "calibration" in scopes:
        body["calibration"] = _calibration(inp.get("ugcl"))
    if "recognition" in scopes:
        body["recognition"] = [pick(x, ("code", "chosen", "modality")) | {"correct": bool(x.get("correct")), "rt_ms": num(x.get("rt_ms")),
                                                                         "options": list(x.get("options") or [])}
                               for x in inp.get("recognition") or []]
    if "outcomes" in scopes:
        body["outcomes"] = _outcomes(inp.get("outcomes"), t0, texts)
    if "safety" in scopes:
        body["safety"] = {"adverse": _adverse(inp.get("adverse"), t0, texts), "stopped_runs": sum(1 for r in runs if r.get("completed") == 0),
                          "runs": len(runs)}
    prof = _profile(inp.get("profile"), scopes)
    if prof:
        body["profile"] = prof
    if role == "clinician":
        body["clinical"] = _clinical(inp.get("clinical"), scopes, t0)
    if role == "lab":
        body["lab"] = _lab(inp.get("lab"), scopes)
    days = sorted({r["day"] for r in runs if r.get("day") is not None})
    rated = sum(1 for r in runs if "sud_change" in r)
    body["quality"] = {"runs": len(runs), "days_active": len(days), "span_days": (days[-1] - days[0] + 1) if days else 0,
                       "rated_share": math.floor(rated / len(runs) * 1000 + 0.5) / 1000 if runs else 0,
                       "with_physiology": sum(1 for r in runs if "hr_before" in r), "weekly_checks": len(srbai)}
    return {k: v for k, v in body.items() if v is not None}


def seal(body: dict) -> dict:
    return dict(body, sha256=hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest())


def check(c: dict) -> list[str]:
    """Problems with a contribution file; empty when it is valid and unchanged."""
    errs = []
    if c.get("schema") != SCHEMA:
        errs.append(f"schema is {c.get('schema')!r}, expected {SCHEMA}")
    body = {k: v for k, v in c.items() if k != "sha256"}
    if hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest() != c.get("sha256"):
        errs.append("checksum does not match: the file was changed or damaged")
    if c.get("role") not in ROLES:
        errs.append("unknown role")
    if not (c.get("consent") or {}).get("agreed"):
        errs.append("no consent")
    return errs


def to_runlog(c: dict) -> list[dict]:
    """The contribution's runs as run-log rows for MEMSTACK, metrics and the analysis kit (timestamps are
    relative: day × 86400 + hour × 3600, plus the run's order)."""
    rows = []
    for i, r in enumerate(c.get("runs") or []):
        ts = (r.get("day") or 0) * DAY + (r.get("hour") if r.get("hour") is not None else 12) * 3600 + i
        row = {"timestamp": ts, "participant": c.get("participant") or "", "protocol": r.get("protocol", ""),
               "trigger_note": r.get("trigger_note", "")}
        for k in RUN_CORE + RUN_PHYS:
            if k in r:
                row[k] = r[k]
        rows.append(row)
    return rows


POOL_FIELDS = ["contribution", "participant", "role", "day", "hour", "weekday", "protocol"] + list(RUN_CORE) + list(RUN_PHYS) + ["sud_change", "agency_change"]


def pool(contribs: list[dict]) -> str:
    """All runs of many contributions as one CSV table, one row per run."""
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=POOL_FIELDS, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for c in contribs:
        for r in c.get("runs") or []:
            w.writerow(dict(r, contribution=c.get("contribution_id"), participant=c.get("participant"), role=c.get("role")))
    return buf.getvalue()


def bids_events(timeline: dict) -> str:
    """BIDS events.tsv for a compiled RSX timeline, so EEG and other recordings can be aligned with every cue."""
    lines = ["onset\tduration\ttrial_type\tphase\tvalue"]
    for e in timeline["events"]:
        if e.get("tier"):
            val = e["tier"]
        elif e["channel"] == "haptic":
            val = f"on={e.get('on', 0)} off={e.get('off', 0)} x={e.get('count', 1)}"
        elif e["channel"] == "marker":
            val = str(e.get("text") or "")
        else:
            val = ""
        val = val.replace("\t", " ").replace("\n", " ") or "n/a"
        lines.append(f"{e['t'] / 1000:.3f}\t{e.get('dur', 0) / 1000:.3f}\t{e['channel']}/{e['kind']}\t{e.get('phase', '')}\t{val}")
    return "\n".join(lines) + "\n"


def main(argv=None):
    a = argv or sys.argv[1:]
    if len(a) < 2 or a[0] not in ("check", "pool"):
        print(__doc__)
        return 2
    docs = [json.load(open(p, encoding="utf-8")) for p in a[1:]]
    if a[0] == "check":
        bad = 0
        for p, c in zip(a[1:], docs):
            errs = check(c)
            bad += bool(errs)
            print(p + ": " + ("ok, " + str(len(c.get("runs") or [])) + " runs" if not errs else "; ".join(errs)))
        return 1 if bad else 0
    sys.stdout.write(pool(docs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
