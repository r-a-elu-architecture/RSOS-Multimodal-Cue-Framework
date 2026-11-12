"""Bluetooth Heart Rate Service (HRS) driver: the standard every chest strap and most watches speak.

Heart Rate Measurement characteristic (UUID 0x2A37), Bluetooth SIG Heart Rate Service 1.0:
  byte 0 flags: bit 0  heart-rate value is uint16 (else uint8)
                bits 1-2 sensor contact status (bit 2 = feature supported, bit 1 = contact detected)
                bit 3  energy expended (uint16, kJ) present
                bit 4  one or more RR intervals present (uint16 each, units of 1/1024 s)
  then heart rate, then energy expended if present, then RR intervals to the end of the packet.

`parse_hrm` is mirrored by `parseHeartRateMeasurement` in docs/js/hrs.js; tests feed both the same packets.
`HrsStream` turns notifications into the beat-time / RR arrays the StressDetector uses.
"""
from __future__ import annotations

import struct

import numpy as np


def parse_hrm(packet: bytes) -> dict:
    if len(packet) < 2:
        raise ValueError("heart rate measurement too short")
    flags = packet[0]
    i = 1
    if flags & 0x01:
        hr = struct.unpack_from("<H", packet, i)[0]; i += 2
    else:
        hr = packet[i]; i += 1
    contact = None
    if flags & 0x04:
        contact = bool(flags & 0x02)
    energy = None
    if flags & 0x08:
        energy = struct.unpack_from("<H", packet, i)[0]; i += 2
    rr = []
    if flags & 0x10:
        while i + 1 < len(packet):
            rr.append(struct.unpack_from("<H", packet, i)[0] * 1000.0 / 1024.0); i += 2
    return {"hr": hr, "contact": contact, "energy_kj": energy, "rr_ms": rr}


def encode_hrm(hr: int, rr_ms=(), contact=None, energy_kj=None, hr16=False) -> bytes:
    """Build a packet (used for tests and for replaying recordings through the real parser)."""
    flags = (0x01 if hr16 else 0) | (0x04 | (0x02 if contact else 0) if contact is not None else 0)
    flags |= (0x08 if energy_kj is not None else 0) | (0x10 if len(rr_ms) else 0)
    out = bytes([flags]) + (struct.pack("<H", hr) if hr16 else bytes([hr]))
    if energy_kj is not None:
        out += struct.pack("<H", energy_kj)
    for r in rr_ms:
        out += struct.pack("<H", int(round(r * 1024 / 1000)))
    return out


class HrsStream:
    """Accumulates RR intervals from notifications. Beat times are reconstructed from the RR sum."""

    def __init__(self):
        self.t, self.rr, self.motion = [], [], []
        self._clock = 0.0

    def push(self, packet: bytes, moving: bool = False):
        m = parse_hrm(packet)
        for r in m["rr_ms"]:
            if 300 <= r <= 2000:          # drop physiologically impossible intervals (artefacts)
                self._clock += r / 1000.0
                self.t.append(self._clock); self.rr.append(r); self.motion.append(moving)
        return m

    def recording(self) -> dict:
        return {"t": np.array(self.t), "rr": np.array(self.rr), "motion": np.array(self.motion, bool)}
