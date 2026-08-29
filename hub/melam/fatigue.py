"""Fatigue feature extraction: HR trend, strike amplitude decay, timing jitter growth."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FatigueFeatures:
    node: str
    hr_bpm: float
    hr_slope_bpm_per_min: float
    amp_decay_pct: float        # % drop of median strike peak, first half vs second half of window
    jitter_growth_pct: float    # % growth of IOI jitter, first half vs second half
    strikes_per_min: float


def _median(xs: list[float]) -> float:
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return 0.0
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def _pct_change(a: float, b: float) -> float:
    return 0.0 if a == 0 else (b - a) / a * 100.0


def extract(node: str, window_s: float,
            hr_series: list[tuple[float, float]],      # (t_s, bpm)
            strikes: list[tuple[float, float]]) -> FatigueFeatures:  # (t_s, peak_g)
    hr = [b for _, b in hr_series if b > 0]
    hr_now = _median(hr[-5:]) if hr else 0.0
    slope = 0.0
    if len(hr_series) >= 2 and hr_series[-1][0] > hr_series[0][0]:
        dt_min = (hr_series[-1][0] - hr_series[0][0]) / 60.0
        slope = (hr_series[-1][1] - hr_series[0][1]) / dt_min if dt_min > 0 else 0.0

    half = len(strikes) // 2
    first, second = strikes[:half], strikes[half:]
    amp_decay = -_pct_change(_median([p for _, p in first]), _median([p for _, p in second]))

    def jitter(seg: list[tuple[float, float]]) -> float:
        ts = [t for t, _ in seg]
        ioi = [b - a for a, b in zip(ts, ts[1:])]
        m = _median(ioi)
        return _median([abs(x - m) for x in ioi]) if ioi else 0.0

    jitter_growth = _pct_change(jitter(first), jitter(second))
    spm = len(strikes) / (window_s / 60.0) if window_s > 0 else 0.0
    return FatigueFeatures(node, hr_now, slope, amp_decay, jitter_growth, spm)
