"""Non-interactive demo: fixed sample score results -> PracticeAnalysis printed as
JSON. No keyboard input, no clock, no Gemma/Gemini call."""
from __future__ import annotations

import json

from .analysis import analyze
from .input_sources import InputEvent
from .scheduler import build_schedule, score_events

PHRASE = ["dhim", "tha", "ka", "ta", "ki"]
TEMPO_BPM = 90


def sample_events() -> list[InputEvent]:
    """Same mixed example as scheduler_cli.py: one of each outcome except missed,
    which the "ki" beat gets by simply having no nearby event."""
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
    results = score_events(schedule, sample_events())
    analysis = analyze(results, PHRASE, TEMPO_BPM)
    print(json.dumps(analysis.as_dict(), indent=2))


if __name__ == "__main__":
    main()
