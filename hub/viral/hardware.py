"""5 buzzers + 5 LEDs on Pi GPIO; dry mode prints. Non-blocking pulses via threads."""
from __future__ import annotations

import logging
import threading
import time

from .config import BUZZER_PINS, LED_PINS

log = logging.getLogger(__name__)


class Glove:
    def __init__(self, dry: bool):
        self.dry = dry
        if not dry:
            from gpiozero import LED, PWMOutputDevice
            self.buzz = [PWMOutputDevice(p, frequency=200) for p in BUZZER_PINS]
            self.leds = [LED(p) for p in LED_PINS]
        log.info("glove %s", "DRY" if dry else f"buzzers {BUZZER_PINS} leds {LED_PINS}")

    def _pulse(self, finger: int, ms: int, strength: float, led: bool) -> None:
        if self.dry:
            return
        if led: self.leds[finger].on()
        self.buzz[finger].value = strength
        time.sleep(ms / 1000)
        self.buzz[finger].value = 0
        if led: self.leds[finger].off()

    def cue(self, finger: int, ms: int = 60, strength: float = 1.0, led: bool = True) -> None:
        threading.Thread(target=self._pulse, args=(finger, ms, strength, led), daemon=True).start()

    def led(self, finger: int, on: bool) -> None:
        if not self.dry:
            (self.leds[finger].on if on else self.leds[finger].off)()

    def all_off(self) -> None:
        if not self.dry:
            for b in self.buzz: b.value = 0
            for l in self.leds: l.off()
