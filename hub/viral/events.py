"""One event type for every input: real IMU, laptop keys, future gloves."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Strike:
    finger: int
    t_s: float           # server monotonic time
    velocity: float      # 0..1
    source: str          # "imu" | "key"
