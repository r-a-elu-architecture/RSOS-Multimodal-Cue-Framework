"""A formal learning model of the Override Protocol, for generating testable predictions.

Two processes are modelled separately, because they are different things:

1. **Valence (Pavlovian), Rescorla-Wagner (1972).** On each run every cue that is
   present (the trigger and the tier's channel cues) changes its associative
   strength V by  dV_i = alpha_i * beta * (lam - sum_j V_j),  summing over the cues
   present. The outcome lam is the agency state the routine produces (+1).
   The trigger starts negative (it currently predicts distress).

2. **Habit (stimulus-response automaticity).** Each completed run in the presence
   of a trigger strengthens the trigger -> routine link:  h <- h + eta * (1 - h),
   the asymptotic curve used for habit formation (Lally et al., 2010).
   Latency from trigger to "I move, I act" falls with h.

Everything here is a model: parameters are assumptions, not measurements. The
point is to make the protocol's claims precise enough to be tested and possibly
refuted (spec/OVERRIDE_PROTOCOL.md section 10).
"""
from __future__ import annotations

from dataclasses import dataclass

# Assumed per-channel saliences (alpha). Change them; the predictions are reported
# across a sweep in model/PREDICTIONS.md, not for one setting.
DEFAULT_ALPHA = {"V": 0.30, "A": 0.25, "K": 0.30, "O": 0.35, "G": 0.20, "trigger": 0.30}


@dataclass
class RWModel:
    alpha: dict
    beta: float = 0.5
    lam: float = 1.0

    def run(self, V: dict, present: list[str]) -> float:
        """One reinforced trial with the listed cues present. Updates V in place;
        returns the prediction error before the update."""
        total = sum(V.get(c, 0.0) for c in present)
        err = self.lam - total
        for c in present:
            V[c] = V.get(c, 0.0) + self.alpha[c] * self.beta * err
        return err


def acquisition(channels: list[str], trials: int, alpha: dict | None = None, beta: float = 0.5) -> list[dict]:
    """Stage A: practise the bundle alone (no trigger). Returns per-trial records with
    the compound strength (sum V) and the strength of the weakest single channel."""
    m = RWModel(alpha or DEFAULT_ALPHA, beta)
    V = {c: 0.0 for c in channels}
    out = []
    for n in range(1, trials + 1):
        m.run(V, channels)
        out.append({"trial": n, "compound": sum(V.values()),
                    "single_min": min(V.values()), "single_max": max(V.values()), **{f"V_{c}": V[c] for c in channels}})
    return out


def trials_to(series: list[dict], key: str, level: float) -> int | None:
    for r in series:
        if r[key] >= level:
            return r["trial"]
    return None


def counterconditioning(channels: list[str], pretrain: int, pairings: int, v_trigger0: float = -0.8,
                        alpha: dict | None = None, beta: float = 0.5) -> list[dict]:
    """Stage A (``pretrain`` bundle-only runs) then stage B (``pairings`` runs in which the
    trigger is present together with the bundle). Tracks the trigger's own valence."""
    m = RWModel(alpha or DEFAULT_ALPHA, beta)
    V = {c: 0.0 for c in channels}
    for _ in range(pretrain):
        m.run(V, channels)
    V["trigger"] = v_trigger0
    out = []
    for n in range(1, pairings + 1):
        m.run(V, channels + ["trigger"])
        out.append({"pairing": n, "V_trigger": V["trigger"], "compound": sum(V[c] for c in channels)})
    return out


def habit(runs: int, eta: float = 0.035, latency_max_s: float = 20.0, latency_min_s: float = 1.0) -> list[dict]:
    """Automaticity h and predicted latency after each trigger-paired run."""
    h, out = 0.0, []
    for n in range(1, runs + 1):
        h += eta * (1.0 - h)
        out.append({"run": n, "automaticity": h, "latency_s": latency_min_s + (latency_max_s - latency_min_s) * (1 - h)})
    return out
