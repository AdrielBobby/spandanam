"""5 buzzers + 5 LEDs on Pi GPIO; dry mode logs each cue. Non-blocking pulses via threads."""
from __future__ import annotations

import logging
import os
import threading
import time

from .config import BUZZER_PINS, FINGERS, LED_PINS

log = logging.getLogger(__name__)


def _name(finger: int) -> str:
    """Readable finger label for logs; falls back to f<n> if out of range."""
    return FINGERS[finger] if 0 <= finger < len(FINGERS) else f"f{finger}"


class Glove:
    def __init__(self, dry: bool):
        self.dry = dry
        self.buzz_enabled = os.environ.get("THAALAM_NO_BUZZ", "0") != "1"    # THAALAM_NO_BUZZ=1 mutes buzzers (LEDs keep working)
        if not dry:
            from gpiozero import LED, PWMOutputDevice
            self.buzz = [PWMOutputDevice(p, frequency=200) for p in BUZZER_PINS]
            self.leds = [LED(p) for p in LED_PINS]
        log.info("glove %s%s", "DRY" if dry else f"buzzers {BUZZER_PINS} leds {LED_PINS}", "" if self.buzz_enabled else " · buzzers MUTED (THAALAM_NO_BUZZ=1)")

    def _log(self, msg: str, *args: object) -> None:
        """INFO in dry mode (visible on the laptop), DEBUG on the Pi (quiet during a live run)."""
        log.log(logging.INFO if self.dry else logging.DEBUG, msg, *args)

    def _pulse(self, finger: int, ms: int, strength: float, led: bool) -> None:
        if self.dry:
            return
        if led: self.leds[finger].on()
        if self.buzz_enabled: self.buzz[finger].value = strength
        time.sleep(ms / 1000)
        if self.buzz_enabled: self.buzz[finger].value = 0
        if led: self.leds[finger].off()

    def cue(self, finger: int, ms: int = 60, strength: float = 1.0, led: bool = True) -> None:
        self._log("cue %s %dms x%.2f led=%s", _name(finger), ms, strength, "on" if led else "off")
        if self.dry:
            return
        threading.Thread(target=self._pulse, args=(finger, ms, strength, led), daemon=True).start()

    def led(self, finger: int, on: bool) -> None:
        self._log("led %s %s", _name(finger), "on" if on else "off")
        if not self.dry:
            (self.leds[finger].on if on else self.leds[finger].off)()

    def all_off(self) -> None:
        self._log("all_off")
        if not self.dry:
            for b in self.buzz: b.value = 0
            for l in self.leds: l.off()
