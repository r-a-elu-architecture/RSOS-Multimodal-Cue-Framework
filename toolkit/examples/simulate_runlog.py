"""Synthetic RSOS run logs, for trying the cue engine before real data exists.

Everything here is invented. People belong to hidden response types that differ in which program,
tier and voice help them, and how that depends on the trigger channel. The output has the exact
columns of the protocol player's CSV export, so real logs can replace it without code changes.
"""
import numpy as np
import pandas as pd

PROTOCOLS = ["override", "swish", "interrupt_only"]
TIERS = ["LION", "EAGLE", "BEAR"]
VOICES = ["own", "computer"]
TRIGGERS = ["V", "A", "O", "memory"]

# Hidden response types: benefit (in rating points) added for each choice. Invented for illustration.
TYPES = [
    {"protocol": {"override": 2.0, "swish": 0.5, "interrupt_only": 0.8}, "tier": {"LION": 1.0, "EAGLE": 0.2, "BEAR": 0.4},
     "voice": {"own": 1.2, "computer": 0.0}, "trigger": {"V": 0.0, "A": 0.2, "O": 0.5, "memory": -0.3}},
    {"protocol": {"override": 0.8, "swish": 2.2, "interrupt_only": 0.4}, "tier": {"LION": 0.2, "EAGLE": 1.1, "BEAR": 0.3},
     "voice": {"own": 0.3, "computer": 0.4}, "trigger": {"V": 0.8, "A": -0.2, "O": 0.0, "memory": 0.4}},
    {"protocol": {"override": 1.0, "swish": 0.2, "interrupt_only": 1.9}, "tier": {"LION": 0.3, "EAGLE": 0.1, "BEAR": 1.2},
     "voice": {"own": 0.9, "computer": 0.1}, "trigger": {"V": -0.2, "A": 0.6, "O": 0.2, "memory": 0.7}},
]
# Interaction: swish works best for visual triggers, interrupt_only for memories.
SPECIAL = {("swish", "V"): 1.0, ("interrupt_only", "memory"): 0.8, ("override", "O"): 0.6}


def benefit(t, protocol, tier, voice, trigger):
    return (t["protocol"][protocol] + t["tier"][tier] + t["voice"][voice] + t["trigger"][trigger]
            + SPECIAL.get((protocol, trigger), 0.0))


def simulate(n_people=60, runs=(20, 40), seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for p in range(n_people):
        k = int(rng.integers(len(TYPES))); t = TYPES[k]
        for r in range(int(rng.integers(*runs))):
            proto, tier, voice, trig = (rng.choice(PROTOCOLS), rng.choice(TIERS), rng.choice(VOICES), rng.choice(TRIGGERS))
            rows.append(row(p, r, k, proto, tier, voice, trig, benefit(t, proto, tier, voice, trig), rng))
    return pd.DataFrame(rows)


def row(p, r, k, proto, tier, voice, trig, b, rng):
    gain = b + rng.normal(0, 1.0)
    sud0 = int(rng.integers(5, 9)); ag0 = int(rng.integers(2, 6))
    return {"timestamp": 1_800_000_000 + r * 3600, "participant": f"p{p:03d}", "protocol": proto, "trigger": "self",
            "trigger_channel": trig, "trigger_note": "", "sud_before": sud0, "sud_after": int(np.clip(round(sud0 - gain / 2), 0, 10)),
            "agency_before": ag0, "agency_after": int(np.clip(round(ag0 + gain / 2), 0, 10)), "latency_s": "",
            "completed": 1, "stopped_at_phase": "", "tier": tier, "voice": voice, "type": k}
