"""CM1 — the compression layer (spec/CM1.md).

Recovered role (archive, CM1_Historical_Reconstruction): higher-level symbolic compression and cross-domain pattern
distillation ("Universal Compression"); post-run compression feeding MEMSTACK; works with UGCL for glyph encoding;
the exact codec is absent. Here it is built as:

  signature(runs)            one person's practice compressed into 13 numbers: how much each kind of program helps,
                             how fast each sense starts the state, how often runs are completed
  fit(signatures, K)         a few response profiles that summarise many people (k-means, deterministic)
  describe(profile)          a profile in plain words ("scent opens the state fastest; the observer helps most")
  assign(signature, prof)    the closest profile for one person, with a confidence that grows with their runs
  suggest(signature, prof)   where to start: which kind of node, which sense to put the strongest cue on
  patterns(rows)             what repeats across everyone's runs: mean change in distress by program kind,
                             sense, glyph, vibration code, outputs and time of day, with support and interval
  pack / unpack              a person's nodes, codes, glyphs, dose and safety state in a few dozen bytes for a device

signature, assign, suggest, pack and unpack are identical in docs/js/cm1.js (tested). Until real contributions
arrive, profiles and patterns are fitted on a synthetic population with known profiles (synthetic_population), so
the method can be checked against the truth: python -m rsso.cm1 writes docs/data/cm1.json and rsso/results/cm1.md.
"""
from __future__ import annotations

import base64
import json
import math
import random

FAMILIES = ["associated", "observer", "override", "breathing", "other"]
CHANNELS = ["V", "A", "K", "O", "G", "thought", "memory"]
DIM = len(FAMILIES) + len(CHANNELS) + 1
LABELS = [f"help:{f}" for f in FAMILIES] + [f"speed:{c}" for c in CHANNELS] + ["completion"]
SHRINK = 3.0           # runs it takes for a person's own mean to count as much as the population's
CODEC_VERSION = 1


def _num(v):
    if v is None or v == "" or isinstance(v, bool):
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def r3(x: float) -> float:
    return math.floor(x * 1000 + 0.5) / 1000


def family(r: dict) -> str:
    p = str(r.get("protocol") or "")
    mode = r.get("node_mode") or ""
    if p.startswith("node_") or p.startswith("plan") or mode:
        return "observer" if (mode == "observer" or "observer" in p) else "associated"
    if p in ("override", "interrupt_only", "swish") or p.startswith("tier"):
        return "override"
    if p == "paced_breathing":
        return "breathing"
    return "other"


def signature(runs: list[dict]) -> dict:
    """{v: [13 numbers], n: [support per number]}. help:* = shrunk mean drop in distress (before - after) per kind of
    program; speed:* = shrunk share of started runs that began within 3 s, per sense; completion = share completed."""
    v, n = [], []
    for f in FAMILIES:
        xs = [_num(r.get("sud_before")) - _num(r.get("sud_after")) for r in runs
              if family(r) == f and _num(r.get("sud_before")) is not None and _num(r.get("sud_after")) is not None]
        v.append(r3(sum(xs) / (len(xs) + SHRINK)) if xs else 0.0)
        n.append(len(xs))
    for c in CHANNELS:
        ls = [_num(r.get("latency_s")) for r in runs if str(r.get("trigger_channel") or "") == c and _num(r.get("latency_s")) is not None]
        v.append(r3(sum(1 for x in ls if x <= 3) / (len(ls) + SHRINK)) if ls else 0.0)
        n.append(len(ls))
    done = [r for r in runs if str(r.get("completed")) not in ("", "None")]
    comp = [1 if str(r.get("completed")) in ("1", "1.0", "True", "true") else 0 for r in done]
    v.append(r3((sum(comp) + SHRINK * 0.9) / (len(comp) + SHRINK)) if comp else 0.9)
    n.append(len(comp))
    return {"v": v, "n": n}


