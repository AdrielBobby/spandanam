"""Fake nodes for developing the hub without hardware: 3 drummers, one lagging, one tiring."""
from __future__ import annotations

import argparse
import json
import math
import random
import socket
import time


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1"); ap.add_argument("--port", type=int, default=9000)
    ap.add_argument("--bpm", type=float, default=80)
    a = ap.parse_args()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    nodes = {"drummer-1": 0.0, "drummer-2": 0.09, "drummer-3": -0.02}  # phase lag seconds
    period = 60.0 / a.bpm
    t0 = time.time(); hr0 = 95
    while True:
        t = time.time() - t0
        for n, lag in nodes.items():
            phase = ((t - lag) % period) / period
            strike = 6.0 * math.exp(-((phase - 0.02) ** 2) / 0.0004)
            if n == "drummer-3":
                strike *= max(0.4, 1 - t / 120)               # amplitude decays over 2 min
            az = 9.81 + strike * 9.81 + random.gauss(0, 0.3)
            bpm = hr0 + (t * 0.6 if n == "drummer-3" else t * 0.05) + random.gauss(0, 1)
            pkt = {"id": n, "t": int(time.time() * 1e6), "ax": random.gauss(0, .2), "ay": random.gauss(0, .2),
                   "az": az, "gx": 0, "gy": 0, "gz": 0, "bpm": round(bpm)}
            sock.sendto(json.dumps(pkt).encode(), (a.host, a.port))
        time.sleep(0.01)


if __name__ == "__main__":
    main()
