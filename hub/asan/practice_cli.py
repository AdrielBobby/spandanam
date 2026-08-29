"""Interactive Windows practice round: composes KeyboardSimulator's key-mapping
building blocks (normalize_key, is_quit_key, InputEvent) with the pure scheduler/
scorer to play one timed five-finger vaaythari phrase and print a result table.

Time-bounded key collection is done here (msvcrt.kbhit() polling), not in
input_sources.KeyboardSimulator, whose .events() generator blocks indefinitely on
msvcrt.getwch() and has no notion of a deadline.
"""
from __future__ import annotations

import argparse
import json
import platform
import time
from datetime import datetime
from pathlib import Path
from typing import Sequence

from .analysis import PracticeAnalysis, analyze
from .input_sources import InputEvent, KeyboardSimulator, is_quit_key, normalize_key
from .practice import (
    collection_window_ms,
    cue_time_ms,
    format_cue,
    format_prepare_cue,
    format_result_table,
    summarize,
    to_relative_event,
)
from .lessons import load_lesson
from .scheduler import ExpectedEvent, ScoreResult, TimingWindow, beat_duration_ms, format_lanes, score_events

DEFAULT_LESSON_ID = "vaaythari_basic_1"
POLL_INTERVAL_S = 0.005  # 5ms: responsive enough, negligible CPU for a hackathon prototype

# repo_root/logs/practice.jsonl — one JSON line per completed round, read by dashboard/server.py.
LOG_PATH = Path(__file__).resolve().parents[2] / "logs" / "practice.jsonl"


def build_lesson_schedule(
    phrase: Sequence[str], finger_map: dict[str, str], tempo_bpm: float, start_time_ms: int = 0
) -> tuple[ExpectedEvent, ...]:
    """Build the expected-event schedule for a lesson, sourcing each bol's finger from
    the lesson's own finger_map (already validated by lessons.load_lesson) instead of
    the global config.SYLLABLE_FINGER that scheduler.build_schedule() uses — this is
    what lets each lesson define its own bol-to-finger mapping."""
    bd = beat_duration_ms(tempo_bpm)
    return tuple(
        ExpectedEvent(i, bol, finger_map[bol], start_time_ms + i * bd, bd)
        for i, bol in enumerate(phrase)
    )


def positive_bpm(value: str) -> float:
    v = float(value)
    if v <= 0:
        raise argparse.ArgumentTypeError(f"--bpm must be > 0, got {value!r}")
    return v


def non_negative_countdown(value: str) -> int:
    v = int(value)
    if v < 0:
        raise argparse.ArgumentTypeError(f"--countdown must be >= 0, got {value!r}")
    return v


def non_negative_lead_in_ms(value: str) -> int:
    v = int(value)
    if v < 0:
        raise argparse.ArgumentTypeError(f"--lead-in-ms must be >= 0, got {value!r}")
    return v


def non_negative_cue_advance_ms(value: str) -> int:
    v = int(value)
    if v < 0:
        raise argparse.ArgumentTypeError(f"--cue-advance-ms must be >= 0, got {value!r}")
    return v


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Interactive five-finger vaaythari practice round (Windows console).")
    ap.add_argument(
        "--lesson",
        default=DEFAULT_LESSON_ID,
        help=f"lesson id to load from content/lessons/ (default: {DEFAULT_LESSON_ID!r})",
    )
    ap.add_argument(
        "--bpm",
        type=positive_bpm,
        default=None,
        help="tempo in beats per minute (must be > 0); defaults to the selected lesson's tempo_bpm if omitted",
    )
    ap.add_argument("--countdown", type=non_negative_countdown, default=3, help="countdown seconds (must be >= 0)")
    ap.add_argument(
        "--lead-in-ms",
        type=non_negative_lead_in_ms,
        default=750,
        help="milliseconds after 'Go!' before the first beat's scoring target (must be >= 0, default 750)",
    )
    ap.add_argument(
        "--cue-advance-ms",
        type=non_negative_cue_advance_ms,
        default=450,
        help=(
            "milliseconds before each beat's target that the early 'PREPARE' cue fires, giving reaction "
            "time before the '>>> HIT NOW' cue on the beat itself (must be >= 0, default 450)"
        ),
    )
    return ap.parse_args(argv)


def _require_windows() -> None:
    if platform.system() != "Windows":
        raise RuntimeError(
            "practice_cli requires Windows console input (msvcrt) and only runs on Windows. "
            "A cross-platform or hardware input adapter can be added later."
        )


def run_countdown(seconds: int) -> bool:
    """Print a countdown, polling for quit throughout. Returns True if q/Esc was pressed."""
    _require_windows()
    import msvcrt

    for remaining in range(seconds, 0, -1):
        print(f"{remaining}...", flush=True)
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            if msvcrt.kbhit():
                if is_quit_key(msvcrt.getwch()):
                    return True
            else:
                time.sleep(POLL_INTERVAL_S)
    print("Go!", flush=True)
    return False


