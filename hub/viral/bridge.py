"""Bridge between Adriel's pure scheduler/analysis layer (hub/asan) and the Viralthaalam server/Gemma pipeline (hub/viral).

- phrase_to_score(): a vaaythari phrase (["dhim","tha","ka",...]) -> practice Score using asan.config.SYLLABLE_FINGER.
- analysis_for_coach(): asan.analysis.PracticeAnalysis (deterministic facts) -> the dict Gemma's coach() explains.
  Gemma never computes the facts; it only turns them into teaching language. That is the whole point of the split.
"""
from __future__ import annotations

from asan.analysis import PracticeAnalysis
from asan.config import FINGERS as FINGER_NAMES
from asan.config import SYLLABLE_FINGER

from .config import FINGER_COLORS
from .score import FingerMap, Note, Score

FINGER_INDEX = {name: i for i, name in enumerate(FINGER_NAMES)}


def finger_syllables() -> tuple[str, ...]:
    """One representative syllable per finger, derived from SYLLABLE_FINGER (first seen wins)."""
    out: dict[str, str] = {}
    for syl, finger in SYLLABLE_FINGER.items():
        out.setdefault(finger, syl)
    return tuple(out.get(f, "") for f in FINGER_NAMES)


def phrase_to_score(phrase: list[str], bpm: float, title: str = "vaaythari", cycles: int = 1, kit: str = "chenda") -> Score:
    unknown = [s for s in phrase if s not in SYLLABLE_FINGER]
    if unknown:
        raise ValueError(f"unsupported syllables: {unknown}")
    notes = tuple(Note(float(c * len(phrase) + i), FINGER_INDEX[SYLLABLE_FINGER[s]], 1.0, s)
                  for c in range(cycles) for i, s in enumerate(phrase))
    fmap = FingerMap(tuple(FINGER_NAMES), tuple(FINGER_COLORS), finger_syllables())
    n = len(phrase)
    phrases = tuple((float(c * n), float((c + 1) * n)) for c in range(cycles))
    return Score(title, bpm, n, notes, fmap, kit, f"{'-'.join(phrase)} ({n})", phrases)


def analysis_for_coach(a: PracticeAnalysis, bpm: float) -> dict:
    """Flatten deterministic facts into the summary Gemma's coach() receives."""
    return {
        "accuracy": round(a.accepted_accuracy_pct / 100, 3),
        "notes": a.total_expected,
        "weak_fingers": list(a.weak_fingers),
        "weak_syllables": list(a.weak_bols),
        "dominant_error": a.dominant_error,
        "recommended_bpm": a.recommended_tempo_bpm,
        "recommended_phrase": list(a.recommended_phrase),
        "current_bpm": bpm,
        "facts": a.deterministic_feedback,
    }
