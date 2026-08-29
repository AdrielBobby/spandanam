"""Pure five-finger exercise scheduler and scorer.

Turns a requested vaaythari phrase into an ordered schedule of expected finger-tap
events (one per beat), and scores a batch of InputEvents against it. No clock, IO,
or hardware access: callers pass start_time_ms and already-captured InputEvents.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from .config import FINGERS, SYLLABLE_FINGER
from .input_sources import InputEvent


class UnsupportedSyllableError(ValueError):
    """Raised by build_schedule() when a bol has no entry in config.SYLLABLE_FINGER."""


class Outcome(str, Enum):
    CORRECT_ON_TIME = "correct_on_time"
    CORRECT_EARLY = "correct_early"
    CORRECT_LATE = "correct_late"
    WRONG_FINGER = "wrong_finger"
    MISSED = "missed"
    EXTRA = "extra"


@dataclass(frozen=True)
class TimingWindow:
    on_time_ms: int = 120
    accept_ms: int = 300

    def __post_init__(self) -> None:
        if self.on_time_ms < 0:
            raise ValueError(f"on_time_ms must be >= 0, got {self.on_time_ms}")
        if self.accept_ms <= 0:
            raise ValueError(f"accept_ms must be > 0, got {self.accept_ms}")
        if self.on_time_ms > self.accept_ms:
            raise ValueError(
                f"on_time_ms ({self.on_time_ms}) must be <= accept_ms ({self.accept_ms})"
            )


@dataclass(frozen=True)
class ExpectedEvent:
    beat_index: int
    bol: str
    finger: str
    expected_time_ms: int
    duration_ms: int  # == beat_duration_ms for this schedule

    def as_dict(self) -> dict:
        return {
            "beat_index": self.beat_index,
            "bol": self.bol,
            "finger": self.finger,
            "expected_time_ms": self.expected_time_ms,
            "duration_ms": self.duration_ms,
        }


@dataclass(frozen=True)
class ScoreResult:
    expected: ExpectedEvent | None
    actual: InputEvent | None
    outcome: Outcome
    timing_error_ms: int | None  # actual.timestamp_ms - expected.expected_time_ms; None for missed/extra

    def as_dict(self) -> dict:
        return {
            "expected": self.expected.as_dict() if self.expected is not None else None,
            "actual": self.actual.as_dict() if self.actual is not None else None,
            "outcome": self.outcome.value,
            "timing_error_ms": self.timing_error_ms,
        }


def beat_duration_ms(tempo_bpm: float) -> int:
    return round(60000 / tempo_bpm)


def build_schedule(phrase: Sequence[str], tempo_bpm: float, start_time_ms: int = 0) -> tuple[ExpectedEvent, ...]:
    """One ExpectedEvent per bol, in order. Raises UnsupportedSyllableError for any bol
    not present in config.SYLLABLE_FINGER."""
    bd = beat_duration_ms(tempo_bpm)
    schedule = []
    for i, bol in enumerate(phrase):
        finger = SYLLABLE_FINGER.get(bol)
        if finger is None:
            raise UnsupportedSyllableError(
                f"unsupported syllable {bol!r} at index {i} (not in config.SYLLABLE_FINGER)"
            )
        schedule.append(ExpectedEvent(i, bol, finger, start_time_ms + i * bd, bd))
    return tuple(schedule)


def score_events(
    schedule: Sequence[ExpectedEvent],
    events: Sequence[InputEvent],
    window: TimingWindow = TimingWindow(),
) -> tuple[ScoreResult, ...]:
    """One ScoreResult per expected event (schedule order), then one ScoreResult per
    unmatched actual event (original order, outcome=EXTRA).

    Matching is global nearest-pair-first: every (expected, actual) pair within
    window.accept_ms is a candidate, sorted by smallest timing error first, and
    greedily accepted only while both sides are still unclaimed. This avoids
    arrival-order bias (a later, closer tap losing a beat to an earlier, worse one).
    """
    schedule = list(schedule)
    events = list(events)

    candidates = []
    for ei, exp in enumerate(schedule):
        for ai, act in enumerate(events):
            delta = act.timestamp_ms - exp.expected_time_ms
            if abs(delta) <= window.accept_ms:
                candidates.append((abs(delta), exp.expected_time_ms, act.timestamp_ms, ei, ai, delta))
    candidates.sort(key=lambda c: (c[0], c[1], c[2]))

    claimed_expected: dict[int, tuple[int, int]] = {}  # ei -> (ai, delta)
    claimed_actual: set[int] = set()
    for _, _, _, ei, ai, delta in candidates:
        if ei in claimed_expected or ai in claimed_actual:
            continue
        claimed_expected[ei] = (ai, delta)
        claimed_actual.add(ai)

    results: list[ScoreResult] = []
    for ei, exp in enumerate(schedule):
        if ei not in claimed_expected:
            results.append(ScoreResult(exp, None, Outcome.MISSED, None))
            continue
        ai, delta = claimed_expected[ei]
        act = events[ai]
        if act.finger == exp.finger:
            if abs(delta) <= window.on_time_ms:
                outcome = Outcome.CORRECT_ON_TIME
            elif delta < 0:
                outcome = Outcome.CORRECT_EARLY
            else:
                outcome = Outcome.CORRECT_LATE
        else:
            outcome = Outcome.WRONG_FINGER
        results.append(ScoreResult(exp, act, outcome, delta))

    for ai, act in enumerate(events):
        if ai not in claimed_actual:
            results.append(ScoreResult(None, act, Outcome.EXTRA, None))

    return tuple(results)


def format_lanes(schedule: Sequence[ExpectedEvent]) -> str:
    """One line per finger in config.FINGERS order, listing that finger's (bol,
    expected_time_ms) pairs in beat order."""
    by_finger: dict[str, list[ExpectedEvent]] = {f: [] for f in FINGERS}
    for exp in schedule:
        by_finger[exp.finger].append(exp)
    lines = []
    for finger in FINGERS:
        taps = by_finger[finger]
        taps_str = ", ".join(f"{e.bol}@{e.expected_time_ms}ms" for e in taps) if taps else "(no taps)"
        lines.append(f"{finger:>6}: {taps_str}")
    return "\n".join(lines)
