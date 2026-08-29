"""Compose an 8-motor frame from band levels + the current body map, and send it."""
from __future__ import annotations

import socket

from .config import MOTORS


def compose_frame(levels: dict[str, float], onsets: dict[str, bool], body_map: dict[str, tuple[str, ...]],
                  gains: dict[str, float], motif: dict[str, int] | None, max_int: int) -> bytes:
    """levels: band->0..1, body_map: band->motors, gains: band->0..1.5 (Gemma personalisation),
    motif: optional motor->intensity overlay (kaalam change, kalasham). Onsets get a 30% kick."""
    out = {m: 0.0 for m in MOTORS}
    for band, motors in body_map.items():
        v = levels.get(band, 0.0) * gains.get(band, 1.0) * (1.3 if onsets.get(band) else 1.0)
        for m in motors:
            if m in out:
                out[m] = max(out[m], v)
    ints = [min(max_int, int(out[m] * max_int)) for m in MOTORS]
    if motif:
        ints = [max(i, motif.get(m, 0)) for i, m in zip(ints, MOTORS)]
    return b"S" + bytes(ints)


class BandLink:
    def __init__(self, host: str, port: int):
        self.addr = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def send(self, frame: bytes) -> None:
        self.sock.sendto(frame, self.addr)
