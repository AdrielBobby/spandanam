"""UDP ingest of node JSON samples. Immutable Sample records, async generator."""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Sample:
    node: str
    t_us: int
    ax: float
    ay: float
    az: float
    gx: float
    gy: float
    gz: float
    bpm: float
    addr: tuple[str, int]

    @property
    def accel_mag_g(self) -> float:
        return ((self.ax**2 + self.ay**2 + self.az**2) ** 0.5) / 9.81


def parse_sample(raw: bytes, addr: tuple[str, int]) -> Sample | None:
    try:
        d = json.loads(raw)
        return Sample(
            node=str(d["id"]), t_us=int(d["t"]),
            ax=float(d["ax"]), ay=float(d["ay"]), az=float(d["az"]),
            gx=float(d.get("gx", 0)), gy=float(d.get("gy", 0)), gz=float(d.get("gz", 0)),
            bpm=float(d.get("bpm", 0)), addr=addr,
        )
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        log.debug("bad packet from %s: %s", addr, e)
        return None


class _Proto(asyncio.DatagramProtocol):
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue

    def datagram_received(self, data: bytes, addr):
        s = parse_sample(data, addr)
        if s is not None:
            self.queue.put_nowait(s)


async def open_ingest(host: str, port: int) -> tuple[asyncio.Queue, asyncio.DatagramTransport]:
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue(maxsize=10_000)
    transport, _ = await loop.create_datagram_endpoint(lambda: _Proto(queue), local_addr=(host, port))
    log.info("listening on udp://%s:%d", host, port)
    return queue, transport