def _d2(a: list[float], b: list[float], scale: list[float] | None = None) -> float:
    if scale is None:
        return sum((x - y) ** 2 for x, y in zip(a, b))
    return sum(((x - y) / s) ** 2 for x, y, s in zip(a, b, scale))


class _LCG:
    """Tiny deterministic generator (identical in JavaScript)."""
    def __init__(self, seed: int):
        self.s = seed & 0x7FFFFFFF or 1

    def next(self) -> float:
        self.s = (self.s * 48271) % 0x7FFFFFFF
        return self.s / 0x7FFFFFFF


def _kmeans(X: list[list[float]], K: int, seed: int, iters: int):
    rng = _LCG(seed)
    cents = [list(X[int(rng.next() * len(X)) % len(X)])]
    while len(cents) < K:
        d = [min(_d2(x, c) for c in cents) for x in X]
        tot = sum(d) or 1.0
        u, acc = rng.next() * tot, 0.0
        for x, w in zip(X, d):
            acc += w
            if acc >= u:
                cents.append(list(x))
                break
        else:
            cents.append(list(X[-1]))
    lab = None
    for _ in range(iters):
        new = [min(range(K), key=lambda k: (_d2(x, cents[k]), k)) for x in X]
        if new == lab:
            break
        lab = new
        for k in range(K):
            m = [x for x, l in zip(X, lab) if l == k]
            if m:
                cents[k] = [sum(col) / len(m) for col in zip(*m)]
    inertia = sum(_d2(x, cents[l]) for x, l in zip(X, lab))
    return cents, lab, inertia


def fit(signatures: list[dict], K: int = 4, seed: int = 1, iters: int = 50, restarts: int = 10) -> list[dict]:
    """k-means (k-means++ seeding, the best of several restarts) on signatures in units of their spread across people;
    profiles sorted by size."""
    raw = [s["v"] for s in signatures]
    scale = []
    for col in zip(*raw):     # every number counts in units of its spread across people
        m = sum(col) / len(col)
        sd = math.sqrt(sum((x - m) ** 2 for x in col) / len(col))
        scale.append(r3(sd) if sd > 1e-3 else 1.0)
    X = [[x / sc for x, sc in zip(v, scale)] for v in raw]
    best = None
    for r in range(restarts):
        res = _kmeans(X, K, seed + r, iters)
        if best is None or res[2] < best[2] - 1e-9:
            best = res
    cents, lab, _ = best
    sizes = [lab.count(k) for k in range(K)]
    order = sorted(range(K), key=lambda k: (-sizes[k], k))
    out = []
    for i, k in enumerate(order):
        c = [x * sc for x, sc in zip(cents[k], scale)]
        out.append({"id": f"P{i + 1}", "centroid": [r3(x) for x in c], "scale": scale, "people": sizes[k], "text": describe(c)})
    return out


FAMILY_WORDS = {"associated": "an associated node (in the body)", "observer": "the observer (nothing binds)", "override": "the Override Protocol",
                "breathing": "paced breathing", "other": "other programs"}
CHANNEL_WORDS = {"V": "something seen", "A": "a sound", "K": "a feeling in the body", "O": "a scent", "G": "a taste", "thought": "a thought", "memory": "a memory"}


def describe(c: list[float]) -> str:
    helps = c[:len(FAMILIES)]
    speed = c[len(FAMILIES):len(FAMILIES) + len(CHANNELS)]
    best = max(range(len(FAMILIES)), key=lambda i: (helps[i], -i))
    out = [f"helped most by {FAMILY_WORDS[FAMILIES[best]]}"] if helps[best] >= 0.5 else ["little change from any program yet"]
    fast = max(range(len(CHANNELS)), key=lambda i: (speed[i], -i))
    if speed[fast] >= 0.2:
        out.append(f"{CHANNEL_WORDS[CHANNELS[fast]]} starts the state fastest")
    if c[-1] < 0.75:
        out.append("often stops runs early: worth a session with a therapist")
    return "; ".join(out)


