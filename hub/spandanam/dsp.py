"""Fast path: per-band energy + onset detection at 100 Hz. Pure functions."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import BANDS


@dataclass(frozen=True)
class BandFrame:
    energy: dict[str, float]     # 0..1 normalised per band
    onset: dict[str, bool]


def band_energies(frame: np.ndarray, sr: int) -> dict[str, float]:
    if frame.size == 0:
        return {b: 0.0 for b in BANDS}
    spec = np.abs(np.fft.rfft(frame * np.hanning(frame.size)))
    freqs = np.fft.rfftfreq(frame.size, 1 / sr)
    out = {}
    for name, (lo, hi) in BANDS.items():
        m = (freqs >= lo) & (freqs < hi)
        out[name] = float(np.sqrt(np.mean(spec[m] ** 2))) if m.any() else 0.0
    return out


def normalise(energy: dict[str, float], running_max: dict[str, float], decay: float = 0.995
              ) -> tuple[dict[str, float], dict[str, float]]:
    """Adaptive gain: track a decaying max per band, return 0..1 levels and the new max."""
    new_max = {b: max(energy[b], running_max.get(b, 1e-6) * decay) for b in energy}
    levels = {b: min(1.0, energy[b] / new_max[b]) if new_max[b] > 0 else 0.0 for b in energy}
    return levels, new_max


def detect_onsets(levels: dict[str, float], prev: dict[str, float], rise: float = 0.35) -> dict[str, bool]:
    return {b: (levels[b] - prev.get(b, 0.0)) > rise for b in levels}
