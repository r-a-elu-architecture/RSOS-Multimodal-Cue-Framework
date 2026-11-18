"""The public edition of the archive records (spec/PUBLIC_EDITION.md §2, rule E1): "GPT" becomes "model".

The originals in archive/ are never edited. Generators apply edit() to what they publish, after any check against the
original, so the published edition equals the original plus exactly this rule.
"""
from __future__ import annotations

import re

_RULES = [
    (re.compile(r"\bGPT Behavior\b"), "Model Behavior"),
    (re.compile(r"\bChatGPT\b"), "the model"),
    (re.compile(r"\bGPT-(\d+(?:\.\d+)?[a-z]?)\b"), r"model version \1"),
    (re.compile(r"\bGPTs\b"), "models"),
    # at the start of a line, a field or a sentence (after optional bullets, spaces, quotes or a dash)
    (re.compile(r"(^|[\n:.!?;]\s*|^[•\-\s]*|\n[•\-\s]*|[\"“(]\s*)GPT\b"), r"\1Model"),
    (re.compile(r"\bGPT\b"), "model"),
    (re.compile(r"\bgpt\b"), "model"),
]


def edit(s: str) -> str:
    for pat, rep in _RULES:
        s = pat.sub(rep, s)
    return s


def edit_all(x):
    """Apply edit() to every string in a JSON-like structure (keys and values)."""
    if isinstance(x, str):
        return edit(x)
    if isinstance(x, list):
        return [edit_all(v) for v in x]
    if isinstance(x, dict):
        return {edit_all(k): edit_all(v) for k, v in x.items()}
    return x
