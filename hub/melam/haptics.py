"""Act: send single-char commands back to nodes over UDP. Rate-limited per node."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, replace

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class HapticState:
    last_sent_s: dict[str, float]


def should_send(state: HapticState, node: str, now_s: float, min_gap_s: float) -> bool:
    return now_s - state.last_sent_s.get(node, -1e9) >= min_gap_s


def mark_sent(state: HapticState, node: str, now_s: float) -> HapticState:
    return replace(state, last_sent_s={**state.last_sent_s, node: now_s})


async def send(transport: asyncio.DatagramTransport, addr: tuple[str, int], node_port: int, cmd: str) -> None:
    transport.sendto(cmd.encode(), (addr[0], node_port))
    log.debug("-> %s:%d %s", addr[0], node_port, cmd)
