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
    window: tuple = ()  # raw (t_s, ax, ay, az, gx, gy, gz) samples around the hit, for finger classification / dataset capture


PRE_S, POST_S = 0.10, 0.20   # capture window around a strike


def stroke_from_samples(t_s: float, mags_g: list[float], gravity_xyz: tuple[float, float, float],
                        threshold_g: float) -> Stroke | None:
    if len(mags_g) < 2 or (max(mags_g) - 1.0) < threshold_g:   # window peak above the ~1 g rest
        return None
    gx, gy, gz = gravity_xyz
    tilt = math.degrees(math.atan2(gz, math.hypot(gx, gy))) if any((gx, gy, gz)) else 0.0
    return Stroke(t_s, max(mags_g) - 1.0, tilt)


class MPU6050Reader(threading.Thread):
    """Background reader; call .drain() to get strokes since last call. Dry-run yields nothing."""
    ADDR, PWR, ACC, ACFG, GYR = 0x68, 0x6B, 0x3B, 0x1C, 0x43

    def __init__(self, threshold_g: float, dry_run: bool = False):
        super().__init__(daemon=True)
        self.threshold, self.dry = threshold_g, dry_run
        self._strokes: list[Stroke] = []
        self._lock = threading.Lock()
        self._ring: list[tuple] = []                  # recent raw samples (t, ax, ay, az, gx, gy, gz)
        self._pending: list[tuple[float, Stroke]] = []  # strokes waiting for their POST_S tail of samples
        self._bus = None
        if not dry_run:
            self._open_bus()

    def _read_g(self) -> tuple[float, float, float]:
        d = self._bus.read_i2c_block_data(self.ADDR, self.ACC, 6)
        def s16(h, l): v = (h << 8) | l; return v - 65536 if v > 32767 else v
        return tuple(s16(d[i], d[i + 1]) / 2048.0 for i in (0, 2, 4))   # ±16 g range

    def _read_all(self) -> tuple[float, float, float, float, float, float]:
        """accel (g) + gyro (deg/s, ±250 range) in one 14-byte burst read."""
        d = self._bus.read_i2c_block_data(self.ADDR, self.ACC, 14)
        def s16(h, l): v = (h << 8) | l; return v - 65536 if v > 32767 else v
        ax, ay, az = (s16(d[i], d[i + 1]) / 2048.0 for i in (0, 2, 4))
        gx, gy, gz = (s16(d[i], d[i + 1]) / 131.0 for i in (8, 10, 12))
        return ax, ay, az, gx, gy, gz

    def _open_bus(self) -> None:
        from smbus2 import SMBus
        self._bus = SMBus(1); self._bus.write_byte_data(self.ADDR, self.PWR, 0)
        self._bus.write_byte_data(self.ADDR, self.ACFG, 0x18)          # ±16 g, matches the /2048 scale

    def run(self) -> None:
        if self.dry: return
        mags, grav, t0 = [], (0.0, 0.0, 1.0), time.monotonic()
        last_t, armed, errors = 0.0, True, 0
        while True:
            try:
                x, y, z, gx, gy, gz = self._read_all(); m = math.sqrt(x * x + y * y + z * z)
                errors = 0
            except OSError as e:                                     # bus glitch / contention: never let the thread die
                errors += 1
                if errors in (1, 50): log.warning("IMU read error (%s), retrying%s", e, " and re-opening bus" if errors >= 50 else "")
                if errors >= 50:
                    try: self._open_bus()
                    except OSError: pass
                    errors = 0
                time.sleep(0.05); continue
            if m < 1.3: grav = (x, y, z)           # quiet moment: remember gravity for tilt
            mags = (mags + [m])[-4:]
            now = time.monotonic() - t0
            self._ring.append((now, x, y, z, gx, gy, gz))
            if len(self._ring) > 400: del self._ring[:-400]
            s = stroke_from_samples(now, mags, grav, self.threshold)
            if s and armed and now - last_t > 0.12:     # one Stroke per hit: 120 ms refractory + re-arm
                last_t, armed = now, False
                self._pending.append((now, s))          # publish once the POST_S tail has been captured
            elif m < 1.0 + self.threshold * 0.4:        # settled back toward rest -> ready for the next hit
                armed = True
            self._flush_pending(now)
            time.sleep(0.002)

    def _flush_pending(self, now: float) -> None:
        ready = [(t, s) for t, s in self._pending if now - t >= POST_S]
        if not ready: return
        self._pending = [(t, s) for t, s in self._pending if now - t < POST_S]
        for t, s in ready:
            win = tuple(r for r in self._ring if t - PRE_S <= r[0] <= t + POST_S)
            with self._lock: self._strokes.append(Stroke(s.t_s, s.peak_g, s.tilt_deg, win))

    def drain(self) -> list[Stroke]:
        with self._lock:
            out, self._strokes = self._strokes, []
        return out