def assign(sig: dict, profiles: list[dict]) -> dict:
    """The closest profile; confidence from the distance margin and how many runs the signature rests on."""
    d = sorted(((_d2(sig["v"], p["centroid"], p.get("scale")), i) for i, p in enumerate(profiles)))
    best = profiles[d[0][1]]
    margin = (d[1][0] - d[0][0]) / (d[1][0] + d[0][0]) if len(d) > 1 and d[1][0] + d[0][0] > 0 else 1.0
    runs = sum(sig["n"][:len(FAMILIES)])
    conf = r3(margin * runs / (runs + 10))
    return {"profile": best["id"], "text": best["text"], "distance": r3(math.sqrt(d[0][0])), "confidence": conf, "runs": runs}


def suggest(sig: dict, profiles: list[dict]) -> dict:
    """Where to start. Each number is the person's own (shrunk) value blended with their profile's, by support."""
    a = assign(sig, profiles)
    cent = next(p for p in profiles if p["id"] == a["profile"])["centroid"]
    blend = []
    for i, (own, n) in enumerate(zip(sig["v"], sig["n"])):
        w = n / (n + 5.0)
        blend.append(r3(w * own + (1 - w) * cent[i]))
    helps = blend[:len(FAMILIES)]
    speed = blend[len(FAMILIES):len(FAMILIES) + len(CHANNELS)]
    fam = max(range(3), key=lambda i: (helps[i], -i))            # among node kinds and the override
    ch = max(range(5), key=lambda i: (speed[i], -i))              # among the five senses a cue can use
    rec = [f"Start with {FAMILY_WORDS[FAMILIES[fam]]}.", f"Put the strongest cue on {CHANNEL_WORDS[CHANNELS[ch]]} ({CHANNELS[ch]})."]
    if blend[-1] < 0.75:
        rec.append("Runs are often stopped early: keep them short and review the plan with a therapist.")
    return {"assign": a, "family": FAMILIES[fam], "channel": CHANNELS[ch], "values": blend, "recommendations": rec}


def _hour_bucket(h) -> str:
    h = _num(h)
    if h is None:
        return ""
    return "night" if h < 6 else "morning" if h < 12 else "afternoon" if h < 18 else "evening"


def patterns(rows: list[dict], min_n: int = 20) -> list[dict]:
    """What repeats across everyone: mean drop in distress per value of each feature, with support and a 95% interval,
    ranked by how far the value stands from the overall mean."""
    rated = [r for r in rows if _num(r.get("sud_before")) is not None and _num(r.get("sud_after")) is not None]
    if not rated:
        return []
    drop = lambda r: _num(r["sud_before"]) - _num(r["sud_after"])
    allm = sum(drop(r) for r in rated) / len(rated)
    feats = {"kind": family, "sense": lambda r: str(r.get("trigger_channel") or ""), "glyph": lambda r: str(r.get("glyph") or ""),
             "code": lambda r: str(r.get("tacton") or ""), "outputs": lambda r: str(r.get("outputs") or ""), "time": lambda r: _hour_bucket(r.get("local_hour", r.get("hour")))}
    out = []
    for name, fn in feats.items():
        groups = {}
        for r in rated:
            k = fn(r)
            if k:
                groups.setdefault(k, []).append(drop(r))
        for k, xs in sorted(groups.items()):
            if len(xs) < min_n:
                continue
            m = sum(xs) / len(xs)
            sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) if len(xs) > 1 else 0.0
            half = 1.96 * sd / math.sqrt(len(xs))
            out.append({"feature": name, "value": k, "n": len(xs), "mean_drop": r3(m), "low": r3(m - half), "high": r3(m + half),
                        "vs_all": r3(m - allm)})
    out.sort(key=lambda p: (-abs(p["vs_all"]), p["feature"], p["value"]))
    return out


