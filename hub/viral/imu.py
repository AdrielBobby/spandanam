"""MPU6050 on the stick (Pi I2C). Stroke events with peak g and wrist tilt at impact."""
from __future__ import annotations

import logging
import math
import threading
import time
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Stroke:
    t_s: float
    peak_g: float
    tilt_deg: float     # stick angle from horizontal at impact (from gravity vector before the hit)


def stroke_from_samples(t_s: float, mags_g: list[float], gravity_xyz: tuple[float, float, float],
                        threshold_g: float) -> Stroke | None:
    if len(mags_g) < 2 or (max(mags_g) - 1.0) < threshold_g:   # window peak above the ~1 g rest
        return None
    gx, gy, gz = gravity_xyz
    tilt = math.degrees(math.atan2(gz, math.hypot(gx, gy))) if any((gx, gy, gz)) else 0.0
    return Stroke(t_s, max(mags_g) - 1.0, tilt)


class MPU6050Reader(threading.Thread):
    """Background reader; call .drain() to get strokes since last call. Dry-run yields nothing."""
    ADDR, PWR, ACC, ACFG = 0x68, 0x6B, 0x3B, 0x1C

    def __init__(self, threshold_g: float, dry_run: bool = False):
        super().__init__(daemon=True)
        self.threshold, self.dry = threshold_g, dry_run
        self._strokes: list[Stroke] = []
        self._lock = threading.Lock()
        self._bus = None
        if not dry_run:
            from smbus2 import SMBus
            self._bus = SMBus(1); self._bus.write_byte_data(self.ADDR, self.PWR, 0)
            self._bus.write_byte_data(self.ADDR, self.ACFG, 0x18)   # accel FS_SEL=3 => +/-16 g, matches the /2048 scale

    def _read_g(self) -> tuple[float, float, float]:
        d = self._bus.read_i2c_block_data(self.ADDR, self.ACC, 6)
        def s16(h, l): v = (h << 8) | l; return v - 65536 if v > 32767 else v
        return tuple(s16(d[i], d[i + 1]) / 2048.0 for i in (0, 2, 4))   # ±16 g range

    def run(self) -> None:
        if self.dry: return
        mags, grav, t0 = [], (0.0, 0.0, 1.0), time.monotonic()
        last_t, armed = 0.0, True
        while True:
            x, y, z = self._read_g(); m = math.sqrt(x * x + y * y + z * z)
            if m < 1.3: grav = (x, y, z)           # quiet moment: remember gravity for tilt
            mags = (mags + [m])[-4:]
            now = time.monotonic() - t0
            s = stroke_from_samples(now, mags, grav, self.threshold)
            if s and armed and now - last_t > 0.12:     # one Stroke per hit: 120 ms refractory + re-arm
                with self._lock: self._strokes.append(s)
                last_t, armed = now, False
            elif m < 1.0 + self.threshold * 0.4:        # settled back toward rest -> ready for the next hit
                armed = True
            time.sleep(0.004)

    def drain(self) -> list[Stroke]:
        with self._lock:
            out, self._strokes = self._strokes, []
        return out