def collect_events(
    schedule: Sequence[ExpectedEvent], window_ms: int, start_time_ms: int, cue_advance_ms: int
) -> tuple[list[InputEvent], bool]:
    """Poll the console for finger-key presses for window_ms (measured from
    start_time_ms), printing two live cues per beat as they come due — an early
    'PREPARE' at cue_time_ms() and the on-beat '>>> HIT NOW' at expected_time_ms —
    the laptop-only stand-in for the future per-finger LED + buzzer cue.
    Returns (events with ABSOLUTE monotonic-ms timestamps, quit_requested)."""
    _require_windows()
    import msvcrt

    events: list[InputEvent] = []
    quit_requested = False
    next_prepare = 0
    next_hit = 0
    while True:
        elapsed_ms = int(time.monotonic() * 1000) - start_time_ms
        if elapsed_ms >= window_ms:
            break
        while next_prepare < len(schedule) and cue_time_ms(schedule[next_prepare], cue_advance_ms) <= elapsed_ms:
            print(format_prepare_cue(schedule[next_prepare]), flush=True)
            next_prepare += 1
        while next_hit < len(schedule) and schedule[next_hit].expected_time_ms <= elapsed_ms:
            print(format_cue(schedule[next_hit]), flush=True)
            next_hit += 1
        if not msvcrt.kbhit():
            time.sleep(POLL_INTERVAL_S)
            continue
        ch = msvcrt.getwch()
        now_ms = int(time.monotonic() * 1000)
        if is_quit_key(ch):
            quit_requested = True
            break
        event = normalize_key(ch, KeyboardSimulator.SOURCE, now_ms)
        if event is not None:
            events.append(event)
    return events, quit_requested


def build_log_entry(
    results: Sequence[ScoreResult],
    phrase: Sequence[str],
    tempo_bpm: float,
    analysis: PracticeAnalysis,
    now: datetime | None = None,
) -> dict:
    """Build one JSONL log entry from a completed round's results, phrase, tempo, and
    coaching analysis. Pure and deterministic given `now`; no file or clock access
    unless now is omitted (defaults to the local current time)."""
    now = now if now is not None else datetime.now().astimezone()
    summary = summarize(results).as_dict()
    analysis_dict = analysis.as_dict()
    beats = [
        {
            "index": r.expected.beat_index,
            "bol": r.expected.bol,
            "expected_finger": r.expected.finger,
            "expected_ms": r.expected.expected_time_ms,
            "actual_finger": r.actual.finger if r.actual is not None else None,
            "actual_ms": r.actual.timestamp_ms if r.actual is not None else None,
            "error_ms": r.timing_error_ms,
            "outcome": r.outcome.value,
        }
        for r in results
        if r.expected is not None
    ]
    return {
        "timestamp": now.isoformat(),
        "session_id": now.date().isoformat(),
        "phrase": list(phrase),
        "tempo_bpm": tempo_bpm,
        "summary": {
            **summary,
            "dominant_error": analysis_dict["dominant_error"],
            "weak_fingers": analysis_dict["weak_fingers"],
            "weak_bols": analysis_dict["weak_bols"],
            "recommended_tempo_bpm": analysis_dict["recommended_tempo_bpm"],
            "recommended_phrase": analysis_dict["recommended_phrase"],
        },
        "beats": beats,
    }


def append_log_entry(entry: dict, path: Path = LOG_PATH) -> None:
    """Append one JSON line to path, creating its parent directory if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def main() -> None:
    args = parse_args()
    lesson = load_lesson(args.lesson)
    phrase = lesson["phrase"]
    finger_map = lesson["finger_map"]
    tempo_bpm = args.bpm if args.bpm is not None else lesson["tempo_bpm"]

    window = TimingWindow()
    schedule = build_lesson_schedule(phrase, finger_map, tempo_bpm, start_time_ms=args.lead_in_ms)

    print(
        f"Lesson {lesson['id']!r} ({lesson['name']}) - phrase {phrase} @ {tempo_bpm} bpm - "
        f"5 finger lanes (times include the {args.lead_in_ms}ms lead-in):"
    )
    print(format_lanes(schedule))
    print()
    print("Keys: 1=thumb  2=index  3=middle  4=ring  5=pinky   q/Esc=quit")
    print("Each beat prints two cues: 'PREPARE -> FINGER [key] bol' gives you a heads-up,")
    print("then '>>> HIT NOW -> FINGER [key] bol' marks the moment to actually press the key.")
    print(f"PREPARE fires {args.cue_advance_ms}ms before HIT NOW. First HIT NOW is {args.lead_in_ms}ms after 'Go!'.")
    print()

    if run_countdown(args.countdown):
        print("Quit before the round started.")
        return

    start_time_ms = int(time.monotonic() * 1000)
    window_ms = collection_window_ms(schedule, window)
    raw_events, quit_requested = collect_events(schedule, window_ms, start_time_ms, args.cue_advance_ms)
    relative_events = [to_relative_event(e, start_time_ms) for e in raw_events]
    results = score_events(schedule, relative_events, window)

    print()
    print(format_result_table(results))
    print()
    for key, value in summarize(results).as_dict().items():
        print(f"{key}: {value}")

    analysis = analyze(results, phrase, tempo_bpm)
    print()
    print("=== Coaching ===")
    print(analysis.deterministic_feedback)
    print(f"Next tempo: {analysis.recommended_tempo_bpm} bpm")
    print(f"Practice phrase: {'-'.join(analysis.recommended_phrase)}")
    if analysis.weak_fingers:
        print(f"Weak fingers: {', '.join(analysis.weak_fingers)}")
    if analysis.weak_bols:
        print(f"Weak bols: {', '.join(analysis.weak_bols)}")

    append_log_entry(build_log_entry(results, phrase, tempo_bpm, analysis))

    if quit_requested:
        print()
        print("Quit requested - round ended early.")


if __name__ == "__main__":
    main()
