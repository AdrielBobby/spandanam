"""Free-flow tempo on the fingers: buzz the beat, LED the downbeat. Pure schedule + a tiny runner."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class Click:
    beat: int
    downbeat: bool
    finger: int


def click_pattern(beats_per_cycle: int, mode: str = "all") -> list[Click]:
    """'all' = every finger buzzes each beat; 'walk' = beat walks thumb→pinky; 'downbeat' = thumb only on 1."""
    out = []
    for b in range(beats_per_cycle):
        if mode == "walk":
            out.append(Click(b, b == 0, b % 5))
        elif mode == "downbeat":
            if b == 0: out.append(Click(b, True, 0))
        else:
            out += [Click(b, b == 0, f) for f in range(5)]
    return out


async def run_metronome(bpm: float, beats_per_cycle: int, mode: str, on_click, stop: asyncio.Event) -> None:
    pattern = click_pattern(beats_per_cycle, mode)
    beat_s = 60.0 / bpm
    t0 = time.monotonic(); b = 0
    while not stop.is_set():
        target = t0 + b * beat_s
        await asyncio.sleep(max(0.0, target - time.monotonic()))
        for c in pattern:
            if c.beat == b % beats_per_cycle:
                on_click(c)
        b += 1
