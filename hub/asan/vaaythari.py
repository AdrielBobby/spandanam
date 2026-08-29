"""Phrase model: syllables -> hands, timing, haptic tap schedule, and diffing what was played vs what was asked."""
from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from .config import ACCENT_SYLLABLES, SYLLABLES


@dataclass(frozen=True)
class Phrase:
    syllables: tuple[str, ...]
    bpm: float

    @property
    def beat_s(self) -> float:
        return 60.0 / self.bpm

    @property
    def duration_s(self) -> float:
        return self.beat_s * len(self.syllables)

    def text(self) -> str:
        return "-".join(self.syllables)


@dataclass(frozen=True)
class Tap:
    t_s: float
    zone: str
    strength: float


def tap_schedule(p: Phrase) -> tuple[Tap, ...]:
    """One buzzer pulse per syllable: hand zone, plus the accent buzzer on dhim/thom."""
    taps = []
    for i, s in enumerate(p.syllables):
        t = i * p.beat_s
        taps.append(Tap(t, SYLLABLES.get(s, "right"), 1.0))
        if s in ACCENT_SYLLABLES:
            taps.append(Tap(t, "accent", 1.0))
    return tuple(taps)


def validate_syllables(syls: list[str]) -> tuple[str, ...]:
    return tuple(s for s in syls if s in SYLLABLES)


@dataclass(frozen=True)
class Diff:
    similarity: float           # 0..1
    missing: tuple[str, ...]
    extra: tuple[str, ...]
    swapped: tuple[tuple[str, str], ...]


def diff_phrase(asked: tuple[str, ...], played: tuple[str, ...]) -> Diff:
    sm = SequenceMatcher(a=asked, b=played)
    missing, extra, swapped = [], [], []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "delete": missing += asked[i1:i2]
        elif op == "insert": extra += played[j1:j2]
        elif op == "replace":
            swapped += list(zip(asked[i1:i2], played[j1:j2]))
            missing += asked[i1 + (j2 - j1):i2]; extra += played[j1 + (i2 - i1):j2]
    return Diff(sm.ratio(), tuple(missing), tuple(extra), tuple(swapped))
