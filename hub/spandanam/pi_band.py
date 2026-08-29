"""Run the wearable directly from Raspberry Pi GPIO (no XIAO). 3-zone kit: chest, wrist, finger buzzers.
Wiring: each buzzer (+) -> GPIO via 100 Ω, (-) -> GND. For >40 mA buzzers/motors use an NPN transistor.
"""
from __future__ import annotations

import logging

from .config import MOTORS

log = logging.getLogger(__name__)

# 3-zone mapping of the 8 logical motors onto physical GPIO pins.
ZONE_PINS = {"chest": 18, "wrist": 13, "finger": 12}       # hardware-PWM capable pins on Pi 5
ZONE_OF = {"chest": "chest", "back": "chest", "l_wrist": "wrist", "r_wrist": "wrist",
           "l_shoulder": "finger", "r_shoulder": "finger", "l_finger": "finger", "r_finger": "finger"}


def collapse_to_zones(frame: bytes) -> dict[str, float]:
    """8-motor frame -> 3 zone duty cycles (0..1), max-pooled."""
    vals = dict(zip(MOTORS, frame[1:9]))
    out = {z: 0.0 for z in ZONE_PINS}
    for m, v in vals.items():
        z = ZONE_OF[m]
        out[z] = max(out[z], v / 255.0)
    return out


class PiBand:
    def __init__(self):
        from gpiozero import PWMOutputDevice
        self.pwm = {z: PWMOutputDevice(p, frequency=200) for z, p in ZONE_PINS.items()}
        log.info("Pi band on pins %s", ZONE_PINS)

    def send(self, frame: bytes) -> None:
        for z, duty in collapse_to_zones(frame).items():
            self.pwm[z].value = duty

    def off(self) -> None:
        for d in self.pwm.values():
            d.value = 0
