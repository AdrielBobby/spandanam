"""Pure helpers for the interactive practice round: everything here is testable
without a keyboard, a real clock, or the console — the interactive parts (countdown,
key polling, printing) live in practice_cli.py and call into this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .input_sources import KEY_FINGER_MAP, InputEvent
from .scheduler import ExpectedEvent, Outcome, ScoreResult, TimingWindow

FINGER_KEY_MAP: dict[str, str] = {finger: key for key, finger in KEY_FINGER_MAP.items()}


def collection_window_ms(schedule: Sequence[ExpectedEvent], window: TimingWindow, tail_ms: int = 500) -> int:
    """How long (ms) after round start to keep collecting taps: the last beat's
    expected time + the timing acceptance window + a small tail, so a late tap on
    the final beat still has a chance to be scored. Requires a non-empty schedule —
    there's no meaningful collection window for zero expected beats."""
    if not schedule:
        raise ValueError("collection_window_ms requires a non-empty schedule")
    last = schedule[-1]
    return last.expected_time_ms + window.accept_ms + tail_ms


def to_relative_event(event: InputEvent, start_time_ms: int) -> InputEvent:
    """Rebase an InputEvent's absolute timestamp_ms to be relative to start_time_ms,
    preserving finger, source, and strength exactly."""
    return InputEvent(event.timestamp_ms - start_time_ms, event.finger, event.source, event.strength)


@dataclass(frozen=True)
class Summary:
    total_expected: int
    correct_on_time: int
    correct_early: int
    correct_late: int
    wrong_finger: int
    missed: int
    extra: int
    accepted_accuracy_pct: float

    def as_dict(self) -> dict:
        return {
            "total_expected": self.total_expected,
            "correct_on_time": self.correct_on_time,
            "correct_early": self.correct_early,
            "correct_late": self.correct_late,
            "wrong_finger": self.wrong_finger,
            "missed": self.missed,
            "extra": self.extra,
            "accepted_accuracy_pct": self.accepted_accuracy_pct,
        }


def summarize(results: Sequence[ScoreResult]) -> Summary:
    """Count each outcome and compute accepted accuracy = (on_time+early+late)/total_expected*100.
    total_expected is the number of results tied to an expected beat (i.e. everything
    except EXTRA); accuracy is 0.0 when there were no expected beats at all."""
    counts = {outcome: 0 for outcome in Outcome}
    for r in results:
        counts[r.outcome] += 1

    correct_on_time = counts[Outcome.CORRECT_ON_TIME]
    correct_early = counts[Outcome.CORRECT_EARLY]
    correct_late = counts[Outcome.CORRECT_LATE]
    wrong_finger = counts[Outcome.WRONG_FINGER]
    missed = counts[Outcome.MISSED]
    extra = counts[Outcome.EXTRA]

    total_expected = correct_on_time + correct_early + correct_late + wrong_finger + missed
    accepted = correct_on_time + correct_early + correct_late
    accuracy = (accepted / total_expected * 100) if total_expected else 0.0

    return Summary(total_expected, correct_on_time, correct_early, correct_late, wrong_finger, missed, extra, accuracy)


def cue_time_ms(event: ExpectedEvent, cue_advance_ms: int) -> int:
    """When (ms, relative to round start) to fire the PREPARE cue for this beat:
    max(0, expected_time_ms - cue_advance_ms) — never negative, and never later than
    the beat's own scoring target. Does not change expected_time_ms itself."""
    if cue_advance_ms < 0:
        raise ValueError(f"cue_advance_ms must be >= 0, got {cue_advance_ms}")
    return max(0, event.expected_time_ms - cue_advance_ms)


def format_prepare_cue(event: ExpectedEvent, finger_key: dict[str, str] = FINGER_KEY_MAP) -> str:
    """Early warning cue, e.g. 'PREPARE -> THUMB  [1]  dhim', printed cue_advance_ms
    before the beat's scoring target so the user has reaction time. Raises ValueError
    if event.finger has no entry in finger_key, rather than printing e.g. '[None]'."""
    if event.finger not in finger_key:
        raise ValueError(f"no key mapped for finger {event.finger!r} (not in FINGER_KEY_MAP)")
    key = finger_key[event.finger]
    return f"PREPARE -> {event.finger.upper():<6} [{key}]  {event.bol}"


def format_cue(event: ExpectedEvent, finger_key: dict[str, str] = FINGER_KEY_MAP) -> str:
    """On-beat cue at the scoring target itself, e.g. '>>> HIT NOW -> THUMB  [1]  dhim'
    — the '>>> ' prefix makes it visually distinct from the earlier PREPARE cue, since
    this is the moment the user should actually press the key. Laptop-only stand-in
    for the future per-finger LED + buzzer cue. Raises ValueError if event.finger has
    no entry in finger_key, rather than printing e.g. '[None]'."""
    if event.finger not in finger_key:
        raise ValueError(f"no key mapped for finger {event.finger!r} (not in FINGER_KEY_MAP)")
    key = finger_key[event.finger]
    return f">>> HIT NOW -> {event.finger.upper():<6} [{key}]  {event.bol}"


def format_result_table(results: Sequence[ScoreResult]) -> str:
    """One row per expected beat (schedule order: beat, bol, expected finger, expected
    time, actual finger/time, timing error, outcome), followed by any EXTRA taps."""
    header = f"{'beat':>4} {'bol':<6} {'exp_finger':<10} {'exp_ms':>7} {'act_finger':<10} {'act_ms':>7} {'err_ms':>7} outcome"
    lines = [header]
    for r in results:
        if r.expected is not None:
            beat = str(r.expected.beat_index)
            bol = r.expected.bol
            exp_finger = r.expected.finger
            exp_ms = str(r.expected.expected_time_ms)
        else:
            beat = bol = exp_finger = exp_ms = "-"
        if r.actual is not None:
            act_finger = r.actual.finger
            act_ms = str(r.actual.timestamp_ms)
        else:
            act_finger = act_ms = "-"
        err_ms = str(r.timing_error_ms) if r.timing_error_ms is not None else "-"
        lines.append(
            f"{beat:>4} {bol:<6} {exp_finger:<10} {exp_ms:>7} {act_finger:<10} {act_ms:>7} {err_ms:>7} {r.outcome.value}"
        )
    return "\n".join(lines)
