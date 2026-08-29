"""Deterministic post-round coaching analysis.

Turns completed ScoreResult objects into a structured PracticeAnalysis: reliable,
computed facts (weak fingers/bols, dominant error type, a recommended next tempo and
phrase, and a plain-English summary built only from those facts) for Gemma to explain
later. Pure Python only: no clock, keyboard, hardware, file, network, or model access.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

from .practice import summarize
from .scheduler import Outcome, ScoreResult

DominantError = Literal["early", "late", "wrong_finger", "missed", "extra", "none"]

_SEVERITY_WEIGHT: dict[Outcome, int] = {
    Outcome.CORRECT_ON_TIME: 0,
    Outcome.CORRECT_EARLY: 1,
    Outcome.CORRECT_LATE: 1,
    Outcome.WRONG_FINGER: 3,
    Outcome.MISSED: 3,
    # Outcome.EXTRA intentionally absent: extra taps have no expected event and never
    # count toward a finger's or bol's weakness score.
}

_DOMINANT_PRIORITY: tuple[str, ...] = ("missed", "wrong_finger", "late", "early", "extra")

_ERROR_LABELS: dict[str, str] = {
    "early": "early taps",
    "late": "late taps",
    "wrong_finger": "wrong-finger taps",
    "missed": "missed beats",
    "extra": "extra taps",
}

_MIN_TEMPO_BPM = 40
_MAX_TEMPO_BPM = 120


@dataclass(frozen=True)
class PracticeAnalysis:
    accepted_accuracy_pct: float
    total_expected: int
    weak_fingers: tuple[str, ...]
    weak_bols: tuple[str, ...]
    dominant_error: DominantError
    recommended_tempo_bpm: int
    recommended_phrase: tuple[str, ...]
    deterministic_feedback: str

    def as_dict(self) -> dict:
        return {
            "accepted_accuracy_pct": self.accepted_accuracy_pct,
            "total_expected": self.total_expected,
            "weak_fingers": list(self.weak_fingers),
            "weak_bols": list(self.weak_bols),
            "dominant_error": self.dominant_error,
            "recommended_tempo_bpm": self.recommended_tempo_bpm,
            "recommended_phrase": list(self.recommended_phrase),
            "deterministic_feedback": self.deterministic_feedback,
        }


def _rank_weaknesses(results: Sequence[ScoreResult]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Sum severity weight per expected finger/bol (skipping EXTRA results, which have
    no expected event); rank descending by weight, ties broken by first occurrence in
    results order; drop zero-weight entries. Returns (weak_fingers, weak_bols)."""
    finger_score: dict[str, int] = {}
    finger_first_seen: dict[str, int] = {}
    bol_score: dict[str, int] = {}
    bol_first_seen: dict[str, int] = {}

    for i, r in enumerate(results):
        if r.expected is None:
            continue
        weight = _SEVERITY_WEIGHT.get(r.outcome, 0)
        finger, bol = r.expected.finger, r.expected.bol
        finger_score[finger] = finger_score.get(finger, 0) + weight
        finger_first_seen.setdefault(finger, i)
        bol_score[bol] = bol_score.get(bol, 0) + weight
        bol_first_seen.setdefault(bol, i)

    def _rank(score: dict[str, int], first_seen: dict[str, int]) -> tuple[str, ...]:
        names = [name for name, s in score.items() if s > 0]
        names.sort(key=lambda name: (-score[name], first_seen[name]))
        return tuple(names)

    return _rank(finger_score, finger_first_seen), _rank(bol_score, bol_first_seen)


