"""Consented programming: cues a person (or a client with their therapist) chooses to install.

A programmed cue is content the person wants to become automatic: a thought or chain of thoughts, a
metaphor, a sound, a glyph, a behaviour. It can come from the consented-programming tiers of the ledger
(spec/TIER_LEDGER.md §2). It may act below awareness when it fires; it never acts without the person's
knowledge:

  - every cue has a consent record naming its exact content, who wrote it, the person it acts on, and how long
    it is valid;
  - a program that contains a cue (MARK "programmed:<id>") is refused unless that record is valid now;
  - therapist-led cues (the release-of-identity tiers 414, 420, 439, 440) also need a therapist present and a
    screening answer recorded before the session;
  - the person can list every cue and revoke any of them at any time; a revoked cue never runs again.

Conformance checks C12 and C13 test this. docs/js/consent.js is the same logic for the player (tested).
"""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field

THERAPIST_LED_TIERS = {"414", "420", "439", "440"}
SCREENING_QUESTION = "Right now, are you in crisis, or having thoughts of harming yourself or not wanting to live?"
CONSENT_SCHEMA = "rsos-consent/1"


@dataclass
class Consent:
    id: str
    content: str                  # exactly what will be delivered (words, metaphor, thought chain)
    person: str                   # the person it acts on, who gives the consent
    author: str = "self"          # "self" or "therapist"
    tier: str = ""                # ledger tier it comes from, e.g. "422"
    created_ms: int = 0
    expires_ms: int | None = None
    therapist_present: bool = False
    screened_ok: bool | None = None   # answer to the screening question was "no" (True), "yes" (False), not asked (None)
    revoked_ms: int | None = None
    sound_hz: float | None = None
    glyph: str = ""

    @property
    def therapist_led(self) -> bool:
        return self.tier in THERAPIST_LED_TIERS


def check(c: Consent | None, now_ms: int) -> tuple[bool, str]:
    """May this cue run now?"""
    if c is None:
        return False, "no consent record"
    if not c.content.strip() or not c.person.strip():
        return False, "consent must name the content and the person"
    if c.revoked_ms is not None and c.revoked_ms <= now_ms:
        return False, "revoked"
    if c.expires_ms is not None and now_ms >= c.expires_ms:
        return False, "expired"
    if c.therapist_led:
        if not c.therapist_present:
            return False, "therapist-led: needs a therapist present"
        if c.screened_ok is not True:
            return False, "therapist-led: screening not passed"
    return True, "ok"


@dataclass
class ConsentStore:
    items: dict[str, Consent] = field(default_factory=dict)

    def add(self, c: Consent) -> Consent:
        if c.id in self.items:
            raise ValueError(f"cue {c.id} already exists")
        self.items[c.id] = c
        return c

    def list(self) -> list[Consent]:
        """Everything ever programmed for this person, revoked cues included."""
        return sorted(self.items.values(), key=lambda c: c.created_ms)

    def revoke(self, cid: str, now_ms: int) -> None:
        self.items[cid].revoked_ms = now_ms

    def check(self, cid: str, now_ms: int) -> tuple[bool, str]:
        return check(self.items.get(cid), now_ms)

    def to_json(self) -> str:
        return json.dumps({"schema": CONSENT_SCHEMA, "cues": [asdict(c) for c in self.list()]}, ensure_ascii=False)


def programmed_ids(timeline: dict) -> list[str]:
    return [e["text"].split(":", 1)[1] for e in timeline["events"]
            if e["channel"] == "marker" and str(e.get("text", "")).startswith("programmed:")]


def gate(timeline: dict, store: ConsentStore | None, now_ms: int) -> tuple[bool, str]:
    """A program with programmed cues starts only if every cue's consent is valid now."""
    for cid in programmed_ids(timeline):
        ok, why = check(store.items.get(cid) if store else None, now_ms)
        if not ok:
            return False, f"cue {cid}: {why}"
    return True, "ok"


def _q(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


def cue_program(c: Consent, inhale_s: int = 4, exhale_s: int = 6) -> str:
    """The RSX program that delivers one cue: settle, inhale, the cue on the exhale, then a quiet exhale."""
    lines = [f"# Programmed cue {c.id} (consent record), from tier {c.tier or '-'}; author: {c.author}.",
             f"PROTOCOL cue_{c.id} {_q('Programmed cue')}", "VERSION 1.0",
             "SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4",
             f"BREATH inhale={inhale_s}s exhale={exhale_s}s",
             "PHASE settle dur=2s {", '  FEEL "Settle"', "}",
             "PHASE inhale breath=inhale {", '  FEEL "Breathe in"', "}",
             "PHASE cue breath=exhale {", f"  SAY {_q(c.content)}"]
    if c.sound_hz:
        lines.append(f"  TONE {int(math.floor(c.sound_hz + 0.5))}Hz 2s")
    lines += [f"  MARK {_q('programmed:' + c.id)}", "}",
              "PHASE rest breath=exhale {", '  FEEL "Let it settle"', '  MARK "installed"', "}"]
    return "\n".join(lines) + "\n"
