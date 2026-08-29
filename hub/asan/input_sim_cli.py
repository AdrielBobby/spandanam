"""Manual demo: press 1-5 to emit a finger-tap event, q/Esc to quit. Windows console only."""
from __future__ import annotations

import json

from .input_sources import KeyboardSimulator


def main() -> None:
    print("Five-finger keyboard simulator — 1 thumb, 2 index, 3 middle, 4 ring, 5 pinky, q/Esc to quit.")
    for event in KeyboardSimulator().events():
        print(json.dumps(event.as_dict()))


if __name__ == "__main__":
    main()