def _dominant_error(results: Sequence[ScoreResult]) -> DominantError:
    """Most frequent of early/late/wrong_finger/missed/extra (correct_on_time ignored);
    ties broken by priority missed > wrong_finger > late > early > extra. "none" only
    if every count is zero (all expected events correct_on_time, no extras)."""
    counts = {name: 0 for name in _DOMINANT_PRIORITY}
    for r in results:
        if r.outcome == Outcome.CORRECT_EARLY:
            counts["early"] += 1
        elif r.outcome == Outcome.CORRECT_LATE:
            counts["late"] += 1
        elif r.outcome == Outcome.WRONG_FINGER:
            counts["wrong_finger"] += 1
        elif r.outcome == Outcome.MISSED:
            counts["missed"] += 1
        elif r.outcome == Outcome.EXTRA:
            counts["extra"] += 1

    if all(count == 0 for count in counts.values()):
        return "none"
    max_count = max(counts.values())
    for category in _DOMINANT_PRIORITY:
        if counts[category] == max_count:
            return category  # type: ignore[return-value]
    raise AssertionError("unreachable: _DOMINANT_PRIORITY covers every counted category")


def _recommended_tempo(current_tempo_bpm: float, accepted_accuracy_pct: float, dominant_error: DominantError) -> int:
    if accepted_accuracy_pct < 60:
        tempo = current_tempo_bpm - 20
    elif accepted_accuracy_pct < 80:
        tempo = current_tempo_bpm - 10
    elif accepted_accuracy_pct < 95:
        tempo = current_tempo_bpm
    elif dominant_error == "none":
        tempo = current_tempo_bpm + 5
    else:
        tempo = current_tempo_bpm
    return int(round(min(_MAX_TEMPO_BPM, max(_MIN_TEMPO_BPM, tempo))))


def _recommended_phrase(weak_bols: tuple[str, ...], phrase: Sequence[str]) -> tuple[str, ...]:
    if weak_bols:
        return tuple(weak_bols[:3])
    return tuple(phrase[:5])


def _feedback(
    results_count: int,
    accepted_accuracy_pct: float,
    weak_fingers: tuple[str, ...],
    weak_bols: tuple[str, ...],
    dominant_error: DominantError,
    recommended_tempo_bpm: int,
    recommended_phrase: tuple[str, ...],
) -> str:
    if results_count == 0:
        return "No beats were captured this round, so there is nothing to analyze yet."

    phrase_text = "-".join(recommended_phrase) if recommended_phrase else "(none)"
    plan = f"Next tempo {recommended_tempo_bpm} bpm, practice phrase {phrase_text}."

    if dominant_error == "none" and not weak_fingers:
        return f"Perfect round at {accepted_accuracy_pct:.0f}% accepted accuracy, no weak fingers. {plan}"

    error_label = _ERROR_LABELS.get(dominant_error, "errors")
    if weak_fingers:
        finger_part = f"the {weak_fingers[0]} finger"
        if weak_bols:
            finger_part += f" (especially '{weak_bols[0]}')"
        return f"Accepted accuracy was {accepted_accuracy_pct:.0f}%; {error_label} were the main issue, most on {finger_part}. {plan}"
    return f"Accepted accuracy was {accepted_accuracy_pct:.0f}%; {error_label} were the main issue. {plan}"


def analyze(results: Sequence[ScoreResult], phrase: Sequence[str], current_tempo_bpm: float) -> PracticeAnalysis:
    """Turn one round's completed ScoreResults into a PracticeAnalysis. Raises
    ValueError if current_tempo_bpm <= 0."""
    if current_tempo_bpm <= 0:
        raise ValueError(f"current_tempo_bpm must be > 0, got {current_tempo_bpm}")

    summary = summarize(results)
    weak_fingers, weak_bols = _rank_weaknesses(results)
    dominant_error = _dominant_error(results)
    recommended_tempo = _recommended_tempo(current_tempo_bpm, summary.accepted_accuracy_pct, dominant_error)
    recommended_phrase = _recommended_phrase(weak_bols, phrase)
    feedback = _feedback(
        len(results),
        summary.accepted_accuracy_pct,
        weak_fingers,
        weak_bols,
        dominant_error,
        recommended_tempo,
        recommended_phrase,
    )
    return PracticeAnalysis(
        summary.accepted_accuracy_pct,
        summary.total_expected,
        weak_fingers,
        weak_bols,
        dominant_error,
        recommended_tempo,
        recommended_phrase,
        feedback,
    )
