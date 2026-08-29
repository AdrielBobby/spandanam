"""Wearer's IMU tap-along: are the taps locked to the melam's onsets? Closed-loop proof the haptics carry rhythm."""
from __future__ import annotations

from dataclasses import dataclass
from statistics import median


@dataclass(frozen=True)
class TapSync:
    taps: int
    offset_ms: float     # median signed offset tap - nearest onset (+ = late)
    locked: bool


def detect_tap(prev_mag: float, mag_g: float, threshold_g: float = 2.0) -> bool:
    return (mag_g - prev_mag) > threshold_g


def tap_sync(onsets_s: list[float], taps_s: list[float], tol_ms: float = 90.0) -> TapSync:
    if not onsets_s or len(taps_s) < 3:
        return TapSync(len(taps_s), 0.0, False)
    offs = [(t - min(onsets_s, key=lambda o: abs(o - t))) * 1000 for t in taps_s[-8:]]
    med = median(offs)
    return TapSync(len(taps_s), med, abs(med) <= tol_ms)
