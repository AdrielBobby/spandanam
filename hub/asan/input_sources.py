"""Input-source abstraction: normalizes any finger-input device to one event shape.

KeyboardSimulator stands in for the future five-IMU glove during laptop development.
A later MultiIMUReader implements the same InputSource protocol and yields the same
InputEvent shape, so nothing downstream needs to know which one it's talking to.
"""
from __future__ import annotations

import platform
import time
from dataclasses import dataclass
from typing import Iterator, Protocol

from .config import FINGERS

KEY_FINGER_MAP: dict[str, str] = dict(zip("12345", FINGERS))
QUIT_KEYS = {"q", "Q", "\x1b"}  # 'q'/'Q' or Escape


@dataclass(frozen=True)
class InputEvent:
    timestamp_ms: int
    finger: str
    source: str
    strength: float = 1.0

    def as_dict(self) -> dict:
        return {
            "timestamp_ms": self.timestamp_ms,
            "finger": self.finger,
            "source": self.source,
            "strength": self.strength,
        }


class InputSource(Protocol):
    def events(self) -> Iterator[InputEvent]: ...


def normalize_key(key: str, source: str = "keyboard_simulator", now_ms: int | None = None) -> InputEvent | None:
    """Map one raw key char to a normalized event, or None if it's not a finger key (1-5)."""
    finger = KEY_FINGER_MAP.get(key)
    if finger is None:
        return None
    ts = now_ms if now_ms is not None else int(time.monotonic() * 1000)
    return InputEvent(ts, finger, source, 1.0)


def is_quit_key(key: str) -> bool:
    return key in QUIT_KEYS


class KeyboardSimulator:
    """Windows console keyboard reader (msvcrt) standing in for the future 5-IMU glove."""

    SOURCE = "keyboard_simulator"

    def events(self) -> Iterator[InputEvent]:
        if platform.system() != "Windows":
            raise RuntimeError(
                "KeyboardSimulator uses Windows console input (msvcrt) and only runs on Windows. "
                "A cross-platform or hardware (MultiIMUReader) input adapter can be added later."
            )
        import msvcrt

        while True:
            ch = msvcrt.getwch()
            if is_quit_key(ch):
                return
            event = normalize_key(ch, self.SOURCE)
            if event is not None:
                yield event
