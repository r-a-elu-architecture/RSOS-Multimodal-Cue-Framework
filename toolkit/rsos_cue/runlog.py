"""Bridge from the RSOS run log (protocol player / rsx RunRecord) to the cue engine.

A run-log row records one run of an RSX program. The cue engine sees it as one trial:

  glyph   <- tier       (the tier bundle used, e.g. LION)
  sound   <- voice      (own recording, computer voice, or none)
  plan    <- protocol   (the RSX program, e.g. override, swish, interrupt_only)
  context <- trigger_channel (V, A, K, O, G, thought, memory; empty = practice)
  outcome <- (sud_before - sud_after) + (agency_after - agency_before)   (higher is better)

Only completed runs with all four ratings are used. The codebook returned with the space maps each
category name to its index, so recommendations can be translated back into program settings.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .core import ProgramSpace

RATINGS = ["sud_before", "sud_after", "agency_before", "agency_after"]


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    for c in ("tier", "voice", "protocol", "trigger_channel"):
        if c not in d:
            d[c] = ""
        d[c] = d[c].fillna("").astype(str)
    d["tier"] = d["tier"].replace("", "none")
    d["voice"] = d["voice"].replace("", "none")
    d["trigger_channel"] = d["trigger_channel"].replace("", "practice")
    for c in RATINGS:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    if "completed" in d:
        d = d[pd.to_numeric(d["completed"], errors="coerce").fillna(1) == 1]
    d = d.dropna(subset=RATINGS)
    d["outcome"] = (d["sud_before"] - d["sud_after"]) + (d["agency_after"] - d["agency_before"])
    return d


def space_from_runlog(df: pd.DataFrame, codebook: dict | None = None):
    """Return (ProgramSpace, codebook). Pass an existing codebook to keep indices stable."""
    d = _clean(df)
    if codebook is None:
        codebook = {k: sorted(str(x) for x in d[c].unique()) for k, c in
                    (("glyph", "tier"), ("sound", "voice"), ("plan", "protocol"), ("context", "trigger_channel"))}
    space = ProgramSpace(n_glyph=len(codebook["glyph"]), n_sound=len(codebook["sound"]),
                         n_plan=len(codebook["plan"]), n_context=len(codebook["context"]))
    return space, codebook


def histories_from_runlog(df: pd.DataFrame, codebook: dict) -> list[dict]:
    """One history per participant, in the format ArchetypeBank.fit expects."""
    d = _clean(df)
    idx = {k: {v: i for i, v in enumerate(vals)} for k, vals in codebook.items()}
    d = d[d["tier"].isin(idx["glyph"]) & d["voice"].isin(idx["sound"]) & d["protocol"].isin(idx["plan"])
          & d["trigger_channel"].isin(idx["context"])]
    out = []
    order = ["participant", "timestamp"] if "timestamp" in d else ["participant"]
    for pid, t in d.sort_values(order).groupby("participant"):
        progs = np.column_stack([t["tier"].map(idx["glyph"]), t["voice"].map(idx["sound"]),
                                 t["protocol"].map(idx["plan"])]).astype(int)
        out.append(dict(person_id=pid, programs=progs, contexts=t["trigger_channel"].map(idx["context"]).to_numpy(int),
                        outcomes=t["outcome"].to_numpy(float)))
    return out


def describe(codebook: dict, program: tuple, context: int | None = None) -> dict:
    """Translate (glyph, sound, plan) indices back into tier, voice and protocol names."""
    g, s, p = program
    out = {"tier": codebook["glyph"][g], "voice": codebook["sound"][s], "protocol": codebook["plan"][p]}
    if context is not None:
        out["trigger_channel"] = codebook["context"][context]
    return out
