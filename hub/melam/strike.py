"""Strike (stroke onset) detection from accelerometer magnitude. Pure functions, no mutation."""
from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class StrikeState:
    last_strike_us: int = -10**12
    armed: bool = True


@dataclass(frozen=True)
class Strike:
    node: str
    t_us: int
    peak_g: float


def detect_strike(state: StrikeState, t_us: int, mag_g: float,
                  threshold_g: float, refractory_s: float) -> tuple[StrikeState, Strike | None]:
    """Threshold crossing with hysteresis re-arm and refractory period.
    mag_g is |accel|/g; gravity contributes ~1g so the excess over 1g is the strike energy."""
    excess = mag_g - 1.0
    refractory_us = int(refractory_s * 1e6)
    if state.armed and excess >= threshold_g and (t_us - state.last_strike_us) >= refractory_us:
        return replace(state, last_strike_us=t_us, armed=False), Strike("", t_us, excess)
    if not state.armed and excess < threshold_g * 0.5:
        return replace(state, armed=True), None
    return state, None
