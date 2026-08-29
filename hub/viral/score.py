"""Finger score: what to play. Immutable, JSON-friendly, shared by learn (from audio), compose (Gemini) and practice."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from .config import FINGER_COLORS, FINGERS


@dataclass(frozen=True)
class Note:
    beat: float          # position in beats from start
    finger: int          # 0..4
    velocity: float = 1.0
    label: str = ""      # vaaythari syllable or voice name


@dataclass(frozen=True)
class FingerMap:
    names: tuple[str, ...] = tuple(FINGERS)          # what each finger plays (voice name)
    colors: tuple[str, ...] = tuple(FINGER_COLORS)
    syllables: tuple[str, ...] = ("", "", "", "", "")


@dataclass(frozen=True)
class Score:
    title: str
    bpm: float
    beats_per_cycle: int          # thaalam cycle length (e.g. 8 for adi/chempada, 6 for panchari's base, 14 for thriputa)
    notes: tuple[Note, ...]
    finger_map: FingerMap = field(default_factory=FingerMap)
    kit: str = "chenda"
    thaalam: str = ""
    phrases: tuple[tuple[float, float], ...] = ()    # (start_beat, end_beat) practice segments

    @property
    def beat_s(self) -> float:
        return 60.0 / self.bpm

    @property
    def length_beats(self) -> float:
        return max((n.beat for n in self.notes), default=0.0) + 1.0

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    def slice(self, start_beat: float, end_beat: float) -> "Score":
        ns = tuple(Note(n.beat - start_beat, n.finger, n.velocity, n.label) for n in self.notes if start_beat <= n.beat < end_beat)
        return Score(self.title, self.bpm, self.beats_per_cycle, ns, self.finger_map, self.kit, self.thaalam, ())


def score_from_dict(d: dict) -> Score:
    notes = tuple(Note(float(n["beat"]), int(n["finger"]) % 5, float(n.get("velocity", 1.0)), str(n.get("label", "")))
                  for n in d.get("notes", []) if "beat" in n and "finger" in n)
    fm = d.get("finger_map", {})
    fmap = FingerMap(tuple(fm.get("names", FINGERS))[:5] or tuple(FINGERS),
                     tuple(fm.get("colors", FINGER_COLORS))[:5] or tuple(FINGER_COLORS),
                     tuple((fm.get("syllables") or ["", "", "", "", ""]))[:5])
    phrases = tuple((float(a), float(b)) for a, b in d.get("phrases", []))
    return Score(str(d.get("title", "untitled")), float(d.get("bpm", 90)), int(d.get("beats_per_cycle", 8)),
                 tuple(sorted(notes, key=lambda n: n.beat)), fmap, str(d.get("kit", "chenda")), str(d.get("thaalam", "")), phrases)


def quantize(beats: list[float], grid: float = 0.25) -> list[float]:
    return [round(b / grid) * grid for b in beats]
