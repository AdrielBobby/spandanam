"""Motion coach: explains weak/flat hits using the MPU6050's wrist tilt at impact
(imu.Stroke.tilt_deg), which is already computed per-stroke in imu.py -- this module
adds no new sensor logic, just turns strokes into a round-level coaching verdict.

Only ever has real data for finger 0 (thumb): the only finger with a physical IMU
today (see README's "1 real IMU on the thumb, 4 fingers emulated by laptop keys").
Fingers 1-4 are key-emulated and never produce a Stroke.

tilt_deg is the stick's angle from HORIZONTAL at impact (0 = flat, ~90 = upright,
per imu.py's docstring), so "flat" is a LOW tilt_deg, not high. No peak_g-based
"weak" verdict here: imu_strike_g (Config, default 2.5) already gates which
accelerometer jumps become a Stroke at all, so a genuinely weak hit mostly never
reaches this module in the first place -- avg_peak_g is still reported for
context, just not used to branch the verdict.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .imu import Stroke

FLAT_TILT_DEG = 30.0   # rough starting guess -- needs tuning against real strikes on hardware


@dataclass(frozen=True)
class MotionFeedback:
    avg_tilt_deg: float
    avg_peak_g: float
    verdict: str        # "good" | "flat"
    hint: str

    def as_dict(self) -> dict:
        return {"avg_tilt_deg": round(self.avg_tilt_deg, 1), "avg_peak_g": round(self.avg_peak_g, 2),
                "verdict": self.verdict, "hint": self.hint}


def motion_feedback(strokes: Sequence[Stroke]) -> MotionFeedback | None:
    """Aggregate feedback over a round's thumb strokes. None if there were none --
    e.g. --dry laptop mode (MPU6050Reader never yields strokes there), or a round
    played entirely on key-emulated fingers."""
    if not strokes:
        return None
    avg_tilt = sum(s.tilt_deg for s in strokes) / len(strokes)
    avg_g = sum(s.peak_g for s in strokes) / len(strokes)
    if avg_tilt < FLAT_TILT_DEG:
        return MotionFeedback(avg_tilt, avg_g, "flat", "Wrist is dropping flat at impact -- keep it more upright.")
    return MotionFeedback(avg_tilt, avg_g, "good", "")
