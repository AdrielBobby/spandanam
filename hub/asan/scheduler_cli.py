"""Non-interactive demo: build a fixed phrase's schedule, print the 5 finger lanes,
score a small hard-coded set of example taps against it, print the results."""
from __future__ import annotations

import json

from .input_sources import InputEvent
from .scheduler import build_schedule, format_lanes, score_events

PHRASE = ["dhim", "tha", "ka", "ta", "ki"]
TEMPO_BPM = 90


def example_events() -> list[InputEvent]:
    """One example of each outcome: on-time, early, late, wrong-finger, missed (no
    event given for the "ki" beat), and one extra tap far from every beat."""
    return [
        InputEvent(10, "thumb", "keyboard_simulator", 1.0),    # beat0 dhim@0ms   -> correct_on_time
        InputEvent(467, "index", "keyboard_simulator", 1.0),   # beat1 tha@667ms  -> correct_early
        InputEvent(1584, "ring", "keyboard_simulator", 1.0),   # beat2 ka@1334ms  -> correct_late
        InputEvent(2001, "pinky", "keyboard_simulator", 1.0),  # beat3 ta@2001ms  -> wrong_finger (expected middle)
        # beat4 ki@2668ms (ring) gets nothing nearby -> missed
        InputEvent(5000, "thumb", "keyboard_simulator", 1.0),  # far from every beat -> extra
    ]


def main() -> None:
    schedule = build_schedule(PHRASE, TEMPO_BPM)
    print(f"Phrase {PHRASE} @ {TEMPO_BPM} bpm - 5 finger lanes:")
    print(format_lanes(schedule))
    print()
    print("Scoring example taps:")
    for result in score_events(schedule, example_events()):
        print(json.dumps(result.as_dict()))


if __name__ == "__main__":
    main()
