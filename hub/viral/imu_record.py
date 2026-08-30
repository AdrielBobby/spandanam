"""Capture labelled IMU strike windows for a finger classifier (Edge Impulse-ready CSVs).

  python -m viral.imu_record index --n 200            # on the Pi; the index LED lights as a prompt
Writes data/imu/<finger>/<finger>.<k>.csv with rows: timestamp(ms),ax,ay,az,gx,gy,gz  (one file per strike,
~300 ms window: 100 ms before the hit, 200 ms after). Upload the folder to Edge Impulse with label = finger.
"""
from __future__ import annotations

import argparse
import csv
import os
import time
from pathlib import Path

from .config import FINGERS
from .hardware import Glove
from .imu import MPU6050Reader

DATA = Path(__file__).resolve().parents[2] / "data" / "imu"


def write_window(path: Path, window: tuple) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    t0 = window[0][0] if window else 0.0
    with path.open("w", newline="") as f:
        w = csv.writer(f); w.writerow(["timestamp", "ax", "ay", "az", "gx", "gy", "gz"])
        for t, ax, ay, az, gx, gy, gz in window:
            w.writerow([round((t - t0) * 1000, 2), round(ax, 4), round(ay, 4), round(az, 4), round(gx, 2), round(gy, 2), round(gz, 2)])
    return len(window)


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("finger", choices=FINGERS); ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--dry", action="store_true"); a = ap.parse_args()
    fi = FINGERS.index(a.finger); glove = Glove(a.dry)
    imu = MPU6050Reader(float(os.environ.get("IMU_STRIKE_G", "1.0")), dry_run=a.dry); imu.start()
    existing = len(list((DATA / a.finger).glob("*.csv"))) if (DATA / a.finger).exists() else 0
    print(f"Recording {a.n} strikes for {a.finger.upper()} (already have {existing}). LED {fi} is lit — tap with that finger. Ctrl-C to stop.")
    glove.led(fi, True); k = existing
    try:
        while k < existing + a.n:
            for s in imu.drain():
                if len(s.window) < 20: continue
                k += 1; n = write_window(DATA / a.finger / f"{a.finger}.{k:04d}.csv", s.window)
                print(f"  #{k}  peak {s.peak_g:.1f} g  samples {n}  ({(k - existing)}/{a.n})")
                glove.cue(fi, ms=30, led=False)
            time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        glove.led(fi, False); glove.all_off()
    print(f"saved to {DATA / a.finger}  — total {k} files")


if __name__ == "__main__":
    main()
