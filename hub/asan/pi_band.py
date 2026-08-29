"""3 buzzers on the student's wrist, driven by Pi 5 hardware PWM. right = right-hand stroke, left = left, accent = dhim/thom."""
from __future__ import annotations

import logging
import time

from .config import ZONES

log = logging.getLogger(__name__)
ZONE_PINS = {"right": 18, "left": 13, "accent": 12}


class PiBand:
    def __init__(self, dry_run: bool = False):
        self.dry = dry_run
        if not dry_run:
            from gpiozero import PWMOutputDevice
            self.pwm = {z: PWMOutputDevice(p, frequency=200) for z, p in ZONE_PINS.items()}
        log.info("band %s pins %s", "DRY" if dry_run else "GPIO", ZONE_PINS)

    def pulse(self, zone: str, ms: int, strength: float = 1.0) -> None:
        if zone not in ZONES:
            return
        if self.dry:
            print(f"  ~{zone}~", end="", flush=True); time.sleep(ms / 1000); return
        self.pwm[zone].value = strength; time.sleep(ms / 1000); self.pwm[zone].value = 0

    def off(self) -> None:
        if not self.dry:
            for d in self.pwm.values():
                d.value = 0
