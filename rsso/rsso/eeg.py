"""AUG EEG input: one stream interface for any headset, a replay source, a synthetic source and an
arousal detector built on band powers.

  EEGStream     interface: `channels`, `srate`, `pull(seconds)` -> array (samples, channels)
  ReplayStream  plays back a recording (numpy array or CSV), in chunks, as a live headset would
  SyntheticEEG  pink background plus a 10 Hz alpha rhythm; "arousal" events suppress alpha and raise beta
                (the usual direction of change with arousal and stress; magnitudes here are assumptions)
  LslStream     any headset that publishes to Lab Streaming Layer (Muse via muse-lsl, OpenBCI, Emotiv, …);
                needs the optional `pylsl` package
  band_powers   log power in theta, alpha and beta bands (Welch)
  ArousalDetector  flags a sustained rise of the beta/alpha ratio over the person's own baseline

EEG-based state detection differs a lot between people and headsets. The detector is a starting point to be
calibrated per person (the UGCL / calibration stage), not a validated measure of stress.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import welch

BANDS = {"theta": (4, 8), "alpha": (8, 13), "beta": (13, 30)}


class EEGStream:
    channels: list
    srate: float

    def pull(self, seconds: float) -> np.ndarray:
        raise NotImplementedError


class ReplayStream(EEGStream):
    def __init__(self, data, srate: float, channels=None):
        self.data = np.asarray(data, float)
        if self.data.ndim == 1:
            self.data = self.data[:, None]
        self.srate = float(srate)
        self.channels = list(channels or [f"ch{i}" for i in range(self.data.shape[1])])
        self.pos = 0

    @classmethod
    def from_csv(cls, path, srate: float, time_column: str | None = None):
        import pandas as pd
        d = pd.read_csv(path)
        if time_column:
            d = d.drop(columns=[time_column])
        return cls(d.to_numpy(float), srate, list(d.columns))

    def pull(self, seconds: float) -> np.ndarray:
        n = int(round(seconds * self.srate))
        chunk = self.data[self.pos:self.pos + n]
        self.pos += len(chunk)
        return chunk

    @property
    def done(self) -> bool:
        return self.pos >= len(self.data)


@dataclass
class ArousalEvent:
    t_s: float
    dur_s: float = 60.0
    alpha_drop: float = 0.5     # fraction of alpha amplitude lost at the peak
    beta_rise: float = 0.6      # fractional increase of beta amplitude at the peak


def synthetic_eeg(duration_s: float, srate: float = 256, events=(), channels=("AF7", "AF8", "TP9", "TP10"), seed: int = 0):
    """Returns (data, srate, channels): microvolt-scale signals with alpha and beta rhythms."""
    rng = np.random.default_rng(seed)
    n = int(duration_s * srate); t = np.arange(n) / srate
    alpha_env = np.ones(n); beta_env = np.ones(n)
    for e in events:
        rise = np.clip((t - e.t_s) / 5, 0, 1) * np.exp(-np.clip(t - e.t_s - e.dur_s, 0, None) / 20)
        rise[t < e.t_s] = 0
        alpha_env *= 1 - e.alpha_drop * rise
        beta_env *= 1 + e.beta_rise * rise
    out = []
    for c in range(len(channels)):
        white = rng.normal(size=n)
        f = np.fft.rfftfreq(n, 1 / srate); spec = np.fft.rfft(white); spec[1:] /= np.sqrt(f[1:]); spec[0] = 0
        pink = np.fft.irfft(spec, n); pink *= 6 / pink.std()
        ph = rng.uniform(0, 2 * np.pi, 2)
        alpha = 10 * alpha_env * np.sin(2 * np.pi * (10 + 0.3 * np.sin(2 * np.pi * t / 7)) * t + ph[0])
        beta = 3 * beta_env * np.sin(2 * np.pi * 20 * t + ph[1]) * (1 + 0.3 * rng.normal(size=n).cumsum() / np.sqrt(n))
        out.append(pink + alpha + beta)
    return np.stack(out, 1), float(srate), list(channels)


class LslStream(EEGStream):
    """Reads the first EEG stream on the network through Lab Streaming Layer (pip install pylsl)."""

    def __init__(self, stream_type: str = "EEG", timeout: float = 10):
        try:
            from pylsl import StreamInlet, resolve_byprop
        except ImportError as e:
            raise ImportError("LslStream needs the pylsl package: pip install pylsl") from e
        found = resolve_byprop("type", stream_type, timeout=timeout)
        if not found:
            raise RuntimeError(f"no LSL stream of type {stream_type} found")
        self.inlet = StreamInlet(found[0]); info = self.inlet.info()
        self.srate = info.nominal_srate(); self.channels = [f"ch{i}" for i in range(info.channel_count())]

    def pull(self, seconds: float) -> np.ndarray:
        chunk, _ = self.inlet.pull_chunk(timeout=seconds, max_samples=int(seconds * self.srate))
        return np.asarray(chunk, float).reshape(-1, len(self.channels))


def band_powers(x: np.ndarray, srate: float) -> dict:
    """Log10 band power per band, averaged over channels."""
    f, p = welch(x, fs=srate, nperseg=min(len(x), int(2 * srate)), axis=0)
    out = {}
    for name, (lo, hi) in BANDS.items():
        m = (f >= lo) & (f < hi)
        out[name] = float(np.log10(p[m].mean(axis=0).mean() + 1e-12))
    return out


@dataclass
class ArousalDetector:
    window_s: float = 4.0
    step_s: float = 1.0
    baseline_s: float = 120.0
    z_threshold: float = 2.5
    sustain_s: float = 6.0
    rearm_s: float = 120.0

    def __post_init__(self):
        self.buf = None; self.t = 0.0; self.hist = []; self.held = 0.0; self.last = -1e9; self.detections = []

    def push(self, chunk: np.ndarray, srate: float):
        """Feed consecutive chunks. Returns detection times (s) found in this chunk."""
        self.buf = chunk if self.buf is None else np.vstack([self.buf, chunk])
        keep = int(self.window_s * srate)
        found = []
        step = int(self.step_s * srate)
        while len(self.buf) >= keep + step:
            win = self.buf[:keep]
            self.buf = self.buf[step:]
            self.t += self.step_s
            bp = band_powers(win, srate)
            ratio = bp["beta"] - bp["alpha"]            # log10(beta/alpha)
            base = [r for (tt, r) in self.hist if tt <= self.t - 10 and tt > self.t - 10 - self.baseline_s]
            self.hist.append((self.t, ratio))
            if len(base) < self.baseline_s / self.step_s / 2:
                continue
            z = (ratio - np.mean(base)) / (np.std(base) + 1e-9)
            self.held = self.held + self.step_s if z > self.z_threshold else 0.0
            if self.held >= self.sustain_s and self.t - self.last >= self.rearm_s:
                self.detections.append(self.t); found.append(self.t); self.last = self.t; self.held = 0.0
        return found