# ---- the device bundle ----
SYMS = {".": 0, "-": 1, " ": 2}


def _fletcher(b: bytes) -> int:
    s1 = s2 = 0
    for x in b:
        s1 = (s1 + x) % 255
        s2 = (s2 + s1) % 255
    return (s2 << 8) | s1


def pack(plan: dict, glyph_chars: list[str], contain_state: dict | None = None, envelope: dict | None = None) -> str:
    """A person's nodes, codes, glyphs, dose and safety state as base64 (a few dozen bytes)."""
    env = envelope or {"haptic_amp_max": 0.6, "refractory_ms_min": 90000, "max_per_hour": 6, "max_per_day": 20}
    nodes = (plan or {}).get("nodes") or []
    sched = ((plan or {}).get("schedule") or [{}])[0]
    q = (contain_state or {}).get("quarantine") or {}
    out = bytearray(b"C1")
    out.append(CODEC_VERSION)
    out.append(min(len(nodes), 8))
    mask = 0
    for i, n in enumerate(nodes[:8]):
        out.append(1 if n.get("mode") == "observer" else 0)
        gi = glyph_chars.index(n["glyph"]) if n.get("glyph") in glyph_chars else 0xFFFF
        out += bytes([gi >> 8, gi & 0xFF])
        code = str(n.get("tacton") or "")[:20]
        out.append(len(code))
        bits = 0
        nb = 0
        for ch in code:
            bits = (bits << 2) | SYMS.get(ch, 0)
            nb += 2
            if nb == 8:
                out.append(bits)
                bits = nb = 0
        if nb:
            out.append(bits << (8 - nb))
        name = str(n.get("name") or "").encode("utf-8")[:16]
        out.append(len(name))
        out += name
        if ("node_" + str(n.get("key") or "").lower()) in q:
            mask |= 1 << i
    out.append(min(255, int(sched.get("per_day") or 0)))
    out.append(min(255, int(sched.get("days") or 0)))
    out.append(int(math.floor(env["haptic_amp_max"] * 100 + 0.5)))
    rs = int(env["refractory_ms_min"] // 1000)
    out += bytes([rs >> 8, rs & 0xFF, env["max_per_hour"], env["max_per_day"], mask,
                  1 if (contain_state or {}).get("escalation", {}).get("active") else 0])
    c = _fletcher(bytes(out))
    out += bytes([c >> 8, c & 0xFF])
    return base64.b64encode(bytes(out)).decode("ascii")


def unpack(b64: str, glyph_chars: list[str]) -> dict:
    b = base64.b64decode(b64)
    if b[:2] != b"C1" or b[2] != CODEC_VERSION:
        raise ValueError("not a CM1 bundle")
    if _fletcher(b[:-2]) != (b[-2] << 8 | b[-1]):
        raise ValueError("CM1 bundle checksum does not match")
    i, nodes = 4, []
    rev = {v: k for k, v in SYMS.items()}
    for _ in range(b[3]):
        mode = "observer" if b[i] else "associated"
        gi = b[i + 1] << 8 | b[i + 2]
        ln = b[i + 3]
        i += 4
        code, nbytes = "", (ln * 2 + 7) // 8
        for k in range(ln):
            byte = b[i + (k * 2) // 8]
            code += rev.get((byte >> (6 - (k * 2) % 8)) & 3, ".")
        i += nbytes
        nl = b[i]
        name = b[i + 1:i + 1 + nl].decode("utf-8", "replace")
        i += 1 + nl
        nodes.append({"name": name, "mode": mode, "glyph": glyph_chars[gi] if gi < len(glyph_chars) else "", "tacton": code})
    per_day, days, amp = b[i], b[i + 1], b[i + 2] / 100
    refr = (b[i + 3] << 8 | b[i + 4]) * 1000
    mph, mpd, mask, esc = b[i + 5], b[i + 6], b[i + 7], b[i + 8]
    for k, n in enumerate(nodes):
        n["paused"] = bool(mask >> k & 1)
    return {"nodes": nodes, "dose": {"per_day": per_day, "days": days}, "envelope": {"haptic_amp_max": amp, "refractory_ms_min": refr, "max_per_hour": mph, "max_per_day": mpd},
            "escalation": bool(esc), "bytes": len(b)}


# ---- a synthetic population with known profiles, to check CM1 against the truth ----
TRUE_PROFILES = {
    "sound-led": {"help": {"associated": 2.6, "observer": 0.6, "override": 1.8, "breathing": 1.0}, "fast": "A", "complete": 0.95},
    "scent-led": {"help": {"associated": 2.2, "observer": 0.5, "override": 1.4, "breathing": 1.2}, "fast": "O", "complete": 0.93},
    "observer-helped": {"help": {"associated": 0.6, "observer": 2.6, "override": 0.8, "breathing": 1.2}, "fast": "memory", "complete": 0.9},
    "struggling": {"help": {"associated": 0.4, "observer": 0.4, "override": 0.3, "breathing": 0.6}, "fast": "K", "complete": 0.55},
}
PROTO = {"associated": ("node_lion", "associated"), "observer": ("node_observer", "observer"), "override": ("override", ""), "breathing": ("paced_breathing", "")}


def synthetic_population(people: int = 160, runs: int = 30, seed: int = 7, hard: bool = False) -> list[dict]:
    """hard: profiles twice as close together, the fast sense less consistent and ratings noisier."""
    rng = random.Random(seed)
    p_fast, noise = (0.3, 1.6) if hard else (0.45, 1.1)
    names = list(TRUE_PROFILES)
    out = []
    for k in range(people):
        truth = names[k % len(names)]
        tp = TRUE_PROFILES[truth]
        if hard:
            mean = {f: sum(TRUE_PROFILES[t]["help"][f] for t in names) / len(names) for f in PROTO}
            tp = dict(tp, help={f: (tp["help"][f] + mean[f]) / 2 for f in PROTO}, complete=(tp["complete"] + 0.83) / 2)
        rows = []
        for j in range(runs):
            fam = rng.choice(list(PROTO))
            proto, mode = PROTO[fam]
            ch = tp["fast"] if rng.random() < p_fast else rng.choice(CHANNELS)
            lat = rng.uniform(0.5, 2.5) if ch == tp["fast"] else rng.uniform(2, 12)
            before = rng.randint(4, 9)
            after = max(0, min(10, round(before - tp["help"][fam] + rng.gauss(0, noise))))
            rows.append({"timestamp": 1_800_000_000 + j * 3600 * 5, "participant": f"s{k:03d}", "protocol": proto, "node_mode": mode,
                         "trigger_channel": ch, "latency_s": round(lat, 1), "sud_before": before, "sud_after": after,
                         "completed": 1 if rng.random() < tp["complete"] else 0, "local_hour": rng.choice([8, 13, 19, 23]),
                         "glyph": "🦁" if fam == "associated" else "∅" if fam == "observer" else "",
                         "tacton": "..-" if fam == "associated" else "-" if fam == "observer" else "", "outputs": "voice+tone+vibration"})
        out.append({"truth": truth, "runs": rows})
    return out


def evaluate(pop: list[dict], K: int = 4, first: int = 10) -> dict:
    """Fit on half the people (all their runs); assign the other half from only their first `first` runs."""
    train = [p for k, p in enumerate(pop) if (k // len(TRUE_PROFILES)) % 2 == 0]
    test = [p for k, p in enumerate(pop) if (k // len(TRUE_PROFILES)) % 2 == 1]
    prof = fit([signature(p["runs"]) for p in train], K)
    # map each fitted profile to the true profile most of its training members have
    mem = {}
    for p in train:
        a = assign(signature(p["runs"]), prof)["profile"]
        mem.setdefault(a, []).append(p["truth"])
    label = {k: max(set(v), key=lambda t: (v.count(t), t)) for k, v in mem.items()}
    hits = right_family = clear = 0
    for p in test:
        s = suggest(signature(p["runs"][:first]), prof)
        hits += label.get(s["assign"]["profile"]) == p["truth"]
        tp = TRUE_PROFILES[p["truth"]]["help"]         # the kind that truly helps most is the same in both settings
        ranked = sorted(["associated", "observer", "override"], key=lambda f: -tp[f])
        if tp[ranked[0]] - tp[ranked[1]] >= 0.5:      # only where one kind clearly helps most
            clear += 1
            right_family += s["family"] == ranked[0]
    full = sum(label.get(assign(signature(p["runs"]), prof)["profile"]) == p["truth"] for p in test)
    return {"profiles": prof, "labels": label, "people": len(pop), "test": len(test), "first_runs": first,
            "assigned_right_first": hits, "assigned_right_all": int(full), "best_kind_right_first": right_family, "with_clear_best": clear}


def main():
    from .ledger import ROOT
    pop = synthetic_population()
    ev = evaluate(pop)
    rows = [r for p in pop for r in p["runs"]]
    pats = patterns(rows)
    data = {"format": "rsos-cm1/1", "source": "synthetic population with known profiles (rsso/rsso/cm1.py synthetic_population); refit on pooled contributions",
            "labels": LABELS, "families": FAMILIES, "channels": CHANNELS, "profiles": ev["profiles"], "patterns": pats[:24]}
    (ROOT / "docs" / "data" / "cm1.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    hard = evaluate(synthetic_population(hard=True))
    t = ev["test"]
    pc = lambda a: f"{a}/{t} ({round(100 * a / t)}%)"
    lines = ["# CM1 on a synthetic population with known profiles", "",
             f"{ev['people']} virtual people from 4 true profiles ({', '.join(TRUE_PROFILES)}), 30 runs each. CM1 fits 4 profiles on half of them; "
             f"the other {t} are assigned from only their first {ev['first_runs']} runs. The hard setting puts the profiles twice as close together, "
             "makes the fastest sense less consistent and the ratings noisier.", "",
             "| | Clear profiles | Hard setting |", "|---|---|---|",
             f"| Right profile from the first {ev['first_runs']} runs | {pc(ev['assigned_right_first'])} | {pc(hard['assigned_right_first'])} |",
             f"| Right profile from all 30 runs | {pc(ev['assigned_right_all'])} | {pc(hard['assigned_right_all'])} |",
             f"| Suggests the kind of program that truly helps most, from the first {ev['first_runs']} runs (people whose profile has a clear best) | "
             f"{ev['best_kind_right_first']}/{ev['with_clear_best']} ({round(100 * ev['best_kind_right_first'] / ev['with_clear_best'])}%) | "
             f"{hard['best_kind_right_first']}/{hard['with_clear_best']} ({round(100 * hard['best_kind_right_first'] / hard['with_clear_best'])}%) |", "",
             "Profiles found (clear setting):", "",
             "| Profile | People | Matches true profile | In plain words |", "|---|---|---|---|"]
    for p in ev["profiles"]:
        lines.append(f"| {p['id']} | {p['people']} | {ev['labels'].get(p['id'], '-')} | {p['text']} |")
    lines += ["", "Top patterns across all runs (mean drop in distress, 95% interval):", "", "| Feature | Value | Runs | Mean drop | Interval | vs all |", "|---|---|---|---|---|---|"]
    for p in pats[:12]:
        lines.append(f"| {p['feature']} | {p['value']} | {p['n']} | {p['mean_drop']} | {p['low']} to {p['high']} | {p['vs_all']:+} |")
    lines += ["", "These are synthetic results: they show that the method recovers known structure, not that people respond this way."]
    (ROOT / "rsso" / "results" / "cm1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:8]))


if __name__ == "__main__":
    main()
