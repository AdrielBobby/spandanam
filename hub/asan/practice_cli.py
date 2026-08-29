"""Interactive Windows practice round: composes KeyboardSimulator's key-mapping
building blocks (normalize_key, is_quit_key, InputEvent) with the pure scheduler/
scorer to play one timed five-finger vaaythari phrase and print a result table.

Time-bounded key collection is done here (msvcrt.kbhit() polling), not in
input_sources.KeyboardSimulator, whose .events() generator blocks indefinitely on
msvcrt.getwch() and has no notion of a deadline.
"""
from __future__ import annotations

import argparse
import platform
import time
from typing import Sequence

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
from .scheduler import ExpectedEvent, TimingWindow, build_schedule, format_lanes, score_events

PHRASE = ["dhim", "tha", "ka", "ta", "ki"]
POLL_INTERVAL_S = 0.005  # 5ms: responsive enough, negligible CPU for a hackathon prototype


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
    ap.add_argument("--bpm", type=positive_bpm, default=60.0, help="tempo in beats per minute (must be > 0)")
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


def main() -> None:
    args = parse_args()
    window = TimingWindow()
    schedule = build_schedule(PHRASE, args.bpm, start_time_ms=args.lead_in_ms)

    print(f"Phrase {PHRASE} @ {args.bpm} bpm - 5 finger lanes (times include the {args.lead_in_ms}ms lead-in):")
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

    if quit_requested:
        print()
        print("Quit requested - round ended early.")


if __name__ == "__main__":
    main()
